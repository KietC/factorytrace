#!/usr/bin/env python3
"""English: Build and install an isolated wheel, then verify packaged resource use.

中文：构建并隔离安装 wheel 后检验打包资源与实际命令；可编辑安装通过不能代替 wheel 验收，测试环境和输出不属于发布源码。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def invoke(
    command: list[str], *, cwd: Path, environment: dict[str, str], timeout: int = 240
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            timeout=timeout,
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"command failed ({error.returncode}): {command!r}\n"
            f"stdout:\n{error.stdout}\nstderr:\n{error.stderr}"
        ) from error


def read_lock(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, version = line.partition("==")
        if not separator or not name or not version:
            raise ValueError(f"non-exact tested lock line: {raw_line}")
        result[name] = version
    return result


def assert_release_tree_has_no_links(root: Path) -> None:
    excluded = {
        ".venv",
        ".build-venv",
        ".git",
        "output",
        "smoke_cases",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "build",
        "dist",
        "wheelhouse",
    }
    for current, directories, filenames in os.walk(root):
        current_path = Path(current)
        directories[:] = [
            name
            for name in directories
            if name not in excluded and not name.endswith(".egg-info")
        ]
        for name in directories:
            path = current_path / name
            if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
                raise RuntimeError(f"linked directory is forbidden in wheel source: {path}")
        for name in filenames:
            path = current_path / name
            if path.is_symlink():
                raise RuntimeError(f"linked file is forbidden in wheel source: {path}")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--wheel-output-dir",
        type=Path,
        help="Optionally retain the verified wheel in this release-artifact directory.",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    lock = read_lock(root / "constraints-tested.txt")
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    commands: list[dict[str, Any]] = []
    scratch_parent = root / "output"
    scratch_parent.mkdir(parents=True, exist_ok=True)
    assert_release_tree_has_no_links(root)

    with tempfile.TemporaryDirectory(
        prefix="wheel-smoke-", dir=scratch_parent
    ) as temporary:
        temporary_root = Path(temporary).resolve()
        source_stage = temporary_root / "source"
        shutil.copytree(
            root,
            source_stage,
            symlinks=True,
            ignore=shutil.ignore_patterns(
                ".venv",
                ".build-venv",
                ".git",
                "output",
                "smoke_cases",
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
                "*.egg-info",
                "build",
                "dist",
                "wheelhouse",
                "*.whl",
                "*.tar.gz",
            ),
        )
        wheelhouse = temporary_root / "wheelhouse"
        wheelhouse.mkdir()
        download = invoke(
            [
                sys.executable,
                "-m",
                "pip",
                "download",
                "--only-binary=:all:",
                "--dest",
                str(wheelhouse),
                "--requirement",
                str(source_stage / "constraints-tested.txt"),
            ],
            cwd=temporary_root,
            environment=environment,
        )
        commands.append(
            {
                "step": "download_exact_lock_wheels",
                "status": "PASS",
                "wheelhouse_files": len(list(wheelhouse.iterdir())),
            }
        )
        build = invoke(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "--no-build-isolation",
                "--wheel-dir",
                str(wheelhouse),
                str(source_stage),
            ],
            cwd=temporary_root,
            environment=environment,
        )
        commands.append({"step": "build_staged_wheel", "status": "PASS"})
        wheels = sorted(wheelhouse.glob("factory_trace_toolkit-*.whl"))
        if len(wheels) != 1:
            raise RuntimeError(f"expected one toolkit wheel, found {len(wheels)}")
        wheel = wheels[0]

        venv_root = temporary_root / "venv"
        venv.EnvBuilder(with_pip=True, system_site_packages=False).create(venv_root)
        python = (
            venv_root / "Scripts" / "python.exe"
            if os.name == "nt"
            else venv_root / "bin" / "python"
        )
        lock_install = invoke(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--find-links",
                str(wheelhouse),
                "--requirement",
                str(source_stage / "constraints-tested.txt"),
            ],
            cwd=temporary_root,
            environment=environment,
        )
        commands.append({"step": "install_exact_lock_offline", "status": "PASS"})
        install = invoke(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--find-links",
                str(wheelhouse),
                "factory-trace-toolkit[full]==2.0.0",
            ],
            cwd=temporary_root,
            environment=environment,
        )
        commands.append({"step": "install_wheel_offline", "status": "PASS"})
        invoke(
            [str(python), "-m", "pip", "check"],
            cwd=temporary_root,
            environment=environment,
        )

        lock_probe = (
            "import json; from importlib import metadata; "
            f"expected={lock!r}; "
            "observed={k: metadata.version(k) for k in expected}; "
            "assert observed == expected, (observed, expected); "
            "print(json.dumps(observed, sort_keys=True))"
        )
        observed_lock = json.loads(
            invoke(
                [str(python), "-c", lock_probe],
                cwd=temporary_root,
                environment=environment,
            ).stdout
        )

        inspect = invoke(
            [
                str(python),
                "-c",
                (
                    "import json, pathlib, factorytrace; "
                    "print(json.dumps({'version': factorytrace.__version__, "
                    "'module': str(pathlib.Path(factorytrace.__file__).resolve())}))"
                ),
            ],
            cwd=temporary_root,
            environment=environment,
        )
        installed = json.loads(inspect.stdout)
        module_path = Path(installed["module"])
        for forbidden_root in (root / "src", source_stage):
            try:
                module_path.relative_to(forbidden_root)
            except ValueError:
                continue
            raise RuntimeError(f"wheel smoke imported a source tree: {module_path}")

        resource_probe = r'''
import hashlib
import json
import sysconfig
from pathlib import Path

root = Path(sysconfig.get_path("data")) / "share" / "factory-trace-toolkit"
required = {
    "schemas": ["case.v2.schema.json", "candidate.v2.schema.json", "evidence.v2.schema.json", "assessment.v2.schema.json"],
    "templates": ["product_profile.example.json", "contacts.csv", "manufacturer_inquiry_zh.md"],
    "process_packs": ["certified_product.json", "metal_forming.json", "sanitary_valve.json"],
    "tessdata": ["MANIFEST.json", "LICENSE", "eng.traineddata", "osd.traineddata", "chi_sim.traineddata", "chi_tra.traineddata"],
    "ocr_probes": ["MANIFEST.json", "chi_sim_probe.png", "chi_tra_probe.png"],
    "fonts": ["MANIFEST.json", "LICENSE", "NotoSansCJKsc-Regular.otf"],
}
for folder, names in required.items():
    for name in names:
        path = root / folder / name
        assert path.is_file() and path.stat().st_size > 0, path
for folder in ("tessdata", "ocr_probes", "fonts"):
    manifest = json.loads((root / folder / "MANIFEST.json").read_text(encoding="utf-8"))
    for name, record in manifest["files"].items():
        expected = record["sha256"] if isinstance(record, dict) else record
        actual = hashlib.sha256((root / folder / name).read_bytes()).hexdigest()
        assert actual.casefold() == expected.casefold(), (folder, name)
print(json.dumps({"resource_root": str(root), "required": required}, ensure_ascii=False))
'''
        installed_resources = json.loads(
            invoke(
                [str(python), "-c", resource_probe],
                cwd=temporary_root,
                environment=environment,
            ).stdout
        )

        cases_root = temporary_root / "cases"
        init_result = invoke(
            [
                str(python),
                "-m",
                "factorytrace",
                "init",
                "wheel-case",
                "--root",
                str(cases_root),
            ],
            cwd=temporary_root,
            environment=environment,
        )
        case_root = cases_root / "wheel-case"
        validate_result = invoke(
            [
                str(python),
                "-m",
                "factorytrace",
                "validate",
                "--case-root",
                str(case_root),
            ],
            cwd=temporary_root,
            environment=environment,
        )
        pack_result = invoke(
            [str(python), "-m", "factorytrace", "process-pack", "list"],
            cwd=temporary_root,
            environment=environment,
        )
        validation = json.loads(validate_result.stdout)
        packs = json.loads(pack_result.stdout)
        if validation.get("status") != "PASS":
            raise RuntimeError("wheel-installed schema validation did not pass")
        if packs.get("status") != "PASS" or not isinstance(packs.get("packs"), list):
            raise RuntimeError(f"invalid installed process-pack index: {packs}")
        pack_ids = {
            item.get("pack_id")
            for item in packs["packs"]
            if isinstance(item, dict)
        }
        expected_packs = {"certified_product", "metal_forming", "sanitary_valve"}
        if not expected_packs.issubset(pack_ids):
            raise RuntimeError(f"wheel-installed process packs missing: {expected_packs - pack_ids}")
        resource_root = Path(installed_resources["resource_root"]).resolve()
        for item in packs["packs"]:
            Path(item["path"]).resolve().relative_to(resource_root)
        commands.extend(
            [
                {"step": "verify_exact_lock", "packages": len(observed_lock)},
                {"step": "verify_six_resource_classes", "result": installed_resources},
                {"step": "init_from_installed_templates", "status": "PASS"},
                {"step": "validate_from_installed_schemas", "status": validation.get("status")},
                {"step": "list_installed_process_packs", "pack_ids": sorted(pack_ids)},
            ]
        )
        report = {
            "schema": 2,
            "status": "PASS",
            "python": sys.version,
            "wheel_name": wheel.name,
            "wheel_sha256": sha256_file(wheel),
            "installed_version": installed["version"],
            "installed_module": installed["module"],
            "source_tree_imported": False,
            "exact_lock_packages": observed_lock,
            "pip_check": "PASS",
            "validation_status": validation["status"],
            "process_packs": sorted(pack_ids),
            "installed_resources": installed_resources,
            "commands": commands,
            "temporary_environment_removed_on_exit": True,
        }
        if args.wheel_output_dir is not None:
            wheel_output_dir = args.wheel_output_dir.resolve()
            wheel_output_dir.mkdir(parents=True, exist_ok=True)
            retained_wheel = wheel_output_dir / wheel.name
            shutil.copy2(wheel, retained_wheel)
            report["retained_wheel"] = {
                "path": str(retained_wheel),
                "sha256": sha256_file(retained_wheel),
            }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
