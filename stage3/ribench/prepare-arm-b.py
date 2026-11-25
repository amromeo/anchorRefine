"""Recover the published Task E rows and preserve all original columns for export."""
import csv
import gzip
import hashlib
import io
import json
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
sources = json.loads((here.parents[1] / "stage2/ribench/comparators/sources.json").read_text())
cache = Path(sys.argv[1])
for cohort in ("small", "large"):
    rows = []
    fields = None
    for item in sources["files"]:
        name = item["cache"]
        keep = name.startswith("accuracy/results/diagnostics/part-") if cohort == "small" else name == "armB-fits.csv"
        if not keep:
            continue
        payload = (cache / name).read_bytes()
        if hashlib.sha256(payload).hexdigest() != item["sha256"]:
            raise ValueError(name)
        reader = csv.DictReader(io.StringIO(payload.decode()))
        if fields is not None and fields != reader.fieldnames:
            raise ValueError(f"Source schema differs for {name}")
        fields = reader.fieldnames
        rows.extend(r for r in reader if r["method"] == "armB" and r["stage"] ==
                    ("small" if cohort == "small" else "50000") and r["dataset_id"].startswith("r-"))
    if len(rows) != (2880 if cohort == "small" else 1440) or len({row["Index"] for row in rows}) != len(rows):
        raise ValueError(f"Unexpected {cohort} Arm B inventory")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(sorted(rows, key=lambda r: int(r["Index"])))
    with (here / f"arm-b-{cohort}.csv.gz").open("wb") as target:
        with gzip.GzipFile(filename="", mode="wb", fileobj=target, mtime=0) as archive:
            archive.write(stream.getvalue().encode())
