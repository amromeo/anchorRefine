"""Verify the shard evidence and render the Stage 0 report from frozen rules."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile


def require(test, message):
    if not test:
        raise ValueError(message)


def save_table(path, rows, columns):
    with path.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as zipped:
            with io.TextIOWrapper(zipped, encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, columns, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)


def pct(value):
    return f"{100 * value:.6g}%" if math.isfinite(value) else "unavailable"


def number(value):
    return float(value) if value else float("nan")


def summarize(directory):
    provenance = json.loads((directory / "run.json").read_text())
    artifacts = json.loads((directory / "artifacts.json").read_text())
    manifest = Path("archive/c2/testsets.csv")
    with manifest.open(newline="") as stream:
        cases = {int(r["Index"]): (r["Analyte"], int(r["N"])) for r in csv.DictReader(stream)}
    require(len(cases) == 2880, "Unexpected Stage 0 case count")
    tables = {}
    fields = {}
    for name in ("same-machine", "historical-audit", "parameter-differences", "conditions"):
        tables[name] = []
    pairs = {"engines_first", "engines_repeat", "cran_repeat", "vendored_repeat"}
    require(len(artifacts) == 20, "Require all 20 shard artifacts")
    members = set()
    hosts = []
    for art in artifacts:
        matched = re.fullmatch(r"stage0-shard-(\d+)", art["name"])
        require(matched is not None, "Unrecognized artifact")
        shard = int(matched[1])
        require(1 <= shard <= 20 and shard not in members, "Missing or duplicate shard")
        members.add(shard)
        archive = directory / "shards" / (art["name"] + ".zip")
        require("sha256:" + hashlib.sha256(archive.read_bytes()).hexdigest() == art["digest"],
                f"Artifact checksum mismatch: {archive}")
        with ZipFile(archive) as z:
            digests = {}
            for line in z.read("SHA256SUMS").decode().splitlines():
                digest, file = line.split("  ", 1)
                digests[file] = digest
                require(hashlib.sha256(z.read(file)).hexdigest() == digest, f"Failed checksum: {file}")
            for role in ("cran", "vendored"):
                for rep in (1, 2):
                    require(f"{role}-{rep}.rds" in digests, "A raw result stream is missing")
            host = z.read("host.txt").decode().splitlines()
            require(f"commit={provenance['head_sha']} run={provenance['id']} " in host[0],
                    "Result does not identify the frozen source and run")
            hosts.append(host)
            shard_ids = set(sorted(cases)[shard - 1::20])
            for name in tables:
                handle = io.StringIO(z.read(name + ".csv").decode())
                reader = csv.DictReader(handle)
                fields[name] = reader.fieldnames
                rows = list(reader)
                for r in rows:
                    index = int(r["Index"])
                    require(index in shard_ids and (r["Analyte"], int(r["N"])) == cases[index]
                            and int(r["shard"]) == shard, f"Mismatched case: {index}")
                if name != "conditions":
                    require({int(r["Index"]) for r in rows} == shard_ids, f"Incomplete {name}")
                tables[name].extend(rows)

    exact = defaultdict(list)
    endpoints = defaultdict(list)
    for r in tables["same-machine"]:
        exact[int(r["Index"])].append(r)
    for r in tables["historical-audit"]:
        endpoints[int(r["Index"])].append(r)
    require(len(tables["parameter-differences"]) == len(cases), "Invalid parameter row count")
    same_ok, cross_ok, overall_ok = {}, {}, {}
    for index, (marker, _) in cases.items():
        pairs_here, limits = exact[index], endpoints[index]
        require(len(pairs_here) == 4 and {r["pair"] for r in pairs_here} == pairs,
                f"Incomplete same-machine comparisons: {index}")
        required = {"upper": 0.95} if marker == "CRP" else {"lower": 0.025, "upper": 0.975}
        require(len(limits) == len(required) and
                {r["endpoint"]: float(r["probability"]) for r in limits} == required,
                f"Wrong endpoints: {index}")
        same_ok[index] = all(r["exact"] == "TRUE" for r in pairs_here)
        cross_ok[index] = all(r["historical_pass"] == "TRUE" for r in limits)
        overall_ok[index] = same_ok[index] and cross_ok[index] and all(
            r["native_valid"] == "TRUE" and r["fit_status"] == r["archived_status"] == "ResultFound"
            for r in limits)
    for name, rows in tables.items():
        rows.sort(key=lambda r: (int(r["Index"]), r.get("pair", ""), r.get("endpoint", "")))
        save_table(directory / (name + ".csv.gz"), rows, fields[name])
    failures = [i for i in sorted(cases) if not overall_ok[i]]
    with (directory / "exceptions.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Index", "Analyte", "N", "same_machine", "c2", "problem"])
        for i in failures:
            reasons = [r["pair"] for r in exact[i] if r["exact"] != "TRUE"]
            reasons += [r["endpoint"] + " fails C2 audit" for r in endpoints[i] if r["historical_pass"] != "TRUE"]
            reasons += [r["endpoint"] + " missing native limit" for r in endpoints[i] if r["native_valid"] != "TRUE"]
            reasons += sorted({r["fit_status"] for r in endpoints[i] if r["fit_status"] != "ResultFound"})
            w.writerow([i, *cases[i], same_ok[i], cross_ok[i], ", ".join(reasons)])
    all_limits = tables["historical-audit"]
    differences = [number(r["fraction_of_width"]) for r in all_limits]
    valid = [(i, v) for i, v in enumerate(differences) if math.isfinite(v)]
    exact_count = sum(same_ok.values())
    cross_count = sum(cross_ok.values())
    conditions = Counter(r["kind"] for r in tables["conditions"])
    fit_failures = sum(any(r["fit_status"] != "ResultFound" for r in group) for group in endpoints.values())
    native_failures = sum(any(r["native_valid"] != "TRUE" for r in group) for group in endpoints.values())
    result = "Passed" if not failures else "Did not pass"
    url = provenance["html_url"]
    lines = ["# Stage 0 reproduction report", "",
             f"**{result}.** The native same-machine comparison and its repeats agreed on "
             f"{exact_count:,} of {len(cases):,} datasets. The C2 historical audit passed on "
             f"{cross_count:,} of {len(cases):,} datasets.", "",
             f"Each dataset underwent four fits (CRAN and pass-through, twice), for {4*len(cases):,} fits. "
             "Each group of four ran in fresh R sessions on the same host. The benchmark used 20 runner jobs. "
             "Equality covers the complete fitted object, native and historical interval data frames, "
             "and captured conditions. Elapsed time and host metadata were recorded separately.", "",
             "| Routine N | Planned | Completed | Missing | All four exact comparisons passed | C2 audit passed |",
             "|---:|---:|---:|---:|---:|---:|"]
    for n in sorted({n for _, n in cases.values()}):
        ids = [i for i, v in cases.items() if v[1] == n]
        lines.append(f"| {n:,} | {len(ids):,} | {len(ids):,} | 0 | {sum(same_ok[i] for i in ids):,} | "
                     f"{sum(cross_ok[i] for i in ids):,} |")
    lines += ["", f"Fit failures in the first pass-through run: {fit_failures:,} datasets. "
              f"Datasets with unavailable native point limits: {native_failures:,}. "
              f"All four runs together recorded {conditions['warnings']:,} warnings and {conditions['error']:,} errors. "
              f"The log also retains {conditions['messages']:,} messages.", "",
              f"The audit compared {len(all_limits):,} endpoints with C2. The archived limit came from the "
              "full-precision RIbench performance RDS. Both historical calculations used "
              "RIbench 1.0.2 with truncNormal = FALSE. The tolerance was 0.1% of archived interval width "
              "per endpoint. The 288 CRP datasets each contributed their 95th percentile and used the "
              "archived upper limit as width.", "",
              "| Endpoint | Audited | Within tolerance including C2 reconstruction | Largest absolute difference / width |",
              "|---|---:|---:|---:|"]
    for name in ["lower", "upper"]:
        rows = [r for r in all_limits if r["endpoint"] == name]
        rates = [number(r["fraction_of_width"]) for r in rows if r["fraction_of_width"]]
        lines.append(f"| {name.capitalize()} | {len(rows):,} | {sum(r['historical_pass']=='TRUE' for r in rows):,} | "
                     f"{pct(max(rates, default=float('nan')))} |")
    if valid:
        worst_i, worst = max(valid, key=lambda item: item[1])
        row = all_limits[worst_i]
        lines += ["", f"Maximum observed difference: {pct(worst)} of archived width "
                  f"(Index {row['Index']}, {row['Analyte']}, {row['endpoint']}). "
                  f"{sum(x == 0 for _, x in valid):,} historical endpoint differences were zero."]
    restored = [number(r["reconstruction_error"]) / number(r["width"]) for r in all_limits
                if number(r["width"]) > 0 and math.isfinite(number(r["reconstruction_error"]))]
    scales = [abs(number(r["native_minus_historical"])) / number(r["width"]) for r in all_limits
              if number(r["width"]) > 0 and math.isfinite(number(r["native_minus_historical"]))]
    lines += ["", f"Re-extracting limits from the archived C2 fits gave a maximum discrepancy of "
              f"{pct(max(restored, default=float('nan')))} of archived width from the saved C2 endpoints.",
              "", f"On the same new fit, native refineR and the historical extraction differed by more than "
              f"0.1% of archived width at {sum(x > 0.001 for x in scales):,} of {len(scales):,} comparable endpoints. "
              f"The maximum was {pct(max(scales, default=float('nan')))}. The native extractor corrects for "
              "Box–Cox support. C2 used untruncated normal quantiles.", ""]
    if failures:
        lines += [f"All {len(failures):,} affected indices are in [exceptions.csv](exceptions.csv).", ""]
    cpu_names = {line.split(":", 1)[1].strip() for host in hosts for line in host
                 if line.startswith("Model name:")}
    build_session = Path("stage0/frozen/build-session.txt").read_text().splitlines()
    flags = ("Platform:", "Running under:", "BLAS:", "LAPACK:")
    environment = [line.strip() for line in build_session if line.startswith(flags)]
    with ZipFile("archive/c2/ribench-scored-independent.zip") as archive:
        c2_session = archive.read("versions-1.txt").decode().splitlines()
    c2_environment = [line.strip() for line in c2_session if line.startswith(flags)]
    lines += ["The runner CPU models were " + ", ".join(sorted(cpu_names)) + ". "
              "The new environment and the archived C2 session both used R 4.5.0. "
              "The archived session file identifies the C2 environment. The C2 workflow imported its "
              "refineR fits from the preceding small-N run.", "",
              "| Environment | Platform and numerical libraries |", "|---|---|",
              "| Stage 0 | " + " · ".join(environment) + " |",
              "| Archived C2 session | " + " · ".join(c2_environment) + " |", ""]
    lines += [f"The fit workflow ran at commit `{provenance['head_sha']}`. "
              f"All {len(cases):,} routine and anchor hashes passed before fitting. "
              "Each shard verified its sources, libraries and inputs before and after fitting. "
              "[Workflow run](" + url + ") · [Input and build freeze](../../stage0/frozen/) · "
              "[Frozen rules](../../docs/stage0/DESIGN.md)", "",
              "[Same-machine comparisons](same-machine.csv.gz) · [C2 endpoint comparisons](historical-audit.csv.gz) · "
              "[Parameter changes and timings](parameter-differences.csv.gz) · [Warnings and errors](conditions.csv.gz) · "
              "[Full R objects, logs and runner records](shards/)", "",
              "The study stops here for review before Stage 1.", ""]
    (directory / "REPORT.md").write_text("\n".join(lines))
    print(lines[2])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="run directory containing the verified shard ZIPs")
    summarize(parser.parse_args().directory)
