"""Bind cohort progression and escalation to GitHub's authenticated audit artifacts."""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

REPO = "amromeo/anchorRefine"
WORKFLOW = ".github/workflows/stage3-ribench.yml"
MANIFEST = Path("stage3/ribench/SHA256SUMS")
COHORT_SIZE = {"small": 2880, "large": 1440}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def api(path):
    return subprocess.check_output(["gh", "api", f"repos/{REPO}/actions/{path}"])


def run_id(value):
    require(re.fullmatch(r"[1-9][0-9]{0,18}", value), "Expected a GitHub run ID")
    return int(value)


def outcome(audit, cohort, mode):
    require(audit["cohort"] == cohort and audit["mode"] == mode, "Wrong audit cohort or mode")
    if audit["passed"] is True:
        n = COHORT_SIZE[cohort]
        expected = n if mode == "full" else n // 10
        require(audit["full_required"] is False and audit["datasets"] == n
                and audit["audited_datasets"] == expected
                and audit["same_host_exact_datasets"] == audit["cross_host_passed_datasets"] == expected
                and audit["exact_repeat_shards"] == audit["distinct_host_shards"] == 48
                and audit["archived_baseline_matches"] == n and audit["archive_reproduction_passed"] is True,
                "Incomplete technical audit")
        return "passed"
    require(audit["passed"] is False and mode == "sampled" and audit["full_required"] is True,
            "Only a sampled comparison discrepancy can authorize the full repeat")
    return "full_required"


def receipt(audit_bytes, cohort, mode, run, attempt, commit):
    audit = json.loads(audit_bytes)
    manifest_sha = sha(MANIFEST.read_bytes())
    require(audit["source_manifest_sha256"] == manifest_sha and
            audit["sample_sha256"] == sha(MANIFEST.with_name("audit-sample.csv").read_bytes()),
            "Audit source freeze or sampled dataset identity differs")
    return dict(cohort=cohort, mode=mode, outcome=outcome(audit, cohort, mode),
                run_id=run, run_attempt=attempt, commit=commit,
                source_manifest_sha256=manifest_sha, audit_sha256=sha(audit_bytes))


def check_prior(run_number, cohort, expected_outcome):
    info = json.loads(api(f"runs/{run_number}"))
    conclusion = "success" if expected_outcome == "passed" else "failure"
    require(info["id"] == run_number and info["repository"]["full_name"] == REPO
            and info["event"] == "workflow_dispatch" and info["status"] == "completed"
            and info["path"] == WORKFLOW and info["conclusion"] == conclusion,
            f"Run {run_number} does not have the required workflow provenance and conclusion")
    listing = json.loads(api(f"runs/{run_number}/artifacts?per_page=100"))
    require(len(listing["artifacts"]) == listing["total_count"], "Incomplete GitHub artifact listing")
    name = f"stage3-ribench-{cohort}-report"
    matches = [a for a in listing["artifacts"] if a["name"] == name]
    require(len(matches) == 1, "Expected one audit or completed report")
    artifact = matches[0]
    archive = Path(f"results/stage3-ribench-{cohort}-{run_number}/artifacts/{name}.zip")
    if archive.is_file():
        data = archive.read_bytes()
    else:
        require(not artifact["expired"], "The original report ZIP must be restored from the permanent archive")
        data = api(f"artifacts/{artifact['id']}/zip")
    require(len(data) == artifact["size_in_bytes"] and "sha256:" + sha(data) == artifact["digest"],
            "Prior report ZIP differs from GitHub's size or SHA-256")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        require(len(z.namelist()) == len(set(z.namelist())), "Ambiguous prior report ZIP members")
        record = json.loads(z.read("eligibility.json"))
        audit_bytes = z.read("evidence/audit.json")
        require(z.read("source-manifest.sha256") == MANIFEST.read_bytes(),
                "The prior run used a different source freeze")
    mode, attempt = record["mode"], record["run_attempt"]
    require(mode in ("sampled", "full") and type(attempt) is int and 1 <= attempt <= info["run_attempt"]
            and info["display_title"] == f"Stage 3 RIbench {cohort} {mode}", "Wrong prior mode or attempt")
    prior = json.loads(api(f"runs/{run_number}/attempts/{attempt}"))
    require(prior["id"] == run_number and prior["run_attempt"] == attempt
            and prior["head_sha"] == info["head_sha"] and prior["conclusion"] == conclusion,
            "Prior run attempt differs from its receipt")
    calculated = receipt(audit_bytes, cohort, mode, run_number, attempt, info["head_sha"])
    require(all(record.get(k) == value for k, value in calculated.items())
            and calculated["outcome"] == expected_outcome, "Prior technical receipt is ineligible")
    print(f"Verified {cohort} {mode} run {run_number}, attempt {attempt}, {expected_outcome}")


def main(command):
    cohort = os.environ["COHORT"]
    mode = os.environ["AUDIT_MODE"]
    commit = os.environ["GITHUB_SHA"]
    attempt = int(os.environ["GITHUB_RUN_ATTEMPT"])
    current = run_id(os.environ["GITHUB_RUN_ID"])
    require(cohort in COHORT_SIZE and mode in ("sampled", "full") and attempt >= 1
            and re.fullmatch(r"[0-9a-f]{40}", commit) and os.environ["GITHUB_REPOSITORY"] == REPO
            and os.environ["GITHUB_EVENT_NAME"] == "workflow_dispatch", "Unexpected workflow context")
    small = os.environ.get("SMALL_RUN_ID", "")
    sampled = os.environ.get("SAMPLED_RUN_ID", "")
    require(bool(small) == (cohort == "large"), "Only large runs require a passed small run ID")
    require(bool(sampled) == (mode == "full"), "Only full repeats require a prior sampled failure ID")
    small = run_id(small) if small else None
    sampled = run_id(sampled) if sampled else None
    require(current not in (small, sampled), "A run cannot serve as its own prerequisite")
    if command == "gate":
        if small is not None:
            check_prior(small, "small", "passed")
        if sampled is not None:
            check_prior(sampled, cohort, "full_required")
    else:
        require(command == "issue", "Expected gate or issue")
        record = receipt(Path("output/evidence/audit.json").read_bytes(), cohort, mode,
                         current, attempt, commit)
        record.update(prior_small_run=small, prior_sampled_run=sampled)
        Path("output/eligibility.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main(sys.argv[1])
