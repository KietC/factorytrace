"""English: Exercise CLI migrations, YAML loading, and public-payload compatibility.

中文：检验 CLI 迁移、YAML 安全加载与公开输出兼容；迁移失败不发布半成品，执行日志不得污染源案件。
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from factorytrace.audit import audit_case
from factorytrace.cli import main as cli_main
from factorytrace.init_case import create_case
from factorytrace.process_packs import load_process_pack


def inventory(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


class V2IntegrationTests(unittest.TestCase):
    def _make_directory_link(self, link: Path, target: Path) -> None:
        if os.name == "nt":
            result = subprocess.run(
                ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                self.skipTest(f"could not create Windows junction: {result.stderr}")
        else:
            os.symlink(target, link, target_is_directory=True)

    def test_complete_cli_migration_never_logs_to_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "legacy"
            (source / "candidates").mkdir(parents=True)
            (source / "case.json").write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "case_id": "legacy",
                        "objective": "trace source",
                        "created_at_utc": "2026-08-01T00:00:00Z",
                        "time_zone": "UTC",
                        "status": "research_complete_source_unresolved",
                    }
                ),
                encoding="utf-8",
            )
            (source / "candidates" / "CAND-001.json").write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "candidate_id": "CAND-001",
                        "display_name": "Legacy candidate",
                        "target_processes": ["forming"],
                        "entities": {},
                        "evidence": [],
                        "red_flags": [],
                    }
                ),
                encoding="utf-8",
            )
            before = inventory(source)
            destination = root / "migrated"
            with redirect_stdout(io.StringIO()):
                exit_code = cli_main(
                    [
                        "migrate",
                        "--case-root",
                        str(source),
                        "--to",
                        "2",
                        "--output-root",
                        str(destination),
                    ]
                )
            self.assertEqual(exit_code, 0)
            self.assertEqual(inventory(source), before)
            migrated_case = json.loads(
                (destination / "case.json").read_text(encoding="utf-8")
            )
            self.assertEqual(migrated_case["status"], "research")
            self.assertEqual(
                migrated_case["legacy_status"], "research_complete_source_unresolved"
            )
            execution_log = (destination / "logs" / "execution_log.csv").read_text(
                encoding="utf-8-sig"
            )
            self.assertIn("migrate", execution_log)

    def test_canonical_migration_does_not_follow_external_junction(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "legacy"
            (source / "candidates").mkdir(parents=True)
            (source / "work" / "xlsx_build").mkdir(parents=True)
            (source / "output").mkdir()
            (source / "case.json").write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "case_id": "legacy-junction",
                        "objective": "trace source",
                        "created_at_utc": "2026-08-01T00:00:00Z",
                        "time_zone": "UTC",
                        "status": "research",
                    }
                ),
                encoding="utf-8",
            )
            (source / "output" / "legacy-release.zip").write_bytes(b"legacy")
            external = root / "external-runtime"
            external.mkdir()
            sentinel = external / "DO_NOT_COPY.txt"
            sentinel.write_text("outside case", encoding="utf-8")
            link = source / "work" / "xlsx_build" / "node_modules"
            self._make_directory_link(link, external)

            destination = root / "migrated"
            before = hashlib.sha256(sentinel.read_bytes()).hexdigest()
            with redirect_stdout(io.StringIO()):
                exit_code = cli_main(
                    [
                        "migrate",
                        "--case-root",
                        str(source),
                        "--to",
                        "2",
                        "--copy-mode",
                        "canonical",
                        "--output-root",
                        str(destination),
                    ]
                )
            self.assertEqual(exit_code, 0)
            self.assertFalse((destination / "work" / "xlsx_build").exists())
            self.assertFalse((destination / "output" / "legacy-release.zip").exists())
            self.assertEqual(hashlib.sha256(sentinel.read_bytes()).hexdigest(), before)
            receipt = json.loads(
                (destination / "output" / "migration_v1_to_v2.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(
                any(
                    row["path"] == "work/xlsx_build/node_modules"
                    for row in receipt["rejected_entries"]
                )
            )
            self.assertTrue(
                any(
                    row["path"] == "output/legacy-release.zip"
                    for row in receipt["skipped_entries"]
                )
            )

    def test_failed_migration_never_publishes_partial_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "invalid"
            source.mkdir()
            (source / "case.json").write_text(
                json.dumps({"schema": 99, "case_id": "invalid"}), encoding="utf-8"
            )
            destination = root / "destination"
            with self.assertRaises(ValueError):
                cli_main(
                    [
                        "migrate",
                        "--case-root",
                        str(source),
                        "--to",
                        "2",
                        "--output-root",
                        str(destination),
                    ]
                )
            self.assertFalse(destination.exists())
            self.assertTrue((root / "destination.migration-failed.json").is_file())

    def test_yaml_process_pack_is_safe_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "probe.yaml").write_text(
                """schema: factorytrace.process-pack.v2
pack_id: probe
version: 1
description: probe
required_processes: [forming]
required_evidence: []
required_photos: []
required_documents: []
certification: {mode: all, schemes: [], hard_gates: []}
events: {required_biz_steps: [], certified_biz_steps: []}
social: {maximum_authority: entity_identity}
""",
                encoding="utf-8",
            )
            pack = load_process_pack("probe", pack_dir=root)
            self.assertEqual(pack["required_processes"], ["forming"])

    def test_audit_public_payload_removes_deprecated_confidence_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            case = create_case("audit-v2", Path(temporary).resolve())
            report = audit_case(case, "research")
            rendered = json.dumps(report, ensure_ascii=False)
            self.assertNotIn('"confidence_index"', rendered)


if __name__ == "__main__":
    unittest.main()
