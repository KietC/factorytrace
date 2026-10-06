"""English: Copy supplied files into the original-artifact store and inventory their hashes.

中文：将输入副本存入原件库并记录哈希与元信息；并发读取不改源文件，清单更新由文件锁串行保护。
"""

from __future__ import annotations

import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from PIL import ExifTags, Image

from .common import (
    FileLock,
    atomic_write_json,
    load_json,
    safe_name,
    sanitize_url_for_record,
    sha256_file,
    utc_now,
)


def _image_metadata(path: Path) -> dict[str, Any] | None:
    try:
        with Image.open(path) as image:
            exif = {
                ExifTags.TAGS.get(key, str(key)): str(value)
                for key, value in image.getexif().items()
            }
            return {
                "format": image.format,
                "mode": image.mode,
                "width": image.width,
                "height": image.height,
                "frames": getattr(image, "n_frames", 1),
                "exif": exif,
            }
    except (OSError, ValueError):
        return None


def _profile_source(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError(f"not a file: {resolved}")
    stat = resolved.stat()
    return {
        "source": resolved,
        "sha256": sha256_file(resolved),
        "size": stat.st_size,
        "filesystem_modified_at_utc": datetime.fromtimestamp(
            stat.st_mtime, timezone.utc
        ).isoformat(),
        "image": _image_metadata(resolved),
    }


def _expand_inputs(paths: Iterable[Path], recursive: bool) -> list[Path]:
    expanded: list[Path] = []
    for path in paths:
        resolved = path.resolve(strict=True)
        if resolved.is_file():
            expanded.append(resolved)
        elif resolved.is_dir() and recursive:
            expanded.extend(item for item in resolved.rglob("*") if item.is_file())
        else:
            raise ValueError(f"directory requires --recursive: {resolved}")
    return sorted(set(expanded), key=lambda item: str(item).casefold())


def ingest(
    paths: Iterable[Path],
    case_root: Path,
    *,
    relationship: str,
    source_url: str = "",
    recursive: bool = False,
    workers: int = 4,
) -> list[dict[str, Any]]:
    """Profile inputs concurrently, then serialize original-store/manifest updates.

    中文：并发读取输入元数据，再在案件锁内提交原件副本与清单；保留输入源字节，相同内容仍保留文件来源关系。
    """
    case_root = case_root.resolve(strict=True)
    originals = case_root / "artifacts" / "original"
    originals.mkdir(parents=True, exist_ok=True)
    sources = _expand_inputs(paths, recursive)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        profiles = list(pool.map(_profile_source, sources))

    records: list[dict[str, Any]] = []
    for profile in profiles:
        source: Path = profile["source"]
        destination = originals / safe_name(source.name)
        if destination.exists() and sha256_file(destination) != profile["sha256"]:
            destination = originals / (
                f"{destination.stem}.{profile['sha256'][:8]}{destination.suffix}"
            )
        if destination.resolve() != source.resolve() and not destination.exists():
            shutil.copy2(source, destination)
        record = {
            "artifact_id": f"ART-{profile['sha256'][:12].upper()}",
            "relative_path": destination.relative_to(case_root).as_posix(),
            "original_sources": [str(source)],
            "source_url": sanitize_url_for_record(source_url),
            "size": destination.stat().st_size,
            "sha256": profile["sha256"],
            "acquired_at_utc": utc_now(),
            "filesystem_modified_at_utc": profile["filesystem_modified_at_utc"],
            "produced_by": "factorytrace ingest",
            "relationship": relationship,
            "image": profile["image"],
        }
        records.append(record)

    manifest_path = case_root / "manifest.json"
    with FileLock(case_root / ".manifest.lock"):
        manifest = load_json(manifest_path)
        artifacts = manifest.setdefault("artifacts", [])
        by_path = {item.get("relative_path"): item for item in artifacts}
        for record in records:
            existing = by_path.get(record["relative_path"])
            if existing is None:
                artifacts.append(record)
                by_path[record["relative_path"]] = record
            else:
                aliases = existing.setdefault("original_sources", [])
                for source in record["original_sources"]:
                    if source not in aliases:
                        aliases.append(source)
        atomic_write_json(manifest_path, manifest)
    return records


def run(args: object) -> int:
    records = ingest(
        args.paths,
        args.case_root,
        relationship=args.relationship,
        source_url=args.source_url,
        recursive=args.recursive,
        workers=args.workers,
    )
    print(json.dumps({"ingested": len(records), "records": records}, ensure_ascii=False))
    return 0
