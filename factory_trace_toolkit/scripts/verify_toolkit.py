#!/usr/bin/env python3
"""Verify source integrity and optional real capabilities before release.

发布前验证源码完整性，并按需执行真实能力探针。
Reports may contain local paths: store them outside public source history.
报告可能含本机路径：必须存放在公开源码历史之外。
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import tokenize
import tomllib
from pathlib import Path


REQUIRED = (
    "VERSION",
    "README.md",
    "CHANGELOG.md",
    "OPERATIONS_MANUAL.md",
    "EVIDENCE_STANDARD.md",
    "PHOTO_MATERIAL_CHECKLIST.md",
    "PROMPTS.md",
    "PROMPT_EXECUTION_PROTOCOL.md",
    "SELF_ITERATION.md",
    "CROSS_PLATFORM.md",
    "ENVIRONMENT_AND_DEPENDENCIES.md",
    "MODEL_USAGE_AND_PROVENANCE.md",
    "CASE_DATA_MODEL.md",
    "SOURCE_ACCESS_POLICY.md",
    "ONLINE_RESEARCH_2026-07-25.md",
    "PORTABLE_MEMORY.md",
    "PORTABLE_PROVENANCE.md",
    "TROUBLESHOOTING.md",
    "pyproject.toml",
    "requirements.txt",
    "constraints-tested.txt",
    ".github/workflows/ci.yml",
    "schemas/README.md",
    "schemas/case.v2.schema.json",
    "schemas/candidate.v2.schema.json",
    "schemas/evidence.v2.schema.json",
    "schemas/assessment.v2.schema.json",
    "templates/product_profile.example.json",
    "templates/crop_plan.example.json",
    "templates/candidate.example.json",
    "templates/model_usage_log.csv",
    "templates/execution_log.csv",
    "templates/research_round.example.json",
    "templates/materials_plan.example.json",
    "templates/parties.example.json",
    "templates/sites.example.json",
    "templates/cert_records.example.json",
    "templates/supply_events.example.json",
    "templates/social_records.example.json",
    "templates/access_receipt.example.json",
    "process_packs/sanitary_valve.json",
    "process_packs/metal_forming.json",
    "process_packs/certified_product.json",
    "scripts/bootstrap.ps1",
    "scripts/bootstrap.sh",
    "scripts/install_media_tools.ps1",
    "scripts/install_media_tools.sh",
    "scripts/capability_smoke.py",
    "scripts/generate_ocr_probes.py",
    "scripts/hash_toolkit.py",
    "scripts/package_toolkit.py",
    "scripts/run_pipeline.ps1",
    "scripts/run_pipeline.sh",
    "scripts/verify_toolkit.py",
    "scripts/wheel_smoke.py",
    "scripts/v2_end_to_end_smoke.py",
    "src/factorytrace/__main__.py",
    "src/factorytrace/cli.py",
    "src/factorytrace/common.py",
    "src/factorytrace/assessment.py",
    "src/factorytrace/_resources.py",
    "src/factorytrace/certification.py",
    "src/factorytrace/events.py",
    "src/factorytrace/migration.py",
    "src/factorytrace/process_packs.py",
    "src/factorytrace/reporting.py",
    "src/factorytrace/schema_validation.py",
    "src/factorytrace/social.py",
    "src/factorytrace/v2_commands.py",
    "resources/tessdata/MANIFEST.json",
    "resources/tessdata/LICENSE",
    "resources/tessdata/eng.traineddata",
    "resources/tessdata/osd.traineddata",
    "resources/tessdata/chi_sim.traineddata",
    "resources/tessdata/chi_tra.traineddata",
    "resources/ocr_probes/MANIFEST.json",
    "resources/ocr_probes/chi_sim_probe.png",
    "resources/ocr_probes/chi_tra_probe.png",
    "memory/CORE_RULES.md",
    "memory/core_rules.json",
    "memory/DEPRECATIONS.md",
)
EXCLUDED_PARTS = {
    ".venv",
    ".build-venv",
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
    "output",
    "smoke_cases",
    "wheelhouse",
}
EXCLUDED_SUFFIXES = {".pyc", ".zip", ".whl", ".gz"}
EXCLUDED_FILES = {
    "CHECKSUMS_SHA256.txt",
    "PACKAGE_CHECKSUMS_SHA256.txt",
    "environment.current.json",
    "verification.json",
}
PORTABLE_LOCAL_FILES = {
    "environment.current.json",
    "verification.json",
    "SOURCES_AND_PROVENANCE.md",
    "ENVIRONMENT_CHANGE_RECEIPT_2026-08-01.md",
}
TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".jsonl",
    ".csv",
    ".py",
    ".ps1",
    ".sh",
    ".toml",
    ".yml",
    ".yaml",
}
SECRET_PATTERNS = {
    "absolute Windows user path": re.compile(
        r"(?i)\b[A-Z]:[\\/]Users[\\/](?!<|user(?:name)?[\\/])[^\\/\s]+"
    ),
    "absolute macOS user path": re.compile(
        r"(?<![:\w])/Users/(?!<|user(?:name)?/)[^/\s]+"
    ),
    "absolute Linux home path": re.compile(
        r"(?<![:\w])/home/(?!<|user(?:name)?/)[^/\s]+"
    ),
    "UNC share path": re.compile(r"(?<!\\)\\\\[^\\\s<>]+\\[^\\\s<>]+"),
    # Detect arbitrary drive-root workspaces without retaining a real host name.
    # 检测通用盘符工作目录，不在检测规则里保留真实宿主工作区名称。
    "workspace-specific absolute path": re.compile(
        r"(?i)\b[A-Z]:[\\/](?!Program Files(?: \(x86\))?(?:[\\/]|[\"']|\n|$)|Windows[\\/]|Users[\\/]|\.\.\.)[^\s\"']+"
    ),
    "PEM private key": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
    ),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub classic token": re.compile(r"\bghp_[A-Za-z0-9]{36,}\b"),
    "GitHub fine-grained token": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}\b"),
    "OpenAI-style secret key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "Bearer token": re.compile(
        r"(?i)Authorization\s*:\s*Bearer\s+"
        r"(?!REDACTED|PLACEHOLDER)[A-Za-z0-9._~-]{16,}"
    ),
    "credential assignment": re.compile(
        r"(?im)\b(?:Cookie|Set-Cookie|API[_-]?KEY|CLIENT[_-]?SECRET)\s*[:=]\s*"
        r"[\"']?(?!REDACTED\b|PLACEHOLDER\b|EXAMPLE\b|NONE\b|NULL\b|\$\{|\$env:)"
        r"[^\s\"'`;]{12,}"
    ),
}
TESSDATA_METADATA = {
    "schema": 1,
    "project": "tesseract-ocr/tessdata_fast",
    "repository": "https://github.com/tesseract-ocr/tessdata_fast",
    "revision": "87416418657359cb625c412a48b6e1d6d41c29bd",
    "license": "Apache-2.0",
}
TESSDATA_FILES = {
    "eng.traineddata",
    "osd.traineddata",
    "chi_sim.traineddata",
    "chi_tra.traineddata",
    "LICENSE",
}
OCR_PROBE_FILES = {"chi_sim_probe.png", "chi_tra_probe.png"}


def _requirement_name(specification: str) -> str:
    return re.split(r"[<>=!~;\s\[]", specification.strip(), maxsplit=1)[0].lower()


def _normalized_requirement_spec(specification: str) -> str:
    return re.sub(r"\s+", "", specification).casefold()


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="backslashreplace")
            except (AttributeError, OSError, ValueError):
                pass


def _python_string_payload(text: str) -> str:
    """Extract string constants and comments, excluding regex definitions.

    提取字符串常量和注释，排除正则定义本身，避免把检测规则当成泄漏。
    """
    tree = ast.parse(text)
    excluded_nodes: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        is_re_compile = (
            isinstance(function, ast.Attribute)
            and function.attr == "compile"
            and isinstance(function.value, ast.Name)
            and function.value.id == "re"
        )
        if is_re_compile:
            for argument in (*node.args, *(item.value for item in node.keywords)):
                excluded_nodes.update(id(child) for child in ast.walk(argument))
    values = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in excluded_nodes
    ]
    values.extend(
        token.string
        for token in tokenize.generate_tokens(io.StringIO(text).readline)
        if token.type == tokenize.COMMENT
    )
    return "\n".join(values)


def _python_has_literal_credential_assignment(text: str) -> bool:
    sensitive_name = re.compile(
        r"(?i)^(?:api_?key|client_?secret|password|passwd|token|cookie|authorization)$"
    )

    def is_secret_literal(node: ast.AST | None) -> bool:
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            return False
        value = node.value.strip()
        if len(value) < 12:
            return False
        return not re.match(
            r"(?i)^(?:redacted|placeholder|example|none|null|changeme|\$\{|\$env:)",
            value,
        )

    def target_names(node: ast.AST) -> list[str]:
        if isinstance(node, ast.Name):
            return [node.id]
        if isinstance(node, (ast.Tuple, ast.List)):
            return [name for item in node.elts for name in target_names(item)]
        return []

    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and is_secret_literal(node.value):
            if any(
                sensitive_name.match(name)
                for target in node.targets
                for name in target_names(target)
            ):
                return True
        if isinstance(node, ast.AnnAssign) and is_secret_literal(node.value):
            if any(sensitive_name.match(name) for name in target_names(node.target)):
                return True
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if (
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and sensitive_name.match(key.value)
                    and is_secret_literal(value)
                ):
                    return True
    return False


def _portable_findings(path: Path, text: str) -> list[str]:
    payload = _python_string_payload(text) if path.suffix.lower() == ".py" else text
    findings = [
        label for label, pattern in SECRET_PATTERNS.items() if pattern.search(payload)
    ]
    if path.suffix.lower() == ".py" and _python_has_literal_credential_assignment(text):
        findings.append("credential assignment")
    return list(dict.fromkeys(findings))


def _verify_hashed_resource_manifest(
    directory: Path,
    *,
    expected_files: set[str],
    nested_hash: bool,
    errors: list[str],
    checks: list[str],
) -> dict[str, object] | None:
    manifest_path = directory / "MANIFEST.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        records = manifest.get("files")
        if not isinstance(records, dict):
            raise ValueError("files must be an object")
        recorded_files = set(records)
        disk_files = {
            item.name
            for item in directory.iterdir()
            if item.is_file() and item.name != "MANIFEST.json"
        }
        if recorded_files != expected_files:
            errors.append(
                f"resource manifest file set mismatch: {manifest_path.relative_to(directory.parents[1])}"
            )
        if disk_files != expected_files:
            errors.append(
                f"resource directory file set mismatch: {directory.relative_to(directory.parents[1])}"
            )
        for filename in sorted(expected_files & recorded_files & disk_files):
            record = records[filename]
            expected_hash = record.get("sha256") if nested_hash and isinstance(record, dict) else record
            if not isinstance(expected_hash, str) or not re.fullmatch(
                r"[A-Fa-f0-9]{64}", expected_hash
            ):
                errors.append(f"invalid resource hash: {directory.name}/{filename}")
                continue
            actual_hash = hashlib.sha256((directory / filename).read_bytes()).hexdigest()
            if actual_hash.casefold() != expected_hash.casefold():
                errors.append(f"resource hash mismatch: {directory.name}/{filename}")
            else:
                checks.append(f"resource-hash:{directory.name}/{filename}")
        return manifest
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        errors.append(f"resource manifest invalid: {manifest_path}: {error}")
        return None


def _checksum_population(root: Path) -> set[str]:
    output = set()
    for path in _iter_release_files(root):
        relative = path.relative_to(root)
        if path.name in EXCLUDED_FILES:
            continue
        output.add(relative.as_posix())
    return output


def _iter_release_files(root: Path):
    """Yield release files without descending into output, venvs, or caches.

    只枚举发布文件，不进入输出目录、虚拟环境或缓存。
    """
    for current, directories, filenames in os.walk(root):
        current_path = Path(current)
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in EXCLUDED_PARTS and not directory.endswith(".egg-info")
        )
        for directory in directories:
            candidate = current_path / directory
            if candidate.is_symlink() or getattr(candidate, "is_junction", lambda: False)():
                raise RuntimeError(f"linked directory is forbidden in release tree: {candidate}")
        for filename in sorted(filenames):
            candidate = current_path / filename
            if candidate.suffix.lower() in EXCLUDED_SUFFIXES:
                continue
            if candidate.is_symlink():
                raise RuntimeError(f"linked file is forbidden in release tree: {candidate}")
            candidate.resolve().relative_to(root)
            yield candidate


def main() -> int:
    _configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--skip-runtime-smoke",
        action="store_true",
        help="Skip external-tool and end-to-end capability probes; integrity tests still run.",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[str] = []
    try:
        release_files = list(_iter_release_files(root))
    except (OSError, RuntimeError, ValueError) as error:
        release_files = []
        errors.append(f"release tree safety check failed: {error}")

    for relative in REQUIRED:
        path = root / relative
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing or empty: {relative}")
        else:
            checks.append(f"file:{relative}")

    for path in (item for item in release_files if item.suffix.lower() == ".py"):
        relative = path.relative_to(root)
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            checks.append(f"python:{relative.as_posix()}")
        except Exception as error:  # noqa: BLE001
            errors.append(f"python syntax: {path}: {error}")

    json_paths = [path for path in release_files if path.suffix.lower() == ".json"]
    for path in json_paths:
        try:
            json.loads(path.read_text(encoding="utf-8"))
            checks.append(f"json:{path.relative_to(root).as_posix()}")
        except Exception as error:  # noqa: BLE001
            errors.append(f"json invalid: {path.relative_to(root).as_posix()}: {error}")

    tessdata_manifest = _verify_hashed_resource_manifest(
        root / "resources" / "tessdata",
        expected_files=TESSDATA_FILES,
        nested_hash=False,
        errors=errors,
        checks=checks,
    )
    if tessdata_manifest is not None:
        for key, expected in TESSDATA_METADATA.items():
            if tessdata_manifest.get(key) != expected:
                errors.append(f"tessdata manifest {key} is not the fixed release value")
        if not any(error.startswith("tessdata manifest") for error in errors):
            checks.append("tessdata-fixed-upstream-revision")

    probe_manifest = _verify_hashed_resource_manifest(
        root / "resources" / "ocr_probes",
        expected_files=OCR_PROBE_FILES,
        nested_hash=True,
        errors=errors,
        checks=checks,
    )
    if probe_manifest is not None:
        generation = probe_manifest.get("generation")
        canonical_probe_metadata = {
            "schema": 2,
            "generator": "scripts/generate_ocr_probes.py",
        }
        for key, expected in canonical_probe_metadata.items():
            if probe_manifest.get(key) != expected:
                errors.append(f"OCR probe manifest {key} is not the release value")
        if not isinstance(generation, dict):
            errors.append("OCR probe manifest generation metadata is missing")
        else:
            if generation.get("font_sha256") != (
                "2C76254F6FC379FDDFCE0A7E84FB5385BB135D3E399294F6EEB6680D0365B74B"
            ):
                errors.append("OCR probe canonical font hash mismatch")
            if generation.get("pillow_version") != "12.3.0":
                errors.append("OCR probe Pillow version is not the tested release version")
        probe_records = probe_manifest.get("files", {})
        expected_text = {
            "chi_sim_probe.png": "工厂生产 316 不锈钢",
            "chi_tra_probe.png": "工廠生產 316 不鏽鋼",
        }
        for filename, text_value in expected_text.items():
            record = probe_records.get(filename)
            if not isinstance(record, dict) or record.get("text") != text_value:
                errors.append(f"OCR probe text mismatch: {filename}")
        if not any(error.startswith("OCR probe") for error in errors):
            checks.append("ocr-probe-fixed-generation-provenance")

    local_link = re.compile(r"\[[^\]]+\]\((?!https?://|mailto:|#)([^)]+)\)")
    for path in (item for item in release_files if item.suffix.lower() == ".md"):
        relative = path.relative_to(root)
        for target in local_link.findall(path.read_text(encoding="utf-8")):
            clean = target.strip("<>").split("#", 1)[0]
            if clean and not (path.parent / clean).exists():
                errors.append(
                    "broken local markdown link: "
                    f"{relative.as_posix()} -> {target}"
                )

    source_checksum_path = root / "CHECKSUMS_SHA256.txt"
    package_checksum_path = root / "PACKAGE_CHECKSUMS_SHA256.txt"
    checksum_path = (
        source_checksum_path
        if source_checksum_path.is_file()
        else package_checksum_path
    )
    if checksum_path.is_file():
        listed_paths: set[str] = set()
        for line_number, line in enumerate(
            checksum_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                expected, relative = line.split(maxsplit=1)
                relative = relative.strip()
                if relative in listed_paths:
                    errors.append(
                        f"duplicate checksum target at line {line_number}: {relative}"
                    )
                listed_paths.add(relative)
                target = (root / relative).resolve()
                target.relative_to(root)
                if not target.is_file():
                    errors.append(
                        f"checksum target missing at line {line_number}: {relative}"
                    )
                    continue
                digest = hashlib.sha256(target.read_bytes()).hexdigest().upper()
                if digest != expected.upper():
                    errors.append(f"checksum mismatch: {relative}")
                else:
                    checks.append(f"checksum:{relative}")
            except (ValueError, OSError) as error:
                errors.append(f"bad checksum line {line_number}: {error}")
        expected_paths = _checksum_population(root)
        for relative in sorted(expected_paths - listed_paths):
            errors.append(f"checksum coverage missing: {relative}")
        for relative in sorted(listed_paths - expected_paths):
            errors.append(f"checksum contains excluded/unexpected path: {relative}")
    else:
        errors.append(
            "missing CHECKSUMS_SHA256.txt or PACKAGE_CHECKSUMS_SHA256.txt"
        )

    try:
        pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8")
        pyproject = tomllib.loads(pyproject_text)
        version_file = (root / "VERSION").read_text(encoding="utf-8").strip()
        init_text = (root / "src" / "factorytrace" / "__init__.py").read_text(
            encoding="utf-8"
        )
        init_match = re.search(
            r'(?m)^__version__\s*=\s*"([^"]+)"\s*$', init_text
        )
        versions = {
            version_file,
            str(pyproject.get("project", {}).get("version", "")),
            init_match.group(1) if init_match else "",
        }
        if "" in versions or len(versions) != 1:
            errors.append(f"version mismatch: {sorted(versions)}")
        else:
            checks.append(f"version:{version_file}")
        project = pyproject.get("project", {})
        if project.get("requires-python") != ">=3.11,<3.15":
            errors.append("pyproject requires-python must be >=3.11,<3.15")
        direct_specs = list(project.get("dependencies", []))
        extras = project.get("optional-dependencies", {})
        full_specs = list(extras.get("full", []))
        component_specs = []
        for extra_name in ("reports", "media", "packs"):
            component_specs.extend(extras.get(extra_name, []))
        if {_normalized_requirement_spec(item) for item in full_specs} != {
            _normalized_requirement_spec(item) for item in component_specs
        }:
            errors.append("pyproject full extra is not the union of reports/media/packs")
        requirement_specs = [
            line.strip()
            for line in (root / "requirements.txt")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        supported_specs = {
            _normalized_requirement_spec(item) for item in direct_specs + full_specs
        }
        supported_names = {
            _requirement_name(item) for item in direct_specs + full_specs
        }
        if {
            _normalized_requirement_spec(item) for item in requirement_specs
        } != supported_specs:
            errors.append(
                "requirements.txt specifications do not match pyproject core + full extras"
            )
        constraint_specs = [
            line.strip()
            for line in (root / "constraints-tested.txt")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        non_exact = [item for item in constraint_specs if "==" not in item]
        if non_exact:
            errors.append(f"constraints are not exact: {non_exact}")
        constraint_names = {_requirement_name(item) for item in constraint_specs}
        missing_constraints = supported_names - constraint_names
        if missing_constraints:
            errors.append(
                "constraints missing supported dependencies: "
                + ", ".join(sorted(missing_constraints))
            )
        build_requires = set(pyproject.get("build-system", {}).get("requires", []))
        if "setuptools==83.0.0" not in build_requires:
            errors.append("pyproject build backend is not pinned to setuptools==83.0.0")
        elif "setuptools" not in constraint_names:
            errors.append("constraints missing setuptools build backend")
        else:
            checks.append("dependency-metadata-consistency")
    except (OSError, tomllib.TOMLDecodeError, TypeError, ValueError) as error:
        errors.append(f"version files invalid: {error}")

    try:
        import yaml
    except ImportError as error:
        errors.append(f"YAML parser unavailable: {error}")
    else:
        try:
            yaml_paths = [
                path
                for path in release_files
                if path.suffix.lower() in {".yml", ".yaml"}
            ]
            for path in yaml_paths:
                yaml.safe_load(path.read_text(encoding="utf-8"))
                checks.append(f"yaml:{path.relative_to(root).as_posix()}")
        except (OSError, yaml.YAMLError) as error:
            errors.append(f"YAML invalid: {error}")

    for path in release_files:
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if path.name in PORTABLE_LOCAL_FILES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            for label in _portable_findings(path, text):
                errors.append(f"portable scan found {label}: {relative.as_posix()}")
        except SyntaxError as error:
            errors.append(f"portable Python scan failed: {relative.as_posix()}: {error}")
        checks.append(f"portable-scan:{relative.as_posix()}")

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(root / "src")
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    process = subprocess.run(
        [
            sys.executable,
            "-W",
            "error::DeprecationWarning",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-v",
        ],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if process.returncode:
        errors.append("unit tests failed")
    else:
        checks.append("unit-tests")

    dependency_check = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    if dependency_check.returncode:
        errors.append(f"pip check failed: {dependency_check.stdout.strip()}")
    else:
        checks.append("pip-check")

    runtime_smoke: dict[str, object] | None = None
    end_to_end_smoke: dict[str, object] | None = None
    if not args.skip_runtime_smoke:
        with tempfile.TemporaryDirectory(prefix="factorytrace-verify-") as temporary:
            temporary_root = Path(temporary)
            capability_output = temporary_root / "capability.json"
            capability_process = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "capability_smoke.py"),
                    "--work-root",
                    str(root),
                    "--output",
                    str(capability_output),
                ],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
            )
            if capability_output.is_file():
                runtime_smoke = json.loads(capability_output.read_text(encoding="utf-8"))
            if capability_process.returncode or not runtime_smoke:
                errors.append(
                    "dependency capability smoke failed: "
                    f"{capability_process.stderr.strip() or capability_process.stdout.strip()}"
                )
            elif runtime_smoke.get("status") != "PASS":
                errors.append("dependency capability smoke reported FAIL")
            else:
                checks.append("dependency-capability-smoke")

            integration_output = temporary_root / "v2-end-to-end.json"
            integration_process = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "v2_end_to_end_smoke.py"),
                    "--output",
                    str(integration_output),
                ],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=240,
            )
            if integration_output.is_file():
                end_to_end_smoke = json.loads(
                    integration_output.read_text(encoding="utf-8")
                )
            if integration_process.returncode or not end_to_end_smoke:
                errors.append(
                    "v2 end-to-end smoke failed: "
                    f"{integration_process.stderr.strip() or integration_process.stdout.strip()}"
                )
            elif end_to_end_smoke.get("status") != "PASS":
                errors.append("v2 end-to-end smoke reported FAIL")
            else:
                checks.append("v2-end-to-end-smoke")
    else:
        warnings.append(
            "runtime capability smoke was explicitly skipped; external tools were not verified"
        )

    report = {
        "schema": 1,
        "root": str(root),
        "status": "PASS" if not errors else "FAIL",
        "checks_passed": len(checks),
        "errors": errors,
        "warnings": warnings,
        "test_stdout": process.stdout,
        "test_stderr": process.stderr,
        "runtime_smoke": runtime_smoke,
        "end_to_end_smoke": end_to_end_smoke,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
