"""Validate release inventory parsing / 验证发布清单的路径解析。"""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("public_package", ROOT / "scripts/package_public_release.py")
assert SPEC is not None and SPEC.loader is not None
PACKAGER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKAGER)


class PublicPackageTests(unittest.TestCase):
    def parse(self, lines: str) -> dict[str, str]:
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "manifest.sha256"
            manifest.write_text(lines, encoding="utf-8")
            return PACKAGER.read_manifest(manifest)

    def test_valid_relative_path(self) -> None:
        self.assertEqual(self.parse("a" * 64 + "  docs/guide.md\n"), {"docs/guide.md": "A" * 64})

    def test_duplicates_are_rejected(self) -> None:
        row = "a" * 64 + "  README.md\n"
        with self.assertRaises(ValueError):
            self.parse(row + row)

    def test_escape_and_drive_paths_are_rejected(self) -> None:
        for name in ("../data", "/data", "docs/../data", "drive:/data", "docs\\data"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.parse("a" * 64 + "  " + name + "\n")

    def test_invalid_digest_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.parse("not-a-digest  README.md\n")


if __name__ == "__main__":
    unittest.main()
