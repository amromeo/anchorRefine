"""Publish the RIbench Task G index, model and decision joins, and original Arm B evidence."""
import csv
import gzip
import io
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from stage3.taskg import ARMS, ZERO, digest, require

HERE = Path(__file__).resolve().parent
COMPARATORS = ROOT / "stage2/ribench/comparators"
SEEDS = {"primary": "pit_primary_seed", "alternate": "pit_alternate_seed"}
SHARDS = 48


def compare_primary(path, aggregate, fits=False):
    with path.open(newline="") as stream:
        original = csv.DictReader(stream)
        aux = {f"{ext}_{s}" for ext in ("native", "historical")
               for s in ("z_upper_before_group", "group_has_zero_upper")} if fits else set()
        require(set(aggregate.fieldnames) == set(original.fieldnames) | aux,
                f"Incorrect aggregate schema for {path}")
        for row in original:
            published = next(aggregate, None)
            require(published is not None, f"Short table for {path}")
            if fits:
                for ext in ("native", "historical"):
                    key = ext + "_z_upper"
                    before = published.pop(key + "_before_group")
                    flag = published.pop(ext + "_group_has_zero_upper")
                    require(flag in ("TRUE", "FALSE"), f"Invalid zero group flag for {path}")
                    expected = row[key + "_if_group_zero"] if flag == "TRUE" else row[key]
                    require(published[key] == expected, f"Invalid grouped z for {row['Index']}")
                    published[key] = before
            require(row == published, f"Changed {path.name} cells for {row['Index']}/{row['arm']}")
            yield row


def arm_b(cohort, output, parents):
    source = COMPARATORS / "comparators.csv.gz"
    destination = output / "task-g-arm-b.csv.gz"
    canonical = {}
    with gzip.open(source, "rt", newline="") as stream, destination.open("wb") as target:
        rows = csv.DictReader(stream)
        with gzip.GzipFile(filename="", fileobj=target, mode="wb", mtime=0) as comp:
            with io.TextIOWrapper(comp, newline="") as text:
                writer = csv.DictWriter(text, rows.fieldnames, lineterminator="\n")
                writer.writeheader()
                for row in rows:
                    i = int(row["Index"])
                    if row["method"] != "taskE_armB" or i not in parents:
                        continue
                    parent = parents[i]
                    require(i not in canonical and all(row[k] == parent[k] for k in
                        ("routine_hash", "anchor_hash", "anchor_seed", "ribench_hashcode", "N", "Analyte", "Scenario"))
                        and float(row["fractionPathol"]) == float(parent["fractionPathol"]),
                        f"Arm B paired inputs differ for {i}")
                    writer.writerow(row)
                    canonical[i] = row
    require(canonical.keys() == parents.keys(), "Arm B pairing incomplete")
    name = "task-g-arm-b-original.csv.gz"
    shutil.copyfile(HERE / f"arm-b-{cohort}.csv.gz", output / name)
    with gzip.open(output / name, "rt", newline="") as f:
        seen = set()
        for row in csv.DictReader(f):
            i = int(row["Index"])
            r = canonical[i]
            require(i not in seen and row["dataset_id"] == f"r-{i}" and
                    row["Analyte"] == r["Analyte"] and row["technical"] == "FALSE" and
                    (row["declined"] == "TRUE") == (r["reported_status"] == "declined"),
                    f"External Arm B decision does not match original for {i}")
            seen.add(i)
        require(seen == set(canonical), "Arm B source inventory")
    extra = [destination, output / name]
    if cohort == "small":
        path = output / "task-g-arm-b-component.csv.gz"
        shutil.copyfile(COMPARATORS / "small-armB-selected.csv.gz", path)
        with gzip.open(path, "rt") as stream:
            rows = list(csv.DictReader(stream))
            require(len(rows) == len(parents) and {int(r["Index"]) for r in rows} == set(parents),
                    "Small Arm B component coverage")
            require(all(all(r[k] == parents[int(r["Index"])][k] for k in ("routine_hash", "anchor_hash"))
                        for r in rows), "Small Arm B component hashes")
        extra.append(path)
    shutil.copyfile(COMPARATORS / "sources.json", output / "task-g-comparator-provenance.json")
    return extra + [output / "task-g-comparator-provenance.json"]


def export(cohort, raw, output):
    evidence = output / "evidence"
    audit = json.loads((evidence / "audit.json").read_text())
    design = ROOT / "stage2/ribench" / f"design-{cohort}.csv"
    with design.open(newline="") as f:
        ids = {int(r["Index"]) for r in csv.DictReader(f)}
    require(audit["passed"] and audit["cohort"] == cohort and audit["datasets"] == len(ids), "Incomplete audit")
    with (evidence / "audit-shards.csv").open(newline="") as stream:
        audited = {int(r["shard"]): r for r in csv.DictReader(stream)}
    require(set(audited) == set(range(1, SHARDS + 1)), "Audit shard inventory")
    fits = evidence / "fits.csv.gz"
    checks = evidence / "checks.csv.gz"
    all_arms = set(ARMS + ZERO)
    parents, index, objects = {}, {}, []
    with gzip.open(fits, "rt", newline="") as fitfile, gzip.open(checks, "rt", newline="") as checkfile:
        fit_rows, check_rows = csv.DictReader(fitfile), csv.DictReader(checkfile)
        for shard in range(1, SHARDS + 1):
            role = f"primary-{shard}"
            source = raw / role
            archive = f"artifacts/stage3-ribench-{cohort}-{shard}.zip"
            member = f"{role}/results.rds"
            rds = source / "results.rds"
            rds_hash = digest(rds)
            require(rds_hash == audited[shard]["results.rds"], f"RDS digest, shard {shard}")
            with (source / "object-index.csv").open(newline="") as f:
                positions = {}
                for row in csv.DictReader(f):
                    i = int(row["Index"])
                    require(i == int(row["j"]) and i in ids and i not in positions and i not in index, i)
                    positions[i] = row
            require(len(positions) == len(ids) // SHARDS and
                    sorted(int(r["rds_position"]) for r in positions.values()) ==
                    list(range(1, len(positions) + 1)), f"Invalid RDS positions, shard {shard}")
            objects.append(dict(shard=shard, archive=archive, member=member, rds_sha256=rds_hash,
                                bytes=rds.stat().st_size, datasets=len(positions)))
            seen = {i: set() for i in positions}
            for row in compare_primary(source / "fits.csv", fit_rows, fits=True):
                i, arm = int(row["Index"]), row["arm"]
                require(row["Index"] == row["j"] and arm in all_arms and arm not in seen[i] and
                        all(row[k] == positions[i][k] for k in ("routine_hash","anchor_hash","N")),
                        f"Invalid fit for {i}/{arm}")
                if arm == "stage2":
                    parents[i] = row
                seen[i].add(arm)
            require(all(arms == all_arms for arms in seen.values()), f"Missing fit in {role}")
            seen = {i: set() for i in positions}
            for row in compare_primary(source / "checks.csv", check_rows):
                i, arm = int(row["Index"]), row["arm"]
                kind = row["seed_kind"]
                key = arm, kind
                require(row["Index"] == row["j"] and arm in all_arms and key not in seen[i] and
                        row["panel"] == "guidance" and kind in SEEDS and row["seed"] == parents[i][SEEDS[kind]],
                        f"Invalid check for {i}/{key}")
                seen[i].add(key)
            require(all(len(keys) == 2 * len(all_arms) for keys in seen.values()), f"Missing checks in {role}")
            for i,p in positions.items():
                index[i] = dict(Index=i, j=i, N=p["N"], stage2_fallback=parents[i]["fallback"],
                                Analyte=parents[i]["Analyte"], Scenario=parents[i]["Scenario"],
                                fractionPathol=parents[i]["fractionPathol"], shard=shard, archive=archive,
                                member=member, rds_position=p["rds_position"],
                                routine_hash=p["routine_hash"], anchor_hash=p["anchor_hash"])
        require(next(fit_rows, None) is None and next(check_rows, None) is None,"Trailing records")
    require(set(index) == ids, "Missing dataset IDs")
    idx = output / "task-g-index.csv"
    with idx.open("w", newline="") as f:
        writer=csv.DictWriter(f, next(iter(index.values())).keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(index[i] for i in sorted(index))
    guide = output / "TASK-G.md"
    shutil.copyfile(HERE / "TASK-G.md", guide)
    files = [fits, checks, idx, guide, evidence / "audit.json", *arm_b(cohort, output, parents)]
    manifest = dict(phase="ribench", cohort=cohort, run_id=os.environ.get("GITHUB_RUN_ID"),
                    run_commit=os.environ.get("GITHUB_SHA"), datasets=len(ids),
                    scientific_arms=ARMS, zero_weight_audit_arms=ZERO, external_comparator="taskE_armB",
                    fit_rows=len(ids)*len(all_arms), check_rows=len(ids)*len(all_arms)*2,
                    fit_key=["j","arm"], check_key=["j","arm","panel","seed_kind"], dataset_key="Index",
                    sha256={str(p.relative_to(output)):digest(p) for p in files}, primary_rds=objects)
    (output / "task-g-manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(f"Task G RIbench {cohort}: {len(ids)} datasets, {manifest['fit_rows']} fits, {manifest['check_rows']} checks")


if __name__ == "__main__":
    export(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]))
