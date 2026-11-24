"""Index the audited primary R objects and publish the joins for Task G."""
import csv
import gzip
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

CASES = 7488
SHARDS = 96
ARMS = ("baseline", "stage2", "w1", "t0.25", "anchorsOnly")
ZERO = ("w0", "t0")
INPUT_HASHES = ("routine_hash", "anchor_hash", "diagnostic_hash")
SEEDS = {
    ("guidance", "primary"): "pit_primary_seed",
    ("guidance", "alternate"): "pit_alternate_seed",
    ("diagnostic", "primary"): "diagnostic_primary_seed",
    ("diagnostic", "alternate"): "diagnostic_alternate_seed",
}
FIELDS = ("j", "N", "stage2_fallback", "shard", "archive", "member",
          "rds_position", *INPUT_HASHES)


def require(condition, error):
    if not condition:
        raise ValueError(error)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def identical_rows(path, aggregate):
    """The public aggregate must contain the exact CSV cells from the original run."""
    with path.open(newline="") as stream:
        rows = csv.DictReader(stream)
        require(rows.fieldnames == aggregate.fieldnames, f"{path} schema differs")
        for row in rows:
            require(row == next(aggregate, None), f"{path} differs in dataset {row['j']}")
            yield row


def export(raw, output):
    evidence = output / "evidence"
    audit = json.loads((evidence / "audit.json").read_text())
    require(audit["passed"] and audit["phase"] == "confirmation" and
            audit["datasets"] == CASES and audit["exact_repeat_shards"] == SHARDS and
            audit["distinct_host_shards"] == SHARDS, "Incomplete confirmation audit")
    fits = evidence / "fits.csv.gz"
    checks = evidence / "checks.csv.gz"
    all_arms = set(ARMS + ZERO)
    index = {}
    objects = []
    with (evidence / "audit-shards.csv").open(newline="") as stream:
        audited = {int(r["shard"]): r for r in csv.DictReader(stream)}
    with gzip.open(fits, "rt", newline="") as fitfile, gzip.open(checks, "rt", newline="") as checkfile:
        fit_rows = csv.DictReader(fitfile)
        check_rows = csv.DictReader(checkfile)
        for shard in range(1, SHARDS + 1):
            role = f"primary-{shard}"
            source = raw / role
            archive = f"artifacts/stage3-confirmation-{shard}.zip"
            rds = source / "results.rds"
            rds_hash = digest(rds)
            require(rds_hash == audited[shard]["results.rds"], f"RDS digest, shard {shard}")
            positions = {}
            with (source / "object-index.csv").open(newline="") as stream:
                for row in csv.DictReader(stream):
                    j = int(row["j"])
                    require(j not in index and j not in positions, f"Duplicate dataset {j}")
                    require(1 <= j <= CASES, f"Unknown dataset {j}")
                    positions[j] = row
            require(len(positions) == CASES // SHARDS and
                    sorted(int(r["rds_position"]) for r in positions.values()) ==
                    list(range(1, len(positions) + 1)), f"Invalid R object positions, shard {shard}")
            objects.append(dict(shard=shard, archive=archive, member=f"{role}/results.rds",
                                rds_sha256=rds_hash, bytes=rds.stat().st_size, datasets=len(positions)))
            seen = {j: set() for j in positions}
            parents = {}
            for row in identical_rows(source / "fits.csv", fit_rows):
                j, arm = int(row["j"]), row["arm"]
                require(arm in all_arms and arm not in seen[j] and row["phase"] == "confirmation",
                        f"Unexpected fit {(j, arm)}")
                seen[j].add(arm)
                require(all(row[k] == positions[j][k] for k in ("N", *INPUT_HASHES)),
                        f"Saved inputs disagree for {(j, arm)}")
                if arm == "stage2":
                    parents[j] = row
            require(all(arms == all_arms for arms in seen.values()), f"Missing fit in shard {shard}")
            decisions = {j: set() for j in positions}
            for row in identical_rows(source / "checks.csv", check_rows):
                j, arm = int(row["j"]), row["arm"]
                panel = row["panel"], row["seed_kind"]
                key = (arm, *panel)
                require(arm in all_arms and key not in decisions[j] and panel in SEEDS and
                        row["seed"] == parents[j][SEEDS[panel]], f"Invalid check {(j, *key)}")
                decisions[j].add(key)
            require(all(len(keys) == 4 * len(all_arms) for keys in decisions.values()),
                    f"Missing decisions in shard {shard}")
            for j, position in positions.items():
                index[j] = dict(j=j, N=position["N"], stage2_fallback=parents[j]["fallback"],
                                shard=shard, archive=archive, member=f"{role}/results.rds",
                                rds_position=position["rds_position"],
                                **{k: position[k] for k in INPUT_HASHES})
        require(next(fit_rows, None) is None and next(check_rows, None) is None,
                "Public tables include unexpected trailing records")
    require(set(index) == set(range(1, CASES + 1)), "Missing datasets")
    index_file = output / "task-g-index.csv"
    with index_file.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(index[j] for j in sorted(index))
    guide = output / "TASK-G.md"
    shutil.copyfile(Path(__file__).with_name("TASK-G.md"), guide)
    files = [fits, checks, index_file, guide, evidence / "audit.json"]
    manifest = dict(phase="confirmation", run_id=os.environ.get("GITHUB_RUN_ID"),
                    run_commit=os.environ.get("GITHUB_SHA"), datasets=CASES,
                    scientific_arms=ARMS, zero_weight_audit_arms=ZERO,
                    fit_rows=CASES * len(all_arms), check_rows=CASES * len(all_arms) * 4,
                    fit_key=["j", "arm"], check_key=["j", "arm", "panel", "seed_kind"],
                    sha256={str(p.relative_to(output)): digest(p) for p in files},
                    primary_rds=objects)
    (output / "task-g-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Task G: {len(index)} datasets, {manifest['fit_rows']} fits, {manifest['check_rows']} checks")


if __name__ == "__main__":
    export(*map(Path, sys.argv[1:]))
