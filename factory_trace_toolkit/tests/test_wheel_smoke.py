"""Test isolated build dependencies without using the caller's installed backend.

测试隔离构建依赖，避免借用调用环境已安装的后端。
"""
from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "factorytrace_wheel_smoke",
    Path(__file__).resolve().parents[1] / "scripts" / "wheel_smoke.py",
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class IsolatedBuildTests(unittest.TestCase):
    def test_environment_removes_install_redirectors_without_changing_parent(self) -> None:
        source = {
            "PIP_TARGET": "outside-fixture", "PIP_ROOT": "outside-fixture",
            "PIP_REQUIREMENT": "fixture.txt", "PIP_CONFIG_FILE": "fixture.ini",
            "PYTHONPATH": "outside-fixture", "PYTHONHOME": "outside-fixture",
            "VIRTUAL_ENV": "outside-fixture",
            "HTTPS_PROXY": "http://proxy.example.invalid",
            "SSL_CERT_FILE": "fixture-cert.pem",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            with patch.dict(MODULE.os.environ, source, clear=True):
                before = dict(MODULE.os.environ)
                environment = MODULE.isolated_environment(root)
                self.assertEqual(dict(MODULE.os.environ), before)
            for name in ("PIP_TARGET", "PIP_ROOT", "PIP_REQUIREMENT", "PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
                self.assertNotIn(name, environment)
            self.assertEqual(environment["PIP_CONFIG_FILE"], os.devnull)
            self.assertEqual(environment["PIP_CACHE_DIR"], str(root / "pip-cache"))
            self.assertEqual(environment["PYTHONNOUSERSITE"], "1")
            self.assertEqual(environment["HTTPS_PROXY"], source["HTTPS_PROXY"])
            self.assertEqual(environment["SSL_CERT_FILE"], source["SSL_CERT_FILE"])

    def test_backend_is_installed_offline_only_into_disposable_venv(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            wheelhouse = root / "wheelhouse"
            environment = {"PYTHONUTF8": "1"}
            with patch.object(MODULE.venv, "EnvBuilder") as builder, patch.object(MODULE, "invoke") as invoke:
                python = MODULE.prepare_build_python(
                    root, wheelhouse, {"pip": "26.1.2", "setuptools": "83.0.0"}, environment,
                )
            expected = root / "build-venv" / (
                "Scripts/python.exe" if os.name == "nt" else "bin/python"
            )
            self.assertEqual(python, expected)
            builder.assert_called_once_with(with_pip=True, system_site_packages=False)
            builder.return_value.create.assert_called_once_with(root / "build-venv")
            command = invoke.call_args.args[0]
            self.assertEqual(command[0], str(expected))
            self.assertIn("--no-index", command)
            self.assertEqual(command[command.index("--find-links") + 1], str(wheelhouse))
            self.assertIn("pip==26.1.2", command)
            self.assertIn("setuptools==83.0.0", command)
            self.assertEqual(invoke.call_args.kwargs, {"cwd": root, "environment": environment})

    def test_missing_backend_lock_fails_before_creating_an_environment(self) -> None:
        with patch.object(MODULE.venv, "EnvBuilder") as builder, patch.object(MODULE, "invoke") as invoke:
            with self.assertRaises(ValueError):
                MODULE.prepare_build_python(Path("fixture"), Path("wheels"), {"pip": "26.1.2"}, {})
        builder.assert_not_called()
        invoke.assert_not_called()


if __name__ == "__main__":
    unittest.main()
