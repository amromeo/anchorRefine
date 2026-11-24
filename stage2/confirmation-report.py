"""Score the single frozen candidate and component arms on audited confirmation data.

Usage: python stage2/confirmation-report.py AUDITED_DATA_DIR OUTPUT_DIR
"""
import argparse
import csv
import gzip
import io
import json
import os
import sys
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path

os.environ["OPENBLAS_NUM_THREADS"] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stage2 import report as dev
from stage2.report import np, num, logical, ensure, read_rows, Bootstrap, cluster_interval

ARMS = ("baseline", "candidate", "peak", "start", "region")
LABELS = dict(baseline="Unchanged refineR",candidate="Frozen candidate (peak only)",peak="Peak only",
              start="Starting values only",region="Search regions only")
EXT, PANELS, SEEDS = dev.EXTRACTIONS, dev.PANELS, dev.SEEDS
COHORT = 2880
PRIMARY = dict(N_group="all", pathology="all", disease="all", family="all", fraction="all", rounding="all")


def load(directory):
    audit = json.loads((directory/"audit.json").read_text())
    ensure(audit["passed"] is True and audit["datasets"]==COHORT and audit["fits"]==COHORT*len(ARMS)
           and audit["checks"]==COHORT*len(ARMS)*4, "Incomplete confirmation audit")
    ensure(audit["distinct_host_shards"]==audit["exact_repeat_shards"]>0, "Incomplete machine checks")
    fit_rows, check_rows = (read_rows(directory/name) for name in ("fits.csv","checks.csv"))
    ids=range(1,COHORT+1)
    fits={(int(r["j"]),r["arm"]):r for r in fit_rows}
    checks={(int(r["j"]),r["arm"],r["panel"],r["seed_kind"]):r for r in check_rows}
    ensure(set(fits)==set(product(ids,ARMS)) and len(fits)==len(fit_rows),"Invalid fit inventory")
    ensure(set(checks)==set(product(ids,ARMS,PANELS,SEEDS)) and len(checks)==len(check_rows),
           "Invalid panel/seed inventory")
    ensure(all(r["selected_rule"]=="peak" for r in fit_rows), "Unexpected selected candidate rule")
    # The candidate and component arm represent the same frozen method. Verify scores,
    # fit identity, branches and releases case by case before reporting their common result.
    for i in ids:
        cand,peak=fits[i,"candidate"],fits[i,"peak"]
        ensure(all(cand[k]==peak[k] for k in ("fit_hash","fit_status","fallback","reason","guidance_used",
            "peak_index","Mu","Sigma","Lambda","Shift",*(f"{e}_{f}" for e in EXT for f in
            ("lower","upper","z_lower","z_upper","ordered","nonfinite")))),f"Candidate/peak fit mismatch at {i}")
        for p,s in product(PANELS,SEEDS):
            a,b=checks[i,"candidate",p,s],checks[i,"peak",p,s]
            ensure(all(a[k]==b[k] for k in a if k!="arm"),f"Candidate/peak check mismatch at {i}/{p}/{s}")
    metadata=[fits[i,"baseline"] for i in ids]
    cell_counts=Counter(int(r["cell_id"]) for r in metadata)
    ensure(len(cell_counts)==360 and set(cell_counts.values())=={8},"Expected eight replicates per factorial cell")
    fields=("cell_id","replicate","N","disease","fraction","family","rounding_fraction","truth_lower",
            "truth_upper","routine_hash","anchor_hash","diagnostic_hash","routine_seed","anchor_seed",
            "diagnostic_seed","fitter_seed","pit_primary_seed","pit_alternate_seed",
            "diagnostic_primary_seed","diagnostic_alternate_seed")
    arms, reasons = {}, {}
    for arm in ARMS:
        rows=[fits[i,arm] for i in ids]
        ensure(all(all(r[k]==base[k] for k in fields) for r,base in zip(rows,metadata)),f"Unpaired inputs for {arm}")
        fit_status=np.array([r["fit_status"] for r in rows])
        ensure(set(fit_status)<={"ResultFound","fit_failed"},f"Unknown fit status for {arm}")
        valid=fit_status=="ResultFound"
        status,src,why={}, {}, {}
        for panel,seed in product(PANELS,SEEDS):
            key=(panel,seed)
            src[key]=[checks[i,arm,panel,seed] for i in ids]
            stem="pit" if panel=="guidance" else "diagnostic"
            ensure(all(r["seed"]==case[f"{stem}_{seed}_seed"] for r,case in zip(src[key],rows)),
                   f"Panel seed mismatch for {arm}/{key}")
            status[key]=np.array([r["status"] for r in src[key]])
            why[key]=np.array([r["reason"] for r in src[key]])
            p=np.array([num(r["p"]) for r in src[key]])
            tested=np.isin(status[key],["keep","decline"])
            ensure(set(status[key])<={"keep","decline","check_failed","fit_failed"} and
                   np.array_equal(status[key]=="fit_failed",~valid) and np.isfinite(p[tested]).all()
                   and np.all((p[tested]>=0)&(p[tested]<=1))
                   and np.array_equal(status[key][tested]=="decline",p[tested]<.01),f"Invalid decisions for {arm}/{key}")
        estimates={}
        for ext in EXT:
            def endpoints(source,prefix):
                return np.array([[num(r[prefix+k]) for k in ("lower","upper")] for r in source])
            limits=endpoints(rows,ext+"_")
            z=endpoints(rows,ext+"_z_")
            finite=np.isfinite(limits).all(axis=1)
            ensure(np.array_equal(~finite,[logical(r[f"{ext}_nonfinite"]) for r in rows])
                   and not (finite & ~valid).any() and not np.isnan(z[finite]).any(),"Invalid limits or scores")
            for key in src:
                released=endpoints(src[key],f"released_{ext}_")
                expected=np.where(((status[key]=="keep") & finite)[:,None],limits,np.nan)
                ensure(np.array_equal(released,expected,equal_nan=True),f"Release mismatch for {arm}/{ext}/{key}")
            az=np.abs(z)
            estimates[ext]=dev.Estimates(z,finite,np.any(np.isfinite(limits)&(limits<=0),axis=1),
                finite & (limits[:,0]>=limits[:,1]),az.mean(axis=1),az.max(axis=1),np.minimum(az,5).mean(axis=1))
        arms[arm]=dev.Arm(valid,np.array([logical(r["fallback"]) for r in rows]),
                          np.array([r["reason"] for r in rows]),status,estimates)
        reasons[arm]=why
    return metadata,arms,reasons,audit


def strata(meta):
    values={"N_group":np.array([r["N"] for r in meta]),
            "pathology":np.array([dev.TARGET if float(r["fraction"])>.2 else dev.CONTROL for r in meta]),
            "disease":np.array([r["disease"] for r in meta]),"family":np.array([r["family"] for r in meta]),
            "fraction":np.array([str(float(r["fraction"])) for r in meta]),
            "rounding":np.array([str(float(r["rounding_fraction"])) for r in meta])}
    # Include all marginal and joint strata of the four comparison factors. Exact
    # fractions and rounding levels are also reported overall and by N/pathology.
    def mask_for(key):
        mask=np.ones(len(meta),dtype=bool)
        for k,v in key.items():
            if v!="all":
                mask &= values[k]==v
        return mask
    for n,p,d,f in product(*( ("all",*sorted(set(values[k]))) for k in ("N_group","pathology","disease","family"))):
        key=dict(PRIMARY,N_group=n,pathology=p,disease=d,family=f)
        yield key,mask_for(key)
    for axis in ("fraction","rounding"):
        for v,n,p in product(sorted(set(values[axis])),("all",*dev.N_GROUPS),("all",dev.TARGET,dev.CONTROL)):
            key=dict(PRIMARY,N_group=n,pathology=p); key[axis]=v
            mask=mask_for(key)
            if mask.any():
                yield key,mask


def compare(tables,group,boot,mask,scores,losses,returns):
    for arm,ext in product(ARMS[1:],EXT):
        for am,bm in (("pre","pre"),("checked","checked"),("checked","pre")):
            akey,bkey=(arm,ext,am),("baseline",ext,bm)
            a,b=scores[akey],scores[bkey]
            delta=losses[akey]-losses[bkey]
            n=len(delta)
            row=dict(**group,arm=arm,extraction=ext,candidate_mode=am,baseline_mode=bm,planned=n,
                arm_loss=a["all_set_loss"],baseline_loss=b["all_set_loss"],arm_implausible=a["implausible"],
                baseline_implausible=b["implausible"],arm_nonreturns=a["nonreturns"],baseline_nonreturns=b["nonreturns"],
                arm_fit_failures=a["fit_failures"],baseline_fit_failures=b["fit_failures"],
                **cluster_interval(boot,delta,np.ones(n,dtype=bool)))
            tables["paired-loss"].append(row)
            both=returns[akey] & returns[bkey]
            tables["common-returned"].append(dict(**group,arm=arm,extraction=ext,candidate_mode=am,baseline_mode=bm,
                planned=n,arm_returned=a["returned"],baseline_returned=b["returned"],both_returned=int(both.sum()),
                arm_loss=dev.average(losses[akey][both]),baseline_loss=dev.average(losses[bkey][both]),
                **cluster_interval(boot,np.where(both,delta,0),both)))
            formal=all(group[k]=="all" for k in ("disease","family","rounding","fraction"))
            if formal and ext=="native" and group["N_group"] in dev.N_GROUPS and group["pathology"]!="all" and am==bm:
                # Failures remain charged in both modes. Separate from decline & check failures,
                # raw fit failures are already evaluated by the pre-check nonreturn condition.
                loss_met=row["value"]<0 if group["pathology"]==dev.TARGET else row["value"]<=.02
                implausible_met=a["implausible"]<=b["implausible"]
                nonreturn_met=a["nonreturns"]<=b["nonreturns"]
                tables["gates"].append(dict(**row,decision="formal" if arm=="candidate" else "descriptive",
                    loss_met=loss_met,implausible_met=implausible_met,nonreturns_met=nonreturn_met,
                    all_met=loss_met and implausible_met and nonreturn_met))


def common_panel_noise(tables,key,boot,arms,mask):
    for seed in SEEDS:
        usable=[];flips=[]
        for arm in ("baseline","candidate"):
            a,b=(arms[arm].checks[p,seed][mask] for p in PANELS)
            usable.append(np.isin(a,["keep","decline"]) & np.isin(b,["keep","decline"]))
            flips.append(a!=b)
        ok=usable[0] & usable[1]
        a,b=flips
        tables["paired-panel-noise"].append(dict(**key,seed=seed,planned=len(ok),both_evaluable=int(ok.sum()),
            baseline_switches=int((a&ok).sum()),candidate_switches=int((b&ok).sum()),
            baseline_only=int((a&~b&ok).sum()),candidate_only=int((b&~a&ok).sum()),
            **cluster_interval(boot,np.where(ok,b.astype(int)-a,0),ok)))


def analyze(meta,arms,reasons):
    cells=np.array([int(r["cell_id"]) for r in meta])
    views={(a,e):dev.views(data,data.estimates[e]) for a,data in arms.items() for e in EXT}
    for group,mask in strata(meta):
        tables=defaultdict(list)
        boot=Bootstrap(cells[mask]); scores,losses,returns={},{},{}
        common_panel_noise(tables,group,boot,arms,mask)
        for arm,data in arms.items():
            spec=dict(**group,arm=arm)
            dev.flip_metrics(tables,spec,boot,data,mask)
            counts=Counter(data.reasons[mask & data.fallback])
            tables["fallback"].append(dict(**spec,planned=int(mask.sum()),fallback=int(data.fallback[mask].sum()),
                failed_fallback=int((data.fallback & ~data.fit_valid & mask).sum()),reason="all",count=int(data.fallback[mask].sum())))
            for reason,n in sorted(counts.items()):
                tables["fallback"].append(dict(**spec,planned=int(mask.sum()),fallback=int(data.fallback[mask].sum()),
                    failed_fallback=int((data.fallback & ~data.fit_valid & mask).sum()),reason=reason,count=n))
            for ext,model in data.estimates.items():
                key=dict(**spec,extraction=ext)
                dev.check_metrics(tables,key,boot,data,model,mask)
                for (panel,seed),reason in reasons[arm].items():
                    eligible=np.ones(int(mask.sum()),dtype=bool)
                    dev.rate(tables,"panel-rates",dict(**key,panel=panel,seed=seed,unit="dataset",
                        metric="structural_incompatibility"),boot,reason[mask]=="structural_incompatibility",eligible)
                for mode,(returned,loss) in views[arm,ext].items():
                    sk=(arm,ext,mode)
                    scores[sk]=dev.accuracy(tables,key,boot,mask,data,model,mode,returned,loss)
                    losses[sk]=loss[mask];returns[sk]=returned[mask]
        compare(tables,group,boot,mask,scores,losses,returns)
        yield group,tables


def factorial_cells(metadata,arms):
    """One row for each arm, extraction and mode within every original factorial cell."""
    cells=defaultdict(list)
    for i,r in enumerate(metadata):
        cells[r["cell_id"]].append(i)
    for c,ids in cells.items():
        r=metadata[ids[0]]
        info={k:r[k] for k in ("N","fraction","disease","family","rounding_fraction")}
        for a,e in product(ARMS,EXT):
            model=arms[a].estimates[e]
            for mode,(ret,loss) in dev.views(arms[a],model).items():
                bret,bloss=dev.views(arms["baseline"],arms["baseline"].estimates[e])[mode]
                yield dict(**info,cell_id=c,arm=a,extraction=e,mode=mode,planned=len(ids),
                    returned=int(ret[ids].sum()),baseline_returned=int(bret[ids].sum()),all_set_loss=np.mean(loss[ids]),
                    baseline_loss=np.mean(bloss[ids]),difference=np.mean(loss[ids]-bloss[ids]),
                    implausible=int((ret[ids] & (model.absolute[ids]>5)).sum()))


COMPRESSED={"accuracy","endpoints","coverage","paired-loss","common-returned","decision-pairs",
            "panel-rates","paired-panel-noise","fallback","factorial-cells"}


class Output:
    """Write one stratum at a time so full panel tables fit comfortably on the runner."""
    def __init__(self,directory):
        self.directory=directory;self.files={};self.writers={}
        directory.mkdir(parents=True,exist_ok=True)

    def add(self,name,rows):
        for r in rows:
            if name not in self.files:
                target=self.directory/(name+(".csv.gz" if name in COMPRESSED else ".csv"))
                if name in COMPRESSED:
                    raw=target.open("wb")
                    gz=gzip.GzipFile(filename="",mode="wb",fileobj=raw,mtime=0,compresslevel=5)
                    stream=io.TextIOWrapper(gz,encoding="utf-8",newline="")
                    handles=[stream,raw]
                else:
                    stream=target.open("w",encoding="utf-8",newline=""); handles=[stream]
                self.files[name]=handles
                self.writers[name]=csv.DictWriter(stream,fieldnames=list(r),lineterminator="\n")
                self.writers[name].writeheader()
            self.writers[name].writerow({k:"" if isinstance(v,(float,np.floating)) and np.isnan(v) else v
                                         for k,v in r.items()})
    def close(self):
        for handles in self.files.values():
            for handle in handles:
                handle.close()


def md_table(cols,rows):
    return ["", "| "+" | ".join(cols)+" |","| "+" | ".join("---" for _ in cols)+" |",
            *["| "+" | ".join(map(str,r))+" |" for r in rows], ""]


def render(table,audit):
    def lookup(name,**keys):
        rows=[r for r in table[name] if all(r[k]==v for k,v in keys.items())]
        ensure(len(rows)==1,f"Invalid summary filter for {name}: {keys}");return rows[0]
    def numfmt(x):
        return f"{x:.4f}" if np.isfinite(x) else "—"
    def interval(r,scale=1):
        if not np.isfinite(r["ci_low"]):
            return "—"
        return f"[{(scale*r['ci_low']):+.3f}, {(scale*r['ci_high']):+.3f}]"
    def pct(k,n):
        return f"{k:,}/{n:,} ({100*k/n:.1f}%)" if n else "0/0"
    def verdict(value):
        return "met" if value else "missed"
    gate=[r for r in table["gates"] if r["decision"]=="formal"]
    ensure(len(gate)==8,"Expected four native success gates per comparison mode")
    summary={m:all(r["all_met"] for r in gate if r["candidate_mode"]==m) for m in ("pre","checked")}
    lines=["# Stage 2 confirmation", "",
        f"The frozen K24 peak-only fitter **{verdict(summary['pre'])}** its prespecified native-limit criteria "
        f"against unchanged refineR. Its checked release **{verdict(summary['checked'])}** the criteria against "
        "refineR after both received the same check. The study used 2,880 fresh simulated routine datasets and "
        "eight independent replicates in each of 360 design cells. The frozen candidate and peak-only ablation "
        "had identical fits, limits and check decisions in all 2,880 cases.", "", "## Candidate versus refineR", "",
        "Each dataset contributes the average of the two absolute healthy-scale endpoint z errors after clipping "
        "each at 5. An unavailable interval contributes 5. A negative difference favors the candidate. The healthy "
        "Box–Cox support correction is included in the native limits used for the success criteria."]
    for mode,title in (("pre","Before checking"),("checked","Released after the primary guidance-panel check")):
        data=[]
        for n,p in product(dev.N_GROUPS,(dev.TARGET,dev.CONTROL)):
            r=lookup("gates",**dict(PRIMARY,N_group=n,pathology=p),arm="candidate",candidate_mode=mode)
            data.append([f"{int(n):,}",p,r["planned"],numfmt(r["arm_loss"]),numfmt(r["baseline_loss"]),
                         f"{r['value']:+.4f} {interval(r)}",
                         f"{r['arm_implausible']} / {r['baseline_implausible']}",
                         f"{r['arm_nonreturns']} / {r['baseline_nonreturns']}",verdict(r["all_met"])])
        lines+=["","### "+title]
        lines+=md_table(["N","Pathology","Datasets","Candidate loss","refineR loss","Δ [95% interval]",
                         "Implausible, candidate / refineR","Nonreturns, candidate / refineR","Gate"],data)
    lines+=["Above 20% pathology the loss difference must be strictly negative. At 20% or below the "
            "maximum permitted excess is 0.02. Both strata also require candidate implausible and nonreturn "
            "counts no greater than refineR. An implausible returned interval has uncapped mean absolute "
            "endpoint z error above 5. A missing or declined interval carries the full loss penalty. "
            "The gate decisions use the point estimates.", "", "## Individual components", "",
            "Each native-limit difference compares the indicated arm with unchanged refineR on identical "
            "datasets. The checked columns apply the primary check to both arms. The three component arms "
            "describe how the fixed search operations behaved in confirmation."]
    data=[]
    for n,p in product(dev.N_GROUPS,(dev.TARGET,dev.CONTROL)):
        key=dict(PRIMARY,N_group=n,pathology=p)
        row=[f"{int(n):,}",p]
        for a in ("peak","start","region"):
            for m in ("pre","checked"):
                r=lookup("paired-loss",**key,arm=a,extraction="native",candidate_mode=m,baseline_mode=m)
                row.append(f"{r['value']:+.4f}")
        data.append(row)
    lines+=md_table(["N","Pathology","Peak pre","Peak checked","Starts pre","Starts checked","Regions pre",
                     "Regions checked"],data)
    lines+=["## Coverage and error among returned intervals", "",
            "Overall means below give each dataset equal weight. The kept-set means use each arm's own "
            "finite returned intervals. The paired common-returned table additionally compares the methods "
            "on the same jointly available cases."]
    data=[]
    for a,m in product(ARMS,("pre","checked")):
        r=lookup("accuracy",**PRIMARY,arm=a,extraction="native",mode=m)
        data.append([LABELS[a],m,pct(r["returned"],r["planned"]),numfmt(r["kept_capped_mean_abs_z"]),
            numfmt(r["all_set_loss"]),r["implausible"],r["severe_E_gt5"],r["nonfinite"],r["out_of_support"],
            r["unordered"],r["fit_failures"],r["fallback"]])
    lines+=md_table(["Arm","Mode","Returned","Returned capped loss","All-set loss","Implausible","E > 5",
                     "Nonfinite","Outside support","Unordered","Fit failures","Fallbacks"],data)
    lines+=["## Disease distribution", "",
            "The following native paired differences pool both routine sample sizes. The fully crossed "
            "tables give disease, healthy family, pathology and sample size together."]
    data=[]
    for d in sorted({r["disease"] for r in table["paired-loss"]}-{"all"}):
        for p in (dev.TARGET,dev.CONTROL):
            key=dict(PRIMARY,disease=d,pathology=p)
            pre,checked=[lookup("paired-loss",**key,arm="candidate",extraction="native",candidate_mode=m,baseline_mode=m)
                         for m in ("pre","checked")]
            data.append([d,p,pre["planned"],f"{pre['value']:+.4f}",f"{checked['value']:+.4f}"])
    lines+=md_table(["Disease pattern","Pathology","Datasets","Pre-check Δ","Checked Δ"],data)
    lines+=["## Guidance and fresh-panel checks", "",
            "A fit is declined at p < 0.01. E is the larger absolute endpoint z error of the corresponding "
            "pre-check native fit. The capture and good-loss fractions below count every classifiable valid fit "
            "in that error category. The fresh panel was drawn independently of fitting. Actual release uses "
            "the guidance panel and primary randomized PIT seed."]
    data=[]
    for a,p,s in product(("baseline","candidate"),PANELS,SEEDS):
        key=dict(PRIMARY,arm=a,panel=p,seed=s,extraction="native",unit="dataset")
        rr=[lookup("panel-rates",**key,metric=m) for m in ("declined_evaluable","bad_gt1","bad_gt5","good_lt0.25")]
        data.append([LABELS[a],p,s,*[pct(r["count"],r["denominator"]) for r in rr]])
    lines+=md_table(["Arm","Panel","PIT seed","Evaluable declined","E > 1 caught","E > 5 caught",
                     "E < 0.25 declined"],data)
    data=[]
    for s in SEEDS:
        fractions=[]
        for a in ("baseline","candidate"):
            r=lookup("decision-pairs",**PRIMARY,arm=a,panel_a="guidance",seed_a=s,panel_b="diagnostic",seed_b=s)
            fractions.append(pct(r["count"],r["denominator"]))
        r=lookup("paired-panel-noise",**PRIMARY,seed=s)
        data.append([s,*fractions,r["both_evaluable"],r["candidate_only"],r["baseline_only"],
                     f"{100*r['value']:+.2f} {interval(r,100)}"])
    lines+=md_table(["PIT seed","refineR panel switches","Candidate panel switches","Common evaluable",
                     "Only candidate switched","Only refineR switched","Paired excess in points [95% interval]"],data)
    lines+=["Panel disagreement includes changes in both the 40 measurements and the randomized PIT draw. "
            "The paired excess uses only datasets evaluable under both panels in both arms. A fresh panel can "
            "change the decision even when a fit was made independently of both panels.", "",
            "## Descriptive endpoint and release comparisons", "",
            "The historical C2 extraction uses the same fitted parameters and check decisions. The native "
            "checked-candidate versus ungated-refineR comparison includes the cost of withholding an interval "
            "on the candidate side."]
    data=[]
    for n,p in product(dev.N_GROUPS,(dev.TARGET,dev.CONTROL)):
        key=dict(PRIMARY,N_group=n,pathology=p)
        values=[lookup("paired-loss",**key,arm="candidate",extraction=e,candidate_mode=a,baseline_mode=b)["value"]
             for e,a,b in (("historical","pre","pre"),("historical","checked","checked"),("native","checked","pre"))]
        data.append([f"{int(n):,}",p,*[f"{v:+.4f}" for v in values]])
    lines+=md_table(["N","Pathology","Historical pre Δ","Historical checked Δ","Native checked vs ungated Δ"],data)
    lines+=["## Reproducibility and files", "",
            f"All {audit['fits']:,} fits and {audit['checks']:,} check records passed the technical audit. "
            f"The same-host repeats matched across {audit['exact_repeat_shards']} shards. The distinct-host "
            f"comparison covered {audit['distinct_host_shards']} shards. Maximum differences were "
            f"{audit['max_endpoint_fraction']:.6g} of reference width for endpoints and "
            f"{audit['max_p_difference']:.6g} for p-values. [Audit](evidence/audit.json)", "",
            "The 95% descriptive intervals use 2,000 paired percentile resamples of factorial cells with "
            "PCG64 seed 37000000. All replicates in a sampled cell keep their common weight. Tables include "
            "valid and undefined replicate counts. An interval requires at least two informative cells.", "",
            "- All four primary strata include raw counts for each numerical gate. [Gate details](gates.csv)",
            "- Paired contrasts cover all marginal and joint groups of N, pathology, disease and healthy "
            "family, exact fractions and rounding, and all 360 factorial cells. "
            "[Paired loss](paired-loss.csv.gz) · [Common returned](common-returned.csv.gz) · [Cells](factorial-cells.csv.gz)",
            "- Each arm has before- and after-check accuracy, coverage, endpoint bias and error, and fallback "
            "counts by recorded reason. [Accuracy](accuracy.csv.gz) · [Coverage](coverage.csv.gz) · "
            "[Endpoints](endpoints.csv.gz) · [Fallbacks](fallback.csv.gz)",
            "- Both panels and both seeds have denominator-specific decline, bad capture, good loss, and failures, "
            "with separate endpoint-level analyses. [Panel rates](panel-rates.csv.gz) · "
            "[Decision reversals](decision-pairs.csv.gz) · [Paired panel disagreement](paired-panel-noise.csv.gz)",
            "- Each fit and each panel decision is available by dataset. [Fits](evidence/fits.csv.gz) · "
            "[Checks](evidence/checks.csv.gz)", ""]
    return "\n".join(lines)


def report(root,out):
    meta,arms,reasons,audit=load(root)
    writer=Output(out);summary=defaultdict(list)
    try:
        for group,tables in analyze(meta,arms,reasons):
            for name,rows in tables.items():
                writer.add(name,rows)
                if group["family"]=="all" and group["fraction"]==group["rounding"]=="all" and (
                    group["disease"]=="all" or (name=="paired-loss" and group["N_group"]=="all")):
                    summary[name].extend(rows)
        writer.add("factorial-cells",factorial_cells(meta,arms))
    finally:
        writer.close()
    (out/"REPORT.md").write_text(render(summary,audit),encoding="utf-8")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("audited_data_dir",type=Path);p.add_argument("output_dir",type=Path)
    args=p.parse_args()
    report(args.audited_data_dir,args.output_dir)
