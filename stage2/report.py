"""Report frozen Stage 2 development fits and choose K before confirmation.

Usage: python stage2/report.py merged_dir output_dir
"""
import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import product
from pathlib import Path

os.environ["OPENBLAS_NUM_THREADS"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage1.report import Bootstrap, average, ensure, logical, num, quantile, read_rows
import numpy as np

ARMS = ("baseline", "K24", "K28")
EXTRACTIONS = ("native", "historical")
PANELS = ("guidance", "diagnostic")
SEEDS = ("primary", "alternate")
N_GROUPS = ("1500", "50000")
TARGET = ">20%"
CONTROL = "<=20%"


@dataclass
class Estimates:
    z: np.ndarray
    finite: np.ndarray
    out: np.ndarray
    unordered: np.ndarray
    absolute: np.ndarray
    maximum: np.ndarray
    capped: np.ndarray


@dataclass
class Arm:
    fit_valid: np.ndarray
    fallback: np.ndarray
    reasons: np.ndarray
    checks: dict
    estimates: dict


def load(root):
    fit_rows = read_rows(root / "fits.csv")
    check_rows = read_rows(root / "checks.csv")
    checks = {(int(r["j"]), r["arm"], r["panel"], r["seed_kind"]): r
              for r in check_rows}
    n = 1440
    expected = set(product(range(1, n + 1), ARMS, PANELS, SEEDS))
    ensure(set(checks) == expected, "Missing or unexpected check keys")
    ensure(len(check_rows) == len(expected), "Duplicate checks")
    fits = {(int(r["j"]), r["arm"]): r for r in fit_rows}
    ensure(set(fits) == set(product(range(1, n + 1), ARMS)) and len(fit_rows) == n * 3,
           "Incomplete or duplicate fits")
    jj = range(1, n + 1)
    metadata = [fits[j, "baseline"] for j in jj]
    cell_ids = [int(r["cell_id"]) for r in metadata]
    ensure(len(set(cell_ids)) == 360 and set(Counter(cell_ids).values()) == {4},
           "Expected four development replicates per factorial cell")
    arms = {}
    for arm in ARMS:
        rows = [fits[j, arm] for j in jj]
        for f in ("N", "fraction", "family", "disease", "rounding_fraction", "replicate", "cell_id",
                  "routine_hash", "anchor_hash", "diagnostic_hash"):
            ensure(all(r[f] == ref[f] for r, ref in zip(rows, metadata)), f"Unpaired inputs: {arm}/{f}")
        flags = np.array([r["fit_status"] for r in rows])
        ensure(set(flags) <= {"ResultFound", "fit_failed"}, f"Unknown fit status in {arm}")
        fit_valid = flags == "ResultFound"
        fallback = np.array([logical(r["fallback"]) for r in rows])
        reasons = np.array([r["reason"] for r in rows])
        statuses = {}
        estimates = {}
        for panel, seed in product(PANELS, SEEDS):
            status = np.array([checks[j, arm, panel, seed]["status"] for j in jj])
            ensure(set(status) <= {"keep", "decline", "check_failed", "fit_failed"}
                   and np.array_equal(status == "fit_failed", ~fit_valid), f"Invalid check status: {arm}")
            statuses[panel, seed] = status
        for ext in EXTRACTIONS:
            ends = ("lower", "upper")
            lim = np.array([[num(r[f"{ext}_{e}"]) for e in ends] for r in rows])
            z = np.array([[num(r[f"{ext}_z_{e}"]) for e in ends] for r in rows])
            finite = np.all(np.isfinite(lim), axis=1)
            ensure(np.array_equal(~finite, [logical(r[f"{ext}_nonfinite"]) for r in rows]),
                   "Nonfinite flag and limits differ")
            ensure(not np.any(finite & ~fit_valid), "Failed fit with finite endpoints")
            ensure(not np.any(np.isnan(z[finite])), "Returned finite limit missing a score")
            out = np.any(np.isfinite(lim) & (lim <= 0), axis=1)
            unordered = finite & (lim[:, 0] >= lim[:, 1])
            for (panel, seed), status in statuses.items():
                released = np.array([[num(checks[j, arm, panel, seed][f"released_{ext}_{e}"])
                                      for e in ends] for j in jj])
                expected_ri = np.where(((status == "keep") & finite)[:, None], lim, np.nan)
                ensure(np.array_equal(released, expected_ri, equal_nan=True),
                       f"Released endpoints differ from decision: {arm}/{ext}/{panel}/{seed}")
            abs_z = np.abs(z)
            estimates[ext] = Estimates(z, finite, out, unordered, abs_z.mean(axis=1),
                                       abs_z.max(axis=1), np.minimum(abs_z, 5).mean(axis=1))
        arms[arm] = Arm(fit_valid, fallback, reasons, statuses, estimates)
    return metadata, arms


def strata(rows):
    ns = np.array([r["N"] for r in rows])
    path = np.where(np.array([float(r["fraction"]) for r in rows]) > .2, TARGET, CONTROL)
    all_rows = np.ones(len(rows), dtype=bool)
    for n, p in product(("all", *N_GROUPS), ("all", TARGET, CONTROL)):
        mask = (all_rows if n == "all" else ns == n) & (all_rows if p == "all" else path == p)
        ensure(mask.any(), f"Empty prespecified stratum: {n}/{p}")
        yield dict(N_group=n, pathology=p, factor="all", level="all"), mask
    for key in ("fraction", "disease", "family", "rounding_fraction"):
        # Decimal strings preserve input precision in the case files; use readable labels here.
        values = np.array([str(float(r[key])) if key in {"fraction", "rounding_fraction"} else r[key]
                           for r in rows])
        for value in sorted(set(values)):
            for p in ("all", TARGET, CONTROL):
                mask = (values == value) & (all_rows if p == "all" else path == p)
                if mask.any():
                    yield dict(N_group="all", pathology=p, factor=key, level=value), mask


def cluster_interval(boot, numerators, denominator):
    point, samples, _, k = boot.ratio(numerators, denominator)
    lo, hi, valid = boot.interval(samples, k)
    return dict(value=point, ci_low=lo, ci_high=hi, informative_cells=k,
                bootstrap_valid=valid, bootstrap_undefined=len(samples) - valid)


def rate(tables, name, key, boot, event, eligible):
    count = event & eligible
    tables[name].append(dict(**key, count=int(count.sum()), denominator=int(eligible.sum()),
                             **cluster_interval(boot, count, eligible)))


def views(data, model):
    all_rows = np.ones_like(data.fit_valid)
    keep = data.checks["guidance", "primary"] == "keep"
    result = {}
    for mode, selected in (("pre", all_rows), ("checked", keep)):
        returned = selected & model.finite
        result[mode] = (returned, np.where(returned, model.capped, 5.0))
    return result


def check_metrics(tables, key, boot, arm, model, mask):
    known = model.finite[mask]
    all_rows = np.ones_like(known)
    valid_fit = arm.fit_valid[mask]
    for (panel, seed), statuses in arm.checks.items():
        status = statuses[mask]
        tested = np.isin(status, ["keep", "decline"])
        decline = status == "decline"
        d = dict(**key, panel=panel, seed=seed)
        for metric, event, eligible in (
                ("declined_all", decline, all_rows), ("declined_valid_fit", decline, valid_fit),
                ("declined_evaluable", decline, tested), ("fit_failure", ~valid_fit, all_rows),
                ("check_failure", status == "check_failed", valid_fit)):
            rate(tables, "panel-rates", dict(**d, unit="dataset", metric=metric), boot, event, eligible)
        for unit, err in (("dataset", model.maximum[mask]), ("lower", abs(model.z[mask, 0])),
                          ("upper", abs(model.z[mask, 1]))):
            for metric, eligible in (("bad_gt1", err > 1), ("bad_gt5", err > 5), ("good_lt0.25", err < .25)):
                for suffix, population in (("", known), ("_evaluable", known & tested)):
                    rate(tables, "panel-rates", dict(**d, unit=unit, metric=metric + suffix),
                         boot, decline, eligible & population)


def flip_metrics(tables, key, boot, arm, mask):
    pairs = [(p, "primary", p, "alternate") for p in PANELS]
    pairs += [("guidance", s, "diagnostic", s) for s in SEEDS]
    for p1, s1, p2, s2 in pairs:
        a, b = arm.checks[p1, s1][mask], arm.checks[p2, s2][mask]
        evaluated = np.isin(a, ["keep", "decline"]) & np.isin(b, ["keep", "decline"])
        rate(tables, "decision-pairs",
             dict(**key, panel_a=p1, seed_a=s1, panel_b=p2, seed_b=s2,
                  keep_to_decline=int(((a == "keep") & (b == "decline")).sum()),
                  decline_to_keep=int(((a == "decline") & (b == "keep")).sum()),
                  any_status_different=int((a != b).sum()), planned=len(a)),
             boot, a != b, evaluated)


def accuracy(tables, key, boot, mask, arm, model, mode, returned, loss):
    ret = returned[mask]
    eligible = model.finite[mask]
    # 'considered' includes all fits before the check and only kept fits after it.
    considered = np.ones_like(ret) if mode == "pre" else arm.checks["guidance", "primary"][mask] == "keep"
    raw = model.absolute[mask][ret]
    e = model.maximum[mask][ret]
    retained = model.capped[mask][ret]
    score = dict(planned=len(ret), fit_failures=int((~arm.fit_valid[mask]).sum()),
                 fallback=int(arm.fallback[mask].sum()), returned=int(ret.sum()),
                 nonreturns=int((~ret).sum()), nonfinite=int((considered & ~eligible).sum()),
                 unordered=int((ret & model.unordered[mask]).sum()), out_of_support=int((ret & model.out[mask]).sum()),
                 implausible=int((raw > 5).sum()), severe_E_gt5=int((e > 5).sum()),
                 kept_mean_abs_z=average(raw), kept_median_abs_z=quantile(raw, .5),
                 kept_capped_mean_abs_z=average(retained), all_set_loss=average(loss[mask]),
                 E_q50=quantile(e, .5), E_q90=quantile(e, .9), E_q95=quantile(e, .95), E_q99=quantile(e, .99))
    tables["accuracy"].append(dict(**key, mode=mode, **score))
    for pos, end in enumerate(("lower", "upper")):
        z = model.z[mask, pos][ret]
        with np.errstate(invalid="ignore"):
            tables["endpoints"].append(dict(**key, mode=mode, endpoint=end, planned=len(ret),
                scored=len(z), signed_mean_z=average(z), median_abs_z=quantile(abs(z), .5),
                mean_abs_z=average(abs(z)), capped_mean_abs_z=average(np.minimum(abs(z), 5))))
    rate(tables, "coverage", dict(**key, mode=mode), boot, ret, np.ones_like(ret))
    return score


def analyze(metadata, arms):
    tables = defaultdict(list)
    tables["fallback"] = []
    cells = np.array([int(r["cell_id"]) for r in metadata])
    rank = defaultdict(list)
    for group, mask in strata(metadata):
        boot = Bootstrap(cells[mask])
        scores = {}
        losses = {}
        for arm_name, arm in arms.items():
            d = dict(**group, arm=arm_name)
            flip_metrics(tables, d, boot, arm, mask)
            counts = Counter(arm.reasons[mask & arm.fallback])
            for reason, n in sorted(counts.items()):
                tables["fallback"].append(dict(**d, reason=reason, count=n, planned=int(mask.sum())))
            for ext, model in arm.estimates.items():
                key = dict(**d, extraction=ext)
                check_metrics(tables, key, boot, arm, model, mask)
                for mode, (returned, loss) in views(arm, model).items():
                    scores[arm_name, ext, mode] = accuracy(tables, key, boot, mask, arm, model, mode, returned, loss)
                    losses[arm_name, ext, mode] = loss[mask]
        for ext, arm_name in product(EXTRACTIONS, ARMS[1:]):
            for candidate_mode, baseline_mode in (("pre", "pre"), ("checked", "checked"), ("checked", "pre")):
                a_key, b_key = (arm_name, ext, candidate_mode), ("baseline", ext, baseline_mode)
                delta = losses[a_key] - losses[b_key]
                diff = cluster_interval(boot, delta, np.ones(len(delta), dtype=bool))
                a, b = scores[a_key], scores[b_key]
                d = dict(**group, arm=arm_name, extraction=ext, candidate_mode=candidate_mode,
                         baseline_mode=baseline_mode, planned=len(delta), candidate_loss=a["all_set_loss"],
                         baseline_loss=b["all_set_loss"], candidate_implausible=a["implausible"],
                         baseline_implausible=b["implausible"], candidate_nonreturns=a["nonreturns"],
                         baseline_nonreturns=b["nonreturns"], **diff)
                tables["paired-loss"].append(d)
                gate = group["N_group"] in N_GROUPS and group["pathology"] in (TARGET, CONTROL)
                if ext != "native" or not gate or candidate_mode != baseline_mode:
                    continue
                loss_ok = diff["value"] < 0 if group["pathology"] == TARGET else diff["value"] <= .02
                plaus_ok = a["implausible"] <= b["implausible"]
                nonreturn_ok = a["nonreturns"] <= b["nonreturns"]
                tables["gates"].append(dict(**d, loss_met=loss_ok, implausible_met=plaus_ok,
                                            nonreturns_met=nonreturn_ok, all_met=loss_ok and plaus_ok and nonreturn_ok))
                if group["pathology"] == TARGET and candidate_mode == "pre":
                    rank[arm_name].append((group["N_group"], diff["value"]))
    for arm_name in ARMS[1:]:
        by_n = dict(rank[arm_name])
        ensure(set(by_n) == set(N_GROUPS) and len(rank[arm_name]) == 2, "Missing N-specific ranking entries")
        tables["ranking"].append(dict(arm=arm_name, K=int(arm_name[1:]), delta_N1500=by_n["1500"],
                                      delta_N50000=by_n["50000"], worst_delta=max(by_n.values())))
    chosen = min(tables["ranking"], key=lambda r: (r["worst_delta"], -r["K"]))["K"]
    return tables, chosen


def render(tables, chosen):
    def pick(table, **filters):
        match = [row for row in tables[table]
                 if all(row[key] == value for key, value in filters.items())]
        ensure(len(match) == 1, f"Expected one {table} result for {filters}")
        return match[0]

    def number(x, decimals=4):
        return "—" if np.isnan(x) else f"{x:.{decimals}f}"

    def pct(r):
        return f"{r['count']}/{r['denominator']} ({100*r['value']:.1f}%)" if r["denominator"] else "0/0"

    def table(cols, rows):
        return ["", "| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |",
                *["| " + " | ".join(map(str, row)) + " |" for row in rows], ""]

    arm = f"K{chosen}"
    main = dict(factor="all", level="all", extraction="native")
    all_sets = dict(N_group="all", pathology="all", factor="all", level="all")
    primary = dict(**all_sets, extraction="native", panel="guidance", seed="primary", unit="dataset")
    lines = ["# Stage 2 development results", "",
             f"**K = {chosen} was selected** from 1,440 independent development datasets. "
             "The selection used the worse of the two sample-size differences in pre-check capped loss "
             "above 20% pathology. A lower difference favors the guided fit. An exact tie selects K = 28.",
             "", "## Candidate selection", ""]
    lines += table(["K", "Difference at N = 1,500", "Difference at N = 50,000", "Worse difference"],
                   [(r["K"], number(r["delta_N1500"], 6), number(r["delta_N50000"], 6),
                     number(r["worst_delta"], 6)) for r in tables["ranking"]])
    lines += ["## Native fits and checked releases", "",
              "Each formal comparison uses the corresponding refineR baseline. "
              "The release uses the original 40 anchors and the primary PIT seed. "
              "Each returned interval contributes the average of its two absolute endpoint errors capped at 5. "
              "A missing interval contributes 5. Implausible intervals have an uncapped mean absolute "
              "endpoint error above 5. The gates apply separately to each sample size and pathology group.",
              ""]
    rows = []
    for a, n, p, mode in product(ARMS[1:], N_GROUPS, (TARGET, CONTROL), ("pre", "checked")):
        r = pick("gates", **main, arm=a, N_group=n, pathology=p, candidate_mode=mode, baseline_mode=mode)
        rows.append((a, n, p, mode, number(r["candidate_loss"]), number(r["baseline_loss"]),
                     f"{number(r['value'])} [{number(r['ci_low'])}, {number(r['ci_high'])}]",
                     f"{r['candidate_implausible']} / {r['baseline_implausible']}",
                     f"{r['candidate_nonreturns']} / {r['baseline_nonreturns']}", "met" if r["all_met"] else "missed"))
    lines += table(["Arm", "N", "Pathology", "Mode", "Arm loss", "Baseline loss", "Difference [95% CI]",
                    "Implausible, arm / baseline", "Nonreturns, arm / baseline", "All gates"], rows)
    for mode, label in (("pre", "Pre-check fitter"), ("checked", "Checked release")):
        passed = all(r["all_met"] for r in tables["gates"] if r["arm"] == arm and r["candidate_mode"] == mode)
        verdict = "met" if passed else "missed"
        lines += [f"**{label}.** {arm} {verdict} the full set of development gates.", ""]
    lines += ["## Returned intervals", "",
              "Accuracy of returned intervals uses only finite endpoint pairs. Coverage and all-set loss "
              "use all assigned datasets, including fallback and fit failures.", ""]
    rows = []
    for a, mode in product(ARMS, ("pre", "checked")):
        r = pick("accuracy", **all_sets, extraction="native", arm=a, mode=mode)
        rows.append((a, mode, f"{r['returned']}/{r['planned']}", number(r["kept_capped_mean_abs_z"]),
                     number(r["all_set_loss"]), r["severe_E_gt5"], r["out_of_support"],
                     r["unordered"], r["nonfinite"], r["fallback"], r["fit_failures"]))
    lines += table(["Arm", "Mode", "Returned", "Returned capped loss", "All-set loss", "E > 5",
                    "Outside support", "Unordered", "Nonfinite", "Fallback", "Fit failures"], rows)
    lines += ["## Original and independent anchor panels", "",
              "Each fraction is the number declined divided by the number of valid pre-check fits in the "
              "error group. E is the larger absolute endpoint error. The diagnostic panel was sampled "
              "independently of fitting. Only the guidance panel determines the release.", ""]
    rows = []
    for a, panel, seed in product(ARMS, PANELS, SEEDS):
        d = dict(primary, arm=a, panel=panel, seed=seed)
        rows.append([a, panel, seed, *[pct(pick("panel-rates", **d, metric=m))
                                        for m in ("declined_all", "bad_gt1", "bad_gt5", "good_lt0.25")]])
    lines += table(["Arm", "Panel", "PIT seed", "All declined", "E > 1 caught", "E > 5 caught",
                    "E < 0.25 declined"], rows)
    rows = []
    for a in ARMS:
        for key in [("guidance", "primary", "guidance", "alternate"),
                    ("diagnostic", "primary", "diagnostic", "alternate"),
                    ("guidance", "primary", "diagnostic", "primary"),
                    ("guidance", "alternate", "diagnostic", "alternate")]:
            pa, sa, pb, sb = key
            r = pick("decision-pairs", **all_sets, arm=a, panel_a=pa, seed_a=sa, panel_b=pb, seed_b=sb)
            rows.append((a, f"{pa} {sa}", f"{pb} {sb}", pct(r), r["keep_to_decline"], r["decline_to_keep"]))
    lines += table(["Arm", "First check", "Second check", "Paired decisions changed",
                    "Keep → decline", "Decline → keep"], rows)
    lines += ["## Disease overlapping the healthy center", ""]
    rows = []
    for a, p, mode in product(ARMS, (TARGET, CONTROL), ("pre", "checked")):
        r = pick("accuracy", N_group="all", pathology=p, factor="disease", level="overlapping",
                 extraction="native", arm=a, mode=mode)
        rows.append((a, p, mode, f"{r['returned']}/{r['planned']}", number(r["all_set_loss"]), r["implausible"]))
    lines += table(["Arm", "Pathology", "Mode", "Returned", "All-set loss", "Implausible"], rows)
    lines += ["## Descriptive comparisons", "",
              "Checked candidate versus ungated refineR is reported separately from the like-for-like "
              "success comparisons. Historical C2 extraction is secondary.", ""]
    rows = []
    for a, p in product(ARMS[1:], (TARGET, CONTROL)):
        common = dict(N_group="all", pathology=p, factor="all", level="all", arm=a)
        desc = pick("paired-loss", **common, extraction="native", candidate_mode="checked", baseline_mode="pre")
        hist = pick("paired-loss", **common, extraction="historical", candidate_mode="pre", baseline_mode="pre")
        hist_checked = pick("paired-loss", **common, extraction="historical",
                            candidate_mode="checked", baseline_mode="checked")
        rows.append((a, p, number(desc["value"]), number(hist["value"]), number(hist_checked["value"])))
    lines += table(["Arm", "Pathology", "Native checked vs ungated", "Historical pre vs pre",
                    "Historical checked vs checked"], rows)
    lines += ["The CSV tables include all arms, both extractions, sample sizes, pathology groups, "
              "healthy families, disease patterns and rounding increments. Panel rates include denominators "
              "for all eligible valid fits and for evaluable checks. Rate and paired-difference intervals "
              "use 2,000 percentile bootstrap draws, resampling factorial cells with replicates together "
              "(PCG64 seed 37000000). The gate judgments use point estimates. This development report "
              "selects the candidate for independent confirmation.", ""]
    return "\n".join(lines)


def save(directory, tables, chosen):
    directory.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        columns = list(rows[0]) if rows else ["N_group", "pathology", "factor", "level", "arm",
                                              "reason", "count", "planned"]
        with (directory / f"{name}.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow({k: "" if isinstance(v, (float, np.floating)) and np.isnan(v) else v
                                 for k, v in row.items()})
    with (directory / "selection.json").open("w", encoding="utf-8") as f:
        json.dump(dict(chosen_K=chosen, development_datasets=1440, ranking=tables["ranking"]),
                  f, indent=2, allow_nan=False)
        f.write("\n")
    (directory / "REPORT.md").write_text(render(tables, chosen), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("merged_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    datasets, fits = load(args.merged_dir)
    tables, chosen = analyze(datasets, fits)
    save(args.output_dir, tables, chosen)
