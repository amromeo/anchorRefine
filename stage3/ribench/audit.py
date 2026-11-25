"""Authenticate all primary RIbench records, then audit the assigned same- and separate-host pairs."""
import argparse
import csv
import gzip
import io
import json
import math
import sys
import uuid
from contextlib import ExitStack
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from stage2.audit import ELECTION, PARAMETERS, TRACE, check_one_decision, digest, flag, missing, number, require, same_fields, table, write_rows
from stage2.ribench.audit import Audit, CHECK_KEY, FIT_KEY, FLAGS, LIMITS, PEAK, PEAK_VALUES, SCORES, SHA, compare_baseline, finalize_scores, widths
from stage2.ribench.audit_reference import EXTRACTIONS, indexed, published, read_reference, sides

ARMS = ("baseline", "stage2", "w0", "w1", "t0", "t0.25", "anchorsOnly")
SEEDS = ("primary", "alternate")
SHARDS = 48
REF = {"small": ("45316106750", "0fe24bec17293cba7688c20c66d473a2feb703245d10243debcdd4932e0deda0"),
       "large": ("45326071964", "babb80cdba84a78b5d1858ed448046a177295963458237a8ceb33c0f9ae3247e")}
DIR = Path(__file__).resolve().parent
NUMERIC = (*PARAMETERS, *PEAK_VALUES, *SCORES, "C_H", "A", "J", "loglik_anchor_mu", "loglik_anchor_sigma",
           "ao_location", "ao_spread", "ao_shift", "center_shift", "spread_shift", "healthy_center_z", "healthy_spread_z")
VARIABLE_HASHES = ("case_hash", "result_hash", "fit_hash", "hist_hash")


def previous_results(cohort):
    run, manifest = REF[cohort]
    root = ROOT / f"results/stage2-ribench-{cohort}-{run}"
    files = ("evidence/fits.csv.gz", "evidence/checks.csv.gz")
    published(root, manifest, files)
    select = lambda r: r["arm"] == "candidate"
    return indexed(root/files[0], ("Index",), select), indexed(root/files[1], ("Index", "seed_kind"), select)


def validate_case(fits, checks, design, cohort):
    i = design["Index"]
    parent = fits[i, "stage2"]
    valid_parent = parent["fit_status"] == "ResultFound"
    fallback = flag(parent["fallback"])
    for arm in ARMS:
        row = fits[i, arm]
        ctx = (i, arm)
        same_fields(design, row, design, ctx)
        require(row["j"] == i and row["phase"] == "ribench" and row["cohort"] == cohort, (ctx, "case identity"))
        require(row["fit_status"] in ("ResultFound", "fit_failed"), (ctx, "fit status"))
        valid = row["fit_status"] == "ResultFound"
        require(SHA.fullmatch(row["result_hash"]) and row["result_hash"] == parent["result_hash"], (ctx, "case result hash"))
        require(SHA.fullmatch(row["case_hash"]) and row["case_hash"] == parent["case_hash"], (ctx, "serialized case hash"))
        require(not valid or SHA.fullmatch(row["fit_hash"]), (ctx, "full fit hash"))
        require(flag(row["parent_fallback"]) == fallback, (ctx, "parent fallback"))
        if valid and arm != "anchorsOnly":
            require(all(math.isfinite(number(row[k])) for k in ("Mu","Sigma","Lambda","Shift")) and number(row["Sigma"])>0,
                    (ctx,"model parameters"))
        if valid and arm == "anchorsOnly":
            require(not missing(row["ao_transform"]) and all(math.isfinite(number(row[k])) for k in ("ao_location","ao_spread","ao_shift")),
                    (ctx,"anchors-only fit"))
        if arm in ("w0", "w1", "t0", "t0.25"):
            require(number(row["weight"]) == float(arm[1:]) and flag(row["inherited_fallback"]) == fallback,
                    (ctx,"frozen weight and parent path"))
        if arm == "w1":
            path = "invalid_parent" if not valid_parent else "unguided" if fallback else "guided"
            entered = row["branch"] in ("weighted", "retained_parent", "search_fallback")
            require(row["weighted_search_path"] == path and flag(row["weighted_search_entered"]) == entered and
                    flag(row["weighted_search_attempted"]) == valid_parent, (ctx,"weighted search"))
        if arm in ("w0","t0"):
            require(all(flag(row[k]) for k in ("zero_score_exact","zero_fit_exact","zero_rng_exact")), (ctx,"zero identity"))
            same_fields(parent,row,("fit_hash","fit_status","fallback",*PARAMETERS,*TRACE,*ELECTION,*LIMITS,*FLAGS,*SCORES),ctx)
        if arm == "stage2" and fallback:
            same_fields(row,fits[i,"baseline"],("fit_hash","fit_status",*PARAMETERS,*LIMITS,*FLAGS),ctx)
        for ext in EXTRACTIONS:
            requested = sides(design)
            vals = [number(row[f"{ext}_{s}"]) for s in requested]
            complete = all(map(math.isfinite,vals))
            require(flag(row[ext+"_nonfinite"]) == (not complete), (ctx,ext,"finite"))
            if len(requested) == 1:
                require(all(missing(row[ext+"_"+k]) for k in ("lower","z_lower","out_lower","ordered")), (ctx,ext,"CRP"))
            else:
                require((flag(row[ext+"_ordered"]) == (vals[0] < vals[1])) if complete else missing(row[ext+"_ordered"]),
                        (ctx,ext,"ordered"))
            for side,value in zip(requested,vals):
                out=row[f"{ext}_out_{side}"]
                require((flag(out) == (value <= number(design["nonp_shift"]))) if math.isfinite(value) else missing(out),
                        (ctx,ext,side,"support"))
            require(valid or all(math.isnan(v) for v in vals), (ctx,"failed fit with limits"))
        for seed in SEEDS:
            check = checks[i,arm,"guidance",seed]
            require(check["seed"] == design["pit_"+seed+"_seed"] and check["j"] == i, (ctx,"check identity"))
            if arm == "anchorsOnly":
                require(missing(check["p"]) and missing(check["statistic"]) and check["status"] == ("keep" if valid else "fit_failed"),
                        (ctx,seed,"anchors-only reporting rule"))
                for key in LIMITS:
                    expected=valid and not flag(row[key.split("_")[0]+"_nonfinite"])
                    require(check["released_"+key] == row[key] if expected else missing(check["released_"+key]),(ctx,key))
            else:
                check_one_decision(check,row,(ctx,seed))
            if arm in ("w0","t0") or (arm=="stage2" and fallback):
                original=checks[i,"baseline" if arm=="stage2" else "stage2","guidance",seed]
                same_fields(check,original,(k for k in check if k!="arm"),(ctx,seed,"parent check"))


def compare_pair(audit, source, index, fit, other, checks, other_checks, reference=False):
    ctx = index, fit["arm"]
    w=widths(fit)
    fields = (*PARAMETERS,*PEAK,*PEAK_VALUES,*TRACE,*ELECTION,*LIMITS,*FLAGS,*SCORES,
              "fit_hash","fit_status","fit_upstream_status","reason","clarity","fallback","election_reason") if reference else fit.keys()
    for k in fields:
        mode = ("limit" if k in LIMITS else "hash" if k in VARIABLE_HASHES else "number" if k in NUMERIC else "exact")
        audit.compare(source,ctx,k,fit[k],other[k],mode,w.get(k.split("_")[0]))
    for kind in SEEDS:
        first,second=checks[kind],other_checks[kind]
        for k in first:
            if reference and k=="arm":
                continue
            mode="limit" if k.startswith("released_") else "probability" if k=="p" else "number" if k=="statistic" else "exact"
            audit.compare(source,(*ctx,kind),k,first[k],second[k],mode,w.get(k.split("_")[1]) if k.startswith("released_") else None)


def read_cases(directory,ids):
    pairs=set(product(ids,ARMS))
    result=[]
    for name,key,expected in (("fits",FIT_KEY,pairs),("checks",CHECK_KEY,{(*p,"guidance",s) for p in pairs for s in SEEDS})):
        path=directory/(name+".csv")
        rows=table(path,key)
        require(rows.keys()==expected,(directory.name,name,"missing or extra case/arm key",len(rows),len(expected)))
        result.append(rows)
    return tuple(result)


def make_writer(stack,out,name):
    binary=stack.enter_context((out/(name+".csv.gz")).open("wb"))
    zipped=stack.enter_context(gzip.GzipFile(filename="",fileobj=binary,mode="wb",mtime=0))
    stream=stack.enter_context(io.TextIOWrapper(zipped,encoding="utf-8",newline=""))
    writer=None
    def append(rows):
        nonlocal writer
        for r in rows:
            if writer is None:
                writer=csv.DictWriter(stream,fieldnames=list(r),lineterminator="\n")
                writer.writeheader()
            writer.writerow(r)
    return append


def compare_archives(i, fits, checks, refs, saved_fits, saved_checks, ao, audit):
    compare_baseline("primary",fits[i,"baseline"],checks,refs,audit)
    current=fits[i,"stage2"]
    new_checks={s:checks[i,"stage2","guidance",s] for s in SEEDS}
    old_checks={s:saved_checks[i,s] for s in SEEDS}
    compare_pair(audit,"stage2",i,saved_fits[i,],current,old_checks,new_checks,True)
    anchor=fits[i,"anchorsOnly"]
    comp=ao[i,]
    same_fields(anchor,comp,("Index","Analyte","Scenario","N","fractionPathol","routine_hash","anchor_hash","ribench_hashcode","anchor_seed"),(i,"archived anchors-only inputs"))
    require((anchor["fit_status"]=="ResultFound")== (comp["status"]=="returned"),(i,"archived anchors-only status"))
    width=number(comp["upper"])-(number(comp["lower"]) if flag(anchor["requested_lower"]) else 0)
    for side in sides(anchor):
        for ext in EXTRACTIONS:
            audit.compare("anchors_only",i,ext+"_"+side,comp[side],anchor[ext+"_"+side],"limit",width)


def main(cohort,mode,raw,out):
    out.mkdir(parents=True,exist_ok=True)
    refs=read_reference(cohort)
    ids,design=refs[:2]
    original,original_checks=previous_results(cohort)
    ao=indexed(ROOT/"stage2/ribench/comparators/comparators.csv.gz",("Index",),lambda r:r["method"]=="anchorsOnly")
    samples=indexed(DIR/"audit-sample.csv",("Index",),lambda r:r["cohort"]==cohort)
    require(len(samples)==len(ids)//10 and all((i,) in design for i, in samples), "audit sample inventory")
    for key,s in samples.items():
        same_fields(s,design[key],("Index","Analyte","N","fractionPathol"),("sample",key))
    selected=set(str(i) for i in ids) if mode=="full" else {i for i, in samples}
    manifest=digest(DIR/"SHA256SUMS")
    groups=set()
    for s in range(1,SHARDS+1):
        with (raw/f"primary-{s}"/"fits.csv").open(newline="") as f:
            for r in csv.DictReader(f):
                groups.update((r["Analyte"],r["arm"],e) for e in EXTRACTIONS if number(r[e+"_upper"])==0)
    hosts=[]; cases=[]; reference_matches=[]; full_needed=False
    with ExitStack() as stack:
        def opened(name): return stack.enter_context((out/name).open("w",newline=""))
        audit=Audit(opened("discrepancies.csv"))
        changed=csv.writer(opened("z-adjustments.csv"),lineterminator="\n")
        changed.writerow(("role","Index","Analyte","arm","extraction","local_z_upper","cohort_z_upper"))
        fit_out,ck_out=(make_writer(stack,out,name) for name in ("fits","checks"))
        for s in range(1,SHARDS+1):
            require(digest(raw/f"build-{s}"/"source-manifest.sha256")==manifest,(s,"source manifest"))
            primary_ids=[str(i) for i in ids[s-1::SHARDS]]
            sample=[i for i in primary_ids if i in selected]
            by_role={}
            meta={"shard":s,"audited_datasets":len(sample)}
            incomplete = {}
            for role,included in (("primary",primary_ids),("repeat",sample),("other",sample)):
                directory=raw/f"{role}-{s}"
                if role == "primary":
                    by_role[role] = read_cases(directory, included)
                else:
                    try:
                        by_role[role] = read_cases(directory, included)
                    except (KeyError, ValueError, OSError, csv.Error) as exc:
                        incomplete[role] = str(exc)
                        by_role[role] = ({}, {})
                        audit.change("same_host" if role=="repeat" else "cross_host", s, "sample rows",
                                     "complete assigned records", str(exc), False)
                        full_needed = True
                require(bool(included) != (directory/"empty.txt").is_file(), (role,s,"empty assignment marker"))
                meta[role+"_boot"]=str(uuid.UUID((directory/"boot.txt").read_text().strip()))
                meta[role+"_platform"]=(directory/"platform.txt").read_text().strip()
                meta[role+"_pid"]=int((directory/"r-pid.txt").read_text().strip())
                require(meta[role+"_platform"] and meta[role+"_pid"]>0,(role,s,"host provenance"))
                if role=="primary":
                    for f in ("fits.csv","checks.csv","results.rds"):
                        meta[f]=digest(directory/f)
            require(meta["primary_boot"]==meta["repeat_boot"]!=meta["other_boot"] and
                    meta["primary_pid"]!=meta["repeat_pid"] and meta["primary_platform"]==meta["repeat_platform"],(s,"audit sessions"))
            fits,checks=by_role["primary"]
            # Whole-cohort primary group flags apply also to subset reruns.
            # Changes in the discrete zero-URL branch are audited explicitly.
            for role in by_role:
                finalize_scores(by_role[role][0],groups,changed,role)
            pre=audit.failures
            for i in primary_ids:
                validate_case(fits,checks,design[i,],cohort)
                before=audit.failures
                audit.run("reference",i,compare_archives,i,fits,checks,refs,original,original_checks,ao,audit)
                reference_matches.append({"Index":i,"passed":before==audit.failures})
            primary_failed=audit.failures!=pre
            for i in sample:
                same=audit.failures
                repeated,rc=by_role["repeat"]
                crossed,cc=by_role["other"]
                for arm in ARMS if "repeat" not in incomplete else ():
                    f,rf=fits[i,arm],repeated[i,arm]
                    if f.keys()!=rf.keys():
                        audit.change("same_host",(i,arm),"fit schema",list(f),list(rf),False)
                        continue
                    for field,v in f.items():
                        audit.compare("same_host",(i,arm),field,v,rf[field])
                    for seed in SEEDS:
                        key=(i,arm,"guidance",seed)
                        if checks[key].keys()!=rc[key].keys():
                            audit.change("same_host",key,"check schema",list(checks[key]),list(rc[key]),False)
                            continue
                        for field,v in checks[key].items():
                            audit.compare("same_host",key,field,v,rc[key][field])
                exact="repeat" not in incomplete and same==audit.failures
                before=audit.failures
                for arm in ARMS if "other" not in incomplete else ():
                    a,b=fits[i,arm],crossed[i,arm]
                    if a.keys()!=b.keys() or any(checks[i,arm,"guidance",k].keys()!=cc[i,arm,"guidance",k].keys() for k in SEEDS):
                        audit.change("cross_host",(i,arm),"schema","primary fit/check schema","differs",False)
                        continue
                    for ext in EXTRACTIONS:
                        audit.compare("cross_host",(i,arm),ext+"_zero_upper",
                                      number(a[ext+"_upper"])==0, number(b[ext+"_upper"])==0)
                    audit.run("cross_host",(i,arm),compare_pair,audit,"cross_host",i,a,b,
                        {s:checks[i,arm,"guidance",s] for s in SEEDS},{s:cc[i,arm,"guidance",s] for s in SEEDS})
                within="other" not in incomplete and before==audit.failures
                full_needed |= not (exact and within)
                design_row=design[i,]
                cases.append(dict(cohort=cohort,Index=i,N=design_row["N"],Analyte=design_row["Analyte"],
                    fractionPathol=design_row["fractionPathol"],in_frozen_sample=(i,) in samples,
                    seed=next(iter(samples.values()))["seed"],shard=s,same_host_exact=exact,cross_host_passed=within))
            meta.update(exact=all(r["same_host_exact"] for r in cases if r["shard"]==s),
                        distinct=True,reference_passed=not primary_failed)
            hosts.append(meta)
            fit_out(fits.values()); ck_out(checks.values())
        for pos,h in enumerate(hosts):
            prev=hosts[pos-1]
            require(h["other_boot"]==prev["primary_boot"] and h["other_platform"]==prev["primary_platform"] and
                    h["other_pid"] not in (prev["primary_pid"],prev["repeat_pid"]),(pos+1,"separate-host assignment"))
    require(len(cases)==len(selected) and len(reference_matches)==len(ids),"incomplete cohorts")
    write_rows(out/"audit-cases.csv",cases); write_rows(out/"audit-shards.csv",hosts)
    write_rows(out/"archive-cases.csv",reference_matches)
    write_rows(out/"audit-sample.csv",[samples[k] for k in sorted(samples,key=lambda v:int(v[0]))])
    archive_passed=all(r["passed"] for r in reference_matches)
    passed=not audit.failures
    rerun=mode=="sampled" and full_needed
    cross=audit.maxima["cross_host"]
    receipt=dict(passed=passed,cohort=cohort,phase="ribench",mode=mode,full_required=rerun,
        datasets=len(ids),fits=len(ids)*len(ARMS),checks=len(ids)*len(ARMS)*2,audited_datasets=len(selected),
        exact_repeat_shards=sum(h["exact"] for h in hosts),distinct_host_shards=len(hosts),
        same_host_exact_datasets=sum(r["same_host_exact"] for r in cases),cross_host_passed_datasets=sum(r["cross_host_passed"] for r in cases),
        archive_reproduction_passed=archive_passed,archived_baseline_matches=sum(r["passed"] for r in reference_matches),
        sample_sha256=digest(DIR/"audit-sample.csv"),source_manifest_sha256=manifest,
        max_endpoint_fraction=cross.get("endpoint_fraction",0),max_p_difference=cross.get("p",0),
        differences=dict(audit.differences),failures=audit.failures)
    (out/"audit.json").write_text(json.dumps(receipt,indent=2,allow_nan=False)+"\n")
    if rerun: return 12
    require(passed,"RIbench audit failed; see discrepancies.csv")
    return 0


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("cohort",choices=("small","large")); parser.add_argument("mode",choices=("sampled","full"))
    parser.add_argument("raw",type=Path); parser.add_argument("out",type=Path)
    args=parser.parse_args()
    sys.exit(main(args.cohort,args.mode,args.raw,args.out))
