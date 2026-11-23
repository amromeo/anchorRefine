"""Report the fixed K24 development ablations from the audited merged case files.

Usage: python stage2/ablation-report.py MERGED_DIR OUTPUT_DIR
"""
import argparse
import csv
import gzip
import os
import sys
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

os.environ["OPENBLAS_NUM_THREADS"] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stage2.report import Bootstrap, SEEDS, cluster_interval, ensure, logical, np, num

ARCHIVE = ROOT / "results/stage2-development-45283676579/evidence"
ARMS = ("baseline", "K24", "peak", "start", "region")
EXT = ("native", "historical")
NAMES = {"baseline": "Unchanged refineR", "K24": "Full K24", "peak": "Peak only",
         "start": "Starting values only", "region": "Search regions only"}
KEYS = ("j", "cell_id", "replicate", "N", "fraction", "disease", "family", "rounding_fraction",
        "routine_hash", "anchor_hash", "diagnostic_hash", "fitter_seed", "pit_primary_seed",
        "pit_alternate_seed", "diagnostic_primary_seed", "diagnostic_alternate_seed")
IDS = range(1, 1441)
FITS = ("fit_hash", "fit_status", "fallback", "reason", "election_reason", "clarity",
        "peak_index", "fit_upstream_status",
        *(f"{e}_{field}" for e in EXT for field in ("lower","upper","z_lower","z_upper","nonfinite")))


def records(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def index(rows, keys, arms):
    kept = [r for r in rows if r["arm"] in arms]
    result = {tuple(int(r[k]) if k == "j" else r[k] for k in keys): r for r in kept}
    ensure(len(kept) == len(result), "Duplicate rows for " + str(keys))
    return result


def equal_field(a, b):
    if a == b:
        return True
    try:
        x, y = num(a), num(b)
        return (np.isnan(x) and np.isnan(y)) or x == y
    except ValueError:
        return False


def load(directory):
    merged = index(records(directory / "fits.csv"), ("j", "arm"), ARMS)
    ensure(set(merged) == set(product(IDS, ARMS)), "Missing one or more planned development fits")
    saved = index(records(ARCHIVE / "fits.csv.gz"), ("j", "arm"), ARMS[:2])
    ensure(set(saved) == set(product(IDS, ARMS[:2])), "Incomplete archived comparators")
    for key, old in saved.items():
        new = merged[key]
        ensure(all(equal_field(old[f], new[f]) for f in (*KEYS, *FITS)),
               f"Development comparator changed at {key}")
    checks = index(records(ARCHIVE / "checks.csv.gz"), ("j","arm","panel","seed_kind"), ARMS[:2])
    merged_checks = index(records(directory / "checks.csv"), ("j","arm","panel","seed_kind"), ARMS[:2])
    ensure(set(merged_checks) == set(checks) == set(product(IDS, ARMS[:2], ("guidance","diagnostic"), SEEDS)),
           "Incomplete paired panel records")
    for key, row in checks.items():
        ensure(all(equal_field(row[f], merged_checks[key][f]) for f in ("seed","p","status","reason")),
               f"Panel check changed at {key}")
        valid_fit = saved[key[:2]]["fit_status"] == "ResultFound"
        ensure(row["status"] in ("keep","decline","check_failed","fit_failed") and
               (row["status"] == "fit_failed") == (not valid_fit), f"Inconsistent panel status at {key}")
    cases = [saved[i, "baseline"] for i in IDS]
    cells = [int(r["cell_id"]) for r in cases]
    ensure(len(set(cells)) == 360 and set(Counter(cells).values()) == {4}, "Invalid factorial cells")
    for i in IDS:
        k24 = merged[i, "K24"]
        baseline = saved[i, "baseline"]
        for arm in ARMS:
            r = merged[i, arm]
            ensure(all(equal_field(r[k], baseline[k]) for k in KEYS), f"Unpaired {arm} inputs for {i}")
            if arm == "baseline":
                continue
            ensure(all(equal_field(r[k], k24[k]) for k in ("clarity","election_reason","peak_index",
                                                             "upstream_peak_index","same_peak")),
                   f"Component election or peak diagnostic changed in {i}/{arm}")
            ensure(float(r["K"]) == 24, f"Unexpected K for {i}/{arm}")
            if logical(r["fallback"]):
                ensure(r["fit_status"] == baseline["fit_status"] and
                       r["fit_hash"] == baseline["fit_hash"], f"Fallback differs from baseline in {i}/{arm}")
    # The old case table supplies all numerical baseline and full-K24 comparator outcomes.
    rows = {arm:[(saved if arm in ARMS[:2] else merged)[i,arm] for i in IDS] for arm in ARMS}
    labels = []
    for i in IDS:
        r = merged[i, "K24"]
        if logical(r["clarity"]):
            equal = logical(r["same_peak"])
            ensure(equal == (int(r["upstream_peak_index"]) == int(r["peak_index"])),
                   f"Wrong raw coarse peak comparison at {i}")
            labels.append("same" if equal else "different")
        else:
            ensure(r["same_peak"] in ("", "NA", "NaN"), f"Peak comparison without a clear election at {i}")
            labels.append("no_clear_election")
    return cases, rows, checks, np.array(labels)


def grouping(cases):
    cols = {"N": [r["N"] for r in cases], "pathology": [">20%" if float(r["fraction"])>.2 else "<=20%" for r in cases],
            "disease": [r["disease"] for r in cases], "family": [r["family"] for r in cases]}
    vals = {k:np.array(v) for k,v in cols.items()}
    for levels in product(*[("all", *sorted(set(v))) for v in cols.values()]):
        key = dict(zip(cols, levels))
        mask = np.ones(len(cases), dtype=bool)
        for field, value in key.items():
            if value != "all":
                mask &= vals[field] == value
        ensure(mask.any(), f"Empty design stratum {key}")
        yield key, mask


def score(rows, extraction):
    valid = np.array([r["fit_status"] == "ResultFound" for r in rows])
    limit = np.array([[num(r[f"{extraction}_{k}"]) for k in ("lower","upper")] for r in rows])
    z = np.abs([[num(r[f"{extraction}_z_{k}"]) for k in ("lower","upper")] for r in rows])
    finite = np.isfinite(limit).all(axis=1)
    ensure(np.array_equal(~finite,[logical(r[f"{extraction}_nonfinite"]) for r in rows]) and
           not (finite & ~valid).any() and not np.isnan(z[finite]).any(), "Invalid endpoint record")
    return dict(loss=np.where(finite, np.minimum(z,5).mean(axis=1), 5.0), returned=finite,
                fit_failed=~valid, implausible=finite & (z.mean(axis=1)>5))


def fallback_step(row):
    if not logical(row["fallback"]):
        return "none"
    if not logical(row["clarity"]):
        ensure(row["reason"] == row["election_reason"], "Inconsistent initial election failure")
        return "initial_election"
    # stage2_guided writes the active step before its diagnostic message.
    return row["reason"].split(maxsplit=1)[0]


def paired(key, scores, arm, comparator, mask, boot):
    a,b = scores[arm],scores[comparator]
    av,bv = a["loss"][mask], b["loss"][mask]
    return dict(**key, arm=arm, comparator=comparator, planned=len(av), arm_mean=av.mean(),
                comparator_mean=bv.mean(), arm_failures=int(a["fit_failed"][mask].sum()),
                comparator_failures=int(b["fit_failed"][mask].sum()), arm_nonreturns=int((~a["returned"][mask]).sum()),
                comparator_nonreturns=int((~b["returned"][mask]).sum()), arm_implausible=int(a["implausible"][mask].sum()),
                comparator_implausible=int(b["implausible"][mask].sum()),
                **cluster_interval(boot, av-bv, np.ones(len(av),dtype=bool)))


def panel_data(checks):
    out = {}
    for arm,seed in product(ARMS[:2],SEEDS):
        decisions = {p:np.array([checks[i,arm,p,seed]["status"] for i in IDS]) for p in ("guidance","diagnostic")}
        a,b = decisions.values()
        out[arm,seed] = dict(known=np.isin(a,("decline","keep")) & np.isin(b,("decline","keep")),
                             disagree=a!=b, keep_to_decline=(a=="keep") & (b=="decline"),
                             decline_to_keep=(a=="decline") & (b=="keep"),
                             guidance_decline=a=="decline", fresh_decline=b=="decline")
    return out


def noise(tables, key, mask, boot, panels):
    for seed in SEEDS:
        a,b = panels["K24",seed],panels["baseline",seed]
        common = a["known"] & b["known"]
        for arm in ARMS[:2]:
            p = panels[arm,seed]
            for population,eligible in (("own",p["known"]),("common",common)):
                use=eligible[mask]
                counts={f:int((v[mask] & use).sum()) for f,v in p.items() if f!="known"}
                tables["panel-noise"].append(dict(**key, seed=seed, arm=arm, population=population,
                        planned=int(mask.sum()), evaluable=int(use.sum()), nonevaluable=int((~use).sum()),
                        **counts, **cluster_interval(boot, p["disagree"][mask] & use, use)))
        use = common[mask]
        # Switch comparison and signed decline differences use exactly the same four checks.
        for metric in ("disagree","keep_to_decline","decline_to_keep","guidance_decline","fresh_decline",
                       "guidance_minus_fresh"):
            def metric_value(panel):
                if metric == "guidance_minus_fresh":
                    return panel["guidance_decline"].astype(int)-panel["fresh_decline"].astype(int)
                return panel[metric].astype(int)
            x,y = metric_value(a)[mask],metric_value(b)[mask]
            tables["paired-panel-noise"].append(dict(**key, seed=seed, metric=metric,
                planned=int(mask.sum()), evaluable=int(use.sum()), K24_sum=int(x[use].sum()),
                baseline_sum=int(y[use].sum()), K24_only=int(((x>y)&use).sum()),
                baseline_only=int(((x<y)&use).sum()), **cluster_interval(boot, (x-y)*use, use)))


def analyze(cases, rows, checks, same_peak):
    tables = defaultdict(list)
    cells=np.array([int(r["cell_id"]) for r in cases])
    scores={e:{a:score(rows[a],e) for a in ARMS} for e in EXT}
    panels=panel_data(checks)
    steps={a:np.array([fallback_step(r) for r in rows[a]]) for a in ARMS[1:]}
    is_fallback={a:s!="none" for a,s in steps.items()}
    ensure(is_fallback["K24"].sum()==331,"Frozen original K24 fallback count changed")
    for arm,ext in product(ARMS[1:],EXT):
        a,b,full=(scores[ext][name] for name in (arm,"baseline","K24"))
        for i,r in enumerate(cases):
            tables["case-loss"].append(dict(j=r["j"],cell_id=r["cell_id"],N=r["N"],fraction=r["fraction"],
                pathology=">20%" if float(r["fraction"])>.2 else "<=20%",disease=r["disease"],family=r["family"],
                arm=arm,extraction=ext,peak_comparison=same_peak[i],fallback=is_fallback[arm][i],
                arm_returned=a["returned"][i],baseline_returned=b["returned"][i],arm_loss=a["loss"][i],
                baseline_loss=b["loss"][i],full_K24_loss=full["loss"][i],
                arm_minus_baseline=a["loss"][i]-b["loss"][i],arm_minus_full_K24=a["loss"][i]-full["loss"][i]))
    reasons={}
    for a in ARMS[1:]:
        reasons[a] = sorted(set((step,r["reason"]) for step,r in zip(steps[a],rows[a]) if step!="none"))
        for j, (step,r) in enumerate(zip(steps[a],rows[a])):
            if step=="none":
                continue
            tables["fallback-cases"].append(dict(j=r["j"], arm=a, N=r["N"], fraction=r["fraction"],
                pathology=">20%" if float(r["fraction"])>.2 else "<=20%", disease=r["disease"], family=r["family"],
                cell_id=r["cell_id"], replicate=r["replicate"], step=step, reason=r["reason"],
                peak_comparison=same_peak[j], fallback_fit_status=r["fit_status"]))
    for group, mask in grouping(cases):
        boot=Bootstrap(cells[mask])
        n=int(mask.sum())
        ones=np.ones(n,dtype=bool)
        for a in ARMS[1:]:
            falls=is_fallback[a][mask]
            tables["fallback-rates"].append(dict(**group,arm=a,planned=n,fallback=int(falls.sum()),
                    failed_after_fallback=int((falls & scores["native"][a]["fit_failed"][mask]).sum()),
                    **cluster_interval(boot,falls,ones)))
            step_reason=Counter((steps[a][i],rows[a][i]["reason"]) for i in np.flatnonzero(mask & is_fallback[a]))
            for step,reason in reasons[a]:
                count=step_reason[step,reason]
                tables["fallback-steps"].append(dict(**group,arm=a,step=step,reason=reason,count=count,
                    planned=n,fallback=int(falls.sum()),fraction_planned=count/n,
                    fraction_of_fallback=count/falls.sum() if falls.any() else np.nan))
        for e in EXT:
            for a in ARMS[1:]:
                for comparator in (("baseline",) if a=="K24" else ("baseline","K24")):
                    tables["paired-loss"].append(paired(dict(**group,extraction=e),scores[e],a,comparator,mask,boot))
        if group["disease"]!="all" or group["family"]!="all":
            continue
        noise(tables,group,mask,boot,panels)
        for peak in ("same","different","no_clear_election"):
            subset=mask & (same_peak==peak)
            if not subset.any():
                continue
            subboot=Bootstrap(cells[subset])
            for a,e in product(ARMS[1:],EXT):
                tables["peak-diagnostic"].append(paired(dict(**group,peak_comparison=peak,extraction=e),
                    scores[e],a,"baseline",subset,subboot))
    return tables


def grid(headers, data):
    return ["", "| "+" | ".join(headers)+" |", "| "+" | ".join("---" for _ in headers)+" |",
            *["| "+" | ".join(map(str,row))+" |" for row in data], ""]


def render(tables):
    overall=dict(N="all",pathology="all",disease="all",family="all")
    def select(name,**filters):
        return [r for r in tables[name] if all(r[k]==v for k,v in filters.items())]
    def one(name,**filters):
        found=select(name,**filters)
        ensure(len(found)==1,f"Expected one row for {name}, {filters}")
        return found[0]
    def diff(x):
        return f"{x:+.4f}"
    def proportion(count,total):
        return f"{count:,}/{total:,} ({100*count/total:.1f}%)" if total else "0/0"
    def ci(row,scale=1):
        if not np.isfinite(row["ci_low"]):
            return "—"
        return f"[{scale*row['ci_low']:+.3f}, {scale*row['ci_high']:+.3f}]"
    lines=["# K24 development ablations", "",
           "The same 1,440 development datasets and 40 guidance anchors per dataset were used for all arms. "
           "Unchanged refineR and full K24 use the archived fits and panel decisions from the original development run. "
           "Each ablation activates one component of the original K24 search and uses the same clarity requirement.",
           "", "## Accuracy before the check", "",
           "Each difference subtracts the unchanged refineR loss from the indicated arm’s loss. Negative values "
           "favor that arm. Each dataset contributes the mean of its two absolute endpoint z errors, "
           "capped at 5 per endpoint. A missing interval contributes 5. Fallback cases count in their assigned arm. "
           "The four primary strata pool rounding increments and replicates."]
    for extraction,title in (("native","Native refineR limits (primary)"),
                             ("historical","Historical C2 limits (secondary)")):
        lines+=["","### "+title]
        data=[]
        for n,p in product(("1500","50000"),(">20%","<=20%")):
            grp=dict(overall,N=n,pathology=p)
            res=[one("paired-loss",**grp,arm=a,comparator="baseline",extraction=extraction) for a in ARMS[1:]]
            data.append([f"{int(n):,}",p,res[0]["planned"],f"{res[0]['comparator_mean']:.4f}",
                         *[diff(r["value"]) for r in res]])
        lines+=grid(["N","Pathology","Datasets","refineR loss","Full K24 Δ","Peak only Δ",
                     "Starting values only Δ","Search regions only Δ"],data)
    lines+=["### Healthy families and disease patterns", "",
            "These native-limit differences pool both routine sample sizes. The downloadable paired loss table "
            "also gives each healthy family × disease pattern × N × pathology combination with its interval."]
    data=[]
    for axis in ("family","disease"):
        levels=sorted(set(r[axis] for r in tables["paired-loss"])-{"all"})
        for val,p in product(levels,(">20%","<=20%")):
            key=dict(overall,pathology=p);key[axis]=val
            vals=[one("paired-loss",**key,arm=a,comparator="baseline",extraction="native") for a in ARMS[1:]]
            data.append([val,p,vals[0]["planned"],*[diff(r["value"]) for r in vals]])
    lines+=grid(["Family or disease pattern","Pathology","Datasets","Full K24 Δ","Peak only Δ",
                 "Starting values only Δ","Search regions only Δ"],data)
    lines+=["## When the search fell back to refineR", "",
            "A failed initial election stops guidance immediately. A later search failure follows a clear election. "
            "A pass1_regions no_peak_in_basin failure means the search then found no eligible peak in the "
            "retained basin while defining first-pass regions."]
    data=[]
    for r in select("fallback-steps",**overall,arm="K24"):
        data.append([r["step"],r["reason"],proportion(r["count"],r["fallback"]),proportion(r["count"],r["planned"])])
    lines+=grid(["Full K24 step","Recorded reason","Share of all K24 fallbacks","Share of assigned datasets"],data)
    data=[]
    for a in ARMS[1:]:
        r=one("fallback-rates",**overall,arm=a)
        data.append([NAMES[a],proportion(r["fallback"],r["planned"]),r["failed_after_fallback"]])
    lines+=grid(["Arm","Fallbacks","Fallback fits that also failed"],data)
    lines+=["## First coarse peak", "",
            "The native differences below compare each unchanged arm with pass-through on the same cases. "
            "The groups use the actual upstream raw coarse peak and the elected anchor peak. "
            "An unclear election forms a third group. These conditional means describe existing fits."]
    data=[]
    for peak in ("same","different","no_clear_election"):
        for n,p in product(("1500","50000"),(">20%","<=20%")):
            key=dict(overall,N=n,pathology=p)
            vals=select("peak-diagnostic",**key,peak_comparison=peak,extraction="native")
            if not vals:
                data.append([peak,f"{int(n):,}",p,0,*["—"]*4])
                continue
            lookup={r["arm"]:r for r in vals}
            data.append([peak,f"{int(n):,}",p,vals[0]["planned"],*[diff(lookup[a]["value"]) for a in ARMS[1:]]])
    lines+=grid(["First coarse peak","N","Pathology","Datasets","Full K24 Δ","Peak only Δ",
                 "Starting values only Δ","Search regions only Δ"],data)
    lines+=["## Disagreement between the two 40-anchor panels", "",
            "For each fixed fit, the table compares the decision from its original guidance panel with the "
            "decision from its fresh independent panel. Unchanged refineR uses neither panel to fit its interval. "
            "The original full K24 fit used the guidance panel. A switch in either direction counts as disagreement."]
    data=[]
    for seed in SEEDS:
        for arm, pop in product(ARMS[:2],("own","common")):
            r=one("panel-noise",**overall,arm=arm,seed=seed,population=pop)
            data.append([seed,NAMES[arm],pop,proportion(r["disagree"],r["evaluable"]),
                         r["keep_to_decline"],r["decline_to_keep"],r["nonevaluable"]])
    lines+=grid(["PIT seed","Fit","Evaluable IDs","Disagreement","Keep → decline","Decline → keep",
                 "Excluded from denominator"],data)
    data=[]
    for seed in SEEDS:
        r=one("paired-panel-noise",**overall,seed=seed,metric="disagree")
        data.append([seed,r["evaluable"],r["K24_only"],r["baseline_only"],f"{100*r['value']:+.2f}",ci(r,100)])
    lines+=grid(["PIT seed","Common IDs","Only K24 disagreed","Only refineR disagreed",
                 "K24 − refineR (percentage points)","95% interval (points)"],data)
    r=one("paired-panel-noise",**overall,seed="primary",metric="disagree")
    base=one("panel-noise",**overall,seed="primary",population="own",arm="baseline")
    full=one("panel-noise",**overall,seed="primary",population="own",arm="K24")
    lines+=[f"With the primary PIT seed, changing panels reversed {proportion(base['disagree'],base['evaluable'])} "
            f"of evaluable unchanged refineR decisions and {proportion(full['disagree'],full['evaluable'])} of "
            f"full K24 decisions. On the {r['evaluable']:,} common datasets the difference was "
            f"{100*r['value']:+.2f} percentage points. ",
            "", "The baseline measures how often two independent healthy panels give different decisions "
            "for a fit made without either panel. The K24 comparison also reflects its different fitted "
            "distributions and its use of the original panel in the search. These data do not isolate the "
            "effect of reuse from the change in fitted distributions.", "", "## Data tables", "",
            "- Per-dataset paired differences in all-set loss, the two arm means, nonreturns, fit failures "
            "and implausible counts are summarized for every marginal and cross of pathology, sample size, "
            "disease pattern and healthy family. Implausibility requires an uncapped mean absolute endpoint "
            "z error above 5. [Individual paired losses](case-loss.csv) · [Grouped paired losses](paired-loss.csv)",
            "- The first coarse peak comparison is available by sample size and pathology with both "
            "endpoint extractions. [Peak diagnostic](peak-diagnostic.csv)",
            "- Every fallback has a case identifier, stage, complete recorded reason, final fit status "
            "and design factors. [Cases](fallback-cases.csv) · [Counts by step](fallback-steps.csv) · "
            "[Fallback rates](fallback-rates.csv)",
            "- Panel tables give own and common evaluable populations, directional transitions, paired "
            "differences and cluster intervals for both PIT seeds. [Panel disagreement](panel-noise.csv) · "
            "[Paired differences](paired-panel-noise.csv)", "",
            "The 95% percentile intervals resample complete factorial cells, keeping all replicates in "
            "the selected stratum together. Each stratum uses 2,000 draws and PCG64 seed 37000000. "
            "Paired differences use identical case weights for both estimators. The tables count "
            "undefined replicates and omit intervals for fewer than two informative cells. "
            "Component contrasts evaluate each component in isolation. Combining components can change "
            "the peak and grid jointly, so these contrasts need not add to the full K24 effect.", ""]
    return "\n".join(lines)


def save(out,tables):
    out.mkdir(parents=True,exist_ok=True)
    for name,rows in tables.items():
        with (out/(name+".csv")).open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n")
            w.writeheader()
            for r in rows:
                w.writerow({k:"" if isinstance(v,(float,np.floating)) and np.isnan(v) else v for k,v in r.items()})
    (out/"REPORT.md").write_text(render(tables),encoding="utf-8")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("merged_dir",type=Path)
    p.add_argument("output_dir",type=Path)
    args=p.parse_args()
    save(args.output_dir,analyze(*load(args.merged_dir)))
