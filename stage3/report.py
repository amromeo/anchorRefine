"""Report audited Stage 3 fixtures or development. Reads only the requested phase."""
import csv
import gzip
import json
import math
import os
from collections import Counter, defaultdict
from itertools import product
from pathlib import Path
import sys

os.environ["OPENBLAS_NUM_THREADS"]="1"
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage1.report import Bootstrap, average, logical, num, np, quantile
from stage2.report import Arm, Estimates, accuracy, check_metrics, cluster_interval, flip_metrics, views
from stage3.audit import CONFIG, EXTRACTIONS, FOCUS, NS, PANELS, SEEDS, SIDES, T, W, design, digest, require


def read(path):
    opener=gzip.open if str(path).endswith(".gz") else open
    with opener(path,"rt",newline="",encoding="utf-8") as f:
        yield from csv.DictReader(f)


def save(path,rows):
    if not rows:
        return
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k:"" if isinstance(v,(float,np.floating)) and math.isnan(v) else v for k,v in r.items()})


def table(columns,rows):
    lines=["| "+" | ".join(columns)+" |","| "+" | ".join("---" for _ in columns)+" |"]
    return "\n".join([*lines,*("| "+" | ".join(map(str,row))+" |" for row in rows)])


def fmt(v,n=4,sign=False):
    return "—" if v is None or v=="" or math.isnan(float(v)) else f"{float(v):+.{n}f}" if sign else f"{float(v):.{n}f}"


def label(arm):
    return {"baseline":"Unchanged refineR","stage2":"Stage 2","anchorsOnly":"Anchors-only"}.get(arm,arm)


def influence(evidence):
    by_arm=defaultdict(dict)
    for r in read(evidence/"fits.csv.gz"):
        by_arm[r["arm"]][int(r["j"])]=r
    rows=[]
    for n,arm in product(NS,W):
        values=[r for r in by_arm[arm].values() if int(r["N"])==n]
        require(len(values)==24,(arm,n,len(values)))
        shifts=[(num(r["center_shift"]),num(r["spread_shift"])) for r in values]
        paired=np.array([v for v in shifts if all(map(math.isfinite,v))],dtype=float).reshape((-1,2))
        m=len(paired)
        med=np.median(paired,axis=0) if m else [None,None]
        med_abs=np.median(abs(paired),axis=0) if m else [None,None]
        row=dict(N=n,weight=int(arm[1:]),planned=24,measurable=m,unevaluable=24-m,
                 center_signed=med[0],center_absolute=med_abs[0],spread_signed=med[1],spread_absolute=med_abs[1],
                 parent_failures=sum(by_arm["stage2"][int(r["j"])]["fit_status"]=="fit_failed" for r in values),
                 fit_failures=sum(r["fit_status"]=="fit_failed" for r in values),
                 fallbacks=sum(logical(r["fallback"]) for r in values),
                 inherited_fallback=sum(r["inherited_fallback"]=="TRUE" for r in values),
                 extra_fallback=sum(r["extra_fallback"]=="TRUE" for r in values),
                 parent_retained=sum(r["parent_retained"]=="TRUE" for r in values),
                 identical_fits=sum(r["fit_status"]=="ResultFound" and r["fit_hash"]==by_arm["stage2"][int(r["j"])]["fit_hash"] for r in values),
                 unchanged_center_spread=int((paired==0).all(axis=1).sum()))
        if arm=="w0" and m:
            require((paired==0).all(),(n,"weight-zero influence"))
        rows.append(row)
    return rows


def influence_text(rows):
    return "\n\n".join([
        "Each N has 24 fixtures. Center is the native median and spread is half the distance from the 15.87th to the 84.13th percentile, after mapping each quantile to the parent Stage 2 transformation. Shifts are candidate minus parent, divided by the parent Sigma. Medians include unchanged fits.",
        table(["N","w","Paired / 24","Center, signed","Center, absolute","Spread, signed","Spread, absolute","Unchanged fits","Fallbacks"],
              [[f"{int(r['N']):,}",r["weight"],r["measurable"],
                *(fmt(r[k],5) for k in ("center_signed","center_absolute","spread_signed","spread_absolute")),
                r["identical_fits"],r["fallbacks"]] for r in rows]),
        "[Full influence results](influence.csv)"])


def load_arm_data(evidence, phase):
    n,_,names=CONFIG[phase]
    # Retain only needed scalar fields. Raw case files also contain full search traces.
    fields=("fit_status","fallback","reason","center_shift","spread_shift","healthy_center_z","healthy_spread_z",
            "same_peak","healthy_median_in_basin","inherited_fallback","extra_fallback","parent_retained")
    est_fields=tuple(f"{e}_{k}" for e in EXTRACTIONS for k in ("lower","upper","z_lower","z_upper"))
    fits={a:[None]*n for a in names}
    checks={a:{(p,s):np.full(n,"",dtype="U13") for p,s in product(PANELS,SEEDS)} for a in names}
    for r in read(evidence/"fits.csv.gz"):
        jj=int(r["j"])-1
        require(fits[r["arm"]][jj] is None,(r["arm"],r["j"],"duplicate"))
        fits[r["arm"]][jj]={k:r[k] for k in (*fields,*est_fields)}
    for r in read(evidence/"checks.csv.gz"):
        statuses=checks[r["arm"]][r["panel"],r["seed_kind"]]
        jj=int(r["j"])-1
        require(not statuses[jj],"duplicate check")
        statuses[jj]=r["status"]

    arms={}; extras={}
    for a,rows in fits.items():
        require(all(r is not None for r in rows) and all((v!="").all() for v in checks[a].values()),(a,"incomplete"))
        data=Arm(np.array([r["fit_status"]=="ResultFound" for r in rows]),
                 np.array([logical(r["fallback"]) for r in rows]),np.array([r["reason"] for r in rows]),
                 checks[a],{})
        for ext in EXTRACTIONS:
            ends=np.array([[num(r[f"{ext}_{s}"]) for s in SIDES] for r in rows])
            z=np.array([[num(r[f"{ext}_z_{s}"]) for s in SIDES] for r in rows])
            finite=np.isfinite(ends).all(axis=1)
            scored=finite & ~np.isnan(z).any(axis=1)
            require(np.array_equal(scored,finite),(ext,a,"missing z on finite interval"))
            ab=np.abs(z)
            data.estimates[ext]=Estimates(z,scored,(ends<=0).any(axis=1),ends[:,0]>=ends[:,1],
                                         ab.mean(axis=1),ab.max(axis=1),np.minimum(ab,5.).mean(axis=1))
        arms[a]=data
        extras[a]={k:np.array([num(r[k]) for r in rows]) for k in ("center_shift","spread_shift","healthy_center_z","healthy_spread_z")}
        for k in ("same_peak","healthy_median_in_basin","inherited_fallback","extra_fallback","parent_retained"):
            extras[a][k]=np.array([r[k] for r in rows])
    return arms,extras


def selection(arms,meta):
    ref=views(arms["stage2"],arms["stage2"].estimates["native"])["pre"][1]
    control=meta["fraction"]<=.2
    focus=~control & np.isin(meta["disease"],tuple(FOCUS))
    sep=~control & ~focus
    rows=[]; chosen={}
    for arm_type, options in [("primary",W),("postfit",T)]:
        for a in options:
            diff=views(arms[a],arms[a].estimates["native"])["pre"][1]-ref
            r=dict(arm=arm_type,model=a,weight=float(a[1:]))
            for k,m,count in [("control",control,288),("focus",focus,432),("separated",sep,216)]:
                for n in NS:
                    v=diff[(meta["N"]==n)&m]
                    require(len(v)==count and np.isfinite(v).all(),(a,n,k,len(v)))
                    r[f"{k}_{n}"]=average(v)
            r["eligible"]=all(r[f"control_{n}"]<=.02 for n in NS)
            r["worst_focus"]=max(r[f"focus_{n}"] for n in NS)
            rows.append(r)
        eligible=[r for r in rows if r["arm"]==arm_type and r["eligible"]]
        require(any(r["weight"]==0 and r["worst_focus"]==0 for r in eligible),(arm_type,"zero weight"))
        chosen[arm_type]=min(eligible,key=lambda r:(r["worst_focus"],r["weight"]))["model"]
    for r in rows:
        r["selected"]=r["model"]==chosen[r["arm"]]
    return rows,chosen


def strata(meta,extras,chosen):
    n=meta["N"]; hi=meta["fraction"]>.2; focus=hi & np.isin(meta["disease"],tuple(FOCUS))
    all_rows=np.ones(len(n),bool)
    for size in (None,*NS):
        ns=all_rows if size is None else n==size
        for part,sub in (("all",all_rows),("control",~hi),("high",hi),("focus",focus),("separated_high",hi&~focus)):
            yield "N/pathology","all" if size is None else str(size),part,ns&sub
    for f in ("fraction","family","disease","rounding_fraction"):
        for v in sorted(set(meta[f])):
            for part,sub in (("all",all_rows),("control",~hi),("high",hi)):
                mask=(meta[f]==v)&sub
                if mask.any():
                    yield f,str(v),part,mask
    for f,arr in (("initial_peak_agrees",extras["stage2"]["same_peak"]),
                  ("basin_contains_healthy_median",extras["stage2"]["healthy_median_in_basin"])):
        for v in sorted(set(arr)):
            for part,sub in (("all",all_rows),("control",~hi),("high",hi)):
                mask=(arr==v)&sub
                if mask.any():
                    yield f,v or "unavailable",part,mask
    # Parent retention after a valid search is an available update, provided it
    # passed all eligibility checks. Inherited primary fallback has no update.
    primary=chosen["primary"]; post=chosen["postfit"]
    both=((extras[primary]["inherited_fallback"]!="TRUE") & (extras[primary]["extra_fallback"]!="TRUE")
          & (extras[post]["extra_fallback"]!="TRUE"))
    for name in (primary,post):
        both &= np.isfinite(extras[name]["center_shift"]) & np.isfinite(extras[name]["spread_shift"])
    if primary!="w0" and post!="t0" and both.any():
        yield "both_updates_available","yes","all",both


def analyze(meta,arms,extras,chosen):
    tables=defaultdict(list)
    selected=list(dict.fromkeys(("baseline","stage2",chosen["primary"],chosen["postfit"],"anchorsOnly")))
    estimates={(a,e):views(arm,arm.estimates[e]) for a,arm in arms.items() for e in EXTRACTIONS}
    for dim,level,part,mask in strata(meta,extras,chosen):
        k=dict(group=dim,level=level,pathology=part)
        boot=Bootstrap(meta["cell_id"][mask])
        study=dim=="N/pathology"
        include=list(arms) if study else selected
        scores={}
        for a in include:
            arm=arms[a]; key=dict(**k,arm=a)
            if a in selected:
                keys=Counter((reason,extra,inherit) for reason,extra,inherit in zip(arm.reasons[mask],
                             extras[a]["extra_fallback"][mask],extras[a]["inherited_fallback"][mask]))
                for (reason,extra,inherit),count in sorted(keys.items()):
                    tables["branches"].append(dict(**key,reason=reason,extra_fallback=extra,inherited_fallback=inherit,
                                                  count=count,total=int(mask.sum())))
                if a!="anchorsOnly" and study:
                    flip_metrics(tables,key,boot,arm,mask)
            for e in EXTRACTIONS:
                if e=="historical" and a not in selected:
                    continue
                model=arm.estimates[e]; ek=dict(**key,extraction=e)
                if a in selected and a!="anchorsOnly" and study and (part in ("control","high","focus") or level=="all"):
                    check_metrics(tables,ek,boot,arm,model,mask)
                for m,(ret,loss) in estimates[a,e].items():
                    scores[a,e,m]=accuracy(tables,ek,boot,mask,arm,model,m,ret,loss)
                    if a in selected:
                        curve=extras[a]; use=mask&ret
                        cc=curve["healthy_center_z"][use];ss=curve["healthy_spread_z"][use]
                        tables["curve"].append(dict(**ek,mode=m,planned=int(mask.sum()),returned=int(use.sum()),
                            center_n=int(np.isfinite(cc).sum()),mean_center_bias=average(cc[np.isfinite(cc)]),
                            spread_n=int(np.isfinite(ss).sum()),mean_spread_bias=average(ss[np.isfinite(ss)])))
        for a in include:
            refs=[b for b in ("stage2","baseline","anchorsOnly") if b!=a and (a in selected or b=="stage2")]
            for b in refs:
                for e in EXTRACTIONS if a in selected else ("native",):
                    for m,bm in [("pre","pre"),("checked","checked"),("checked","pre")]:
                        if m!=bm and not (b=="baseline" and a in selected):
                            continue
                        aa=scores[a,e,m]; bb=scores[b,e,bm]; ra,la=estimates[a,e][m]; rb,lb=estimates[b,e][bm]
                        d=(la-lb)[mask]
                        both=(ra&rb)[mask]
                        ci=cluster_interval(boot,d,np.ones(len(d),bool))
                        joint=cluster_interval(boot,np.where(both,d,0.),both)
                        row=dict(**k,arm=a,baseline=b,extraction=e,mode=m,baseline_mode=bm,planned=len(d),
                                 arm_loss=aa["all_set_loss"],baseline_loss=bb["all_set_loss"],
                                 arm_implausible=aa["implausible"],baseline_implausible=bb["implausible"],
                                 arm_nonreturns=aa["nonreturns"],baseline_nonreturns=bb["nonreturns"],
                                 common_returned=int(both.sum()),arm_common_loss=average(la[mask][both]),
                                 baseline_common_loss=average(lb[mask][both]),common_difference=joint["value"],
                                 common_ci_low=joint["ci_low"],common_ci_high=joint["ci_high"],**ci)
                        tables["paired-loss"].append(row)
                        if (a in chosen.values() and b=="baseline" and e=="native" and m==bm and study
                                and level!="all" and part in ("control","high")):
                            ok_loss=ci["value"]<=.02 if part=="control" else ci["value"]<0
                            ok_impl=aa["implausible"]<=bb["implausible"];ok_cov=aa["nonreturns"]<=bb["nonreturns"]
                            tables["development-gates"].append(dict(**row,loss_met=ok_loss,implausible_met=ok_impl,
                                nonreturn_met=ok_cov,all_met=bool(ok_loss and ok_impl and ok_cov)))
    return tables


def diagnostic_summary(evidence):
    groups=defaultdict(list)
    for r in read(evidence/"sensitivity.csv.gz"):
        groups[r["arm"],r["N"],r["w"],r["variant"]].append(r)
    result=[]
    for (arm,n,w,v),rr in sorted(groups.items(),key=lambda q:(q[0][0],int(q[0][1]),float(q[0][2]),q[0][3])):
        base=[num(r["base_upper"])-num(r["base_lower"]) for r in rr]
        delta=[max(abs(num(r["endpoint_delta_lower"])),abs(num(r["endpoint_delta_upper"])))/width
               for r,width in zip(rr,base) if width>0 and all(math.isfinite(num(r[k])) for k in ("endpoint_delta_lower","endpoint_delta_upper"))]
        status=Counter(r["status"] for r in rr)
        branches=Counter(r["branch"] for r in rr)
        result.append(dict(arm=arm,N=n,weight=w,variant=v,planned=len(rr),measurable=len(delta),
                           median_max_endpoint_fraction=quantile(np.array(delta),.5),
                           maximum_endpoint_fraction=max(delta,default=np.nan),
                           statuses=json.dumps(status,sort_keys=True),branches=json.dumps(branches,sort_keys=True)))
    return result


def development_text(tables,chosen,rank,inf,audit):
    def pick(which,**kw):
        rr=[r for r in tables[which] if all(r[k]==v for k,v in kw.items())]
        require(len(rr)==1,(which,kw,len(rr)))
        return rr[0]
    sections=["# Stage 3 development",
        f"The selected inside-fit weight is **w = {chosen['primary'][1:]}**. The selected post-fit weight is **t = {chosen['postfit'][1:]}**. All 3,744 independent development datasets enter the selection. Confirmation remains unopened.",
        "## Control eligibility and high-pathology target",
        "Entries are paired differences in pre-check native loss from the frozen Stage 2 fit, with 5 for missing fits. A positive difference increases loss. Eligibility requires all four control differences to be at most 0.02. Among eligible weights, the smallest worst difference on high-pathology shoulder and overlapping disease wins, with ties given to the smaller weight. These judgments use full precision.",
        table(["Arm","Weight",*(f"Control {n:,}" for n in NS),"Eligible",*(f"Focus {n:,}" for n in NS),"Worst focus","Selected"],
              [[r["arm"],f"{r['weight']:g}",*(fmt(r[f"control_{n}"],5,True) for n in NS),
                "Yes" if r["eligible"] else "No",*(fmt(r[f"focus_{n}"],5,True) for n in NS),
                fmt(r["worst_focus"],5,True),"Yes" if r["selected"] else ""] for r in rank]),
        "[Unrounded selection values, including high separated disease](selection.csv)",
        "## Influence before full development",influence_text(inf),
        "## Accuracy and coverage",
        "The primary release uses the original guidance panel and primary PIT seed. Mean loss counts each endpoint's absolute healthy-scale z error capped at five, and each nonreturn contributes five. Returned accuracy excludes nonreturns. The anchors-only row uses the C2 reporting rule."]
    overall=dict(group="N/pathology",level="all",pathology="all",extraction="native")
    acc=[]
    for a in dict.fromkeys(("baseline","stage2",*chosen.values(),"anchorsOnly")):
        for m in ("pre","checked"):
            r=pick("accuracy",**overall,arm=a,mode=m)
            acc.append([label(a),m,r["returned"],fmt(r["all_set_loss"]),fmt(r["kept_capped_mean_abs_z"]),
                        r["implausible"],r["fallback"],r["fit_failures"]])
    sections+= [table(["Arm","Mode","Returned / 3,744","All-set loss","Returned loss","Implausible","Fallbacks","Fit failures"],acc),
                "## Comparisons with unchanged refineR by N",
                "These synthetic development comparisons describe the selected weights. A fit passes above 20% pathology only with a lower mean loss. At or below 20%, the margin is 0.02. Each stratum also requires no extra nonreturns or implausible intervals. Both release methods receive the same check. An interval is implausible when its uncapped mean absolute endpoint error exceeds five.",
                table(["N","Pathology","Arm","Mode","Difference [95% interval]","Implausible, arm / refineR","Nonreturns, arm / refineR","Met"],
                    [[r["level"],r["pathology"],label(r["arm"]),r["mode"],
                      f"{fmt(r['value'],4,True)} [{fmt(r['ci_low'],4,True)}, {fmt(r['ci_high'],4,True)}]",
                      f"{r['arm_implausible']} / {r['baseline_implausible']}",f"{r['arm_nonreturns']} / {r['baseline_nonreturns']}",
                      "Yes" if r["all_met"] else "No"] for r in tables["development-gates"]]),
                "## Guidance and fresh-panel checks",
                "E is the larger absolute endpoint z error before checking. Each capture or loss denominator includes all classifiable valid fits in that group. Only guidance-panel decisions determine release."]
    panel=[]
    for a in dict.fromkeys(("baseline","stage2",*chosen.values())):
        for p in PANELS:
            labels=[]
            for metric in ("declined_evaluable","bad_gt1","bad_gt5","good_lt0.25"):
                r=pick("panel-rates",**overall,arm=a,panel=p,seed="primary",unit="dataset",metric=metric)
                labels.append(f"{r['count']}/{r['denominator']}")
            panel.append([label(a),p,*labels])
    sections +=[table(["Arm","Panel","Declined","E > 1 caught","E > 5 caught","E < 0.25 declined"],panel),
                "Paired intervals use 2,000 percentile bootstrap resamples of factorial cells, preserving their replicates, with PCG64 seed 37000000. Synthetic ground truth is available only to scoring. The technical audit covers every planned case and all primary, repeated and independent-host results.",
                f"All {audit['exact_repeat_shards']} same-host shard repeats and {audit['distinct_host_shards']} separate-host comparisons passed. The maximum cross-host endpoint difference was {audit['max_endpoint_fraction']:.4g} of reference width. The maximum absolute PIT probability difference was {audit['max_p_difference']:.4g}.",
                "[Paired losses and jointly returned results](paired-loss.csv) · [Accuracy](accuracy.csv) · [Endpoint errors](endpoints.csv) · [Center and spread bias](curve.csv) · [Fallback and peak decisions](branches.csv) · [Panel capture](panel-rates.csv) · [PIT-seed and panel disagreement](decision-pairs.csv) · [Unit, width and N sensitivity](sensitivity-summary.csv) · [Technical audit](evidence/audit.json) · [Case-level fits](evidence/fits.csv.gz) · [Case-level checks](evidence/checks.csv.gz)"]
    return "\n\n".join(sections)+"\n"


def report(phase,evidence,out):
    out.mkdir(parents=True,exist_ok=True)
    audit=json.loads((evidence/"audit.json").read_text())
    n,shards,_=CONFIG[phase]
    require(audit["phase"]==phase and audit["passed"] and audit["datasets"]==n and
            audit["exact_repeat_shards"]==audit["distinct_host_shards"]==shards,"Incomplete technical audit")
    receipt=dict(phase=phase,passed=True,datasets=n,audit_sha256=digest(evidence/"audit.json"))
    if phase=="influence":
        inf=influence(evidence)
        save(out/"influence.csv",inf)
        text="# Stage 3 influence check\n\nAll 96 frozen fixtures were evaluated before full development.\n\n"+influence_text(inf)
        text+=f"\n\nAll {shards} same-host repeats and {shards} distinct-host audits passed. [Technical audit](evidence/audit.json) · [Fixture identities](evidence/identities.csv.gz)\n"
        receipt["influence_sha256"]=digest(out/"influence.csv")
    else:
        planned=list(design(phase).values())
        meta={k:np.array([r[k] for r in planned]) for k in planned[0]}
        arms,extra=load_arm_data(evidence,phase)
        rank,chosen=selection(arms,meta)
        print(f"Development selection: {chosen}",flush=True)
        t=analyze(meta,arms,extra,chosen)
        for k,rows in t.items():save(out/(k+".csv"),rows)
        save(out/"selection.csv",rank)
        save(out/"sensitivity-summary.csv",diagnostic_summary(evidence))
        inf=list(read(out/"influence.csv"))
        require(len(inf)==24,"Expected 24 rows from prior influence report")
        receipt.update(chosen_w=float(chosen["primary"][1:]),chosen_t=float(chosen["postfit"][1:]),
                       selection_sha256=digest(out/"selection.csv"),influence_sha256=digest(out/"influence.csv"))
        text=development_text(t,chosen,rank,inf,audit)
    (out/"REPORT.md").write_text(text)
    receipt["report_sha256"]=digest(out/"REPORT.md")
    (out/"receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt),flush=True)


if __name__=="__main__":
    phase=sys.argv[1]
    if len(sys.argv)==4:
        evidence,out=map(Path,sys.argv[2:])
    else:
        out=Path(sys.argv[2])
        evidence=out/"evidence"
    report(phase,evidence,out)
