#!/usr/bin/env python3
"""English: Discover a working toolkit command and delegate arguments without a shell.

中文：按显式根目录、当前解释器与 PATH 寻找可运行入口，再无 shell 转发参数；发现失败须修复环境，不静默调用别的工具。
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Sequence


def _candidate_commands(toolkit_root: Path | None) -> list[list[str]]:
    commands: list[list[str]] = []
    if toolkit_root is not None:
        root = toolkit_root.resolve()
        if os.name == "nt":
            commands.append([str(root / ".venv" / "Scripts" / "factorytrace.exe")])
            commands.append([str(root / ".venv" / "Scripts" / "python.exe"), "-m", "factorytrace"])
        else:
            commands.append([str(root / ".venv" / "bin" / "factorytrace")])
            commands.append([str(root / ".venv" / "bin" / "python"), "-m", "factorytrace"])
        commands.append([sys.executable, "-m", "factorytrace"])
    on_path = shutil.which("factorytrace")
    if on_path:
        commands.append([on_path])
    commands.append([sys.executable, "-m", "factorytrace"])
    return commands


def discover_command(toolkit_root: Path | None) -> list[str]:
    for command in _candidate_commands(toolkit_root):
        executable = Path(command[0])
        if executable.is_absolute() and not executable.exists():
            continue
        try:
            probe = subprocess.run(
                [*command, "--help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=20,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if probe.returncode == 0:
            return command
    raise FileNotFoundError(
        "factorytrace CLI not found. Set --toolkit-root or FACTORY_TRACE_TOOLKIT."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Locate and invoke factorytrace without shell interpolation."
    )
    parser.add_argument(
        "--toolkit-root",
        type=Path,
        default=Path(os.environ["FACTORY_TRACE_TOOLKIT"])
        if os.environ.get("FACTORY_TRACE_TOOLKIT")
        else None,
        help="Path to factory_trace_toolkit (or set FACTORY_TRACE_TOOLKIT).",
    )
    parser.add_argument(
        "--print-command",
        action="store_true",
        help="Print the resolved command as JSON before execution.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Resolve the core CLI and exit without running delegated arguments.",
    )
    parser.add_argument(
        "factorytrace_args",
        nargs=argparse.REMAINDER,
        help="Arguments for factorytrace; place them after --.",
    )
    return parser


def _strip_separator(values: Sequence[str]) -> list[str]:
    values = list(values)
    return values[1:] if values[:1] == ["--"] else values


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = discover_command(args.toolkit_root)
    delegated = _strip_separator(args.factorytrace_args)
    if args.print_command or args.check_only:
        print(json.dumps({"command": command, "delegated": delegated}, ensure_ascii=False))
    if args.check_only:
        return 0
    if not delegated:
        delegated = ["--help"]
    completed = subprocess.run([*command, *delegated], check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
