"""Report the audited RIbench evaluation of the frozen K24 peak-only candidate.

python stage2/ribench/report.py {small,large} AUDITED_DIRECTORY OUTPUT_DIRECTORY
"""
import argparse
import csv
import gzip
import io
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import product
from pathlib import Path

os.environ["OPENBLAS_NUM_THREADS"] = "1"
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from stage1 import report as s1
from stage1.report import Bootstrap, Method, average, ensure, logical, np, num
from stage2.report import cluster_interval

ARMS=("baseline","candidate","peak","start","region")
COMPARATORS=("taskE_armB","anchoredRI_improved","anchorsOnly")
LABELS=dict(baseline="Unchanged refineR",candidate="Frozen K24 peak-only candidate",peak="Peak only",
            start="Starting values only",region="Search regions only",taskE_armB="anchoredRI Arm B (Task E)",
            anchoredRI_improved="Improved anchoredRI baseline",anchorsOnly="Anchors only")
EXT=("native","historical")
SEEDS=("primary","alternate")
SIDES=("lower","upper")
COMPARATOR_INPUT=Path(__file__).with_name("comparators")/"comparators.csv.gz"


@dataclass
class Fit:
    estimates: dict
    out: dict
    valid: np.ndarray
    fallback: np.ndarray
    reason: np.ndarray
    step: np.ndarray
    decisions: dict
    check_reasons: dict


def read(path):
    opener=gzip.open if path.suffix==".gz" else open
    with opener(path,"rt",encoding="utf-8-sig",newline="") as stream:
        return list(csv.DictReader(stream))


def matrix(rows,fields):
    return np.array([[num(r[k]) for k in fields] for r in rows])


def model(z,limits,truth,lower,matched,statuses):
    finite=np.isfinite(limits[:,1]) & (~lower | np.isfinite(limits[:,0]))
    ensure(not np.isfinite(limits[~lower,0]).any() and np.isnan(z[~lower,0]).all(),
           "CRP lower limits or scores present")
    state=np.array(statuses)
    returned=(state=="returned") & finite
    ensure(np.array_equal(returned,state=="returned"),"Returned result lacks an endpoint")
    scored=returned & ~np.isnan(z[:,1]) & (~lower | ~np.isnan(z[:,0]))
    az=np.abs(z); clipped=np.minimum(az,5)
    abs_mean=np.where(lower,(az[:,0]+az[:,1])/2,az[:,1])
    capped=np.where(lower,(clipped[:,0]+clipped[:,1])/2,clipped[:,1])
    maximum=np.where(lower,np.maximum(az[:,0],az[:,1]),az[:,1])
    return Method(z,limits,truth,np.repeat(state[:,None],2,axis=1).astype(object),matched,returned,scored,
                  maximum,abs_mean,capped,lower)


def load_inputs(directory,cohort):
    audit=json.loads((directory/"audit.json").read_text())
    n=2880 if cohort=="small" else 1440
    ensure(audit["passed"] is True and (audit["datasets"],audit["fits"],audit["checks"])==(n,n*5,n*10)
           and audit["exact_repeat_shards"]==audit["distinct_host_shards"]>0,"Incomplete cohort audit")
    fr,cr=read(directory/"fits.csv"),read(directory/"checks.csv")
    fd={(int(r["Index"]),r["arm"]):r for r in fr}
    cd={(int(r["Index"]),r["arm"],r["seed_kind"]):r for r in cr}
    ids=sorted({i for i,a in fd})
    ensure(len(ids)==n and len(fd)==len(fr) and set(fd)==set(product(ids,ARMS)), "Invalid fit inventory")
    ensure(len(cd)==len(cr) and set(cd)==set(product(ids,ARMS,SEEDS))
           and all(r["panel"]=="guidance" for r in cr),"Invalid check inventory")
    cases=[fd[i,"baseline"] for i in ids]
    ensure(Counter(int(r["N"]) for r in cases)==({1000:1440,5000:1440} if cohort=="small" else {50000:1440}),
           "Incorrect RIbench sample sizes")
    lower=np.array([r["Analyte"]!="CRP" for r in cases])
    truth=matrix(cases,["truth_lower","truth_upper"])
    ensure(np.isnan(truth[~lower,0]).all() and np.isfinite(truth[lower,0]).all()
           and np.isfinite(truth[:,1]).all(),"Missing truth for a requested limit")
    outputs={}
    peak_rows=[fd[i,"candidate"] for i in ids]
    compare=[]
    for r in peak_rows:
        if r["clarity"] in ("NA",""):
            compare.append("unavailable")
        elif not logical(r["clarity"]):
            compare.append("unclear")
        elif r["same_peak"] in ("NA",""):
            compare.append("unavailable")
        else:
            equal=logical(r["same_peak"])
            ensure(equal==(int(r["upstream_peak_index"])==int(r["anchor_initial_index"])),"Peak comparison differs")
            compare.append("same" if equal else "different")
    for arm in ARMS:
        rows=[fd[i,arm] for i in ids]
        for r,b in zip(rows,cases):
            ensure(all(r[k]==b[k] for k in ("Index","N","Scenario","fractionPathol","Analyte","routine_hash",
                                              "anchor_hash","ribench_hashcode","truth_lower","truth_upper","requested_lower"))
                   and logical(r["requested_lower"])==(r["Analyte"]!="CRP"),"Unpaired RIbench inputs")
        valid=np.array([r["fit_status"]=="ResultFound" for r in rows])
        ensure(all(r["fit_status"] in ("ResultFound","fit_failed") for r in rows),"Unexpected fit status")
        md,out,dec,reason={}, {}, {}, {}
        for ext in EXT:
            limit=matrix(rows,[f"{ext}_{k}" for k in SIDES]); z=matrix(rows,[f"{ext}_z_{k}" for k in SIDES])
            finite=np.isfinite(limit[:,1]) & (~lower | np.isfinite(limit[:,0]))
            ensure(np.array_equal(~finite,[logical(r[f"{ext}_nonfinite"]) for r in rows])
                   and not (finite & ~valid).any(),"Fit status differs from limits")
            out[ext]=np.array([any(r[f"{ext}_out_{s}"] not in ("","NA","NaN") and logical(r[f"{ext}_out_{s}"])
                                    for s in SIDES) for r in rows])
            status=np.where(finite,"returned",np.where(valid,"extraction_failed","fit_failed"))
            md[ext]=model(z,limit,truth,lower,np.ones(n,dtype=bool),status)
        for seed,offset in (("primary",38000000),("alternate",39000000)):
            checks=[cd[i,arm,seed] for i in ids]
            d=np.array([r["status"] for r in checks]); pv=np.array([num(r["p"]) for r in checks])
            tested=np.isin(d,("keep","decline"))
            ensure(np.array_equal([int(r["seed"]) for r in checks],np.array(ids)+offset)
                   and set(d)<={"keep","decline","check_failed","fit_failed"}
                   and np.array_equal(d=="fit_failed",~valid) and np.isfinite(pv[tested]).all()
                   and np.all((pv[tested]>=0)&(pv[tested]<=1)) and np.array_equal(d[tested]=="decline",pv[tested]<.01),
                   f"Unexpected {arm} check for {seed}")
            dec[seed]=d;reason[seed]=np.array([r["reason"] for r in checks])
            for ext in EXT:
                rel=matrix(checks,[f"released_{ext}_{k}" for k in SIDES]); est=md[ext]
                expected=np.where(((d=="keep") & est.returned)[:,None],est.estimate,np.nan)
                ensure(np.array_equal(rel,expected,equal_nan=True),"Released limit differs from the recorded decision")
        steps=["none" if not logical(r["fallback"]) else
               (r["reason"].split(maxsplit=1)[0] if r["clarity"] not in ("","NA") and logical(r["clarity"])
                else "initial_election") for r in rows]
        outputs[arm]=Fit(md,out,valid,np.array([logical(r["fallback"]) for r in rows]),np.array([r["reason"] for r in rows]),
                          np.array(steps),dec,reason)
    for i in ids:
        a,b=fd[i,"candidate"],fd[i,"peak"]
        for k in ("fit_hash","fit_status","fallback","reason","peak_index","Mu","Sigma","Lambda","Shift",
                  *(f"{e}_{field}" for e in EXT for field in ("lower","upper","z_lower","z_upper"))):
            ensure(a[k]==b[k],f"Candidate and peak-only arms differ at {i}/{k}")
        for seed in SEEDS:
            a,b=cd[i,"candidate",seed],cd[i,"peak",seed]
            ensure(all(a[k]==b[k] for k in a if k!="arm"),f"Candidate and peak-only check differ at {i}")
    return cases,outputs,np.array(compare),audit


def load_comparators(cases,path=COMPARATOR_INPUT):
    ids={int(r["Index"]) for r in cases}
    source=[r for r in read(path) if int(r["Index"]) in ids]
    entries={(int(r["Index"]),r["method"]):r for r in source}
    ensure(len(entries)==len(source) and all(m in COMPARATORS for _,m in entries),"Duplicate or unrecognized comparator")
    cmp={}
    truth=matrix(cases,["truth_lower","truth_upper"])
    lower=np.array([r["Analyte"]!="CRP" for r in cases])
    for method,variant in product(COMPARATORS,("raw","reported")):
        prefix="" if variant=="raw" else "reported_"
        statuses=[];matched=[]; limits=[]; z=[]
        for info in cases:
            r=entries.get((int(info["Index"]),method))
            status=r[prefix+"status"] if r else "unavailable"
            ensure(status in {"returned","declined","fit_failed","extraction_failed","unavailable"},
                   f"Unknown archived status {method}/{variant}: {status}")
            present=status!="unavailable" and r is not None
            if present:
                ensure(int(r["N"])==int(info["N"]) and r["Analyte"]==info["Analyte"]
                       and all(r[k]==info[k] for k in ("routine_hash","anchor_hash")),
                       f"Comparator identity mismatch for {method} at Index {info['Index']}")
            matched.append(present);statuses.append(status)
            limits.append([num(r[prefix+s]) if r else np.nan for s in SIDES])
            z.append([num(r[prefix+"z_"+s]) if r else np.nan for s in SIDES])
        cmp[method,variant]=model(np.asarray(z),np.asarray(limits),truth,lower,np.array(matched),statuses)
    return cmp


def strata(cases):
    size=np.array([r["N"] for r in cases]);an=np.array([r["Analyte"] for r in cases])
    scenario=np.array([r["Scenario"] for r in cases])
    frac=np.array([float(r["fractionPathol"]) for r in cases])
    criteria=np.where(frac>.2,">20%","<=20%"); all_rows=np.ones(len(size),dtype=bool)
    for group,mask in [("all",all_rows),(">20%",frac>.2),("<=20%",frac<=.2)]:
        yield dict(group="all" if group=="all" else "pathology",stratum="All" if group=="all" else group),mask
    for name,fields in [
        ("N",(size,)),("analyte",(an,)),("fraction",(frac,)),("scenario",(scenario,)),
        ("N/pathology",(size,criteria)),("analyte/pathology",(an,criteria)),("scenario/pathology",(scenario,criteria)),
        ("N/analyte",(size,an)),("N/fraction",(size,frac)),("analyte/fraction",(an,frac)),
        ("analyte/scenario",(an,scenario)),("analyte/N/fraction",(an,size,frac))]:
        for values in sorted(set(zip(*fields))):
            mask=all_rows.copy()
            for labels,v in zip(fields,values):
                mask &= labels==v
            label="/".join(format(v,"g") if isinstance(v,(float,np.floating)) else str(v) for v in values)
            yield dict(group=name,stratum=label),mask


def pair(key,a,b,boot,mask):
    matched=a.paired & b.paired & mask
    common=matched & a.scored & b.scored
    aa=np.where(a.scored,a.capped,5);bb=np.where(b.scored,b.capped,5)
    shift=cluster_interval(boot,np.where(matched,aa-bb,0),matched)
    partial=cluster_interval(boot,np.where(common,aa-bb,0),common)
    return dict(**key,planned=int(mask.sum()),matched=int(matched.sum()),unmatched=int((mask & ~matched).sum()),
        arm_returned=int((matched&a.returned).sum()),baseline_returned=int((matched&b.returned).sum()),
        arm_scored=int((matched&a.scored).sum()),baseline_scored=int((matched&b.scored).sum()),
        arm_nonreturns=int((matched&~a.returned).sum()),baseline_nonreturns=int((matched&~b.returned).sum()),
        arm_implausible=int((matched&a.scored&(a.absolute>5)).sum()),baseline_implausible=int((matched&b.scored&(b.absolute>5)).sum()),
        arm_loss=average(aa[matched]),baseline_loss=average(bb[matched]),
        arm_returned_scored_mean=average(a.capped[matched&a.scored]),baseline_returned_scored_mean=average(b.capped[matched&b.scored]),
        common_scored=int(common.sum()),arm_common_mean=average(aa[common]),baseline_common_mean=average(bb[common]),
        common_difference=partial["value"],common_ci_low=partial["ci_low"],common_ci_high=partial["ci_high"],
        common_clusters=partial["informative_cells"],common_bootstrap_valid=partial["bootstrap_valid"],**shift)


def analyze(cases,arms,peaks,comp,cohort):
    for group,subset in strata(cases):
        tbl=defaultdict(list)
        ids=np.flatnonzero(subset); n=len(ids); sel=np.ones(n,dtype=bool)
        key=dict(cohort=cohort,**group)
        boot=Bootstrap([(cases[i]["Analyte"],cases[i]["Scenario"]) for i in ids])
        pk=peaks[subset]; clear=np.isin(pk,("same","different")); fell=arms["candidate"].fallback[subset]
        for name,event,elig in (("different_all",pk=="different",sel),("different_clear",pk=="different",clear),
                ("same_all",pk=="same",sel),("unclear_all",pk=="unclear",sel),("unavailable_all",pk=="unavailable",sel),
                ("candidate_fallback",fell,sel)):
            both=event & elig
            tbl["peak-fallback"].append(dict(**key,metric=name,planned=n,clear=int(clear.sum()),same=int((pk=="same").sum()),
                different=int((pk=="different").sum()),unclear=int((pk=="unclear").sum()),
                unavailable=int((pk=="unavailable").sum()),fallback=int(fell.sum()),count=int(both.sum()),denominator=int(elig.sum()),
                **cluster_interval(boot,both,elig)))
        models={}; validity={}
        for arm,data in arms.items():
            fallback=data.fallback[subset]
            validity[arm]=data.valid[subset]
            pre_dec=data.decisions["primary"][subset];other=data.decisions["alternate"][subset]
            both=np.isin(pre_dec,("keep","decline")) & np.isin(other,("keep","decline"))
            flips=both & (pre_dec!=other)
            tbl["seed-changes"].append(dict(**key,arm=arm,planned=n,both_evaluable=int(both.sum()),changed=int(flips.sum()),
                keep_to_decline=int(((pre_dec=="keep")&(other=="decline")).sum()),
                decline_to_keep=int(((pre_dec=="decline")&(other=="keep")).sum()),**cluster_interval(boot,flips,both)))
            counts=Counter(zip(data.step[subset][fallback],data.reason[subset][fallback]))
            for (step,reason),count in [(("all","all"),int(fallback.sum())),*sorted(counts.items())]:
                tbl["fallback"].append(dict(**key,arm=arm,step=step,reason=reason,count=count,fallback=int(fallback.sum()),
                    planned=n,fallback_fit_failed=int((fallback&~data.valid[subset]).sum())))
            for ext in EXT:
                base=data.estimates[ext].subset(ids)
                models[arm,ext,"pre"]=base
                models[arm,ext,"checked"]=base.gated(pre_dec=="keep",pre_dec)
                for seed in SEEDS:
                    spec=dict(**key,arm=arm,extraction=ext,seed=seed,mode="check")
                    d=data.decisions[seed][subset]
                    s1.check_metrics(tbl,spec,boot,base,d,data.check_reasons[seed][subset],data.valid[subset])
                for mode in ("pre","checked"):
                    m=models[arm,ext,mode]
                    spec=dict(**key,arm=arm,extraction=ext,seed="primary" if mode=="checked" else "none",mode=mode)
                    s1.accuracy(tbl,spec,boot,m,sel)
                    eligible=sel if mode=="pre" else pre_dec=="keep"
                    acc=tbl["accuracy"][-1]
                    acc.update(fit_failures=int((~data.valid[subset]).sum()),nonreturns=int((~m.returned).sum()),
                        unscored_returned=int((m.returned&~m.scored).sum()),nonfinite=int((eligible&~base.returned).sum()),
                        fallback=int(fallback.sum()),implausible=int((m.scored&(m.absolute>5)).sum()),
                        severe=int((m.scored&(m.maximum>5)).sum()),out_of_support=int((eligible&data.out[ext][subset]).sum()),
                        unordered_two_sided=int((m.returned & m.lower_needed & (m.estimate[:,0]>=m.estimate[:,1])).sum()),
                        CRP_nonpositive_upper=int((m.returned & ~m.lower_needed & (m.estimate[:,1]<=0)).sum()))
        for a,ext in product(ARMS[1:],EXT):
            for mode,bm in (("pre","pre"),("checked","checked"),("checked","pre")):
                r=pair(dict(**key,arm=a,extraction=ext,mode=mode,baseline="baseline",baseline_mode=bm),
                       models[a,ext,mode],models["baseline",ext,bm],boot,sel)
                tbl["paired-loss"].append(r)
                if group["group"]=="pathology" and ext=="native" and mode==bm:
                    err=r["value"]<0 if group["stratum"]==">20%" else r["value"]<=.02
                    impl=r["arm_implausible"]<=r["baseline_implausible"]
                    coverage=r["arm_nonreturns"]<=r["baseline_nonreturns"]
                    auditable=r["matched"]==n
                    tbl["gates"].append(dict(**r,arm_fit_failure=int((~validity[a]).sum()),
                        baseline_fit_failure=int((~validity["baseline"]).sum()),label="formal" if a=="candidate" else "descriptive",
                        loss_met=err,implausible_met=impl,nonreturn_met=coverage,complete=auditable,
                        all_met=bool(err and impl and coverage and auditable)))
        for (method,variant),original in comp.items():
            ref=original.subset(ids)
            for ext,a in product(EXT,("candidate","baseline")):
                mode="pre" if variant=="raw" else "checked"
                tbl["comparators"].append(pair(dict(**key,arm=a,extraction=ext,mode=mode,baseline=method,baseline_mode=variant),
                    models[a,ext,mode],ref,boot,sel))
        yield key,tbl


class Tables:
    def __init__(self,directory):
        import contextlib
        self.directory=directory;directory.mkdir(parents=True,exist_ok=True)
        self.files=contextlib.ExitStack(); self.writers={}

    def add(self,name,rows):
        for r in rows:
            if name not in self.writers:
                if name=="gates":
                    stream=self.files.enter_context((self.directory/(name+".csv")).open("w",newline="",encoding="utf-8"))
                else:
                    raw=self.files.enter_context((self.directory/(name+".csv.gz")).open("wb"))
                    compressed=self.files.enter_context(gzip.GzipFile(filename="",mode="wb",fileobj=raw,mtime=0,compresslevel=4))
                    stream=self.files.enter_context(io.TextIOWrapper(compressed,newline="",encoding="utf-8"))
                self.writers[name]=csv.DictWriter(stream,fieldnames=list(r),lineterminator="\n")
                self.writers[name].writeheader()
            self.writers[name].writerow({k:"" if isinstance(v,(float,np.floating)) and np.isnan(v) else v for k,v in r.items()})


def markdown(columns,values):
    return ["","| "+" | ".join(columns)+" |","| "+" | ".join("---" for _ in columns)+" |",
            *["| "+" | ".join(map(str,r))+" |" for r in values],""]


def render(cohort,rows,audit):
    def pick(name,group="all",stratum="All",**d):
        d.update(group=group,stratum=stratum)
        found=[r for r in rows[name] if all(r[k]==v for k,v in d.items())]
        ensure(len(found)==1,f"Ambiguous {name} result for {d}");return found[0]
    def label(v):return "met" if v else "missed"
    def fmt(v):return "—" if np.isnan(v) else f"{v:.4f}"
    def pct(k,n):return f"{k:,}/{n:,} ({100*k/n:.1f}%)" if n else "0/0"
    def interval(r):
        return f"[{r['ci_low']:+.3f}, {r['ci_high']:+.3f}]" if np.isfinite(r["ci_low"]) else "—"
    gates=[r for r in rows["gates"] if r["label"]=="formal"]
    ensure(len(gates)==4,"Expected four cohort-level candidate gate decisions")
    passed={m:all(r["all_met"] for r in gates if r["mode"]==m) for m in ("pre","checked")}
    title="N ≤ 5,000" if cohort=="small" else "N = 50,000"
    lines=[f"# Stage 2 RIbench at {title}", "",
        f"The frozen K24 peak-only fitter **{label(passed['pre'])}** the pre-check criteria for this cohort. "
        f"Its checked release **{label(passed['checked'])}** the criteria against refineR receiving the same check. "
        f"The audit covered all {audit['datasets']:,} routine datasets. Native support-corrected limits determine "
        "these decisions. Each interval contributes its mean absolute endpoint z error with each endpoint capped at 5. "
        "CRP contributes its 95th-percentile upper limit only. An unavailable or unscored interval contributes 5.",
        "", "## Candidate versus unchanged refineR", ""]
    data=[]
    for m,p in product(("pre","checked"),(">20%","<=20%")):
        r=pick("gates","pathology",p,arm="candidate",mode=m)
        data.append([m,p,r["planned"],fmt(r["arm_loss"]),fmt(r["baseline_loss"]),
                     f"{r['value']:+.4f} {interval(r)}",f"{r['arm_implausible']} / {r['baseline_implausible']}",
                     f"{r['arm_nonreturns']} / {r['baseline_nonreturns']}",label(r["all_met"])])
    lines+=markdown(["Mode","Pathology","Sets","Candidate loss","refineR loss","Δ [95% interval]",
                     "Implausible, candidate / refineR","Nonreturns, candidate / refineR","Gate"],data)
    lines+=["The high-pathology gate requires a strictly lower mean loss. At 20% pathology or below, "
            "the permitted increase is 0.02. Both gates also require no increase in the number of "
            "implausible intervals or nonreturns. The implausibility definition uses the uncapped mean "
            "absolute endpoint z above 5. Each gate uses paired point estimates.", "",
            "## Components and reported intervals", "",
            "The frozen candidate equals the independently labeled peak-only arm on every case. "
            "The other arms use anchor-guided starting values or search regions, respectively."]
    data=[]
    for a,m in product(ARMS,("pre","checked")):
        r=pick("accuracy",arm=a,extraction="native",mode=m)
        data.append([LABELS[a],m,pct(r["returned"],r["planned"]),fmt(r["mean_capped_abs_z"]),fmt(r["penalty5_mean"]),
            r["implausible"],r["severe"],r["nonfinite"],r["out_of_support"],r["unordered_two_sided"],r["fit_failures"]])
    lines+=markdown(["Arm","Mode","Returned","Returned/scored loss","All-set loss","Implausible","E > 5",
                     "Nonfinite","Outside support","Unordered","Fit failures"],data)
    data=[]
    for p in (">20%","<=20%"):
        for a in ("candidate","start","region"):
            vals=[pick("paired-loss","pathology",p,arm=a,extraction=e,mode=m,baseline_mode=b)
                for e,m,b in (("native","pre","pre"),("native","checked","checked"),("native","checked","pre"),
                              ("historical","pre","pre"),("historical","checked","checked"))]
            data.append([p,LABELS[a],*[f"{r['value']:+.4f}" for r in vals]])
    lines+=markdown(["Pathology","Arm","Native pre Δ","Native checked Δ","Native checked vs ungated Δ",
                     "Historical pre Δ","Historical checked Δ"],data)
    lines+=["## Peak choice and fallback", "",
            "Different peaks means that the anchor election and refineR chose different detected indices on the "
            "initial raw density. The all-assigned rate uses every dataset. The clear-comparison rate uses just "
            "clear elections with an upstream peak for comparison. An unclear election and an unavailable "
            "comparison are counted separately. Fallback uses all assigned datasets."]
    data=[]
    for group in ("all","analyte","N","fraction"):
        vals=[r for r in rows["peak-fallback"] if r["group"]==group and r["metric"]=="different_all"]
        for r in vals:
            data.append([group,r["stratum"],r["same"],pct(r["different"],r["planned"]),pct(r["different"],r["clear"]),
                         r["unclear"],r["unavailable"],pct(r["fallback"],r["planned"])])
    lines+=markdown(["Group","Value","Same","Different / assigned","Different / clear","Unclear","Unavailable","Fallback / assigned"],data)
    lines+=["The joint table includes every observed analyte × N × pathological fraction combination, its "
            "assigned and clear denominators, and cluster intervals. [Peak choice and fallback](peak-fallback.csv.gz) · "
            "[Fallback reasons](fallback.csv.gz)", "", "## Archival comparisons on the same datasets", "",
            "Raw comparisons use ungated Stage 2 and the comparator’s raw estimates. Checked comparisons use "
            "the primary Stage 2 release and the intervals originally reported by each comparator. The published "
            "safeguards and original comparator limits apply with both Stage 2 extractions. "
            "Each paired comparison verifies the routine and anchor identities. Missing archive coverage is "
            "excluded from the paired population and counted separately from a withheld or failed estimate."]
    data=[]
    for method,variant in product(COMPARATORS,("raw","reported")):
        r=pick("comparators",arm="candidate",extraction="native",baseline=method,baseline_mode=variant)
        data.append([LABELS[method],variant,pct(r["matched"],r["planned"]),r["arm_returned"],r["baseline_returned"],
            fmt(r["arm_loss"]),fmt(r["baseline_loss"]),f"{fmt(r['value'])} {interval(r)}",r["common_scored"],
            fmt(r["arm_common_mean"]),fmt(r["baseline_common_mean"])])
    lines+=markdown(["Comparator","Version","Matched / planned","Candidate returned","Comparator returned",
                     "Candidate loss","Comparator loss","Δ [95% interval]","Common scored",
                     "Candidate on common","Comparator on common"],data)
    lines+=["## Anchor check", "",
        "A primary p-value below 0.01 declines the fit. Capture and good-result loss use every classifiable "
        "valid fit in the indicated group. E is the largest absolute endpoint z. The alternate seed uses "
        "the same rounded measurements and a fresh PIT randomization. Both decisions apply to both extractions."]
    data=[]
    for a,e in product(("baseline","candidate"),EXT):
        rr=[pick("rates",arm=a,extraction=e,seed="primary",mode="check",unit="dataset",metric=name) for name in (
            "decline","declined_bad_gt1","declined_bad_gt5","declined_good_lt0.25")]
        flip=pick("seed-changes",arm=a)
        data.append([LABELS[a],e,*[pct(r["numerator"],r["denominator"]) for r in rr],
                     pct(flip["changed"],flip["both_evaluable"])])
    lines+=markdown(["Arm","Extraction","Evaluable fits declined","E > 1 caught","E > 5 caught",
                     "E < 0.25 declined","Seed reversals"],data)
    lines+=["## Reproducibility and evidence", "",
        f"All {audit['fits']:,} fits and {audit['checks']:,} check records passed the technical audit. "
        f"Same-host reruns matched across {audit['exact_repeat_shards']} shards. The independent-host audit "
        f"covered {audit['distinct_host_shards']} shards. The largest endpoint difference was "
        f"{audit['max_endpoint_fraction']:.6g} of reference width and the largest p-value difference was "
        f"{audit['max_p_difference']:.6g}. [Audit](evidence/audit.json)", "",
        "Descriptive 95% intervals resample RIbench (Analyte, Scenario) clusters intact. Each stratum "
        "uses 2,000 paired percentile bootstrap draws with PCG64 seed 37000000. Paired differences "
        "use common cluster weights. Undefined replicates are excluded and intervals require two informative "
        "clusters. The data tables identify all case and endpoint denominators.", "",
        "- [Prespecified gate details](gates.csv) · [Paired loss and common-returned differences](paired-loss.csv.gz) · "
        "[Descriptive paired comparators](comparators.csv.gz)",
        "- [Before-check and after-check accuracy](accuracy.csv.gz) · [Signed endpoint errors](endpoints.csv.gz) · "
        "[Check rates, capture and coverage](rates.csv.gz) · [Threshold ties](boundary-counts.csv.gz) · [Seed reversals](seed-changes.csv.gz)",
        "- [Case fits](evidence/fits.csv.gz) · [Check records](evidence/checks.csv.gz)", ""]
    return "\n".join(lines)


def report(cohort,directory,out,comparator_path=COMPARATOR_INPUT):
    cases,arms,peaks,audit=load_inputs(directory,cohort)
    comp=load_comparators(cases,comparator_path)
    summary=defaultdict(list); writer=Tables(out)
    try:
        for key,tbl in analyze(cases,arms,peaks,comp,cohort):
            for name,rows in tbl.items():
                writer.add(name,rows)
                if key["group"] in ("all","pathology") or (name=="peak-fallback" and key["group"] in ("analyte","N","fraction")):
                    summary[name].extend(rows)
    finally:
        writer.files.close()
    (out/"REPORT.md").write_text(render(cohort,summary,audit),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cohort",choices=("small","large"));parser.add_argument("audited_directory",type=Path)
    parser.add_argument("output_directory",type=Path)
    args=parser.parse_args()
    report(args.cohort,args.audited_directory,args.output_directory)
