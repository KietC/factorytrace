"""English: Create labeled image derivatives while retaining original references and hashes.

中文：生成带变换标识的派生图并保留原件引用与哈希；裁剪、遮标和边缘图不能被标为现场原图。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps

from .common import atomic_write_json, safe_name, sha256_file, utc_now


def dhash(image: Image.Image, size: int = 8) -> str:
    gray = image.convert("L").resize((size + 1, size), Image.Resampling.LANCZOS)
    if hasattr(gray, "get_flattened_data"):
        values = list(gray.get_flattened_data())
    else:
        values = list(gray.getdata())
    value = 0
    for row in range(size):
        offset = row * (size + 1)
        for column in range(size):
            value = (value << 1) | int(
                values[offset + column] > values[offset + column + 1]
            )
    return f"{value:0{size * size // 4}x}"


def parse_region(value: str) -> dict[str, Any]:
    try:
        name, raw = value.split("=", 1)
        x, y, width, height = (int(part) for part in raw.split(","))
    except (ValueError, TypeError) as error:
        raise ValueError("region must be NAME=X,Y,WIDTH,HEIGHT") from error
    if not name.strip() or min(x, y) < 0 or width <= 0 or height <= 0:
        raise ValueError(f"invalid region: {value}")
    return {"name": name.strip(), "xywh": [x, y, width, height]}


def _validate_region(region: dict[str, Any], width: int, height: int) -> None:
    x, y, region_width, region_height = region["xywh"]
    if x + region_width > width or y + region_height > height:
        raise ValueError(
            f"region {region['name']!r} exceeds image bounds {width}x{height}"
        )


def _save(image: Image.Image, path: Path, role: str, transform: str) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=False, compress_level=6)
    return {
        "path": path.as_posix(),
        "sha256": sha256_file(path),
        "width": image.width,
        "height": image.height,
        "dhash64": dhash(image),
        "role": role,
        "transform": transform,
    }


def generate_variants(
    image_path: Path,
    case_root: Path,
    *,
    crop_plan: Path | None = None,
    crops: list[str] | None = None,
    masks: list[str] | None = None,
    mirror: bool = False,
) -> Path:
    case_root = case_root.resolve(strict=True)
    source = image_path.resolve(strict=True)
    source_sha = sha256_file(source)
    with Image.open(source) as opened:
        normalized = ImageOps.exif_transpose(opened).convert("RGB")

    plan: dict[str, Any] = {"crops": [], "masks": []}
    if crop_plan:
        plan = json.loads(crop_plan.read_text(encoding="utf-8"))
    plan["crops"] = list(plan.get("crops", [])) + [
        parse_region(value) for value in (crops or [])
    ]
    plan["masks"] = list(plan.get("masks", [])) + [
        parse_region(value) for value in (masks or [])
    ]
    for region in plan["crops"] + plan["masks"]:
        _validate_region(region, normalized.width, normalized.height)

    output = case_root / "work" / "variants" / source_sha[:12]
    output.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    records.append(
        _save(
            normalized,
            output / "V01_full.png",
            "whole-product",
            "EXIF orientation applied; RGB conversion",
        )
    )
    records.append(
        _save(
            normalized.convert("L"),
            output / "V02_grayscale.png",
            "whole-product",
            "8-bit grayscale",
        )
    )

    if plan["masks"]:
        masked = normalized.copy()
        draw = ImageDraw.Draw(masked)
        for region in plan["masks"]:
            x, y, width, height = region["xywh"]
            draw.rectangle((x, y, x + width, y + height), fill=(127, 127, 127))
        records.append(
            _save(
                masked,
                output / "V03_brand_masked.png",
                "brand-neutral-discovery",
                "neutral rectangles applied only to declared irrelevant brand regions",
            )
        )

    if mirror:
        records.append(
            _save(
                ImageOps.mirror(normalized),
                output / "V04_mirror.png",
                "whole-product-fallback",
                "horizontal mirror",
            )
        )

    for index, region in enumerate(plan["crops"], start=10):
        x, y, width, height = region["xywh"]
        crop = normalized.crop((x, y, x + width, y + height))
        role = region.get("role") or region["name"]
        records.append(
            _save(
                crop,
                output / f"V{index:02d}_crop_{safe_name(region['name'])}.png",
                role,
                f"rectangular crop xywh={region['xywh']}",
            )
        )

    for record in records:
        path = Path(record["path"])
        try:
            record["path"] = path.relative_to(case_root).as_posix()
        except ValueError:
            pass
    manifest = {
        "schema": 1,
        "created_at_utc": utc_now(),
        "source": {
            "path": str(source),
            "sha256": source_sha,
            "width": normalized.width,
            "height": normalized.height,
            "dhash64": dhash(normalized),
        },
        "policy": (
            "Original untouched. Variants use deterministic orientation, colorspace, "
            "grayscale, declared crops/masks, and optional mirror only; no generative edit."
        ),
        "variants": records,
    }
    manifest_path = output / "variant_manifest.json"
    atomic_write_json(manifest_path, manifest)
    return manifest_path


def run(args: object) -> int:
    manifest = generate_variants(
        args.image,
        args.case_root,
        crop_plan=args.crop_plan,
        crops=args.crop,
        masks=args.mask,
        mirror=args.mirror,
    )
    print(json.dumps({"manifest": str(manifest)}, ensure_ascii=False))
    return 0
