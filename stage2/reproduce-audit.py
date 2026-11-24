"""Verify the selected peak-only rule against its frozen development arm."""
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
    number, require, table, write_rows,
)


ARCHIVE = Path(__file__).resolve().parents[1] / "results/stage2-ablations-45293475762/evidence"
ARCHIVE_SHA256 = {
    "fits": "b4a7097c640e439058fc6deacaf8d82c20314a9671eb5b5e6efdf1981ae8dbf8",
    "checks": "8a1549c254a37c5ce424dcefee317b0c7dc3dddc74c507f68185dbfa87005538",
}
FILES = ("fits.csv", "checks.csv", "matches.csv", "results.rds")
J_KEY = ("j",)
FIT_KEY = ("j", "arm")
CHECK_KEY = ("j", "arm", "panel", "seed_kind")
PEAK_DIAGNOSTIC = ("upstream_peak_index", "anchor_initial_index", "same_peak", "initial_peak_count")
ELECTION_NUMERIC = ("peak_location", "peak_left", "peak_right", "peak_target")
SCORES = tuple(f"{ext}_z_{s}" for ext in EXTRACTIONS for s in SIDES)
FLAGS = tuple(f"{ext}_{field}" for ext in EXTRACTIONS
              for field in ("nonfinite", "ordered", "out_lower", "out_upper"))
LIMITS = tuple(f"{ext}_{side}" for ext in EXTRACTIONS for side in SIDES)
EXACT_FLAGS = ("inputs_exact", "exact_fit", "exact_search", "exact_fit_row",
               "exact_checks", "exact_scoring", "exact_diagnostic")


class Discrepancies:
    def __init__(self):
        self.rows = []

    def add(self, context, field, observed, expected):
        self.rows.append(dict(context=str(context), field=str(field),
                              observed=str(observed), expected=str(expected)))

    def equal(self, context, field, observed, expected):
        if observed != expected:
            self.add(context, field, observed, expected)

    def fields(self, context, actual, expected, fields):
        for field in fields:
            if field not in actual:
                self.add(context, field, "[missing column]", expected[field])
            else:
                self.equal(context, field, actual[field], expected[field])

    def call(self, context, fn, *args):
        try:
            return fn(*args)
        except (OSError, ValueError, KeyError, TypeError, OverflowError, csv.Error) as exc:
            self.add(context, fn.__name__, str(exc), "valid input")
            return None

    def keys(self, context, rows, expected):
        for key in sorted(expected - rows.keys()):
            self.add(context, "missing row", key, "present")
        for key in sorted(rows.keys() - expected):
            self.add(context, "unexpected row", key, "absent")


def archived(name, keys):
    path = ARCHIVE / f"{name}.csv.gz"
    require(digest(path) == ARCHIVE_SHA256[name], (path, "archived digest"))
    result = {}
    with gzip.open(path, "rt", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["arm"] == "peak":
                key = tuple(row[k] for k in keys)
                require(key not in result, (name, "duplicate archive key", key))
                result[key] = row
    indices = range(1, 1441)
    expected = {(str(i), "peak") for i in indices}
    if name == "checks":
        expected = {(*k, p, s) for k in expected for p in PANELS for s in SEEDS}
    require(result.keys() == expected, (name, "incomplete published peak arm"))
    return result


def host(d):
    boot = str(uuid.UUID((d / "boot.txt").read_text().strip()))
    platform = (d / "platform.txt").read_text().strip()
    pid = int((d / "r-pid.txt").read_text().strip())
    require(platform and pid > 0, (d, "missing platform or R process"))
    return dict(boot=boot, platform=platform, pid=pid)


def check_processes(dirs, shard, issues):
    details = {"shard": shard}
    for role, directory in dirs.items():
        meta = issues.call(directory, host, directory) or {}
        details.update({f"{role}_{k}": v for k, v in meta.items()})
    if all(f"{r}_pid" in details for r in dirs):
        issues.equal(shard, "same-host boot", details["repeat_boot"], details["primary_boot"])
        issues.equal(shard, "same-host platform", details["repeat_platform"], details["primary_platform"])
        if details["repeat_pid"] == details["primary_pid"]:
            issues.add(shard, "separate R processes", details["repeat_pid"], "different PID")
        if details["other_boot"] == details["primary_boot"]:
            issues.add(shard, "cross-machine", details["other_boot"], "different boot")
    for filename in FILES:
        primary, repeat = [issues.call((shard, r), digest, dirs[r] / filename) for r in ("primary", "repeat")]
        details[filename] = primary
        issues.equal((shard, "same-host bytes"), filename, repeat, primary)
    return details


def check_receipt(match, fit, expected, context, issues):
    expected_fields = {
        "rule": "peak", "source_arm": "peak", "archived_result_hash": expected["result_hash"],
        "archived_fit_hash": expected["fit_hash"], "fit_hash": fit["fit_hash"],
        "selected_result_hash": fit["result_hash"], "fit_status": fit["fit_status"],
        "archived_fit_status": expected["fit_status"], "inputs_exact": "TRUE", "search_structure": "TRUE",
        "exact_diagnostic": "TRUE",
        "exact_fit": "TRUE" if fit["fit_hash"] == expected["fit_hash"] else "FALSE",
    }
    expected_fields.update({k: expected[k] for k in INPUT_HASHES})
    issues.fields(context, match, expected_fields, expected_fields)
    for field in EXACT_FLAGS:
        issues.call((context, field), flag, match[field])


def verify_rows(fits, checks, matches, original, indices, role, maxima, issues):
    fit_keys = {(str(i), "selected") for i in indices}
    check_keys = {(*k, p, s) for k in fit_keys for p in PANELS for s in SEEDS}
    issues.keys((role, "fits"), fits, fit_keys)
    issues.keys((role, "checks"), checks, check_keys)
    issues.keys((role, "matches"), matches, {k[:1] for k in fit_keys})
    archived_fits, archived_checks = original
    verified = {j for j, arm in fit_keys if (j, arm) in fits and (j,) in matches
                and all((j, arm, p, s) in checks for p in PANELS for s in SEEDS)}
    for key in sorted(fit_keys & fits.keys()):
        before = len(issues.rows)
        j, _ = key
        row = fits[key]
        ref = archived_fits[j, "peak"]
        context = (role, j)
        issues.fields(context, row, {"rule": "peak", "source_arm": "peak"}, ("rule", "source_arm"))
        # The original job ran on a different VM. Compare data/branch identity
        # exactly and quantitative outputs under the frozen practical audit.
        # The historical whole-case digest covers all five original arms.
        skip = {"arm", "fit_hash", "result_hash", "original_result_hash",
                *PARAMETERS, *LIMITS, *SCORES, *ELECTION_NUMERIC}
        issues.fields((context, "archived peak fit"), row, ref, set(ref) - skip)
        issues.call(context, compare_fit, ref, row, (context, "archived peak fit"), maxima, issues)
        for field in (*INPUT_HASHES, "result_hash"):
            issues.call(context, hash_field, row, field)
        issues.call(context, check_one_fit, row, context)
        if (j,) in matches:
            issues.call(context, check_receipt, matches[j,], row, ref, context, issues)
        if len(issues.rows) != before:
            verified.discard(j)
    for key in sorted(checks.keys() & check_keys):
        before = len(issues.rows)
        j, arm, panel, seed = key
        check = checks[key]
        ref = archived_checks[j, "peak", panel, seed]
        context = (role, key)
        issues.call(context, compare_decision, ref, check, archived_fits[j, "peak"],
                    (context, "archived peak decision"), maxima, issues)
        if (j, arm) in fits:
            issues.call(context, check_one_decision, check, fits[j, arm], context)
        if len(issues.rows) != before:
            verified.discard(j)
    return len(verified)


def compare_limits(ref, actual, ref_fit, prefix, context, maxima, issues):
    for ext in EXTRACTIONS:
        width = number(ref_fit[ext + "_upper"]) - number(ref_fit[ext + "_lower"])
        for side in SIDES:
            key = f"{prefix}{ext}_{side}"
            x, y = number(ref[key]), number(actual[key])
            if not math.isfinite(x) or not math.isfinite(y):
                issues.equal(context, key, actual[key], ref[key])
                if not prefix and ref_fit["fit_status"] == "ResultFound":
                    issues.add(context, key, (x, y), "auditable finite endpoints")
                continue
            if not math.isfinite(width) or width <= 0:
                issues.add(context, ext + " reference width", width, "finite and positive")
                continue
            delta = abs(x - y) / width
            if not delta <= 0.001:
                issues.add(context, key + " relative difference", delta, "<= 0.001")
            maxima["endpoint_fraction"] = max(maxima["endpoint_fraction"], delta)


def compare_fit(ref, actual, context, maxima, issues):
    for field in PARAMETERS + ELECTION_NUMERIC + SCORES:
        issues.call(context, compare_number, ref, actual, field, context, maxima)
    compare_limits(ref, actual, ref, "", context, maxima, issues)


def compare_decision(ref, actual, ref_fit, context, maxima, issues):
    issues.fields(context, actual, ref, ("panel", "seed_kind", "status", "reason", "seed"))
    issues.call(context, compare_number, ref, actual, "statistic", context, maxima)
    if ref["status"] in ("keep", "decline"):
        delta = abs(number(ref["p"]) - number(actual["p"]))
        if not delta <= 0.0001:
            issues.add(context, "absolute p difference", delta, "<= 0.0001")
        if math.isfinite(delta):
            maxima["p"] = max(maxima["p"], delta)
    else:
        issues.equal(context, "p", actual["p"], ref["p"])
    compare_limits(ref, actual, ref_fit, "released_", context, maxima, issues)


def cross_hosts(left, right, maxima, issues):
    fits, checks, _ = left
    other_fits, other_checks, _ = right
    for key in fits.keys() & other_fits.keys():
        row, other = fits[key], other_fits[key]
        fields = (*ELECTION, *TRACE, *INPUT_HASHES, *FLAGS, *PEAK_DIAGNOSTIC,
                  "arm", "K", "rule", "source_arm", "fit_status", "fit_upstream_status",
                  "guidance_used", "fallback", "reason", "clarity", "election_reason")
        issues.fields((key, "cross-host"), other, row, fields)
        issues.call(key, compare_fit, row, other, (key, "cross-host"), maxima, issues)
    for key in checks.keys() & other_checks.keys():
        if key[:2] in fits:
            issues.call(key, compare_decision, checks[key], other_checks[key], fits[key[:2]],
                        (key, "cross-host"), maxima, issues)


def audit(raw, out):
    out.mkdir(parents=True, exist_ok=True)
    issues = Discrepancies()
    originals = [issues.call(name, archived, name, keys) for name, keys in (("fits", FIT_KEY), ("checks", CHECK_KEY))]
    roles = ("primary", "repeat", "other")
    tables = (("fits", FIT_KEY), ("checks", CHECK_KEY), ("matches", J_KEY))
    merged = {name: [] for name, _ in tables}
    maxima = dict.fromkeys((*PARAMETERS, *SCORES, *ELECTION_NUMERIC, "statistic", "endpoint_fraction", "p"), 0.0)
    archive_maxima = maxima.copy()
    archived_matches = 0
    details = []
    for shard in range(1, 49):
        dirs = {role: raw / f"{role}-{shard}" for role in roles}
        details.append(check_processes(dirs, shard, issues))
        pair = []
        for role in ("primary", "other"):
            directory = dirs[role]
            rows = [issues.call(directory, table, directory / (name + ".csv"), keys) for name, keys in tables]
            if None in rows:
                continue
            if None not in originals:
                verified = issues.call(directory, verify_rows, *rows, originals, range(shard, 1441, 48),
                                       directory.name, archive_maxima, issues)
                if role == "primary":
                    archived_matches += verified or 0
            pair.append(rows)
            if role == "primary":
                for (name, _), content in zip(tables, rows):
                    merged[name].extend(content.values())
        if len(pair) == 2:
            issues.call(shard, cross_hosts, *pair, maxima, issues)
    for i, row in enumerate(details):
        prev = details[i - 1]
        if "other_pid" in row and "primary_pid" in prev and "repeat_pid" in prev:
            issues.equal(i + 1, "neighbor boot", row["other_boot"], prev["primary_boot"])
            issues.equal(i + 1, "neighbor platform", row["other_platform"], prev["primary_platform"])
            if row["other_pid"] in (prev["primary_pid"], prev["repeat_pid"]):
                issues.add(i + 1, "neighbor R process", row["other_pid"], "different PID")
    passed = not issues.rows
    summary = dict(passed=passed, rule="peak", source_arm="peak",
                   datasets=len(merged["matches"]), fits=len(merged["fits"]), checks=len(merged["checks"]),
                   archived_matches=archived_matches,
                   archived_reference_fits=len(originals[0] or {}), archived_reference_checks=len(originals[1] or {}),
                   archived_sha256=ARCHIVE_SHA256, shards=len(details), discrepancy_count=len(issues.rows),
                   exact_repeat_shards=len(details) if passed else None,
                   distinct_host_shards=len(details) if passed else None,
                   exact_archive_counts={f: sum(r.get(f) == "TRUE" for r in merged["matches"]) for f in EXACT_FLAGS},
                   max_archive_differences=archive_maxima,
                   max_endpoint_fraction=maxima["endpoint_fraction"], max_p_difference=maxima["p"],
                   max_differences={f: maxima[f] for f in (*PARAMETERS, *SCORES, *ELECTION_NUMERIC, "statistic")})
    if passed:
        for name, rows in merged.items():
            write_rows(out / (name + ".csv"), sorted(rows, key=lambda r: (
                int(r["j"]), r.get("panel", ""), r.get("seed_kind", ""))))
        write_rows(out / "audit-shards.csv", details)
    with (out / "discrepancies.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("context", "field", "observed", "expected"))
        writer.writeheader()
        writer.writerows(issues.rows)
    (out / "audit.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return passed


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python3 stage2/reproduce-audit.py RAW_DIR MERGED_DIR")
    sys.exit(0 if audit(Path(sys.argv[1]), Path(sys.argv[2])) else 1)
