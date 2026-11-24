"""Audit the opened confirmation study. Importing this module reads no study data."""
import csv
import json
import math
from pathlib import Path
import sys
import uuid

from audit import (ELECTION, EXTRACTIONS, INPUT_HASHES, PANELS, PARAMETERS, SEEDS, SIDES,
                   TRACE, check_one_decision, check_one_fit, digest, flag, hash_field,
                   missing, number, require, same_fields, table, write_rows)


ARMS = ("baseline", "candidate", "peak", "start", "region")
SEED_FIELDS = ("routine_seed", "anchor_seed", "diagnostic_seed", "fitter_seed",
               "pit_primary_seed", "pit_alternate_seed", "diagnostic_primary_seed",
               "diagnostic_alternate_seed")
ELECTION_VALUES = ("peak_location", "peak_left", "peak_right", "peak_target")
SCORES = tuple(f"{ext}_z_{s}" for ext in EXTRACTIONS for s in SIDES)
LIMITS = tuple(f"{ext}_{s}" for ext in EXTRACTIONS for s in SIDES)
FLAG_FIELDS = tuple(f"{ext}_{f}" for ext in EXTRACTIONS
                    for f in ("ordered", "nonfinite", "out_lower", "out_upper"))
FIT_KEY = ("j", "arm")
CHECK_KEY = (*FIT_KEY, "panel", "seed_kind")


def design_for_scoring():
    stage = Path(__file__).parent
    design = table(stage / "confirmation-design.csv", ("j",))
    development = table(stage / "development-design.csv", ("j",))
    require(set(design) == {(str(i),) for i in range(1, 2881)}, "Confirmation design coverage")
    for (j,), row in design.items():
        i = int(j)
        cell, rep = divmod(i - 1, 8)
        original = development[str(cell * 4 + 1),]
        shared = set(original) - {"j", "replicate", *SEED_FIELDS}
        require(row.keys() == original.keys() and int(row["replicate"]) == rep + 1,
                ("confirmation replicate or schema", j))
        same_fields(row, original, shared, ("confirmation factorial design", j))
        for offset, key in enumerate(SEED_FIELDS):
            require(int(row[key]) == 72000000 + 10 * i + offset, ("confirmation seed", j, key))
    return design


def verify_fit_set(fits, checks, planned, context):
    j = planned["j"]
    base = fits[j, "baseline"]
    peak = fits[j, "peak"]
    for key, val in planned.items():
        if base[key] != val:
            require(math.isclose(float(base[key]), float(val), rel_tol=5e-15), (context, "design", key))
    require(int(base["cell_id"]) == (int(j) - 1) // 8 + 1, (context, "cell"))
    same_fields(fits[j, "candidate"], peak, (f for f in peak if f != "arm"), (context, "candidate/peak"))
    shared = (*planned, *INPUT_HASHES, "result_hash", "cell_id", "selected_rule")
    for arm in ARMS:
        fit = fits[j, arm]
        same_fields(base, fit, shared, (context, arm, "paired input"))
        require(fit["selected_rule"] == "peak", (context, arm, "rule"))
        for field in (*INPUT_HASHES, "result_hash"):
            hash_field(fit, field)
        check_one_fit(fit, (context, arm))
        fallback = flag(fit["fallback"])
        require(flag(fit["guidance_used"]) == (arm != "baseline" and not fallback
                and fit["fit_status"] == "ResultFound"), (context, arm, "guidance_used"))
        if arm == "baseline":
            require(not fallback and missing(fit["K"]), (context, arm, "baseline"))
        else:
            same_fields(peak, fit, (*ELECTION, *ELECTION_VALUES, "clarity", "election_reason"),
                        (context, arm, "common election"))
            require(fit["K"] == "24" and (fallback or flag(fit["clarity"])), (context, arm, "K/clarity"))
        if arm in ("start", "region"):
            require(all(missing(fit[k]) for k in TRACE), (context, arm, "inactive peak tracking"))
        if fallback:
            same_fields(base, fit, ("fit_hash", "fit_status", "fit_upstream_status", *PARAMETERS,
                                    *LIMITS, *SCORES, *FLAG_FIELDS), (context, arm, "fallback"))
        for panel in PANELS:
            for seed in SEEDS:
                row = checks[j, arm, panel, seed]
                check_one_decision(row, fit, (context, arm, panel, seed))
                if arm == "candidate" or fallback:
                    match = "peak" if arm == "candidate" else "baseline"
                    same_fields(row, checks[j, match, panel, seed], (k for k in row if k != "arm"),
                                (context, arm, panel, seed, match))


def audit(raw, out):
    out.mkdir(parents=True, exist_ok=True)
    design = design_for_scoring()
    fit_rows, check_rows, hosts, issues = [], [], [], []
    maxdiff = dict.fromkeys((*PARAMETERS, *ELECTION_VALUES, *SCORES, "statistic", "p", "endpoint_fraction"), 0.0)
    diffs = out / "cross-host-differences.csv"
    diff_file = diffs.open("w", newline="")
    changes = csv.writer(diff_file, lineterminator="\n")
    changes.writerow(("shard", "j", "arm", "panel", "seed_kind", "field", "reference",
                      "other", "absolute_difference", "fraction_of_width", "test_passed"))
    change_count = 0

    def compare(shard, key, field, left, right, numeric=False, threshold=None, width=None,
                hash_only=False):
        nonlocal change_count
        if left == right:
            return
        change_count += 1
        passed = hash_only
        delta = fraction = ""
        if numeric:
            x, y = number(left), number(right)
            if math.isfinite(x) and math.isfinite(y):
                delta = abs(x - y)
                if field in maxdiff:
                    maxdiff[field] = max(maxdiff[field], delta)
                if width is not None and math.isfinite(width) and width > 0:
                    fraction = delta / width
                    maxdiff["endpoint_fraction"] = max(maxdiff["endpoint_fraction"], fraction)
                    passed = fraction <= 0.001
                elif width is not None:
                    passed = delta == 0
                else:
                    passed = threshold is None or delta <= threshold
            else:
                passed = (math.isnan(x) and math.isnan(y)) or x == y
        changes.writerow((shard, *key, *(("", "") if len(key) == 2 else ()), field,
                          left, right, delta, fraction, passed))
        if not passed:
            issues.append(f"Cross-host difference outside the rule: shard={shard}, key={key}, field={field}")

    def capture(check, description):
        try:
            check()
        except (ValueError, TypeError, KeyError, OSError) as error:
            issues.append(f"{description}: {error}")

    for shard in range(1, 49):
        dirs = [raw / f"{role}-{shard}" for role in ("primary", "repeat", "other")]
        primary, repeat, other = dirs
        try:
            boots = [str(uuid.UUID((d / "boot.txt").read_text().strip())) for d in dirs]
            pids = [int((d / "r-pid.txt").read_text()) for d in dirs]
            platforms = [(d / "platform.txt").read_text().strip() for d in dirs]
            host_ok = (boots[0] == boots[1] and boots[0] != boots[2] and min(pids) > 0
                       and pids[0] != pids[1] and all(platforms) and platforms[0] == platforms[1])
            if not host_ok:
                issues.append(f"Host or process identities are invalid for shard {shard}")
            fingerprints = {}
            exact = True
            for filename in ("results.rds", "fits.csv", "checks.csv"):
                fingerprints[filename] = digest(primary / filename)
                if fingerprints[filename] != digest(repeat / filename):
                    exact = False
                    issues.append(f"Same-host repeat differs for shard {shard}: {filename}")
            hosts.append(dict(shard=shard, primary_boot=boots[0], other_boot=boots[2], primary_pid=pids[0],
                              repeat_pid=pids[1], other_pid=pids[2], primary_platform=platforms[0],
                              other_platform=platforms[2], exact=exact, host_ok=host_ok, **fingerprints))
            cases = range(shard, 2881, 48)
            fit_keys = {(str(i), arm) for i in cases for arm in ARMS}
            check_keys = {(*k, p, s) for k in fit_keys for p in PANELS for s in SEEDS}
            tables = []
            for directory in (primary, other):
                fits = table(directory / "fits.csv", FIT_KEY)
                checks = table(directory / "checks.csv", CHECK_KEY)
                require(set(fits) == fit_keys and set(checks) == check_keys,
                        (directory.name, "missing or unexpected fit/check rows"))
                for i in cases:
                    capture(lambda: verify_fit_set(fits, checks, design[str(i),], (directory.name, i)),
                            f"Pairing shard={shard} j={i}")
                tables.append((fits, checks))
            (fits, checks), (other_fits, other_checks) = tables
            for key, row in fits.items():
                independent = other_fits[key]
                require(row.keys() == independent.keys(), (shard, "fit schema"))
                for field, val in row.items():
                    if field in LIMITS:
                        ext = field.split("_")[0]
                        width = number(row[ext + "_upper"]) - number(row[ext + "_lower"])
                        compare(shard, key, field, val, independent[field], numeric=True, width=width)
                    else:
                        compare(shard, key, field, val, independent[field],
                                numeric=field in (*PARAMETERS, *ELECTION_VALUES, *SCORES),
                                hash_only=field in ("fit_hash", "result_hash"))
            for key, row in checks.items():
                independent = other_checks[key]
                require(row.keys() == independent.keys(), (shard, "check schema"))
                for field, val in row.items():
                    if field.startswith("released_"):
                        fit = fits[key[:2]]
                        ext = field.split("_")[1]
                        width = number(fit[ext + "_upper"]) - number(fit[ext + "_lower"])
                        compare(shard, key, field, val, independent[field], numeric=True, width=width)
                    else:
                        compare(shard, key, field, val, independent[field],
                                numeric=field in ("p", "statistic"), threshold=0.0001 if field == "p" else None)
            fit_rows.extend(fits.values())
            check_rows.extend(checks.values())
        except (ValueError, KeyError, OSError) as error:
            issues.append(f"Cannot audit shard {shard}: {error}")
    diff_file.close()
    indexed = {h["shard"]: h for h in hosts}
    for s, row in indexed.items():
        prev = indexed.get((s - 2) % 48 + 1)
        if not (prev and row["other_boot"] == prev["primary_boot"] and row["other_platform"] ==
                prev["primary_platform"] and row["other_pid"] not in (prev["primary_pid"], prev["repeat_pid"])):
            issues.append(f"Independent job ring provenance differs at shard {s}")
    summary = dict(passed=not issues, datasets=len(design), fits=len(fit_rows), checks=len(check_rows),
                   exact_repeat_shards=sum(h["exact"] for h in hosts),
                   distinct_host_shards=sum(h["host_ok"] for h in hosts),
                   max_endpoint_fraction=maxdiff["endpoint_fraction"], max_p_difference=maxdiff["p"],
                   max_parameter_differences={k: maxdiff[k] for k in PARAMETERS},
                   max_score_differences={k: maxdiff[k] for k in SCORES},
                   max_election_and_statistic_differences={k: maxdiff[k] for k in (*ELECTION_VALUES, "statistic")},
                   cross_host_differences=change_count, errors=issues)
    if hosts:
        write_rows(out / "audit-shards.csv", hosts)
    (out / "audit.json").write_text(json.dumps(summary, indent=2) + "\n")
    require(not issues, ("confirmation audit failed; see audit.json and cross-host-differences.csv", len(issues)))
    write_rows(out / "fits.csv", sorted(fit_rows, key=lambda r: (int(r["j"]), r["arm"])))
    write_rows(out / "checks.csv", sorted(check_rows, key=lambda r: (int(r["j"]), r["arm"], r["panel"], r["seed_kind"])))
    print(json.dumps(summary))


if __name__ == "__main__":
    audit(Path(sys.argv[1]), Path(sys.argv[2]))
