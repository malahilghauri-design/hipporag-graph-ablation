#!/usr/bin/env python3
"""Standalone synthetic ID, schema and metadata checker.

Author: Malahil Ghauri
Licence: MIT (see repository LICENSE)

Scope
-----
This checker validates *synthetic* per-query result files only. It does
not read the historical result files in ``results/``, does not change the
existing scripts, and does not run retrieval, indexing or a model.

It implements the decisions agreed with Ryan Gomez in the
"Contract v0.3 and next milestone" thread:

* 18 Oct 2026 -- strict ID-set equality (no intersection mode); a
  recomputed-recall mismatch blocks a validated report and must name the
  offending ID/k; a small manifest sits next to the two saved files and
  records their hashes, declared dataset/metric/scale/k and the exact
  analysis revision. A declaration is not independent proof of provenance.
* 28 Oct / 9 Nov 2026 -- IDs are sorted before pairing and before any
  resampling, so order alone never changes the result; improved /
  worsened / tied are mutually exclusive under one tolerance, 1e-9.
* 21 Nov 2026 -- the task is the standalone synthetic ID, schema and
  metadata checker, with reordered-ID and mismatched-ID fixtures, in a
  separate review folder, using the field names ``query_id``, ``score``,
  ``dataset_id``, ``metric``, ``scale`` and ``k``. Total cap: two hours.

Synthetic file format
--------------------
Each file is a JSON list of records, one record per query, all at one k::

    {"query_id": "syn-q01", "dataset_id": "musique-dev-synthetic",
     "metric": "recall", "scale": "per-query", "k": 10, "score": 1.0}

``score`` is the per-query recall at that k (0 or 1 for a single gold
passage, in general a number in [0, 1]). The two files being compared
must agree on ``dataset_id``, ``metric``, ``scale`` and ``k``.

Manifest format (``manifest.json``, next to the two files)::

    {"dataset_id": "musique-dev-synthetic", "metric": "recall",
     "scale": "per-query", "k": 10, "revision": "v0.3",
     "files": {"baseline.json": {"sha256": "...", "n": 5,
                                 "mean_score": 0.6},
               "variant.json":  {"sha256": "...", "n": 5,
                                 "mean_score": 0.4}}}

Usage
-----
    python check_synthetic.py baseline.json variant.json manifest.json \
        --report report.json

Exit 0: VALIDATED -- every check passed.
Exit 2: BLOCKED -- a diagnostic report was still written (see ``--report``);
        the errors name the offending file, field and, where applicable,
        query_id. Do not treat a diagnostic report as a validated result.
Exit 1: the inputs could not be read at all (no report is written).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

TOLERANCE = 1e-9
ALLOWED_K = (2, 5, 10)
METRIC = "recall"
SCALE = "per-query"
REQUIRED_FIELDS = ("query_id", "score", "dataset_id", "metric", "scale", "k")


class CheckError:
    """One blocking finding; ``query_id`` is None for file-level findings."""

    def __init__(self, code: str, message: str, file: str | None = None,
                 query_id: str | None = None, field: str | None = None):
        self.code = code
        self.message = message
        self.file = file
        self.query_id = query_id
        self.field = field

    def as_dict(self) -> dict:
        return {"code": self.code, "file": self.file,
                "query_id": self.query_id, "field": self.field,
                "message": self.message}


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_file(path: Path, errors: list[CheckError]) -> dict[str, dict] | None:
    """Validate one synthetic file. Returns {query_id: record} or None."""
    name = path.name
    try:
        data = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(CheckError("unreadable", f"cannot read {name}: {exc}",
                                 file=name))
        return None
    if not isinstance(data, list) or not data:
        errors.append(CheckError("schema", "file must be a non-empty JSON list",
                                 file=name))
        return None

    records: dict[str, dict] = {}
    seen_meta: dict[str, object] = {}
    for index, record in enumerate(data):
        where = f"record {index}"
        if not isinstance(record, dict):
            errors.append(CheckError("schema", f"{where} is not an object",
                                     file=name))
            continue
        for field in REQUIRED_FIELDS:
            if field not in record:
                errors.append(CheckError("schema", f"{where} is missing {field}",
                                         file=name, field=field))
        for field in record:
            if field not in REQUIRED_FIELDS:
                errors.append(CheckError("schema",
                                         f"{where} has unknown field {field}",
                                         file=name, field=field))
        if any(field not in record for field in REQUIRED_FIELDS):
            continue

        query_id = record["query_id"]
        if not isinstance(query_id, str) or not query_id.strip():
            errors.append(CheckError("schema", f"{where}: query_id must be a "
                                     "non-empty string", file=name,
                                     field="query_id"))
            continue
        if query_id in records:
            errors.append(CheckError("duplicate_id",
                                     f"duplicate query_id {query_id}",
                                     file=name, query_id=query_id,
                                     field="query_id"))
            continue

        # Metadata must be consistent within a file.
        for field in ("dataset_id", "metric", "scale", "k"):
            if field in seen_meta and record[field] != seen_meta[field]:
                errors.append(CheckError(
                    "metadata_mismatch",
                    f"{where}: {field} {record[field]!r} differs from "
                    f"{seen_meta[field]!r} in the same file",
                    file=name, query_id=query_id, field=field))
        for field in ("dataset_id", "metric", "scale", "k"):
            seen_meta.setdefault(field, record[field])

        if not isinstance(record["dataset_id"], str) or not record["dataset_id"].strip():
            errors.append(CheckError("schema", f"{where}: dataset_id must be a "
                                     "non-empty string", file=name,
                                     query_id=query_id, field="dataset_id"))
        if record["metric"] != METRIC:
            errors.append(CheckError("schema", f"{where}: metric must be "
                                     f"{METRIC!r}", file=name,
                                     query_id=query_id, field="metric"))
        if record["scale"] != SCALE:
            errors.append(CheckError("schema", f"{where}: scale must be "
                                     f"{SCALE!r}", file=name,
                                     query_id=query_id, field="scale"))
        if not isinstance(record["k"], int) or isinstance(record["k"], bool) \
                or record["k"] not in ALLOWED_K:
            errors.append(CheckError("schema", f"{where}: k must be one of "
                                     f"{list(ALLOWED_K)}", file=name,
                                     query_id=query_id, field="k"))
        score = record["score"]
        if not _is_number(score) or score < 0 or score > 1:
            errors.append(CheckError("schema", f"{where}: score must be a "
                                     "number in [0, 1]", file=name,
                                     query_id=query_id, field="score"))
        records[query_id] = record
    return records


def check_manifest(manifest_path: Path, files: dict[str, Path],
                   means: dict[str, float | None],
                   counts: dict[str, int | None],
                   meta: dict[str, object | None],
                   errors: list[CheckError]) -> str | None:
    """Verify the manifest against the files it describes. Returns revision."""
    try:
        manifest = load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(CheckError("unreadable",
                                 f"cannot read {manifest_path.name}: {exc}",
                                 file=manifest_path.name))
        return None
    if not isinstance(manifest, dict):
        errors.append(CheckError("schema", "manifest must be a JSON object",
                                 file=manifest_path.name))
        return None
    for field in ("dataset_id", "metric", "scale", "k", "revision", "files"):
        if field not in manifest:
            errors.append(CheckError("schema", f"manifest is missing {field}",
                                     file=manifest_path.name, field=field))
    if any(field not in manifest
           for field in ("dataset_id", "metric", "scale", "k", "revision", "files")):
        return None
    if not isinstance(manifest["revision"], str) or not manifest["revision"].strip():
        errors.append(CheckError("schema", "manifest revision must be a "
                                 "non-empty string", file=manifest_path.name,
                                 field="revision"))
    for field in ("dataset_id", "metric", "scale", "k"):
        if meta[field] is not None and manifest[field] != meta[field]:
            errors.append(CheckError(
                "manifest_metadata_mismatch",
                f"manifest {field} {manifest[field]!r} differs from the "
                f"files' {meta[field]!r}", file=manifest_path.name,
                field=field))
    declared = manifest["files"]
    if not isinstance(declared, dict):
        errors.append(CheckError("schema", "manifest files must be an object",
                                 file=manifest_path.name, field="files"))
        return manifest["revision"] if isinstance(manifest["revision"], str) else None
    for label, path in files.items():
        entry = declared.get(path.name)
        if entry is None:
            errors.append(CheckError("manifest_missing_file",
                                     f"manifest has no entry for {path.name}",
                                     file=manifest_path.name, field="files"))
            continue
        if not isinstance(entry, dict):
            errors.append(CheckError("schema", f"manifest entry for {path.name} "
                                     "must be an object",
                                     file=manifest_path.name, field="files"))
            continue
        if entry.get("sha256") != sha256_file(path):
            errors.append(CheckError("manifest_hash_mismatch",
                                     f"sha256 of {path.name} does not match "
                                     "the manifest", file=path.name,
                                     field="sha256"))
        if entry.get("n") != counts[label]:
            errors.append(CheckError("manifest_mean_mismatch",
                                     f"manifest n for {path.name} is "
                                     f"{entry.get('n')!r}, recomputed "
                                     f"{counts[label]!r}", file=path.name,
                                     field="n"))
        declared_mean = entry.get("mean_score")
        if not _is_number(declared_mean) or means[label] is None \
                or abs(declared_mean - means[label]) > TOLERANCE:
            errors.append(CheckError(
                "manifest_mean_mismatch",
                f"manifest mean_score for {path.name} is "
                f"{declared_mean!r}, recomputed {means[label]!r}",
                file=path.name, field="mean_score"))
    return manifest["revision"] if isinstance(manifest["revision"], str) else None


def check(baseline_path: Path, variant_path: Path,
          manifest_path: Path) -> tuple[dict, int]:
    """Run every check. Returns (report, exit_code)."""
    errors: list[CheckError] = []
    files = {"baseline": baseline_path, "variant": variant_path}
    parsed = {label: validate_file(path, errors)
              for label, path in files.items()}
    if any(records is None for records in parsed.values()):
        return {"status": "diagnostic",
                "errors": [e.as_dict() for e in errors]}, 1

    baseline, variant = parsed["baseline"], parsed["variant"]
    means = {label: (sum(r["score"] for r in records.values()) / len(records)
                     if records else None)
             for label, records in parsed.items()}
    counts = {label: len(records) for label, records in parsed.items()}

    # Metadata shared by both files, when each file is internally consistent.
    meta: dict[str, object | None] = {}
    for field in ("dataset_id", "metric", "scale", "k"):
        values = {records[next(iter(records))][field] for records in parsed.values()
                  if records}
        meta[field] = values.pop() if len(values) == 1 else None
        if len(values) > 1:
            errors.append(CheckError(
                "metadata_mismatch",
                f"{field} differs between baseline and variant",
                field=field))

    revision = check_manifest(manifest_path, files, means, counts, meta, errors)

    # Strict ID-set equality. Sorting first means a reordered file passes;
    # a missing or extra ID is reported by name and blocks validation.
    baseline_ids = sorted(baseline)
    variant_ids = sorted(variant)
    for query_id in sorted(set(baseline_ids) - set(variant_ids)):
        errors.append(CheckError("id_mismatch",
                                 f"query_id {query_id} is in baseline but "
                                 "not in variant", file=variant_path.name,
                                 query_id=query_id, field="query_id"))
    for query_id in sorted(set(variant_ids) - set(baseline_ids)):
        errors.append(CheckError("id_mismatch",
                                 f"query_id {query_id} is in variant but "
                                 "not in baseline", file=baseline_path.name,
                                 query_id=query_id, field="query_id"))

    mean_diff = None
    improved = worsened = tied = 0
    paired_n = None
    if baseline_ids == variant_ids:
        paired_n = len(baseline_ids)
        diffs = []
        for query_id in baseline_ids:  # sorted: pairing is order-independent
            diff = baseline[query_id]["score"] - variant[query_id]["score"]
            diffs.append(diff)
            if diff > TOLERANCE:
                improved += 1
            elif diff < -TOLERANCE:
                worsened += 1
            else:
                tied += 1
        # Sum the per-query diffs, rather than subtracting the two means,
        # so the reported diff is the mean of what was actually paired.
        mean_diff = sum(diffs) / paired_n
        # improved / worsened / tied are mutually exclusive by construction;
        # assert the invariant rather than trusting the counts.
        assert improved + worsened + tied == paired_n

    status = "validated" if not errors else "diagnostic"
    report = {"status": status, "revision": revision,
              "dataset_id": meta["dataset_id"], "metric": meta["metric"],
              "scale": meta["scale"], "k": meta["k"],
              "n": paired_n,
              "baseline_mean": means["baseline"],
              "variant_mean": means["variant"], "mean_diff": mean_diff,
              "improved": improved, "worsened": worsened, "tied": tied,
              "errors": [e.as_dict() for e in errors]}
    return report, 0 if status == "validated" else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a pair of synthetic per-query result files "
                    "against their manifest.")
    parser.add_argument("baseline", type=Path)
    parser.add_argument("variant", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path, required=True,
                        help="where to write the validated/diagnostic report")
    args = parser.parse_args(argv)
    report, code = check(args.baseline, args.variant, args.manifest)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n",
                           encoding="utf-8")
    if report["status"] == "validated":
        print(f"VALIDATED: n={report['n']} k={report['k']} "
              f"baseline={report['baseline_mean']:.4f} "
              f"variant={report['variant_mean']:.4f} "
              f"diff={report['mean_diff']:+.4f} "
              f"improved={report['improved']} worsened={report['worsened']} "
              f"tied={report['tied']}")
    else:
        print(f"BLOCKED: {len(report['errors'])} error(s); "
              f"diagnostic report written to {args.report}")
        for error in report["errors"]:
            print(f"  - [{error['code']}] {error['file'] or ''} "
                  f"{error['query_id'] or ''} {error['message']}")
    return code


if __name__ == "__main__":
    sys.exit(main())
