"""English: Convert legacy documents into versioned siblings while preserving source bytes.

中文：将旧版文档转换为新版副本并保留源字节；推测的主体、地点与产品关联降为待核，不从地址推断地区验证。
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .assessment import HYPOTHESES
from .common import atomic_write_json, utc_now
from .scoring import source_cluster_key


class MigrationError(ValueError):
    """Raised when a document cannot be migrated safely.

    中文：文档无法安全迁移时的显式错误，不允许静默生成看似有效的新版。
    """


def _canonical_sha256(value: Any) -> str:
    rendered = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(rendered).hexdigest()


def _version(document: Mapping[str, Any]) -> int:
    value = document.get("schema_version", document.get("schema", 1))
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise MigrationError(f"unsupported schema version value: {value!r}") from error


def _stable_id(prefix: str, value: str, index: int = 0) -> str:
    digest = hashlib.sha1(f"{value}|{index}".encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{digest}"


def _party_records(entities: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, set[str]] = {}
    for source_key, role in (
        ("contracting_entity", "contracting_entity"),
        ("payment_entity", "payment_entity"),
        ("manufacturer_entity", "claimed_manufacturer"),
    ):
        name = str(entities.get(source_key) or "").strip()
        if name:
            grouped.setdefault(name, set()).add(role)
    return [
        {
            "party_id": _stable_id("PARTY", name),
            "legal_name": name,
            "roles": sorted(roles),
            "entity_resolution_state": "unverified",
        }
        for name, roles in grouped.items()
    ]


def _site_records(entities: dict[str, Any]) -> list[dict[str, Any]]:
    raw = entities.get("manufacturing_sites", [])
    sites = raw if isinstance(raw, list) else [raw]
    return [
        {
            "site_id": _stable_id("SITE", str(site), index),
            "address": str(site),
            "site_role": "claimed_manufacturing_site",
            "verification_state": "unverified",
        }
        for index, site in enumerate(sites)
        if str(site).strip()
    ]


def _manual_scores(document: dict[str, Any]) -> dict[str, Any]:
    scores: dict[str, Any] = {}
    if "confidence_index" in document:
        scores["confidence_index"] = document["confidence_index"]
    for key in ("research_assessment", "human_assessment"):
        value = document.get(key)
        if isinstance(value, dict):
            scores[key] = copy.deepcopy(value)
    return scores


def migrate_candidate_v1_to_v2(
    candidate: Mapping[str, Any], *, migrated_at_utc: str | None = None
) -> dict[str, Any]:
    """Return a v2 candidate without mutating the v1 input.

    Guessed entity/site/product links are deliberately marked unverified.  The
    function never infers mainland status from an address or an entity name.

    中文：深拷贝并转换旧版候选，推测关联标记为未验证；地址与主体名称不能产生已验证地区状态。
    """
    if not isinstance(candidate, Mapping):
        raise TypeError("candidate must be a mapping")
    source = copy.deepcopy(dict(candidate))
    version = _version(source)
    if version == 2:
        return source
    if version != 1:
        raise MigrationError(f"only schema v1 can be migrated to v2, got v{version}")
    if not str(source.get("candidate_id") or "").strip():
        raise MigrationError("candidate_id is required for candidate migration")

    migrated = copy.deepcopy(source)
    migrated["schema"] = 2
    migrated["schema_version"] = 2
    entities = migrated.get("entities", {})
    entities = entities if isinstance(entities, dict) else {}
    migrated["parties"] = migrated.get("parties") or _party_records(entities)
    migrated["sites"] = migrated.get("sites") or _site_records(entities)
    exact_sku = str(entities.get("exact_sku") or "").strip()
    migrated["product_identity"] = migrated.get("product_identity") or {
        "identity_state": "unverified" if exact_sku else "unknown",
        "exact_sku_or_revision": exact_sku,
        "material": "",
        "ratings": {},
    }
    migrated["process_scope"] = migrated.get("process_scope") or [
        {
            "process": str(process),
            "performance_state": "unverified",
            "make_or_buy": "unknown",
        }
        for process in migrated.get("target_processes", [])
    ]
    migrated["hypotheses"] = migrated.get("hypotheses") or [
        {"hypothesis_id": key, "statement": statement, "state": "untested"}
        for key, statement in HYPOTHESES.items()
    ]
    for collection in (
        "claims",
        "source_artifacts",
        "cert_records",
        "supply_events",
        "social_accounts",
        "social_posts",
        "access_receipts",
        "contacts",
    ):
        if not isinstance(migrated.get(collection), list):
            migrated[collection] = []

    migrated["verified_mainland_site"] = (
        migrated.get("verified_mainland_site")
        if isinstance(migrated.get("verified_mainland_site"), bool)
        else "unknown"
    )
    migrated_evidence: list[dict[str, Any]] = []
    for index, raw_item in enumerate(migrated.get("evidence", [])):
        if not isinstance(raw_item, dict):
            continue
        item = copy.deepcopy(raw_item)
        item["schema_version"] = 2
        item.setdefault("source_cluster_id", source_cluster_key(item, index))
        migrated_evidence.append(item)
    migrated["evidence"] = migrated_evidence

    manual_scores = _manual_scores(source)
    if manual_scores:
        migrated["legacy_manual_score"] = {
            "values": manual_scores,
            "excluded_from_v2_assessment": True,
            "notice": (
                "Historical human/legacy values are retained for provenance only; "
                "they are not calibrated source-factory probabilities."
            ),
        }
    migrated.pop("confidence_index", None)
    legacy_payloads: dict[str, Any] = {}
    for key in ("research_assessment", "human_assessment"):
        if key in migrated:
            legacy_payloads[key] = migrated.pop(key)
    if legacy_payloads:
        migrated["legacy_payloads"] = legacy_payloads
    migrated["migration"] = {
        "source_schema_version": 1,
        "target_schema_version": 2,
        "source_document_sha256": _canonical_sha256(source),
        "migrated_at_utc": migrated_at_utc or utc_now(),
        "non_destructive": True,
        "not_inferred": [
            "verified_mainland_site",
            "entity_relationships",
            "manufacturing_site_authorization",
            "exact_product_or_batch_link",
        ],
    }
    return migrated


def migrate_case_v1_to_v2(
    case: Mapping[str, Any], *, migrated_at_utc: str | None = None
) -> dict[str, Any]:
    if not isinstance(case, Mapping):
        raise TypeError("case must be a mapping")
    source = copy.deepcopy(dict(case))
    version = _version(source)
    if version == 2:
        return source
    if version != 1:
        raise MigrationError(f"only schema v1 can be migrated to v2, got v{version}")
    if not str(source.get("case_id") or "").strip():
        raise MigrationError("case_id is required for case migration")
    migrated = copy.deepcopy(source)
    migrated["schema"] = 2
    migrated["schema_version"] = 2
    allowed_statuses = {
        "open",
        "research",
        "operational",
        "paused",
        "superseded",
        "confirmed",
        "closed",
    }
    legacy_status = str(migrated.get("status", "open"))
    migration_warnings: list[str] = []
    if legacy_status not in allowed_statuses:
        migrated["legacy_status"] = legacy_status
        migrated["status"] = "research" if "research" in legacy_status else "open"
        migration_warnings.append(
            f"legacy status {legacy_status!r} mapped to {migrated['status']!r}; "
            "the original value is preserved in legacy_status"
        )
    migrated.setdefault(
        "assessment_policy",
        {
            "single_probability_forbidden": True,
            "mainland_filter_affects_attribution": False,
            "llm_outputs_are_evidence": False,
        },
    )
    migrated["migration"] = {
        "source_schema_version": 1,
        "target_schema_version": 2,
        "source_document_sha256": _canonical_sha256(source),
        "migrated_at_utc": migrated_at_utc or utc_now(),
        "non_destructive": True,
        "warnings": migration_warnings,
    }
    return migrated


def migrate_document_v1_to_v2(
    document: Mapping[str, Any], *, migrated_at_utc: str | None = None
) -> dict[str, Any]:
    if "candidate_id" in document:
        return migrate_candidate_v1_to_v2(
            document, migrated_at_utc=migrated_at_utc
        )
    if "case_id" in document:
        return migrate_case_v1_to_v2(document, migrated_at_utc=migrated_at_utc)
    raise MigrationError("cannot determine v1 document type; candidate_id or case_id is required")


def migrate_json_file(
    source_path: Path,
    destination_path: Path | None = None,
    *,
    overwrite: bool = False,
) -> Path:
    """Write a migrated sibling/file while preserving source bytes.

    中文：新版写入不同路径并核对源字节未变化；已有目标默认拒绝覆盖，不允许原地迁移。
    """
    source_path = Path(source_path)
    if destination_path is None:
        destination_path = source_path.with_name(f"{source_path.stem}.v2.json")
    destination_path = Path(destination_path)
    if source_path.resolve() == destination_path.resolve():
        raise MigrationError("destination must differ from source for non-destructive migration")
    if destination_path.exists() and not overwrite:
        raise FileExistsError(f"migration destination already exists: {destination_path}")
    source_bytes_before = source_path.read_bytes()
    document = json.loads(source_bytes_before.decode("utf-8-sig"))
    migrated = migrate_document_v1_to_v2(document)
    atomic_write_json(destination_path, migrated)
    if source_path.read_bytes() != source_bytes_before:
        raise MigrationError("source changed during migration; destination cannot be trusted")
    return destination_path
