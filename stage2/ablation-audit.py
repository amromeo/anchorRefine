"""Audit development-only K24 ablations and merge paired primary rows."""
import csv
import gzip
import json
import math
from pathlib import Path
import sys
import uuid

from audit import (
    ELECTION, EXTRACTIONS, INPUT_HASHES, PANELS, PARAMETERS, SEEDS, SIDES, TRACE,
    check_one_decision, check_one_fit, compare_number, digest, flag, hash_field,
    missing, number, require, same_fields, table, write_rows,
)


ARMS = ("baseline", "K24", "peak", "start", "region")
ORIGINAL_ARMS = ("baseline", "K24")
FIT_KEY = ("j", "arm")
CHECK_KEY = (*FIT_KEY, "panel", "seed_kind")
ELECTION_NUMBERS = ("peak_location", "peak_left", "peak_right", "peak_target")
CLARITY = ("clarity", "election_reason", *ELECTION, *ELECTION_NUMBERS)
PEAK_DIAGNOSTIC = ("upstream_peak_index", "anchor_initial_index", "same_peak", "initial_peak_count")
STATUS = ("fit_status", "fit_upstream_status", "fallback", "reason", "guidance_used")
ENDPOINT_FLAGS = tuple(f"{x}_{f}" for x in EXTRACTIONS
                       for f in ("nonfinite", "ordered", "out_lower", "out_upper"))
SCORES = tuple(f"{x}_z_{s}" for x in EXTRACTIONS for s in SIDES)
LIMITS = tuple(f"{x}_{s}" for x in EXTRACTIONS for s in SIDES)
ORIGINAL = Path(__file__).resolve().parents[1] / "results/stage2-development-45283676579"
ARCHIVED_SHA = {
    "fits": "785a06233db585f73e2720fdf381a0e0849b982c2b2e3e452bd5e9b786ebb93a",
    "checks": "2308b04b6c64ad5c1873ac3ea7989518537d733f90fee0c8735dad6b8e83038c",
}


def original_table(name, keys):
    path = ORIGINAL / "evidence" / f"{name}.csv.gz"
    require(digest(path) == ARCHIVED_SHA[name], (path, "published development digest"))
    data = {}
    with gzip.open(path, "rt", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["arm"] in ORIGINAL_ARMS:
                key = tuple(row[f] for f in keys)
                require(key not in data, ("duplicate archived row", key))
                data[key] = row
    return data


def verify_pairing(fits, checks, original, cases, design, context):
    frozen_fits, frozen_checks = original
    expected = {(str(i), arm) for i in cases for arm in ARMS}
    expected_checks = {(*key, p, s) for key in expected for p in PANELS for s in SEEDS}
    require(set(fits) == expected, (context, "missing or unexpected fits"))
    require(set(checks) == expected_checks, (context, "missing or unexpected checks"))
    for i in cases:
        j = str(i)
        reference = frozen_fits[j, "baseline"]
        elected = frozen_fits[j, "K24"]
        diagnostic = fits[j, "K24"]
        count = len(elected["basin_counts"].split(",")) if elected["basin_counts"] else 0
        require(int(diagnostic["initial_peak_count"]) == count, (context, j, "initial peak count"))
        if flag(elected["clarity"]):
            upstream = int(diagnostic["upstream_peak_index"])
            actual = int(diagnostic["anchor_initial_index"])
            require(1 <= upstream <= 512 and 1 <= actual <= 512 and count > 0
                    and actual == int(elected["peak_index"])
                    and flag(diagnostic["same_peak"]) == (actual == upstream),
                    (context, j, "initial peak comparison"))
        else:
            require(all(missing(diagnostic[f]) for f in PEAK_DIAGNOSTIC[:3]),
                    (context, j, "unclear initial peak comparison"))
        planned = design[j,]
        for field, value in planned.items():
            if reference[field] != value:
                require(math.isclose(float(reference[field]), float(value), rel_tol=5e-15),
                        (context, j, "original design differs", field))
        require(int(reference["cell_id"]) == (i - 1) // 4 + 1, (context, j, "cell"))
        for arm in ARMS:
            key = (j, arm)
            fit = fits[key]
            same_fields(fit, diagnostic, PEAK_DIAGNOSTIC, (context, key, "shared initial peak diagnostic"))
            same_fields(reference, fit, (*planned, *INPUT_HASHES, "cell_id"), (context, key, "inputs"))
            for field in INPUT_HASHES + ("result_hash", "original_result_hash"):
                hash_field(fit, field)
            require(fit["original_result_hash"] == reference["result_hash"]
                    and fit["result_hash"] == fits[j, "baseline"]["result_hash"],
                    (context, key, "original or new per-case result digest"))
            check_one_fit(fit, (context, key))
            fallback = flag(fit["fallback"])
            valid = fit["fit_status"] == "ResultFound"
            require(flag(fit["guidance_used"]) == (arm != "baseline" and not fallback and valid),
                    (context, key, "guidance use"))
            if arm in ORIGINAL_ARMS:
                ref_fit = frozen_fits[key]
                same_fields(ref_fit, fit, (f for f in ref_fit if f != "result_hash"),
                            (context, key, "original fit"))
            if arm == "baseline":
                require(not fallback and missing(fit["K"]), (context, key, "baseline flags"))
            else:
                same_fields(elected, fit, CLARITY, (context, key, "original K24 election"))
                require(fit["K"] == "24" and (fallback or flag(fit["clarity"])),
                        (context, key, "threshold or clarity"))
            if fallback:
                same_fields(reference, fit, ("fit_status", "fit_hash", *PARAMETERS, *LIMITS,
                                             *SCORES, *ENDPOINT_FLAGS), (context, key, "fallback"))
            if arm in ("start", "region"):
                require(all(missing(fit[k]) for k in TRACE), (context, key, "inactive peak tracking"))
            for panel in PANELS:
                for seed in SEEDS:
                    ck = (*key, panel, seed)
                    check = checks[ck]
                    check_one_decision(check, fit, (context, ck))
                    if arm in ORIGINAL_ARMS:
                        original_row = frozen_checks[ck]
                        same_fields(check, original_row, original_row, (context, ck, "original check"))
                    if fallback:
                        base = frozen_checks[j, "baseline", panel, seed]
                        same_fields(check, base, (f for f in base if f != "arm"),
                                    (context, ck, "fallback check"))


def compare_hosts(fits, independent_fits, checks, independent_checks, design_fields, maxima):
    fixed = (*design_fields, *INPUT_HASHES, *ELECTION, *TRACE, *STATUS, *ENDPOINT_FLAGS, *PEAK_DIAGNOSTIC,
             "cell_id", "K", "clarity", "election_reason", "original_result_hash")
    for key, row in fits.items():
        other = independent_fits[key]
        same_fields(row, other, fixed, (key, "cross-host branches and status"))
        for field in PARAMETERS + ELECTION_NUMBERS + SCORES:
            compare_number(row, other, field, key, maxima)
        if row["fit_status"] != "ResultFound":
            continue
        for ext in EXTRACTIONS:
            lo, hi = (number(row[f"{ext}_{side}"]) for side in SIDES)
            width = hi - lo
            require(math.isfinite(width) and width > 0, (key, ext, "non-auditable width", lo, hi))
            for side, x in zip(SIDES, (lo, hi)):
                delta = abs(x - number(other[f"{ext}_{side}"])) / width
                require(delta <= 0.001, (key, ext, side, "endpoint tolerance", delta))
                maxima["endpoint_fraction"] = max(maxima["endpoint_fraction"], delta)
    for key, row in checks.items():
        other = independent_checks[key]
        same_fields(row, other, ("status", "reason", "seed"), (key, "cross-host decisions"))
        compare_number(row, other, "statistic", key, maxima)
        if row["status"] in ("keep", "decline"):
            delta = abs(number(row["p"]) - number(other["p"]))
            require(delta <= 0.0001, (key, "PIT p tolerance", delta))
            maxima["p"] = max(maxima["p"], delta)
        # check_one_decision enforced identity with each host's raw limits
        # for each kept panel/seed and missing releases for every other row.


def hosts(dirs, shard):
    primary, repeat, other = dirs
    boots = [str(uuid.UUID((d / "boot.txt").read_text().strip())) for d in dirs]
    pids = [int((d / "r-pid.txt").read_text()) for d in dirs]
    platforms = [(d / "platform.txt").read_text().strip() for d in dirs]
    require(boots[0] == boots[1] and boots[0] != boots[2], (shard, "VM boots", boots))
    require(min(pids) > 0 and pids[0] != pids[1], (shard, "R processes", pids))
    require(all(platforms) and platforms[0] == platforms[1], (shard, "platforms", platforms))
    fingerprint = {}
    for name in ("fits.csv", "checks.csv", "results.rds"):
        fingerprint[name] = digest(primary / name)
        require(fingerprint[name] == digest(repeat / name), (shard, "same-host exact", name))
    return dict(shard=shard, primary_boot=boots[0], other_boot=boots[2], primary_pid=pids[0],
                repeat_pid=pids[1], other_pid=pids[2], primary_platform=platforms[0],
                other_platform=platforms[2], **fingerprint)


def audit(raw, out):
    design = table(Path(__file__).with_name("development-design.csv"), ["j"])
    require(set(design) == {(str(i),) for i in range(1, 1441)}, "Development indices")
    original = original_table("fits", FIT_KEY), original_table("checks", CHECK_KEY)
    require(len(original[0]) == 2880 and len(original[1]) == 11520, "Archived reference coverage")
    maxima = dict.fromkeys(PARAMETERS + ELECTION_NUMBERS + SCORES + ("statistic", "p", "endpoint_fraction"), 0.0)
    details, fit_rows, check_rows = [], [], []
    for shard in range(1, 49):
        dirs = [raw / f"{role}-{shard}" for role in ("primary", "repeat", "other")]
        details.append(hosts(dirs, shard))
        cases = range(shard, 1441, 48)
        paired = []
        for directory in (dirs[0], dirs[2]):
            fits = table(directory / "fits.csv", FIT_KEY)
            checks = table(directory / "checks.csv", CHECK_KEY)
            verify_pairing(fits, checks, original, cases, design, directory.name)
            paired.append((fits, checks))
        (fits, checks), (independent_fits, independent_checks) = paired
        compare_hosts(fits, independent_fits, checks, independent_checks, tuple(design["1",]), maxima)
        fit_rows.extend(fits.values())
        check_rows.extend(checks.values())
    for idx, row in enumerate(details):
        prev = details[idx - 1]
        require(row["other_boot"] == prev["primary_boot"] and row["other_platform"] == prev["primary_platform"]
                and row["other_pid"] not in (prev["primary_pid"], prev["repeat_pid"]),
                (row["shard"], "independent neighbor process"))
    out.mkdir(parents=True, exist_ok=True)
    write_rows(out / "fits.csv", sorted(fit_rows, key=lambda r: (int(r["j"]), r["arm"])))
    write_rows(out / "checks.csv", sorted(check_rows, key=lambda r: (
        int(r["j"]), r["arm"], r["panel"], r["seed_kind"])))
    write_rows(out / "audit-shards.csv", details)
    summary = dict(datasets=len(design), fits=len(fit_rows), checks=len(check_rows),
        original_reference_fits=len(original[0]), original_reference_checks=len(original[1]),
        original_reference_sha256=ARCHIVED_SHA, new_fit_rows=3 * len(design),
        new_check_rows=12 * len(design), exact_repeat_shards=len(details), distinct_host_shards=len(details),
        max_endpoint_fraction=maxima["endpoint_fraction"], max_p_difference=maxima["p"],
        max_parameter_differences={f: maxima[f] for f in PARAMETERS},
        max_score_differences={f: maxima[f] for f in SCORES},
        max_election_and_statistic_differences={f: maxima[f] for f in (*ELECTION_NUMBERS, "statistic")})
    (out / "audit.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    audit(Path(sys.argv[1]), Path(sys.argv[2]))
