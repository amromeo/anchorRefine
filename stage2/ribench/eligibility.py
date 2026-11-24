"""Bind the N=50,000 dispatch to the successful small-cohort technical audit."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def api(path):
    return subprocess.check_output(["gh", "api", path])


def validate(audit):
    counts = {"datasets": 2880, "archived_baseline_matches": 2880, "exact_repeat_shards": 48,
              "distinct_host_shards": 48}
    require(audit["passed"] is True and audit["cohort"] == "small"
            and all(audit[k] == expected for k, expected in counts.items()),
            "Incomplete or failed small-cohort technical audit")


def receipt(audit_bytes, run, attempt, commit):
    validate(json.loads(audit_bytes))
    return dict(cohort="small", run_id=run, run_attempt=attempt, commit=commit,
                source_manifest_sha256=sha(Path("stage2/ribench/SHA256SUMS").read_bytes()),
                audit_sha256=sha(audit_bytes))


def main(command):
    repo = os.environ["GITHUB_REPOSITORY"]
    run_id = int(os.environ["GITHUB_RUN_ID"])
    attempt = int(os.environ["GITHUB_RUN_ATTEMPT"])
    commit = os.environ["GITHUB_SHA"]
    cohort = os.environ["COHORT"]
    require(repo == "amromeo/anchorRefine" and os.environ["GITHUB_EVENT_NAME"] == "workflow_dispatch"
            and attempt >= 1 and re.fullmatch(r"[0-9a-f]{40}", commit), "Unexpected workflow environment")
    if command == "issue":
        require(cohort == "small", "Only the small cohort issues a technical receipt")
        data = receipt(Path("output/evidence/audit.json").read_bytes(), run_id, attempt, commit)
        Path("output/eligibility.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        return
    require(command == "gate", "Expected gate or issue")
    supplied = os.environ.get("SMALL_RUN_ID", "")
    if cohort == "small":
        require(not supplied, "The small dispatch takes no prior run ID")
        return
    require(cohort == "large" and re.fullmatch(r"[1-9][0-9]{0,18}", supplied),
            "The large dispatch requires the completed small run ID")
    small = int(supplied)
    prefix = f"repos/{repo}/actions"
    run = json.loads(api(f"{prefix}/runs/{small}"))
    require(run["id"] == small and run["event"] == "workflow_dispatch" and run["status"] == "completed"
            and run["conclusion"] == "success" and run["repository"]["full_name"] == repo
            and run["path"] == ".github/workflows/stage2-ribench.yml"
            and run["display_title"] == "Stage 2 RIbench small", "Expected a successful small-cohort run")

    listed = json.loads(api(f"{prefix}/runs/{small}/artifacts?per_page=100"))
    require(len(listed["artifacts"]) == listed["total_count"], "Incomplete artifact list")
    reports = [item for item in listed["artifacts"] if item["name"] == "ribench-small-report"]
    require(len(reports) == 1, "Expected one small report artifact")
    report = reports[0]
    permanent = Path(f"results/stage2-ribench-small-{small}/artifacts/ribench-small-report.zip")
    if permanent.is_file():
        data = permanent.read_bytes()
    else:
        require(not report["expired"], "The small report is no longer live or locally archived")
        data = api(f"{prefix}/artifacts/{report['id']}/zip")
    require(len(data) == report["size_in_bytes"] and "sha256:" + sha(data) == report["digest"],
            "Small report ZIP does not match GitHub's digest and size")
    with zipfile.ZipFile(io.BytesIO(data)) as artifact:
        require(len(set(artifact.namelist())) == len(artifact.namelist()), "Ambiguous small report ZIP")
        record = json.loads(artifact.read("eligibility.json"))
        audit_bytes = artifact.read("evidence/audit.json")
    producing = record["run_attempt"]
    require(type(producing) is int and 1 <= producing <= run["run_attempt"], "Invalid small audit attempt")
    prior = json.loads(api(f"{prefix}/runs/{small}/attempts/{producing}"))
    require(prior["head_sha"] == run["head_sha"] and prior["conclusion"] == "success"
            and prior["id"] == small and prior["run_attempt"] == producing, "Invalid small audit provenance")
    require(record == receipt(audit_bytes, small, producing, run["head_sha"]),
            "Small technical receipt or frozen RIbench sources differ")
    print(f"Verified the complete small-cohort technical audit from run {small} at {run['head_sha']}")


if __name__ == "__main__":
    main(sys.argv[1])
