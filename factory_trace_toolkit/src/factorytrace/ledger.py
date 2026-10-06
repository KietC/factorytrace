"""English: Normalize candidate claims into a reviewable evidence ledger.

中文：将候选主张整理为可审查的证据台账；引用必须保留证据标识，汇总行不是新增独立来源。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .common import load_json, write_csv


FIELDS = [
    "case_id",
    "claim_id",
    "evidence_id",
    "candidate_id",
    "role",
    "component",
    "legal_entity",
    "physical_site",
    "process",
    "claim_text",
    "source_class",
    "source_url",
    "local_path",
    "issuer",
    "published_at",
    "captured_at_utc",
    "fact_or_inference",
    "stance",
    "strength",
    "independence_group",
    "entity_bind",
    "site_bind",
    "sku_bind",
    "exact_sku_or_revision",
    "batch_id",
    "batch_or_revision",
    "quoted_text",
    "ocr_confidence",
    "sha256",
    "archive_path",
    "conflict_group",
    "review_status",
    "reviewer",
    "notes",
]


def build_ledger_rows(case_root: Path) -> list[dict[str, Any]]:
    root = case_root.resolve(strict=True)
    case = load_json(root / "case.json")
    rows = []
    seen: set[str] = set()
    for candidate_path in sorted((root / "candidates").glob("*.json")):
        candidate = load_json(candidate_path)
        candidate_id = str(candidate.get("candidate_id", ""))
        for item in candidate.get("evidence", []):
            evidence_id = str(item.get("evidence_id", "")).strip()
            if not evidence_id:
                raise ValueError(f"{candidate_path.name}: evidence_id is required")
            if evidence_id in seen:
                raise ValueError(f"duplicate evidence_id: {evidence_id}")
            seen.add(evidence_id)
            rows.append(
                {
                    "case_id": case.get("case_id", ""),
                    "claim_id": item.get("claim_id", ""),
                    "evidence_id": evidence_id,
                    "candidate_id": candidate_id,
                    "role": item.get("role", ""),
                    "component": item.get("component", ""),
                    "legal_entity": item.get("legal_entity", ""),
                    "physical_site": item.get("physical_site", ""),
                    "process": item.get("process", ""),
                    "claim_text": item.get("observed_fact", ""),
                    "source_class": item.get("source_class", ""),
                    "source_url": item.get("source_url", ""),
                    "local_path": item.get("local_path", ""),
                    "issuer": item.get("issuer", ""),
                    "published_at": item.get("published_at_utc", ""),
                    "captured_at_utc": item.get("captured_at_utc", ""),
                    "fact_or_inference": (
                        "inference" if item.get("inference") else "fact"
                    ),
                    "stance": item.get("stance", ""),
                    "strength": item.get("strength", ""),
                    "independence_group": item.get("independence_group", ""),
                    "entity_bind": item.get("entity_bind", ""),
                    "site_bind": item.get("site_bind", ""),
                    "sku_bind": item.get("sku_bind", ""),
                    "exact_sku_or_revision": item.get(
                        "exact_sku_or_revision", ""
                    ),
                    "batch_id": item.get("batch_id", ""),
                    "batch_or_revision": (
                        item.get("batch_id")
                        or item.get("exact_sku_or_revision", "")
                    ),
                    "quoted_text": item.get("quoted_text", ""),
                    "ocr_confidence": item.get("ocr_confidence", ""),
                    "sha256": item.get("sha256", ""),
                    "archive_path": item.get("archive_path", ""),
                    "conflict_group": item.get("conflict_group", ""),
                    "review_status": item.get("review_status", ""),
                    "reviewer": item.get("reviewer", ""),
                    "notes": item.get("limitations", ""),
                }
            )
    rows.sort(key=lambda row: str(row["evidence_id"]))
    return rows


def sync_ledger(case_root: Path, output: Path | None = None) -> Path:
    root = case_root.resolve(strict=True)
    destination = output or (root / "evidence" / "evidence_register.csv")
    write_csv(destination, FIELDS, build_ledger_rows(root))
    return destination


def run(args: object) -> int:
    rows = build_ledger_rows(args.case_root)
    output = args.output or (
        args.case_root / "evidence" / "evidence_register.csv"
    )
    write_csv(output, FIELDS, rows)
    print(
        json.dumps(
            {"evidence_rows": len(rows), "output": str(output)},
            ensure_ascii=False,
        )
    )
    return 0
