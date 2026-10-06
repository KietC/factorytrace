#!/usr/bin/env python3
"""English: Hash source files after pruning generated trees and rejecting links.

中文：先排除生成目录并拒绝链接，再生成源码校验清单；使用 LF 保持跨平台字节一致。
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path


EXCLUDED_PARTS = {
    ".venv",
    ".build-venv",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
    "output",
    "smoke_cases",
    "wheelhouse",
}
EXCLUDED_SUFFIXES = {".pyc", ".zip", ".whl", ".gz"}
EXCLUDED_FILES = {
    "CHECKSUMS_SHA256.txt",
    "PACKAGE_CHECKSUMS_SHA256.txt",
    "environment.current.json",
    "verification.json",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def iter_source_files(root: Path):
    """Yield files without entering generated/private trees.

    中文：遍历前剪枝，避免枚举虚拟环境或生成目录中的非发布文件。
    """
    for current, directories, filenames in os.walk(root):
        current_path = Path(current)
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in EXCLUDED_PARTS and not directory.endswith(".egg-info")
        )
        for directory in directories:
            candidate = current_path / directory
            if candidate.is_symlink() or getattr(candidate, "is_junction", lambda: False)():
                raise RuntimeError(f"refusing linked directory in release tree: {candidate}")
        for filename in sorted(filenames):
            candidate = current_path / filename
            if candidate.suffix.lower() in EXCLUDED_SUFFIXES:
                continue
            if candidate.is_symlink():
                raise RuntimeError(f"refusing linked file in release tree: {candidate}")
            candidate.resolve().relative_to(root)
            yield candidate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or root / "CHECKSUMS_SHA256.txt"
    rows = []
    for path in iter_source_files(root):
        relative = path.relative_to(root)
        if path.name in EXCLUDED_FILES:
            continue
        rows.append(f"{sha256_file(path)}  {relative.as_posix()}")
    output.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print(f"files={len(rows)} output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
