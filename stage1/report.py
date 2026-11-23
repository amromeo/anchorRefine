"""Stage 1 reporting. Run with the frozen cohort CSVs (checks.csv and estimates.csv).

OPENBLAS_NUM_THREADS=1 python3 stage1/report.py --small PATH --large PATH --out PATH
Either cohort can be reported independently. Input Z has RIbench's truth-minus-estimate sign.
"""
import argparse
import csv
import math
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

os.environ["OPENBLAS_NUM_THREADS"] = "1"
import numpy as np

REPLICATES = 2000
SEED = 37000000
EXTRACTIONS = ("historical", "native")
SEEDS = ("primary", "secondary")
LABELS = {
    "refineR": "refineR alone",
    "gate": "refineR with anchor check",
    "anchorsOnly": "Anchors only",
    "anchoredRI_old": "anchoredRI (C2 old fitter)",
    "anchoredRI_taskE_raw": "anchoredRI (Task E raw)",
    "anchoredRI_taskE_reported": "anchoredRI (Task E reported)",
}
BASE_METHODS = {"refineR", "anchorsOnly", "anchoredRI_old"}


def ensure(condition, message):
    if not condition:
        raise ValueError(message)


def num(value):
    return np.nan if value in (None, "", "NA", "NaN") else float(value)


def logical(value):
    if value in ("TRUE", "True", "1"):
        return True
    if value in ("FALSE", "False", "0"):
        return False
    raise ValueError(f"Expected a logical, found {value!r}")


def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def quantile(values, prob):
    """R type 7 percentile. Infinities count as values, including a tied infinite tail."""
    ordered = np.sort(values[~np.isnan(values)])
    if not len(ordered):
        return math.nan
    x = (len(ordered) - 1) * prob
    left, right = ordered[math.floor(x)], ordered[math.ceil(x)]
    if left == right or math.floor(x) == math.ceil(x):
        return float(left)
    if np.isinf(right):
        return float(right)
    return float(left + (x % 1) * (right - left))


def average(values):
    return float(np.mean(values)) if len(values) else math.nan


@dataclass
class Method:
    z: np.ndarray
    estimate: np.ndarray
    truth: np.ndarray
    status: np.ndarray
    paired: np.ndarray
    returned: np.ndarray
    scored: np.ndarray
    maximum: np.ndarray
    absolute: np.ndarray
    capped: np.ndarray
    lower_needed: np.ndarray

    def subset(self, idx):
        return Method(**{k: v[idx] for k, v in vars(self).items()})

    def gated(self, keep, decisions=None):
        status = self.status
        if decisions is not None:
            status = status.copy()
            status[decisions=="decline", :] = "declined"
            status[decisions=="check_failed", :] = "unavailable"
        return Method(**{**vars(self), "returned": self.returned & keep,
                         "scored": self.scored & keep, "status": status})


def cohort_data(root, cohort):
    checks = sorted(read_rows(root / "checks.csv"), key=lambda r: int(r["Index"]))
    position = {int(r["Index"]): i for i, r in enumerate(checks)}
    n = len(checks)
    ensure(n == len(position) == (2880 if cohort == "small" else 1440),
           f"Duplicate or missing Index in {cohort} checks")
    allowed_n = {1000: 1440, 5000: 1440} if cohort == "small" else {50000: 1440}
    for nominal, expected in allowed_n.items():
        ensure(sum(int(r["N"]) == nominal for r in checks) == expected, "Wrong cohort N")
    not_crp = np.array([r["Analyte"] != "CRP" for r in checks])
    shape = (n, 2)
    tables = {}
    for row in read_rows(root / "estimates.csv"):
        key = row["extraction"], row["method"]
        ensure(key[0] in EXTRACTIONS and key[1] in LABELS and key[1] != "gate", str(key))
        if key not in tables:
            tables[key] = (np.full(shape, np.nan), np.full(shape, np.nan), np.full(shape, np.nan),
                           np.full(shape, "", dtype=object), np.zeros(shape, dtype=bool))
        z, estimate, truth, status, paired = tables[key]
        i = position[int(row["Index"])]
        info = checks[i]
        ensure(all(row[k] == info[k] for k in ("Analyte", "Scenario")) and
               int(row["N"]) == int(info["N"]) and
               float(row["fractionPathol"]) == float(info["fractionPathol"]), "Index mismatch")
        j = {"lower": 0, "upper": 1}[row["endpoint"]]
        ensure(not_crp[i] or j == 1, "Unexpected CRP lower limit")
        ensure(float(row["probability"]) == ((0.025, 0.975)[j] if not_crp[i] else 0.95),
               "Incorrect endpoint probability")
        ensure(status[i, j] == "", f"Duplicate estimate {key}, Index {row['Index']}")
        status[i, j] = row["status"]
        ensure(status[i, j] in {"returned", "unavailable", "unmatched", "declined"},
               f"Unknown estimate status {status[i,j]!r}")
        z[i, j], estimate[i, j], truth[i, j] = (num(row[k]) for k in ("z", "estimate", "truth"))
        paired[i, j] = logical(row["paired"])
    methods = {}
    for key, (z, estimate, truth, status, paired) in tables.items():
        ensure(np.all(status[:, 1] != "") and np.all(status[not_crp, 0] != ""),
               f"Incomplete requested endpoint inventory for {key}")
        # Require every requested limit for an interval. A CRP set contributes just its upper.
        ret = (status[:, 1] == "returned") & (~not_crp | (status[:, 0] == "returned"))
        ret &= np.isfinite(estimate[:, 1]) & (~not_crp | np.isfinite(estimate[:, 0]))
        paired = paired[:, 1] & (~not_crp | paired[:, 0])
        scored = ret & ~np.isnan(z[:, 1]) & (~not_crp | ~np.isnan(z[:, 0]))
        lower, upper = np.abs(z[:, 0]), np.abs(z[:, 1])
        maximum = np.where(not_crp, np.maximum(lower, upper), upper)
        absolute = np.where(not_crp, (upper + lower) / 2, upper)
        capped = np.where(not_crp, (np.minimum(5, lower) + np.minimum(5, upper)) / 2,
                          np.minimum(5, upper))
        methods[key] = Method(z, estimate, truth, status, paired, ret, scored, maximum,
                              absolute, capped, not_crp)
    ids = {m for e, m in methods}
    ensure(BASE_METHODS <= ids and all((e, m) in methods for e in EXTRACTIONS for m in ids),
           "Missing comparator/extraction")
    # The comparator's single estimation formula is repeated in both analyses.
    for m in ids - {"refineR"}:
        for k in ("z", "estimate", "truth", "status", "paired"):
            a = getattr(methods["historical", m], k)
            b = getattr(methods["native", m], k)
            ensure(np.array_equal(a, b, equal_nan=True) if a.dtype.kind == "f" else np.array_equal(a, b),
                   f"{m} changed across extraction analyses")
    for row in checks:
        for s in SEEDS:
            decision = row[s + "_status"]
            p = num(row[s + "_p"])
            ensure(decision in {"keep", "decline", "check_failed"}, "Unknown anchor decision")
            if decision != "check_failed":
                ensure(np.isfinite(p) and 0 <= p <= 1 and (p < 0.01) == (decision == "decline"),
                       f"Inconsistent decision for {row['Index']}")
    return checks, methods


class Bootstrap:
    """Identical paired weights for every analysis of a stratum."""
    def __init__(self, keys):
        ordered = sorted(set(keys))
        mapping = {k: i for i, k in enumerate(ordered)}
        self.group = np.array([mapping[k] for k in keys])
        self.k = len(ordered)
        rng = np.random.Generator(np.random.PCG64(SEED))
        self.weights = rng.multinomial(self.k, np.full(self.k, 1.0 / self.k),
                                       size=REPLICATES).astype(float)

    def totals(self, values):
        return np.bincount(self.group, weights=values.astype(float), minlength=self.k)

    def ratio(self, numerator, denominator):
        a, b = self.totals(numerator), self.totals(denominator)
        observed = a.sum() / b.sum() if b.sum() else np.nan
        balanced = average(a[b>0] / b[b>0])
        with np.errstate(invalid="ignore", divide="ignore"):
            samples = self.weights @ a / (self.weights @ b)
        return observed, samples, balanced, int(np.count_nonzero(b))

    @staticmethod
    def interval(samples, informative):
        valid = samples[np.isfinite(samples)]
        if informative < 2 or not len(valid):
            return np.nan, np.nan, len(valid)
        lo, hi = np.quantile(valid, [0.025, 0.975])
        return lo, hi, len(valid)


def strata(checks):
    groups = defaultdict(list)
    for i, r in enumerate(checks):
        path = ">20%" if float(r["fractionPathol"]) > .20 else "<=20%"
        n, marker, scenario = r["N"], r["Analyte"], r["Scenario"]
        for kind, value in [("all", "All"), ("pathology", path), ("N", n), ("scenario", scenario),
                            ("analyte", marker), ("N/pathology", f"{n}/{path}"),
                            ("scenario/pathology", f"{scenario}/{path}"),
                            ("analyte/scenario", f"{marker}/{scenario}")]:
            groups[kind, value].append(i)
    return groups


def rate(tables, d, boot, name, positive, eligible, unit="dataset"):
    numerator = positive & eligible
    val, dist, balanced, k = boot.ratio(numerator, eligible)
    lo, hi, reps = boot.interval(dist, k)
    tables["rates"].append(dict(**d, metric=name, unit=unit, numerator=int(numerator.sum()),
                denominator=int(eligible.sum()), estimate=val, ci_low=lo, ci_high=hi,
                scenario_balanced=balanced, informative_clusters=k, bootstrap_valid=reps))


def check_metrics(tables, d, boot, base, decisions, reasons, valid_fit):
    all_rows = np.ones(len(decisions), bool)
    keep, decline = decisions == "keep", decisions == "decline"
    tested = keep | decline
    rate(tables, d, boot, "decline", decline, tested)
    rate(tables, d, boot, "nonreturn", ~(keep & base.returned), all_rows)
    rate(tables, d, boot, "fit_failure", ~valid_fit, all_rows)
    rate(tables, d, boot, "check_failed_after_valid_fit", ~tested & valid_fit, all_rows)
    rate(tables, d, boot, "check_failed_any", ~tested, all_rows)
    rate(tables, d, boot, "structural_incompatibility", reasons == "structural_incompatibility", all_rows)
    rate(tables, d, boot, "unscored_valid_baseline", ~base.scored, valid_fit)
    for unit, err, known in [("dataset", base.maximum, valid_fit & base.scored),
                             ("lower", abs(base.z[:,0]), valid_fit & base.lower_needed & base.returned & ~np.isnan(base.z[:,0])),
                             ("upper", abs(base.z[:,1]), valid_fit & base.returned & ~np.isnan(base.z[:,1]))]:
        for label, threshold, group in [("bad_gt1", 1, err > 1), ("bad_gt5", 5, err > 5),
                                         ("good_lt0.25", .25, err < .25)]:
            classified = known & group
            rate(tables, d, boot, "declined_" + label, decline, classified, unit)
            rate(tables, d, boot, "declined_" + label + "_evaluable", decline, classified & tested, unit)
            tables["boundary-counts"].append(dict(**d, unit=unit, threshold=threshold,
                equal=int((known & (err == threshold)).sum()), scored=int(known.sum())))


def accuracy(tables, d, boot, m, selected):
    scored = selected & m.scored
    absolute = m.absolute[scored]
    maximum = m.maximum[scored]
    loss = m.capped[scored]
    old = absolute <= 5
    unordered = np.where(m.lower_needed, m.estimate[:,1] <= m.estimate[:,0], m.estimate[:,1] <= 0)
    binary = dict(unordered_or_zero_width=(unordered, selected & m.returned), returned=(m.returned, selected), severe_gt5=(m.maximum>5, scored),
                  bad_gt1=(m.maximum>1, scored), c2_implausible=(m.absolute>5, scored))
    for label, (positive, eligible) in binary.items():
        rate(tables, d, boot, "accuracy_" + label, positive, eligible)
    penalty = np.where(m.scored, m.capped, 5.0)
    info = dict(planned=int(selected.sum()), paired=int((selected & m.paired).sum()),
                returned=int((selected & m.returned).sum()), scored=int(scored.sum()),
                declined_by_method=int((selected & (m.status[:,1]=="declined")).sum()),
                unmatched=int((selected & ~m.paired).sum()),
                mean_abs_z=average(absolute), median_abs_z=quantile(absolute, .5),
                mean_capped_abs_z=average(loss), c2_mean_abs_z_excluding_gt5=average(absolute[old]),
                c2_included=int(old.sum()), penalty5_mean=average(penalty[selected]))
    for prob in (0.50, .90, .95, .99):
        info["E_q" + str(round(100*prob))] = quantile(maximum, prob)
    info["scenario_balanced_capped"] = boot.ratio(np.where(scored, m.capped, 0),scored)[2]
    info["scenario_balanced_penalty5"] = boot.ratio(np.where(selected,penalty,0),selected)[2]
    tables["accuracy"].append(dict(**d, **info))
    for j, end in enumerate(("lower", "upper")):
        ok = scored & (m.lower_needed if j == 0 else True)
        vals = m.z[ok,j]
        # Physical bias only within an analyte; mixed analytes can have incompatible units.
        bias_units = average(m.truth[ok,j] - m.estimate[ok,j]) if d["group"] in (
            "analyte", "analyte/scenario") else np.nan
        with np.errstate(invalid="ignore"):
            signed = average(vals)
        tables["endpoints"].append(dict(**d, endpoint=end, n=len(vals), mean_signed_z=signed,
            mean_error_in_analyte_units=bias_units, mean_abs_z=average(abs(vals)),
            median_abs_z=quantile(abs(vals),.5), mean_capped_abs_z=average(np.minimum(abs(vals),5))))


def paired_contrast(tables, d, boot, lhs, rhs, index_mask, name, mode):
    matched = index_mask & lhs.paired & rhs.paired
    a_ok, b_ok = matched & lhs.scored, matched & rhs.scored
    a_loss, b_loss = lhs.capped, rhs.capped
    if mode == "common":
        a_ok = b_ok = a_ok & b_ok
    elif mode == "penalized":
        a_loss = np.where(lhs.scored, lhs.capped, 5)
        b_loss = np.where(rhs.scored, rhs.capped, 5)
        a_ok = b_ok = matched
    a, ax, ab, ka = boot.ratio(np.where(a_ok, a_loss, 0), a_ok)
    b, bx, bb, kb = boot.ratio(np.where(b_ok, b_loss, 0), b_ok)
    lo, hi, reps = boot.interval(ax-bx, min(ka,kb))
    tables["paired-loss"].append(dict(**d, comparison_set=name, planned=int(index_mask.sum()),
        matched=int(matched.sum()), n_lhs=int(a_ok.sum()), n_rhs=int(b_ok.sum()),
        lhs_capped_mean=a, rhs_capped_mean=b, difference=a-b, ci_low=lo, ci_high=hi,
        scenario_balanced_difference=ab-bb, informative_clusters_lhs=ka,
        informative_clusters_rhs=kb, bootstrap_valid=reps))


def analyze(root, cohort, tables):
    checks, methods = cohort_data(root, cohort)
    full_keys = [(r["Analyte"],r["Scenario"]) for r in checks]
    all_dec = {s:np.array([r[s+"_status"] for r in checks]) for s in SEEDS}
    all_reasons = {s:np.array([r[s+"_reason"] for r in checks]) for s in SEEDS}
    all_valid = np.array([logical(r["fit_valid"]) for r in checks])
    for (kind, group), indices in strata(checks).items():
        ids = np.asarray(indices)
        boot = Bootstrap([full_keys[i] for i in indices])
        d = dict(cohort=cohort, group=kind, stratum=group)
        any_case = np.ones(len(ids),bool)
        dec = {s:all_dec[s][ids] for s in SEEDS}
        both = (dec["primary"] != "check_failed") & (dec["secondary"] != "check_failed")
        changed = dec["primary"] != dec["secondary"]
        for metric, positive, eligible in [
                ("flip",changed,both), ("flip_all_planned",changed & both,any_case),
                ("status_change_any",changed,any_case),
                ("keep_to_decline",(dec["primary"]=="keep") & (dec["secondary"]=="decline"),both),
                ("decline_to_keep",(dec["primary"]=="decline") & (dec["secondary"]=="keep"),both)]:
            rate(tables, dict(**d, extraction="shared", seed="both", method="gate", population="all"),
                 boot,metric,positive,eligible)
        for extraction in EXTRACTIONS:
            group_methods = {m:data.subset(ids) for (e,m),data in methods.items() if e==extraction}
            base = group_methods["refineR"]
            for m, model in group_methods.items():
                spec = dict(**d, extraction=extraction, seed="independent", method=m, population="all")
                accuracy(tables,spec,boot,model,any_case)
                if m != "refineR":
                    paired_contrast(tables,dict(**d,extraction=extraction,seed="independent",
                        lhs="refineR", rhs=m),boot,base,model,any_case,"both_scored","common")
            for seed in SEEDS:
                keep = dec[seed] == "keep"
                gated = base.gated(keep, dec[seed])
                part = dict(**d,extraction=extraction,seed=seed)
                spec = dict(**part, method="gate",population="all")
                check_metrics(tables,spec,boot,base,dec[seed],all_reasons[seed][ids],all_valid[ids])
                accuracy(tables,spec,boot,gated,any_case)
                for m, model in group_methods.items():
                    spec = dict(**part,method=m,population="gate_kept")
                    # For a paired kept-subset table, unmatched records cannot contribute estimates.
                    accuracy(tables,spec,boot,model.gated(model.paired & base.paired),keep)
                    pair = dict(**part,lhs="gate",rhs=m)
                    paired_contrast(tables,pair,boot,gated,model,keep,"kept_both_scored","common")
                    paired_contrast(tables,pair,boot,gated,model,any_case,"each_returned","own")
                    paired_contrast(tables,pair,boot,gated,model,any_case,"all_matched_penalty5","penalized")


def text_number(x):
    if isinstance(x, (float, np.floating)) and math.isnan(x):
        return ""
    return x


def outputs(directory, tables):
    import gzip
    import io
    directory.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        with (directory / (name+".csv.gz")).open("wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as zs:
                with io.TextIOWrapper(zs, encoding="utf-8", newline="") as stream:
                    w = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
                    w.writeheader()
                    w.writerows({k:text_number(v) for k,v in r.items()} for r in rows)


def report(tables, cohorts):
    pretty = {"small": "N ≤ 5,000", "large": "N = 50,000"}
    def pick(table, **conditions):
        matches = [r for r in tables[table] if all(r[k] == v for k,v in conditions.items())]
        ensure(len(matches)==1, "Report selector did not identify one row: "+str(conditions))
        return matches[0]
    def pct(v):
        return "–" if not np.isfinite(v) else f"{100*v:.1f}%"
    def f3(v):
        return "–" if np.isnan(v) else f"{v:.3f}"
    def fraction(r, interval=False):
        result = f"{r['numerator']:,}/{r['denominator']:,} ({pct(r['estimate'])})"
        if interval and np.isfinite(r["ci_low"]):
            result += f", 95% CI {pct(r['ci_low'])} to {pct(r['ci_high'])}"
        return result
    def getrate(d, metric):
        return pick("rates",**d,method="gate",population="all",unit="dataset",metric=metric)
    lines = ["# Stage 1 rounded-anchor results", "",
        "The anchor check keeps the original refineR limits when the randomized PIT likelihood-ratio "
        "test gives p ≥ 0.01. Each set uses one decision for both extraction formulas. The primary seed "
        "is 38000000 + Index. Estimates are paired with comparators by test set.", ""]
    for cohort in cohorts:
        common = dict(cohort=cohort,group="all",stratum="All")
        primary = dict(**common,extraction="historical",seed="primary")
        lines += [f"## {pretty[cohort]}", "",
            f"The primary check declined {fraction(getrate(primary,'decline'),True)} evaluable fits. "
            f"There were {getrate(primary,'fit_failure')['numerator']:,} invalid baseline fits, "
            f"{getrate(primary,'check_failed_after_valid_fit')['numerator']:,} check failures on valid fits, "
            f"and {getrate(primary,'structural_incompatibility')['numerator']:,} declines for a zero-probability "
            "measurement interval.", ""]
        seed_spec = dict(**common,extraction="shared",seed="both")
        flip = getrate(seed_spec,"flip")
        flip_all = getrate(seed_spec,"flip_all_planned")
        lines += [f"Changing the PIT seed to 39000000 + Index reversed {fraction(flip,True)} "
            f"decisions among sets evaluable twice ({fraction(flip_all)} of all planned). "
            f"{getrate(seed_spec,'keep_to_decline')['numerator']:,} changed from keep to decline and "
            f"{getrate(seed_spec,'decline_to_keep')['numerator']:,} from decline to keep. "
            f"The second seed declined {fraction(getrate(dict(**common,extraction='historical',seed='secondary'),'decline'))} "
            "evaluable fits.", ""]
        for extraction in EXTRACTIONS:
            meaning = "C2 historical limits (primary)" if extraction=="historical" else "Native refineR limits (secondary)"
            lines += ["### "+meaning, "",
                "Bad-result capture and good-result loss use the largest absolute endpoint z deviation (E). "
                "CRP contributes its upper endpoint. The denominators below include every classifiable valid "
                "baseline result in the indicated class, including any failed checks.", "",
                "| Pathological fraction | Declined / evaluable | Caught E > 1 | Caught E > 5 | Declined E < 0.25 | Kept / planned | Kept mean capped absolute z |",
                "|---|---:|---:|---:|---:|---:|---:|"]
            for group_kind, group in (("all","All"),("pathology","<=20%"),("pathology",">20%")):
                d = dict(cohort=cohort,group=group_kind,stratum=group,extraction=extraction,seed="primary")
                q = pick("accuracy",**d,method="gate",population="all")
                metrics = [fraction(getrate(d,m)) for m in ("decline","declined_bad_gt1","declined_bad_gt5",
                                                              "declined_good_lt0.25")]
                lines.append("| " + " | ".join([group.replace("<=","≤")] + metrics +
                    [f"{q['returned']:,}/{q['planned']:,}", f3(q['mean_capped_abs_z'])]) + " |")
            lines += ["","| Method | Returned / planned | Scored | Mean absolute z | Mean capped absolute z | E 95th percentile | Capped loss with 5 for no result | Capped mean on gate-kept sets |",
                      "|---|---:|---:|---:|---:|---:|---:|---:|"]
            available = [m for m in LABELS if any(r['cohort']==cohort and r['method']==m for r in tables["accuracy"])]
            for method in available:
                d = dict(**common,extraction=extraction,method=method)
                row = pick("accuracy",**d,population="all",seed="primary" if method=="gate" else "independent")
                kept = row if method=="gate" else pick("accuracy",**d,population="gate_kept",seed="primary")
                lines.append("| "+" | ".join([LABELS[method],f"{row['returned']:,}/{row['planned']:,}",
                    f"{row['scored']:,}",f3(row['mean_abs_z']),f3(row['mean_capped_abs_z']),
                    f3(row['E_q95']),f3(row['penalty5_mean']),f3(kept['mean_capped_abs_z'])])+" |")
            lines.append("")
    lines += ["## Reading the tables", "",
        "The capped loss clips each requested endpoint at 5, then averages within each dataset. The historical "
        "RIbench exclusion-based score drops datasets whose uncapped mean |z| exceeds 5. The files report both. "
        "The failure-penalized sensitivity assigns 5 to every unscored, failed or withheld result. "
        "The gate changes which results are returned, so the kept subset has the same refineR accuracy as "
        "ungated refineR on those same indices.", "",
        "All accuracy means weight datasets equally, including one-sided CRP. Signed bias uses truth minus estimate "
        "on the healthy z scale. Measurements with infinite z retain their severity and capped loss. A missing z "
        "leaves a returned result unscored. Full paired comparisons use verified matched inputs. "
        "The native analysis changes the refineR endpoint formula only. Comparator limits and both PIT decisions "
        "remain the same under both analyses.", "",
        "The 95% descriptive intervals use 2,000 paired cluster bootstrap resamples. Within each summary stratum "
        "the observed (Analyte, Scenario) groups are sampled with replacement as intact clusters using NumPy PCG64 "
        "seed 37000000. Undefined bootstrap ratios are omitted and their valid replicate count is shown. "
        "Intervals require at least two informative parent groups. Scenario-balanced estimates weight contributing "
        "groups equally. Strata overlap and their counts must not be added.", "",
        "| File | Contents |","|---|---|",
        "| [rates.csv.gz](rates.csv.gz) | Declines, failures, structural declines, both capture denominators, good losses, coverage, severity rates and seed reversals with uncertainty |",
        "| [accuracy.csv.gz](accuracy.csv.gz) | Own available and gate-kept populations, returned and scored denominators, loss, E quantiles, historical score and failure sensitivity |",
        "| [endpoints.csv.gz](endpoints.csv.gz) | Signed bias and mean, median and capped endpoint errors |",
        "| [paired-loss.csv.gz](paired-loss.csv.gz) | Paired differences in mean capped loss and bootstrap intervals for common-scored, separately returned and failure-penalized populations |",
        "| [boundary-counts.csv.gz](boundary-counts.csv.gz) | Counts exactly at each strict threshold for intervals and individual endpoints |", "",
        "Each file includes overall, pathological-fraction, individual N, analyte, and Scenario rows. "
        "The raw and reported Task E rows, when present, distinguish its selected fits from outputs released by "
        "its original safeguard. The C2 old-fitter row is the historical anchoredRI comparator.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--small",type=Path)
    parser.add_argument("--large",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    args = parser.parse_args()
    inputs = {name:path for name,path in [("small",args.small),("large",args.large)] if path is not None}
    if not inputs:
        parser.error("Supply at least one cohort")
    tables = defaultdict(list)
    for name, path in inputs.items():
        analyze(path,name,tables)
    outputs(args.out,tables)
    (args.out/"REPORT.md").write_text(report(tables,inputs),encoding="utf-8")


if __name__ == "__main__":
    main()
