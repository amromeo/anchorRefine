"""Verify complete paired development outputs and merge the primary runs."""
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import uuid


ARMS = ("baseline", "K24", "K28")
PANELS = ("guidance", "diagnostic")
SEEDS = ("primary", "alternate")
EXTRACTIONS = ("native", "historical")
SIDES = ("lower", "upper")
INPUT_HASHES = ("routine_hash", "anchor_hash", "diagnostic_hash")
PARAMETERS = ("Mu", "Sigma", "Lambda", "Shift", "P", "Cost", "rf")
ELECTION = ("peak_index", "winner_basin", "winner_votes", "runner_up", "vote_lead",
            "basin_counts", "assignments")
TRACE = ("peak_phases", "peak_passes", "peak_coarse_indices", "peak_fine_indices")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def table(path, keys):
    with path.open(newline="") as stream:
        result = {}
        for row in csv.DictReader(stream):
            key = tuple(row[k] for k in keys)
            if key in result:
                raise ValueError(f"{path}: duplicate {key}")
            result[key] = row
    return result


def number(value):
    return math.nan if value in ("", "NA", "NaN") else float(value)


def require(ok, context):
    if not ok:
        raise ValueError(str(context))


def same_fields(left, right, fields, context):
    for field in fields:
        require(left[field] == right[field], (context, field, left[field], right[field]))


def flag(value):
    require(value in ("TRUE", "FALSE"), ("expected boolean", value))
    return value == "TRUE"


def missing(value):
    return value in ("", "NA", "NaN")


def hash_field(row, field):
    require(re.fullmatch(r"[0-9a-f]{64}", row[field]), (row["j"], row["arm"], field))


def compare_number(left, right, field, context, maxima):
    v, w = number(left[field]), number(right[field])
    if math.isfinite(v) and math.isfinite(w):
        maxima[field] = max(maxima.get(field, 0.0), abs(v - w))
    else:
        require(left[field] == right[field], (context, field, left[field], right[field]))


def check_one_fit(fit, context):
    valid = fit["fit_status"] == "ResultFound"
    require(valid or fit["fit_status"] == "fit_failed", (context, "fit_status"))
    if valid:
        hash_field(fit, "fit_hash")
        require(all(math.isfinite(number(fit[k])) for k in ("Mu", "Sigma", "Lambda", "Shift"))
                and number(fit["Sigma"]) > 0, (context, "fitted parameters"))
    for ext in EXTRACTIONS:
        vals = [number(fit[f"{ext}_{side}"]) for side in SIDES]
        finite = all(map(math.isfinite, vals))
        require(flag(fit[f"{ext}_nonfinite"]) == (not finite), (context, ext, "nonfinite"))
        ordered = fit[f"{ext}_ordered"]
        require((flag(ordered) == (vals[0] < vals[1])) if finite else missing(ordered),
                (context, ext, "ordering flag"))
        for side, value in zip(SIDES, vals):
            out = fit[f"{ext}_out_{side}"]
            require((flag(out) == (value <= 0)) if math.isfinite(value) else missing(out),
                    (context, ext, side, "support flag"))
        if not valid:
            require(all(math.isnan(v) for v in vals), (context, ext, "failed fit with limits"))


def check_one_decision(check, fit, context):
    panel, seed_kind = check["panel"], check["seed_kind"]
    stem = "pit" if panel == "guidance" else "diagnostic"
    require(check["seed"] == fit[f"{stem}_{seed_kind}_seed"], (context, "PIT seed"))
    status = check["status"]
    require((status == "fit_failed") == (fit["fit_status"] == "fit_failed"),
            (context, "fit status", status))
    p = number(check["p"])
    if status in ("keep", "decline"):
        require(0 <= p <= 1 and (p < 0.01) == (status == "decline"), (context, status, p))
    else:
        require(status in ("fit_failed", "check_failed") and missing(check["p"]), (context, status, p))
    for ext in EXTRACTIONS:
        released = status == "keep" and not flag(fit[f"{ext}_nonfinite"])
        for side in SIDES:
            field = f"{ext}_{side}"
            value = check[f"released_{field}"]
            require((value == fit[field]) if released else missing(value), (context, field, value))


def check_pairing(fits, checks, indices, design, context):
    fit_keys = {(str(i), arm) for i in indices for arm in ARMS}
    check_keys = {(*key, p, s) for key in fit_keys for p in PANELS for s in SEEDS}
    require(set(fits) == fit_keys, (context, "incomplete or unexpected fit keys"))
    require(set(checks) == check_keys, (context, "incomplete or unexpected check keys"))
    for i in indices:
        j = str(i)
        reference = fits[j, "baseline"]
        for field in INPUT_HASHES + ("result_hash",):
            hash_field(reference, field)
        planned = design[j,]
        for field in planned:
            if reference[field] != planned[field]:
                require(math.isclose(float(reference[field]), float(planned[field]), rel_tol=5e-15),
                        (context, j, "frozen design", field))
        require(int(reference["cell_id"]) == (i - 1) // 4 + 1, (context, j, "cell"))
        for arm in ARMS:
            key = j, arm
            fit = fits[key]
            same_fields(reference, fit, tuple(planned) + INPUT_HASHES + ("cell_id", "result_hash"), key)
            check_one_fit(fit, (context, key))
            fallback = flag(fit["fallback"])
            valid = fit["fit_status"] == "ResultFound"
            require(flag(fit["guidance_used"]) == (arm != "baseline" and not fallback and valid),
                    (context, key, "guidance_used"))
            if arm == "baseline":
                require(not fallback and missing(fit["K"]), (context, key, "baseline"))
            else:
                require(fit["K"] == arm[1:] and (fallback or flag(fit["clarity"])),
                        (context, key, "K or clarity"))
            if fallback:
                same_fields(reference, fit, ("fit_hash", "fit_status"), (context, key, "fallback"))
            for p in PANELS:
                for s in SEEDS:
                    check = checks[j, arm, p, s]
                    check_one_decision(check, fit, (context, j, arm, p, s))
                    if fallback:
                        base = checks[j, "baseline", p, s]
                        same_fields(check, base, (k for k in base if k != "arm"),
                                    (context, key, "fallback check"))
        low, high = fits[j, "K24"], fits[j, "K28"]
        same_fields(low, high, ELECTION + ("peak_location", "peak_left", "peak_right", "peak_target"),
                    (context, j, "initial election"))
        if flag(high["clarity"]):
            require(flag(low["clarity"]), (context, j, "K thresholds"))
            same_fields(low, high, ("fit_hash", "fit_status", "fallback", "reason") + TRACE,
                        (context, j, "identical eligible search"))


def write_rows(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def audit(raw, out):
    out.mkdir(exist_ok=True, parents=True)
    design = table(Path(__file__).with_name("development-design.csv"), ["j"])
    require(set(design) == {(str(i),) for i in range(1, 1441)}, "Frozen design indices")
    merged = {"fits": [], "checks": []}
    details = []
    parameter_deltas = dict.fromkeys(PARAMETERS, 0.0)
    score_deltas = {f"{ext}_z_{s}": 0.0 for ext in EXTRACTIONS for s in SIDES}
    other_deltas = dict.fromkeys(("peak_location", "peak_left", "peak_right", "peak_target",
                                  "statistic"), 0.0)
    max_p = max_endpoint = 0.0
    for shard in range(1, 49):
        dirs = [raw / f"{role}-{shard}" for role in ("primary", "repeat", "other")]
        primary, repeat, other = dirs
        boots = [str(uuid.UUID((d / "boot.txt").read_text().strip())) for d in dirs]
        require(boots[0] == boots[1] and boots[0] != boots[2], (shard, "boot IDs", boots))
        pids = [int((d / "r-pid.txt").read_text().strip()) for d in dirs]
        require(min(pids) > 0 and pids[0] != pids[1], (shard, "process IDs", pids))
        platforms = [(d / "platform.txt").read_text().strip() for d in dirs]
        require(all(platforms) and platforms[0] == platforms[1], (shard, "platform"))
        fingerprints = {}
        for filename in ("results.rds", "fits.csv", "checks.csv"):
            fingerprints[filename] = digest(primary / filename)
            require(fingerprints[filename] == digest(repeat / filename), (shard, filename))
        fit_keys = ["j", "arm"]
        check_keys = fit_keys + ["panel", "seed_kind"]
        fits, other_fits = [table(d / "fits.csv", fit_keys) for d in (primary, other)]
        checks, other_checks = [table(d / "checks.csv", check_keys) for d in (primary, other)]
        indices = range(shard, 1441, 48)
        for f, c, role in ((fits, checks, "primary"), (other_fits, other_checks, "other")):
            check_pairing(f, c, indices, design, (shard, role))
        fields = (tuple(next(iter(design.values()))) + INPUT_HASHES + ELECTION + TRACE +
                  ("cell_id", "K", "fit_status", "fit_upstream_status", "fallback", "reason",
                   "guidance_used", "clarity", "election_reason"))
        for key, row in fits.items():
            rr = other_fits[key]
            same_fields(row, rr, fields, key)
            for field in PARAMETERS:
                compare_number(row, rr, field, key, parameter_deltas)
            for field in ("peak_location", "peak_left", "peak_right", "peak_target"):
                compare_number(row, rr, field, key, other_deltas)
            for ext in EXTRACTIONS:
                flags = [f"{ext}_{f}" for f in ("nonfinite", "ordered", "out_lower", "out_upper")]
                same_fields(row, rr, flags, key)
                for s in SIDES:
                    compare_number(row, rr, f"{ext}_z_{s}", key, score_deltas)
                if row["fit_status"] == "fit_failed":
                    continue
                lo, hi = [number(row[f"{ext}_{s}"]) for s in SIDES]
                width = hi - lo
                require(math.isfinite(width) and width > 0, (key, ext, "non-auditable width", lo, hi))
                for s, v in zip(SIDES, (lo, hi)):
                    delta = abs(v - number(rr[f"{ext}_{s}"])) / width
                    require(delta <= 0.001, (key, ext, s, "endpoint tolerance", delta))
                    max_endpoint = max(max_endpoint, delta)
        for key, row in checks.items():
            rr = other_checks[key]
            same_fields(row, rr, ("status", "reason", "seed"), key)
            compare_number(row, rr, "statistic", key, other_deltas)
            if row["status"] in ("keep", "decline"):
                delta = abs(number(row["p"]) - number(rr["p"]))
                require(delta <= 0.0001, (key, "PIT p tolerance", delta))
                max_p = max(max_p, delta)
        merged["fits"].extend(fits.values())
        merged["checks"].extend(checks.values())
        details.append(dict(shard=shard, primary_boot=boots[0], other_boot=boots[2],
                            primary_pid=pids[0], repeat_pid=pids[1], other_pid=pids[2],
                            primary_platform=platforms[0], other_platform=platforms[2],
                            **fingerprints))
    # The third process evaluates the next shard on the same VM. Verify that
    # each independent record belongs to the predecessor in the workflow ring.
    for i, row in enumerate(details):
        predecessor = details[i - 1]
        require(row["other_boot"] == predecessor["primary_boot"] and
                row["other_platform"] == predecessor["primary_platform"],
                (row["shard"], "neighbor provenance"))
        require(row["other_pid"] not in (predecessor["primary_pid"], predecessor["repeat_pid"]),
                (row["shard"], "neighbor process"))
    for name, rows in merged.items():
        write_rows(out / (name + ".csv"), sorted(rows, key=lambda r: (
            int(r["j"]), r["arm"], r.get("panel", ""), r.get("seed_kind", ""))))
    write_rows(out / "audit-shards.csv", details)
    summary = dict(datasets=len(design), fits=len(merged["fits"]), checks=len(merged["checks"]),
                   exact_repeat_shards=len(details), distinct_host_shards=len(details),
                   max_p_difference=max_p, max_endpoint_fraction=max_endpoint,
                   max_parameter_differences=parameter_deltas, max_score_differences=score_deltas,
                   max_election_and_statistic_differences=other_deltas)
    (out / "audit.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(summary)


if __name__ == "__main__":
    audit(Path(sys.argv[1]), Path(sys.argv[2]))
