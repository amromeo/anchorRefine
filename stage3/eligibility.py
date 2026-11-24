"""Bind full development to the verified influence report at the same source freeze."""

import csv
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
from statistics import median
import subprocess
import sys
import zipfile


REPOSITORY = "amromeo/anchorRefine"
WORKFLOW = ".github/workflows/stage3-development.yml"
INFLUENCE_REPORT = "stage3-influence-report"
TABLES = {"influence.csv": None, "influence-nonfallback.csv": False, "influence-fallback.csv": True}
ORIGINAL_AUDIT = "evidence/original-influence-audit.json"
REPORT_HASHES = {"audit_sha256": "evidence/audit.json", "original_audit_sha256": ORIGINAL_AUDIT,
                 "report_sha256": "REPORT.md", "table_sha256": "influence.csv",
                 "nonfallback_sha256": "influence-nonfallback.csv", "fallback_sha256": "influence-fallback.csv"}
FILES = (*REPORT_HASHES.values(), "evidence/fits.csv.gz", "receipt.json")
SIZES = (1000, 1500, 5000, 50000)
WEIGHTS = (0, 1, 10, 100, 1000, 10000)


def require(valid, message):
    if not valid:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def api(path):
    return subprocess.check_output(["gh", "api", f"repos/{REPOSITORY}/actions/{path}"])


def shift(value):
    return math.nan if value in ("", "NA") else float(value)


def check_tables(files):
    rows = csv.DictReader(io.StringIO(gzip.decompress(files["evidence/fits.csv.gz"]).decode()))
    fits = {(int(r["j"]), r["arm"]): r for r in rows}
    parents = {j: r for (j, arm), r in fits.items() if arm == "stage2"}
    require(set(parents) == set(range(1, 97)) and len(fits) == 96 * 7,
            "Incomplete influence fit evidence")
    for parent in parents.values():
        require(parent["fallback"] in ("TRUE", "FALSE"), "Unknown Stage 2 parent branch")
    cells = {(n, w) for n in SIZES for w in WEIGHTS}
    for filename, partition in TABLES.items():
        rows = list(csv.DictReader(io.StringIO(files[filename].decode())))
        require(len(rows) == len(cells) and {(int(r["N"]), int(r["weight"])) for r in rows} == cells,
                f"{filename} must cover each weight and routine sample size once")
        for row in rows:
            n, w = int(row["N"]), int(row["weight"])
            assigned = [j for j, p in parents.items() if int(p["N"]) == n and
                        (partition is None or (p["fallback"] == "TRUE") == partition)]
            if partition is None:
                require(len(assigned) == 24, f"Expected 24 audited fixtures at N={n}")
            require(int(row["planned"]) == len(assigned) and int(row["parent_fallbacks"]) ==
                    sum(parents[j]["fallback"] == "TRUE" for j in assigned),
                    f"{filename} assignment differs from audited Stage 2 branches at N={n}, w={w}")
            arm = [fits[j, f"w{w}"] for j in assigned]
            require(int(row["weighted_attempts"]) == sum(r["weighted_search_attempted"] == "TRUE" for r in arm),
                    f"{filename} weighted attempts disagree with audited fits at N={n}, w={w}")
            pairs = [(shift(r["center_shift"]), shift(r["spread_shift"])) for r in arm]
            pairs = [(c, s) for c, s in pairs if math.isfinite(c) and math.isfinite(s)]
            require(int(row["measurable"]) == len(pairs) and int(row["unevaluable"]) == len(arm) - len(pairs),
                    f"{filename} measurable count differs from audited fits at N={n}, w={w}")
            if w == 0:
                require(all(c == s == 0 for c, s in pairs), "Weight zero differs from Stage 2")
            for i, parameter in enumerate(("center", "spread")):
                shifts = [p[i] for p in pairs]
                for key, values in ((parameter + "_signed", shifts),
                                    (parameter + "_absolute", [abs(x) for x in shifts])):
                    actual = row[key]
                    require((actual == "") if not pairs else float(actual) == median(values),
                            f"{filename} {key} differs from the audited shifts at N={n}, w={w}")


def validate(files):
    audit = json.loads(files["evidence/audit.json"])
    require(audit["passed"] is True and audit["phase"] == "influence"
            and audit["datasets"] == 96
            and audit["exact_repeat_shards"] == audit["distinct_host_shards"] == 24,
            "The prior influence technical audit is incomplete")
    check_tables(files)
    original = json.loads(files[ORIGINAL_AUDIT])
    require(original["passed"] is True and str(original["original_run_id"]) == "45407973511" and
            original["datasets"] == 96, "Comparison with the archived original influence run did not pass")
    report = json.loads(files["receipt.json"])
    require(report["passed"] is True and report["phase"] == "influence" and report["datasets"] == 96
            and files["REPORT.md"].strip() and all(report[k] == sha(files[v]) for k, v in REPORT_HASHES.items()),
            "Amended influence report receipt differs from the audited evidence")


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
        require(set(FILES).issubset(archive.namelist()),
                "Expected the amended influence report with all-fixture and fallback-stratified tables")
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
        for filename in TABLES:
            (copy_to / filename).write_bytes(files[filename])
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
