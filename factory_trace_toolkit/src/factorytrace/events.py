"""English: Validate event structure, chronology, object lineage, and certified-site semantics.

中文：验证事件结构、时间先后、对象链路与认证地点语义；事件声明需要外部证据，格式通过不代表真实发生。
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence


EVENT_TYPES = frozenset(
    {
        "ObjectEvent",
        "AggregationEvent",
        "TransactionEvent",
        "TransformationEvent",
        "AssociationEvent",
    }
)
ACTION_EVENT_TYPES = frozenset(
    {"ObjectEvent", "AggregationEvent", "TransactionEvent", "AssociationEvent"}
)
ACTIVE_CERT_STATUSES = frozenset({"active", "certified", "current", "valid"})
TIMEZONE_OFFSET = re.compile(r"^[+-](?:0\d|1\d|2[0-3]):[0-5]\d$")
EVENT_RESULT_SCHEMA = "factorytrace.events.v2"
EVENT_ADAPTER_ID = "factorytrace.events.validate_event_chain"
ADAPTER_ENVELOPE_SCHEMA = "factorytrace.adapter-provenance.v2"


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
    certification_hashes: dict[str, str] = {}
    certifications = input_payload.get("certifications", [])
    if isinstance(certifications, list):
        for record in certifications:
            if not isinstance(record, Mapping):
                continue
            identifier = record.get("certificate_id") or record.get(
                "certificationIdentification"
            )
            if identifier is not None and str(identifier).strip():
                certification_hashes[str(identifier).strip()] = _canonical_sha256(
                    record
                )
    provenance = {
        "schema": ADAPTER_ENVELOPE_SCHEMA,
        "adapter_id": EVENT_ADAPTER_ID,
        "adapter_version": 2,
        "input_sha256": _canonical_sha256(input_payload),
        "events_sha256": _canonical_sha256(input_payload.get("events", [])),
        "certification_registry_sha256": _canonical_sha256(certifications),
        "certificate_record_sha256_by_id": certification_hashes,
    }
    provenance["payload_sha256"] = _canonical_sha256(
        _envelope_payload(result, provenance)
    )
    result["adapter_provenance"] = provenance
    return result


def validate_event_result_envelope(result: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the schema, adapter provenance, and payload integrity.

    中文：检查Schema、适配器来源与摘要一致性；结果封装完整不等于原始事件已获独立证明。
    """

    errors: list[str] = []
    if result.get("schema") != EVENT_RESULT_SCHEMA:
        errors.append(f"schema must be {EVENT_RESULT_SCHEMA}")
    provenance = result.get("adapter_provenance")
    if not isinstance(provenance, Mapping):
        errors.append("adapter_provenance is required")
    else:
        if provenance.get("schema") != ADAPTER_ENVELOPE_SCHEMA:
            errors.append(f"adapter provenance schema must be {ADAPTER_ENVELOPE_SCHEMA}")
        if provenance.get("adapter_id") != EVENT_ADAPTER_ID:
            errors.append(f"adapter_id must be {EVENT_ADAPTER_ID}")
        if provenance.get("adapter_version") != 2:
            errors.append("adapter_version must be 2")
        input_hash = str(provenance.get("input_sha256") or "")
        if not re.fullmatch(r"[0-9a-f]{64}", input_hash):
            errors.append("adapter input_sha256 must be a lowercase SHA-256")
        for field in ("events_sha256", "certification_registry_sha256"):
            if not re.fullmatch(r"[0-9a-f]{64}", str(provenance.get(field) or "")):
                errors.append(f"adapter {field} must be a lowercase SHA-256")
        record_hashes = provenance.get("certificate_record_sha256_by_id")
        if not isinstance(record_hashes, Mapping) or any(
            not str(identifier).strip()
            or not re.fullmatch(r"[0-9a-f]{64}", str(digest or ""))
            for identifier, digest in (
                record_hashes.items() if isinstance(record_hashes, Mapping) else []
            )
        ):
            errors.append(
                "adapter certificate_record_sha256_by_id must map certificate IDs to SHA-256"
            )
        expected_payload_hash = _canonical_sha256(
            _envelope_payload(result, provenance)
        )
        if provenance.get("payload_sha256") != expected_payload_hash:
            errors.append("event result payload hash mismatch")
    return {
        "schema": "factorytrace.event-envelope-validation.v2",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def _step(value: Any) -> str:
    rendered = _normal(value).rstrip("/")
    return re.split(r"[:/#]", rendered)[-1] if rendered else ""


def _parse_time(
    value: Any,
    *,
    allow_naive: bool = False,
    end_of_day: bool = False,
) -> datetime | None:
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
    if parsed.tzinfo is None:
        if not allow_naive:
            return None
        if end_of_day and isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()):
            parsed = parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _rendered_offset(value: Any) -> str | None:
    if not value:
        return None
    rendered = str(value).strip()
    if rendered.endswith("Z"):
        rendered = rendered[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(rendered)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    total_minutes = int(parsed.utcoffset().total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    hours, minutes = divmod(abs(total_minutes), 60)
    return f"{sign}{hours:02d}:{minutes:02d}"


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return list(value) if isinstance(value, list) else [value]


def _identifiers(value: Any) -> list[str]:
    result: list[str] = []
    for item in _as_list(value):
        if isinstance(item, Mapping):
            identifier = item.get("epc") or item.get("epcClass") or item.get("id")
        else:
            identifier = item
        if identifier is not None and str(identifier).strip():
            result.append(str(identifier).strip())
    return result


def _event_ids(event: Mapping[str, Any], *fields: str) -> list[str]:
    result: list[str] = []
    for field in fields:
        result.extend(_identifiers(event.get(field)))
    return result


def _site_id(event: Mapping[str, Any]) -> str:
    value = event.get("site_id", event.get("bizLocation"))
    if isinstance(value, Mapping):
        value = value.get("id") or value.get("site_id")
    return str(value or "").strip()


def _certificate_ids(event: Mapping[str, Any]) -> list[str]:
    values = _as_list(event.get("certification_ids"))
    if event.get("certificate_id"):
        values.append(event["certificate_id"])
    return [str(value).strip() for value in values if str(value).strip()]


def _error(
    errors: list[dict[str, Any]],
    code: str,
    event_id: str | None,
    message: str,
    **details: Any,
) -> None:
    item: dict[str, Any] = {"code": code, "event_id": event_id, "message": message}
    if details:
        item["details"] = details
    errors.append(item)


def _certificate_map(
    certifications: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in certifications:
        identifier = item.get("certificate_id") or item.get(
            "certificationIdentification"
        )
        if identifier:
            result[str(identifier).strip()] = dict(item)
    return result


def _detect_dependency_cycles(
    dependencies: Mapping[str, set[str]], errors: list[dict[str, Any]]
) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in visiting:
            cycle_start = path.index(node) if node in path else 0
            cycle = path[cycle_start:] + [node]
            _error(
                errors,
                "DEPENDENCY_CYCLE",
                node,
                "event dependency graph contains a cycle",
                cycle=cycle,
            )
            return
        if node in visited:
            return
        visiting.add(node)
        for predecessor in dependencies.get(node, set()):
            if predecessor in dependencies:
                visit(predecessor, path + [node])
        visiting.remove(node)
        visited.add(node)

    for event_id in dependencies:
        visit(event_id, [])


def validate_event_chain(
    events: Sequence[Mapping[str, Any]],
    certifications: Sequence[Mapping[str, Any]] = (),
    *,
    required_certified_biz_steps: Iterable[str] = (),
    terminal_object_ids: Iterable[str] = (),
) -> dict[str, Any]:
    """Validate EPCIS-style structure plus cross-event manufacturing semantics.

    This intentionally goes beyond JSON-schema validation: event IDs are
    mandatory, object inputs need prior provenance, explicit predecessor links
    must be chronological, and certification-bearing events must occur at an
    authorized site while the certificate is active.

    中文：除JSON结构外，还检查事件ID、前置对象来源、时间顺序与有效认证地点；跨事件语义不能靠结构验证代替。
    """

    event_records = [dict(item) for item in events]
    certification_records = [dict(item) for item in certifications]
    required_steps_input = [str(item) for item in required_certified_biz_steps]
    terminal_ids_input = [str(item) for item in terminal_object_ids]
    adapter_input = {
        "events": event_records,
        "certifications": certification_records,
        "required_certified_biz_steps": required_steps_input,
        "terminal_object_ids": terminal_ids_input,
    }

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    normalized_steps = {_step(value) for value in required_steps_input}
    certs = _certificate_map(certification_records)
    indexed: list[tuple[int, dict[str, Any], str, datetime | None]] = []
    by_id: dict[str, tuple[dict[str, Any], datetime | None]] = {}
    dependencies: dict[str, set[str]] = {}

    for index, raw in enumerate(event_records):
        event = dict(raw)
        event_id = str(event.get("eventID") or "").strip()
        if not event_id:
            synthetic = f"<missing:{index}>"
            _error(errors, "EVENT_ID_REQUIRED", None, "eventID is mandatory", index=index)
            event_id = synthetic
        elif event_id in by_id:
            _error(
                errors,
                "DUPLICATE_EVENT_ID",
                event_id,
                "eventID must be unique within the event set",
            )

        event_type = str(event.get("type") or "").strip()
        if event_type not in EVENT_TYPES:
            _error(
                errors,
                "INVALID_EVENT_TYPE",
                event_id,
                "unsupported or missing EPCIS event type",
                observed=event_type,
            )
        if event_type in ACTION_EVENT_TYPES and _normal(event.get("action")) not in {
            "add",
            "delete",
            "observe",
        }:
            _error(
                errors,
                "ACTION_REQUIRED",
                event_id,
                "event type requires ADD, DELETE, or OBSERVE action",
            )

        event_time = _parse_time(event.get("eventTime"))
        if event_time is None:
            _error(
                errors,
                "EVENT_TIME_INVALID",
                event_id,
                "eventTime must be an ISO-8601 timestamp with timezone",
            )
        offset = str(event.get("eventTimeZoneOffset") or "")
        if not TIMEZONE_OFFSET.fullmatch(offset):
            _error(
                errors,
                "TIMEZONE_OFFSET_REQUIRED",
                event_id,
                "eventTimeZoneOffset must use ±HH:MM",
                observed=offset,
            )
        elif event_time is not None and _rendered_offset(event.get("eventTime")) != offset:
            _error(
                errors,
                "TIMEZONE_OFFSET_MISMATCH",
                event_id,
                "eventTimeZoneOffset does not match the UTC offset encoded in eventTime",
                observed=offset,
                event_time_offset=_rendered_offset(event.get("eventTime")),
            )

        predecessors = {
            str(value).strip()
            for value in _as_list(event.get("predecessorEventIDs"))
            if str(value).strip()
        }
        dependencies[event_id] = predecessors
        indexed.append((index, event, event_id, event_time))
        if event_id not in by_id:
            by_id[event_id] = (event, event_time)

    for _, event, event_id, event_time in indexed:
        for predecessor in dependencies.get(event_id, set()):
            if predecessor not in by_id:
                _error(
                    errors,
                    "ORPHAN_PREDECESSOR",
                    event_id,
                    "predecessorEventID does not exist",
                    predecessor=predecessor,
                )
                continue
            predecessor_time = by_id[predecessor][1]
            if (
                event_time is not None
                and predecessor_time is not None
                and predecessor_time > event_time
            ):
                _error(
                    errors,
                    "PREDECESSOR_TIME_ORDER",
                    event_id,
                    "predecessor occurs after the dependent event",
                    predecessor=predecessor,
                )
    _detect_dependency_cycles(dependencies, errors)

    planned_producers: dict[str, list[tuple[datetime, str]]] = {}
    for _, event, event_id, event_time in indexed:
        if event_time is None:
            continue
        event_type = event.get("type")
        step = _step(event.get("bizStep"))
        action = _normal(event.get("action"))
        produced: list[str] = []
        if event_type == "TransformationEvent":
            produced = _event_ids(event, "outputEPCList", "outputQuantityList")
        elif event_type == "ObjectEvent" and (
            step in {"commissioning", "receiving"} or action == "add"
        ):
            produced = _event_ids(event, "epcList", "quantityList")
        elif event_type == "AggregationEvent" and action == "add":
            produced = _event_ids(event, "parentID")
        for identifier in produced:
            planned_producers.setdefault(identifier, []).append((event_time, event_id))

    known_objects: dict[str, dict[str, Any]] = {}
    lineage: dict[str, dict[str, Any]] = {}
    sorted_events = sorted(
        indexed,
        key=lambda item: (
            item[3] is None,
            item[3] or datetime.max.replace(tzinfo=timezone.utc),
            item[0],
        ),
    )
    observed_steps: set[str] = set()
    referenced_certificate_ids: set[str] = set()
    certified_event_certificate_ids: dict[str, set[str]] = {}

    for _, event, event_id, event_time in sorted_events:
        event_type = event.get("type")
        step = _step(event.get("bizStep"))
        action = _normal(event.get("action"))
        if step:
            observed_steps.add(step)

        inputs: list[str] = []
        outputs: list[str] = []
        observed: list[str] = []
        if event_type == "TransformationEvent":
            inputs = _event_ids(event, "inputEPCList", "inputQuantityList")
            outputs = _event_ids(event, "outputEPCList", "outputQuantityList")
            if not inputs:
                _error(
                    errors,
                    "TRANSFORMATION_INPUT_REQUIRED",
                    event_id,
                    "TransformationEvent must identify at least one input",
                )
            if not outputs:
                _error(
                    errors,
                    "TRANSFORMATION_OUTPUT_REQUIRED",
                    event_id,
                    "TransformationEvent must identify at least one output",
                )
        elif event_type == "ObjectEvent":
            observed = _event_ids(event, "epcList", "quantityList")
            if step in {"commissioning", "receiving"} or action == "add":
                outputs = observed
                observed = []
        elif event_type == "AggregationEvent":
            children = _event_ids(event, "childEPCs", "childQuantityList")
            if action == "add":
                inputs = children
                outputs = _event_ids(event, "parentID")
            else:
                observed = [*_event_ids(event, "parentID"), *children]
        elif event_type in {"TransactionEvent", "AssociationEvent"}:
            observed = _event_ids(
                event,
                "epcList",
                "quantityList",
                "childEPCs",
                "childQuantityList",
            )

        for identifier in [*inputs, *observed]:
            if identifier in known_objects:
                continue
            future = [
                producer
                for producer in planned_producers.get(identifier, [])
                if event_time is not None and producer[0] > event_time
            ]
            if future:
                _error(
                    errors,
                    "OBJECT_TIME_ORDER",
                    event_id,
                    "object is consumed or observed before its producing event",
                    object_id=identifier,
                    future_producers=[producer[1] for producer in future],
                )
            else:
                _error(
                    errors,
                    "ORPHAN_OBJECT",
                    event_id,
                    "object has no prior receiving/commissioning/production event",
                    object_id=identifier,
                )

        for identifier in outputs:
            if identifier in known_objects:
                _error(
                    errors,
                    "DUPLICATE_OBJECT_OUTPUT",
                    event_id,
                    "object identifier was already introduced by an earlier event",
                    object_id=identifier,
                    earlier_event=known_objects[identifier]["event_id"],
                )
            known_objects[identifier] = {
                "event_id": event_id,
                "event_time": event.get("eventTime"),
                "site_id": _site_id(event),
            }
            lineage[identifier] = {
                "produced_by": event_id,
                "inputs": list(inputs),
                "site_id": _site_id(event),
            }

        cert_ids = _certificate_ids(event)
        referenced_certificate_ids.update(cert_ids)
        certification_required = step in normalized_steps
        if certification_required and cert_ids:
            certified_event_certificate_ids.setdefault(step, set()).update(cert_ids)
        if certification_required and not cert_ids:
            _error(
                errors,
                "CERTIFICATION_REQUIRED",
                event_id,
                "this business step requires an explicit certificate reference",
                biz_step=step,
            )
        for cert_id in cert_ids:
            certificate = certs.get(cert_id)
            if certificate is None:
                _error(
                    errors,
                    "UNKNOWN_CERTIFICATE",
                    event_id,
                    "referenced certificate is absent from the supplied registry snapshot",
                    certificate_id=cert_id,
                )
                continue
            if _normal(certificate.get("status")) not in ACTIVE_CERT_STATUSES:
                _error(
                    errors,
                    "CERTIFICATE_INACTIVE",
                    event_id,
                    "certificate was not active",
                    certificate_id=cert_id,
                    status=certificate.get("status"),
                )
            valid_from = _parse_time(
                certificate.get("valid_from"), allow_naive=True
            )
            valid_to = _parse_time(
                certificate.get("valid_to"), allow_naive=True, end_of_day=True
            )
            if valid_from is None or valid_to is None:
                _error(
                    errors,
                    "CERTIFICATE_WINDOW_INVALID",
                    event_id,
                    "certificate validity window is missing or malformed",
                    certificate_id=cert_id,
                )
            elif event_time is not None and not (valid_from <= event_time <= valid_to):
                _error(
                    errors,
                    "CERTIFICATE_OUTSIDE_VALIDITY",
                    event_id,
                    "event occurred outside the certificate validity window",
                    certificate_id=cert_id,
                    event_time=event.get("eventTime"),
                )
            authorized_sites = {
                _normal(value)
                for value in _as_list(certificate.get("authorized_site_ids"))
                if _normal(value)
            }
            site = _normal(_site_id(event))
            if not site or site not in authorized_sites:
                _error(
                    errors,
                    "CERTIFICATE_SITE_MISMATCH",
                    event_id,
                    "event site is not in the certificate's authorized-site set",
                    certificate_id=cert_id,
                    site_id=_site_id(event),
                    authorized_site_ids=sorted(authorized_sites),
                )

        declaration = event.get("errorDeclaration")
        if declaration is not None:
            if not isinstance(declaration, Mapping):
                _error(
                    errors,
                    "ERROR_DECLARATION_INVALID",
                    event_id,
                    "errorDeclaration must be an object",
                )
            else:
                for corrective_id in _as_list(declaration.get("correctiveEventIDs")):
                    if str(corrective_id) not in by_id:
                        _error(
                            errors,
                            "ORPHAN_CORRECTIVE_EVENT",
                            event_id,
                            "correctiveEventID does not exist",
                            corrective_event_id=corrective_id,
                        )

    terminal_reports: list[dict[str, Any]] = []
    for identifier in terminal_ids_input:
        rendered = str(identifier)
        exists = rendered in known_objects
        terminal_reports.append(
            {
                "object_id": rendered,
                "present": exists,
                "lineage": lineage.get(rendered),
            }
        )
        if not exists:
            _error(
                errors,
                "TERMINAL_OBJECT_MISSING",
                None,
                "required terminal object was not produced or received",
                object_id=rendered,
            )

    result = {
        "schema": EVENT_RESULT_SCHEMA,
        "status": "PASS" if not errors else "FAIL",
        "events_checked": len(event_records),
        "unique_event_ids": len(by_id),
        "objects_tracked": len(known_objects),
        "observed_biz_steps": sorted(observed_steps),
        "referenced_certificate_ids": sorted(referenced_certificate_ids),
        "certified_event_certificate_ids": {
            step: sorted(values)
            for step, values in sorted(certified_event_certificate_ids.items())
        },
        "required_certified_biz_steps": sorted(normalized_steps),
        "terminal_objects": terminal_reports,
        "object_lineage": lineage,
        "errors": errors,
        "warnings": warnings,
        "meaning": (
            "PASS confirms internal event-chain semantics for the supplied records. "
            "It does not authenticate the event submitter or prove that reported events occurred."
        ),
    }
    return _attach_adapter_provenance(result, input_payload=adapter_input)
