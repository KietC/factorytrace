"""English: Create case directories and add missing templates without replacing user evidence.

中文：创建案件目录并补齐模板，不覆盖已有证据；历史备份名保留兼容，初始化不是数据迁移。
"""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from ._resources import resource_directory
from .common import (
    atomic_write_json,
    atomic_write_text,
    safe_slug,
    utc_now,
    write_csv,
)
from .environment import build_environment_report


CASE_DIRS = (
    "artifacts/original",
    "work/variants",
    "work/queries",
    "evidence/web",
    "evidence/factory",
    "evidence/certificates",
    "evidence/communications",
    "evidence/government",
    "evidence/social",
    "evidence/trade",
    "evidence/structured",
    "candidates",
    "output",
    "logs",
)

TEMPLATE_COPIES = {
    "product_profile.example.json": "work/product_profile.json",
    "crop_plan.example.json": "work/crop_plan.json",
    "candidate.example.json": "candidates/CAND-001.json",
    "evidence_register.csv": "evidence/evidence_register.csv",
    "url_queue.csv": "evidence/url_queue.csv",
    "contacts.csv": "evidence/contacts.csv",
    "search_log.csv": "output/search_log.csv",
    "model_usage_log.csv": "logs/model_usage_log.csv",
    "execution_log.csv": "logs/execution_log.csv",
    "research_round.example.json": "work/research_round.json",
    "materials_plan.example.json": "work/materials_plan.json",
    "access_receipt.example.json": "work/access_receipt.example.json",
    "parties.example.json": "evidence/structured/parties.json",
    "sites.example.json": "evidence/structured/sites.json",
    "cert_records.example.json": "evidence/structured/cert_records.json",
    "supply_events.example.json": "evidence/structured/supply_events.json",
    "social_records.example.json": "evidence/structured/social_records.json",
}


def _upgrade_csv_header(path: Path, template: Path) -> None:
    with template.open(encoding="utf-8-sig", newline="") as stream:
        template_fields = list(csv.DictReader(stream).fieldnames or [])
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        old_fields = list(reader.fieldnames or [])
        rows = list(reader)
    if all(field in old_fields for field in template_fields):
        return
    # Retain the historical backup name because external case automation and
    # rollback checks already depend on it.
    # 中文：外部案件自动化与回滚检查依赖历史备份名，不能仅为整洁而随意改名。
    backup = path.with_suffix(path.suffix + ".pre-1.1.bak")
    if not backup.exists():
        shutil.copy2(path, backup)
    fields = template_fields + [
        field for field in old_fields if field not in template_fields
    ]
    write_csv(path, fields, rows)


def ensure_v2_layout(case_root: Path) -> Path:
    """Add missing v2 directories/templates without replacing existing case data.

    中文：只补充缺失目录或模板，已有案件记录保持不变；升级模板不等于重置案件。
    """
    for relative in CASE_DIRS:
        (case_root / relative).mkdir(parents=True, exist_ok=True)
    template_root = resource_directory("templates")
    for source_name, destination_name in TEMPLATE_COPIES.items():
        destination = case_root / destination_name
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(template_root / source_name, destination)
    receipt_log = case_root / "evidence" / "access_receipts.jsonl"
    if not receipt_log.exists():
        atomic_write_text(receipt_log, "")
    return template_root


def create_case(
    name: str,
    root: Path,
    *,
    objective: str = "Trace the actual manufacturing entity, site, process, and exact SKU.",
    time_zone: str = "UTC",
    resume: bool = False,
) -> Path:
    root = root.resolve()
    case_root = root / safe_slug(name)
    if case_root.exists() and any(case_root.iterdir()) and not resume:
        raise FileExistsError(
            f"case directory is not empty: {case_root}; use --resume to keep it"
    )
    case_root.mkdir(parents=True, exist_ok=True)
    template_root = ensure_v2_layout(case_root)
    if resume:
        _upgrade_csv_header(
            case_root / "output" / "search_log.csv",
            template_root / "search_log.csv",
        )

    case_path = case_root / "case.json"
    if not case_path.exists():
        atomic_write_json(
            case_path,
            {
                "schema": 2,
                "schema_version": 2,
                "case_id": safe_slug(name),
                "name": name,
                "objective": objective,
                "created_at_utc": utc_now(),
                "time_zone": time_zone,
                "status": "open",
                "assessment_policy": {
                    "single_probability_forbidden": True,
                    "mainland_filter_affects_attribution": False,
                    "llm_outputs_are_evidence": False,
                },
                "decision_rule": (
                    "Do not call a candidate the confirmed manufacturer until the "
                    "computed confirmed-stage audit passes."
                ),
            },
        )
    manifest_path = case_root / "manifest.json"
    if not manifest_path.exists():
        atomic_write_json(
            manifest_path,
            {
                "schema": 2,
                "schema_version": 2,
                "case_id": safe_slug(name),
                "created_at_utc": utc_now(),
                "artifacts": [],
            },
        )
    if not (case_root / "notes.md").exists():
        atomic_write_text(
            case_root / "notes.md",
            "# Notes\n\n## Observations\n\n## Assumptions\n\n## Failed hypotheses\n\n",
        )
    if not (case_root / "commands.log").exists():
        atomic_write_text(case_root / "commands.log", "")
    if not (case_root / "STATUS.md").exists():
        atomic_write_text(
            case_root / "STATUS.md",
            "# Current status\n\nNo source factory has been confirmed.\n",
        )
    if not (case_root / "claims.jsonl").exists():
        atomic_write_text(case_root / "claims.jsonl", "")
    environment_path = case_root / "output" / "environment.json"
    if not environment_path.exists():
        atomic_write_json(
            environment_path,
            build_environment_report(
                anchor=case_root,
                requested_profile="auto",
                model_mode="undeclared",
            ),
        )
    return case_root


def run(args: object) -> int:
    case_root = create_case(
        args.name,
        args.root,
        objective=args.objective,
        time_zone=args.time_zone,
        resume=args.resume,
    )
    print(json.dumps({"case_root": str(case_root)}, ensure_ascii=False))
    return 0
