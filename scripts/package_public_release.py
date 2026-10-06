#!/usr/bin/env python3
"""Package only the reviewed public manifest, never the whole working directory.

只打包已经审核的公开清单，不递归打包整个工作目录。
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import zipfile
from pathlib import Path, PurePosixPath


def sha256_file(path: Path) -> str:
    """Stream the digest / 流式计算摘要。"""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_manifest(path: Path) -> dict[str, str]:
    """Reject duplicate, malformed and escaping archive paths.

    拒绝重复、格式错误或可能逃逸归档根目录的路径。
    """
    records: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        digest, separator, name = line.partition("  ")
        parts = PurePosixPath(name).parts
        if (not separator or not re.fullmatch(r"[A-Fa-f0-9]{64}", digest)
                or not name or name.startswith("/") or "\\" in name or ":" in name
                or any(part in {".", ".."} for part in name.split("/"))
                or not parts or name in records):
            raise ValueError("Invalid or duplicate source-manifest entry.")
        records[name] = digest.upper()
    return records


def package(root: Path, output: Path) -> dict[str, object]:
    """Require privacy PASS, then verify every compressed file and checksum.

    隐私检查通过后，逐个验证压缩文件的内容与摘要。
    """
    root = root.resolve(strict=True)
    output = output.resolve()
    try:
        output.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("Store the release archive outside the source repository.")
    if output.suffix.lower() != ".zip" or output.exists() or output.with_suffix(".zip.sha256").exists():
        raise ValueError("Choose a new .zip output; existing archives/checksums are not overwritten.")
    spec = importlib.util.spec_from_file_location("release_gate", root / "scripts/verify_public_release.py")
    assert spec is not None and spec.loader is not None
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    review = gate.verify(root)
    if review["status"] != "PASS":
        raise ValueError(f"Public-source review failed: {review['problems']}")
    records = read_manifest(root / "SOURCE_MANIFEST.sha256")
    records["SOURCE_MANIFEST.sha256"] = sha256_file(root / "SOURCE_MANIFEST.sha256")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation protects an earlier release; fixed ZIP metadata omits host timestamps.
    # 独占创建保留旧发布包；固定 ZIP 元数据不泄漏宿主文件时间。
    with zipfile.ZipFile(output, mode="x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, digest in sorted(records.items()):
            source = (root / name).resolve(strict=True)
            source.relative_to(root)
            if sha256_file(source) != digest:
                raise ValueError(f"Source changed while packaging: {name}")
            info = zipfile.ZipInfo(f"factorytrace/{name}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            with source.open("rb") as reader, archive.open(info, "w") as writer:
                shutil.copyfileobj(reader, writer, 1024 * 1024)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None or len(archive.infolist()) != len(records):
            raise ValueError("Archive CRC or coverage validation failed.")
        for name, expected in records.items():
            digest = hashlib.sha256()
            with archive.open(f"factorytrace/{name}") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest().upper() != expected:
                raise ValueError(f"Archive digest mismatch: {name}")
    archive_digest = sha256_file(output)
    output.with_suffix(".zip.sha256").write_text(
        f"{archive_digest}  {output.name}\n", encoding="utf-8", newline="\n"
    )
    return {"status": "PASS", "archive": output.name, "files": len(records),
            "bytes": output.stat().st_size, "sha256": archive_digest}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = package(args.root, args.output)
    except (OSError, ValueError) as error:
        result = {"status": "FAIL", "error": str(error)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
