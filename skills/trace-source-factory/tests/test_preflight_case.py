"""English: Regress canonical command-log handling and no-follow path checks.

中文：以临时合成案件回归标准命令日志与禁止跟随链接的检查；测试不需要真实案件或平台登录。
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "preflight_case.py"
SPEC = importlib.util.spec_from_file_location("trace_source_preflight", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PreflightCaseTests(unittest.TestCase):
    def make_operational_case(self, root: Path, *, command_log: str | None) -> Path:
        case = root / "case"
        for relative in (
            "artifacts/original",
            "work",
            "evidence",
            "candidates",
            "logs",
            "output",
        ):
            (case / relative).mkdir(parents=True, exist_ok=True)
        (case / "case.json").write_text(
            json.dumps({"case_id": "preflight-test"}), encoding="utf-8"
        )
        (case / "artifacts" / "original" / "source.bin").write_bytes(b"source")
        (case / "work" / "product_profile.json").write_text("{}", encoding="utf-8")
        (case / "evidence" / "evidence_register.csv").write_text(
            "evidence_id\n", encoding="utf-8-sig"
        )
        (case / "claims.jsonl").write_text("", encoding="utf-8")
        (case / "logs" / "execution_log.csv").write_text(
            "timestamp,command\n", encoding="utf-8-sig"
        )
        if command_log:
            path = case / command_log
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("test\n", encoding="utf-8")
        return case

    def test_root_commands_log_is_canonical_and_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            case = self.make_operational_case(Path(temporary), command_log="commands.log")
            result = MODULE.inspect_case(case, "operational")
            self.assertEqual(result["status"], "PASS")
            self.assertFalse(any("legacy command log" in item for item in result["warnings"]))

    def test_missing_both_command_log_locations_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            case = self.make_operational_case(Path(temporary), command_log=None)
            result = MODULE.inspect_case(case, "operational")
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("expected one of" in item for item in result["errors"]))

    def test_reparse_point_is_reported_without_following_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = self.make_operational_case(root, command_log="commands.log")
            external = root / "external"
            external.mkdir()
            (external / "sentinel.txt").write_text("outside", encoding="utf-8")
            link = case / "work" / "external-link"
            if os.name == "nt":
                result = subprocess.run(
                    ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(external)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    self.skipTest(f"could not create Windows junction: {result.stderr}")
            else:
                os.symlink(external, link, target_is_directory=True)
            result = MODULE.inspect_case(case, "operational")
            self.assertIn("work/external-link", result["metrics"]["reparse_points"])
            self.assertTrue(any("canonical migration" in item for item in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
