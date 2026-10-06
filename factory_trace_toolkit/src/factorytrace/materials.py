"""English: Check stage-required photographs, measurements, and accepted material records.

中文：核验阶段所需照片、尺寸与材料记录；只有被接受且可定位的记录用于满足门槛，营销文案不能代替材质证据。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image

from .common import atomic_write_json, load_json, path_within, sha256_file, utc_now


STAGES = {"discovery": 0, "comparison": 1, "process": 2, "confirmed": 3}
ACCEPTED_STATUSES = {"verified", "accepted"}


def check_materials(
    case_root: Path,
    plan_path: Path,
    *,
    stage: str,
) -> dict[str, Any]:
    root = case_root.resolve(strict=True)
    plan = load_json(plan_path)
    errors: list[str] = []
    warnings: list[str] = []
    checked: list[dict[str, Any]] = []
    seen: set[str] = set()
    known_source_ids: set[str] = set()
    manifest_path = root / "manifest.json"
    if manifest_path.is_file():
        manifest = load_json(manifest_path)
        known_source_ids.update(
            str(item.get("artifact_id"))
            for item in manifest.get("artifacts", [])
            if item.get("artifact_id")
        )
    for candidate_path in (root / "candidates").glob("*.json"):
        candidate = load_json(candidate_path)
        known_source_ids.update(
            str(item.get("evidence_id"))
            for item in candidate.get("evidence", [])
            if item.get("evidence_id")
        )

    for index, item in enumerate(plan.get("items", []), start=1):
        if not isinstance(item, dict):
            errors.append(f"item {index}: must be an object")
            continue
        item_id = str(item.get("item_id", "")).strip()
        if not item_id:
            errors.append(f"item {index}: item_id is required")
            continue
        if item_id in seen:
            errors.append(f"duplicate item_id: {item_id}")
        seen.add(item_id)
        required_from = str(item.get("required_from", "confirmed"))
        if required_from not in STAGES:
            errors.append(f"{item_id}: invalid required_from {required_from}")
            continue
        required_now = STAGES[required_from] <= STAGES[stage]
        status = str(item.get("status", "missing"))
        paths = item.get("paths", [])
        if not isinstance(paths, list):
            errors.append(f"{item_id}: paths must be a list")
            paths = []
        item_errors: list[str] = []
        file_reports: list[dict[str, Any]] = []
        if required_now and status not in ACCEPTED_STATUSES:
            item_errors.append(f"status is {status}, expected verified/accepted")
        if required_now and item.get("file_required") and not paths:
            item_errors.append("at least one file path is required")
        source_id = str(item.get("source_or_evidence_id", "")).strip()
        if stage == "confirmed" and required_now:
            if not source_id:
                item_errors.append(
                    "source_or_evidence_id is required for confirmed readiness"
                )
            elif source_id not in known_source_ids:
                item_errors.append(
                    f"unknown source_or_evidence_id: {source_id}"
                )

        for value in paths:
            target = (root / str(value)).resolve()
            if not path_within(target, root):
                item_errors.append(f"path escapes case root: {value}")
                continue
            if not target.is_file():
                item_errors.append(f"file missing: {value}")
                continue
            report: dict[str, Any] = {
                "path": target.relative_to(root).as_posix(),
                "size": target.stat().st_size,
                "sha256": sha256_file(target),
            }
            try:
                with Image.open(target) as image:
                    report["image"] = {
                        "format": image.format,
                        "width": image.width,
                        "height": image.height,
                    }
                    minimum = int(item.get("min_long_edge_px") or 0)
                    if minimum and max(image.width, image.height) < minimum:
                        item_errors.append(
                            f"{value}: long edge below {minimum}px"
                        )
            except (OSError, ValueError):
                pass
            file_reports.append(report)

        if item_errors:
            (errors if required_now else warnings).extend(
                f"{item_id}: {message}" for message in item_errors
            )
        checked.append(
            {
                "item_id": item_id,
                "required_now": required_now,
                "status": status,
                "files": file_reports,
                "errors": item_errors,
            }
        )

    return {
        "schema": 1,
        "created_at_utc": utc_now(),
        "case_root": str(root),
        "plan_path": str(plan_path.resolve()),
        "stage": stage,
        "status": "PASS" if not errors else "FAIL",
        "checked_items": checked,
        "errors": errors,
        "warnings": warnings,
        "meaning": (
            "PASS means the declared material checklist for this stage is complete. "
            "It does not prove authenticity or manufacturing identity."
        ),
    }


def run(args: object) -> int:
    plan_path = args.plan or (args.case_root / "work" / "materials_plan.json")
    report = check_materials(args.case_root, plan_path, stage=args.stage)
    output = args.output or (
        args.case_root / "output" / f"materials_{args.stage}.json"
    )
    atomic_write_json(output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1
