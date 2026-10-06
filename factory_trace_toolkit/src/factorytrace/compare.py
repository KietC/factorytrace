"""English: Compare image hashes, edges, and normalized pixels in bounded worker pools.

中文：在有上限的进程池中比较图像哈希、边缘与归一化像素；相似度用于候选筛选，不证明同模或同厂。
"""

from __future__ import annotations

import csv
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat

from .common import safe_name, sha256_file, write_csv
from .variants import dhash


FIELDS = [
    "candidate",
    "candidate_sha256",
    "reference_sha256",
    "dhash_distance",
    "normalized_mean_abs_error",
    "edge_jaccard",
    "triage_similarity",
    "automated_media_relation",
    "physical_product_inference",
    "overlay_path",
    "warning",
]
AUTO_WORKER_CAP = 8


def automatic_worker_count(candidate_count: int) -> int:
    """Keep auto mode bounded on high-core workstations and small batches.

    中文：自动并发数受CPU、候选数与上限约束，避免少量任务启动过多进程消耗内存。
    """
    usable_cpus = max(1, (os.cpu_count() or 2) - 1)
    return max(1, min(AUTO_WORKER_CAP, usable_cpus, max(1, candidate_count)))


def _hamming(left: str, right: str) -> int:
    return (int(left, 16) ^ int(right, 16)).bit_count()


def _normalized(path: Path, size: int = 512) -> Image.Image:
    with Image.open(path) as opened:
        image = ImageOps.exif_transpose(opened).convert("L")
    return ImageOps.fit(image, (size, size), method=Image.Resampling.LANCZOS)


def _edge_mask(image: Image.Image) -> Image.Image:
    edges = image.filter(ImageFilter.FIND_EDGES)
    return edges.point(lambda value: 255 if value >= 32 else 0, mode="1")


def _compare_one(task: tuple[str, str, str]) -> dict[str, Any]:
    reference_text, candidate_text, overlay_text = task
    reference_path = Path(reference_text)
    candidate_path = Path(candidate_text)
    overlay_path = Path(overlay_text)
    reference = _normalized(reference_path)
    candidate = _normalized(candidate_path)
    difference = ImageChops.difference(reference, candidate)
    mean_error = ImageStat.Stat(difference).mean[0] / 255.0
    reference_edges = _edge_mask(reference)
    candidate_edges = _edge_mask(candidate)
    intersection = 0
    union = 0
    if hasattr(reference_edges, "get_flattened_data"):
        reference_values = list(reference_edges.get_flattened_data())
        candidate_values = list(candidate_edges.get_flattened_data())
    else:
        reference_values = list(reference_edges.getdata())
        candidate_values = list(candidate_edges.getdata())
    for left, right in zip(reference_values, candidate_values):
        left_on = bool(left)
        right_on = bool(right)
        intersection += int(left_on and right_on)
        union += int(left_on or right_on)
    edge_jaccard = intersection / union if union else 1.0
    hash_distance = _hamming(dhash(reference), dhash(candidate))
    triage = max(
        0.0,
        min(
            100.0,
            100.0
            * (
                0.4 * (1.0 - hash_distance / 64.0)
                + 0.3 * (1.0 - mean_error)
                + 0.3 * edge_jaccard
            ),
        ),
    )

    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    overlay = Image.new("RGB", reference.size, "black")
    ref_pixels = reference_edges.convert("L")
    candidate_pixels = candidate_edges.convert("L")
    overlay.paste((255, 0, 0), mask=ref_pixels)
    overlay.paste((0, 255, 0), mask=candidate_pixels)
    overlap = ImageChops.multiply(ref_pixels, candidate_pixels)
    overlay.paste((255, 255, 255), mask=overlap)
    overlay.save(overlay_path, format="PNG")
    reference_sha256 = sha256_file(reference_path)
    candidate_sha256 = sha256_file(candidate_path)
    if reference_sha256 == candidate_sha256:
        media_relation = "same_file"
    elif hash_distance <= 3 and mean_error <= 0.08:
        media_relation = "derivative_image_candidate"
    else:
        media_relation = "visual_similarity_only"
    return {
        "candidate": str(candidate_path),
        "candidate_sha256": candidate_sha256,
        "reference_sha256": reference_sha256,
        "dhash_distance": hash_distance,
        "normalized_mean_abs_error": f"{mean_error:.6f}",
        "edge_jaccard": f"{edge_jaccard:.6f}",
        "triage_similarity": f"{triage:.2f}",
        "automated_media_relation": media_relation,
        "physical_product_inference": (
            "not_assessed; same instance/model/tooling requires independent manual evidence"
        ),
        "overlay_path": str(overlay_path),
        "warning": (
            "Triage only. Perspective, lighting and compression can dominate; "
            "this is not proof of a shared mold."
        ),
    }


def compare_images(
    reference: Path,
    candidates: list[Path],
    output_csv: Path,
    *,
    workers: int = 0,
) -> list[dict[str, Any]]:
    if workers < 0 or workers > 61:
        raise ValueError("workers must be 0 (auto) or between 1 and 61")
    output_csv = output_csv.resolve()
    overlay_dir = output_csv.parent / f"{output_csv.stem}_overlays"
    tasks = [
        (
            str(reference.resolve(strict=True)),
            str(candidate.resolve(strict=True)),
            str(overlay_dir / f"{index:03d}_{safe_name(candidate.stem)}.png"),
        )
        for index, candidate in enumerate(candidates, start=1)
    ]
    max_workers = (
        workers if workers > 0 else automatic_worker_count(candidate_count=len(tasks))
    )
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        rows = list(pool.map(_compare_one, tasks))
    write_csv(output_csv, FIELDS, rows)
    return rows


def run(args: object) -> int:
    rows = compare_images(
        args.reference, args.candidates, args.output, workers=args.workers
    )
    print(json.dumps({"compared": len(rows), "output": str(args.output)}, ensure_ascii=False))
    return 0
