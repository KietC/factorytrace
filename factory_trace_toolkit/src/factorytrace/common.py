"""English: Provide UTF-8, path safety, hashes, redaction, atomic writes, and short file locks.

中文：提供编码、路径、哈希、脱敏、原子写入与短时文件锁；替换完整文件不等于多步事务，锁超时必须显式处理。
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import uuid
from contextlib import AbstractContextManager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
SENSITIVE_URL_KEY = re.compile(
    r"(?i)(?:^|[_-])(?:access[_-]?token|auth|authorization|code|cookie|credential|"
    r"key|oauth|pass(?:word)?|secret|session|sig(?:nature)?|skey|token)(?:$|[_-])"
)


def configure_utf8_stdio() -> None:
    """Make CLI JSON/text deterministic on legacy Windows code pages.

    中文：为旧 Windows 代码页配置 UTF-8 输出；不可重配的封装流保留原状。
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, OSError, ValueError):
            # Embedded/frozen runtimes can expose a non-reconfigurable wrapper.
            # 中文：内嵌或冻结环境的流可能不支持重配置，不能因此中断业务命令。
            continue


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(value: str, fallback: str = "item", max_length: int = 180) -> str:
    normalized = unicodedata.normalize("NFC", value)
    normalized = re.sub(r"[\x00-\x1f<>:\"/\\|?*]", "_", normalized)
    normalized = normalized.rstrip(" .")
    if not normalized:
        normalized = fallback
    stem = Path(normalized).stem
    if stem.upper() in WINDOWS_RESERVED:
        normalized = f"_{normalized}"
    if len(normalized) > max_length:
        suffix = Path(normalized).suffix[:20]
        normalized = normalized[: max_length - len(suffix) - 9] + "-" + hashlib.sha1(
            normalized.encode("utf-8")
        ).hexdigest()[:8] + suffix
    return normalized


def safe_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value.strip())
    normalized = re.sub(r"[^\w.-]+", "-", normalized, flags=re.UNICODE)
    normalized = normalized.strip("-.")
    if not normalized:
        normalized = f"case-{hashlib.sha1(value.encode('utf-8')).hexdigest()[:8]}"
    return safe_name(normalized, fallback="case")


def sanitize_url_for_record(value: str) -> str:
    """Redact credentials and sensitive queries while retaining provenance.

    中文：保留可追溯 URL 结构并隐去凭据及敏感参数；不会替代对网页正文的隐私审查。
    """
    if not value:
        return ""
    parsed = urllib.parse.urlsplit(value)
    hostname = parsed.hostname or ""
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    netloc = hostname
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    if parsed.username or parsed.password:
        netloc = f"[REDACTED]@{netloc}"
    query = urllib.parse.urlencode(
        [
            (
                key,
                "[REDACTED]" if SENSITIVE_URL_KEY.search(key) else query_value,
            )
            for key, query_value in urllib.parse.parse_qsl(
                parsed.query, keep_blank_values=True
            )
        ],
        doseq=True,
    )
    fragment = parsed.fragment
    if re.search(r"(?i)(token|auth|secret|session|skey|signature)", fragment):
        fragment = "[REDACTED]"
    return urllib.parse.urlunsplit(
        (parsed.scheme, netloc or parsed.netloc, parsed.path, query, fragment)
    )


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """Write a sibling temporary file, then replace the complete destination.

    中文：先写同目录临时文件再整体替换目标；单文件原子替换不提供跨文件事务，需与案件锁配合。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(text, encoding=encoding, newline="\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(
        path, json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def path_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


class FileLock(AbstractContextManager["FileLock"]):
    """Portable lock based on exclusive lock-file creation.

    It is deliberately simple: state updates are short and are followed by an
    atomic replace. A stale lock is removed only after its age exceeds the
    configured threshold.

    中文：通过排他创建锁文件协调短时状态更新，再以原子替换提交；仅超过配置年龄才删除旧锁，不是跨主机租约。
    """

    def __init__(
        self,
        path: Path,
        timeout: float = 30.0,
        stale_after: float = 300.0,
        poll: float = 0.05,
    ) -> None:
        self.path = path
        self.timeout = timeout
        self.stale_after = stale_after
        self.poll = poll
        self.fd: int | None = None

    def __enter__(self) -> "FileLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self.fd = os.open(
                    self.path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    0o600,
                )
                os.write(
                    self.fd,
                    json.dumps(
                        {"pid": os.getpid(), "created_at_utc": utc_now()}
                    ).encode("utf-8"),
                )
                return self
            except FileExistsError:
                try:
                    age = time.time() - self.path.stat().st_mtime
                    if age > self.stale_after:
                        self.path.unlink()
                        continue
                except FileNotFoundError:
                    continue
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"timed out waiting for lock: {self.path}")
                time.sleep(self.poll)

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
