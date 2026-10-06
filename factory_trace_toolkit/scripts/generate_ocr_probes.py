#!/usr/bin/env python3
"""Regenerate synthetic OCR probes from an explicitly identified open font.

使用明确指定的开源字体重新生成合成 OCR 探针，不读取生产照片。
Keep the font hash and rendering settings stable for byte-level reproduction.
保持字体哈希与渲染参数稳定，才能按字节复现。
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version


PROBES = (
    ("chi_sim_probe.png", "工厂生产 316 不锈钢"),
    ("chi_tra_probe.png", "工廠生產 316 不鏽鋼"),
)
CANVAS = (1600, 280)
TEXT_ORIGIN = (45, 55)
# Larger glyphs are not always easier for the fixed OCR engine to recognize.
# 固定 OCR 引擎下字号越大不一定越准；此参数已通过简繁严格文字验证。
FONT_SIZE = 96
STROKE_WIDTH = 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic probe bytes for one explicit font and record "
            "the font/Pillow provenance in MANIFEST.json."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "resources" / "ocr_probes",
    )
    parser.add_argument(
        "--font",
        type=Path,
        required=True,
        help="CJK TrueType/OpenType/TTC font; no platform-dependent fallback is used.",
    )
    parser.add_argument("--font-size", type=int, default=FONT_SIZE)
    parser.add_argument("--stroke-width", type=int, default=STROKE_WIDTH)
    args = parser.parse_args()
    if not 16 <= args.font_size <= 180 or not 0 <= args.stroke_width <= 3:
        parser.error("font size must be 16..180 and stroke width 0..3")
    # Never use the host's default/proprietary font as a hidden dependency.
    # 不把宿主默认字体或私有字体作为隐含依赖。
    font_path = args.font.expanduser().resolve(strict=True)
    if not font_path.is_file():
        raise FileNotFoundError(f"font is not a regular file: {font_path}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(str(font_path), args.font_size, index=0)
    file_records: dict[str, dict[str, str]] = {}
    for name, text in PROBES:
        image = Image.new("L", CANVAS, 255)
        drawing = ImageDraw.Draw(image)
        drawing.text(
            TEXT_ORIGIN,
            text,
            font=font,
            fill=0,
            stroke_width=args.stroke_width,
        )
        target = args.output_dir / name
        temporary = target.with_name(f".{target.name}.tmp")
        image.save(temporary, format="PNG", optimize=False)
        temporary.replace(target)
        file_records[name] = {"text": text, "sha256": sha256_file(target)}

    # Record only public font identity, never its local absolute source path.
    # 只记录公开字体身份，不保存其本机绝对路径。
    manifest = {
        "schema": 2,
        "generator": "scripts/generate_ocr_probes.py",
        "generation": {
            "font_name": font_path.name,
            "font_sha256": sha256_file(font_path),
            "font_index": 0,
            "pillow_version": pillow_version,
            "image_mode": "L",
            "canvas": list(CANVAS),
            "font_size": args.font_size,
            "text_origin": list(TEXT_ORIGIN),
            "stroke_width": args.stroke_width,
            "background": 255,
            "foreground": 0,
        },
        "files": file_records,
    }
    manifest_path = args.output_dir / "MANIFEST.json"
    temporary_manifest = manifest_path.with_name(".MANIFEST.json.tmp")
    temporary_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary_manifest.replace(manifest_path)
    print(
        json.dumps(
            {
                "status": "PASS",
                "font_name": font_path.name,
                "font_sha256": manifest["generation"]["font_sha256"],
                "pillow_version": pillow_version,
                "output_dir": str(args.output_dir.resolve()),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
