"""English: Deduplicate source identities and calculate evidence sufficiency, not odds.

中文：先去重来源身份，再计算证据充分度而非概率；同文转载不能靠不同分组名反复累加，反证会降低分值。
"""

from __future__ import annotations

import json
import math
import urllib.parse
from pathlib import Path
from typing import Any

from .common import atomic_write_json


DIMENSIONS = {
    "entity_chain": 15,
    "physical_site_process": 25,
    "exact_sku_process": 30,
    "commercial_batch_chain": 15,
    "certification_manufacturing_site": 10,
    "independent_corroboration": 5,
}

STRENGTH = {"direct": 1.0, "strong": 0.75, "supporting": 0.4, "lead": 0.15}
SOURCE = {
    "certifier": 1.0,
    "government": 1.0,
    "buyer_document": 0.95,
    "independent_audit": 0.9,
    "supplier_live": 0.8,
    "logistics": 0.7,
    "trade_data": 0.65,
    "media": 0.5,
    "platform": 0.4,
    "self_published": 0.3,
    "search_snippet": 0.15,
}
BINDING = {"exact": 1.0, "partial": 0.6, "family": 0.45, "similar": 0.25, "none": 0.1}

_TRACKING_QUERY_KEYS = {
    "spm",
    "scm",
    "ref",
    "referrer",
    "source",
    "fbclid",
    "gclid",
    "gbraid",
    "wbraid",
}


def _canonical_url(value: str) -> str:
    """Return a stable URL identity while retaining product/query identifiers.

    中文：规范化来源URL但保留产品与查询标识，避免把不同详情页误合并。
    """
    try:
        parsed = urllib.parse.urlsplit(value.strip())
        hostname = (parsed.hostname or "").casefold()
        port = parsed.port
        if port and not (
            (parsed.scheme.casefold() == "http" and port == 80)
            or (parsed.scheme.casefold() == "https" and port == 443)
        ):
            hostname = f"{hostname}:{port}"
        query = sorted(
            (key, item_value)
            for key, item_value in urllib.parse.parse_qsl(
                parsed.query, keep_blank_values=True
            )
            if not key.casefold().startswith("utm_")
            and key.casefold() not in _TRACKING_QUERY_KEYS
        )
        path = parsed.path or "/"
        if path != "/":
            path = path.rstrip("/")
        return urllib.parse.urlunsplit(
            (
                parsed.scheme.casefold(),
                hostname,
                path,
                urllib.parse.urlencode(query, doseq=True),
                "",
            )
        )
    except (TypeError, ValueError):
        return value.strip()


def source_cluster_key(item: dict[str, Any], index: int = 0) -> str:
    """Resolve the strongest available same-source identity.

    Content hashes and canonical URLs outrank a contributor supplied
    ``independence_group``.  This prevents the same document or page from being
    counted repeatedly merely by assigning different group labels.

    中文：内容哈希与规范URL优先于人工独立组名，避免同文档换组名后重复计分。
    """
    sha256 = str(item.get("sha256") or "").strip().casefold()
    if len(sha256) == 64 and all(character in "0123456789abcdef" for character in sha256):
        return f"sha256:{sha256}"
    artifact_id = str(item.get("source_artifact_id") or "").strip()
    if artifact_id:
        return f"artifact:{artifact_id.casefold()}"
    source_url = str(item.get("source_url") or "").strip()
    if source_url:
        return f"url:{_canonical_url(source_url)}"
    declared = str(
        item.get("source_cluster_id") or item.get("independence_group") or ""
    ).strip()
    if declared:
        return f"group:{declared.casefold()}"
    evidence_id = str(item.get("evidence_id") or "").strip()
    if evidence_id:
        return f"evidence:{evidence_id.casefold()}"
    return f"ungrouped:{index}"


def _binding_factor(item: dict[str, Any], dimension: str) -> float:
    if dimension == "entity_chain":
        return BINDING.get(item.get("entity_bind", "none"), 0.1)
    if dimension in {"physical_site_process", "certification_manufacturing_site"}:
        return BINDING.get(item.get("site_bind", "none"), 0.1)
    if dimension in {"exact_sku_process", "commercial_batch_chain"}:
        sku = BINDING.get(item.get("sku_bind", "none"), 0.1)
        site = BINDING.get(item.get("site_bind", "none"), 0.1)
        return math.sqrt(sku * site)
    return 1.0


def evidence_signal(item: dict[str, Any]) -> float:
    dimension = str(item.get("dimension") or "")
    return (
        STRENGTH.get(item.get("strength", "lead"), 0.15)
        * SOURCE.get(item.get("source_class", "search_snippet"), 0.15)
        * _binding_factor(item, dimension)
    )


def _is_usable(item: dict[str, Any]) -> bool:
    return item.get("review_status") not in {"rejected", "superseded"}


def _deduplicated_signals(
    evidence: list[dict[str, Any]], dimension: str, stance: str
) -> dict[str, float]:
    groups: dict[str, float] = {}
    for index, item in enumerate(evidence):
        if not _is_usable(item):
            continue
        if item.get("dimension") != dimension or item.get("stance") != stance:
            continue
        group = source_cluster_key(item, index)
        groups[group] = max(groups.get(group, 0.0), evidence_signal(item))
    return groups


def _entity_value(candidate: dict[str, Any], key: str) -> bool:
    value = candidate.get("entities", {}).get(key)
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value)
    return bool(value)


def calculate_ess(candidate: dict[str, Any]) -> dict[str, Any]:
    """Calculate the legacy Evidence Sufficiency Score without implying odds.

    中文：计算历史兼容的证据充分度分数，并计入来源去重与反证；分数不表示厂家的统计概率。
    """
    evidence = candidate.get("evidence", [])
    if not isinstance(evidence, list):
        raise ValueError("candidate.evidence must be a list")
    evidence = [item for item in evidence if isinstance(item, dict)]
    components: dict[str, dict[str, Any]] = {}
    raw_score = 0.0
    for dimension, maximum in DIMENSIONS.items():
        support = _deduplicated_signals(evidence, dimension, "support")
        contradict = _deduplicated_signals(evidence, dimension, "contradict")
        support_score = maximum * min(1.0, sum(support.values()) / 1.5)
        contradiction_penalty = maximum * min(0.8, sum(contradict.values()) / 1.2)
        score = max(0.0, support_score - contradiction_penalty)
        components[dimension] = {
            "maximum": maximum,
            "score": round(score, 2),
            "support_groups": support,
            "contradiction_groups": contradict,
        }
        raw_score += score

    target_processes = set(candidate.get("target_processes", []))
    strong_factory_items = [
        item
        for item in evidence
        if _is_usable(item)
        and item.get("stance") == "support"
        and item.get("dimension") == "physical_site_process"
        and item.get("strength") in {"direct", "strong"}
        and SOURCE.get(item.get("source_class", ""), 0) >= 0.65
        and item.get("site_bind") == "exact"
        and (not target_processes or item.get("process") in target_processes)
    ]
    exact_sku_items = [
        item
        for item in evidence
        if _is_usable(item)
        and item.get("stance") == "support"
        and item.get("dimension") == "exact_sku_process"
        and item.get("strength") in {"direct", "strong"}
        and item.get("sku_bind") == "exact"
        and item.get("site_bind") == "exact"
        and SOURCE.get(item.get("source_class", ""), 0) >= 0.65
        and (not target_processes or item.get("process") in target_processes)
    ]
    red_flags = candidate.get("red_flags", [])
    critical_unresolved = any(
        flag.get("severity") == "critical" and flag.get("status") != "resolved"
        for flag in red_flags
        if isinstance(flag, dict)
    )
    unresolved_site_conflict = any(
        flag.get("type") == "site_conflict" and flag.get("status") != "resolved"
        for flag in red_flags
        if isinstance(flag, dict)
    )
    exact_mismatch = any(
        flag.get("type") == "exact_sku_mismatch" and flag.get("status") != "resolved"
        for flag in red_flags
        if isinstance(flag, dict)
    )
    gates = {
        "entity_chain_clear": all(
            _entity_value(candidate, key)
            for key in ("contracting_entity", "payment_entity", "manufacturer_entity")
        ),
        "manufacturing_site_exact": _entity_value(candidate, "manufacturing_sites")
        and components["physical_site_process"]["score"] >= 8,
        "physical_target_process": bool(strong_factory_items),
        "exact_sku_or_batch_bound": bool(exact_sku_items),
        "responsibility_chain_closed": (
            components["commercial_batch_chain"]["score"] >= 7.5
            and bool(candidate.get("responsibility_chain_explanation", "").strip())
        ),
        "no_critical_red_flags": not critical_unresolved,
    }

    caps: list[dict[str, Any]] = []
    source_classes = {
        item.get("source_class") for item in evidence if _is_usable(item)
    }
    if source_classes and source_classes <= {
        "platform",
        "self_published",
        "media",
        "search_snippet",
    }:
        caps.append({"cap": 20, "reason": "marketing/platform evidence only"})
    if not gates["physical_target_process"]:
        caps.append({"cap": 55, "reason": "target process at exact site not independently shown"})
    if not gates["exact_sku_or_batch_bound"]:
        caps.append({"cap": 59, "reason": "exact SKU/batch not bound to target process and site"})
    if unresolved_site_conflict:
        caps.append({"cap": 50, "reason": "manufacturing-site conflict unresolved"})
    if critical_unresolved:
        caps.append({"cap": 35, "reason": "critical red flag unresolved"})
    if exact_mismatch:
        caps.append({"cap": 20, "reason": "non-adjustable exact-SKU mismatch"})
    final_score = min([95.0, raw_score] + [float(item["cap"]) for item in caps])
    all_gates = all(gates.values())
    if final_score >= 80 and all_gates:
        verdict = "A / confirmed target-process manufacturer"
    elif final_score >= 60:
        verdict = "B / high-confidence candidate; hard evidence still missing"
    elif final_score >= 30:
        verdict = "C / candidate supplier or related factory; manufacturing unconfirmed"
    else:
        verdict = "D / seller, repost source, or insufficient evidence"
    return {
        "target_processes": sorted(target_processes),
        "components": components,
        "raw_score": round(raw_score, 2),
        "caps": caps,
        "evidence_sufficiency_score": round(final_score, 2),
        "hard_gates": gates,
        "hard_gates_passed": sum(gates.values()),
        "hard_gates_total": len(gates),
        "verdict": verdict,
    }


def score_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Compatibility entry point returning the complete v2 assessment.

    中文：保留旧评分入口但返回完整新版多轴评估，不能当作旧概率输出使用。
    """
    # Local import avoids a module cycle: assessment uses calculate_ess above.
    # 中文：延迟导入避免循环依赖，因为assessment也使用上面的calculate_ess。
    from .assessment import assess_candidate

    return assess_candidate(candidate)


def score_paths(paths: list[Path], output_dir: Path) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for path in paths:
        candidate = json.loads(path.read_text(encoding="utf-8"))
        result = score_candidate(candidate)
        atomic_write_json(output_dir / f"{result['candidate_id']}-score.json", result)
        results.append(result)
    results.sort(key=lambda item: item["evidence_sufficiency_score"], reverse=True)
    atomic_write_json(
        output_dir / "candidate-ranking.json",
        {
            "schema": 2,
            "schema_version": 2,
            "notice": (
                "Ranking by Evidence Sufficiency Score (ESS), not source-factory "
                "probability. Procurement ranking requires its separate eligibility gate."
            ),
            "candidates": results,
        },
    )
    return results


def run(args: object) -> int:
    paths: list[Path] = []
    for path in args.candidates:
        if path.is_dir():
            paths.extend(sorted(path.glob("*.json")))
        else:
            paths.append(path)
    results = score_paths(paths, args.output_dir)
    print(json.dumps({"scored": len(results), "results": results}, ensure_ascii=False))
    return 0
