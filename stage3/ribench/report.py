"""Summarize one technically audited Stage 3 RIbench cohort on identical datasets."""
import csv
import hashlib
import json
import math
import os
import sys
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

os.environ["OPENBLAS_NUM_THREADS"] = "1"
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from stage1 import report as s1
from stage1.report import Bootstrap, ensure, logical, np, num
from stage2.report import cluster_interval
from stage2.ribench import report as ri

SCIENTIFIC = ("baseline", "stage2", "w1", "t0.25", "anchorsOnly")
CANDIDATES = ("w1", "t0.25")
ARM_LABEL = dict(ri.LABELS, stage2="Stage 2", w1="Primary (w = 1)",
                 **{"t0.25": "Post-fit (t = 0.25)"})
EXT = ri.EXT
MODES = ("pre", "checked")
GATES = (">20%", "<=20%")
OVERLAP = ("overlapPatholLeft", "overlapPatholRight")
SEED_KIND = ("primary", "alternate")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(cohort, evidence):
    n = {"small": 2880, "large": 1440}[cohort]
    audit = json.loads((evidence / "audit.json").read_text())
    ensure(audit["passed"] and audit["cohort"] == cohort and audit["datasets"] == n and
           audit["fits"] == 7*n and audit["checks"] == 14*n,
           "Expected complete primary coverage after a passing technical audit")
    fitrows = ri.read(evidence/"fits.csv.gz")
    checkrows = ri.read(evidence/"checks.csv.gz")
    fd = {(int(r["Index"]), r["arm"]): r for r in fitrows}
    cd = {(int(r["Index"]), r["arm"], r["seed_kind"]): r for r in checkrows}
    ids = sorted({i for i, a in fd})
    all_labels = (*SCIENTIFIC, "w0", "t0")
    ensure(len(ids) == n and len(fd) == len(fitrows) and set(fd) == set(product(ids, all_labels)),
           "Incomplete or duplicate RIbench fit records")
    ensure(len(cd) == len(checkrows) and set(cd) == set(product(ids, all_labels, SEED_KIND))
           and all(r["panel"] == "guidance" for r in checkrows), "Incomplete or duplicate guidance decisions")
    cases = [fd[i, "stage2"] for i in ids]
    spec_path = ROOT/("archive/c2/testsets.csv" if cohort=="small" else "stage1/large/testsets.csv")
    spec = {int(r["Index"]): r for r in ri.read(spec_path)}
    ensure(set(spec) == set(ids), "The RIbench cohort definition differs from the audit")
    for i, row in zip(ids, cases):
        original = spec[i]
        ensure(original["HashCode"] == row["ribench_hashcode"] and
               original["Analyte"] == row["Analyte"] and original["Scenario"] == row["Scenario"] and
               float(original["fractionPathol"]) == float(row["fractionPathol"]) and
               float(original["N"]) == int(row["N"]), f"RIbench specification mismatch for {i}")
        for k in OVERLAP:
            ensure(original[k] in ("low", "medium", "high"), f"Unknown {k} at {i}")
            row[k] = original[k]
    truth = ri.matrix(cases, ["truth_lower","truth_upper"])
    lower = np.array([r["Analyte"] != "CRP" for r in cases])
    arms, fields = {}, {}
    for arm in SCIENTIFIC:
        rows = [fd[i, arm] for i in ids]
        valid = np.array([r["fit_status"] == "ResultFound" for r in rows])
        estimates, outside = {}, {}
        for ext in EXT:
            limits = ri.matrix(rows, [f"{ext}_{s}" for s in ri.SIDES])
            z = ri.matrix(rows, [f"{ext}_z_{s}" for s in ri.SIDES])
            finite = np.isfinite(limits[:,1]) & (~lower | np.isfinite(limits[:,0]))
            status = np.where(finite,"returned",np.where(valid,"extraction_failed","fit_failed"))
            estimates[ext] = ri.model(z,limits,truth,lower,np.ones(n,dtype=bool),status)
            outside[ext] = np.array([any(r[f"{ext}_out_{s}"] == "TRUE" for s in ri.SIDES) for r in rows])
        decisions, reasons = {}, {}
        for seed in SEED_KIND:
            checked = [cd[i,arm,seed] for i in ids]
            decisions[seed] = np.array([r["status"] for r in checked])
            reasons[seed] = np.array([r["reason"] for r in checked])
        arms[arm] = ri.Fit(estimates,outside,valid,np.array([logical(r["fallback"]) for r in rows]),
                           np.array([r["reason"] for r in rows]),np.array([r["branch"] for r in rows]),
                           decisions,reasons)
        fields[arm] = {k: np.array([r[k] for r in rows]) for k in
                       ("parent_fallback","weighted_search_attempted","weighted_search_entered",
                        "weighted_search_path","extra_fallback","parent_retained","branch","reason")}
        for k in ("healthy_center_z","healthy_spread_z"):
            fields[arm][k] = np.array([num(r[k]) for r in rows])
    comparators = ri.load_comparators(cases)
    ensure(all(v.paired.all() for v in comparators.values()), "Incomplete archived comparator coverage")
    return cases, arms, fields, comparators, audit


def strata(cases, parent, available):
    labels = {k: np.array([r[k] for r in cases]) for k in ("Analyte","Scenario","N",*OVERLAP)}
    frac = np.array([float(r["fractionPathol"]) for r in cases])
    labels["fraction"] = np.array([format(v,"g") for v in frac])
    labels["pathology"] = np.where(frac>.2,">20%","<=20%")
    labels["parent"] = np.where(parent,"fallback","nonfallback")
    labels["healthy_median_in_basin"] = np.array([r["healthy_median_in_basin"] for r in cases])
    labels["initial_peak_agrees"] = np.array([r["same_peak"] for r in cases])
    every = np.ones(len(cases),dtype=bool)
    yield "all", "All", every
    if np.any(available):
        yield "both_updates_available", "all", available
        for value in ("fallback","nonfallback"):
            mask = available & (labels["parent"] == value)
            if mask.any():
                yield "both_updates_available", value, mask
    # Single-factor, parent-specific and joint clinical breakdowns, including
    # the ordered left/right overlap levels recorded in RIbench's specification.
    for factors in (("pathology",),("N",),("Analyte",),("Scenario",),("fraction",),("parent",),
                    (OVERLAP[0],),(OVERLAP[1],),OVERLAP,("N","pathology"),("N","parent"),
                    ("parent","pathology"),("N","parent","pathology"),("parent","fraction"),
                    ("N","fraction"),("Analyte","fraction"),("Analyte","pathology"),
                    ("healthy_median_in_basin",),("initial_peak_agrees",),("healthy_median_in_basin","pathology"),
                    ("N","Analyte","fraction"),("parent",*OVERLAP),
                    (*OVERLAP,"pathology"),(*OVERLAP,"fraction"),("parent",*OVERLAP,"fraction")):
        for values in sorted(set(zip(*(labels[k] for k in factors)))):
            mask = every.copy()
            for k,v in zip(factors,values):
                mask &= labels[k] == v
            yield "/".join(factors), "/".join(values), mask


def summarize(cohort, cases, arms, fields, comparators):
    parent = arms["stage2"].fallback
    both = ((fields["w1"]["weighted_search_entered"] == "TRUE") &
            (fields["w1"]["extra_fallback"] == "FALSE") &
            (fields["t0.25"]["extra_fallback"] == "FALSE") &
            arms["w1"].valid & arms["t0.25"].valid)
    groups = list(strata(cases,parent,both))
    for group, stratum, mask in groups:
        tables = defaultdict(list)
        key = dict(cohort=cohort,group=group,stratum=stratum)
        idx = np.flatnonzero(mask)
        count = len(idx)
        all_rows = np.ones(count,dtype=bool)
        boot = Bootstrap([(cases[i]["Analyte"],cases[i]["Scenario"]) for i in idx])
        detailed = group in {"healthy_median_in_basin","healthy_median_in_basin/pathology","initial_peak_agrees","all","pathology","N","Analyte","Scenario","fraction","parent",
            *OVERLAP,"/".join(OVERLAP),"N/pathology","parent/pathology","N/parent","parent/fraction","N/parent/pathology"}
        levels = EXT if detailed else ("native",)
        models = {}
        for arm, data in arms.items():
            keep = data.decisions["primary"][idx] == "keep"
            if detailed:
                branch_fields = ("branch","reason","parent_fallback","weighted_search_path",
                                 "weighted_search_attempted","weighted_search_entered","extra_fallback","parent_retained")
                for vals,ct in Counter(zip(*(fields[arm][k][idx] for k in branch_fields))).items():
                    tables["branches"].append(dict(**key,arm=arm,**dict(zip(branch_fields,vals)),count=ct,planned=count))
                if arm != "anchorsOnly":
                    d1,d2 = (data.decisions[s][idx] for s in SEED_KIND)
                    tested = np.isin(d1,("keep","decline")) & np.isin(d2,("keep","decline"))
                    changes = (d1 != d2) & tested
                    tables["seed-changes"].append(dict(**key,arm=arm,planned=count,both_evaluable=int(tested.sum()),
                        changed=int(changes.sum()),keep_to_decline=int(((d1=="keep")&(d2=="decline")).sum()),
                        decline_to_keep=int(((d1=="decline")&(d2=="keep")).sum()),**cluster_interval(boot,changes,tested)))
            for ext in levels:
                base = data.estimates[ext].subset(idx)
                models[arm,ext,"pre"] = base
                models[arm,ext,"checked"] = base.gated(keep,data.decisions["primary"][idx])
                if detailed and arm != "anchorsOnly":
                    for seed in SEED_KIND:
                        spec = dict(**key,arm=arm,extraction=ext,seed=seed,mode="check")
                        s1.check_metrics(tables,spec,boot,base,data.decisions[seed][idx],
                                         data.check_reasons[seed][idx],data.valid[idx])
                if detailed:
                    for mode in MODES:
                        m = models[arm,ext,mode]
                        ok = all_rows if mode == "pre" else keep
                        spec = dict(**key,arm=arm,extraction=ext,mode=mode,seed="primary" if mode=="checked" else "none")
                        s1.accuracy(tables,spec,boot,m,all_rows)
                        if ext == "native":
                            curve = dict(**spec,planned=count,returned=int(m.returned.sum()))
                            for label,k in (("center","healthy_center_z"),("spread","healthy_spread_z")):
                                values = fields[arm][k][idx]
                                measured = m.returned & np.isfinite(values)
                                curve[label+"_n"] = int(measured.sum())
                                curve["mean_"+label+"_bias"] = s1.average(values[measured])
                            tables["curve"].append(curve)
                        tables["accuracy"][-1].update(fit_failures=int((~data.valid[idx]).sum()),
                            nonreturns=int((~m.returned).sum()),unscored_returned=int((m.returned & ~m.scored).sum()),
                            implausible=int((m.scored & (m.absolute>5)).sum()),severe=int((m.scored & (m.maximum>5)).sum()),
                            outside_support=int((ok & data.out[ext][idx]).sum()),nonfinite=int((ok&~base.returned).sum()),
                            unordered=int((m.returned & m.lower_needed & (m.estimate[:,0]>=m.estimate[:,1])).sum()),
                            CRP_nonpositive_upper=int((m.returned & ~m.lower_needed & (m.estimate[:,1]<=0)).sum()))
        for arm,ext,mode in product(CANDIDATES,levels,MODES):
            lhs = models[arm,ext,mode]
            comparison = {"baseline":models["baseline",ext,mode],"stage2":models["stage2",ext,mode],
                          "anchorsOnly":models["anchorsOnly",ext,mode]}
            variant = "raw" if mode == "pre" else "reported"
            for method in ("taskE_armB","anchoredRI_improved"):
                comparison[method] = comparators[method,variant].subset(idx)
            if detailed and mode=="checked":
                comparison["ungated_refineR"] = models["baseline",ext,"pre"]
            for ref, rhs in comparison.items():
                bm = variant if ref in ("taskE_armB","anchoredRI_improved") else "pre" if ref=="ungated_refineR" else mode
                row = ri.pair(dict(**key,arm=arm,extraction=ext,mode=mode,baseline=ref,baseline_mode=bm),lhs,rhs,boot,all_rows)
                tables["paired-loss"].append(row)
                if ref=="baseline" and ext=="native" and group in ("pathology","N/pathology"):
                    high = stratum.split("/")[-1] == ">20%"
                    loss_ok = row["value"]<0 if high else row["value"]<=.02
                    impl_ok = row["arm_implausible"] <= row["baseline_implausible"]
                    coverage_ok = row["arm_nonreturns"] <= row["baseline_nonreturns"]
                    complete = row["matched"] == count
                    tables["gates" if group=="pathology" else "gates-by-n"].append(dict(**row,
                        loss_met=loss_ok,implausible_met=impl_ok,nonreturn_met=coverage_ok,complete=complete,
                        all_met=bool(loss_ok and impl_ok and coverage_ok and complete)))
        yield tables


def f(x, signed=False):
    return format(x,"+.4f" if signed else ".4f") if math.isfinite(x) else "NA"


def ci(row):
    return f"{f(row['value'],True)} [{f(row['ci_low'],True)}, {f(row['ci_high'],True)}]"


def formatted(rows, headers):
    return "\n".join(ri.markdown(headers,rows))


def derive(tables):
    """Compute the gap on identical denominators and decompose changes from Stage 2."""
    pairs = tables["paired-loss"]
    lookup = {(r["arm"],r["extraction"],r["mode"],r["baseline"]): r for r in pairs}
    for arm,ext,mode,baseline in lookup:
        if baseline != "stage2":
            continue
        r = lookup[arm,ext,mode,baseline]
        ao = lookup[arm,ext,mode,"anchorsOnly"]
        ensure(r["matched"] == ao["matched"] == r["planned"], "Incomplete gap comparison")
        tables["gap"].append({k:r[k] for k in ("cohort","group","stratum","arm","extraction","mode","planned")} |
            dict(stage2_loss=r["baseline_loss"],arm_loss=r["arm_loss"],anchors_only_loss=ao["baseline_loss"],
                 gap_closed=-r["value"],closed_ci_low=-r["ci_high"],closed_ci_high=-r["ci_low"],
                 remaining_gap=ao["value"],remaining_ci_low=ao["ci_low"],remaining_ci_high=ao["ci_high"]))


def contributions(pairs):
    lookup = {(r["group"],r["stratum"],r["arm"],r["extraction"],r["mode"]):r
              for r in pairs if r["baseline"]=="stage2"}
    output = []
    for key,total in lookup.items():
        group,stratum,*suffix = key
        if group not in ("all","N","pathology","N/pathology"):
            continue
        parts = [] if group=="all" else stratum.split("/")
        sub_group = {"all":"parent","N":"N/parent","pathology":"parent/pathology",
                     "N/pathology":"N/parent/pathology"}[group]
        children = []
        for parent in ("fallback","nonfallback"):
            label = "/".join(parts[:1]+[parent]+parts[1:]) if group.startswith("N") else "/".join([parent]+parts)
            row = lookup.get((sub_group,label,*suffix))
            if row is None:
                continue
            share = row["planned"]/total["planned"]
            contribution = share*row["value"]
            children.append((row["planned"],contribution))
            output.append(dict(**row,parent=parent,whole_group=group,whole_stratum=stratum,whole_count=total["planned"],
                               whole_difference=total["value"],population_share=share,weighted_contribution=contribution))
        ensure(sum(n for n,v in children)==total["planned"] and
               math.isclose(sum(v for n,v in children),total["value"],abs_tol=1e-12), "Fallback partition differs")
    return output


def render(cohort,audit,summary):
    gates = summary["gates"]
    v = {a:{m:all(r["all_met"] for r in gates if r["arm"]==a and r["mode"]==m) for m in MODES}
         for a in CANDIDATES}
    sizes = "N ≤ 5,000" if cohort=="small" else "N = 50,000"
    def sentence(arm):
        raw = "met" if v[arm]["pre"] else "missed"
        checked = "met" if v[arm]["checked"] else "missed"
        return f"The {ARM_LABEL[arm].lower()} {raw} the pre-check criteria and {checked} the checked criteria."
    def group_rows(name,group,**fields):
        return [r for r in summary[name] if r["group"]==group and all(r[k]==v for k,v in fields.items())]
    text = [f"# Stage 3 RIbench, {sizes}", f"Both frozen arms ran on {audit['datasets']:,} paired RIbench datasets. "+
            " ".join(sentence(a) for a in CANDIDATES), "## Prespecified gates",
            "The difference is arm minus unchanged refineR in mean capped absolute endpoint z error. "
            "Both sides use native limits. Checked comparisons use each fit’s own guidance-panel decision under the primary PIT seed. "
            "Every failed, withheld or unscorable interval contributes 5. Above 20% pathology the difference must be strictly negative. "
            "At or below 20% the margin is +0.02. Each comparison must also have no extra implausible intervals or nonreturns. "
            "The table gives arm and refineR counts in that order. The formal decision uses the unrounded point estimates.",
            formatted([[r["stratum"],ARM_LABEL[r["arm"]],r["mode"],r["planned"],ci(r),
                        f"{r['arm_implausible']} / {r['baseline_implausible']}",f"{r['arm_nonreturns']} / {r['baseline_nonreturns']}",
                        "Met" if r["all_met"] else "Missed"] for r in gates],
                      ["Pathology","Arm","Release","Assigned","Loss difference [95% interval]","Implausible","Nonreturns","Decision"]),
            "Implausibility means uncapped mean absolute error across requested endpoints above 5. "
            "The severe endpoint flag uses the largest absolute endpoint error. For CRP the only requested endpoint is the 95th percentile. "
            "[Formal comparisons](gates.csv) · [Separate N comparisons](gates-by-n.csv.gz) · [Native and historical contrasts](paired-loss.csv.gz)",
            "## Error and coverage"]
    rows=group_rows("accuracy","all",extraction="native")
    text.append(formatted([[ARM_LABEL[r["arm"]],r["mode"],r["returned"],r["fit_failures"],r["implausible"],
                            f(r["penalty5_mean"]),f(r["mean_capped_abs_z"])] for r in rows],
                          ["Arm","Release","Returned","Fit failures","Implausible","All-set loss","Returned/scored loss"]))
    text += ["## Baseline Stage 2 fallback",
             "Subgroup membership is fixed by the Stage 2 fit on that dataset. The weighted contribution is the within-subgroup difference "
             "multiplied by that subgroup’s share of the cohort. The fallback and non-fallback contributions sum to the pooled change from Stage 2.",
             formatted([[r["parent"],r["planned"],ARM_LABEL[r["arm"]],r["mode"],f(r["baseline_loss"]),f(r["arm_loss"]),
                         ci(r),f(r["weighted_contribution"],True)] for r in summary["parent-contributions"]
                        if r["whole_group"]=="all" and r["extraction"]=="native"],
                       ["Stage 2 subgroup","Datasets","Arm","Release","Stage 2 loss","Arm loss","Change from Stage 2 [95% interval]","Contribution"]),
             "[Parent subgroups by N and pathology](parent-contributions.csv.gz) · [Search branches and reasons](branches.csv.gz) · [Both updates available and common scored results](paired-loss.csv.gz)",
             "## RIbench overlap and pathological fraction",
             "RIbench assigns low, medium or high overlap separately to its left and right pathological components. "
             "These are the original specification labels, including on zero-pathology controls. The tables retain left, right and ordered pair labels. "
             "Pre-check entries below use native limits and all assigned datasets."]
    paired=summary["paired-loss"]
    lookup={(r["group"],r["stratum"],r["arm"]):r for r in paired if
            r["extraction"]=="native" and r["mode"]=="pre" and r["baseline"]=="stage2"}
    for types,title in [((OVERLAP[0],OVERLAP[1]),"Designed overlap"),(("fraction",),"Pathological fraction")]:
        display=[]
        for (g,s,a),r in lookup.items():
            if g in types and a=="w1":
                other=lookup[g,s,"t0.25"]
                display.append([g,s,r["planned"],f(r["baseline_loss"]),f(r["arm_loss"]),ci(r),
                                f(other["arm_loss"]),ci(other)])
        text.append(formatted(display,[title,"Level","Datasets","Stage 2 loss","Primary loss","Primary Δ [95% interval]",
                                       "Post-fit loss","Post-fit Δ [95% interval]"]))
    text += ["[All pairwise overlaps and fractional strata](paired-loss.csv.gz) · [Official case labels](overlap.csv.gz)",
             "## Same-dataset comparisons",
             "Unchanged refineR, frozen Stage 2 and anchors-only used the same ordered inputs. The anchoredRI comparators are the "
             "archived Task E arm B and the improved anchoredRI baseline. Raw comparisons use their fitted intervals. Checked comparisons "
             "use the intervals they originally reported after their own safeguards. The archived C2 anchors-only reporting rule releases a successful fit. "
             "All pairing uses RIbench Index plus ordered routine and anchor hashes. The final two columns restrict both methods to cases where both returned scorable results."]
    comparisons=[r for r in paired if r["group"]=="all" and r["extraction"]=="native" and r["baseline"] in
                 ("taskE_armB","anchoredRI_improved","stage2","anchorsOnly")]
    text.append(formatted([[ARM_LABEL[r["arm"]],r["mode"],ARM_LABEL[r["baseline"]],r["matched"],r["arm_returned"],
            r["baseline_returned"],f(r["arm_loss"]),f(r["baseline_loss"]),ci(r),r["common_scored"],f(r["common_difference"],True)]
            for r in comparisons],["Arm","Release","Comparator","Matched","Arm returned","Comparator returned","Arm loss",
                                   "Comparator loss","Arm − comparator [95% interval]","Common scored","Common Δ"]))
    text += ["## Gap to anchors-only",
             "The gap closed is Stage 2 loss minus arm loss. The remaining gap is arm loss minus anchors-only loss. Both use the same datasets. "
             "On the large cohort the above-20% rows address the prespecified target of 720 datasets.",
             formatted([[r["stratum"],ARM_LABEL[r["arm"]],r["mode"],r["planned"],f(r["stage2_loss"]),f(r["arm_loss"]),
                         f(r["anchors_only_loss"]),f(r["gap_closed"],True),f(r["remaining_gap"],True)]
                        for r in group_rows("gap","pathology",extraction="native")],
                       ["Pathology","Arm","Release","Assigned","Stage 2","Arm","Anchors-only","Gap closed","Remaining gap"]),
             "[Gap estimates, intervals and subgroups](gap.csv.gz) · [Comparator sources](../../stage2/ribench/comparators/README.md)",
             "## Guidance-panel checks",
             "RIbench has one independent panel of 40 screened anchors per dataset. Both PIT seeds use the same rounded panel. "
             "The primary seed determines release. E is the largest absolute error of the requested endpoints before checking."]
    lookup={(r["arm"],r["seed"],r["metric"]):r for r in group_rows("rates","all",extraction="native",mode="check",unit="dataset")}
    data=[]
    for a,seed in product(SCIENTIFIC[:-1],SEED_KIND):
        def count(metric):
            r=lookup[a,seed,metric]
            return f"{r['numerator']} / {r['denominator']}"
        data.append([ARM_LABEL[a],seed,*[count(metric) for metric in ("decline","declined_bad_gt1","declined_bad_gt5","declined_good_lt0.25")]])
    text.append(formatted(data,["Arm","PIT seed","Declined / evaluable","E > 1 caught","E > 5 caught","E < 0.25 declined"]))
    text.append(formatted([[ARM_LABEL[r["arm"]],r["changed"],r["both_evaluable"],f(r["value"])]
                           for r in group_rows("seed-changes","all")],["Arm","PIT-seed reversals","Evaluable under both","Share"]))
    text += ["## Audit and Task G export",
             f"The technical audit covered all {audit['datasets']:,} primary datasets. The verified repeated set contained "
             f"{audit['audited_datasets']:,} datasets. The maximum separate-host endpoint difference was {audit['max_endpoint_fraction']:.6g} "
             f"of reference width, and the maximum PIT probability difference was {audit['max_p_difference']:.6g}. "
             "Descriptive 95% intervals use 2,000 matched bootstrap resamples of (analyte, scenario) clusters with PCG64 seed 37000000. "
             "Intervals require at least two informative clusters.",
             "[Technical audit](evidence/audit.json) · [Fit records](evidence/fits.csv.gz) · [Decisions](evidence/checks.csv.gz) · "
             "[Task G guide](TASK-G.md) · [Error and coverage](accuracy.csv.gz) · [Endpoint errors](endpoints.csv.gz) · "
             "[Healthy curve error by elected basin](curve.csv.gz) · [Capture and good-result loss](rates.csv.gz) · [PIT-seed reversals](seed-changes.csv.gz)"]
    return "\n\n".join(text)+"\n",v


def report(cohort,evidence,out):
    cases,arms,fields,comparators,audit=load(cohort,evidence)
    summary=defaultdict(list)
    out.mkdir(parents=True,exist_ok=True)
    writer=ri.Tables(out)
    wanted={"all","pathology","N","parent","parent/pathology","N/parent","N/pathology","N/parent/pathology",
            "fraction",*OVERLAP}
    try:
        writer.add("overlap",[{k:r[k] for k in ("Index","N","Analyte","Scenario","fractionPathol",
                                                 *OVERLAP,"routine_hash","anchor_hash")} for r in cases])
        for tables in summarize(cohort,cases,arms,fields,comparators):
            derive(tables)
            for name,rows in tables.items():
                writer.add(name,rows)
                if name in ("gates","accuracy","paired-loss","gap","rates","seed-changes") and rows[0]["group"] in wanted:
                    summary[name].extend(rows)
        summary["parent-contributions"]=contributions(summary["paired-loss"])
        writer.add("parent-contributions",summary["parent-contributions"])
    finally:
        writer.files.close()
    gates=summary["gates"]
    ensure(len(gates)==8 and {(r["arm"],r["mode"],r["stratum"]) for r in gates}==set(product(CANDIDATES,MODES,GATES)),
           "Formal gate coverage incomplete")
    text,decisions=render(cohort,audit,summary)
    (out/"REPORT.md").write_text(text,encoding="utf-8")
    files=["REPORT.md","gates.csv","gates-by-n.csv.gz","paired-loss.csv.gz","parent-contributions.csv.gz","gap.csv.gz",
           "accuracy.csv.gz","curve.csv.gz","rates.csv.gz","overlap.csv.gz","seed-changes.csv.gz"]
    receipt=dict(cohort=cohort,datasets=len(cases),fixed_w=1,fixed_t=.25,technical_audit_passed=True,
                 scientific_gate_results=decisions,sha256={name:digest(out/name) for name in files},
                 audit_sha256=digest(evidence/"audit.json"))
    (out/"report-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    if len(sys.argv)!=4 or sys.argv[1] not in ("small","large"):
        raise SystemExit("usage: report.py small|large AUDITED_DIRECTORY OUTPUT_DIRECTORY")
    report(sys.argv[1],Path(sys.argv[2]),Path(sys.argv[3]))
