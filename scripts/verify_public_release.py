#!/usr/bin/env python3
"""Check a public source tree without publishing case or host receipts.

检查公开源码树；不发布案件数据或宿主回执。
Static scanning reduces risk but cannot prove that all arbitrary data is public.
静态扫描降低风险，但不能证明任意数据全部可公开。
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
EXCLUDED = {".git", ".venv", ".build-venv", "__pycache__", ".pytest_cache", "build", "dist", "output", "wheelhouse"}
FORBIDDEN_DIRS = {"cases", "case_lessons", "evidence", "artifacts", "logs", "candidates", "backup", "smoke_cases"}
TEXT = {".py", ".ps1", ".sh", ".md", ".json", ".jsonl", ".csv", ".txt", ".toml", ".yaml", ".yml", ".sha256"}
SPECIAL_SOURCE_NAMES = {"LICENSE", "VERSION", ".gitignore", ".gitattributes", ".editorconfig"}
CONTACT = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PRIVATE_IPV4 = re.compile(r"\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b")


def hash_file(path: Path) -> str:
    """Hash streams rather than loading every trained dataset at once.

    流式计算哈希，不同时把所有语言权重读入内存。
    """
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def files_in(root: Path):
    """Inspect source-only files while refusing links and private data trees.

    只检查源码，拒绝链接和私有案件目录。
    """
    # Resolve once so Windows short-name TEMP paths compare with long paths.
    # 统一解析根目录，避免 Windows 临时目录短文件名与长路径比较失败。
    root = root.resolve(strict=True)
    for current, directories, files in os.walk(root):
        current_path = Path(current)
        for name in directories:
            if name in FORBIDDEN_DIRS:
                raise ValueError(f"Forbidden data directory: {(current_path / name).relative_to(root)}")
        directories[:] = sorted(d for d in directories if d not in EXCLUDED and not d.endswith(".egg-info"))
        for name in directories:
            child = current_path / name
            if child.is_symlink() or getattr(child, "is_junction", lambda: False)():
                raise ValueError("Linked directory is not publishable.")
        for filename in sorted(files):
            path = current_path / filename
            if path.is_symlink():
                raise ValueError("Linked file is not publishable.")
            path.resolve().relative_to(root)
            if path.suffix in {".pyc", ".pyo"}:
                continue
            if filename.startswith((".env", "environment.current", "verification", "DEPLOYMENT_RECEIPT", "SOURCES_AND_PROVENANCE")) or path.suffix.lower() in {".pem", ".key", ".har", ".xlsx", ".docx", ".pdf", ".zip", ".whl"}:
                raise ValueError(f"Forbidden generated/private file: {path.relative_to(root)}")
            # Unknown binary files are not made public just because no pattern matched.
            # 未知二进制不能因为未命中关键词就被公开发布。
            allowed_binary = {
                ".png": root / "factory_trace_toolkit/resources/ocr_probes",
                ".otf": root / "factory_trace_toolkit/resources/fonts",
                ".traineddata": root / "factory_trace_toolkit/resources/tessdata",
            }
            suffix = path.suffix.lower()
            if suffix in allowed_binary:
                if path.parent != allowed_binary[suffix]:
                    raise ValueError(f"Unreviewed binary location: {path.relative_to(root)}")
            elif suffix not in TEXT and filename not in SPECIAL_SOURCE_NAMES:
                raise ValueError(f"Unreviewed file type: {path.relative_to(root)}")
            yield path


def verify(root: Path, write_manifest: bool = False) -> dict[str, object]:
    """Validate code, relative links, public licensing and release inventory.

    校验代码、相对链接、公开许可与发布文件清单。
    """
    if root.is_symlink() or getattr(root, "is_junction", lambda: False)():
        raise ValueError("Linked release root is not publishable.")
    root = root.resolve(strict=True)
    spec = importlib.util.spec_from_file_location("public_release_scan", root / "factory_trace_toolkit/scripts/verify_toolkit.py")
    scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scanner)
    problems: list[str] = []
    sources = list(files_in(root))
    for required in ("LICENSE", "README.md", "DEPLOY.md", "THIRD_PARTY_NOTICES.md", "docs/SETUP_AND_PITFALLS.md", "docs/PUBLIC_RELEASE_AUDIT.md", "skills/trace-source-factory/SKILL.md"):
        if not (root / required).is_file():
            problems.append(f"Missing: {required}")
    for path in sources:
        relative = path.relative_to(root).as_posix()
        if path.suffix.lower() not in TEXT:
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".py":
            ast.parse(text, filename=relative)
        for finding in scanner._portable_findings(path, text):
            problems.append(f"{relative}: {finding}")
        # Contacts may appear only as explicitly reserved synthetic examples.
        # 联系方式只能是明确保留给示例使用的虚构域名。
        for address in CONTACT.findall(text):
            domain = address.split("@", 1)[1].casefold()
            if not (domain in {"example.com", "example.org", "example.net"} or domain.endswith((".example", ".invalid", ".test"))):
                problems.append(f"{relative}: unreviewed email contact")
        if PRIVATE_IPV4.search(text):
            problems.append(f"{relative}: private network address")
        if path.suffix == ".md":
            for target in re.findall(r"\[[^\]]+\]\(([^\s)]+)\)", text):
                if re.match(r"[a-z]+:", target, re.I) or target.startswith(("#", "/")):
                    continue
                target = target.split("#", 1)[0]
                if target and not (path.parent / target).exists():
                    problems.append(f"{relative}: broken relative link {target}")
    # The Noto font is included rather than leaking a proprietary host font hash.
    # 随包验证 Noto 字体，不保留私有宿主字体的指纹。
    font_root = root / "factory_trace_toolkit/resources/fonts"
    manifest = json.loads((font_root / "MANIFEST.json").read_text(encoding="utf-8"))
    for name, digest in manifest["files"].items():
        if hash_file(font_root / name) != digest:
            problems.append(f"Font manifest mismatch: {name}")
    if "MIT License" not in (root / "LICENSE").read_text(encoding="utf-8"):
        problems.append("Root MIT license missing.")
    release_manifest = root / "SOURCE_MANIFEST.sha256"
    population = sorted((p for p in sources if p != release_manifest), key=lambda p: p.relative_to(root).as_posix())
    expected = {p.relative_to(root).as_posix(): hash_file(p) for p in population}
    if write_manifest and not problems:
        release_manifest.write_text("".join(f"{digest}  {name}\n" for name, digest in expected.items()), encoding="utf-8", newline="\n")
    if not release_manifest.is_file():
        problems.append("Source manifest missing.")
    else:
        recorded = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in release_manifest.read_text(encoding="utf-8").splitlines() if line}
        if recorded != expected:
            problems.append("Source manifest hash or coverage mismatch.")
    return {"status": "FAIL" if problems else "PASS", "source_files": len(sources), "problems": problems,
            "limits": "Static patterns are a release gate, not proof of arbitrary content ownership or authenticity."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(args.root, args.write_manifest)
    except (OSError, ValueError, SyntaxError) as error:
        result = {"status": "FAIL", "problems": [str(error)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
