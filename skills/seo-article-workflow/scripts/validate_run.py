#!/usr/bin/env python3
"""Read-only checks of declared article artifacts and research records; no SEO score."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

QUERY_STATES = {"planned", "running", "completed", "partial", "failed", "skipped", "reused"}
METRIC_STATES = {"not_queried", "failed", "empty", "available"}


def validate(run_path):
    run_path = Path(run_path).resolve()
    base = run_path.parent
    errors, warnings = [], []

    def load(path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"Cannot read JSON {path.name}: {exc}")
            return None

    def local(value):
        if not isinstance(value, str) or not value:
            errors.append("Artifact reference must be a non-empty relative path")
            return None
        path = (base / value).resolve()
        if Path(value).is_absolute() or not path.is_relative_to(base):
            errors.append(f"Artifact outside task directory: {value}")
            return None
        if not path.is_file():
            errors.append(f"Missing artifact: {value}")
            return None
        return path

    run = load(run_path)
    if not isinstance(run, dict):
        return {"ok": False, "errors": errors or ["run.json must be an object"], "warnings": warnings}

    artifacts = run.get("artifacts", [])
    if not isinstance(artifacts, list):
        errors.append("artifacts must be an array")
        artifacts = []
    recorded = {}
    for entry in artifacts:
        if not isinstance(entry, dict):
            errors.append("Invalid artifact record")
            continue
        path = local(entry.get("path"))
        if path:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if entry.get("sha256") != digest:
                errors.append(f"Artifact hash mismatch: {entry.get('path')}")
            if entry["path"] in recorded:
                errors.append(f"Duplicate artifact record: {entry['path']}")
            recorded[entry["path"]] = digest

    article_ref = run.get("article")
    if article_ref:
        path = local(article_ref)
        if article_ref not in recorded:
            errors.append("Current article lacks a versioned artifact record")
        if run.get("status") == "approved" and run.get("article_accepted") is not True:
            errors.append("Article marked approved without declared user acceptance")
        if path:
            text = path.read_text(encoding="utf-8")
            if len(re.findall(r"^# [^\n]+", text, re.M)) != 1:
                errors.append("Article must contain exactly one H1")
            pairs = re.findall(r"\[[^\]]*\]\((https?://[^\s)]+)\)|<(https?://[^\s>]+)>", text)
            actual = Counter(a or b for a, b in pairs)
            expected = Counter()
            for link in run.get("link_plan", []):
                if not isinstance(link, dict) or not isinstance(link.get("occurrences"), int) or isinstance(link.get("occurrences"), bool) or link["occurrences"] < 0 or not isinstance(link.get("url"), str):
                    errors.append("Link plan requires URL and non-negative occurrence count")
                    continue
                expected[link["url"]] += link["occurrences"]
            for url in set(actual) | set(expected):
                if actual[url] != expected[url]:
                    errors.append(f"Link occurrence mismatch: {url} (actual {actual[url]}, planned {expected[url]})")
            for url in run.get("forbidden_urls", []):
                if actual[url]:
                    errors.append(f"Forbidden public link: {url}")

    if run.get("queries_file"):
        path = local(run["queries_file"])
        queries = load(path) if path else None
        if queries is not None and not isinstance(queries, list):
            errors.append("Queries must be an array")
            queries = []
        for q in queries or []:
            if not isinstance(q, dict):
                errors.append("Invalid query record")
                continue
            qid = q.get("id", "unnamed query")
            if q.get("status") not in QUERY_STATES:
                errors.append(f"{qid}: invalid query state")
            for key, metric in q.get("metrics", {}).items():
                if not isinstance(metric, dict):
                    errors.append(f"{qid}/{key}: metric must be an object")
                    continue
                status, value = metric.get("status"), metric.get("value")
                if status not in METRIC_STATES:
                    errors.append(f"{qid}/{key}: invalid metric state")
                elif status != "available" and value is not None:
                    errors.append(f"{qid}/{key}: unknown metric must be null")
                elif status == "available" and (not isinstance(value, (int, float)) or isinstance(value, bool)):
                    errors.append(f"{qid}/{key}: available numeric metric requires a number")
            if q.get("status") == "reused":
                reuse = q.get("reuse") or {}
                current = q.get("request") or {}
                original = reuse.get("original_request") or {}
                for key in ["query", "engine", "location", "language", "device", "metric_period"]:
                    if current.get(key) != original.get(key):
                        errors.append(f"{qid}: incompatible reuse condition {key}; label partial/background use instead")
                if not reuse.get("suitability_reason"):
                    errors.append(f"{qid}: reused data needs a suitability reason")
            if q.get("status") in {"completed", "partial", "reused"} and not (q.get("raw_paths") or q.get("raw_reference")):
                warnings.append(f"{qid}: no raw response or snapshot reference recorded")
            for raw in q.get("raw_paths", []):
                local(raw)

    if run.get("evidence_file"):
        path = local(run["evidence_file"])
        evidence = load(path) if path else None
        if evidence is not None and not isinstance(evidence, dict):
            errors.append("Evidence must be an object")
            evidence = {}
        source_ids = set()
        for source in (evidence or {}).get("sources", []):
            sid = source.get("id")
            if not sid or sid in source_ids:
                errors.append("Missing or duplicate source ID")
            source_ids.add(sid)
            scope = source.get("read_scope", {})
            if source.get("full_text_verified") is True and scope.get("kind") != "full_text":
                errors.append(f"{sid}: partial/abstract reading cannot claim full-text verification")
            if source.get("public_role") and source.get("verification_status") in {None, "not_read", "unreachable"}:
                errors.append(f"{sid}: unread source assigned a public role")
        for claim in (evidence or {}).get("claims", []):
            for sid in claim.get("source_ids", []):
                if sid not in source_ids:
                    errors.append(f"{claim.get('id')}: unknown source {sid}")

    return {"ok": not errors, "scope": "declared-record and file consistency only", "errors": errors, "warnings": warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    result = validate(args.run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
