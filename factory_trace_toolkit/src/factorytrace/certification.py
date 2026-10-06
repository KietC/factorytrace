"""English: Evaluate exact product, role, site, rating, and validity certification gates.

中文：按具体产品、主体角色、制造地点、参数与有效期核验认证；持证人不自动成为制造商，摘要不等于外部签名。
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence


ACTIVE_STATUSES = frozenset({"active", "certified", "current", "valid"})
CERTIFICATION_RESULT_SCHEMA = "factorytrace.certification.v2"
CERTIFICATION_ADAPTER_ID = "factorytrace.certification.evaluate_certification"
ADAPTER_ENVELOPE_SCHEMA = "factorytrace.adapter-provenance.v2"
ROLE_NAMES = (
    "licence_holder",
    "approved_user",
    "applicant",
    "listee",
    "manufacturer",
    "assembler",
    "importer",
    "distributor",
)


def _normal(value: Any) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _result_payload(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in result.items()
        if key != "adapter_provenance"
    }


def _envelope_payload(
    result: Mapping[str, Any], provenance: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "result": _result_payload(result),
        "provenance": {
            key: value
            for key, value in provenance.items()
            if key != "payload_sha256"
        },
    }


def _attach_adapter_provenance(
    result: dict[str, Any], *, input_payload: Mapping[str, Any]
) -> dict[str, Any]:
    provenance = {
        "schema": ADAPTER_ENVELOPE_SCHEMA,
        "adapter_id": CERTIFICATION_ADAPTER_ID,
        "adapter_version": 2,
        "input_sha256": _canonical_sha256(input_payload),
        "record_sha256": _canonical_sha256(input_payload.get("record", {})),
        "target_sha256": _canonical_sha256(input_payload.get("target", {})),
    }
    provenance["payload_sha256"] = _canonical_sha256(
        _envelope_payload(result, provenance)
    )
    result["adapter_provenance"] = provenance
    return result


def validate_certification_result_envelope(
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate that a serialized result is an intact adapter envelope.

    The digest is deliberately deterministic so a result can be written to
    disk and checked in a later CLI invocation.  It detects schema-less or
    edited self-reports; it is not a signature from an external trust anchor.

    中文：确定性摘要用于发现序列化结果被修改或缺少Schema；这不是认证机构的签名，也不独立证明记录真实。
    """

    errors: list[str] = []
    if result.get("schema") != CERTIFICATION_RESULT_SCHEMA:
        errors.append(f"schema must be {CERTIFICATION_RESULT_SCHEMA}")
    provenance = result.get("adapter_provenance")
    if not isinstance(provenance, Mapping):
        errors.append("adapter_provenance is required")
    else:
        if provenance.get("schema") != ADAPTER_ENVELOPE_SCHEMA:
            errors.append(f"adapter provenance schema must be {ADAPTER_ENVELOPE_SCHEMA}")
        if provenance.get("adapter_id") != CERTIFICATION_ADAPTER_ID:
            errors.append(f"adapter_id must be {CERTIFICATION_ADAPTER_ID}")
        if provenance.get("adapter_version") != 2:
            errors.append("adapter_version must be 2")
        input_hash = str(provenance.get("input_sha256") or "")
        if not re.fullmatch(r"[0-9a-f]{64}", input_hash):
            errors.append("adapter input_sha256 must be a lowercase SHA-256")
        for field in ("record_sha256", "target_sha256"):
            if not re.fullmatch(r"[0-9a-f]{64}", str(provenance.get(field) or "")):
                errors.append(f"adapter {field} must be a lowercase SHA-256")
        expected_payload_hash = _canonical_sha256(
            _envelope_payload(result, provenance)
        )
        if provenance.get("payload_sha256") != expected_payload_hash:
            errors.append("certification result payload hash mismatch")
    return {
        "schema": "factorytrace.certification-envelope-validation.v2",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def _instant(value: Any, *, end_of_day: bool = False) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif value:
        rendered = str(value).strip()
        if rendered.endswith("Z"):
            rendered = rendered[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(rendered)
        except ValueError:
            return None
    else:
        return None
    if (
        end_of_day
        and isinstance(value, str)
        and len(value.strip()) == 10
        and value.strip()[4:5] == "-"
        and value.strip()[7:8] == "-"
    ):
        parsed = parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _equal_scalar(expected: Any, observed: Any) -> bool:
    expected_number = _decimal(expected)
    observed_number = _decimal(observed)
    if expected_number is not None and observed_number is not None:
        return expected_number == observed_number
    return _normal(expected) == _normal(observed)


def _equal_value(expected: Any, observed: Any) -> bool:
    if isinstance(expected, Mapping):
        if not isinstance(observed, Mapping):
            return False
        observed_by_key = {_normal(key): value for key, value in observed.items()}
        return all(
            _normal(key) in observed_by_key
            and _equal_value(value, observed_by_key[_normal(key)])
            for key, value in expected.items()
        )
    if isinstance(expected, Sequence) and not isinstance(expected, (str, bytes)):
        if not isinstance(observed, Sequence) or isinstance(observed, (str, bytes)):
            return False
        return len(expected) == len(observed) and all(
            _equal_value(left, right) for left, right in zip(expected, observed)
        )
    return _equal_scalar(expected, observed)


def _items(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    result: list[dict[str, Any]] = []
    for item in values:
        if isinstance(item, Mapping):
            result.append(dict(item))
        elif str(item).strip():
            result.append({"party_id": str(item).strip()})
    return result


def _role_bindings(record: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    roles = record.get("roles", {})
    role_map = roles if isinstance(roles, Mapping) else {}
    return {
        role: _items(role_map.get(role, record.get(role)))
        for role in ROLE_NAMES
    }


def _party_ids(items: Sequence[Mapping[str, Any]]) -> set[str]:
    return {
        _normal(item.get("party_id") or item.get("legal_name"))
        for item in items
        if item.get("party_id") or item.get("legal_name")
    }


def _window_contains(
    start_value: Any,
    end_value: Any,
    evaluated_at: datetime,
    *,
    require_bounds: bool,
) -> tuple[bool, str]:
    start = _instant(start_value)
    end = _instant(end_value, end_of_day=True)
    if require_bounds and (start is None or end is None):
        return False, "validity window is missing or malformed"
    if start is not None and evaluated_at < start:
        return False, "not yet valid"
    if end is not None and evaluated_at > end:
        return False, "expired"
    return True, "within validity window"


def _gate(
    passed: bool,
    *,
    expected: Any,
    observed: Any,
    reason: str,
) -> dict[str, Any]:
    return {
        "passed": bool(passed),
        "expected": expected,
        "observed": observed,
        "reason": reason,
    }


def evaluate_certification(
    record: Mapping[str, Any],
    target: Mapping[str, Any],
    *,
    at: str | datetime | None = None,
) -> dict[str, Any]:
    """Evaluate an exact product/site certification conjunction.

    The adapter deliberately does not infer ``manufacturer`` from WaterMark
    Licence Holder/Approved User or UL Applicant/Listee. A party may hold more
    than one role, but every role used by a hard gate must be stated explicitly.

    中文：持证人、申请人或列名人不会自动变成制造商；硬门槛所用角色、具体产品及制造地点须分别明确绑定。
    """

    evaluated_at = _instant(at) if at is not None else datetime.now(timezone.utc)
    if evaluated_at is None:
        raise ValueError("at must be an ISO-8601 datetime")
    adapter_input = {
        "record": dict(record),
        "target": dict(target),
        "evaluated_at_utc": evaluated_at.isoformat(),
    }

    roles = _role_bindings(record)
    products_value = record.get("products")
    products = (
        [dict(item) for item in products_value if isinstance(item, Mapping)]
        if isinstance(products_value, list)
        else [dict(record)]
    )
    expected_model = target.get("model")
    material_aliases = target.get("material_aliases", [])
    if not isinstance(material_aliases, list):
        material_aliases = [material_aliases] if material_aliases else []
    expected_materials = {
        _normal(value)
        for value in [target.get("material"), *material_aliases]
        if value
    }
    expected_ratings = target.get("ratings")
    expected_type = target.get("certification_type")
    expected_site = _normal(target.get("site_id"))
    expected_manufacturer = _normal(target.get("manufacturer_party_id"))

    model_scopes = [
        scope
        for scope in products
        if _normal(scope.get("model")) == _normal(expected_model)
        and bool(_normal(expected_model))
    ]

    scope_reports: list[dict[str, Any]] = []
    for scope in model_scopes:
        materials_value = scope.get("materials", scope.get("material", []))
        materials = materials_value if isinstance(materials_value, list) else [materials_value]
        material_match = bool(expected_materials) and any(
            _normal(value) in expected_materials for value in materials if value
        )
        observed_ratings = scope.get("ratings", record.get("ratings"))
        ratings_match = (
            isinstance(expected_ratings, Mapping)
            and bool(expected_ratings)
            and _equal_value(expected_ratings, observed_ratings)
        )
        observed_type = scope.get(
            "certification_type", record.get("certification_type")
        )
        type_match = bool(_normal(expected_type)) and (
            _normal(expected_type) == _normal(observed_type)
        )
        scoped_sites = scope.get("authorized_site_ids", [])
        if not isinstance(scoped_sites, list):
            scoped_sites = [scoped_sites]
        site_scope_match = bool(expected_site) and expected_site in {
            _normal(value) for value in scoped_sites
        }
        scope_reports.append(
            {
                "model": scope.get("model"),
                "materials": materials,
                "ratings": observed_ratings,
                "certification_type": observed_type,
                "authorized_site_ids": scoped_sites,
                "material_match": material_match,
                "ratings_match": ratings_match,
                "certification_type_match": type_match,
                "site_scope_match": site_scope_match,
                "full_scope_match": all(
                    (material_match, ratings_match, type_match, site_scope_match)
                ),
            }
        )

    authorized_sites_value = record.get("authorized_sites", [])
    authorized_sites = (
        [dict(item) for item in authorized_sites_value if isinstance(item, Mapping)]
        if isinstance(authorized_sites_value, list)
        else []
    )
    matching_sites = [
        site
        for site in authorized_sites
        if _normal(site.get("site_id")) == expected_site and expected_site
    ]
    matching_site = matching_sites[0] if matching_sites else None

    cert_status = _normal(record.get("status"))
    status_active = cert_status in ACTIVE_STATUSES
    cert_window_ok, cert_window_reason = _window_contains(
        record.get("valid_from"),
        record.get("valid_to"),
        evaluated_at,
        require_bounds=True,
    )

    site_status_active = False
    site_window_ok = False
    site_window_reason = "authorized site is absent"
    site_manufacturer = ""
    if matching_site is not None:
        site_status_active = _normal(matching_site.get("status")) in ACTIVE_STATUSES
        site_window_ok, site_window_reason = _window_contains(
            matching_site.get("valid_from"),
            matching_site.get("valid_to"),
            evaluated_at,
            require_bounds=False,
        )
        site_manufacturer = _normal(matching_site.get("manufacturer_party_id"))

    explicit_manufacturers = _party_ids(roles["manufacturer"])
    explicit_manufacturer = bool(site_manufacturer) and (
        site_manufacturer in explicit_manufacturers
    )
    manufacturer_target_match = explicit_manufacturer and (
        not expected_manufacturer or site_manufacturer == expected_manufacturer
    )

    any_material = any(item["material_match"] for item in scope_reports)
    any_ratings = any(item["ratings_match"] for item in scope_reports)
    any_type = any(item["certification_type_match"] for item in scope_reports)
    any_site_scope = any(item["site_scope_match"] for item in scope_reports)
    full_scope = next(
        (item for item in scope_reports if item["full_scope_match"]), None
    )

    gates = {
        "exact_model": _gate(
            bool(model_scopes),
            expected=expected_model,
            observed=[scope.get("model") for scope in products],
            reason="exact normalized model match; family/similar models are rejected",
        ),
        "exact_material": _gate(
            any_material,
            expected=sorted(expected_materials),
            observed=[item["materials"] for item in scope_reports],
            reason="material must match within the exact-model scope",
        ),
        "exact_ratings": _gate(
            any_ratings,
            expected=expected_ratings,
            observed=[item["ratings"] for item in scope_reports],
            reason="all requested rating fields and units must match",
        ),
        "exact_certification_type": _gate(
            any_type,
            expected=expected_type,
            observed=[item["certification_type"] for item in scope_reports],
            reason="finished product, component, classified, and other types are not interchangeable",
        ),
        "active_status": _gate(
            status_active,
            expected=sorted(ACTIVE_STATUSES),
            observed=record.get("status"),
            reason="certificate status must be explicitly active/current",
        ),
        "certificate_valid_at": _gate(
            cert_window_ok,
            expected=evaluated_at.isoformat(),
            observed={
                "valid_from": record.get("valid_from"),
                "valid_to": record.get("valid_to"),
            },
            reason=cert_window_reason,
        ),
        "authorized_site_exact": _gate(
            bool(matching_site) and any_site_scope,
            expected=target.get("site_id"),
            observed={
                "record_sites": [site.get("site_id") for site in authorized_sites],
                "product_scope_sites": [
                    item["authorized_site_ids"] for item in scope_reports
                ],
            },
            reason="site must appear both in the authorization and exact product scope",
        ),
        "site_authorization_current": _gate(
            bool(matching_site) and site_status_active and site_window_ok,
            expected="active authorization at evaluation time",
            observed=(
                {
                    "status": matching_site.get("status"),
                    "valid_from": matching_site.get("valid_from"),
                    "valid_to": matching_site.get("valid_to"),
                }
                if matching_site
                else None
            ),
            reason=site_window_reason,
        ),
        "explicit_manufacturer_role": _gate(
            explicit_manufacturer,
            expected=matching_site.get("manufacturer_party_id") if matching_site else None,
            observed=sorted(explicit_manufacturers),
            reason="manufacturer must be explicit; Licence Holder/Listee is never promoted",
        ),
        "manufacturer_site_binding": _gate(
            manufacturer_target_match,
            expected=target.get("manufacturer_party_id") or "explicit site manufacturer",
            observed=matching_site.get("manufacturer_party_id") if matching_site else None,
            reason="the explicit manufacturer must be bound to the authorized site",
        ),
        "single_scope_conjunction": _gate(
            full_scope is not None,
            expected="model AND material AND ratings AND certification type AND site",
            observed=scope_reports,
            reason="matching fields may not be assembled from different product scopes",
        ),
    }
    failed = [name for name, gate in gates.items() if not gate["passed"]]

    warnings: list[str] = []
    licence_or_listee = _party_ids(
        [*roles["licence_holder"], *roles["approved_user"], *roles["listee"]]
    )
    if licence_or_listee and not explicit_manufacturers:
        warnings.append(
            "Licence Holder/Approved User/Listee is present but no explicit Manufacturer exists."
        )

    result = {
        "schema": CERTIFICATION_RESULT_SCHEMA,
        "status": "PASS" if not failed else "FAIL",
        "decision": (
            "CERTIFICATION_HARD_GATES_PASS"
            if not failed
            else "CERTIFICATION_HARD_GATES_FAIL"
        ),
        "scheme": record.get("scheme"),
        "certificate_id": record.get("certificate_id") or record.get("file_no"),
        "evaluated_at_utc": evaluated_at.isoformat(),
        "target": dict(target),
        "role_bindings": roles,
        "matched_scope": full_scope,
        "matched_site": matching_site,
        "gates": gates,
        "failed_gates": failed,
        "warnings": warnings,
        "meaning": (
            "PASS means one exact product scope, an active certificate, and an explicit "
            "Manufacturer/authorized-site binding all match. It does not prove that a "
            "specific batch was made there or that every upstream process occurred there."
        ),
    }
    return _attach_adapter_provenance(result, input_payload=adapter_input)
