"""English: Separate account identity, site/process bindings, access states, and repost clusters.

中文：分离账号身份、地点工艺关联、访问状态与转载簇；认证账号只证明身份，不自动证明目标产品在该厂生产。
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit


BINDING_STATES = (
    "UNBOUND_ACCOUNT",
    "ENTITY_BOUND",
    "SITE_BOUND",
    "PROCESS_BOUND",
    "TARGET_SKU_BOUND",
)
STATE_RANK = {state: index for index, state in enumerate(BINDING_STATES)}

BLOCKED_STATUSES = frozenset(
    {
        "access_denied",
        "blocked",
        "geo_blocked",
        "login_required",
        "rate_limited",
        "robots_denied",
    }
)
AVAILABLE_STATUSES = frozenset({"active", "available", "reachable"})
REMOVED_STATUSES = frozenset({"deleted", "not_found", "removed"})

REPOST_QUALITY = {
    "native_original": 5,
    "native_share": 4,
    "exact_reupload": 3,
    "derivative_reupload": 2,
    "visual_similarity": 1,
    "unknown": 0,
}


def _normal(value: Any) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def classify_access_state(status: Any) -> dict[str, Any]:
    normalized = _normal(status)
    if normalized in BLOCKED_STATUSES:
        return {
            "state": "BLOCKED",
            "absence_allowed": False,
            "absence_conclusion": "UNKNOWN_BLOCKED_NOT_ABSENCE",
        }
    if normalized in AVAILABLE_STATUSES:
        return {
            "state": "AVAILABLE",
            "absence_allowed": False,
            "absence_conclusion": "NOT_OBSERVED_IS_NOT_ABSENT",
        }
    if normalized in REMOVED_STATUSES:
        return {
            "state": "REMOVED_OR_NOT_FOUND",
            "absence_allowed": False,
            "absence_conclusion": "ACCOUNT_UNAVAILABLE_NOT_PRODUCT_ABSENCE",
        }
    return {
        "state": "UNKNOWN",
        "absence_allowed": False,
        "absence_conclusion": "UNKNOWN_NOT_ABSENCE",
    }


def _canonical_url(value: Any) -> str:
    rendered = str(value or "").strip()
    if not rendered:
        return ""
    try:
        parsed = urlsplit(rendered)
    except ValueError:
        return _normal(rendered)
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.netloc:
        return _normal(rendered)
    return urlunsplit(
        (
            parsed.scheme.casefold(),
            parsed.netloc.casefold(),
            parsed.path.rstrip("/") or "/",
            "",
            "",
        )
    )


def _cluster_tokens(item: Mapping[str, Any], index: int) -> set[tuple[str, str]]:
    fields = (
        "repost_cluster_id",
        "canonical_source_id",
        "origin_content_id",
        "media_sha256",
        "frozen_sha256",
        "perceptual_cluster_id",
    )
    tokens: set[tuple[str, str]] = set()
    for field in fields:
        value = _normal(item.get(field))
        if value:
            tokens.add((field, value))
    for field in ("canonical_url", "source_url", "url"):
        value = _canonical_url(item.get(field))
        if value:
            tokens.add(("canonical_url", value))
    if tokens:
        return tokens
    evidence_id = _normal(item.get("evidence_id")) or str(index)
    return {("singleton", evidence_id)}


def _publisher_tokens(
    item: Mapping[str, Any],
    index: int,
    account: Mapping[str, Any] | None,
) -> set[tuple[str, str]]:
    account = account or {}
    platform = _normal(item.get("platform") or account.get("platform"))
    account_id = _normal(item.get("account_id") or account.get("account_id"))
    source_owner = _normal(item.get("source_owner") or account.get("source_owner"))
    tokens: set[tuple[str, str]] = set()
    if account_id:
        tokens.add(("publisher_account", f"{platform or '<unknown>'}:{account_id}"))
    if source_owner:
        tokens.add(("publisher_owner", source_owner))
    if tokens:
        return tokens
    evidence_id = _normal(item.get("evidence_id")) or str(index)
    return {("publisher_singleton", evidence_id)}


def _values(value: Any) -> set[str]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return {_normal(item) for item in value if _normal(item)}
    normalized = _normal(value)
    return {normalized} if normalized else set()


def _binding_state(
    item: Mapping[str, Any], target: Mapping[str, Any]
) -> tuple[str, dict[str, bool]]:
    bindings = item.get("bindings", item)
    if not isinstance(bindings, Mapping):
        bindings = {}

    expected_entity = _normal(target.get("entity_id"))
    expected_site = _normal(target.get("site_id"))
    expected_processes = _values(target.get("process")) | _values(
        target.get("processes")
    )
    expected_sku = _normal(target.get("sku"))

    entity_match = bool(expected_entity) and (
        _normal(bindings.get("entity_id")) == expected_entity
    )
    site_match = entity_match and bool(expected_site) and (
        _normal(bindings.get("site_id")) == expected_site
    )
    observed_processes = _values(bindings.get("process")) | _values(
        bindings.get("processes")
    )
    process_match = site_match and bool(expected_processes) and bool(
        expected_processes & observed_processes
    )
    sku_match = process_match and bool(expected_sku) and (
        _normal(bindings.get("sku")) == expected_sku
    )
    matches = {
        "entity": entity_match,
        "site": site_match,
        "process": process_match,
        "target_sku": sku_match,
    }
    if sku_match:
        return "TARGET_SKU_BOUND", matches
    if process_match:
        return "PROCESS_BOUND", matches
    if site_match:
        return "SITE_BOUND", matches
    if entity_match:
        return "ENTITY_BOUND", matches
    return "UNBOUND_ACCOUNT", matches


def deduplicate_repost_evidence(
    observations: Sequence[Mapping[str, Any]],
    *,
    account: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Collapse content duplicates and repeated publishers without losing either view.

    Content identifiers answer whether posts reuse the same media/source.  A
    separate publisher identity layer ensures that ten distinct URLs from the
    same platform account or source owner are still only one independent
    publishing subject.  The final independence graph joins on either layer.

    中文：内容层合并相同媒体，发布者层合并同一账号或主体；多个不同URL不能伪装为多个独立来源。
    """

    rendered_observations = [dict(item) for item in observations]
    content_tokens_by_index = [
        _cluster_tokens(item, index)
        for index, item in enumerate(rendered_observations)
    ]
    publisher_tokens_by_index = [
        _publisher_tokens(item, index, account)
        for index, item in enumerate(rendered_observations)
    ]

    def make_clusters(
        tokens_by_index: Sequence[set[tuple[str, str]]], basis: str
    ) -> list[dict[str, Any]]:
        parents = list(range(len(rendered_observations)))

        def find(index: int) -> int:
            while parents[index] != index:
                parents[index] = parents[parents[index]]
                index = parents[index]
            return index

        def union(left: int, right: int) -> None:
            left_root = find(left)
            right_root = find(right)
            if left_root != right_root:
                parents[right_root] = left_root

        token_owner: dict[tuple[str, str], int] = {}
        for index, tokens in enumerate(tokens_by_index):
            for token in tokens:
                if token in token_owner:
                    union(index, token_owner[token])
                else:
                    token_owner[token] = index

        grouped_indexes: dict[int, list[int]] = {}
        for index in range(len(rendered_observations)):
            grouped_indexes.setdefault(find(index), []).append(index)

        clusters: list[dict[str, Any]] = []
        for member_indexes in grouped_indexes.values():
            members = [rendered_observations[index] for index in member_indexes]
            connected_tokens = sorted(
                {
                    f"{field}:{value}"
                    for index in member_indexes
                    for field, value in tokens_by_index[index]
                }
            )
            key = hashlib.sha256(
                "\n".join(connected_tokens).encode("utf-8")
            ).hexdigest()[:20]
            representative = sorted(
                members,
                key=lambda item: (
                    -REPOST_QUALITY.get(
                        _normal(item.get("relationship", "unknown")), 0
                    ),
                    -int(bool(item.get("frozen_sha256") or item.get("media_sha256"))),
                    _normal(item.get("published_at")) or "\uffff",
                    _normal(item.get("evidence_id")),
                ),
            )[0]
            published_times = sorted(
                {
                    str(item.get("published_at")).strip()
                    for item in members
                    if item.get("published_at")
                }
            )
            clusters.append(
                {
                    "independence_group": f"social:{basis}:{key}",
                    "cluster_basis": basis,
                    "cluster_key": key,
                    "connected_identifiers": connected_tokens,
                    "member_indexes": member_indexes,
                    "member_count": len(members),
                    "evidence_ids": [item.get("evidence_id") for item in members],
                    "representative": representative,
                    "earliest_published_at": (
                        published_times[0] if published_times else None
                    ),
                    "relationships": sorted(
                        {
                            _normal(item.get("relationship", "unknown"))
                            for item in members
                        }
                    ),
                }
            )
        clusters.sort(key=lambda item: item["independence_group"])
        return clusters

    content_clusters = make_clusters(
        content_tokens_by_index, "connected_content_identifiers"
    )
    publisher_clusters = make_clusters(
        publisher_tokens_by_index, "connected_publisher_identifiers"
    )
    independence_tokens = [
        content_tokens | publisher_tokens
        for content_tokens, publisher_tokens in zip(
            content_tokens_by_index, publisher_tokens_by_index
        )
    ]
    clusters = make_clusters(independence_tokens, "content_or_publisher_identity")
    return {
        "schema": "factorytrace.social.repost-clusters.v2",
        "input_observations": len(observations),
        "independent_clusters": len(clusters),
        "duplicates_removed": len(observations) - len(clusters),
        "clusters": clusters,
        "content_cluster_count": len(content_clusters),
        "content_clusters": content_clusters,
        "independent_publishing_subjects": len(publisher_clusters),
        "publisher_clusters": publisher_clusters,
    }


def evaluate_social_chain(
    account: Mapping[str, Any],
    observations: Sequence[Mapping[str, Any]],
    target: Mapping[str, Any],
) -> dict[str, Any]:
    """Evaluate social evidence without promoting account identity to production.

    Platform verification may close only ``ENTITY_BOUND``. Reaching a site,
    process, or target SKU requires an observation that explicitly binds every
    preceding element in the same evidence item.

    中文：平台认证最多闭合主体身份；地点、工序与目标SKU都需要同一证据项明确关联前置要素。
    """

    access = classify_access_state(account.get("status"))
    clustered = deduplicate_repost_evidence(observations, account=account)
    expected_entity = _normal(target.get("entity_id"))
    account_entity = _normal(account.get("entity_id"))
    verification = account.get("verification", {})
    if not isinstance(verification, Mapping):
        verification = {}
    platform_entity_verified = (
        bool(verification.get("verified"))
        and bool(expected_entity)
        and account_entity == expected_entity
    )

    best_state = "ENTITY_BOUND" if platform_entity_verified else "UNBOUND_ACCOUNT"
    binding_evidence: list[dict[str, Any]] = []
    for cluster in clustered["clusters"]:
        best_member: dict[str, Any] | None = None
        best_member_state = "UNBOUND_ACCOUNT"
        best_matches: dict[str, bool] = {}
        for index in cluster.get("member_indexes", []):
            item = observations[index]
            state, matches = _binding_state(item, target)
            if STATE_RANK[state] > STATE_RANK[best_member_state]:
                best_member = dict(item)
                best_member_state = state
                best_matches = matches
        if best_member is None:
            best_member = dict(cluster["representative"])
            best_member_state, best_matches = _binding_state(best_member, target)
        binding_evidence.append(
            {
                "independence_group": cluster["independence_group"],
                "representative_evidence_id": best_member.get("evidence_id"),
                "binding_state": best_member_state,
                "matches": best_matches,
                "member_count": cluster["member_count"],
            }
        )
        if STATE_RANK[best_member_state] > STATE_RANK[best_state]:
            best_state = best_member_state

    warnings = [
        "Platform verification authenticates the account/entity only; it does not verify posts, factory site, process, or SKU."
    ]
    if access["state"] == "BLOCKED":
        warnings.append(
            "The account was blocked or inaccessible; no absence conclusion is permitted."
        )
    if clustered["duplicates_removed"]:
        warnings.append(
            "Same-origin reposts were collapsed into one independence group."
        )

    return {
        "schema": "factorytrace.social.v2",
        "status": (
            "TARGET_SKU_BOUND"
            if best_state == "TARGET_SKU_BOUND"
            else "PARTIAL"
            if best_state != "UNBOUND_ACCOUNT"
            else "UNBOUND"
        ),
        "binding_state": best_state,
        "binding_path": list(BINDING_STATES[: STATE_RANK[best_state] + 1]),
        "platform": account.get("platform"),
        "account_id": account.get("account_id"),
        "access": access,
        "platform_entity_verified": platform_entity_verified,
        "target": dict(target),
        "observations_seen": len(observations),
        "independent_clusters": clustered["independent_clusters"],
        "content_cluster_count": clustered["content_cluster_count"],
        "independent_publishing_subjects": clustered[
            "independent_publishing_subjects"
        ],
        "duplicates_removed": clustered["duplicates_removed"],
        "binding_evidence": binding_evidence,
        "repost_clusters": clustered["clusters"],
        "content_clusters": clustered["content_clusters"],
        "publisher_clusters": clustered["publisher_clusters"],
        "absence_conclusion": access["absence_conclusion"],
        "warnings": warnings,
        "meaning": (
            "TARGET_SKU_BOUND is a structured social-media binding, not proof of "
            "certification, batch manufacture, or an independently audited process."
        ),
    }
