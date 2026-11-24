"""Prepare immutable source files for build.R. The Actions ZIP audit is optional."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile


def verified(path, expected):
    with path.open("rb") as f:
        actual = hashlib.file_digest(f, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"SHA-256 mismatch for {path}")


def prepare(cache, zips):
    sources = json.loads(Path(__file__).with_name("sources.json").read_text())
    for path, expected in sources["anchorRefine_inputs"].items():
        verified(Path(path), expected)
    root = f"https://raw.githubusercontent.com/{sources['repository']}/{sources['revision']}/"
    for file in sources["files"]:
        path = cache / file["cache"]
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with urlopen(root + file["path"]) as response:
                payload = response.read()
            if hashlib.sha256(payload).hexdigest() != file["sha256"]:
                raise ValueError(f"Unexpected source bytes for {path}")
            path.write_bytes(payload)
        verified(path, file["sha256"])

    if zips is None:
        return
    # Only the per-key RDS accepted in the published batch manifest is eligible.
    with (cache / "runtime-provenance.csv").open(newline="") as f:
        accepted = [r for r in csv.DictReader(f) if r["key"].startswith("r-")]
    if len({r["key"] for r in accepted}) != len(accepted) or len(accepted) != 2880:
        raise ValueError("Unexpected small-cohort inventory")
    (cache / "fits").mkdir(exist_ok=True)
    for artifact in sources["small_artifacts"]:
        path = zips / (artifact["name"] + ".zip")
        verified(path, artifact["sha256"])
        with ZipFile(path) as bundle:
            for row in accepted:
                batch = f"{row['phase']}-{row['shard']}"
                if "accuracy-" + batch + "-" + row["attempt"] != artifact["name"]:
                    continue
                path_out = cache / "fits" / (row["key"] + ".rds")
                payload = bundle.read(f"{batch}/fits/{path_out.name}")
                if hashlib.sha256(payload).hexdigest() != row["sha256"]:
                    raise ValueError(f"Unexpected fit bytes for {row['key']}")
                path_out.write_bytes(payload)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("--zips", type=Path, help="directory of original Task E ZIP artifacts")
    args = parser.parse_args()
    prepare(args.cache, args.zips)
