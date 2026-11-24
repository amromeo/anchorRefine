"""Bind full development to the verified influence report at the same source freeze."""

import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile


REPOSITORY = "amromeo/anchorRefine"
WORKFLOW = ".github/workflows/stage3-development.yml"
INFLUENCE_REPORT = "stage3-influence-report"
FILES = ("evidence/audit.json", "influence.csv", "REPORT.md", "receipt.json")


def require(valid, message):
    if not valid:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def api(path):
    return subprocess.check_output(["gh", "api", f"repos/{REPOSITORY}/actions/{path}"])


def validate(files):
    audit = json.loads(files["evidence/audit.json"])
    require(audit["passed"] is True and audit["phase"] == "influence"
            and audit["datasets"] == 96
            and audit["exact_repeat_shards"] == audit["distinct_host_shards"] == 24,
            "The prior influence technical audit is incomplete")
    rows = list(csv.DictReader(io.StringIO(files["influence.csv"].decode())))
    cells = {(n, w) for n in (1000, 1500, 5000, 50000) for w in (0, 1, 10, 100, 1000, 10000)}
    require(len(rows) == len(cells) and
            {(int(r["N"]), float(r["weight"])) for r in rows} == cells,
            "Expected each influence weight crossed with each routine sample size")
    for row in rows:
        n = int(row["measurable"])
        require(int(row["planned"]) == 24 and 0 <= n <= 24, "Invalid influence denominator")
        if n:
            medians = [float(row[x]) for x in ("center_signed", "center_absolute", "spread_signed", "spread_absolute")]
            require(all(math.isfinite(x) for x in medians), "Influence medians are incomplete")
            if float(row["weight"]) == 0:
                require(all(x == 0 for x in medians), "Weight zero differs from Stage 2")
    require(files["REPORT.md"].strip() and json.loads(files["receipt.json"]),
            "Influence report or report receipt missing")


def receipt(files, run, attempt, commit):
    validate(files)
    return dict(phase="influence", run_id=run, run_attempt=attempt, commit=commit,
                source_manifest_sha256=sha(Path("stage3/SHA256SUMS").read_bytes()),
                report_files_sha256={name: sha(files[name]) for name in FILES})


def gate(previous_id, copy_to):
    run = json.loads(api(f"runs/{previous_id}"))
    require(run["id"] == previous_id and run["status"] == "completed" and run["conclusion"] == "success"
            and run["event"] == "workflow_dispatch" and run["repository"]["full_name"] == REPOSITORY
            and run["path"] == WORKFLOW and run["display_title"] == "Stage 3 influence",
            "Expected a successful Stage 3 influence run")
    page = json.loads(api(f"runs/{previous_id}/artifacts?per_page=100"))
    require(len(page["artifacts"]) == page["total_count"], "Influence artifact index is incomplete")
    reports = [a for a in page["artifacts"] if a["name"] == INFLUENCE_REPORT]
    require(len(reports) == 1, "Expected one influence report ZIP")
    report = reports[0]
    original = Path(f"results/stage3-influence-{previous_id}/artifacts/{INFLUENCE_REPORT}.zip")
    if original.is_file():
        data = original.read_bytes()
    else:
        require(not report["expired"], "The influence report has expired and has no permanent copy here")
        data = api(f"artifacts/{report['id']}/zip")
    require(report["size_in_bytes"] == len(data) and report["digest"] == "sha256:" + sha(data),
            "The influence report ZIP differs from GitHub's byte count or SHA-256")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        require(len(archive.namelist()) == len(set(archive.namelist())), "Duplicate influence report members")
        record = json.loads(archive.read("eligibility.json"))
        files = {name: archive.read(name) for name in FILES}
    producing = record["run_attempt"]
    require(type(producing) is int and 1 <= producing <= run["run_attempt"],
            "Invalid influence report attempt")
    attempt = json.loads(api(f"runs/{previous_id}/attempts/{producing}"))
    require(attempt["id"] == previous_id and attempt["run_attempt"] == producing
            and attempt["head_sha"] == run["head_sha"] and attempt["conclusion"] == "success",
            "The influence report-producing attempt did not succeed at the recorded revision")
    require(record == receipt(files, previous_id, producing, run["head_sha"]),
            "Influence audit, report files or source freeze differ")
    if copy_to:
        copy_to.mkdir(parents=True, exist_ok=True)
        (copy_to / "influence.csv").write_bytes(files["influence.csv"])
        evidence = dict(**record, artifact_id=report["id"], artifact_digest=report["digest"],
                        artifact_size=report["size_in_bytes"])
        (copy_to / "influence-provenance.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(f"Verified influence run {previous_id}, attempt {producing} at {run['head_sha']}")


def main(args):
    require(args in (["gate"], ["issue"]) or (len(args) == 2 and args[0] == "copy"),
            "Usage: eligibility.py gate|issue|copy DIRECTORY")
    repo = os.environ["GITHUB_REPOSITORY"]
    phase = os.environ["PHASE"]
    commit = os.environ["GITHUB_SHA"]
    run = int(os.environ["GITHUB_RUN_ID"])
    attempt = int(os.environ["GITHUB_RUN_ATTEMPT"])
    require(repo == REPOSITORY and os.environ["GITHUB_EVENT_NAME"] == "workflow_dispatch"
            and re.fullmatch(r"[0-9a-f]{40}", commit) and run > 0 and attempt >= 1,
            "Unexpected Stage 3 workflow context")
    previous = os.environ.get("INFLUENCE_RUN_ID", "")
    if phase == "influence":
        require(not previous and args[0] != "copy", "Influence takes no prior run ID")
        if args == ["issue"]:
            output = Path("output")
            files = {name: (output / name).read_bytes() for name in FILES}
            (output / "eligibility.json").write_text(
                json.dumps(receipt(files, run, attempt, commit), indent=2, sort_keys=True) + "\n")
    else:
        require(phase == "development" and args[0] != "issue" and re.fullmatch(r"[1-9][0-9]{0,18}", previous),
                "Development requires the successful influence run ID")
        gate(int(previous), Path(args[1]) if args[0] == "copy" else None)


if __name__ == "__main__":
    main(sys.argv[1:])
