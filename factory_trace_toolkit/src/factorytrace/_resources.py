"""English: Locate schemas, templates, and process packs in editable or wheel installs.

中文：定位可编辑安装或 wheel 中的资源目录；只允许受支持的资源类别，不依赖当前工作目录。
"""

from __future__ import annotations

import sysconfig
from pathlib import Path


RESOURCE_SHARE = Path("share") / "factory-trace-toolkit"


def resource_directory(name: str) -> Path:
    """Resolve a resource directory for source/editable and wheel installs.

    中文：优先定位源码资源，再定位安装资源；不支持的类别或缺失资源显式报错，不依赖工作目录猜路径。
    """
    if name not in {"schemas", "templates", "process_packs"}:
        raise ValueError(f"unsupported resource directory: {name}")
    source_candidate = Path(__file__).resolve().parents[2] / name
    if source_candidate.is_dir():
        return source_candidate
    data_root = Path(sysconfig.get_path("data"))
    installed_candidate = data_root / RESOURCE_SHARE / name
    if installed_candidate.is_dir():
        return installed_candidate
    raise FileNotFoundError(
        f"factory-trace resource directory is missing: {name}; "
        f"checked {source_candidate} and {installed_candidate}"
    )
