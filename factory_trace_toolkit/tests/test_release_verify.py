"""Test portable-source leak detection, including code comments.

测试可迁移源码的泄漏检测，包括代码注释中的泄漏。
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


TOOLKIT_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "factorytrace_release_verifier",
    TOOLKIT_ROOT / "scripts" / "verify_toolkit.py",
)
assert SPEC is not None and SPEC.loader is not None
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


class ReleaseVerifierTests(unittest.TestCase):
    def test_generic_install_default_is_not_a_host_identity(self) -> None:
        # A documented system installation fallback is not a private workspace.
        # 通用系统安装回退目录不是私有工作区。
        location = "C:" + chr(92) + "Program Files"
        source = "LOCATION = " + repr(location) + "\n"
        self.assertNotIn(
            "workspace-specific absolute path",
            VERIFIER._portable_findings(Path("fixture.py"), source),
        )

    def test_arbitrary_drive_workspace_is_detected(self) -> None:
        location = "X:" + chr(92) + "synthetic-workspace" + chr(92) + "secret.txt"
        self.assertIn(
            "workspace-specific absolute path",
            VERIFIER._portable_findings(Path("fixture.md"), location),
        )

    def test_real_portability_leaks_are_detected(self) -> None:
        # Build synthetic paths at runtime; never embed a real host identity.
        # 在运行时构造虚拟路径，不嵌入真实宿主身份。
        backslash = chr(92)
        samples = {
            "absolute Windows user path": (
                "C:" + backslash + "Users" + backslash + "Alice" + backslash + "secret.txt"
            ),
            "absolute macOS user path": "/" + "Users" + "/alice/secret.txt",
            "absolute Linux home path": "/" + "home" + "/alice/secret.txt",
            "UNC share path": backslash * 2 + "server" + backslash + "share" + backslash + "file.txt",
        }
        for expected_label, sample in samples.items():
            with self.subTest(expected_label=expected_label):
                self.assertIn(
                    expected_label,
                    VERIFIER._portable_findings(Path("fixture.md"), sample),
                )
                python_source = "VALUE = " + repr(sample) + "\n"
                self.assertIn(
                    expected_label,
                    VERIFIER._portable_findings(Path("fixture.py"), python_source),
                )
                comment_source = "# " + sample + "\n"
                self.assertIn(
                    expected_label,
                    VERIFIER._portable_findings(Path("fixture.py"), comment_source),
                )

    def test_literal_python_credential_assignment_is_detected(self) -> None:
        name = "API_" + "KEY"
        secret = "not-a-placeholder-credential"
        python_source = name + " = " + repr(secret) + "\n"
        self.assertIn(
            "credential assignment",
            VERIFIER._portable_findings(Path("fixture.py"), python_source),
        )

    def test_regex_source_is_not_misclassified_as_a_leak(self) -> None:
        for label, pattern in VERIFIER.SECRET_PATTERNS.items():
            with self.subTest(label=label):
                python_source = (
                    "import re\nVALUE = re.compile(" + repr(pattern.pattern) + ")\n"
                )
                self.assertEqual(
                    [],
                    VERIFIER._portable_findings(Path("fixture.py"), python_source),
                )


if __name__ == "__main__":
    unittest.main()
