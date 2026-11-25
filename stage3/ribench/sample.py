"""Reproduce the fixed RIbench audit sample from the original design rows."""
import csv
import hashlib
import io
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
COHORTS = {"small": (1000, 5000), "large": (50000,)}
SEED = 20261125
FIELDS = ("cohort", "Index", "N", "Analyte", "fractionPathol", "stratum_n",
          "stratum_sample_n", "draw_rank", "seed")


def rank(label, *values):
    key = "|".join(str(v) for v in (SEED, label, *values))
    return hashlib.sha256(key.encode("ascii")).digest()


def sample_rows():
    selected = []
    for cohort, sizes in COHORTS.items():
        path = HERE.parents[1] / "stage2" / "ribench" / f"design-{cohort}.csv"
        with path.open(newline="") as stream:
            strata = defaultdict(list)
            for row in csv.DictReader(stream):
                strata[int(row["N"]), row["Analyte"], row["fractionPathol"]].append(int(row["Index"]))
        if {key[0] for key in strata} != set(sizes):
            raise ValueError(f"Unexpected sizes in {cohort}")
        for n in sizes:
            keys = sorted((k for k in strata if k[0] == n),
                          key=lambda k: (rank("allocation", cohort, *k), k))
            if len(keys) != 80 or any(len(strata[k]) != 18 for k in keys):
                raise ValueError(f"Unexpected stratum sizes at N = {n}")
            for position, key in enumerate(keys):
                count = 2 if position < 64 else 1
                indices = sorted(strata[key],
                                 key=lambda i: (rank("dataset", cohort, *key, i), i))
                for draw_rank, index in enumerate(indices[:count], 1):
                    selected.append(dict(zip(FIELDS, (cohort, index, *key, len(indices),
                                                       count, draw_rank, SEED))))
    return sorted(selected, key=lambda r: (r["N"], r["Index"]))


def main():
    data = io.StringIO()
    writer = csv.DictWriter(data, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(sample_rows())
    path = HERE / "audit-sample.csv"
    if sys.argv[1:] == ["--write"]:
        path.write_bytes(data.getvalue().encode("ascii"))
    elif sys.argv[1:] or path.read_bytes() != data.getvalue().encode("ascii"):
        raise SystemExit("Audit sample differs from its fixed draw")


if __name__ == "__main__":
    main()
