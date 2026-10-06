"""English: Build multilingual search lanes from product profiles and resolved process packs.

中文：根据产品档案与已解析工艺包生成多语种检索路线；尺寸状态与容差需要保留，搜索词不是测量结果。
"""

from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path
from typing import Any

from .common import atomic_write_json, safe_slug, utc_now, write_csv
from .process_packs import compose_process_packs


FIELDS = ["query_id", "lane", "language", "query", "purpose"]


def _dimensions(profile: dict[str, Any]) -> list[str]:
    measured = []
    for item in profile.get("measurements", []):
        if not isinstance(item, dict):
            continue
        if not item.get("use_for_search", False):
            continue
        if item.get("status") in {"conflict", "rejected", "unknown"}:
            continue
        search_text = str(item.get("search_text", "")).strip()
        if search_text:
            measured.append(search_text)
    if measured:
        return list(dict.fromkeys(measured))

    # Legacy fallback for profiles created before 1.1.0. New cases should use
    # measurement records with source/status/tolerance instead.
    # 中文：此处仅兼容旧档案；新版尺寸应记录来源、状态和容差，不能直接沿用未经核验的营销尺寸。
    dimensions = profile.get("dimensions_mm", {})
    explicit = [str(value) for value in profile.get("dimension_strings", []) if value]
    if all(dimensions.get(key) for key in ("outer_length", "outer_width")):
        length = dimensions["outer_length"]
        width = dimensions["outer_width"]
        height = dimensions.get("height")
        explicit.extend(
            [
                f"{length}×{width}" + (f"×{height}" if height else ""),
                f"{length} {width}" + (f" {height}" if height else ""),
            ]
        )
    return list(dict.fromkeys(explicit))


def build_queries(profile: dict[str, Any], max_queries: int = 200) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    category_zh = profile.get("category_zh", "")
    category_en = profile.get("category_en", "")
    dimensions = _dimensions(profile)
    models = [str(value).strip() for value in profile.get("exact_models", []) if value]
    features_zh = [str(value).strip() for value in profile.get("features_zh", []) if value]
    features_en = [str(value).strip() for value in profile.get("features_en", []) if value]
    processes_zh = [str(value).strip() for value in profile.get("processes_zh", []) if value]
    processes_en = [str(value).strip() for value in profile.get("processes_en", []) if value]
    parts_zh = [str(value).strip() for value in profile.get("parts_zh", []) if value]
    parts_en = [str(value).strip() for value in profile.get("parts_en", []) if value]
    ignored_brands = [
        str(value).strip() for value in profile.get("visible_brands", []) if value
    ]
    pack_terms = [
        str(value).strip().replace("_", " ")
        for value in profile.get("process_pack_terms", [])
        if str(value).strip()
    ]

    def add(lane: str, language: str, query: str, purpose: str) -> None:
        query = " ".join(query.split())
        key = query.casefold()
        if not query or key in seen or len(rows) >= max_queries:
            return
        seen.add(key)
        rows.append(
            {
                "query_id": f"Q{len(rows) + 1:04d}",
                "lane": lane,
                "language": language,
                "query": query,
                "purpose": purpose,
            }
        )

    for model in models:
        add("exact-model", "multi", f'"{model}"', "Find exact model references and files")
    for dimension in dimensions:
        add(
            "dimension-category",
            "zh",
            f"{dimension} {category_zh}",
            "Find the same dimensional family without relying on branding",
        )
        add(
            "dimension-category",
            "en",
            f"{dimension} {category_en}",
            "Find overseas listings and technical catalogues",
        )
    for pair in itertools.combinations(features_zh[:8], 2):
        add("feature-combination", "zh", f"{category_zh} {' '.join(pair)}", "Distinctive structure")
    for pair in itertools.combinations(features_en[:8], 2):
        add("feature-combination", "en", f"{category_en} {' '.join(pair)}", "Distinctive structure")
    for part in parts_zh:
        for process in processes_zh[:5]:
            add("process-supplier", "zh", f"{part} {process} 厂家", "Find component/process factories")
    for part in parts_en:
        for process in processes_en[:5]:
            add("process-supplier", "en", f"{part} {process} manufacturer", "Find component/process factories")
    for certificate in profile.get("certification_ids", []):
        add(
            "certificate",
            "multi",
            f'"{certificate}" {category_en or category_zh}',
            "Trace licence, model, certificate transitions, and holders",
        )
    for hs_code in profile.get("hs_candidates", []):
        add(
            "trade",
            "en",
            f'"{hs_code}" {category_en} exporter manufacturer',
            "Find logistics and customs references; shipper is not assumed to be manufacturer",
        )
    for term in pack_terms:
        add(
            "process-pack",
            "en",
            f"{category_en or category_zh} {term} manufacturer factory",
            "Find evidence required by the selected process pack",
        )
    if profile.get("brand_policy") == "ignore" and ignored_brands:
        exclusion = " ".join(f'-"{brand}"' for brand in ignored_brands)
        for base in list(rows)[: min(20, len(rows))]:
            add(
                "brand-excluded-web",
                base["language"],
                f"{base['query']} {exclusion}",
                "Reduce irrelevant brand/retail results; brand contributes zero factory evidence",
            )
    return rows


def generate(
    profile_path: Path,
    case_root: Path,
    max_queries: int = 200,
    pack_names: list[str] | None = None,
) -> tuple[Path, Path]:
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    selected_packs = [name for name in (pack_names or []) if name]
    if selected_packs:
        pack = compose_process_packs(selected_packs)
        profile["process_pack_terms"] = list(
            dict.fromkeys(
                [
                    *profile.get("process_pack_terms", []),
                    *pack.get("required_processes", []),
                    *pack.get("required_evidence", []),
                    *pack.get("required_documents", []),
                ]
            )
        )
    rows = build_queries(profile, max_queries=max_queries)
    target = safe_slug(profile.get("target_id", "target"))
    output_dir = case_root.resolve(strict=True) / "work" / "queries"
    csv_path = output_dir / f"{target}_queries.csv"
    json_path = output_dir / f"{target}_queries.json"
    write_csv(csv_path, FIELDS, rows)
    atomic_write_json(
        json_path,
        {
            "schema": 1,
            "generated_at_utc": utc_now(),
            "profile": str(profile_path),
            "process_packs": selected_packs,
            "count": len(rows),
            "queries": rows,
        },
    )
    return csv_path, json_path


def run(args: object) -> int:
    profile = args.profile or (args.case_root / "work" / "product_profile.json")
    csv_path, json_path = generate(
        profile,
        args.case_root,
        max_queries=args.max_queries,
        pack_names=getattr(args, "pack", []),
    )
    print(
        json.dumps(
            {"csv": str(csv_path), "json": str(json_path)}, ensure_ascii=False
        )
    )
    return 0
