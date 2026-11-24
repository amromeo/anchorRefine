"""Audit paired simulation outputs, host provenance and both zero-weight identities."""
import contextlib
import csv
import gzip
import io
import json
import math
from itertools import product
from pathlib import Path
import sys
import uuid
import zipfile
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2.audit import (ELECTION, EXTRACTIONS, INPUT_HASHES, PANELS, PARAMETERS, SEEDS, SIDES,
                          TRACE, check_one_decision, check_one_fit, digest, flag, hash_field,
                          missing, number, require, same_fields, table, write_rows)

NS = (1000, 1500, 5000, 50000)
W = ("w0", "w1", "w10", "w100", "w1000", "w10000")
T = ("t0", "t0.25", "t0.5", "t0.75", "t1")
DISEASES = ("left_separated", "right_separated", "left_shoulder", "right_shoulder",
            "bilateral_separated", "overlapping")
FOCUS = {"left_shoulder", "right_shoulder", "overlapping"}
SEED_FIELDS = ("routine_seed", "anchor_seed", "diagnostic_seed", "fitter_seed", "pit_primary_seed",
               "pit_alternate_seed", "diagnostic_primary_seed", "diagnostic_alternate_seed")
FIT_KEY = ("j", "arm")
CHECK_KEY = (*FIT_KEY, "panel", "seed_kind")
LIMITS = tuple(f"{e}_{s}" for e in EXTRACTIONS for s in SIDES)
ZS = tuple(f"{e}_z_{s}" for e in EXTRACTIONS for s in SIDES)
FLAGS = tuple(f"{e}_{a}" for e in EXTRACTIONS for a in ("ordered","nonfinite","out_lower","out_upper"))
CONFIG = {"influence": (96, 24, ("stage2", *W)), "development": (3744, 96, ("baseline","stage2",*W,*T,"anchorsOnly"))}


def design(phase):
    """Build expected metadata and seeds independently without drawing data."""
    if phase == "influence":
        cells = ((0.45,"left_shoulder"),(0.45,"right_shoulder"),(0.60,"overlapping"),(0.10,"right_shoulder"))
        base = 81000000
    else:
        cells = tuple(product((.1,.2,.25,.45,.60), DISEASES))
        base = 82000000
    cases = {}
    for cell, (family, n, (fraction, disease), rounding) in enumerate(product(
            ("lognormal","linear","power_0.5"), NS, cells, (.05,.25)), 1):
        rep_n = 1 if phase == "influence" else 8 if fraction > .2 and disease in FOCUS else 4
        for replicate in range(1,rep_n+1):
            j = len(cases)+1
            cases[j] = dict(cell_id=cell, family=family, N=n, fraction=fraction, disease=disease,
                            rounding_fraction=rounding, replicate=replicate,
                            **{k: base+10*j+d for d,k in enumerate(SEED_FIELDS)})
    require(len(cases)==CONFIG[phase][0], "Design size")
    manifest = table(Path(__file__).with_name(f"design-{phase}.csv"), ("j",))
    require(len(manifest)==len(cases),"Frozen manifest size")
    for j,expected in cases.items():
        r=manifest[str(j),]
        require(r["phase"]==phase,(j,"wrong frozen phase"))
        for k,v in expected.items():
            require(number(r[k])==v if isinstance(v,(float,int)) else r[k]==v,(j,k,"frozen design"))
        for k in ("lambda","mu","sigma","h","precision","healthy_sd","truth_lower","truth_upper"):
            expected[k]=number(r[k])
        expected["phase"]=phase
    return cases


def validate_case(fits, checks, j, arms, planned):
    key=str(j)
    parent=fits[key,"stage2"]
    for k,v in planned.items():
        if isinstance(v,(float,int)):
            require(number(parent[k])==v,(j,"design",k,parent[k],v))
        else:
            require(parent[k]==v,(j,"design",k,parent[k],v))
    for arm in arms:
        r=fits[key,arm]
        ctx=(j,arm)
        same_fields(parent,r,(*planned,*INPUT_HASHES,"h","truth_lower","truth_upper"),ctx)
        for k in (*INPUT_HASHES,"result_hash"):
            hash_field(r,k)
        require(len(set(r[k] for k in INPUT_HASHES))==3,(ctx,"identical routines or panels"))
        if arm!="anchorsOnly":
            check_one_fit(r,ctx)
        else:
            require(r["fit_status"] in ("ResultFound","fit_failed"),ctx)
        parent_valid=parent["fit_status"]=="ResultFound"
        fallback=flag(parent["fallback"])
        require(flag(r["parent_fallback"])==fallback,(ctx,"parent fallback"))
        if arm in W or arm in T:
            require(flag(r["inherited_fallback"])==fallback,(ctx,"inherited fallback"))
        if arm in W:
            attempt=arm!="w0" and parent_valid
            path="zero" if arm=="w0" else "invalid_parent" if not parent_valid else "unguided" if fallback else "guided"
            require(r["weighted_search_path"]==path and flag(r["weighted_search_attempted"])==attempt,(ctx,path))
            entered=flag(r["weighted_search_entered"])
            success=r["branch"] in ("weighted","retained_parent")
            require(entered==(r["branch"] in ("weighted","retained_parent","search_fallback")),(ctx,"weighted search entry"))
            require(flag(r["extra_fallback"])==(attempt and not success),(ctx,"additional failure"))
            if attempt:
                require(success or (not missing(r["reason"]) and not missing(r["branch"])),(ctx,"unspecified update failure"))
                require(r["fit_status"]=="ResultFound" and (success or flag(r["parent_retained"])),(ctx,"lost valid parent"))
                if not success or r["branch"]=="retained_parent":
                    same_fields(r,parent,("fit_hash",*PARAMETERS,*LIMITS,*ZS,*FLAGS),ctx)
            elif arm!="w0":
                require(r["fit_status"]=="fit_failed" and not entered,(ctx,"failed parent dispatch"))
        if arm in ("w0","t0"):
            require(all(flag(r[k]) for k in ("zero_fit_exact","zero_rng_exact","zero_score_exact")),(ctx,"zero identity"))
            same_fields(r,parent,("fit_hash","fit_status","fallback",*PARAMETERS,*TRACE,
                                  *ELECTION,*LIMITS,*ZS,*FLAGS),ctx)
            if r["fit_status"]=="ResultFound":
                for f in ("center_shift","spread_shift"):
                    if not missing(parent[f]):
                        require(number(r[f])==0,(ctx,f))
        for panel,seed in product(PANELS,SEEDS):
            ck=(*ctx,panel,seed); c=checks[key,arm,panel,seed]
            if arm=="anchorsOnly":
                require(missing(c["p"]) and c["status"]==("keep" if r["fit_status"]=="ResultFound" else "fit_failed"),ck)
                for field in LIMITS:
                    ext=field.split("_")[0]
                    expected=c["status"]=="keep" and not flag(r[ext+"_nonfinite"])
                    require(c["released_"+field]==r[field] if expected else missing(c["released_"+field]),(ck,field))
            else:
                check_one_decision(c,r,ck)
            if arm in ("w0","t0"):
                original=checks[key,"stage2",panel,seed]
                stable=("seed","status","reason","statistic","p",*("released_"+v for v in LIMITS))
                same_fields(c,original,stable,ck)


def csv_rows(path):
    with path.open(newline="") as f:
        rows=csv.DictReader(f)
        return list(rows.fieldnames),list(rows)


def compare_numeric(v,w,context):
    if v==w:
        return 0.
    x,y=number(v),number(w)
    if not (math.isfinite(x) and math.isfinite(y)):
        require((math.isnan(x) and math.isnan(y)) or x==y,(context,v,w))
        return 0.
    return abs(x-y)


class Comparison:
    def __init__(self,writer):
        self.writer=writer
        self.maxima={}
        self.count=0

    def compare(self,k,field,v,w,mode="exact",width=None):
        if v==w:
            return
        passed=True
        d=None
        if mode not in ("exact","hash"):
            d=compare_numeric(v,w,(k,field))
            if mode=="endpoint":
                require(width is not None and width>0 and math.isfinite(width),(k,"invalid reference width",width))
                d/=width
                passed=d<=0.001
            elif mode=="p":
                passed=d<=0.0001
            key="endpoint_fraction" if mode=="endpoint" else field
            self.maxima[key]=max(d,self.maxima.get(key,0.))
        elif mode=="exact":
            passed=False
        self.writer.writerow([k,field,v,w,mode,d,passed])
        self.count+=1
        require(passed,(k,field,v,w,"cross-host discrepancy"))


def paired_fits(comp, primary, other):
    strict=(*FIT_KEY,*SEED_FIELDS,*INPUT_HASHES,*ELECTION,*TRACE,*FLAGS,"fit_status","fallback","reason",
            "guidance_used","fit_upstream_status","clarity","election_reason","same_peak",
            "healthy_median_in_basin","inherited_fallback","extra_fallback","parent_retained","branch",
            "parent_fallback","weighted_search_path","weighted_search_entered","weighted_search_attempted",
            "upstream_peak_index","anchor_initial_index","initial_peak_count","B","k","overlap",
            "zero_fit_exact","zero_rng_exact","zero_score_exact")
    for key,r in primary.items():
        rr=other[key]
        require(r.keys()==rr.keys(),(key,"schema"))
        for k,v in r.items():
            if k in LIMITS:
                ext=k.split("_")[0]
                width=number(r[ext+"_upper"])-number(r[ext+"_lower"])
                comp.compare(key,k,v,rr[k],"endpoint",width)
            elif k.endswith("_hash") and k not in INPUT_HASHES:
                comp.compare(key,k,v,rr[k],"hash")
            elif k in strict:
                comp.compare(key,k,v,rr[k])
            else:
                try:
                    number(v); number(rr[k])
                except ValueError:
                    comp.compare(key,k,v,rr[k])
                else:
                    comp.compare(key,k,v,rr[k],"numeric")


def paired_checks(comp,primary,other,fits):
    for key,r in primary.items():
        rr=other[key]
        require(r.keys()==rr.keys(),(key,"schema"))
        for k,v in r.items():
            if k.startswith("released_"):
                ext=k.split("_")[1]; fit=fits[key[:2]]
                width=number(fit[ext+"_upper"])-number(fit[ext+"_lower"])
                comp.compare(key,k,v,rr[k],"endpoint",width)
            else:
                mode={"p":"p","statistic":"numeric"}.get(k,"exact")
                comp.compare(key,k,v,rr[k],mode)


def verify_host(root,shard):
    dirs=[root/f"{role}-{shard}" for role in ("primary","repeat","other")]
    boots=[str(uuid.UUID((d/"boot.txt").read_text().strip())) for d in dirs]
    pids=[int((d/"r-pid.txt").read_text().strip()) for d in dirs]
    platforms=[(d/"platform.txt").read_text().strip() for d in dirs]
    require(boots[0]==boots[1]!=boots[2] and min(pids)>0 and pids[0]!=pids[1]
            and all(platforms) and platforms[0]==platforms[1],(shard,"host or session provenance"))
    hashes={}
    for filename in ("fits.csv","checks.csv","results.rds","identities.csv","sensitivity.csv"):
        hashes[filename]=digest(dirs[0]/filename)
        require(hashes[filename]==digest(dirs[1]/filename),(shard,filename,"same-host repeat"))
    return dirs,dict(shard=shard,primary_boot=boots[0],other_boot=boots[2],primary_pid=pids[0],
                     repeat_pid=pids[1],other_pid=pids[2],primary_platform=platforms[0],other_platform=platforms[2],**hashes)


def diagnostic_values(comp,filename,dirs):
    headings,rows=csv_rows(dirs[0]/filename)
    other_head,others=csv_rows(dirs[2]/filename)
    require(headings==other_head and len(rows)==len(others),(filename,"diagnostic dimensions"))
    for r,rr in zip(rows,others):
        key=(filename,r["j"],r.get("metric"),r.get("w"),r["variant"])
        if filename=="identities.csv" and flag(r["required"]):
            require(flag(r["passed"]) and flag(rr["passed"]),(key,"required identity"))
        for field in headings:
            if field in ("w","j","N","metric","variant","status","branch","required","passed","B","k","overlap"):
                comp.compare(key,field,r[field],rr[field])
            elif field in ("lower","upper","base_lower","base_upper"):
                stem="base_" if field.startswith("base_") else ""
                width=number(r[stem+"upper"])-number(r[stem+"lower"])
                comp.compare(key,field,r[field],rr[field],"endpoint",width)
            elif r[field]!=rr[field]:
                try:
                    number(r[field]); number(rr[field])
                except ValueError:
                    comp.compare(key,field,r[field],rr[field])
                else:
                    comp.compare(key,field,r[field],rr[field],"numeric")
    return headings,rows


ORIGINAL_RUN = 45407973511
ORIGINAL_REPORT_SHA = "2de251156297713d1cfbf477dba08bb014817a63b0af83b1a7a28fa49edbfa3f"


def original_influence_audit(evidence):
    """Read the pinned GitHub report artifact, after all current shard files have closed."""
    archive=Path(__file__).resolve().parents[1]/"results"/f"stage3-influence-{ORIGINAL_RUN}"/"artifacts"/"stage3-influence-report.zip"
    require(digest(archive)==ORIGINAL_REPORT_SHA,"Original influence report digest mismatch")
    def rows(stream,fields):
        data={}
        with gzip.open(stream,"rt",encoding="utf-8",newline="") as f:
            for r in csv.DictReader(f):
                key=tuple(r[k] for k in fields)
                require(key not in data,(key,"duplicate original-run audit key"))
                data[key]=r
        return data
    with zipfile.ZipFile(archive) as z:
        original=json.loads(z.read("evidence/audit.json"))
        require(original["phase"]=="influence" and original["passed"] and original["datasets"]==96,"Incomplete original run")
        old={}; new={}
        for name,key in (("fits",FIT_KEY),("checks",CHECK_KEY)):
            with z.open("evidence/"+name+".csv.gz") as f:
                old[name]=rows(f,key)
            new[name]=rows(evidence/(name+".csv.gz"),key)
            require(old[name].keys()==new[name].keys(),(name,"changed influence inventory"))
    paths={k:Counter() for k in ("parent","zero","guided_positive","unguided_positive")}
    maxima={}
    with (evidence/"original-influence-differences.csv").open("w",newline="") as f:
        writer=csv.writer(f,lineterminator="\n")
        writer.writerow(["key","field","original","amended","mode","difference","passed"])
        comparators={k:Comparison(writer) for k in paths}
        for key,row in old["fits"].items():
            j,arm=key; now=new["fits"][key]
            fallback=flag(old["fits"][j,"stage2"]["fallback"])
            path="parent" if arm=="stage2" else "zero" if arm=="w0" else "unguided_positive" if fallback else "guided_positive"
            stats=paths[path]; comp=comparators[path]; unchanged=path!="unguided_positive"
            same_fields(row,now,(*SEED_FIELDS,*INPUT_HASHES,"N","j","arm"),key)
            stats["input_hash_comparisons"]+=len(INPUT_HASHES)
            stats["fits"]+=1
            stats["fit_hash_exact"]+=row["fit_hash"]==now["fit_hash"]
            stats["parameter_vectors_exact"]+=all(row[k]==now[k] for k in PARAMETERS)
            stats["raw_endpoints_exact"]+=sum(row[k]==now[k] for k in LIMITS)
            stats["raw_endpoints"]+=len(LIMITS)
            if unchanged:
                common={k:now[k] for k in row}
                paired_fits(comp,{key:row},{key:common})
            for panel,seed in product(PANELS,SEEDS):
                ck=(*key,panel,seed); a=old["checks"][ck]; b=new["checks"][ck]
                stats["checks"]+=1
                stats["decisions_exact"]+=a["status"]==b["status"]
                stats["p_exact"]+=a["p"]==b["p"]
                stats["released_endpoints"]+=len(LIMITS)
                stats["released_endpoints_exact"]+=sum(a["released_"+k]==b["released_"+k] for k in LIMITS)
                if unchanged:
                    paired_checks(comp,{ck:a},{ck:b},old["fits"])
        for path,comp in comparators.items():
            maxima[path]=dict(enforced=path!="unguided_positive",max_endpoint_fraction=comp.maxima.get("endpoint_fraction",0.)
                              if path!="unguided_positive" else None,
                              max_p_difference=comp.maxima.get("p",0.) if path!="unguided_positive" else None)
            paths[path]=dict(paths[path],**maxima[path])
    require(paths["parent"]["fits"]==paths["zero"]["fits"]==96,"Lost original parent or zero coverage")
    receipt=dict(passed=True,original_run_id=ORIGINAL_RUN,original_report_sha256=ORIGINAL_REPORT_SHA,datasets=96,
                 paths=paths,endpoint_fraction_tolerance=.001,p_tolerance=.0001)
    (evidence/"original-influence-audit.json").write_text(json.dumps(receipt,indent=2,allow_nan=False)+"\n")


def audit(phase,raw,evidence):
    n,shards,arms=CONFIG[phase]
    planned=design(phase)
    evidence.mkdir(parents=True,exist_ok=True)
    hosts=[]; counts={}; writers={}; input_cases={}
    required_count=sensitivity_count=0
    identities=[]
    receipt=dict(phase=phase,passed=False,datasets=0,exact_repeat_shards=0,distinct_host_shards=0)
    def persist():
        (evidence/"audit.json").write_text(json.dumps(receipt,indent=2,allow_nan=False)+"\n")
    try:
        with contextlib.ExitStack() as stack:
            def append(name,columns,rows):
                if name not in writers:
                    path=evidence/(name+".csv.gz")
                    raw_stream=stack.enter_context(path.open("wb"))
                    comp=stack.enter_context(gzip.GzipFile(filename="",fileobj=raw_stream,mode="wb",mtime=0))
                    stream=stack.enter_context(io.TextIOWrapper(comp,encoding="utf-8",newline=""))
                    writers[name]=csv.DictWriter(stream,fieldnames=columns,lineterminator="\n")
                    writers[name].writeheader()
                    counts[name]=0
                require(list(writers[name].fieldnames)==columns,(name,"shard schema"))
                writers[name].writerows(rows)
                counts[name]+=len(rows)
            f=stack.enter_context((evidence/"cross-host-differences.csv").open("w",newline=""))
            diff_writer=csv.writer(f,lineterminator="\n")
            diff_writer.writerow(["key","field","primary","other","mode","difference","passed"])
            comp=Comparison(diff_writer)
            for shard in range(1,shards+1):
                dirs,host=verify_host(raw,shard)
                hosts.append(host)
                indices=[j for j in planned if (j-1+(5*((j-1)//shards) if phase=="development" else 0))%shards==shard-1]
                fits_key={(str(i),a) for i in indices for a in arms}
                check_keys={(*k,p,s) for k in fits_key for p,s in product(PANELS,SEEDS)}
                fit_tables=[table(d/"fits.csv",FIT_KEY) for d in (dirs[0],dirs[2])]
                check_tables=[table(d/"checks.csv",CHECK_KEY) for d in (dirs[0],dirs[2])]
                for fs,cs in zip(fit_tables,check_tables):
                    require(set(fs)==fits_key and set(cs)==check_keys,(shard,"case or arm coverage"))
                    for j in indices:
                        validate_case(fs,cs,j,arms,planned[j])
                paired_fits(comp,*fit_tables)
                paired_checks(comp,*check_tables,fit_tables[0])
                for j in indices:
                    r=fit_tables[0][str(j),"stage2"]
                    input_cases[j]=tuple(r[c] for c in INPUT_HASHES)
                for name,records in [("fits",fit_tables[0]),("checks",check_tables[0])]:
                    vals=list(records.values())
                    append(name,list(vals[0]),vals)
                for name in ("identities","sensitivity"):
                    columns,rows=diagnostic_values(comp,name+".csv",dirs)
                    if name=="identities":
                        if phase=="development":
                            require(not rows,"Expected identities only in the influence phase")
                        else:
                            ids={int(r["j"]) for r in rows if r["metric"]=="profile_available"}
                            require(ids==set(indices),(shard,"native-profile coverage"))
                            for j in indices:
                                parent=fit_tables[0][str(j),"stage2"]
                                valid=parent["fit_status"]=="ResultFound"
                                path="unguided" if flag(parent["fallback"]) else "guided"
                                coverage=[r for r in rows if int(r["j"])==j and r["metric"]=="profile_available"]
                                require(len(coverage)==1 and coverage[0]["variant"]==path and
                                        number(coverage[0]["observed"])==int(valid),(j,"original profile path"))
                                profile=[r for r in rows if int(r["j"])==j and r["metric"]=="native_profile"]
                                require(len(profile)==3*int(valid) and all(flag(r["required"]) for r in profile),
                                        (j,"native profile parity evidence"))
                            identities.extend(r for r in rows if int(r["j"])==1 and flag(r["required"]))
                        required_count+=sum(flag(r["required"]) for r in rows)
                    else:
                        variants=("units_0.1","units_10","width_0.5","width_2","duplicate_2")
                        targets={("primary",float(a[1:]),v) for a,v in product(W,variants)}
                        targets|={("postfit",float(a[1:]),v) for a,v in product(T,variants[:2])}
                        wanted={(j,*item) for j in indices if phase=="development" and planned[j]["replicate"]==1 for item in targets}
                        found={(int(r["j"]),r["arm"],float(r["w"]),r["variant"]) for r in rows}
                        require(len(rows)==len(wanted) and found==wanted,(shard,"sensitivity coverage"))
                        sensitivity_count+=len(rows)
                    append(name,columns,rows)
            for i,r in enumerate(hosts):
                prev=hosts[i-1]
                require(r["other_boot"]==prev["primary_boot"] and r["other_platform"]==prev["primary_platform"]
                        and r["other_pid"] not in (prev["primary_pid"],prev["repeat_pid"]),(i+1,"independent runner ring"))
            require(len(input_cases)==n and len({v[0] for v in input_cases.values()})==n,
                    "Expected a distinct routine input per dataset")
            require(len({h for v in input_cases.values() for h in v[1:]})==2*n,
                    "A screened panel is reused across datasets")
            if phase=="influence":
                metrics={"normal_count_score","overlap_replication","fixed_mask_doubled_N","normalized_original_density",
                         "rounded_bin_quadrature","mapped_relative_anchor_score","exact_original_density",
                         "mapped_postfit_blend","mapped_trial_count","structural_zero_support"}
                require(metrics<={r["metric"] for r in identities},"Incomplete required algebraic fixtures")
            if phase=="development":
                require(sensitivity_count>0,"Missing development sensitivity results")
            write_rows(evidence/"audit-shards.csv",hosts)
            receipt.update(passed=True,datasets=n,exact_repeat_shards=shards,distinct_host_shards=shards,
                           fits=counts["fits"],checks=counts["checks"],required_identities=required_count,
                           sensitivity_rows=sensitivity_count,diagnostic_counts=counts,
                           max_endpoint_fraction=comp.maxima.get("endpoint_fraction",0),
                           max_p_difference=comp.maxima.get("p",0),cross_host_differences=comp.count,
                           max_differences=comp.maxima)
        if phase=="influence":
            original_influence_audit(evidence)
            receipt["original_audit_sha256"]=digest(evidence/"original-influence-audit.json")
    except Exception as error:
        receipt["passed"]=False
        receipt["error"]=f"{type(error).__name__}: {error}"
        receipt["verified_shards"]=len(hosts)
        persist()
        raise
    persist()
    print(f"{phase}: audited {n} datasets, {counts['fits']} fits, {counts['checks']} check records",flush=True)


if __name__=="__main__":
    phase,raw,out=sys.argv[1:]
    out=Path(out)
    audit(phase,Path(raw),out if out.name=="evidence" else out/"evidence")
