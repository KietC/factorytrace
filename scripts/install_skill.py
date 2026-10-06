#!/usr/bin/env python3
"""Install one inspected Skill copy without overwriting an existing version.

安装一份已检查的 Skill 副本，不覆盖已有版本、不自动改全局配置。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

SKILL_NAME = "trace-source-factory"


def inventory(root: Path) -> dict[str, str]:
    """Hash regular source files, rejecting links and ignoring generated caches.

    对普通源码文件做哈希；拒绝链接，忽略生成缓存。
    """
    if root.is_symlink() or getattr(root, "is_junction", lambda: False)():
        raise ValueError("Linked Skill root is not supported.")
    result: dict[str, str] = {}
    for current, directories, files in os.walk(root):
        base = Path(current)
        directories[:] = sorted(d for d in directories if d not in {"__pycache__", ".git", ".venv"})
        for child in [*(base / d for d in directories), *(base / f for f in files)]:
            if child.is_symlink() or getattr(child, "is_junction", lambda: False)():
                raise ValueError("Linked Skill entries are not supported.")
        for filename in sorted(files):
            path = base / filename
            if path.suffix in {".pyc", ".pyo"}:
                continue
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def install(source: Path, target_dir: Path) -> dict[str, object]:
    """Copy atomically into an explicit target parent; never choose a host path.

    原子复制到明确的目标父目录，不猜测宿主技能路径。
    """
    source = source.expanduser()
    if source.is_symlink() or getattr(source, "is_junction", lambda: False)():
        raise ValueError("Linked Skill root is not supported.")
    source = source.resolve(strict=True)
    expected = inventory(source)
    if "SKILL.md" not in expected:
        raise ValueError("Source does not contain SKILL.md.")
    target_dir = target_dir.expanduser()
    # A linked parent may redirect writes into an unintended configuration tree.
    # 链接父目录可能把写入转到意外配置目录，因此逐级拒绝。
    for parent in [target_dir, *target_dir.parents]:
        if parent.is_symlink() or getattr(parent, "is_junction", lambda: False)():
            raise ValueError("Linked target directory is not supported.")
    target_dir = target_dir.resolve()
    destination = target_dir / SKILL_NAME
    if destination.is_relative_to(source):
        raise ValueError("Installation target must not be inside the source Skill.")
    target_dir.mkdir(parents=True, exist_ok=True)
    lock = target_dir / f".{SKILL_NAME}.install.lock"
    # Exclusive lock prevents concurrent instances from racing a final rename.
    # 独占锁避免本安装器并发运行时争抢最后重命名。
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        if destination.exists():
            if destination.is_dir() and inventory(destination) == expected:
                return {"status": "ALREADY_INSTALLED", "files": len(expected), "target": str(destination)}
            raise FileExistsError("A different Skill already exists. Back it up and choose another target; no overwrite was performed.")
        with tempfile.TemporaryDirectory(prefix=f".{SKILL_NAME}.install-", dir=target_dir) as temporary:
            staged = Path(temporary) / SKILL_NAME
            staged.mkdir()
            for relative in expected:
                target = staged / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source / relative, target)
            if inventory(staged) != expected:
                raise RuntimeError("Skill copy verification failed.")
            if destination.exists():
                raise FileExistsError("Target appeared while installing; installation stopped.")
            staged.rename(destination)
        return {"status": "INSTALLED", "files": len(expected), "target": str(destination)}
    finally:
        os.close(fd)
        lock.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1] / "skills" / SKILL_NAME)
    parser.add_argument("--target-dir", type=Path, required=True, help="Explicit skills parent directory / 明确指定 skills 父目录")
    args = parser.parse_args()
    try:
        result = install(args.source, args.target_dir)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Install failed / 安装失败: {error}\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
