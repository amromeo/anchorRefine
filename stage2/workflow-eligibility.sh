#!/usr/bin/env bash
set -euo pipefail
python3 - "$@" <<'PY'
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def api(path):
    return subprocess.check_output(["gh", "api", path])


def validate(audit):
    expected = {"datasets": 1440, "archived_matches": 1440, "exact_repeat_shards": 48,
                "distinct_host_shards": 48}
    require(audit["passed"] is True and audit["rule"] == "peak" and audit["source_arm"] == "peak"
            and all(audit[k] == v for k, v in expected.items()),
            "Incomplete or failed development reproduction")


def make_receipt(audit_bytes, run_id, commit, attempt):
    validate(json.loads(audit_bytes))
    return dict(mode="development", rule="peak", K=24, repo=repo, workflow=workflow,
                development_run_id=run_id, run_attempt=attempt, development_commit=commit,
                source_manifest_sha256=sha(Path("stage2/selected-sources.sha256").read_bytes()),
                selected_source_sha256=sha(rule_source), audit_sha256=sha(audit_bytes))


repo = os.environ["GITHUB_REPOSITORY"]
workflow = ".github/workflows/stage2-selected.yml"
commit = os.environ["GITHUB_SHA"]
run_id = int(os.environ["GITHUB_RUN_ID"])
require(repo == "amromeo/anchorRefine" and os.environ["GITHUB_EVENT_NAME"] == "workflow_dispatch",
        "Expected a manual anchorRefine workflow dispatch")
attempt = int(os.environ["GITHUB_RUN_ATTEMPT"])
require(re.fullmatch(r"[0-9a-f]{40}", commit) and attempt >= 1,
        "Expected a dispatch attempt at a specific commit")
rule_source = Path("R/stage2-selected.R").read_bytes()
require(re.findall(rb'^stage2_selected_rule\s*<-\s*"([^"]+)"\s*$', rule_source, re.M) == [b"peak"],
        "Selected-rule declaration differs from the published choice")

if sys.argv[1:] == ["issue"]:
    require(os.environ["MODE"] == "development", "Only development can issue an eligibility record")
    raw = Path("output/evidence/audit.json").read_bytes()
    receipt = make_receipt(raw, run_id, commit, attempt)
    Path("output/eligibility.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
elif sys.argv[1:] == ["gate"]:
    mode = os.environ["MODE"]
    supplied = os.environ.get("DEVELOPMENT_RUN_ID", "")
    if mode == "development":
        require(supplied == "", "Development takes no previous run ID")
        sys.exit(0)
    require(mode == "confirmation" and re.fullmatch(r"[1-9][0-9]{0,18}", supplied),
            "Confirmation requires the completed development run ID")
    dev_id = int(supplied)
    prefix = f"repos/{repo}/actions"
    dev = json.loads(api(f"{prefix}/runs/{dev_id}"))
    require(dev["id"] == dev_id and dev["event"] == "workflow_dispatch"
            and dev["repository"]["full_name"] == repo and dev["path"] == workflow
            and dev["display_title"] == "Stage 2 selected development"
            and dev["status"] == "completed" and dev["conclusion"] == "success",
            "The supplied ID is not a successful selected-rule development run")
    archives = json.loads(api(f"{prefix}/runs/{dev_id}/artifacts?per_page=100"))
    require(archives["total_count"] == len(archives["artifacts"]), "Incomplete artifact listing")
    receipts = [a for a in archives["artifacts"] if a["name"] == "selected-development-receipt"]
    require(len(receipts) == 1, "Expected a single development receipt in the GitHub artifact index")
    artifact = receipts[0]
    published = Path(f"results/stage2-selected-development-{dev_id}")
    original_zip = published / "artifacts" / "selected-development-receipt.zip"
    if original_zip.is_file():
        raw = original_zip.read_bytes()
    else:
        require(not artifact["expired"], "The original receipt ZIP has expired and was not preserved locally")
        raw = api(f"{prefix}/artifacts/{artifact['id']}/zip")
    require(len(raw) == artifact["size_in_bytes"] and "sha256:" + sha(raw) == artifact["digest"],
            "Development receipt ZIP failed its GitHub digest or byte count")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        require(len(archive.namelist()) == len(set(archive.namelist())), "Ambiguous receipt ZIP members")
        receipt_bytes = archive.read("eligibility.json")
        audit_bytes = archive.read("evidence/audit.json")
    require((published / "eligibility.json").read_bytes() == receipt_bytes, "Committed eligibility differs from the successful Actions receipt")
    receipt = json.loads(receipt_bytes)
    producing = receipt["run_attempt"]
    require(type(producing) is int and 1 <= producing <= dev["run_attempt"], "Invalid development attempt")
    archived_attempt = json.loads(api(f"{prefix}/runs/{dev_id}/attempts/{producing}"))
    require(archived_attempt["id"] == dev_id and archived_attempt["run_attempt"] == producing
            and archived_attempt["head_sha"] == dev["head_sha"] and archived_attempt["conclusion"] == "success",
            "The receipt-producing attempt did not succeed at the recorded commit")
    require(receipt == make_receipt(audit_bytes, dev_id, dev["head_sha"], producing),
            "Frozen sources, selected rule or technical audit differ from the successful development run")

    # This workflow's confirmation concurrency group serializes these checks.
    # A dispatch that failed its gate has never run a confirmation worker.
    pages = json.loads(subprocess.check_output(
        ["gh", "api", "--paginate", "--slurp", f"{prefix}/workflows/stage2-selected.yml/runs?event=workflow_dispatch&per_page=100"]))
    for page in pages:
        for prior in page["workflow_runs"]:
            if prior["id"] == run_id or prior["display_title"] != "Stage 2 selected confirmation":
                continue
            count = prior["run_attempt"]
            for attempt in range(1, count + 1):
                lookup = f"{prefix}/runs/{prior['id']}/attempts/{attempt}/jobs?per_page=100"
                jobs = json.loads(api(lookup))
                require(jobs["total_count"] == len(jobs["jobs"]), "Incomplete confirmation-job listing")
                opened = any(s["name"] == "Run paired fits" and s["status"] != "queued"
                             and s.get("conclusion") != "skipped"
                             for j in jobs["jobs"] for s in j.get("steps", []))
                require(not opened, f"Confirmation was previously opened in run {prior['id']}")
    print(f"Verified published development run {dev_id} at {dev['head_sha']} and its source lock")
else:
    raise ValueError("Usage: bash stage2/workflow-eligibility.sh gate|issue")
PY
