"""Read and authenticate permanent Stage 0/1 RIbench reference evidence."""
import csv
import gzip
import math
from pathlib import Path

from stage1.audit import cohort_definition
from stage2.audit import digest, flag, require


ROOT = Path(__file__).resolve().parents[2]
STAGE0 = ROOT / "results/stage0-45241996440"
STAGE1 = ROOT / "results/stage1-45276858699"
S0_PAIRS = ("cran_repeat", "vendored_repeat", "engines_first", "engines_repeat")
EXTRACTIONS = ("native", "historical")


def indexed(path, fields, select=lambda row: True):
    result = {}
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="") as stream:
        for row in csv.DictReader(stream):
            if select(row):
                key = tuple(row[f] for f in fields)
                require(key not in result, (path, "duplicate key", key))
                result[key] = row
    return result


def published(directory, expected, names):
    sums = directory / "SHA256SUMS"
    require(digest(sums) == expected, (sums, "published evidence manifest differs"))
    files = {rel: sha for sha, rel in (s.split(None, 1) for s in sums.read_text().splitlines())}
    for name in names:
        require(digest(directory / name) == files[name], (directory / name, "digest differs"))


def sides(row):
    return ("lower", "upper") if row["Analyte"] != "CRP" else ("upper",)


def read_reference(cohort):
    require(cohort in ("small", "large"), ("cohort", cohort))
    design = indexed(Path(__file__).with_name(f"design-{cohort}.csv"), ("Index",))
    cases = cohort_definition(cohort)
    ids = sorted(cases)
    keys = {(str(i),) for i in ids}
    require(design.keys() == keys, "Design must include exactly the CRAN RIbench cohort")
    endpoint_keys = {(str(i), ext, s) for i in ids for ext in EXTRACTIONS for s in sides(cases[i])}
    published(STAGE1, "b056e5a6e0495a2e4aa3f014f086da18581fad84423da79f508bfea5e7fb6ca5",
              [f"{cohort}/{f}.csv.gz" for f in ("checks", "estimates")])
    checks = indexed(STAGE1 / cohort / "checks.csv.gz", ("Index",))
    estimates = indexed(STAGE1 / cohort / "estimates.csv.gz", ("Index", "extraction", "endpoint"),
                        lambda r: r["method"] == "refineR")
    require(checks.keys() == keys and estimates.keys() == endpoint_keys, "Stage 1 baseline coverage")
    inputs = ROOT / ("archive/c2" if cohort == "small" else "stage1/large")
    models = indexed(inputs / "model-inventory.csv", ("Index",))
    anchors = indexed(inputs / "anchor-sample-hashes.csv", ("Index",))
    require(models.keys() == keys and anchors.keys() == keys, "C2 model and anchor coverage")
    small_limits, small_deltas = {}, {}
    small_inputs = {}
    if cohort == "small":
        published(STAGE0, "7a02085499ee7486b7ddf3e14abfac895d7f80eb0369662a897bda9790966db8",
                  ["same-machine.csv.gz", "historical-audit.csv.gz", "parameter-differences.csv.gz"])
        stage0 = indexed(STAGE0 / "same-machine.csv.gz", ("Index", "pair"))
        require(stage0.keys() == {(str(i), p) for i in ids for p in S0_PAIRS} and
                all(all(flag(r[k]) for k in ("fit_equal", "native_equal", "historical_equal", "exact"))
                    for r in stage0.values()), "Stage 0 CRAN vs pass-through")
        small_limits = indexed(STAGE0 / "historical-audit.csv.gz", ("Index", "endpoint"))
        small_deltas = indexed(STAGE0 / "parameter-differences.csv.gz", ("Index",))
        require(small_deltas.keys() == keys, "Stage 0 parameter coverage")
        require(small_limits.keys() == {(str(i), s) for i in ids for s in sides(cases[i])} and
                all(flag(r["historical_pass"]) and flag(r["native_valid"]) for r in small_limits.values()),
                "Stage 0 C2 audit and native limits")
        path = ROOT / "stage0/frozen/verified-inputs.csv"
        require(digest(path) == "3bd268f986bb5abcb604871a83c89f6011b1b2596082ddb83b0ba6a16d8d1838",
                "Stage 0 ordered input hashes")
        small_inputs = indexed(path, ("Index",))
        require(small_inputs.keys() == keys, "Stage 0 verified inputs coverage")
    for i in ids:
        idx = str(i)
        d, s, specification = design[idx,], checks[idx,], cases[i]
        require(d["Analyte"] == s["Analyte"] == specification["Analyte"] and
                d["Scenario"] == s["Scenario"] == specification["Scenario"] and
                d["ribench_hashcode"] == s["ribench_hashcode"] == specification["HashCode"],
                (idx, "RIbench metadata/input identity"))
        for k in ("N", "fractionPathol", "startSeed", "decimals", "nonp_mu",
                  "nonp_lambda", "nonp_sigma", "nonp_shift"):
            require(float(d[k]) == float(specification[k]), (idx, k, "RIbench specification"))
        raw_truth = {"lower": "GT_LRL", "upper": "GT_URL"}
        require(flag(d["requested_lower"]) == (d["Analyte"] != "CRP")
                and (d["Analyte"] != "CRP" or d["truth_lower"] == "")
                and float(d["upper_probability"]) == (0.95 if d["Analyte"] == "CRP" else 0.975)
                and math.isclose(float(d["h"]), 10.0**(-int(d["decimals"])), rel_tol=2e-15),
                (idx, "requested endpoints or precision"))
        for side in sides(d):
            for ext in EXTRACTIONS:
                e = estimates[idx, ext, side]
                p = float(d["upper_probability"]) if side == "upper" else 0.025
                require(e["paired"] == "TRUE" and float(e["probability"]) == p and
                        float(e["truth"]) == float(d[f"truth_{side}"]) == float(specification[raw_truth[side]]),
                        (idx, ext, side, "reference truth or probability"))
        require(d["stage1_model_sha256"] == s["model_sha256"] == models[idx,]["sha256"] and
                d["stage1_result_hash"] == s["result_hash"] and s["fit_source"] == "archived" and
                d["routine_hash"] == s["routine_hash"] and d["routine_n"] == s["routine_n"] and
                d["anchor_hash"] == s["anchor_hash"] == anchors[idx,]["sha256"] and
                int(d["anchor_n"]) == int(s["anchor_n"]) == 40 and
                int(d["anchor_seed"]) == int(s["anchor_seed"]) == int(anchors[idx,]["seed"]) == 17000000+i and
                int(d["pit_primary_seed"]) == int(s["primary_seed"]) == 38000000+i and
                int(d["pit_alternate_seed"]) == int(s["secondary_seed"]) == 39000000+i and
                int(d["fitter_seed"]) == 123, (idx, "C2 input, fitted model, result or seed identity"))
        if small_inputs:
            f = small_inputs[idx,]
            require(f["routine_md5"] == d["ribench_hashcode"] and f["routine_sha256"] == d["routine_hash"] and
                    f["anchor_sha256"] == d["anchor_hash"] and f["archive_sha256"] == d["stage1_model_sha256"],
                    (idx, "Stage 0 input identity"))
    return ids, design, checks, estimates, small_limits, small_deltas
