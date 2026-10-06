"""Regression checks for public-source boundaries / 公开源码边界的回归测试。"""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("public_gate", SOURCE_ROOT / "scripts/verify_public_release.py")
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


class PublicReleaseTests(unittest.TestCase):
    def test_case_directory_is_rejected_even_if_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "cases").mkdir()
            with self.assertRaisesRegex(ValueError, "Forbidden data directory"):
                list(GATE.files_in(root))

    def test_unknown_database_is_not_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "data.sqlite").write_bytes(b"synthetic test")
            with self.assertRaisesRegex(ValueError, "Unreviewed file type"):
                list(GATE.files_in(root))

    def test_uppercase_private_artifact_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "receipt.XLSX").write_bytes(b"synthetic test")
            with self.assertRaisesRegex(ValueError, "Forbidden generated/private file"):
                list(GATE.files_in(root))

    def test_generated_cache_is_ignored_not_published(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "__pycache__").mkdir()
            (root / "__pycache__/module.pyc").write_bytes(b"synthetic test")
            (root / "README.md").write_text("Synthetic example", encoding="utf-8")
            self.assertEqual([p.name for p in GATE.files_in(root)], ["README.md"])

    def test_reviewed_binary_must_stay_in_resource_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "image.png").write_bytes(b"synthetic test")
            with self.assertRaisesRegex(ValueError, "Unreviewed binary location"):
                list(GATE.files_in(root))


if __name__ == "__main__":
    unittest.main()
