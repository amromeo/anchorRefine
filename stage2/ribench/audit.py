"""Verify one complete RIbench cohort before releasing its primary tables."""
import csv
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from stage2.audit import (ELECTION, PARAMETERS, TRACE, check_one_decision, digest,
                          flag, missing, number, require, same_fields, table, write_rows)
from stage2.ribench.audit_reference import EXTRACTIONS, read_reference, sides


ARMS = ("baseline", "candidate", "peak", "start", "region")
SEEDS = ("primary", "alternate")
FIT_KEY = ("Index", "arm")
CHECK_KEY = (*FIT_KEY, "panel", "seed_kind")
PEAK = ("upstream_peak_index", "anchor_initial_index", "same_peak", "initial_peak_count")
PEAK_VALUES = ("peak_location", "peak_left", "peak_right", "peak_target")
LIMITS = tuple(f"{x}_{s}" for x in EXTRACTIONS for s in ("lower", "upper"))
SCORES = tuple(f"{x}_z_{s}" for x in EXTRACTIONS for s in (
    "lower", "upper", "upper_if_group_zero", "upper_before_group"))
FLAGS = tuple(f"{x}_{f}" for x in EXTRACTIONS for f in ("nonfinite", "ordered", "out_lower", "out_upper"))
FIT_FIELDS = ("fit_hash", "fit_status", "fit_upstream_status", *PARAMETERS, *LIMITS, *FLAGS)
SHA = re.compile(r"^[0-9a-f]{64}$")


class Audit:
    def __init__(self, stream):
        self.writer = csv.writer(stream, lineterminator="\n")
        self.writer.writerow(("source", "context", "field", "expected", "observed", "absolute_difference",
                              "fraction_of_width", "passed"))
        self.failures = 0
        self.differences = Counter()
        self.maxima = defaultdict(dict)

    def change(self, source, context, field, left, right, passed, delta="", fraction=""):
        self.writer.writerow((source, str(context), field, left, right, delta, fraction, passed))
        self.differences[source] += 1
        self.failures += not passed

    def run(self, source, context, fn, *args):
        try:
            return fn(*args)
        except (ValueError, KeyError, IndexError, TypeError, OverflowError, OSError, csv.Error) as exc:
            self.change(source, context, "integrity", "valid record", str(exc), False)
            return None

    def keys(self, source, context, observed, expected):
        for key in sorted(expected - set(observed)):
            self.change(source, context, "missing row", key, "", False)
        for key in sorted(set(observed) - expected):
            self.change(source, context, "unexpected row", "", key, False)

    def compare(self, source, context, field, left, right, mode="exact", width=None):
        if left == right:
            return
        if mode in ("exact", "hash"):
            self.change(source, context, field, left, right, mode == "hash")
            return
        x, y = number(left), number(right)
        if not (math.isfinite(x) and math.isfinite(y)):
            self.change(source, context, field, left, right, x == y or (math.isnan(x) and math.isnan(y)))
            return
        delta = abs(x-y)
        fraction = ""
        passed = True
        maxima = self.maxima[source]
        target = "p" if mode == "probability" else field
        maxima[target] = max(maxima.get(target, 0.0), delta)
        if mode == "limit":
            passed = width is not None and math.isfinite(width) and width > 0
            if passed:
                fraction = delta / width
                maxima["endpoint_fraction"] = max(maxima.get("endpoint_fraction", 0.0), fraction)
                passed = fraction <= 0.001
        if mode == "probability":
            passed = delta <= 0.0001
        self.change(source, context, field, left, right, passed, delta, fraction)


def widths(fit):
    return {ext: number(fit[f"{ext}_upper"]) -
            (number(fit[f"{ext}_lower"]) if flag(fit["requested_lower"]) else 0.0)
            for ext in EXTRACTIONS}


def zero_groups(raw, role, audit):
    groups = set()
    for shard in range(1, 49):
        path = raw / f"{role}-{shard}" / "fits.csv"
        def read():
            with path.open(newline="") as stream:
                for r in csv.DictReader(stream):
                    for x in EXTRACTIONS:
                        if number(r[f"{x}_upper"]) == 0:
                            groups.add((r["Analyte"], r["arm"], x))
        audit.run(role, path, read)
    return groups


def finalize_scores(rows, groups, changes, role):
    for row in rows.values():
        for ext in EXTRACTIONS:
            key = f"{ext}_z_upper"
            original = row[key]
            group = row["Analyte"], row["arm"], ext
            active = group in groups
            row[f"{key}_before_group"] = original
            row[f"{ext}_group_has_zero_upper"] = "TRUE" if active else "FALSE"
            if active:
                row[key] = row[f"{key}_if_group_zero"]
                if row[key] != original:
                    changes.writerow((role, row["Index"], *group, original, row[key]))


def host_proof(dirs, shard, audit):
    meta = {}
    for role, directory in dirs.items():
        def read_host():
            boot = str(uuid.UUID((directory / "boot.txt").read_text().strip()))
            platform = (directory / "platform.txt").read_text().strip()
            pid = int((directory / "r-pid.txt").read_text())
            require(platform and pid > 0, (directory, "host/process identification"))
            return boot, platform, pid
        fields = audit.run("host", directory, read_host)
        if fields:
            meta.update(zip((f"{role}_boot", f"{role}_platform", f"{role}_pid"), fields))
    exact = varied = False
    if len(meta) == 9:
        exact = (meta["primary_boot"] == meta["repeat_boot"] and meta["primary_platform"] == meta["repeat_platform"]
                 and meta["primary_pid"] != meta["repeat_pid"])
        varied = meta["primary_boot"] != meta["other_boot"]
        if not (exact and varied):
            audit.change("host", shard, "isolated runs", "two same-host processes + separate VM", meta, False)
    for f in ("fits.csv", "checks.csv", "results.rds"):
        first, second = [audit.run(role, shard, digest, dirs[role] / f) for role in ("primary", "repeat")]
        meta[f] = first
        if not first or first != second:
            exact = False
            audit.change("same_host", shard, f, first, second, False)
    return dict(shard=shard, exact=exact, distinct=varied, **meta)


def check_case(fits, checks, d, context):
    i = d["Index"]
    base, peak = fits[i, "baseline"], fits[i, "peak"]
    requested = sides(d)
    same_fields(fits[i, "candidate"], peak, (f for f in peak if f != "arm"), (context, "peak identity"))
    counts = [int(s) for s in peak["basin_counts"].split(",")] if peak["basin_counts"] else []
    require(int(peak["initial_peak_count"]) == len(counts), (context, "peak count"))
    if counts:
        assignments = peak["assignments"].split(",")
        voted = Counter(int(a) for a in assignments if not missing(a))
        require(len(assignments) == 40 and all(1 <= k <= len(counts) for k in voted) and
                counts == [voted[k] for k in range(1, len(counts)+1)], (context, "40-anchor basin votes"))
        ranked = sorted(counts, reverse=True) + [0]
        require(int(peak["winner_votes"]) == ranked[0] and int(peak["runner_up"]) == ranked[1] and
                int(peak["vote_lead"]) == ranked[0]-ranked[1], (context, "winner votes and lead"))
    if flag(peak["clarity"]):
        initial, upstream = int(peak["anchor_initial_index"]), int(peak["upstream_peak_index"])
        require(counts and int(peak["winner_votes"]) >= 24 and int(peak["vote_lead"]) >= 8 and
                1 <= upstream <= 512 and 1 <= initial <= 512 and initial == int(peak["peak_index"])
                and flag(peak["same_peak"]) == (initial == upstream), (context, "first peak selection"))
    else:
        require(all(missing(peak[f]) for f in PEAK[:3]), (context, "undefined first-peak comparison"))
    for arm in ARMS:
        fit = fits[i, arm]
        same_fields(fit, d, d, (context, arm, "frozen design and inputs"))
        same_fields(fit, peak, PEAK + ("result_hash",), (context, arm, "paired case"))
        valid = fit["fit_status"] == "ResultFound"
        fallback = flag(fit["fallback"])
        require(fit["selected_rule"] == "peak" and (valid or fit["fit_status"] == "fit_failed"), (context, arm))
        require(SHA.fullmatch(fit["result_hash"]) and (not valid or SHA.fullmatch(fit["fit_hash"])),
                (context, arm, "serialized digests"))
        require(not valid or (all(math.isfinite(number(fit[k])) for k in ("Mu", "Sigma", "Lambda", "Shift"))
                and number(fit["Sigma"]) > 0), (context, arm, "fitted parameters"))
        require(flag(fit["guidance_used"]) == (arm != "baseline" and not fallback and valid),
                (context, arm, "guidance activation"))
        if arm == "baseline":
            require(not fallback and missing(fit["K"]), (context, arm, "pass-through identity"))
        else:
            same_fields(fit, peak, ELECTION + PEAK_VALUES + ("clarity", "election_reason"),
                        (context, arm, "common first election"))
            require(fit["K"] == "24" and (fallback or flag(fit["clarity"])), (context, arm, "threshold"))
        if arm in ("start", "region"):
            require(all(missing(fit[f]) for f in TRACE), (context, arm, "unexpected peak tracking"))
        if fallback:
            # Official scores depend on the whole arm/analyte group. Compare
            # both *unaggregated* alternatives for an identical fallback fit.
            same_fields(fit, base, (*FIT_FIELDS, *(f for f in SCORES if not f.endswith("_z_upper"))),
                        (context, arm, "unchanged fallback fit"))
        for ext in EXTRACTIONS:
            values = [number(fit[f"{ext}_{s}"]) for s in requested]
            complete = all(map(math.isfinite, values))
            require(flag(fit[f"{ext}_nonfinite"]) == (not complete), (context, arm, ext, "finite flag"))
            if len(requested) == 1:
                require(all(missing(fit[f"{ext}_{f}"]) for f in ("lower", "out_lower", "ordered", "z_lower")),
                        (context, arm, ext, "CRP has no lower endpoint"))
            for s, val in zip(requested, values):
                out = fit[f"{ext}_out_{s}"]
                require((flag(out) == (val <= number(d["nonp_shift"]))) if math.isfinite(val) else missing(out),
                        (context, arm, ext, s, "support flag"))
            if len(requested) == 2:
                require((flag(fit[f"{ext}_ordered"]) == (values[0] < values[1])) if complete else
                        missing(fit[f"{ext}_ordered"]), (context, arm, ext, "order flag"))
            require(valid or all(math.isnan(v) for v in values), (context, arm, ext, "failed fit with limits"))
            # A failed fit or wholly unavailable interval has no finite endpoint
            # to audit. Every reported finite endpoint requires a usable width.
            if any(map(math.isfinite, values)):
                w = widths(fit)[ext]
                require(math.isfinite(w) and w > 0, (context, arm, ext, "non-auditable width", values))
        for seed in SEEDS:
            ck = checks[i, arm, "guidance", seed]
            check_one_decision(ck, fit, (context, arm, seed))
            if fallback or arm == "candidate":
                ref = checks[i, "baseline" if fallback else "peak", "guidance", seed]
                same_fields(ck, ref, (f for f in ck if f != "arm"), (context, arm, seed, "paired decision"))


def compare_baseline(role, fit, checks, refs, audit):
    _, design, previous, estimates, small_limits, small_deltas = refs
    i = fit["Index"]
    saved = previous[i,]
    context = role, i
    source = "stage1"
    same_fields(fit, design[i,], design[i,], (context, "baseline input/seed identity"))
    want = "ResultFound" if flag(saved["fit_valid"]) else "fit_failed"
    audit.compare(source, context, "fit_status", want, fit["fit_status"])
    for k in ("Mu", "Sigma", "Lambda", "Shift"):
        audit.compare(source, context, k, saved[k], fit[k], "number")
        if small_deltas:
            # In Stage 0 the published delta is the fresh vendored fit minus
            # C2. The exact engine comparison also verified the CRAN fit.
            original = format(number(saved[k]) + number(small_deltas[i,][k]), ".17g")
            audit.compare("stage0", context, k, original, fit[k], "number")
    for kind, original in zip(SEEDS, ("primary", "secondary")):
        check = checks[i, "baseline", "guidance", kind]
        for field in ("seed", "status", "reason", "statistic", "p"):
            mode = {"p": "probability", "statistic": "number"}.get(field, "exact")
            audit.compare(source, (*context, kind), field, saved[f"{original}_{field}"], check[field], mode)
    for ext in EXTRACTIONS:
        endpoints = sides(fit)
        endpoint_refs = [estimates[i, ext, s] for s in endpoints]
        w = number(endpoint_refs[-1]["estimate"]) - (number(endpoint_refs[0]["estimate"]) if "lower" in endpoints else 0)
        reported = "unavailable" if flag(fit[f"{ext}_nonfinite"]) else "returned"
        for side, ref in zip(endpoints, endpoint_refs):
            key = f"{ext}_{side}"
            audit.compare(source, context, key+"_status", ref["status"], reported)
            if math.isfinite(number(ref["estimate"])):
                require(math.isfinite(w) and w > 0, (context, ext, "non-auditable Stage 1 width"))
            audit.compare(source, context, key, ref["estimate"], fit[key], "limit", w)
            audit.compare(source, context, f"{ext}_z_{side}", ref["z"], fit[f"{ext}_z_{side}"], "number")
            for kind, original in zip(SEEDS, ("primary", "secondary")):
                check = checks[i, "baseline", "guidance", kind]
                audit.compare(source, (*context, kind), "released_"+key, ref["released_"+original],
                              check["released_"+key], "limit", w)
        if small_limits:
            field = "candidate_" + ext
            old = [small_limits[i, side] for side in endpoints]
            w0 = number(old[-1][field]) - (number(old[0][field]) if "lower" in endpoints else 0)
            require(math.isfinite(w0) and w0 > 0, (context, ext, "non-auditable Stage 0 width"))
            for side, ref in zip(endpoints, old):
                key = f"{ext}_{side}"
                audit.compare("stage0", context, "fit_status", ref["fit_status"], fit["fit_status"])
                audit.compare("stage0", context, key, ref[field], fit[key], "limit", w0)


def cross_pair(first, other, checks, other_checks, audit):
    for key in first.keys() & other.keys():
        a, b = first[key], other[key]
        require(a.keys() == b.keys(), (key, "cross-host fit schema"))
        w = widths(a)
        for field in a:
            if field in LIMITS:
                audit.compare("cross_host", key, field, a[field], b[field], "limit", w[field.split("_")[0]])
            else:
                mode = ("hash" if field in ("fit_hash", "result_hash") else
                        "number" if field in (*PARAMETERS, *PEAK_VALUES, *SCORES) else "exact")
                audit.compare("cross_host", key, field, a[field], b[field], mode)
    for key in checks.keys() & other_checks.keys():
        a, b = checks[key], other_checks[key]
        require(a.keys() == b.keys(), (key, "cross-host check schema"))
        if key[:2] not in first:
            continue
        w = widths(first[key[:2]])
        for field in a:
            if field.startswith("released_"):
                audit.compare("cross_host", key, field, a[field], b[field], "limit", w[field.split("_")[1]])
            else:
                mode = {"p": "probability", "statistic": "number"}.get(field, "exact")
                audit.compare("cross_host", key, field, a[field], b[field], mode)


def audit_cohort(cohort, raw, out):
    out.mkdir(parents=True, exist_ok=True)
    fits_primary, checks_primary, hosts = [], [], []
    coverage = Counter()
    archive_cases = []
    matched = 0
    with (out/"discrepancies.csv").open("w", newline="") as log, \
         (out/"z-adjustments.csv").open("w", newline="") as adjustments:
        audit = Audit(log)
        changed = csv.writer(adjustments, lineterminator="\n")
        changed.writerow(("role", "Index", "Analyte", "arm", "extraction", "local_z_upper", "cohort_z_upper"))
        refs = audit.run("reference", cohort, read_reference, cohort)
        if refs is None:
            (out/"audit.json").write_text(json.dumps({"passed": False, "cohort": cohort,
                "error": "Invalid frozen reference; see discrepancies.csv"})+"\n")
            raise ValueError("Invalid frozen RIbench reference")
        ids, design = refs[:2]
        roles = ("primary", "other")
        groups = {role: zero_groups(raw, role, audit) for role in roles}
        for shard in range(1, 49):
            dirs = {r: raw / f"{r}-{shard}" for r in ("primary", "repeat", "other")}
            hosts.append(host_proof(dirs, shard, audit))
            cases = ids[shard-1::48]
            wanted = {(str(i), arm) for i in cases for arm in ARMS}
            wanted_checks = {(*k, "guidance", s) for k in wanted for s in SEEDS}
            tables = {}
            for role in roles:
                d = dirs[role]
                fits = audit.run(role, shard, table, d/"fits.csv", FIT_KEY) or {}
                checks = audit.run(role, shard, table, d/"checks.csv", CHECK_KEY) or {}
                audit.keys(role, (shard, "fits"), fits, wanted)
                audit.keys(role, (shard, "checks"), checks, wanted_checks)
                audit.run(role, shard, finalize_scores, fits, groups[role], changed, role)
                for idx in cases:
                    i = str(idx)
                    audit.run(role, i, check_case, fits, checks, design[i,], (d.name, i))
                    before = audit.failures
                    if (i, "baseline") in fits:
                        audit.run(role, i, compare_baseline, role, fits[i, "baseline"], checks, refs, audit)
                    else:
                        audit.change(role, i, "archive match", "baseline fit", "missing", False)
                    if role == "primary":
                        okay = before == audit.failures
                        matched += okay
                        archive_cases.append(dict(Index=i, stage1_status=refs[2][i,]["fit_valid"],
                            fresh_status=fits.get((i, "baseline"), {}).get("fit_status", "missing"),
                            stage0_reference=cohort == "small", archive_match=okay))
                tables[role] = fits, checks
                if role == "primary":
                    fits_primary.extend(fits.values())
                    checks_primary.extend(checks.values())
                    for r in fits.values():
                        for e in EXTRACTIONS:
                            category = "returned" if r[e+"_nonfinite"] == "FALSE" else "unavailable"
                            coverage[r["arm"], e, r["fit_status"], category] += 1
            first, checks = tables["primary"]
            other, other_checks = tables["other"]
            audit.run("cross_host", shard, cross_pair, first, other, checks, other_checks, audit)
        for idx, row in enumerate(hosts):
            prev = hosts[idx-1]
            needed = ("other_boot", "other_platform", "other_pid")
            if all(k in row for k in needed) and all(k in prev for k in (
                    "primary_boot", "primary_platform", "primary_pid", "repeat_pid")):
                ok = (row["other_boot"] == prev["primary_boot"] and
                      row["other_platform"] == prev["primary_platform"] and
                      row["other_pid"] not in (prev["primary_pid"], prev["repeat_pid"]))
                if not ok:
                    audit.change("host", idx+1, "ring provenance", "predecessor VM and separate PID", row, False)
        if matched != len(ids):
            audit.change("stage1", cohort, "baseline inclusion/reproduction", len(ids), matched, False)
    passed = audit.failures == 0
    max_cross = audit.maxima["cross_host"]
    summary = dict(passed=passed, cohort=cohort, datasets=len(ids), fits=len(fits_primary),
        checks=len(checks_primary), archived_baseline_matches=matched,
        requested_endpoints=sum(len(sides(d)) for d in design.values()), archive_stage0=cohort == "small",
        exact_repeat_shards=sum(h["exact"] for h in hosts), distinct_host_shards=sum(h["distinct"] for h in hosts),
        max_p_difference=max_cross.get("p", 0.0), max_endpoint_fraction=max_cross.get("endpoint_fraction", 0.0),
        max_differences=dict(audit.maxima), differing_fields=dict(audit.differences),
        discrepancies=audit.failures, score_groups_with_zero_upper={r: sorted(groups[r]) for r in roles},
        extraction_coverage=[dict(arm=a, extraction=x, fit_status=s, interval=v, count=count)
                             for (a,x,s,v), count in sorted(coverage.items())])
    # Missing records are logged explicitly. The report consumes complete
    # audited tables only after the technical gate passes.
    (out/"audit.json").write_text(json.dumps(summary, indent=2)+"\n")
    host_fields = sorted(set().union(*(row.keys() for row in hosts)))
    write_rows(out/"audit-shards.csv", [{f: r.get(f, "") for f in host_fields} for r in hosts])
    write_rows(out/"archive-cases.csv", sorted(archive_cases, key=lambda r: int(r["Index"])))
    require(passed, f"{cohort}: {audit.failures} failed audit comparisons; see discrepancies.csv")
    write_rows(out/"fits.csv", sorted(fits_primary, key=lambda r: (int(r["Index"]), r["arm"])))
    write_rows(out/"checks.csv", sorted(checks_primary, key=lambda r: (int(r["Index"]), r["arm"], r["seed_kind"])))
    print(json.dumps({"cohort": cohort, "passed": passed, "datasets": len(ids), "archived_baseline_matches": matched}))


if __name__ == "__main__":
    audit_cohort(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]))
