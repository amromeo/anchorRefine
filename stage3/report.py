"""Report the audited Stage 3 phase requested on the command line."""
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


def influence(evidence, parent_fallback=None):
    by_arm=defaultdict(dict)
    for r in read(evidence/"fits.csv.gz"):
        by_arm[r["arm"]][int(r["j"])]=r
    rows=[]
    for n,arm in product(NS,W):
        values=[r for r in by_arm[arm].values() if int(r["N"])==n]
        require(len(values)==24,(arm,n,len(values)))
        parents=by_arm["stage2"]
        if parent_fallback is not None:
            values=[r for r in values if logical(parents[int(r["j"])]["fallback"])==parent_fallback]
        total=len(values)
        shifts=[(num(r["center_shift"]),num(r["spread_shift"])) for r in values]
        paired=np.array([v for v in shifts if all(map(math.isfinite,v))],dtype=float).reshape((-1,2))
        m=len(paired)
        med=np.median(paired,axis=0) if m else [None,None]
        med_abs=np.median(abs(paired),axis=0) if m else [None,None]
        row=dict(N=n,weight=int(arm[1:]),planned=total,measurable=m,unevaluable=total-m,
                 center_signed=med[0],center_absolute=med_abs[0],spread_signed=med[1],spread_absolute=med_abs[1],
                 parent_failures=sum(by_arm["stage2"][int(r["j"])]["fit_status"]=="fit_failed" for r in values),
                 fit_failures=sum(r["fit_status"]=="fit_failed" for r in values),
                 fallbacks=sum(logical(r["fallback"]) for r in values),
                 inherited_fallback=sum(r["inherited_fallback"]=="TRUE" for r in values),
                 extra_fallback=sum(r["extra_fallback"]=="TRUE" for r in values),
                 parent_retained=sum(r["parent_retained"]=="TRUE" for r in values),
                 identical_fits=sum(r["fit_status"]=="ResultFound" and r["fit_hash"]==by_arm["stage2"][int(r["j"])]["fit_hash"] for r in values),
                 unchanged_center_spread=int((paired==0).all(axis=1).sum()),
                 parent_fallbacks=sum(logical(r["parent_fallback"]) for r in values),
                 weighted_attempts=sum(logical(r["weighted_search_attempted"]) for r in values),
                 weighted_entries=sum(logical(r["weighted_search_entered"]) for r in values),
                 updated_fits=sum(r["branch"]=="weighted" and r["fit_hash"]!=parents[int(r["j"])]["fit_hash"] for r in values),
                 retained_after_scoring=sum(r["branch"]=="retained_parent" for r in values))
        if arm=="w0" and m:
            require((paired==0).all(),(n,"weight-zero influence"))
        rows.append(row)
    return rows


INFLUENCE_TABLES = {"all": ("influence.csv","table_sha256"),
                    "nonfallback": ("influence-nonfallback.csv","nonfallback_sha256"),
                    "fallback": ("influence-fallback.csv","fallback_sha256")}


def influence_text(groups):
    sections=["Center is the native median and spread is half the distance between the 15.87th and 84.13th percentiles, after mapping each quantile to the parent Stage 2 transformation. Shifts are candidate minus parent, divided by parent Sigma. Unchanged fits contribute zero. Parent fallback status is fixed before any weighted search."]
    for group,title in [("all","All fixtures"),("nonfallback","Stage 2 non-fallback fixtures")]:
        sections.extend([f"### {title}",
            table(["N","w","Measured / assigned","Center signed","Center absolute","Spread signed","Spread absolute","Searches entered","Fits changed","Update failures"],
                  [[f"{int(r['N']):,}",r["weight"],f"{r['measurable']} / {r['planned']}",
                    *(fmt(r[k],5) for k in ("center_signed","center_absolute","spread_signed","spread_absolute")),
                    r["weighted_entries"],r["updated_fits"],r["extra_fallback"]] for r in groups[group]])])
    sections.extend(["### Searches on Stage 2 fallback fixtures",
        table(["N","Fallback fixtures","Positive-weight searches attempted / entered","Changed fits","Incumbent selected","Update failures"],
          [[f"{n:,}",rr[0]["planned"],f"{sum(int(r['weighted_attempts']) for r in rr)} / {sum(int(r['weighted_entries']) for r in rr)}",
            *(sum(int(r[k]) for r in rr) for k in ("updated_fits","retained_after_scoring","extra_fallback"))]
           for n in NS for rr in [[r for r in groups["fallback"] if int(r["N"])==n and int(r["weight"])>0]]]),
        "[All fixtures](influence.csv) · [Stage 2 non-fallback](influence-nonfallback.csv) · [Stage 2 fallback](influence-fallback.csv)"])
    return "\n\n".join(sections)


def load_arm_data(evidence, phase):
    n,_,names=CONFIG[phase]
    # Retain only needed scalar fields. Raw case files also contain full search traces.
    search_fields=("branch","parent_fallback","weighted_search_path","weighted_search_entered","weighted_search_attempted")
    fields=(*search_fields,"fit_status","fallback","reason","center_shift","spread_shift","healthy_center_z","healthy_spread_z",
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
        for k in (*search_fields,"same_peak","healthy_median_in_basin","inherited_fallback","extra_fallback","parent_retained"):
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


def strata(meta,extras,chosen,parent_fallback=None):
    n=meta["N"]; hi=meta["fraction"]>.2; focus=hi & np.isin(meta["disease"],tuple(FOCUS))
    all_rows=np.ones(len(n),bool)
    sizes=(None,*NS) if parent_fallback is None else (None,"<=5000",*NS)
    for size in sizes:
        ns=all_rows if size is None else n<=5000 if size=="<=5000" else n==size
        level="all" if size is None else str(size)
        for part,sub in (("all",all_rows),("control",~hi),("high",hi),("focus",focus),("separated_high",hi&~focus)):
            mask=ns&sub
            yield "N/pathology",level,part,mask
            if parent_fallback is not None:
                for group,parents in (("stage2_fallback",parent_fallback),("stage2_nonfallback",~parent_fallback)):
                    subset=mask & parents
                    if subset.any():
                        yield group,level,part,subset
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
    # A scored incumbent is an available weighted update on either parent path.
    # Direct zero-weight dispatch is reported as such and has no fitted update.
    primary=chosen["primary"]; post=chosen["postfit"]
    if primary!="w0" and post!="t0":
        both=(extras[primary]["weighted_search_entered"]=="TRUE") & (extras[primary]["extra_fallback"]!="TRUE")
        both &= extras[post]["extra_fallback"]!="TRUE"
        for name in (primary,post):
            both &= np.isfinite(extras[name]["center_shift"]) & np.isfinite(extras[name]["spread_shift"])
        for level,mask in (("yes",both),("parent_fallback",both & (extras[primary]["parent_fallback"]=="TRUE")),
                           ("parent_nonfallback",both & (extras[primary]["parent_fallback"]=="FALSE"))):
            if mask.any():
                yield "both_updates_available",level,"all",mask


def analyze(meta,arms,extras,chosen,confirmation=False):
    tables=defaultdict(list)
    selected=list(dict.fromkeys(("baseline","stage2",chosen["primary"],chosen["postfit"],"anchorsOnly")))
    estimates={(a,e):views(arm,arm.estimates[e]) for a,arm in arms.items() for e in EXTRACTIONS}
    parent_fallback=arms["stage2"].fallback if confirmation else None
    for dim,level,part,mask in strata(meta,extras,chosen,parent_fallback):
        k=dict(group=dim,level=level,pathology=part)
        boot=Bootstrap(meta["cell_id"][mask])
        study=dim=="N/pathology"
        parent_subset=dim in ("stage2_fallback","stage2_nonfallback")
        include=list(arms) if study and not confirmation else selected
        scores={}
        for a in include:
            arm=arms[a]; key=dict(**k,arm=a)
            if a in selected:
                branch_fields=("branch","parent_fallback","weighted_search_path","weighted_search_attempted",
                               "weighted_search_entered","extra_fallback","inherited_fallback","parent_retained")
                keys=Counter(zip(arm.reasons[mask],*(extras[a][f][mask] for f in branch_fields)))
                for values,count in sorted(keys.items()):
                    tables["branches"].append(dict(**key,**dict(zip(("reason",*branch_fields),values)),
                                                   count=count,total=int(mask.sum())))
                if a!="anchorsOnly" and (study or parent_subset):
                    flip_metrics(tables,key,boot,arm,mask)
            for e in EXTRACTIONS:
                if e=="historical" and a not in selected:
                    continue
                model=arm.estimates[e]; ek=dict(**key,extraction=e)
                if a in selected and a!="anchorsOnly" and (parent_subset or
                        (study and (confirmation or part in ("control","high","focus") or level=="all"))):
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
                            gate=dict(**row,loss_met=ok_loss,implausible_met=ok_impl,
                                      nonreturn_met=ok_cov,all_met=bool(ok_loss and ok_impl and ok_cov))
                            if confirmation:
                                if level in ("<=5000","50000"):
                                    tables["confirmation-gates"].append(gate)
                                if level!="<=5000":
                                    tables["confirmation-gates-by-n"].append(gate)
                            else:
                                tables["development-gates"].append(gate)
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
    enabled=chosen["primary"]!="w0" and chosen["postfit"]!="t0"
    subset=[]
    for level in ("yes","parent_nonfallback","parent_fallback"):
        for a in (chosen["primary"],chosen["postfit"]):
            rr=[r for r in tables["accuracy"] if r["group"]=="both_updates_available" and r["level"]==level
                 and r["extraction"]=="native" and r["arm"]==a and r["mode"]=="pre"]
            if rr:
                r=rr[0]
                subset.append([level,a,r["planned"],r["returned"],fmt(r["all_set_loss"])])
    subset_text=table(["Stage 2 parent subset","Arm","Assigned","Returned","Pre-check loss"],subset) if subset else (
       "At least one selected weight was zero, so no paired fitted updates were available." if not enabled else
       "No dataset had two available updates.")
    panel=[]
    for a in dict.fromkeys(("baseline","stage2",*chosen.values())):
        for p in PANELS:
            labels=[]
            for metric in ("declined_evaluable","bad_gt1","bad_gt5","good_lt0.25"):
                r=pick("panel-rates",**overall,arm=a,panel=p,seed="primary",unit="dataset",metric=metric)
                labels.append(f"{r['count']}/{r['denominator']}")
            panel.append([label(a),p,*labels])
    sections +=[table(["Arm","Panel","Declined","E > 1 caught","E > 5 caught","E < 0.25 declined"],panel),
                "## Both selected updates available",subset_text,
                "Paired intervals use 2,000 percentile bootstrap resamples of factorial cells, preserving their replicates, with PCG64 seed 37000000. Synthetic ground truth is available only to scoring. The technical audit covers every planned case and all primary, repeated and independent-host results.",
                f"All {audit['exact_repeat_shards']} same-host shard repeats and {audit['distinct_host_shards']} separate-host comparisons passed. The maximum cross-host endpoint difference was {audit['max_endpoint_fraction']:.4g} of reference width. The maximum absolute PIT probability difference was {audit['max_p_difference']:.4g}.",
                "[Paired losses and jointly returned results](paired-loss.csv) · [Accuracy](accuracy.csv) · [Endpoint errors](endpoints.csv) · [Center and spread bias](curve.csv) · [Fallback and peak decisions](branches.csv) · [Panel capture](panel-rates.csv) · [PIT-seed and panel disagreement](decision-pairs.csv) · [Unit, width and N sensitivity](sensitivity-summary.csv) · [Technical audit](evidence/audit.json) · [Case-level fits](evidence/fits.csv.gz) · [Case-level checks](evidence/checks.csv.gz)"]
    return "\n\n".join(sections)+"\n"


def confirmation_results(evidence,out,audit,receipt):
    phase="confirmation"
    chosen={"primary":"w1","postfit":"t0.25"}
    scientific=("baseline","stage2",*chosen.values(),"anchorsOnly")
    planned=list(design(phase).values())
    meta={k:np.array([r[k] for r in planned]) for k in planned[0]}
    arms,extras=load_arm_data(evidence,phase)
    tables=analyze(meta,arms,extras,chosen,confirmation=True)
    # The two parent subsets partition each complete stratum. Weight each
    # subgroup's difference by its actual fraction of that stratum.
    combined={}
    keys=("level","pathology","arm","baseline","extraction","mode","baseline_mode")
    for r in tables["paired-loss"]:
        if r["group"]=="N/pathology":
            combined[tuple(r[k] for k in keys)]=r
    contribution=defaultdict(float)
    counts=Counter()
    for r in tables["paired-loss"]:
        if r["group"] not in ("stage2_fallback","stage2_nonfallback"):
            continue
        key=tuple(r[k] for k in keys)
        total=combined[key]["planned"]
        part=r["value"]*r["planned"]/total
        contribution[key]+=part
        counts[key]+=r["planned"]
        tables["parent-comparisons"].append(dict(**r,stratum_total=total,contribution_to_stratum_difference=part))
    require(combined.keys()==counts.keys(),"Missing parent subset partition")
    for key,row in combined.items():
        require(counts[key]==row["planned"] and math.isclose(contribution[key],row["value"],abs_tol=2e-12),
                (key,"Parent subset denominators or mean losses do not add up"))
    for r in tables["accuracy"]:
        if r["group"]=="N/pathology" and r["extraction"]=="native" and r["arm"]=="stage2" and r["mode"]=="pre":
            tables["parent-counts"].append(dict(N=r["level"],pathology=r["pathology"],total=r["planned"],
                stage2_fallback=r["fallback"],stage2_nonfallback=r["planned"]-r["fallback"]))
    for name,levels in (("confirmation-gates",("<=5000","50000")),
                        ("confirmation-gates-by-n",tuple(map(str,NS)))):
        inventory=[(r["level"],r["pathology"],r["arm"],r["mode"]) for r in tables[name]]
        expected=set(product(levels,("control","high"),chosen.values(),("pre","checked")))
        require(len(inventory)==len(expected) and set(inventory)==expected,(name,"Incomplete gate comparisons"))
    for name,rows in tables.items():
        save(out/(name+".csv"),rows)

    def pick(name,**fields):
        matches=[r for r in tables[name] if all(r[k]==v for k,v in fields.items())]
        require(len(matches)==1,(name,fields,"Expected one result"))
        return matches[0]

    def gate_table(rows):
        return table(["N","Pathology","Arm","Mode","Assigned","Loss difference [95% interval]",
                      "Implausible, arm / refineR","Nonreturns, arm / refineR","All criteria met"],
                     [[r["level"],"≤20%" if r["pathology"]=="control" else ">20%",label(r["arm"]),r["mode"],
                       r["planned"],f"{fmt(r['value'],4,True)} [{fmt(r['ci_low'],4,True)}, {fmt(r['ci_high'],4,True)}]",
                       f"{r['arm_implausible']} / {r['baseline_implausible']}",
                       f"{r['arm_nonreturns']} / {r['baseline_nonreturns']}","Yes" if r["all_met"] else "No"] for r in rows])

    formal=tables["confirmation-gates"]
    verdicts={}
    for arm in chosen.values():
        verdicts[arm]={mode:all(r["all_met"] for r in formal if r["arm"]==arm and r["mode"]==mode)
                       for mode in ("pre","checked")}
    pass_word=lambda v:"passed" if v else "missed at least one gate"
    text=["# Stage 3 synthetic confirmation",
        "The primary arm used w = 1 and the post-fit comparator used t = 0.25 throughout the 7,488 fresh simulations. "
        f"The primary arm {pass_word(verdicts['w1']['pre'])} before checking and {pass_word(verdicts['w1']['checked'])} "
        f"after checking. The post-fit comparator {pass_word(verdicts['t0.25']['pre'])} before checking and "
        f"{pass_word(verdicts['t0.25']['checked'])} after checking. Both weights came from development. RIbench awaits review.",
        "## Prespecified comparisons with unchanged refineR",
        "A negative difference favors the Stage 3 arm. Each endpoint contributes its absolute native healthy-scale z error capped at 5. "
        "A missing interval contributes 5 on its own side. Above 20% pathology the paired mean difference must be strictly negative. "
        "At or below 20% it must be at most 0.02. Each comparison also requires at most as many implausible intervals "
        "(uncapped mean absolute endpoint error above 5) and at most as many nonreturns. Before-check and checked comparisons use matching refineR releases. "
        "The decision uses unrounded point estimates. The 95% intervals use 2,000 paired bootstrap resamples of factorial cells.",
        gate_table(formal),"[Formal comparisons at full precision](confirmation-gates.csv)",
        "## Each simulation sample size",gate_table(tables["confirmation-gates-by-n"]),
        "[Each N at full precision](confirmation-gates-by-n.csv)",
        "## Accuracy and coverage",
        "The guidance panel and primary randomized-PIT seed determine the checked release. Anchors-only retains its C2 reporting rule."]
    overall=dict(group="N/pathology",level="all",pathology="all",extraction="native")
    acc=[]
    for arm,mode in product(scientific,("pre","checked")):
        r=pick("accuracy",**overall,arm=arm,mode=mode)
        acc.append([label(arm),mode,r["planned"],r["returned"],fmt(r["all_set_loss"]),
                    fmt(r["kept_capped_mean_abs_z"]),r["implausible"],r["fit_failures"]])
    text.append(table(["Arm","Mode","Assigned","Returned","Mean loss","Mean among returned","Implausible","Fit failures"],acc))
    text.extend(["## Results when Stage 2 fell back",
        "Membership uses the original Stage 2 fallback flag on every dataset, including unsuccessful updates. "
        "The table compares each Stage 3 arm to Stage 2 before and after the guidance-panel check. "
        "A subset's contribution to the pooled pre-check difference is its mean difference multiplied by its share of all datasets at that N. "
        "An empty subset contributes zero."])
    subs=[]
    for size in ("<=5000",*map(str,NS)):
        counts_row=pick("parent-counts",N=size,pathology="all")
        for group in ("stage2_fallback","stage2_nonfallback"):
            count=counts_row[group]
            for arm in chosen.values():
                if count:
                    key=dict(group=group,level=size,pathology="all",arm=arm,baseline="stage2",extraction="native")
                    pre=pick("parent-comparisons",**key,mode="pre",baseline_mode="pre")
                    checked=pick("parent-comparisons",**key,mode="checked",baseline_mode="checked")
                    vals=[fmt(pre["arm_loss"]),fmt(pre["baseline_loss"]),fmt(pre["value"],4,True),
                          fmt(pre["contribution_to_stratum_difference"],4,True),fmt(checked["value"],4,True),
                          f"{count-checked['arm_nonreturns']} / {count-checked['baseline_nonreturns']}"]
                else:
                    vals=["—","—","—","0","—","0 / 0"]
                subs.append([size,"Fallback" if group=="stage2_fallback" else "Non-fallback",count,label(arm),*vals])
    text.extend([table(["N","Stage 2 parent","Assigned","Arm","Pre loss","Stage 2 pre loss","Pre difference","Contribution",
                        "Checked difference","Checked returned, arm / Stage 2"],subs),
        "All N and pathology combinations, including high-pathology shoulder/overlap and separated disease, are available with both extractions, paired intervals and coverage. "
        "The parent counts include empty subsets. Fractions and panel capture use their own displayed denominators. "
        "[Parent counts](parent-counts.csv) · [Parent comparisons](parent-comparisons.csv) · [Panel capture by parent](panel-rates.csv)",
        "## Fits where both updates were available"])
    both=[]
    for r in tables["accuracy"]:
        if r["group"]=="both_updates_available" and r["arm"] in chosen.values() and r["extraction"]=="native":
            both.append([r["level"],label(r["arm"]),r["mode"],r["planned"],r["returned"],fmt(r["all_set_loss"])])
    text.append(table(["Stage 2 parent subset","Arm","Mode","Assigned","Returned","Mean loss"],both)
                if both else "No datasets had both updates available.")
    text.extend(["## High-pathology comparisons at N = 50,000",
        "Gap closed is Stage 2 loss minus arm loss. Remaining gap is arm loss minus anchors-only loss. "
        "These are the observed gaps on the independent synthetic datasets. The previous RIbench gap was 0.0540."])
    gaps=[]
    for part in ("high","focus","separated_high"):
        for mode in ("pre","checked"):
            key=dict(group="N/pathology",level="50000",pathology=part,extraction="native",mode=mode)
            losses={arm:pick("accuracy",**key,arm=arm) for arm in scientific}
            for arm in chosen.values():
                s,a,o=[losses[x]["all_set_loss"] for x in ("stage2",arm,"anchorsOnly")]
                gaps.append([part,mode,losses[arm]["planned"],label(arm),fmt(s),fmt(a),fmt(o),fmt(s-a,4,True),fmt(a-o,4,True)])
    text.extend([table(["Pathology subset","Mode","Assigned","Arm","Stage 2","Arm loss","Anchors-only","Gap closed","Remaining gap"],gaps),
        "## Guidance and fresh-panel checks",
        "E is the larger absolute endpoint z error. Declines are shown among evaluable checks. Capture and good-result loss use all classifiable valid fits in each category."])
    panel=[]
    for group in ("N/pathology","stage2_fallback","stage2_nonfallback"):
        for arm,p in product(scientific[:-1],PANELS):
            key=dict(group=group,level="all",pathology="all",extraction="native",arm=arm,panel=p,seed="primary",unit="dataset")
            if not any(r["group"]==group for r in tables["parent-comparisons"]) and group!="N/pathology":
                continue
            rr=[pick("panel-rates",**key,metric=metric) for metric in ("declined_evaluable","bad_gt1","bad_gt5","good_lt0.25")]
            panel.append(["All" if group=="N/pathology" else group.removeprefix("stage2_"),label(arm),p,
                          *(f"{r['count']}/{r['denominator']}" for r in rr)])
    text.extend([table(["Stage 2 parent","Arm","Panel","Declined","E > 1 caught","E > 5 caught","E < 0.25 declined"],panel),
        "The case-level exports retain both PIT seeds, the guidance and fresh panels, both extractors and every fit failure. "
        "The two zero-weight labels audit identity with Stage 2. The five scientific arms are unchanged refineR, Stage 2, w1, t0.25 and anchors-only. "
        "[Task G fit objects and join keys](TASK-G.md) · [Per-dataset fits](evidence/fits.csv.gz) · [Per-dataset checks](evidence/checks.csv.gz)",
        "## Reproducibility",
        f"All {audit['exact_repeat_shards']} same-host repetitions and {audit['distinct_host_shards']} separate-host shard comparisons passed. "
        f"The maximum cross-host endpoint difference was {audit['max_endpoint_fraction']:.6g} of interval width. "
        f"The maximum absolute difference between PIT probabilities was {audit['max_p_difference']:.6g}. "
        "[Technical audit](evidence/audit.json) · [Fit branches and failure reasons](branches.csv) · [Historical and native paired results](paired-loss.csv) · "
        "[Endpoint errors](endpoints.csv) · [Healthy center and spread by elected basin](curve.csv) · [Coverage](coverage.csv) · "
        "[PIT-seed and panel disagreement](decision-pairs.csv)",
        "## Observations from development",
        "Unit sensitivity was already present in the refineR-based Stage 2 fit. A change of measurement units moved at least one "
        "back-converted endpoint by more than 0.1% of interval width on 36 of 720 Stage 2 datasets, 35 for the primary arm "
        "and 36 for the post-fit arm. In development, t = 0.5 reduced small-N control error but increased control error by 0.0431 at N = 50,000. "
        "Studying a blend weight that varies with N would require new development and confirmation samples. "
        "[Stage 3 development](../stage3-development/REVIEW.md)"])
    receipt.update(technical_audit_passed=True,scientific_gate_results=verdicts,fixed_w=1,fixed_t=.25,
                   formal_gates_sha256=digest(out/"confirmation-gates.csv"),by_n_gates_sha256=digest(out/"confirmation-gates-by-n.csv"),
                   parent_comparisons_sha256=digest(out/"parent-comparisons.csv"),
                   fits_sha256=digest(evidence/"fits.csv.gz"),checks_sha256=digest(evidence/"checks.csv.gz"))
    return "\n\n".join(text)+"\n"


def report(phase,evidence,out):
    out.mkdir(parents=True,exist_ok=True)
    audit=json.loads((evidence/"audit.json").read_text())
    n,shards,_=CONFIG[phase]
    require(audit["phase"]==phase and audit["passed"] and audit["datasets"]==n and
            audit["exact_repeat_shards"]==audit["distinct_host_shards"]==shards,"Incomplete technical audit")
    receipt=dict(phase=phase,passed=True,datasets=n,audit_sha256=digest(evidence/"audit.json"))
    if phase=="influence":
        inf={name:influence(evidence,subset) for name,subset in (("all",None),("nonfallback",False),("fallback",True))}
        for name,(filename,field) in INFLUENCE_TABLES.items():
            save(out/filename,inf[name])
            receipt[field]=digest(out/filename)
        receipt["influence_sha256"]=receipt["table_sha256"]
        original=evidence/"original-influence-audit.json"
        prior=json.loads(original.read_text())
        require(prior["passed"] and prior["datasets"]==n,"Original influence equivalence missing")
        receipt["original_audit_sha256"]=digest(original)
        text="# Stage 3 amended influence check\n\nAll 96 frozen fixtures were evaluated before full development.\n\n"+influence_text(inf)
        text+=f"\n\nAll {shards} same-host repeats and {shards} distinct-host comparisons passed. The comparison to the original run verified all 96 Stage 2 parents, all 96 weight-zero results and {prior['paths']['guided_positive']['fits']} positive-weight non-fallback fits against the practical tolerances. [Original-run comparison by path](evidence/original-influence-audit.json) · [Technical audit](evidence/audit.json) · [Fixture identities](evidence/identities.csv.gz)\n"
    elif phase=="confirmation":
        text=confirmation_results(evidence,out,audit,receipt)
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
        inf={name:list(read(out/filename)) for name,(filename,field) in INFLUENCE_TABLES.items()}
        require(all(len(rr)==24 for rr in inf.values()),"Incomplete amended influence tables")
        for name,(filename,field) in INFLUENCE_TABLES.items():
            receipt[field]=digest(out/filename)
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
