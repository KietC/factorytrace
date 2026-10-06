"""English: Separate evidence sufficiency, capability, trace stage, and procurement utility.

中文：分别评估证据充分度、能力、归因阶段与采购价值；这些指标不是统计概率，未知认证条件不能当作通过。
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from .common import utc_now
from .scoring import SOURCE, calculate_ess, evidence_signal, source_cluster_key


HYPOTHESES: dict[str, str] = {
    "H1": "The named legal entity at the claimed site made the exact target product/process.",
    "H2": "The site is technically capable but has no demonstrated target-product supply link.",
    "H3": "The entity is a brand, licence holder, assembler, exporter, or trader rather than the source factory.",
    "H4": "The entity/site is an upstream tooling, blank, or critical-component subcontractor.",
    "H5": "The apparent product link comes from reposted, customer, or outsourced-factory media.",
}

TRACE_STAGES = (
    "S0_UNLINKED",
    "S1_EXACT_PRODUCT_MATCH",
    "S2_AUTHORIZED_SITE",
    "S3_PROCESS_CONFIRMED",
    "S4_BATCH_LINKED",
)

_REJECTED_REVIEW_STATES = {"rejected", "superseded"}
_AUTHORITATIVE_CLASSES = {
    "certifier",
    "government",
    "buyer_document",
    "independent_audit",
    "supplier_live",
    "logistics",
    "trade_data",
}


def _usable_evidence(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    raw = candidate.get("evidence", [])
    if not isinstance(raw, list):
        raise ValueError("candidate.evidence must be a list")
    return [
        item
        for item in raw
        if isinstance(item, dict)
        and item.get("review_status") not in _REJECTED_REVIEW_STATES
    ]


def _support(item: dict[str, Any]) -> bool:
    return item.get("stance") == "support"


def _explicit_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "yes", "verified", "confirmed", "pass"}:
            return True
        if normalized in {"false", "no", "unverified", "failed", "fail"}:
            return False
    return None


def _normalise_mainland_status(candidate: dict[str, Any]) -> bool | str:
    value = candidate.get("verified_mainland_site")
    if value is None and isinstance(candidate.get("geography"), dict):
        # Only an explicit verification field is accepted. Address text,
        # jurisdiction classes, and multipliers are intentionally ignored.
        # 中文：只接受明确的验证字段，地址文字、地区分类和倍率不能代替已核实地点。
        value = candidate["geography"].get("verified_mainland_site")
    parsed = _explicit_bool(value)
    return parsed if parsed is not None else "unknown"


def _certification_records(candidate: dict[str, Any]) -> dict[str, Any]:
    raw = candidate.get("certification", {})
    return raw if isinstance(raw, dict) else {}


def _scheme_record(
    scheme: str,
    candidate: dict[str, Any],
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    records = _certification_records(candidate)
    raw = records.get(scheme, {})
    if not isinstance(raw, dict):
        raw = {"status": str(raw)} if raw else {}
    status_text = str(raw.get("status") or raw.get("state") or "").strip()
    upper_status = status_text.upper()
    if any(token in upper_status for token in ("INACTIVE", "EXPIRED", "REVOKED", "CANCELLED")):
        active: bool | None = False
    elif "ACTIVE" in upper_status or upper_status in {"CURRENT", "VALID", "LISTED", "CERTIFIED"}:
        active = True
    else:
        active = _explicit_bool(raw.get("active"))

    exact_key_present = any(
        key in raw for key in ("target_exact_match", "exact_product_match", "exact_model_match")
    )
    exact_product = _explicit_bool(
        raw.get(
            "target_exact_match",
            raw.get("exact_product_match", raw.get("exact_model_match")),
        )
    )
    authorized_site = _explicit_bool(
        raw.get(
            "authorized_site_confirmed",
            raw.get("manufacturing_site_confirmed", raw.get("site_confirmed")),
        )
    )
    complete_product = _explicit_bool(raw.get("complete_product"))
    certification_type = str(
        raw.get("certification_type") or raw.get("product_scope") or ""
    ).casefold()
    if any(token in certification_type for token in ("recognized component", "component_only", "component only")):
        complete_product = False

    scheme_evidence = []
    for item in evidence:
        if not _support(item) or item.get("source_class") != "certifier":
            continue
        declared_scheme = str(item.get("certification_scheme") or "").casefold()
        searchable = " ".join(
            str(item.get(key) or "")
            for key in ("source_title", "issuer", "observed_fact")
        ).casefold()
        if declared_scheme == scheme.casefold() or scheme.casefold() in searchable:
            scheme_evidence.append(item)
    if exact_product is None and not exact_key_present:
        exact_product = any(item.get("sku_bind") == "exact" for item in scheme_evidence) or None
    if authorized_site is None:
        authorized_site = any(item.get("site_bind") == "exact" for item in scheme_evidence) or None
    if complete_product is None:
        complete_product = any(
            "complete" in str(item.get("component") or "").casefold()
            or "complete" in str(item.get("role") or "").casefold()
            for item in scheme_evidence
        ) or None

    if complete_product is False:
        state = "COMPONENT_ONLY"
    elif active is False:
        state = "INACTIVE"
    elif exact_product is False:
        state = "MISMATCH_OR_FAMILY_ONLY"
    elif active is True and exact_product is True and authorized_site is True and complete_product is True:
        state = "ACTIVE_EXACT_SITE_COMPLETE"
    elif active is True and exact_product is True:
        state = "ACTIVE_EXACT_SITE_OPEN"
    elif active is True:
        state = "ACTIVE_SCOPE_OPEN"
    elif raw or scheme_evidence:
        state = "UNRESOLVED"
    else:
        state = "UNPROVEN"
    return {
        "state": state,
        "active": active,
        "exact_product": exact_product,
        "authorized_manufacturing_site": authorized_site,
        "complete_product": complete_product,
        "record_present": bool(raw or scheme_evidence),
        "record_id": str(
            raw.get("file_number")
            or raw.get("certificate")
            or raw.get("certificate_number")
            or ""
        ),
        "notice": (
            "A licence holder/listee is not treated as the manufacturer; exact product, "
            "complete-product scope, active status, and authorized site are separate gates."
        ),
    }


def certification_state(
    candidate: dict[str, Any], evidence: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    evidence = _usable_evidence(candidate) if evidence is None else evidence
    ul = _scheme_record("ul", candidate, evidence)
    watermark = _scheme_record("watermark", candidate, evidence)
    states = (ul, watermark)
    if all(
        item["active"] is True
        and item["exact_product"] is True
        and item["authorized_manufacturing_site"] is True
        and item["complete_product"] is True
        for item in states
    ):
        dual_gate = "PASS"
    elif any(
        item["active"] is False
        or item["exact_product"] is False
        or item["complete_product"] is False
        for item in states
    ):
        dual_gate = "FAIL"
    else:
        dual_gate = "OPEN"
    return {
        "ul": ul,
        "watermark": watermark,
        "dual_certification_gate": dual_gate,
        "dual_gate_notice": (
            "UL and WaterMark are independent AND gates; models, ratings, material, "
            "complete-product scope, active status, and manufacturing site cannot be borrowed."
        ),
    }


def _trace_stage(
    candidate: dict[str, Any],
    evidence: list[dict[str, Any]],
    cert_state: dict[str, Any],
) -> tuple[str, dict[str, bool]]:
    """Advance only through exact product, authorized site, process, and batch gates.

    中文：仅在具体产品、授权地点、目标工序与批次链逐级闭合后升级归因阶段；设备能力本身不能跨级。
    """
    target_processes = set(candidate.get("target_processes", []))
    exact_product = any(
        _support(item)
        and item.get("dimension") in {"exact_sku_process", "commercial_batch_chain"}
        and item.get("sku_bind") == "exact"
        and SOURCE.get(item.get("source_class", ""), 0) >= 0.4
        for item in evidence
    ) or any(
        cert_state[scheme]["active"] is True
        and cert_state[scheme]["exact_product"] is True
        for scheme in ("ul", "watermark")
    )
    authorized_site = exact_product and (
        any(
            _support(item)
            and item.get("dimension") == "certification_manufacturing_site"
            and item.get("site_bind") == "exact"
            and item.get("sku_bind") == "exact"
            and item.get("source_class") in {"certifier", "independent_audit", "government"}
            for item in evidence
        )
        or any(
            cert_state[scheme]["active"] is True
            and cert_state[scheme]["exact_product"] is True
            and cert_state[scheme]["authorized_manufacturing_site"] is True
            for scheme in ("ul", "watermark")
        )
    )
    process_confirmed = authorized_site and any(
        _support(item)
        and item.get("dimension") == "exact_sku_process"
        and item.get("sku_bind") == "exact"
        and item.get("site_bind") == "exact"
        and item.get("strength") in {"direct", "strong"}
        and item.get("source_class") in _AUTHORITATIVE_CLASSES
        and (not target_processes or item.get("process") in target_processes)
        for item in evidence
    )
    batch_linked = process_confirmed and any(
        _support(item)
        and item.get("dimension") == "commercial_batch_chain"
        and item.get("sku_bind") == "exact"
        and item.get("site_bind") == "exact"
        and bool(str(item.get("batch_id") or "").strip())
        and item.get("source_class") in {"buyer_document", "logistics", "trade_data", "independent_audit"}
        for item in evidence
    )
    checks = {
        "exact_product_match": bool(exact_product),
        "authorized_site": bool(authorized_site),
        "target_process_confirmed": bool(process_confirmed),
        "batch_linked": bool(batch_linked),
    }
    if batch_linked:
        stage = "S4_BATCH_LINKED"
    elif process_confirmed:
        stage = "S3_PROCESS_CONFIRMED"
    elif authorized_site:
        stage = "S2_AUTHORIZED_SITE"
    elif exact_product:
        stage = "S1_EXACT_PRODUCT_MATCH"
    else:
        stage = "S0_UNLINKED"
    return stage, checks


def _capability_fit(candidate: dict[str, Any], evidence: list[dict[str, Any]]) -> tuple[float, dict[str, Any]]:
    targets = set(candidate.get("target_processes", []))
    by_process: dict[str, dict[str, float]] = defaultdict(dict)
    contradiction = 0.0
    for index, item in enumerate(evidence):
        if item.get("dimension") not in {"physical_site_process", "exact_sku_process"}:
            continue
        if item.get("site_bind") not in {"exact", "partial"}:
            continue
        process = str(item.get("process") or "unknown")
        cluster = source_cluster_key(item, index)
        signal = evidence_signal(item)
        if item.get("stance") == "support":
            by_process[process][cluster] = max(by_process[process].get(cluster, 0.0), signal)
        elif item.get("stance") == "contradict":
            contradiction += signal
    strengths = {
        process: max(groups.values(), default=0.0) for process, groups in by_process.items()
    }
    if targets:
        covered = {process for process in targets if strengths.get(process, 0.0) > 0}
        coverage = len(covered) / len(targets)
        best = max((strengths.get(process, 0.0) for process in targets), default=0.0)
    else:
        covered = {process for process, value in strengths.items() if value > 0}
        values = sorted(strengths.values(), reverse=True)[:3]
        coverage = min(1.0, len(covered) / 3) if covered else 0.0
        best = sum(values) / len(values) if values else 0.0
    score = max(0.0, min(100.0, best * 70 + coverage * 30 - contradiction * 20))
    return round(score, 2), {
        "target_processes": sorted(targets),
        "covered_target_processes": sorted(covered),
        "process_signal": {key: round(value, 4) for key, value in sorted(strengths.items())},
        "notice": (
            "Capability fit measures whether the site could perform the process. It does not "
            "prove that the site made or supplied the target product."
        ),
    }


def _analytic_confidence(
    candidate: dict[str, Any], evidence: list[dict[str, Any]]
) -> tuple[str, float, list[str]]:
    attribution_items = [
        item
        for item in evidence
        if item.get("dimension") in {
            "entity_chain",
            "exact_sku_process",
            "commercial_batch_chain",
            "certification_manufacturing_site",
        }
        or (
            item.get("dimension") == "physical_site_process"
            and item.get("sku_bind") == "exact"
        )
    ]
    groups: dict[str, float] = {}
    exact_groups: set[str] = set()
    contradict_groups: set[str] = set()
    for index, item in enumerate(attribution_items):
        cluster = source_cluster_key(item, index)
        groups[cluster] = max(
            groups.get(cluster, 0.0), SOURCE.get(item.get("source_class", ""), 0.15)
        )
        if item.get("sku_bind") == "exact" and item.get("site_bind") == "exact":
            exact_groups.add(cluster)
        if item.get("stance") == "contradict":
            contradict_groups.add(cluster)
    average_quality = sum(groups.values()) / len(groups) if groups else 0.0
    score = min(100.0, average_quality * 55 + min(4, len(groups)) * 8 + min(2, len(exact_groups)) * 8)
    score -= min(30.0, len(contradict_groups) * 12.0)
    unresolved_critical = sum(
        1
        for flag in candidate.get("red_flags", [])
        if isinstance(flag, dict)
        and flag.get("severity") == "critical"
        and flag.get("status") != "resolved"
    )
    if unresolved_critical:
        score = min(score, 49.0)
    score = max(0.0, score)
    level = "HIGH" if score >= 70 else "MODERATE" if score >= 40 else "LOW"
    basis = [
        f"{len(groups)} independent attribution source cluster(s)",
        f"{len(exact_groups)} cluster(s) bind exact SKU and site",
        f"{len(contradict_groups)} contradictory cluster(s)",
    ]
    if unresolved_critical:
        basis.append(f"{unresolved_critical} unresolved critical red flag(s) cap confidence")
    return level, round(score, 2), basis


def _explicit_hypothesis_effect(item: dict[str, Any], hypothesis_id: str) -> int | None:
    effects = item.get("hypothesis_effects")
    if not isinstance(effects, dict) or hypothesis_id not in effects:
        return None
    value = str(effects[hypothesis_id]).casefold()
    if value in {"support", "supports", "consistent"}:
        return 1
    if value in {"contradict", "contradicts", "inconsistent"}:
        return -1
    return 0


def _heuristic_hypothesis_effect(item: dict[str, Any], hypothesis_id: str) -> int:
    dimension = str(item.get("dimension") or "")
    source = str(item.get("source_class") or "")
    process = str(item.get("process") or "").casefold()
    role = str(item.get("role") or "").casefold()
    component = str(item.get("component") or "").casefold()
    exact = item.get("sku_bind") == "exact" and item.get("site_bind") == "exact"
    batch = dimension == "commercial_batch_chain" and bool(str(item.get("batch_id") or "").strip())
    capability_only = dimension == "physical_site_process" and item.get("sku_bind") != "exact"
    licence_or_trade = any(token in role for token in ("licence", "listee", "trader", "exporter", "brand"))
    upstream = process == "tooling" or "component" in role or "component" in component or "blank" in component
    media_only = source in {"platform", "media", "self_published", "search_snippet"} and item.get("sku_bind") != "exact"
    effect = 0
    if hypothesis_id == "H1":
        effect = 1 if exact or batch else 0
    elif hypothesis_id == "H2":
        effect = 1 if capability_only else -1 if exact or batch else 0
    elif hypothesis_id == "H3":
        effect = 1 if licence_or_trade or (dimension == "entity_chain" and item.get("site_bind") == "none") else -1 if exact or batch else 0
    elif hypothesis_id == "H4":
        effect = 1 if upstream else -1 if exact and "complete" in component else 0
    elif hypothesis_id == "H5":
        effect = 1 if media_only else -1 if exact and source in _AUTHORITATIVE_CLASSES else 0
    if item.get("stance") == "contradict":
        effect *= -1
    return effect


def build_ach(candidate: dict[str, Any], evidence: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    evidence = _usable_evidence(candidate) if evidence is None else evidence
    clustered: dict[str, dict[str, tuple[int, float, str]]] = defaultdict(dict)
    for index, item in enumerate(evidence):
        if item.get("stance") not in {"support", "contradict"}:
            continue
        cluster = source_cluster_key(item, index)
        for hypothesis_id in HYPOTHESES:
            effect = _explicit_hypothesis_effect(item, hypothesis_id)
            if effect is None:
                effect = _heuristic_hypothesis_effect(item, hypothesis_id)
            if effect == 0:
                continue
            weight = evidence_signal(item)
            previous = clustered[cluster].get(hypothesis_id)
            if previous is None or weight > previous[1]:
                clustered[cluster][hypothesis_id] = (
                    effect,
                    weight,
                    str(item.get("evidence_id") or ""),
                )
    hypotheses: list[dict[str, Any]] = []
    for hypothesis_id, statement in HYPOTHESES.items():
        supports: list[str] = []
        contradicts: list[str] = []
        net = 0.0
        for cluster, effects in clustered.items():
            effect = effects.get(hypothesis_id)
            if effect is None:
                continue
            direction, weight, _ = effect
            net += direction * weight
            (supports if direction > 0 else contradicts).append(cluster)
        hypotheses.append(
            {
                "id": hypothesis_id,
                "statement": statement,
                "support_clusters": sorted(supports),
                "contradiction_clusters": sorted(contradicts),
                "net_consistency": round(net, 4),
            }
        )
    top = max((item["net_consistency"] for item in hypotheses), default=0.0)
    leading = [item["id"] for item in hypotheses if item["net_consistency"] == top]
    return {
        "method": "Analysis of Competing Hypotheses (ACH); consistency values are ordinal diagnostics, not probabilities.",
        "hypotheses": hypotheses,
        "leading_hypotheses": leading,
        "independent_source_clusters": len(clustered),
    }


def _verification_priority(
    stage: str,
    capability_score: float,
    candidate: dict[str, Any],
) -> tuple[float, str, list[str]]:
    base = {
        "S0_UNLINKED": 60,
        "S1_EXACT_PRODUCT_MATCH": 52,
        "S2_AUTHORIZED_SITE": 42,
        "S3_PROCESS_CONFIRMED": 25,
        "S4_BATCH_LINKED": 5,
    }[stage]
    score = base + capability_score * 0.3
    unresolved_critical = sum(
        1
        for flag in candidate.get("red_flags", [])
        if isinstance(flag, dict)
        and flag.get("severity") == "critical"
        and flag.get("status") != "resolved"
    )
    score = min(100.0, score + min(10, unresolved_critical * 5))
    drivers = [f"current trace stage is {stage}", f"capability fit is {capability_score:.2f}"]
    if unresolved_critical:
        drivers.append(f"{unresolved_critical} unresolved critical red flag(s)")
    band = "HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW"
    return round(score, 2), band, drivers


def _procurement_utility(
    candidate: dict[str, Any], capability_score: float, cert_state: dict[str, Any]
) -> tuple[float | None, dict[str, Any]]:
    mainland = _normalise_mainland_status(candidate)
    eligible = mainland is True
    raw_inputs = candidate.get("procurement_inputs", candidate.get("procurement", {}))
    inputs = raw_inputs if isinstance(raw_inputs, dict) else {}
    allowed = {
        "quality_fit",
        "commercial_fit",
        "lead_time_fit",
        "capacity_fit",
        "material_fit",
        "cost_fit",
    }
    explicit_values = [
        float(value)
        for key, value in inputs.items()
        if key in allowed and isinstance(value, (int, float)) and 0 <= float(value) <= 100
    ]
    explicit_average = (
        sum(explicit_values) / len(explicit_values) if explicit_values else None
    )
    cert_score = {
        "PASS": 100.0,
        "OPEN": 30.0,
        "FAIL": 0.0,
    }[cert_state["dual_certification_gate"]]
    utility: float | None = None
    if eligible:
        weighted = capability_score * 0.6 + cert_score * 0.2
        denominator = 0.8
        if explicit_average is not None:
            weighted += explicit_average * 0.2
            denominator = 1.0
        utility = round(weighted / denominator, 2)
    details = {
        "eligible_for_mainland_rank": eligible,
        "verified_mainland_site": mainland,
        "buyer_input_count": len(explicit_values),
        "inputs_complete": bool(explicit_values),
        "notice": (
            "Mainland status is a hard procurement-list filter only. It is excluded from "
            "trace stage, analytic confidence, ESS, capability, and ACH attribution."
        ),
    }
    return utility, details


def assess_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Produce the canonical v2 multi-axis assessment for one candidate.

    中文：为单个候选生成标准多轴评估；证据充分度、能力和采购价值保持分离，任何数字都不是校准概率。
    """
    if not isinstance(candidate, dict):
        raise TypeError("candidate must be an object")
    evidence = _usable_evidence(candidate)
    ess = calculate_ess(candidate)
    cert_state = certification_state(candidate, evidence)
    stage, stage_checks = _trace_stage(candidate, evidence, cert_state)
    capability_score, capability_details = _capability_fit(candidate, evidence)
    analytic_level, analytic_score, analytic_basis = _analytic_confidence(candidate, evidence)
    ach = build_ach(candidate, evidence)
    priority, priority_band, priority_drivers = _verification_priority(
        stage, capability_score, candidate
    )
    procurement, procurement_details = _procurement_utility(
        candidate, capability_score, cert_state
    )
    return {
        "schema": 2,
        "schema_version": 2,
        "candidate_id": candidate.get("candidate_id", "UNKNOWN"),
        "display_name": candidate.get("display_name", ""),
        "target_processes": ess["target_processes"],
        "trace_stage": stage,
        "trace_stage_checks": stage_checks,
        "analytic_confidence": analytic_level,
        "analytic_confidence_score": analytic_score,
        "analytic_confidence_basis": analytic_basis,
        "evidence_sufficiency_score": ess["evidence_sufficiency_score"],
        "capability_fit_score": capability_score,
        "capability_fit_details": capability_details,
        "certification_state": cert_state,
        "verification_priority": priority,
        "verification_priority_band": priority_band,
        "verification_priority_drivers": priority_drivers,
        "procurement_utility": procurement,
        "procurement_policy": procurement_details,
        "ach": ach,
        "components": ess["components"],
        "raw_score": ess["raw_score"],
        "caps": ess["caps"],
        "hard_gates": ess["hard_gates"],
        "hard_gates_passed": ess["hard_gates_passed"],
        "hard_gates_total": ess["hard_gates_total"],
        "verdict": ess["verdict"],
        "confidence_index": ess["evidence_sufficiency_score"],
        "confidence_index_deprecated": True,
        "confidence_notice": (
            "DEPRECATED legacy alias of evidence_sufficiency_score (ESS). It is not a "
            "statistically calibrated probability and must not be labelled as source-factory odds."
        ),
        "source_attribution_notice": (
            "Trace stage and ACH describe attribution. Capability, certification, region, "
            "verification priority, and procurement utility are separate axes."
        ),
        "computed_at_utc": utc_now(),
    }


def assess_candidates(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [assess_candidate(candidate) for candidate in candidates]
