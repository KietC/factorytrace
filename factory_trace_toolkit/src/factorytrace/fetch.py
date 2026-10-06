"""English: Capture queued public URLs with bounded concurrency, retries, and metadata.

中文：按队列下载公开 URL 并保存元数据；全局并发不绕过单站节流，登录受限与下载失败不是产品不存在。
"""

from __future__ import annotations

import csv
import email.utils
import hashlib
import json
import os
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .common import (
    atomic_write_json,
    safe_name,
    sanitize_url_for_record,
    sha256_file,
    utc_now,
)


RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}
EXTENSIONS = {
    "text/html": ".html",
    "text/plain": ".txt",
    "application/json": ".json",
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "application/xml": ".xml",
    "text/xml": ".xml",
}


class HostGate:
    """Bound simultaneous host requests and space their start times.

    中文：同时限制每站连接数与请求启动间隔；提高全局workers不会取消单站节流。
    """
    def __init__(self, per_host: int, delay: float) -> None:
        self.per_host = max(1, per_host)
        self.delay = max(0.0, delay)
        self._lock = threading.Lock()
        self._semaphores: dict[str, threading.BoundedSemaphore] = {}
        self._last_request: dict[str, float] = {}

    def acquire(self, host: str) -> threading.BoundedSemaphore:
        with self._lock:
            semaphore = self._semaphores.setdefault(
                host, threading.BoundedSemaphore(self.per_host)
            )
        semaphore.acquire()
        while True:
            with self._lock:
                now = time.monotonic()
                wait = self.delay - (now - self._last_request.get(host, 0.0))
                if wait <= 0:
                    self._last_request[host] = now
                    return semaphore
            time.sleep(min(wait, 0.2))


class RobotsCache:
    """Cache robots rules by origin; a retrieval error uses an empty rule set.

    中文：按源站缓存robots规则；读取出错采用空规则集，此实现不是严格拒绝模式，仍须遵守站点授权与登录限制。
    """
    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent
        self._lock = threading.Lock()
        self._cache: dict[str, urllib.robotparser.RobotFileParser] = {}

    def allowed(self, url: str, timeout: float = 10.0) -> bool:
        parsed = urllib.parse.urlparse(url)
        key = f"{parsed.scheme}://{parsed.netloc}"
        with self._lock:
            parser = self._cache.get(key)
        if parser is None:
            robots_url = f"{key}/robots.txt"
            parser = urllib.robotparser.RobotFileParser(robots_url)
            try:
                request = urllib.request.Request(
                    robots_url, headers={"User-Agent": self.user_agent}
                )
                with urllib.request.urlopen(
                    request, timeout=min(max(timeout, 1.0), 15.0)
                ) as response:
                    payload = response.read(1024 * 1024 + 1)
                if len(payload) > 1024 * 1024:
                    raise ValueError("robots.txt exceeded 1 MiB")
                parser.parse(payload.decode("utf-8", errors="replace").splitlines())
            except (
                OSError,
                TimeoutError,
                ValueError,
                urllib.error.URLError,
            ):
                parser.parse([])
            with self._lock:
                existing = self._cache.get(key)
                if existing is None:
                    self._cache[key] = parser
                else:
                    parser = existing
        return parser.can_fetch(self.user_agent, url)


def _retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            moment = email.utils.parsedate_to_datetime(value)
            return max(0.0, (moment - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError):
            return None


def _extension(content_type: str) -> str:
    mime = content_type.split(";", 1)[0].strip().lower()
    return EXTENSIONS.get(mime, ".bin")


def _iter_queue(path: Path) -> Iterator[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for index, row in enumerate(csv.DictReader(stream), start=1):
            url = (row.get("url") or "").strip()
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                if url:
                    raise ValueError(f"invalid URL at row {index}: {url}")
                continue
            item = dict(row)
            item["id"] = (row.get("id") or f"URL-{index:04d}").strip()
            item["url"] = url
            yield item


def _fetch_one(
    row: dict[str, str],
    output_dir: Path,
    gate: HostGate,
    robots: RobotsCache,
    *,
    user_agent: str,
    timeout: float,
    retries: int,
    max_bytes: int,
    respect_robots: bool,
    force: bool,
) -> dict[str, Any]:
    url = row["url"]
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.casefold()
    base = f"{safe_name(row['id'])}_{hashlib.sha1(url.encode('utf-8')).hexdigest()[:12]}"
    metadata_path = output_dir / f"{base}.metadata.json"
    if metadata_path.exists() and not force:
        cached = json.loads(metadata_path.read_text(encoding="utf-8"))
        cached_path = Path(cached.get("local_path", ""))
        if (
            cached.get("status") == "downloaded"
            and cached_path.is_file()
            and (
                not cached.get("sha256")
                or sha256_file(cached_path).lower() == str(cached["sha256"]).lower()
            )
        ):
            cached["cache_hit"] = True
            return cached

    if respect_robots and not robots.allowed(url, timeout=timeout):
        result = {
            "id": row["id"],
            "candidate_id": row.get("candidate_id", ""),
            "kind": row.get("kind", ""),
            "request_url": sanitize_url_for_record(url),
            "status": "robots-denied",
            "access_status": "blocked_policy",
            "captured_at_utc": utc_now(),
            "notes": "Not fetched because robots.txt disallowed this user agent.",
        }
        atomic_write_json(metadata_path, result)
        return result

    error_text = ""
    attempts_made = 0
    for attempt in range(retries + 1):
        attempts_made = attempt + 1
        part_path: Path | None = None
        semaphore = gate.acquire(host)
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/pdf,image/*,application/json;q=0.9,*/*;q=0.5",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    status = getattr(response, "status", 200)
                    content_type = response.headers.get("Content-Type", "")
                    body_path = output_dir / f"{base}{_extension(content_type)}"
                    part_path = body_path.with_suffix(body_path.suffix + ".part")
                    total = 0
                    with part_path.open("wb") as stream:
                        while True:
                            chunk = response.read(1024 * 1024)
                            if not chunk:
                                break
                            total += len(chunk)
                            if total > max_bytes:
                                raise ValueError(
                                    f"response exceeded --max-bytes ({max_bytes})"
                                )
                            stream.write(chunk)
                    os.replace(part_path, body_path)
                    result = {
                        "id": row["id"],
                        "candidate_id": row.get("candidate_id", ""),
                        "kind": row.get("kind", ""),
                        "request_url": sanitize_url_for_record(url),
                        "final_url": sanitize_url_for_record(response.geturl()),
                        "http_status": status,
                        "status": "downloaded",
                        "access_status": "verified_download",
                        "attempts": attempt + 1,
                        "captured_at_utc": utc_now(),
                        "content_type": content_type,
                        "etag": response.headers.get("ETag", ""),
                        "last_modified": response.headers.get("Last-Modified", ""),
                        "content_length": total,
                        "sha256": sha256_file(body_path),
                        "local_path": str(body_path),
                        "notes": row.get("notes", ""),
                        "cache_hit": False,
                    }
                    atomic_write_json(metadata_path, result)
                    return result
            except urllib.error.HTTPError as error:
                if part_path is not None:
                    part_path.unlink(missing_ok=True)
                status = error.code
                error_text = f"HTTP {status}: {error.reason}"
                if status not in RETRY_STATUS or attempt >= retries:
                    break
                wait = _retry_after_seconds(error.headers.get("Retry-After"))
                time.sleep(
                    min(60.0, wait if wait is not None else (2**attempt + random.random()))
                )
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
                if part_path is not None:
                    part_path.unlink(missing_ok=True)
                error_text = f"{type(error).__name__}: {error}"
                if attempt >= retries:
                    break
                time.sleep(min(30.0, 2**attempt + random.random()))
        finally:
            semaphore.release()

    result = {
        "id": row["id"],
        "candidate_id": row.get("candidate_id", ""),
        "kind": row.get("kind", ""),
        "request_url": sanitize_url_for_record(url),
        "status": "failed",
        "access_status": (
            "rate_limited"
            if "HTTP 429" in error_text
            else "blocked_login"
            if "HTTP 401" in error_text
            else "blocked_policy"
            if "HTTP 403" in error_text
            else "service_unavailable"
            if any(f"HTTP {code}" in error_text for code in (500, 502, 503, 504))
            else "timeout"
            if "Timeout" in error_text or "timed out" in error_text.lower()
            else "failed_unknown"
        ),
        "attempts": attempts_made,
        "captured_at_utc": utc_now(),
        "error": error_text,
        "notes": row.get("notes", ""),
    }
    atomic_write_json(metadata_path, result)
    return result


def fetch_queue(
    queue: Path,
    case_root: Path,
    *,
    workers: int = 8,
    per_host: int = 2,
    delay: float = 1.0,
    timeout: float = 20.0,
    retries: int = 2,
    max_bytes: int = 25 * 1024 * 1024,
    user_agent: str = "FactoryTraceToolkit/2.0 evidence capture",
    respect_robots: bool = True,
    force: bool = False,
) -> list[dict[str, Any]]:
    """Capture a bounded URL queue and save sorted results with access-status metadata.

    中文：有上限地提交URL任务，保存排序回执、哈希与访问状态；失败或受限说明通道状态，不是产品缺席的反证。
    """
    rows = iter(_iter_queue(queue))
    output_dir = case_root.resolve(strict=True) / "evidence" / "web"
    output_dir.mkdir(parents=True, exist_ok=True)
    gate = HostGate(per_host=per_host, delay=delay)
    robots = RobotsCache(user_agent)
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        pending: set[Future[dict[str, Any]]] = set()

        def submit_next() -> bool:
            try:
                row = next(rows)
            except StopIteration:
                return False
            pending.add(
                pool.submit(
                    _fetch_one,
                    row,
                    output_dir,
                    gate,
                    robots,
                    user_agent=user_agent,
                    timeout=timeout,
                    retries=retries,
                    max_bytes=max_bytes,
                    respect_robots=respect_robots,
                    force=force,
                )
            )
            return True

        max_pending = max(1, workers) * 2
        while len(pending) < max_pending and submit_next():
            pass
        while pending:
            completed, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in completed:
                results.append(future.result())
            while len(pending) < max_pending and submit_next():
                pass
    results.sort(key=lambda item: str(item.get("id", "")))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    atomic_write_json(
        case_root / "logs" / f"fetch_results_{stamp}.json",
        {"schema": 2, "created_at_utc": utc_now(), "results": results},
    )
    return results


def run(args: object) -> int:
    results = fetch_queue(
        args.queue,
        args.case_root,
        workers=args.workers,
        per_host=args.per_host,
        delay=args.delay,
        timeout=args.timeout,
        retries=args.retries,
        max_bytes=args.max_bytes,
        user_agent=args.user_agent,
        respect_robots=not args.ignore_robots,
        force=args.force,
    )
    print(
        json.dumps(
            {
                "total": len(results),
                "downloaded": sum(item.get("status") == "downloaded" for item in results),
                "failed": sum(item.get("status") == "failed" for item in results),
                "robots_denied": sum(
                    item.get("status") == "robots-denied" for item in results
                ),
            },
            ensure_ascii=False,
        )
    )
    return 0 if not any(item.get("status") == "failed" for item in results) else 2
