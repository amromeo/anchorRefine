"""Audit a Stage 1 cohort using the frozen RIbench specification."""
import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import re
import struct
import tarfile
import uuid


ROOT = Path(__file__).resolve().parents[1]
SEEDS = ("primary", "secondary")
FROZEN_VARIABLES = ("LC_ALL", "TZ", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
        return digest.hexdigest()


def json_write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def record_host(directory):
    directory.mkdir(parents=True, exist_ok=True)
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    require(bool(boot), "Missing VM boot ID")
    json_write(directory / "host.json", {
        "boot": boot, "node": platform.node(), "platform": platform.platform(),
        "runner": os.environ["RUNNER_NAME"], "os": os.environ["RUNNER_OS"],
        "run": os.environ["GITHUB_RUN_ID"], "attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "job": os.environ["GITHUB_JOB"], "repo": os.environ["GITHUB_REPOSITORY"],
        "commit": os.environ["GITHUB_SHA"], "session": str(uuid.uuid4()),
        "settings": {key: os.environ.get(key) for key in FROZEN_VARIABLES},
    })


def load_hosts(dirs):
    primary, repeat, other = hosts = [json.loads((d / "host.json").read_text()) for d in dirs]
    for field in ("repo", "commit", "settings"):
        require(all(h[field] == primary[field] for h in hosts), "Host mismatch for " + field)
    require(all(primary[k] == repeat[k] for k in ("boot", "runner", "run", "attempt", "job", "node")),
            "Repeat ran on another job or machine")
    require(primary["boot"] != other["boot"], "Cross-machine comparison reused a VM boot")
    require(len({h["session"] for h in hosts}) == 3, "Reused a provenance record")
    pids = [int((d / "r-pid.txt").read_text()) for d in dirs]
    require(all(pid > 0 for pid in pids) and pids[0] != pids[1], "Repeat requires two R sessions")
    for host, pid in zip(hosts, pids):
        host["r_pid"] = pid
    return hosts


def cohort_definition(cohort):
    archive = ROOT / "vendor/RIbench_1.0.2.tar.gz"
    with tarfile.open(archive, "r:gz") as source:
        text = io.TextIOWrapper(source.extractfile("RIbench/inst/extdata/SpecificationTestSets.csv"))
        selected = [r for r in csv.DictReader(text) if
                    (float(r["N"]) <= 5000 if cohort == "small" else float(r["N"]) == 50000)]
    cases = {int(r["Index"]): r for r in selected}
    require(len(cases) == len(selected) == (2880 if cohort == "small" else 1440),
            "Unexpected RIbench cohort definition")
    return cases


def endpoints(case):
    return ("upper",) if case["Analyte"] == "CRP" else ("lower", "upper")


def index_rows(path, cases, keys):
    result = {}
    with path.open(newline="") as stream:
        for row in csv.DictReader(stream):
            idx = int(row["Index"])
            require(idx in cases, f"Unexpected Index {idx} in {path}")
            expected = cases[idx]
            for field in ("N", "Analyte", "Scenario"):
                require(row[field] == expected[field], f"{path} {idx}: unexpected {field}")
            require(float(row["fractionPathol"]) == float(expected["fractionPathol"]),
                    f"{path} {idx}: pathological fraction changed")
            key = (idx, *(row[k] for k in keys))
            require(key not in result, f"Duplicate row {key} in {path}")
            result[key] = row
    return result


def load_run(directory, cases, cohort):
    check_rows = index_rows(directory / "checks.csv", cases, ())
    checks = {k[0]: r for k, r in check_rows.items()}
    require(set(checks) == set(cases), f"Missing check rows in {directory}")
    estimates = index_rows(directory / "estimates.csv", cases, ("method", "extraction", "endpoint"))
    methods = ["refineR", "anchorsOnly", "anchoredRI_old"]
    if cohort == "small":
        methods.extend(["anchoredRI_taskE_raw", "anchoredRI_taskE_reported"])
    expected = {(i, method, extraction, endpoint) for i, case in cases.items()
                for method in methods for extraction in ("native", "historical") for endpoint in endpoints(case)}
    require(set(estimates) == expected,
            f"{directory}: missing {len(expected - estimates.keys())}, extra {len(estimates.keys() - expected)} estimates")
    for (idx, method, ext, side), row in estimates.items():
        expected_prob = 0.95 if cases[idx]["Analyte"] == "CRP" else (0.025 if side == "lower" else 0.975)
        require(float(row["probability"]) == expected_prob, f"Wrong percentile in {directory} Index {idx}")
    return checks, estimates, methods


def numeric(row, field):
    value = row[field]
    return math.nan if value in ("", "NA", "NaN") else float(value)


def same_float(left, right):
    return struct.pack("!d", left) == struct.pack("!d", right)


def finite_delta(left, right):
    if math.isfinite(left) and math.isfinite(right):
        return abs(left - right)
    if math.isinf(left) and left == right:
        return 0.
    return None


def write_csv(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def audit(cohort, dirs, out):
    out.mkdir(parents=True, exist_ok=True)
    hosts = load_hosts(dirs)
    cases = cohort_definition(cohort)
    primary, repeat, other = [load_run(d, cases, cohort) for d in dirs]
    checks, limits, methods = primary
    repeat_checks, repeat_limits, _ = repeat
    independent_checks, independent_limits, _ = other
    file_matches = {name: sha(dirs[0] / name) == sha(dirs[1] / name)
                    for name in ("checks.csv", "estimates.csv", "results.rds")}
    cases_out, limits_out = [], []
    for idx, case in sorted(cases.items()):
        row, again, independent = checks[idx], repeat_checks[idx], independent_checks[idx]
        digest = row["result_hash"]
        exact = bool(re.fullmatch(r"[0-9a-f]{64}", digest)) and digest == again["result_hash"] and row == again
        identity = all(re.fullmatch(r"[0-9a-f]{64}", row[k]) and row[k] == independent[k]
                       for k in ("anchor_hash", "routine_hash"))
        rec = dict(Index=idx, N=case["N"], Analyte=case["Analyte"], input_identity=identity)
        cross_pass = identity
        for seed in SEEDS:
            def check_fields(r):
                return (r[seed + "_status"], r[seed + "_reason"], numeric(r, seed + "_p"),
                        numeric(r, seed + "_statistic"))
            status, reason, p, statistic = check_fields(row)
            status2, reason2, p2, statistic2 = check_fields(independent)
            delta = finite_delta(p, p2)
            stat_delta = finite_delta(statistic, statistic2)
            valid_test = (math.isfinite(p) and math.isfinite(p2) and 0 <= p <= 1 and 0 <= p2 <= 1
                          and status == ("decline" if p < .01 else "keep")
                          and status2 == ("decline" if p2 < .01 else "keep")
                          and stat_delta is not None)
            pass_seed = valid_test and status == status2 and reason == reason2 and delta <= .0001
            rec.update({seed+"_p_delta": delta, seed+"_stat_delta": stat_delta, seed+"_decision": status,
                        seed+"_other_decision": status2, seed+"_audit": pass_seed})
            cross_pass &= pass_seed
        for param in ("Mu", "Sigma", "Lambda", "Shift"):
            rec["delta_" + param] = finite_delta(numeric(row, param), numeric(independent, param))
        gate_ok = True
        for method in methods:
            for ext in ("historical", "native"):
                keys = [(idx, method, ext, ep) for ep in endpoints(case)]
                ref = [numeric(limits[k], "estimate") for k in keys]
                width = ref[-1] if len(ref) == 1 else ref[-1] - ref[0]
                for j, key in enumerate(keys):
                    m, m2 = limits[key], independent_limits[key]
                    exact &= m == repeat_limits[key]
                    estimate = numeric(m2, "estimate")
                    returned = m["status"] == "returned"
                    status_match = m["status"] == m2["status"] and m.get("paired") == m2.get("paired")
                    delta = finite_delta(ref[j], estimate)
                    comparable = math.isfinite(width) and width > 0 and delta is not None
                    # The old and Task E comparators are read-only archived values.
                    # Matching withheld values have no interval to audit.
                    if method == "refineR":
                        ok = returned and status_match and comparable and delta <= .001 * width
                        for case_data, fit_row in ((checks[idx], m), (independent_checks[idx], m2)):
                            for seed in SEEDS:
                                release = numeric(fit_row, "released_" + seed)
                                kept = case_data[seed + "_status"] == "keep"
                                gate_ok &= (same_float(release, numeric(fit_row, "estimate"))
                                            if kept else math.isnan(release))
                    else:
                        ok = status_match and ((returned and comparable and delta <= .001 * width) or
                                               (not returned and m["estimate"] == m2["estimate"]))
                    cross_pass &= ok
                    limits_out.append(dict(Index=idx, method=method, extraction=ext, endpoint=key[-1],
                                           reference=m["estimate"], independent=m2["estimate"],
                                           reference_width=width if math.isfinite(width) else None,
                                           abs_difference=delta,
                                           fraction_of_width=delta/width if comparable else None,
                                           status=m["status"], other_status=m2["status"], passed=ok))
        rec.update(exact=exact, kept_limits_exact=gate_ok, cross_machine=cross_pass)
        cases_out.append(rec)
    write_csv(out / "case-audit.csv", cases_out)
    write_csv(out / "endpoint-audit.csv", limits_out)
    summary = dict(cohort=cohort, expected=len(cases), audited=len(cases_out),
                   passed_exact=sum(r["exact"] for r in cases_out),
                   passed_cross_machine=sum(r["cross_machine"] for r in cases_out),
                   passed_kept_limits=sum(r["kept_limits_exact"] for r in cases_out),
                   exact_file_matches=file_matches, hosts=hosts)
    for seed in SEEDS:
        summary[seed+"_max_abs_p_delta"] = max((r[seed+"_p_delta"] for r in cases_out
                                                 if r[seed+"_p_delta"] is not None), default=None)
    summary["passed"] = all(file_matches.values()) and all(
        r["exact"] and r["kept_limits_exact"] and r["cross_machine"] for r in cases_out)
    json_write(out / "audit-summary.json", summary)
    print(f"{cohort}: {summary['passed_exact']}/{len(cases)} exact, "
          f"{summary['passed_cross_machine']}/{len(cases)} cross-machine, "
          f"{summary['passed_kept_limits']}/{len(cases)} retained-limit checks")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    host_cmd = commands.add_parser("record-host")
    host_cmd.add_argument("directory", type=Path)
    for group in ("small", "large"):
        p = commands.add_parser(group)
        p.add_argument("primary", type=Path)
        p.add_argument("repeat", type=Path)
        p.add_argument("independent", type=Path)
        p.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "record-host":
        record_host(args.directory)
    else:
        raise SystemExit(audit(args.command, [args.primary, args.repeat, args.independent], args.output))
