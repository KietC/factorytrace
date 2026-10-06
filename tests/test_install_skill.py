"""Exercise non-destructive Skill installation with synthetic temporary data.

使用临时合成数据验证 Skill 安装不会覆盖已有文件。
"""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("skill_installer", Path(__file__).resolve().parents[1] / "scripts/install_skill.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SkillInstallerTests(unittest.TestCase):
    def source(self, root: Path) -> Path:
        source = root / "source"
        source.mkdir()
        (source / "SKILL.md").write_text("---\nname: trace-source-factory\ndescription: Synthetic test.\n---\n", encoding="utf-8")
        return source

    def test_install_and_idempotent_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            source = self.source(root)
            target = root / "技能 有空格"
            self.assertEqual(MODULE.install(source, target)["status"], "INSTALLED")
            self.assertEqual(MODULE.install(source, target)["status"], "ALREADY_INSTALLED")

    def test_existing_different_version_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            source = self.source(root)
            target = root / "skills"
            MODULE.install(source, target)
            original = target / "trace-source-factory/SKILL.md"
            original.write_text("preserve me", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                MODULE.install(source, target)
            self.assertEqual(original.read_text(encoding="utf-8"), "preserve me")

    def test_nested_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            source = self.source(Path(temp).resolve())
            with self.assertRaises(ValueError):
                MODULE.install(source, source / "nested")

    def test_missing_entrypoint_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            source = root / "empty"
            source.mkdir()
            with self.assertRaises(ValueError):
                MODULE.install(source, root / "skills")


if __name__ == "__main__":
    unittest.main()
