#!/usr/bin/env python3
"""English: Read-only case preflight for paths, evidence links, and required logs.

中文：只读检查案件路径、证据关联与必要日志；不跟随重解析点，也不以结构完整取代真正生产来源验证。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from typing import Any, Iterable, Sequence


STAGE_REQUIREMENTS = {
    "research": ["case.json", "artifacts/original", "work", "evidence", "output"],
    "operational": [
        "case.json",
        "artifacts/original",
        "work/product_profile.json",
        "evidence/evidence_register.csv",
        "candidates",
        "claims.jsonl",
        "logs/execution_log.csv",
        "output",
    ],
    "confirmed": [
        "case.json",
        "artifacts/original",
        "evidence/evidence_register.csv",
        "candidates",
        "claims.jsonl",
        "logs/model_usage_log.csv",
        "output",
    ],
}

STAGE_ALTERNATIVES = {
    "operational": [("commands.log", "logs/commands.log")],
}


def is_reparse_point(path: Path) -> bool:
    metadata = path.lstat()
    attributes = int(getattr(metadata, "st_file_attributes", 0))
    reparse_flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    return path.is_symlink() or bool(attributes & reparse_flag)


def scan_reparse_points(root: Path) -> list[str]:
    found: list[str] = []
    stack = [root]
    while stack:
        current = stack.pop()
        with os.scandir(current) as entries:
            ordered = sorted(entries, key=lambda item: item.name.casefold())
        for entry in ordered:
            path = Path(entry.path)
            if is_reparse_point(path):
                found.append(path.relative_to(root).as_posix())
            elif entry.is_dir(follow_symlinks=False):
                stack.append(path)
    return sorted(found)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8-sig") as stream:
        return json.load(stream)


def read_jsonl(path: Path) -> list[Any]:
    records: list[Any] = []
    with path.open(encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{line_number}: {exc}") from exc
    return records


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _collect_evidence_ids(candidate: Any) -> Iterable[str]:
    if not isinstance(candidate, dict):
        return []
    values: list[str] = []
    for evidence in candidate.get("evidence", []):
        if isinstance(evidence, dict) and evidence.get("evidence_id"):
            values.append(str(evidence["evidence_id"]))
    return values


def inspect_case(root: Path, stage: str) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    metrics: dict[str, Any] = {}

    if not root.is_dir():
        return {
            "status": "FAIL",
            "case_root": str(root),
            "stage": stage,
            "errors": ["case root does not exist or is not a directory"],
            "warnings": [],
            "metrics": {},
        }

    for relative in STAGE_REQUIREMENTS[stage]:
        if not (root / relative).exists():
            errors.append(f"missing required path: {relative}")

    for alternatives in STAGE_ALTERNATIVES.get(stage, []):
        present = [relative for relative in alternatives if (root / relative).is_file()]
        if not present:
            errors.append(
                "missing required command log; expected one of: " + ", ".join(alternatives)
            )
        elif present[0] != alternatives[0]:
            warnings.append(
                f"legacy command log location in use: {present[0]}; canonical path is {alternatives[0]}"
            )

    try:
        reparse_points = scan_reparse_points(root)
    except OSError as exc:
        reparse_points = []
        warnings.append(f"could not complete reparse-point scan: {exc}")
    metrics["reparse_points"] = reparse_points
    if reparse_points:
        warnings.append(
            "reparse points detected; canonical migration must not follow them: "
            + ", ".join(reparse_points)
        )

    case_path = root / "case.json"
    if case_path.is_file():
        try:
            case = read_json(case_path)
            if not isinstance(case, dict):
                errors.append("case.json must contain an object")
            else:
                metrics["case_id"] = case.get("case_id") or case.get("name")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid case.json: {exc}")

    originals = root / "artifacts" / "original"
    original_files = sorted(path for path in originals.rglob("*") if path.is_file()) if originals.is_dir() else []
    metrics["original_count"] = len(original_files)
    metrics["original_sha256"] = {
        path.relative_to(root).as_posix(): sha256_file(path) for path in original_files
    }
    if originals.is_dir() and not original_files:
        warnings.append("artifacts/original exists but contains no files")

    candidates_dir = root / "candidates"
    candidate_paths = sorted(candidates_dir.glob("*.json")) if candidates_dir.is_dir() else []
    metrics["candidate_count"] = len(candidate_paths)
    evidence_ids: list[str] = []
    candidate_ids: list[str] = []
    for path in candidate_paths:
        try:
            candidate = read_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid candidate {path.name}: {exc}")
            continue
        if not isinstance(candidate, dict):
            errors.append(f"candidate {path.name} must contain an object")
            continue
        candidate_id = str(candidate.get("candidate_id", "")).strip()
        if not candidate_id:
            errors.append(f"candidate {path.name} lacks candidate_id")
        else:
            candidate_ids.append(candidate_id)
        evidence_ids.extend(_collect_evidence_ids(candidate))

    duplicate_candidates = sorted({value for value in candidate_ids if candidate_ids.count(value) > 1})
    duplicate_evidence = sorted({value for value in evidence_ids if evidence_ids.count(value) > 1})
    if duplicate_candidates:
        errors.append("duplicate candidate_id: " + ", ".join(duplicate_candidates))
    if duplicate_evidence:
        errors.append("duplicate evidence_id: " + ", ".join(duplicate_evidence))
    metrics["candidate_evidence_count"] = len(evidence_ids)

    ledger_path = root / "evidence" / "evidence_register.csv"
    if ledger_path.is_file():
        try:
            fields, rows = read_csv(ledger_path)
            metrics["ledger_row_count"] = len(rows)
            ledger_ids = [str(row.get("evidence_id", "")).strip() for row in rows]
            if "evidence_id" not in fields:
                errors.append("evidence ledger lacks evidence_id column")
            missing = sorted(set(evidence_ids) - set(ledger_ids))
            extra = sorted(set(ledger_ids) - set(evidence_ids) - {""})
            if missing:
                errors.append("candidate evidence absent from ledger: " + ", ".join(missing))
            if extra:
                warnings.append("ledger evidence absent from candidate JSON: " + ", ".join(extra))
        except (OSError, csv.Error) as exc:
            errors.append(f"invalid evidence ledger: {exc}")

    claims_path = root / "claims.jsonl"
    if claims_path.is_file():
        try:
            claims = read_jsonl(claims_path)
            metrics["claim_count"] = len(claims)
            claim_ids = [
                str(item.get("claim_id", "")).strip()
                for item in claims
                if isinstance(item, dict)
            ]
            duplicate_claims = sorted({value for value in claim_ids if value and claim_ids.count(value) > 1})
            if duplicate_claims:
                errors.append("duplicate claim_id: " + ", ".join(duplicate_claims))
            known_evidence = set(evidence_ids)
            for index, claim in enumerate(claims, start=1):
                if not isinstance(claim, dict):
                    errors.append(f"claim record {index} must be an object")
                    continue
                refs: list[str] = []
                for key in ("evidence_ids", "source_ids"):
                    value = claim.get(key, [])
                    if isinstance(value, list):
                        refs.extend(str(item) for item in value)
                unknown = sorted(set(refs) - known_evidence)
                if unknown:
                    errors.append(
                        f"claim {claim.get('claim_id', index)} references unknown evidence: "
                        + ", ".join(unknown)
                    )
        except (OSError, ValueError) as exc:
            errors.append(f"invalid claims.jsonl: {exc}")

    if stage == "confirmed":
        if not candidate_paths:
            errors.append("confirmed preflight requires at least one candidate")
        if not evidence_ids:
            errors.append("confirmed preflight requires candidate evidence")
        if not claims_path.is_file():
            errors.append("confirmed preflight requires claims.jsonl")
        warnings.append(
            "preflight never confirms a factory; run the core confirmed audit and close project hard gates"
        )

    return {
        "status": "PASS" if not errors else "FAIL",
        "case_root": str(root),
        "stage": stage,
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only factorytrace case preflight.")
    parser.add_argument("--case-root", type=Path, required=False)
    parser.add_argument(
        "--stage", choices=sorted(STAGE_REQUIREMENTS), default="research"
    )
    parser.add_argument(
        "--self-test", action="store_true", help="Run deterministic in-memory checks."
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        assert set(STAGE_REQUIREMENTS) == {"research", "operational", "confirmed"}
        assert hashlib.sha256(b"factorytrace").hexdigest().startswith("e1e1")
        print(json.dumps({"status": "PASS", "self_test": True}, ensure_ascii=False))
        return 0
    if args.case_root is None:
        print("--case-root is required unless --self-test is used", file=sys.stderr)
        return 2
    result = inspect_case(args.case_root, args.stage)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
