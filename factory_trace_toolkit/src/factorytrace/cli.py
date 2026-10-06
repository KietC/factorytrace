"""English: Parse commands and dispatch to deterministic local evidence operations.

中文：解析参数并调用确定性的本地证据操作；数据默认写入指定案件，CLI 不自行取得平台登录授权。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import urllib.parse
import uuid
from pathlib import Path
from typing import Callable

from . import __version__
from . import (
    audit,
    compare,
    environment,
    fetch,
    init_case,
    intake,
    ledger,
    materials,
    provenance,
    queries,
    reporting,
    scoring,
    v2_commands,
    variants,
)
from .common import FileLock, configure_utf8_stdio, safe_slug, utc_now


EXECUTION_FIELDS = [
    "timestamp_utc",
    "command_id",
    "actor",
    "tool",
    "tool_version",
    "command_or_action",
    "working_directory",
    "input_artifact_ids",
    "output_paths",
    "exit_code",
    "status",
    "notes",
]


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def _nonnegative_int(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return number


def _compare_workers(value: str) -> int:
    number = _nonnegative_int(value)
    if number > 61:
        raise argparse.ArgumentTypeError(
            "must be 0 (auto) or <=61; higher values are unsafe/nonportable"
        )
    return number


def _positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def _nonnegative_float(value: str) -> float:
    number = float(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="factorytrace",
        description=(
            "Evidence-first source-factory tracing. It separates seller, payment "
            "entity, manufacturer, manufacturing site, process, and exact SKU."
        ),
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    command = subparsers.add_parser("init", help="Create a reproducible case")
    command.add_argument("name")
    command.add_argument("--root", type=Path, default=Path.cwd() / "cases")
    command.add_argument(
        "--objective",
        default="Trace the actual manufacturing entity, site, process, and exact SKU.",
    )
    command.add_argument("--time-zone", default="UTC")
    command.add_argument("--resume", action="store_true")
    command.set_defaults(handler=init_case.run)

    command = subparsers.add_parser(
        "migrate", help="Non-destructively copy and migrate a v1 case to schema v2"
    )
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument("--to", type=int, choices=(2,), required=True)
    command.add_argument("--output-root", type=Path)
    command.add_argument(
        "--copy-mode",
        choices=("canonical",),
        default="canonical",
        help="Copy only canonical case evidence and refuse links/junctions",
    )
    command.set_defaults(handler=v2_commands.run_migrate)

    command = subparsers.add_parser(
        "validate", help="Validate case/candidates/evidence and regenerated v2 assessments"
    )
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument("--output", type=Path)
    command.set_defaults(handler=v2_commands.run_validate)

    command = subparsers.add_parser("ingest", help="Freeze and hash source artifacts")
    command.add_argument("paths", type=Path, nargs="+")
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument(
        "--relationship",
        default="Untouched source artifact for product/factory tracing",
    )
    command.add_argument("--source-url", default="")
    command.add_argument("--recursive", action="store_true")
    command.add_argument(
        "--workers", type=_positive_int, default=max(2, min(16, (os.cpu_count() or 4)))
    )
    command.set_defaults(handler=intake.run)

    command = subparsers.add_parser(
        "variants", help="Create deterministic search crops with lineage"
    )
    command.add_argument("image", type=Path)
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument("--crop-plan", type=Path)
    command.add_argument("--crop", action="append", default=[])
    command.add_argument("--mask", action="append", default=[])
    command.add_argument("--mirror", action="store_true")
    command.set_defaults(handler=variants.run)

    command = subparsers.add_parser(
        "queries", help="Generate brand-neutral multilingual search queries"
    )
    command.add_argument(
        "--profile",
        type=Path,
        help="Defaults to CASE_ROOT/work/product_profile.json",
    )
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument(
        "--pack",
        action="append",
        default=[],
        help="Add process-pack requirements to the brand-neutral query set",
    )
    command.add_argument("--max-queries", type=_positive_int, default=200)
    command.set_defaults(handler=queries.run)

    command = subparsers.add_parser(
        "fetch", help="Capture explicit public URLs with polite parallelism"
    )
    command.add_argument("queue", type=Path)
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument("--workers", type=_positive_int, default=8)
    command.add_argument("--per-host", type=_positive_int, default=2)
    command.add_argument("--delay", type=_nonnegative_float, default=1.0)
    command.add_argument("--timeout", type=_positive_float, default=20.0)
    command.add_argument("--retries", type=_nonnegative_int, default=2)
    command.add_argument("--max-bytes", type=_positive_int, default=25 * 1024 * 1024)
    command.add_argument(
        "--user-agent", default="FactoryTraceToolkit/2.0 evidence capture"
    )
    command.add_argument(
        "--ignore-robots",
        action="store_true",
        help="Only for explicit URLs where you have permission; never bypass auth/CAPTCHA.",
    )
    command.add_argument("--force", action="store_true")
    command.set_defaults(handler=fetch.run)

    command = subparsers.add_parser(
        "compare", help="Triage visual similarity and build edge overlays"
    )
    command.add_argument("reference", type=Path)
    command.add_argument("candidates", type=Path, nargs="+")
    command.add_argument("--output", type=Path, required=True)
    command.add_argument(
        "--workers",
        type=_compare_workers,
        default=0,
        help="0=auto (max 8); explicit values must be 1..61",
    )
    command.set_defaults(handler=compare.run)

    command = subparsers.add_parser(
        "score", help="Compute ESS; manual probabilities are not trusted"
    )
    command.add_argument("candidates", type=Path, nargs="+")
    command.add_argument("--output-dir", type=Path, required=True)
    command.set_defaults(handler=scoring.run)

    command = subparsers.add_parser(
        "assess", help="Generate canonical v2 multi-axis assessments for a case"
    )
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument("--output-dir", type=Path)
    command.set_defaults(handler=v2_commands.run_assess)

    command = subparsers.add_parser(
        "hypotheses", help="Generate the H1-H5 ACH matrix and verification priorities"
    )
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument("--output", type=Path)
    command.set_defaults(handler=v2_commands.run_hypotheses)

    command = subparsers.add_parser(
        "capture", help="Append explicit browser/access receipts without treating them as evidence"
    )
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument("--receipt", type=Path, action="append", required=True)
    command.set_defaults(handler=v2_commands.run_capture)

    certification_parser = subparsers.add_parser(
        "certification", help="WaterMark/UL exact-product and authorized-site hard gates"
    )
    certification_sub = certification_parser.add_subparsers(
        dest="certification_command", required=True
    )
    command = certification_sub.add_parser("check")
    command.add_argument("--scheme", choices=("watermark", "ul", "generic"), required=True)
    command.add_argument("--record", type=Path, required=True)
    command.add_argument("--target", type=Path, required=True)
    command.add_argument("--at")
    command.add_argument("--output", type=Path)
    command.set_defaults(handler=v2_commands.run_certification_check)

    social_parser = subparsers.add_parser(
        "social", help="Evaluate account-to-entity/site/process/SKU binding chains"
    )
    social_sub = social_parser.add_subparsers(dest="social_command", required=True)
    command = social_sub.add_parser("assess")
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument("--output", type=Path)
    command.set_defaults(handler=v2_commands.run_social_assess)

    events_parser = subparsers.add_parser(
        "events", help="Validate EPCIS-style production and shipment event chains"
    )
    events_sub = events_parser.add_subparsers(dest="events_command", required=True)
    command = events_sub.add_parser("validate")
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument("--required-certified-biz-step", action="append", default=[])
    command.add_argument("--terminal-object", action="append", default=[])
    command.add_argument("--output", type=Path)
    command.set_defaults(handler=v2_commands.run_events_validate)

    pack_parser = subparsers.add_parser(
        "process-pack", help="List, compose, inspect, or evaluate data-driven process packs"
    )
    pack_sub = pack_parser.add_subparsers(dest="pack_command", required=True)
    command = pack_sub.add_parser("list")
    command.add_argument("--pack-dir", type=Path)
    command.set_defaults(handler=v2_commands.run_process_pack_list)
    command = pack_sub.add_parser("show")
    command.add_argument("name", nargs="+")
    command.add_argument("--pack-dir", type=Path)
    command.set_defaults(handler=v2_commands.run_process_pack_show)
    command = pack_sub.add_parser("evaluate")
    command.add_argument("name", nargs="+")
    command.add_argument("--facts", type=Path, required=True)
    command.add_argument("--pack-dir", type=Path)
    command.add_argument("--output", type=Path)
    command.set_defaults(handler=v2_commands.run_process_pack_evaluate)

    command = subparsers.add_parser(
        "report", help="Generate semantically linted MD/JSON/CSV/XLSX/DOCX reports"
    )
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument(
        "--format",
        dest="formats",
        action="append",
        default=[],
        help="Repeat or use comma-separated md,json,csv,xlsx,docx",
    )
    command.add_argument("--output-dir", type=Path)
    command.set_defaults(handler=reporting.run)

    command = subparsers.add_parser(
        "lint-report", help="Reject probability semantics and unsupported public claims"
    )
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument("--path", type=Path, action="append", default=[])
    command.set_defaults(handler=v2_commands.run_lint_case)

    command = subparsers.add_parser(
        "audit", help="Recompute scores and verify evidence before conclusions"
    )
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument(
        "--stage", choices=("research", "operational", "confirmed"), default="research"
    )
    command.add_argument("--json-output", type=Path)
    command.set_defaults(handler=audit.run)

    command = subparsers.add_parser(
        "doctor", help="Check dependencies/resources and save an environment snapshot"
    )
    command.add_argument("--case-root", type=Path)
    command.add_argument("--output", type=Path)
    command.add_argument(
        "--profile",
        choices=("auto", "minimum", "balanced", "workstation"),
        default="auto",
    )
    command.add_argument(
        "--model-mode",
        choices=("undeclared", "none", "cloud", "local", "hybrid"),
        default="undeclared",
        help="Explicit declaration for this snapshot; not inferred from installed tools.",
    )
    command.add_argument("--model-id", action="append", default=[])
    command.add_argument(
        "--external-visual-service",
        action="append",
        default=[],
        help="Record Lens/Bing/Yandex/TinEye separately from analysis-model mode.",
    )
    command.add_argument(
        "--strict",
        action="store_true",
        help="Return code 2 when the requested resource profile is not met.",
    )
    command.set_defaults(handler=environment.run)

    command = subparsers.add_parser(
        "materials", help="Check staged photo/document readiness"
    )
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument("--plan", type=Path)
    command.add_argument(
        "--stage",
        choices=("discovery", "comparison", "process", "confirmed"),
        default="discovery",
    )
    command.add_argument("--output", type=Path)
    command.set_defaults(handler=materials.run)

    command = subparsers.add_parser(
        "ledger", help="Regenerate the evidence CSV view from canonical candidate JSON"
    )
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument("--output", type=Path)
    command.set_defaults(handler=ledger.run)

    command = subparsers.add_parser(
        "log-model", help="Append a non-evidentiary model-use provenance record"
    )
    command.add_argument("--case-root", type=Path, required=True)
    command.add_argument(
        "--mode", choices=("cloud", "local", "hybrid"), required=True
    )
    command.add_argument("--provider-or-runtime", required=True)
    command.add_argument("--model-id", required=True)
    command.add_argument("--model-revision", default="unknown")
    command.add_argument("--quantization", default="")
    command.add_argument("--endpoint-class", default="chat")
    command.add_argument("--prompt-id", required=True)
    command.add_argument("--input-artifact-id", action="append", default=[])
    command.add_argument("--output-path", type=Path)
    command.add_argument("--human-verified", action="store_true")
    command.add_argument("--notes", default="")
    command.add_argument("--run-id")
    command.set_defaults(handler=provenance.run)
    return parser


def _sanitized_argv(argv: list[str]) -> list[str]:
    output = []
    for value in argv:
        parsed = urllib.parse.urlparse(value)
        if parsed.scheme in {"http", "https"} and parsed.netloc and parsed.query:
            value = urllib.parse.urlunparse(
                (parsed.scheme, parsed.netloc, parsed.path, "", "[REDACTED_QUERY]", "")
            )
        output.append(value)
    return output


def _execution_case_root(args: argparse.Namespace) -> Path | None:
    if getattr(args, "command", "") == "migrate":
        output_root = getattr(args, "output_root", None)
        if output_root is not None:
            return Path(output_root)
        source = Path(args.case_root)
        return source.with_name(f"{source.name}-schema-v2")
    case_root = getattr(args, "case_root", None)
    if case_root is not None:
        return Path(case_root)
    if getattr(args, "command", "") == "init":
        return Path(args.root) / safe_slug(args.name)
    return None


def _append_execution_log(
    args: argparse.Namespace,
    argv: list[str],
    *,
    exit_code: int,
    status: str,
    notes: str = "",
) -> None:
    case_root = _execution_case_root(args)
    if case_root is None or not case_root.is_dir():
        return
    log_path = case_root / "logs" / "execution_log.csv"
    lock_path = case_root / "logs" / ".execution_log.lock"
    sanitized = _sanitized_argv(argv)
    command_text = json.dumps(["factorytrace", *sanitized], ensure_ascii=False)
    command_hash = hashlib.sha256(command_text.encode("utf-8")).hexdigest()
    output_paths = []
    for key in ("output", "output_dir", "json_output"):
        value = getattr(args, key, None)
        if value:
            output_paths.append(str(value))
    row = {
        "timestamp_utc": utc_now(),
        "command_id": f"CMD-{uuid.uuid4().hex[:12]}",
        "actor": "factorytrace-cli",
        "tool": "factorytrace",
        "tool_version": __version__,
        "command_or_action": command_text,
        "working_directory": str(Path.cwd()),
        "input_artifact_ids": "",
        "output_paths": json.dumps(output_paths, ensure_ascii=False),
        "exit_code": str(exit_code),
        "status": status,
        "notes": f"command_sha256={command_hash}" + (f"; {notes}" if notes else ""),
    }
    with FileLock(lock_path):
        write_header = not log_path.is_file() or log_path.stat().st_size == 0
        log_path.parent.mkdir(parents=True, exist_ok=True)
        encoding = "utf-8-sig" if write_header else "utf-8"
        with log_path.open("a", encoding=encoding, newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=EXECUTION_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
        commands_path = case_root / "commands.log"
        with commands_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(
                f"{row['timestamp_utc']} exit={exit_code} {command_text} "
                f"sha256={command_hash}\n"
            )


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    actual_argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(actual_argv)
    handler: Callable[[object], int] = args.handler
    try:
        result = handler(args)
    except Exception as error:
        _append_execution_log(
            args,
            actual_argv,
            exit_code=1,
            status="failed",
            notes=f"{type(error).__name__}: {error}",
        )
        raise
    _append_execution_log(
        args,
        actual_argv,
        exit_code=result,
        status="success" if result == 0 else "failed",
    )
    return result
