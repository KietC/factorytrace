"""English: Coordinate versioned case validation, migration, receipts, and report audits.

中文：协调新版案件验证、迁移、回执与报告审查；先检查词法路径与重解析点，再做解析，迁移仅复制白名单数据。
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import stat
import uuid
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

from .assessment import assess_candidate
from .certification import evaluate_certification
from .common import FileLock, atomic_write_json, atomic_write_text, sha256_file, utc_now
from .events import validate_event_chain
from .init_case import ensure_v2_layout
from .migration import migrate_candidate_v1_to_v2, migrate_case_v1_to_v2
from .process_packs import (
    compose_process_packs,
    evaluate_process_pack,
    list_process_packs,
    load_process_pack,
)
from .reporting import build_report_payload, lint_report_file, lint_report_payload
from .schema_validation import validation_report
from .social import evaluate_social_chain


ACCESS_STATES = {
    "verified_dom",
    "screenshot_only",
    "opened_unverified",
    "blocked_login",
    "captcha",
    "blocked_policy",
    "rate_limited",
    "content_removed",
    "geo_restricted",
    "service_unavailable",
}
BLOCKED_ACCESS_STATES = {
    "blocked_login",
    "captcha",
    "blocked_policy",
    "rate_limited",
    "geo_restricted",
    "service_unavailable",
}

CANONICAL_CASE_ROOT_FILES = frozenset(
    {
        "case.json",
        "manifest.json",
        "claims.jsonl",
        "commands.log",
        "notes.md",
        "STATUS.md",
    }
)
CANONICAL_EXCLUDED_SEGMENTS = frozenset(
    {".venv", "node_modules", "cache", "release", "renders", "staging"}
)
CANONICAL_EVIDENCE_SUFFIXES = frozenset(
    {
        ".bmp",
        ".csv",
        ".docx",
        ".eml",
        ".gif",
        ".htm",
        ".html",
        ".jpeg",
        ".jpg",
        ".json",
        ".jsonl",
        ".md",
        ".msg",
        ".pdf",
        ".png",
        ".sha256",
        ".svg",
        ".tif",
        ".tiff",
        ".tsv",
        ".txt",
        ".webp",
        ".xls",
        ".xlsx",
        ".xml",
        ".yaml",
        ".yml",
        ".zip",
    }
)
CANONICAL_LOG_SUFFIXES = frozenset(
    {".csv", ".json", ".jsonl", ".log", ".md", ".sha256", ".txt"}
)
CANONICAL_WORK_FILES = frozenset(
    {
        "work/product_profile.json",
        "work/image_observations.json",
        "work/materials_plan.json",
        "work/research_round.json",
        "work/crop_plan.json",
        "work/certification_gate.json",
    }
)


def _load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _write_result(path: Path | None, value: Mapping[str, Any]) -> None:
    if path is not None:
        atomic_write_json(Path(path), dict(value))


def _schema_version(value: Mapping[str, Any]) -> int:
    try:
        return int(value.get("schema_version", value.get("schema", 1)))
    except (TypeError, ValueError):
        return -1


def _candidate_paths(case_root: Path) -> list[Path]:
    return sorted((case_root / "candidates").glob("*.json"))


def _is_reparse_point(path: Path) -> bool:
    metadata = path.lstat()
    attributes = int(getattr(metadata, "st_file_attributes", 0))
    reparse_flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    return path.is_symlink() or bool(attributes & reparse_flag)


def _lexical_absolute(path: Path) -> Path:
    """Return an absolute path without resolving links or junctions.

    中文：先建立词法绝对路径，不跟随符号链接或junction，供越界检查使用。
    """

    return Path(os.path.abspath(os.fspath(path)))


def _assert_no_reparse_path_components(
    path: Path, *, label: str, strict: bool
) -> Path:
    """Reject links/junctions in every existing component before ``resolve``.

    ``Path.resolve`` follows a Windows junction even when the junction is the
    supplied case root or destination parent.  Security checks must therefore
    inspect the lexical path with ``lstat`` first.  For a not-yet-created
    destination, inspection stops at the first missing component.

    中文：resolve会跟随根目录或父目录中的junction；先以lstat检查每个已有路径组件，未创建目标在首个缺失组件停止。
    """

    absolute = _lexical_absolute(Path(path))
    parts = absolute.parts
    if not parts:
        raise ValueError(f"{label} is empty")
    current = Path(parts[0])
    components = [current]
    for part in parts[1:]:
        current = current / part
        components.append(current)
    for component in components:
        try:
            component.lstat()
        except FileNotFoundError:
            if strict:
                raise FileNotFoundError(f"{label} component is missing: {component}")
            break
        if _is_reparse_point(component):
            raise ValueError(
                f"{label} contains a symbolic link, junction, or reparse point "
                f"before resolution: {component}"
            )
    return absolute


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _scan_case_files(root: Path) -> tuple[list[Path], list[dict[str, str]]]:
    """Walk a case without following symbolic links or Windows junctions.

    中文：只遍历案件本体，不跟随链接或Windows junction；被拒绝路径单独记录，不把外部文件带入迁移。
    """

    lexical_root = _assert_no_reparse_path_components(
        Path(root), label="case root", strict=True
    )
    resolved_root = lexical_root.resolve(strict=True)
    stack = [resolved_root]
    files: list[Path] = []
    rejected: list[dict[str, str]] = []
    while stack:
        current = stack.pop()
        with os.scandir(current) as entries:
            ordered = sorted(entries, key=lambda item: item.name.casefold())
        for entry in ordered:
            path = Path(entry.path)
            relative = path.relative_to(resolved_root).as_posix()
            if _is_reparse_point(path):
                rejected.append(
                    {"path": relative, "reason": "symlink_or_reparse_point_not_followed"}
                )
                continue
            if entry.is_dir(follow_symlinks=False):
                stack.append(path)
                continue
            if not entry.is_file(follow_symlinks=False):
                rejected.append({"path": relative, "reason": "non_regular_file"})
                continue
            resolved = path.resolve(strict=True)
            if not _inside(resolved, resolved_root):
                rejected.append({"path": relative, "reason": "resolved_path_escapes_case"})
                continue
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(resolved_root).as_posix()), rejected


def _file_inventory(root: Path, *, exclude: Iterable[str] = ()) -> list[dict[str, Any]]:
    lexical_root = _assert_no_reparse_path_components(
        Path(root), label="inventory root", strict=True
    )
    resolved_root = lexical_root.resolve(strict=True)
    excluded = set(exclude)
    files, _ = _scan_case_files(resolved_root)
    rows: list[dict[str, Any]] = []
    for path in files:
        relative = path.relative_to(resolved_root).as_posix()
        if relative in excluded:
            continue
        rows.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return rows


def _canonical_case_file_decision(relative: str) -> tuple[bool, str]:
    """Apply the exact v2 migration allowlist to one POSIX relative path.

    中文：逐条按规范相对路径白名单判定是否复制；运行环境、缓存与发布输出不属于案件证据。
    """

    pure = PurePosixPath(relative)
    parts = pure.parts
    if not parts or pure.is_absolute() or ".." in parts:
        return False, "invalid_relative_path"
    folded_parts = tuple(part.casefold() for part in parts)
    excluded = next(
        (part for part in folded_parts if part in CANONICAL_EXCLUDED_SEGMENTS),
        None,
    )
    if excluded is not None:
        return False, f"excluded_path_segment:{excluded}"
    if len(parts) == 1 and relative in CANONICAL_CASE_ROOT_FILES:
        return True, "canonical_root_file"
    if relative in CANONICAL_WORK_FILES:
        return True, "canonical_work_file"
    if (
        len(parts) >= 3
        and folded_parts[0] == "artifacts"
        and folded_parts[1] in {"original", "derived"}
    ):
        return True, "canonical_artifact"
    if (
        len(parts) == 2
        and folded_parts[0] == "candidates"
        and pure.suffix.casefold() == ".json"
    ):
        return True, "canonical_candidate"
    if (
        len(parts) >= 2
        and folded_parts[0] == "evidence"
        and pure.suffix.casefold() in CANONICAL_EVIDENCE_SUFFIXES
    ):
        return True, "canonical_evidence"
    if (
        len(parts) >= 2
        and folded_parts[0] == "logs"
        and pure.suffix.casefold() in CANONICAL_LOG_SUFFIXES
    ):
        return True, "canonical_log"
    return False, "not_in_canonical_allowlist"


def _is_canonical_case_file(relative: str) -> bool:
    return _canonical_case_file_decision(relative)[0]


def _remove_owned_temporary_directory(path: Path, parent: Path) -> None:
    lexical_parent = _assert_no_reparse_path_components(
        parent, label="migration temporary parent", strict=True
    )
    lexical_path = _assert_no_reparse_path_components(
        path, label="migration temporary path", strict=False
    )
    resolved_parent = lexical_parent.resolve(strict=True)
    resolved_path = lexical_path.resolve(strict=False)
    if resolved_path.parent != resolved_parent or not resolved_path.name.startswith("."):
        raise RuntimeError(f"refusing to remove unowned migration path: {resolved_path}")
    if resolved_path.exists():
        shutil.rmtree(resolved_path)


def validate_case(case_root: Path) -> dict[str, Any]:
    root = Path(case_root).resolve(strict=True)
    documents: list[dict[str, Any]] = []
    semantic_errors: list[str] = []
    warnings: list[str] = []

    case_path = root / "case.json"
    if not case_path.is_file():
        semantic_errors.append("case.json is missing")
        case_document: dict[str, Any] = {}
    else:
        case_document = _load_json(case_path)
        case_schema = (
            "case.v2.schema.json"
            if _schema_version(case_document) == 2
            else "case.schema.json"
        )
        report = validation_report(case_document, case_schema)
        documents.append({"path": "case.json", **report})

    assessment_count = 0
    for path in _candidate_paths(root):
        relative = path.relative_to(root).as_posix()
        try:
            candidate = _load_json(path)
            version = _schema_version(candidate)
            candidate_schema = (
                "candidate.v2.schema.json" if version == 2 else "candidate.schema.json"
            )
            report = validation_report(candidate, candidate_schema)
            documents.append({"path": relative, **report})
            evidence_schema = (
                "evidence.v2.schema.json" if version == 2 else "evidence.schema.json"
            )
            for index, evidence in enumerate(candidate.get("evidence", [])):
                evidence_report = validation_report(evidence, evidence_schema)
                documents.append(
                    {
                        "path": f"{relative}#/evidence/{index}",
                        **evidence_report,
                    }
                )
            assessment = assess_candidate(candidate)
            assessment_report = validation_report(
                assessment, "assessment.v2.schema.json"
            )
            documents.append(
                {
                    "path": f"generated-assessment:{candidate.get('candidate_id', path.stem)}",
                    **assessment_report,
                }
            )
            assessment_count += 1
        except Exception as error:  # Collect all invalid documents. / 中文：一次收集全部无效文档以便集中修复。
            semantic_errors.append(f"{relative}: {type(error).__name__}: {error}")

    contacts_path = root / "evidence" / "contacts.csv"
    if contacts_path.is_file():
        with contacts_path.open(encoding="utf-8-sig", newline="") as stream:
            for row_number, row in enumerate(csv.DictReader(stream), start=2):
                has_contact = any(
                    str(row.get(field, "")).strip()
                    for field in (
                        "contact_name",
                        "phone",
                        "email",
                        "wechat",
                        "whatsapp",
                        "linkedin",
                    )
                )
                if has_contact and not str(row.get("source_url", "")).strip():
                    semantic_errors.append(
                        f"evidence/contacts.csv:{row_number}: contact has no source_url"
                    )
                if has_contact and not str(row.get("last_verified_utc", "")).strip():
                    semantic_errors.append(
                        f"evidence/contacts.csv:{row_number}: contact has no last_verified_utc"
                    )

    invalid = [item for item in documents if not item.get("valid", False)]
    if _schema_version(case_document) != 2:
        warnings.append(
            "case is schema v1; use `factorytrace migrate --case-root ... --to 2` "
            "for the non-destructive v2 path"
        )
    status = "PASS" if not invalid and not semantic_errors else "FAIL"
    return {
        "schema": 2,
        "schema_version": 2,
        "status": status,
        "case_root": str(root),
        "validated_at_utc": utc_now(),
        "documents_checked": len(documents),
        "assessments_recomputed": assessment_count,
        "invalid_documents": invalid,
        "semantic_errors": semantic_errors,
        "warnings": warnings,
    }


def migrate_case_directory(
    case_root: Path,
    *,
    destination_root: Path | None = None,
    copy_mode: str = "canonical",
) -> dict[str, Any]:
    source_lexical = _assert_no_reparse_path_components(
        Path(case_root), label="migration source root", strict=True
    )
    source = source_lexical.resolve(strict=True)
    if copy_mode != "canonical":
        raise ValueError("only copy_mode='canonical' is supported")
    destination_lexical = (
        _assert_no_reparse_path_components(
            Path(destination_root), label="migration destination", strict=False
        )
        if destination_root is not None
        else source.with_name(f"{source.name}-schema-v2")
    )
    destination_parent_lexical = _assert_no_reparse_path_components(
        destination_lexical.parent,
        label="migration destination parent",
        strict=True,
    )
    destination_parent = destination_parent_lexical.resolve(strict=True)
    destination = destination_lexical.resolve(strict=False)
    if destination == source:
        raise ValueError("migration destination must differ from the source case")
    try:
        destination_lexical.lstat()
    except FileNotFoundError:
        pass
    else:
        raise FileExistsError(
            f"migration destination already exists: {destination}; original was not changed"
        )

    if not _inside(destination, destination_parent):
        raise ValueError("migration destination escapes its resolved parent")
    temporary = destination_parent / f".{destination.name}.migration-{uuid.uuid4().hex}.tmp"
    source_before = _file_inventory(source)
    source_files, rejected_entries = _scan_case_files(source)
    copied_entries: list[dict[str, Any]] = []
    skipped_entries: list[dict[str, str]] = []
    migrated_documents: list[str] = []
    warnings: list[str] = []
    try:
        temporary.mkdir(parents=False, exist_ok=False)
        for path in source_files:
            relative = path.relative_to(source).as_posix()
            canonical, decision_reason = _canonical_case_file_decision(relative)
            if not canonical:
                skipped_entries.append({"path": relative, "reason": decision_reason})
                continue
            target = temporary / Path(relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied_entries.append(
                {
                    "path": relative,
                    "bytes": target.stat().st_size,
                    "source_sha256": sha256_file(path),
                    "copied_sha256": sha256_file(target),
                }
            )
            if copied_entries[-1]["source_sha256"] != copied_entries[-1]["copied_sha256"]:
                raise IOError(f"copied file hash mismatch: {relative}")

        case_path = temporary / "case.json"
        if not case_path.is_file():
            raise FileNotFoundError("canonical migration requires case.json")
        case_document = _load_json(case_path)
        if _schema_version(case_document) == 1:
            atomic_write_json(case_path, migrate_case_v1_to_v2(case_document))
            migrated_documents.append("case.json")
        elif _schema_version(case_document) != 2:
            raise ValueError("case.json has an unsupported schema version")

        for path in _candidate_paths(temporary):
            candidate = _load_json(path)
            if _schema_version(candidate) == 1:
                atomic_write_json(path, migrate_candidate_v1_to_v2(candidate))
                migrated_documents.append(path.relative_to(temporary).as_posix())
            elif _schema_version(candidate) != 2:
                raise ValueError(f"unsupported candidate schema: {path.name}")

        ensure_v2_layout(temporary)
        validation = validate_case(temporary)
        source_after = _file_inventory(source)
        source_unchanged = source_before == source_after
        if not source_unchanged:
            raise RuntimeError("source inventory changed during migration")
        if validation["status"] != "PASS":
            raise ValueError(f"migrated case validation failed: {validation['semantic_errors']}")
        if rejected_entries:
            warnings.append(
                f"{len(rejected_entries)} symlink/reparse/non-regular entries were not followed"
            )
        if skipped_entries:
            warnings.append(
                f"{len(skipped_entries)} non-canonical files were intentionally excluded"
            )

        report_relative = "output/migration_v1_to_v2.json"
        destination_inventory = _file_inventory(temporary, exclude=(report_relative,))
        report = {
            "schema": 2,
            "schema_version": 2,
            "status": "PASS",
            "created_at_utc": utc_now(),
            "source_root": str(source),
            "destination_root": str(destination),
            "copy_mode": copy_mode,
            "source_read_only_policy": True,
            "source_unchanged": source_unchanged,
            "migrated_documents": migrated_documents,
            "copied_entries": copied_entries,
            "skipped_entries": skipped_entries,
            "rejected_entries": rejected_entries,
            "source_inventory": source_before,
            "destination_inventory_excluding_this_report": destination_inventory,
            "validation": validation,
            "warnings": warnings,
            "rollback": (
                "The original case was never overwritten. Stop using destination_root and "
                "resume from source_root; no reverse transformation is required."
            ),
        }
        atomic_write_json(temporary / report_relative, report)
        temporary.replace(destination)
        return report
    except Exception as error:
        _remove_owned_temporary_directory(temporary, destination_parent)
        failure_receipt = destination_parent / f"{destination.name}.migration-failed.json"
        atomic_write_json(
            failure_receipt,
            {
                "schema": 2,
                "status": "FAIL",
                "created_at_utc": utc_now(),
                "source_root": str(source),
                "destination_root": str(destination),
                "copy_mode": copy_mode,
                "error": f"{type(error).__name__}: {error}",
                "destination_published": False,
                "rejected_entries": rejected_entries,
                "skipped_entries": skipped_entries,
            },
        )
        raise


def assess_case(case_root: Path, output_dir: Path | None = None) -> dict[str, Any]:
    root = Path(case_root).resolve(strict=True)
    target = Path(output_dir) if output_dir else root / "output" / "assessments"
    target.mkdir(parents=True, exist_ok=True)
    index: list[dict[str, Any]] = []
    for path in _candidate_paths(root):
        candidate = _load_json(path)
        assessment = assess_candidate(candidate)
        validation = validation_report(assessment, "assessment.v2.schema.json")
        if not validation["valid"]:
            raise ValueError(
                f"generated assessment failed schema validation: {path.name}: "
                f"{validation['errors']}"
            )
        output = target / f"{assessment['candidate_id']}.assessment.v2.json"
        atomic_write_json(output, assessment)
        index.append(
            {
                "candidate_id": assessment["candidate_id"],
                "trace_stage": assessment["trace_stage"],
                "analytic_confidence": assessment["analytic_confidence"],
                "evidence_sufficiency_score": assessment[
                    "evidence_sufficiency_score"
                ],
                "capability_fit_score": assessment["capability_fit_score"],
                "verification_priority": assessment["verification_priority"],
                "procurement_utility": assessment["procurement_utility"],
                "output": str(output),
            }
        )
    payload = {
        "schema": 2,
        "schema_version": 2,
        "created_at_utc": utc_now(),
        "semantics": "multi_axis_non_probability",
        "candidates": index,
    }
    atomic_write_json(target / "assessment_index.v2.json", payload)
    return payload


def hypotheses_case(case_root: Path, output: Path | None = None) -> dict[str, Any]:
    root = Path(case_root).resolve(strict=True)
    rows: list[dict[str, Any]] = []
    for path in _candidate_paths(root):
        assessment = assess_candidate(_load_json(path))
        rows.append(
            {
                "candidate_id": assessment["candidate_id"],
                "trace_stage": assessment["trace_stage"],
                "analytic_confidence": assessment["analytic_confidence"],
                "ach": assessment["ach"],
                "verification_priority": assessment["verification_priority"],
                "verification_priority_drivers": assessment[
                    "verification_priority_drivers"
                ],
            }
        )
    payload = {
        "schema": "factorytrace.ach-index.v2",
        "created_at_utc": utc_now(),
        "case_root": str(root),
        "candidates": rows,
    }
    target = output or root / "output" / "hypotheses_v2.json"
    atomic_write_json(target, payload)
    return payload


def capture_receipts(case_root: Path, receipt_paths: list[Path]) -> dict[str, Any]:
    root = Path(case_root).resolve(strict=True)
    receipts: list[dict[str, Any]] = []
    for path in receipt_paths:
        value = _load_json(path)
        values = value if isinstance(value, list) else [value]
        for raw in values:
            if not isinstance(raw, dict):
                raise ValueError(f"receipt must be an object: {path}")
            receipt = dict(raw)
            state = str(receipt.get("access_status", receipt.get("status", ""))).strip()
            if state not in ACCESS_STATES:
                raise ValueError(
                    f"invalid access status {state!r}; expected one of {sorted(ACCESS_STATES)}"
                )
            receipt["access_status"] = state
            receipt.setdefault("captured_at_utc", utc_now())
            receipt["evidence_eligible"] = False
            receipt["absence_conclusion_permitted"] = False
            receipt["interpretation"] = (
                "access obstruction; neither positive nor negative factory evidence"
                if state in BLOCKED_ACCESS_STATES
                else "access receipt only; source contents require separate evidence capture"
            )
            receipt["input_receipt_path"] = str(Path(path).resolve())
            receipts.append(receipt)

    target = root / "evidence" / "access_receipts.jsonl"
    lock = root / "evidence" / ".access_receipts.lock"
    with FileLock(lock):
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8", newline="\n") as stream:
            for receipt in receipts:
                stream.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True) + "\n")
    return {"status": "PASS", "appended": len(receipts), "path": str(target)}


def _infer_social_target(candidate: Mapping[str, Any]) -> dict[str, Any]:
    explicit = candidate.get("social_target")
    if isinstance(explicit, Mapping):
        return dict(explicit)
    parties = candidate.get("parties", [])
    sites = candidate.get("sites", [])
    product = candidate.get("product_identity", {})
    return {
        "entity_id": (
            parties[0].get("party_id")
            if isinstance(parties, list) and parties and isinstance(parties[0], Mapping)
            else ""
        ),
        "site_id": (
            sites[0].get("site_id")
            if isinstance(sites, list) and sites and isinstance(sites[0], Mapping)
            else ""
        ),
        "processes": candidate.get("target_processes", []),
        "sku_id": (
            product.get("exact_sku_or_revision", "")
            if isinstance(product, Mapping)
            else ""
        ),
    }


def assess_social_case(case_root: Path, output: Path | None = None) -> dict[str, Any]:
    root = Path(case_root).resolve(strict=True)
    results: list[dict[str, Any]] = []
    for path in _candidate_paths(root):
        candidate = _load_json(path)
        observations = [
            item
            for item in candidate.get("social_posts", [])
            if isinstance(item, Mapping)
        ]
        target = _infer_social_target(candidate)
        for account in candidate.get("social_accounts", []):
            if not isinstance(account, Mapping):
                continue
            account_id = account.get("account_id")
            selected = [
                item
                for item in observations
                if not item.get("account_id") or item.get("account_id") == account_id
            ]
            results.append(
                {
                    "candidate_id": candidate.get("candidate_id"),
                    "result": evaluate_social_chain(account, selected, target),
                }
            )
    payload = {
        "schema": "factorytrace.social-index.v2",
        "created_at_utc": utc_now(),
        "results": results,
    }
    target_path = output or root / "output" / "social_assessment_v2.json"
    atomic_write_json(target_path, payload)
    return payload


def validate_events_case(
    case_root: Path,
    *,
    required_steps: Iterable[str] = (),
    terminal_objects: Iterable[str] = (),
    output: Path | None = None,
) -> dict[str, Any]:
    root = Path(case_root).resolve(strict=True)
    results: list[dict[str, Any]] = []
    for path in _candidate_paths(root):
        candidate = _load_json(path)
        events = [
            item for item in candidate.get("supply_events", []) if isinstance(item, Mapping)
        ]
        certs = [
            item for item in candidate.get("cert_records", []) if isinstance(item, Mapping)
        ]
        results.append(
            {
                "candidate_id": candidate.get("candidate_id"),
                "result": validate_event_chain(
                    events,
                    certs,
                    required_certified_biz_steps=required_steps,
                    terminal_object_ids=terminal_objects,
                ),
            }
        )
    payload = {
        "schema": "factorytrace.events-index.v2",
        "created_at_utc": utc_now(),
        "status": (
            "PASS"
            if all(item["result"]["status"] == "PASS" for item in results)
            else "FAIL"
        ),
        "results": results,
    }
    target = output or root / "output" / "event_validation_v2.json"
    atomic_write_json(target, payload)
    return payload


def lint_case_reports(case_root: Path, paths: list[Path] | None = None) -> dict[str, Any]:
    root = Path(case_root).resolve(strict=True)
    reports = list(paths or [])
    if not reports:
        supported = {".json", ".md", ".txt", ".csv", ".xlsx", ".docx"}
        report_roots = (root / "output" / "reports", root / "output" / "rankings")
        reports = sorted(
            {
                path
                for report_root in report_roots
                if report_root.is_dir()
                for path in report_root.rglob("*")
                if path.is_file() and path.suffix.casefold() in supported
            },
            key=lambda path: path.as_posix().casefold(),
        )
    errors: list[str] = []
    checked: list[str] = []
    if not reports:
        payload = build_report_payload(root)
        errors.extend(lint_report_payload(payload))
        checked.append("generated:canonical-report-payload")
    for path in reports:
        checked.append(str(path))
        try:
            errors.extend(f"{path}: {item}" for item in lint_report_file(path))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"{path}: report inspection failed: {error}")
    return {"status": "PASS" if not errors else "FAIL", "checked": checked, "errors": errors}


def run_migrate(args: object) -> int:
    if int(args.to) != 2:
        raise ValueError("only migration to schema v2 is supported")
    result = migrate_case_directory(
        args.case_root,
        destination_root=args.output_root,
        copy_mode=getattr(args, "copy_mode", "canonical"),
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "source_root": result["source_root"],
                "destination_root": result["destination_root"],
                "source_unchanged": result["source_unchanged"],
                "copy_mode": result["copy_mode"],
                "copied_files": len(result["copied_entries"]),
                "skipped_files": len(result["skipped_entries"]),
                "rejected_entries": len(result["rejected_entries"]),
                "migrated_documents": len(result["migrated_documents"]),
                "source_files": len(result["source_inventory"]),
                "destination_files": len(
                    result["destination_inventory_excluding_this_report"]
                ),
                "validation_status": result["validation"]["status"],
                "warnings": result["warnings"],
                "report": str(
                    Path(result["destination_root"])
                    / "output"
                    / "migration_v1_to_v2.json"
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if result["status"] == "PASS" else 1


def run_validate(args: object) -> int:
    result = validate_case(args.case_root)
    output = args.output or Path(args.case_root) / "output" / "validation_v2.json"
    atomic_write_json(output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


def run_assess(args: object) -> int:
    result = assess_case(args.case_root, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def run_hypotheses(args: object) -> int:
    result = hypotheses_case(args.case_root, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def run_capture(args: object) -> int:
    result = capture_receipts(args.case_root, args.receipt)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def run_certification_check(args: object) -> int:
    record = _load_json(args.record)
    target = _load_json(args.target)
    if args.scheme != "generic":
        actual = str(record.get("scheme", "")).strip().casefold()
        if actual != args.scheme.casefold():
            raise ValueError(
                f"record scheme {record.get('scheme')!r} does not match --scheme {args.scheme!r}"
            )
    result = evaluate_certification(record, target, at=args.at)
    _write_result(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


def run_social_assess(args: object) -> int:
    result = assess_social_case(args.case_root, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def run_events_validate(args: object) -> int:
    result = validate_events_case(
        args.case_root,
        required_steps=args.required_certified_biz_step,
        terminal_objects=args.terminal_object,
        output=args.output,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


def run_process_pack_list(args: object) -> int:
    result = list_process_packs(pack_dir=args.pack_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


def run_process_pack_show(args: object) -> int:
    result = (
        compose_process_packs(args.name, pack_dir=args.pack_dir)
        if len(args.name) > 1
        else load_process_pack(args.name[0], pack_dir=args.pack_dir)
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def run_process_pack_evaluate(args: object) -> int:
    pack = (
        compose_process_packs(args.name, pack_dir=args.pack_dir)
        if len(args.name) > 1
        else load_process_pack(args.name[0], pack_dir=args.pack_dir)
    )
    result = evaluate_process_pack(pack, _load_json(args.facts))
    _write_result(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


def run_lint_case(args: object) -> int:
    result = lint_case_reports(args.case_root, args.path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1
