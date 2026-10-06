"""English: Resolve inherited process requirements and evaluate sealed adapter results.

中文：解析工艺包继承并核验受封装的适配器结果；原始子包不能跳过父级硬门槛，完整性摘要不是可信签名。
"""

from __future__ import annotations

import json
import re
import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

from ._resources import resource_directory
from .certification import validate_certification_result_envelope
from .events import validate_event_result_envelope

PACK_SCHEMA = "factorytrace.process-pack.v2"
PACK_NAME = re.compile(r"^[a-z][a-z0-9_\-]*$")
PACK_RESOLUTION_SCHEMA = "factorytrace.process-pack-resolution.v2"
PACK_LOADER_ID = "factorytrace.process_packs.loader"


class _ResolvedProcessPack(dict[str, Any]):
    """Loader-created, mutation-evident process-pack mapping.

    The type check intentionally prevents a caller from turning an arbitrary
    JSON object into an evaluable pack by adding ``_resolved: true``.  The
    content digest additionally invalidates a pack that was mutated after it
    left the loader.  This is an integrity boundary, not a cryptographic trust
    signature against code executing inside this Python process.

    中文：加载器类型和内容摘要阻止任意JSON伪造已解析工艺包，并发现后续修改；不是抵抗进程内代码的信任签名。
    """


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _pack_payload(pack: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in pack.items()
        if key not in {"_resolved", "_resolution"}
    }


def _seal_resolved_pack(
    pack: Mapping[str, Any],
    *,
    sources: Sequence[Mapping[str, Any]],
    mode: str,
) -> _ResolvedProcessPack:
    sealed = _ResolvedProcessPack(_pack_payload(pack))
    sealed["_resolved"] = True
    sealed["_resolution"] = {
        "schema": PACK_RESOLUTION_SCHEMA,
        "loader_id": PACK_LOADER_ID,
        "loader_version": 2,
        "mode": mode,
        "sources": [dict(item) for item in sources],
        "payload_sha256": _canonical_sha256(_pack_payload(sealed)),
    }
    return sealed


def _resolution_errors(pack: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(pack, _ResolvedProcessPack):
        errors.append(
            "process pack is unresolved: it is not a loader-created resolved instance; reload it "
            "with load_process_pack() or compose_process_packs()"
        )
        return errors
    resolution = pack.get("_resolution")
    if not isinstance(resolution, Mapping):
        return ["process-pack resolution envelope is missing"]
    if resolution.get("schema") != PACK_RESOLUTION_SCHEMA:
        errors.append(f"resolution schema must be {PACK_RESOLUTION_SCHEMA}")
    if resolution.get("loader_id") != PACK_LOADER_ID:
        errors.append(f"resolution loader_id must be {PACK_LOADER_ID}")
    if resolution.get("loader_version") != 2:
        errors.append("resolution loader_version must be 2")
    expected_hash = _canonical_sha256(_pack_payload(pack))
    if resolution.get("payload_sha256") != expected_hash:
        errors.append("process-pack payload changed after loader resolution")
    sources = resolution.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("resolution sources must contain at least one source digest")
    elif any(
        not isinstance(item, Mapping)
        or not PACK_NAME.fullmatch(str(item.get("pack_id") or ""))
        or not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256") or ""))
        for item in sources
    ):
        errors.append("resolution sources contain an invalid pack_id or SHA-256")

    extends = pack.get("extends", [])
    declared_bases = set(extends) if isinstance(extends, list) else set()
    inheritance = pack.get("resolved_inheritance", [])
    resolved_bases = set(inheritance) if isinstance(inheritance, list) else set()
    missing_bases = sorted(declared_bases - resolved_bases)
    if missing_bases:
        errors.append(
            "unresolved extends entries: " + ", ".join(str(item) for item in missing_bases)
        )
    return errors


def default_pack_dir() -> Path:
    return resource_directory("process_packs")


def _normal(value: Any) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def _unique(values: Sequence[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True)
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _merge(base: Any, overlay: Any) -> Any:
    if isinstance(base, Mapping) and isinstance(overlay, Mapping):
        result = {key: value for key, value in base.items()}
        for key, value in overlay.items():
            result[key] = _merge(result[key], value) if key in result else value
        return result
    if isinstance(base, list) and isinstance(overlay, list):
        return _unique([*base, *overlay])
    return overlay


def validate_process_pack(pack: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    pack_id = str(pack.get("pack_id") or "")
    if pack.get("schema") != PACK_SCHEMA:
        errors.append(f"schema must be {PACK_SCHEMA}")
    if not PACK_NAME.fullmatch(pack_id):
        errors.append("pack_id must match ^[a-z][a-z0-9_-]*$")
    if not isinstance(pack.get("version"), int) or int(pack.get("version", 0)) < 1:
        errors.append("version must be a positive integer")
    if not str(pack.get("description") or "").strip():
        errors.append("description is required")

    for field in (
        "required_processes",
        "required_evidence",
        "required_photos",
        "required_documents",
    ):
        value = pack.get(field, [])
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            errors.append(f"{field} must be a list of non-empty strings")

    certification = pack.get("certification", {})
    if not isinstance(certification, Mapping):
        errors.append("certification must be an object")
    else:
        if certification.get("mode", "all") not in {"all", "any"}:
            errors.append("certification.mode must be all or any")
        for field in ("schemes", "hard_gates"):
            value = certification.get(field, [])
            if not isinstance(value, list) or not all(
                isinstance(item, str) and item.strip() for item in value
            ):
                errors.append(f"certification.{field} must be a string list")
        schemes = certification.get("schemes", [])
        hard_gates = certification.get("hard_gates", [])
        if (
            isinstance(schemes, list)
            and schemes
            and isinstance(hard_gates, list)
            and not hard_gates
        ):
            errors.append(
                "certification.hard_gates must be non-empty when certification.schemes is non-empty"
            )

    extends = pack.get("extends", [])
    if not isinstance(extends, list) or not all(
        isinstance(item, str) and PACK_NAME.fullmatch(item) for item in extends
    ):
        errors.append("extends must be a list of valid process-pack names")

    events = pack.get("events", {})
    if not isinstance(events, Mapping):
        errors.append("events must be an object")
    else:
        for field in ("required_biz_steps", "certified_biz_steps"):
            value = events.get(field, [])
            if not isinstance(value, list) or not all(
                isinstance(item, str) and item.strip() for item in value
            ):
                errors.append(f"events.{field} must be a string list")

    social = pack.get("social", {})
    if not isinstance(social, Mapping):
        errors.append("social must be an object")
    elif social.get("maximum_authority", "entity_identity") != "entity_identity":
        warnings.append(
            "social.maximum_authority should remain entity_identity; social evidence cannot certify production"
        )

    return {
        "schema": "factorytrace.process-pack-validation.v2",
        "status": "PASS" if not errors else "FAIL",
        "pack_id": pack_id,
        "errors": errors,
        "warnings": warnings,
    }


def _pack_path(name: str, pack_dir: Path) -> Path:
    if not PACK_NAME.fullmatch(name):
        raise ValueError(f"invalid process-pack name: {name!r}")
    candidates = [
        (pack_dir / f"{name}{suffix}").resolve()
        for suffix in (".json", ".yaml", ".yml")
        if (pack_dir / f"{name}{suffix}").is_file()
    ]
    if len(candidates) > 1:
        raise ValueError(
            f"ambiguous process pack {name!r}; keep only one of JSON/YAML/YML"
        )
    path = candidates[0] if candidates else (pack_dir / f"{name}.json").resolve()
    try:
        path.relative_to(pack_dir.resolve())
    except ValueError as exc:
        raise ValueError("process-pack path escapes the configured directory") from exc
    return path


def _read_pack(path: Path) -> Any:
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    try:
        import yaml
    except ImportError as error:
        raise RuntimeError(
            "YAML process packs require the 'packs' or 'full' extra: "
            "python -m pip install 'factory-trace-toolkit[packs]'"
        ) from error
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as error:  # Normalize parser-specific YAML errors. / 中文：统一不同解析器的YAML异常。
        raise ValueError(f"invalid YAML process pack {path}: {error}") from error


def _load(
    name: str,
    pack_dir: Path,
    stack: tuple[str, ...],
) -> dict[str, Any]:
    if name in stack:
        raise ValueError(f"circular process-pack inheritance: {' -> '.join((*stack, name))}")
    path = _pack_path(name, pack_dir)
    if not path.is_file():
        raise FileNotFoundError(f"process pack not found: {path}")
    raw = _read_pack(path)
    if not isinstance(raw, dict):
        raise ValueError(f"process pack must be a JSON object: {path}")
    if raw.get("pack_id") != name:
        raise ValueError(f"pack_id {raw.get('pack_id')!r} does not match filename {name!r}")

    bases = raw.get("extends", [])
    if isinstance(bases, str):
        bases = [bases]
    if not isinstance(bases, list) or not all(isinstance(item, str) for item in bases):
        raise ValueError("extends must be a string list")
    if not all(PACK_NAME.fullmatch(item) for item in bases):
        raise ValueError("extends entries must be valid process-pack names")
    raw = dict(raw)
    raw["extends"] = list(bases)
    resolved: dict[str, Any] = {}
    inheritance: list[str] = []
    resolution_sources: list[dict[str, Any]] = []
    for base_name in bases:
        base = _load(base_name, pack_dir, (*stack, name))
        resolved = _merge(resolved, base)
        inheritance.extend(base.get("resolved_inheritance", [base_name]))
        inheritance.append(base_name)
        base_resolution = base.get("_resolution", {})
        if isinstance(base_resolution, Mapping):
            resolution_sources.extend(
                dict(item)
                for item in base_resolution.get("sources", [])
                if isinstance(item, Mapping)
            )
    resolved = _merge(resolved, raw)
    resolved["resolved_inheritance"] = _unique(inheritance)
    resolved["source_path"] = str(path)
    # Evaluation is intentionally restricted to packs that passed the loader's
    # inheritance resolution.  A raw child pack can otherwise appear valid
    # while silently omitting hard gates inherited from its parent.
    # 中文：必须先解析继承；直接评估原始子包可能漏掉父级硬门槛而产生假通过。
    validation = validate_process_pack(resolved)
    if validation["status"] != "PASS":
        raise ValueError(
            f"invalid process pack {name}: " + "; ".join(validation["errors"])
        )
    resolution_sources.append(
        {
            "pack_id": name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    )
    unique_sources: list[dict[str, Any]] = []
    seen_source: set[tuple[str, str]] = set()
    for item in resolution_sources:
        key = (str(item.get("pack_id") or ""), str(item.get("sha256") or ""))
        if key not in seen_source:
            seen_source.add(key)
            unique_sources.append(item)
    return _seal_resolved_pack(resolved, sources=unique_sources, mode="load")


def load_process_pack(
    name: str,
    *,
    pack_dir: Path | None = None,
) -> dict[str, Any]:
    return _load(name, (pack_dir or default_pack_dir()).resolve(), ())


def compose_process_packs(
    names: Sequence[str],
    *,
    pack_dir: Path | None = None,
) -> dict[str, Any]:
    if not names:
        raise ValueError("at least one process-pack name is required")
    directory = (pack_dir or default_pack_dir()).resolve()
    combined: dict[str, Any] = {}
    resolution_sources: list[dict[str, Any]] = []
    for name in names:
        loaded = load_process_pack(name, pack_dir=directory)
        combined = _merge(combined, loaded)
        resolution = loaded.get("_resolution", {})
        if isinstance(resolution, Mapping):
            resolution_sources.extend(
                dict(item)
                for item in resolution.get("sources", [])
                if isinstance(item, Mapping)
            )
    combined["pack_id"] = "__".join(names)
    combined["composed_from"] = list(names)
    combined["source_path"] = None
    validation = validate_process_pack(combined)
    if validation["status"] != "PASS":
        raise ValueError(
            "invalid composed process pack: " + "; ".join(validation["errors"])
        )
    unique_sources: list[dict[str, Any]] = []
    seen_source: set[tuple[str, str]] = set()
    for item in resolution_sources:
        key = (str(item.get("pack_id") or ""), str(item.get("sha256") or ""))
        if key not in seen_source:
            seen_source.add(key)
            unique_sources.append(item)
    return _seal_resolved_pack(combined, sources=unique_sources, mode="compose")


def list_process_packs(*, pack_dir: Path | None = None) -> dict[str, Any]:
    directory = (pack_dir or default_pack_dir()).resolve()
    packs: list[dict[str, Any]] = []
    if directory.is_dir():
        paths = sorted(
            [
                *directory.glob("*.json"),
                *directory.glob("*.yaml"),
                *directory.glob("*.yml"),
            ]
        )
        for path in paths:
            try:
                pack = load_process_pack(path.stem, pack_dir=directory)
                packs.append(
                    {
                        "pack_id": pack["pack_id"],
                        "version": pack["version"],
                        "description": pack["description"],
                        "extends": pack.get("extends", []),
                        "path": str(path),
                        "status": "PASS",
                    }
                )
            except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
                packs.append(
                    {
                        "pack_id": path.stem,
                        "path": str(path),
                        "status": "FAIL",
                        "error": str(exc),
                    }
                )
    return {
        "schema": "factorytrace.process-pack-index.v2",
        "pack_dir": str(directory),
        "packs": packs,
        "status": "PASS" if all(item["status"] == "PASS" for item in packs) else "FAIL",
    }


def _set(value: Any) -> set[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return {_normal(item) for item in value if _normal(item)}
    normalized = _normal(value)
    return {normalized} if normalized else set()


def _result_gate(passed: bool, expected: Any, observed: Any, reason: str) -> dict[str, Any]:
    return {
        "passed": bool(passed),
        "expected": expected,
        "observed": observed,
        "reason": reason,
    }


def evaluate_process_pack(
    pack: Mapping[str, Any],
    facts: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluate data-driven process requirements against adapter results.

    中文：将已解析工艺包的门槛逐项对照适配器结果；缺失、篡改或未经加载器封装的结果不能通过。
    """

    resolution_errors = _resolution_errors(pack)
    if resolution_errors:
        return {
            "schema": "factorytrace.process-pack-evaluation.v2",
            "status": "FAIL",
            "pack_id": pack.get("pack_id"),
            "gates": {},
            "errors": resolution_errors,
        }

    validation = validate_process_pack(pack)
    if validation["status"] != "PASS":
        return {
            "schema": "factorytrace.process-pack-evaluation.v2",
            "status": "FAIL",
            "pack_id": pack.get("pack_id"),
            "gates": {},
            "errors": validation["errors"],
        }

    observed_processes = _set(facts.get("observed_processes"))
    expected_processes = _set(pack.get("required_processes"))
    observed_evidence = _set(facts.get("evidence_types"))
    expected_evidence = _set(pack.get("required_evidence"))
    observed_photos = _set(facts.get("photo_types"))
    expected_photos = _set(pack.get("required_photos"))
    observed_documents = _set(facts.get("document_types"))
    expected_documents = _set(pack.get("required_documents"))

    event_result = facts.get("event_result", {})
    if not isinstance(event_result, Mapping):
        event_result = {}
    event_envelope = validate_event_result_envelope(event_result)
    event_envelope_pass = event_envelope["status"] == "PASS"
    observed_steps = _set(event_result.get("observed_biz_steps"))
    expected_steps = _set(pack.get("events", {}).get("required_biz_steps", []))

    cert_results_value = facts.get("certification_results", [])
    cert_results = (
        [item for item in cert_results_value if isinstance(item, Mapping)]
        if isinstance(cert_results_value, list)
        else []
    )
    certification = pack.get("certification", {})
    expected_schemes = _set(certification.get("schemes", []))
    required_cert_gates = list(certification.get("hard_gates", []))
    passing_schemes: set[str] = set()
    passing_certificate_ids: dict[str, set[str]] = {}
    passing_certificate_hashes: dict[str, dict[str, str]] = {}
    certification_details: list[dict[str, Any]] = []
    for result in cert_results:
        envelope = validate_certification_result_envelope(result)
        envelope_pass = envelope["status"] == "PASS"
        scheme = _normal(result.get("scheme"))
        result_gates = result.get("gates", {})
        named_gates_pass = all(
            isinstance(result_gates.get(name), Mapping)
            and bool(result_gates[name].get("passed"))
            for name in required_cert_gates
        )
        passed = (
            envelope_pass
            and result.get("status") == "PASS"
            and named_gates_pass
        )
        certificate_id = str(result.get("certificate_id") or "").strip()
        provenance = result.get("adapter_provenance", {})
        record_sha256 = (
            str(provenance.get("record_sha256") or "")
            if isinstance(provenance, Mapping)
            else ""
        )
        if passed and scheme:
            passing_schemes.add(scheme)
            if certificate_id:
                passing_certificate_ids.setdefault(scheme, set()).add(certificate_id)
                passing_certificate_hashes.setdefault(scheme, {})[
                    certificate_id
                ] = record_sha256
        certification_details.append(
            {
                "scheme": result.get("scheme"),
                "certificate_id": certificate_id or None,
                "certificate_record_sha256": record_sha256 or None,
                "passed": passed,
                "adapter_envelope_status": envelope["status"],
                "adapter_envelope_errors": envelope["errors"],
                "missing_required_gates": [
                    name
                    for name in required_cert_gates
                    if not (
                        isinstance(result_gates.get(name), Mapping)
                        and bool(result_gates[name].get("passed"))
                    )
                ],
            }
        )
    cert_mode = certification.get("mode", "all")
    if not expected_schemes:
        certs_pass = True
    elif cert_mode == "all":
        certs_pass = expected_schemes <= passing_schemes
    else:
        certs_pass = bool(expected_schemes & passing_schemes)

    referenced_certificate_ids = {
        str(item).strip()
        for item in event_result.get("referenced_certificate_ids", [])
        if str(item).strip()
    }
    event_provenance = event_result.get("adapter_provenance", {})
    event_certificate_hashes = (
        event_provenance.get("certificate_record_sha256_by_id", {})
        if isinstance(event_provenance, Mapping)
        else {}
    )
    if not isinstance(event_certificate_hashes, Mapping):
        event_certificate_hashes = {}
    scheme_bindings: dict[str, list[str]] = {}
    hash_mismatches: dict[str, list[str]] = {}
    for scheme in sorted(expected_schemes):
        referenced = (
            passing_certificate_ids.get(scheme, set()) & referenced_certificate_ids
        )
        scheme_bindings[scheme] = sorted(
            identifier
            for identifier in referenced
            if passing_certificate_hashes.get(scheme, {}).get(identifier)
            == event_certificate_hashes.get(identifier)
        )
        hash_mismatches[scheme] = sorted(
            identifier
            for identifier in referenced
            if passing_certificate_hashes.get(scheme, {}).get(identifier)
            != event_certificate_hashes.get(identifier)
        )
    if not expected_schemes:
        certificate_event_binding_pass = True
    elif cert_mode == "all":
        certificate_event_binding_pass = all(scheme_bindings.get(scheme) for scheme in expected_schemes)
    else:
        certificate_event_binding_pass = any(scheme_bindings.get(scheme) for scheme in expected_schemes)

    gates = {
        "required_processes": _result_gate(
            expected_processes <= observed_processes,
            sorted(expected_processes),
            sorted(observed_processes),
            "all process-pack target processes must be explicitly observed",
        ),
        "required_evidence": _result_gate(
            expected_evidence <= observed_evidence,
            sorted(expected_evidence),
            sorted(observed_evidence),
            "all evidence categories required by the pack must be present",
        ),
        "required_photos": _result_gate(
            expected_photos <= observed_photos,
            sorted(expected_photos),
            sorted(observed_photos),
            "required photographic views must be present",
        ),
        "required_documents": _result_gate(
            expected_documents <= observed_documents,
            sorted(expected_documents),
            sorted(observed_documents),
            "required controlled documents must be present",
        ),
        "certification_adapter_envelopes": _result_gate(
            (
                not expected_schemes
                and not cert_results
            )
            or (
                bool(cert_results)
                and all(
                    item["adapter_envelope_status"] == "PASS"
                    for item in certification_details
                )
            ),
            "every certification result must be an intact factorytrace certification adapter envelope",
            certification_details,
            "schema-less, wrong-adapter, and payload-edited certification results are rejected",
        ),
        "certification_schemes": _result_gate(
            certs_pass,
            {"mode": cert_mode, "schemes": sorted(expected_schemes)},
            {
                "passing_schemes": sorted(passing_schemes),
                "results": certification_details,
            },
            "certification results must pass their exact-scope hard gates",
        ),
        "certificate_event_binding": _result_gate(
            certs_pass
            and event_envelope_pass
            and event_result.get("status") == "PASS"
            and certificate_event_binding_pass,
            {
                "mode": cert_mode,
                "schemes": sorted(expected_schemes),
                "requirement": "a passing certificate ID for every required scheme must be referenced by the validated event chain",
            },
            {
                "referenced_certificate_ids": sorted(referenced_certificate_ids),
                "passing_certificate_ids_by_scheme": {
                    scheme: sorted(values)
                    for scheme, values in sorted(passing_certificate_ids.items())
                },
                "matched_ids_by_scheme": scheme_bindings,
                "certificate_record_hash_mismatches_by_scheme": hash_mismatches,
                "event_certificate_record_sha256_by_id": dict(event_certificate_hashes),
            },
            "validated production events may bind only to the identical certificate registry records evaluated by the certification adapter",
        ),
        "event_chain": _result_gate(
            event_envelope_pass
            and event_result.get("status") == "PASS"
            and expected_steps <= observed_steps,
            sorted(expected_steps),
            {
                "event_status": event_result.get("status"),
                "adapter_envelope_status": event_envelope["status"],
                "adapter_envelope_errors": event_envelope["errors"],
                "observed_biz_steps": sorted(observed_steps),
            },
            "event validator must pass and include every required business step",
        ),
        "event_adapter_envelope": _result_gate(
            event_envelope_pass,
            "an intact factorytrace event adapter envelope",
            event_envelope,
            "schema-less, wrong-adapter, and payload-edited event results are rejected",
        ),
    }
    failed = [name for name, gate in gates.items() if not gate["passed"]]
    return {
        "schema": "factorytrace.process-pack-evaluation.v2",
        "status": "PASS" if not failed else "FAIL",
        "pack_id": pack.get("pack_id"),
        "version": pack.get("version"),
        "gates": gates,
        "failed_gates": failed,
        "social_authority_ceiling": pack.get("social", {}).get(
            "maximum_authority", "entity_identity"
        ),
        "meaning": (
            "PASS means supplied adapter results satisfy this data pack. It remains "
            "an evidence-completeness decision, not a statistical factory probability."
        ),
    }
