#!/usr/bin/env python3
"""English: Build a source-only archive and SHA-256 sidecar from an explicit root.

中文：从指定根目录构建仅含源码的归档与校验文件；排除环境及输出，拒绝链接越界，不收集案件。
"""
from __future__ import annotations

import argparse
import hashlib
import os
import zipfile
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
    "SOURCES_AND_PROVENANCE.md",
    "ENVIRONMENT_CHANGE_RECEIPT_2026-08-01.md",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def iter_package_files(root: Path):
    """Prune excluded trees before enumerating package inputs.

    中文：先剪枝再枚举发布文件；符号链接或 Windows junction 会直接报错。
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
                raise RuntimeError(f"refusing linked directory in package tree: {candidate}")
        for filename in sorted(filenames):
            candidate = current_path / filename
            if candidate.is_symlink():
                raise RuntimeError(f"refusing linked file in package tree: {candidate}")
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
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    output = (
        args.output.resolve()
        if args.output
        else root.parent / f"{root.name}_v{version}_portable.zip"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    files = []
    for path in iter_package_files(root):
        relative = path.relative_to(root)
        if path.name in EXCLUDED_FILES:
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        files.append(path)
    with zipfile.ZipFile(
        output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        package_checksums = []
        for path in files:
            relative = path.relative_to(root)
            archive.write(path, (Path(root.name) / relative).as_posix())
            package_checksums.append(f"{sha256_file(path)}  {relative.as_posix()}")
        archive.writestr(
            (Path(root.name) / "PACKAGE_CHECKSUMS_SHA256.txt").as_posix(),
            "\n".join(package_checksums) + "\n",
        )
    digest = sha256_file(output)
    checksum_path = output.with_suffix(output.suffix + ".sha256")
    checksum_path.write_text(f"{digest}  {output.name}\n", encoding="utf-8", newline="\n")
    print(f"files={len(files)} output={output} sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
