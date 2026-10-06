"""English: Inspect Python packages, media tools, and host capabilities for deployment checks.

中文：检查 Python 依赖、媒体工具与环境能力；只记录实际检测结果，环境清单可能含主机信息，不应直接公开。
"""

from __future__ import annotations

import ctypes
import json
import locale
import os
import platform
import shutil
import ssl
import sys
import tempfile
from importlib import metadata
from pathlib import Path
from typing import Any

from . import __version__ as source_version
from .common import atomic_write_json, utc_now


GIB = 1024**3

RESOURCE_PROFILES: dict[str, dict[str, Any]] = {
    "minimum": {
        "logical_cpus": 4,
        "ram_gib": 8,
        "free_disk_gib": 5,
        "ingest_workers": 2,
        "compare_workers": 2,
        "fetch_workers": 4,
        "per_host": 1,
        "delay_seconds": 2,
        "use_case": "Small case, manual browser search, scripts only",
    },
    "balanced": {
        "logical_cpus": 8,
        "ram_gib": 16,
        "free_disk_gib": 20,
        "ingest_workers": 4,
        "compare_workers": 4,
        "fetch_workers": 8,
        "per_host": 2,
        "delay_seconds": 1,
        "use_case": "Normal case with hundreds of images/pages",
    },
    "workstation": {
        "logical_cpus": 16,
        "ram_gib": 32,
        "free_disk_gib": 50,
        "ingest_workers": 8,
        "compare_workers": 8,
        "fetch_workers": 8,
        "per_host": 2,
        "delay_seconds": 1,
        "use_case": "Large multi-source case; cross-domain parallel work",
    },
}


def _memory_total_bytes() -> int | None:
    if os.name == "nt":
        class MemoryStatusEx(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatusEx()
        status.dwLength = ctypes.sizeof(MemoryStatusEx)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.ullTotalPhys)
        return None

    try:
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
        page_count = int(os.sysconf("SC_PHYS_PAGES"))
        if page_size > 0 and page_count > 0:
            return page_size * page_count
    except (AttributeError, OSError, TypeError, ValueError):
        pass
    return None


def _existing_anchor(path: Path) -> Path:
    current = path.expanduser().resolve()
    if current.is_file():
        current = current.parent
    while not current.exists() and current != current.parent:
        current = current.parent
    return current


def _package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _installed_distribution_inventory() -> dict[str, str]:
    """Return the installed Python distribution name/version inventory.

    中文：记录已安装分发包的名称与版本，以实际环境为准，不表示依赖全部经过功能验证。
    """
    inventory: dict[str, str] = {}
    for distribution in metadata.distributions():
        name = str(distribution.metadata.get("Name") or "").strip()
        if name:
            inventory[name] = distribution.version
    return dict(sorted(inventory.items(), key=lambda item: item[0].casefold()))


def _pillow_supported(version: str | None) -> bool:
    if not version:
        return False
    try:
        major = int(version.split(".", 1)[0])
    except ValueError:
        return False
    return 10 <= major < 13


def _tool(name: str, *alternatives: str) -> str | None:
    for candidate in (name, *alternatives):
        found = shutil.which(candidate)
        if found:
            return found
    # Some Windows installers update the registry/user PATH after the parent
    # Codex process has started, and Tesseract does not add itself to PATH at
    # all.  Resolve the documented per-machine/per-user locations as a stable
    # fallback so a freshly installed tool is usable without an app restart.
    # 中文：父进程的PATH可能过期，Tesseract也可能未添加PATH；因此检查标准安装位置以便无需重启就能使用。
    if os.name == "nt":
        program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        local_app_data = Path(
            os.environ.get(
                "LOCALAPPDATA", str(Path.home() / "AppData" / "Local")
            )
        )
        known: dict[str, tuple[Path, ...]] = {
            "tesseract": (program_files / "Tesseract-OCR" / "tesseract.exe",),
            "exiftool": (
                local_app_data / "Programs" / "ExifTool" / "exiftool.exe",
                program_files / "ExifTool" / "exiftool.exe",
            ),
            "chrome": (
                program_files / "Google" / "Chrome" / "Application" / "chrome.exe",
                Path(os.environ.get("ProgramFiles(x86)", str(program_files)))
                / "Google"
                / "Chrome"
                / "Application"
                / "chrome.exe",
                local_app_data / "Google" / "Chrome" / "Application" / "chrome.exe",
            ),
            "msedge": (
                program_files / "Microsoft" / "Edge" / "Application" / "msedge.exe",
                Path(os.environ.get("ProgramFiles(x86)", str(program_files)))
                / "Microsoft"
                / "Edge"
                / "Application"
                / "msedge.exe",
            ),
            "firefox": (
                program_files / "Mozilla Firefox" / "firefox.exe",
                Path(os.environ.get("ProgramFiles(x86)", str(program_files)))
                / "Mozilla Firefox"
                / "firefox.exe",
            ),
        }
        for candidate in (name, *alternatives):
            for path in known.get(candidate.lower(), ()):
                if path.is_file():
                    return str(path)
    if platform.system() == "Darwin":
        known_macos = {
            "chrome": Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            "msedge": Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
            "firefox": Path("/Applications/Firefox.app/Contents/MacOS/firefox"),
            "safari": Path("/Applications/Safari.app/Contents/MacOS/Safari"),
        }
        for candidate in (name, *alternatives):
            path = known_macos.get(candidate.lower())
            if path is not None and path.is_file():
                return str(path)
    return None


def _writable_unicode_path(anchor: Path) -> tuple[bool, str | None]:
    try:
        with tempfile.TemporaryDirectory(
            prefix="factorytrace-环境-",
            dir=anchor,
        ) as temporary:
            probe = Path(temporary) / "路径 smoke ✅.txt"
            probe.write_text("UTF-8 ✓\n", encoding="utf-8")
            if probe.read_text(encoding="utf-8") != "UTF-8 ✓\n":
                return False, "unicode probe content mismatch"
        return True, None
    except OSError as error:
        return False, str(error)


def _pillow_features() -> dict[str, bool | None]:
    try:
        from PIL import features

        names = ("jpg", "zlib", "webp", "libtiff")
        return {name: bool(features.check(name)) for name in names}
    except (ImportError, ValueError):
        return {name: None for name in ("jpg", "zlib", "webp", "libtiff")}


def _profile_passes(
    profile: dict[str, Any],
    *,
    logical_cpus: int,
    ram_bytes: int | None,
    disk_free_bytes: int,
) -> bool:
    if logical_cpus < int(profile["logical_cpus"]):
        return False
    if ram_bytes is not None and ram_bytes < float(profile["ram_gib"]) * GIB:
        return False
    return disk_free_bytes >= float(profile["free_disk_gib"]) * GIB


def _select_profile(
    logical_cpus: int, ram_bytes: int | None, disk_free_bytes: int
) -> str:
    selected = "minimum"
    for name in ("minimum", "balanced", "workstation"):
        if _profile_passes(
            RESOURCE_PROFILES[name],
            logical_cpus=logical_cpus,
            ram_bytes=ram_bytes,
            disk_free_bytes=disk_free_bytes,
        ):
            selected = name
    return selected


def build_environment_report(
    *,
    anchor: Path,
    requested_profile: str = "auto",
    model_mode: str = "undeclared",
    model_ids: list[str] | None = None,
    external_visual_services: list[str] | None = None,
) -> dict[str, Any]:
    existing_anchor = _existing_anchor(anchor)
    disk = shutil.disk_usage(existing_anchor)
    logical_cpus = os.cpu_count() or 1
    ram_bytes = _memory_total_bytes()
    pillow_version = _package_version("Pillow")
    pip_version = _package_version("pip")
    toolkit_version = _package_version("factory-trace-toolkit")
    version_file = Path(__file__).resolve().parents[2] / "VERSION"
    version_file_value = (
        version_file.read_text(encoding="utf-8").strip()
        if version_file.is_file()
        else None
    )
    path_writable, path_error = _writable_unicode_path(existing_anchor)
    ssl_paths = ssl.get_default_verify_paths()

    core_checks = {
        "python_supported_3_11_to_3_14": (3, 11) <= sys.version_info < (3, 15),
        "python_64bit": sys.maxsize > 2**32,
        "pillow_10_to_12": _pillow_supported(pillow_version),
        "jsonschema_available": _package_version("jsonschema") is not None,
        "toolkit_source_version_consistent": (
            version_file_value is None or version_file_value == source_version
        ),
        "minimum_logical_cpus": logical_cpus
        >= RESOURCE_PROFILES["minimum"]["logical_cpus"],
        "minimum_ram": (
            None
            if ram_bytes is None
            else ram_bytes >= RESOURCE_PROFILES["minimum"]["ram_gib"] * GIB
        ),
        "minimum_free_disk": disk.free
        >= RESOURCE_PROFILES["minimum"]["free_disk_gib"] * GIB,
        "unicode_path_is_writable": path_writable,
    }
    hard_failures = [
        name for name, passed in core_checks.items() if passed is False
    ]
    warnings = [
        name for name, passed in core_checks.items() if passed is None
    ]
    if toolkit_version is not None and toolkit_version != source_version:
        warnings.append(
            f"installed_metadata_differs_from_source:{toolkit_version}!={source_version}"
        )
    if pip_version != "26.1.2":
        warnings.append(f"pip_differs_from_tested:{pip_version}!=26.1.2")
    stdout_encoding = getattr(sys.stdout, "encoding", None)
    if stdout_encoding and stdout_encoding.lower().replace("-", "") not in {
        "utf8",
        "utf8sig",
    }:
        warnings.append(f"stdout_not_utf8:{stdout_encoding}")

    recommended_profile = _select_profile(logical_cpus, ram_bytes, disk.free)
    effective_profile = (
        recommended_profile if requested_profile == "auto" else requested_profile
    )
    profile_ok = _profile_passes(
        RESOURCE_PROFILES[effective_profile],
        logical_cpus=logical_cpus,
        ram_bytes=ram_bytes,
        disk_free_bytes=disk.free,
    )
    if not profile_ok:
        warnings.append(f"requested_profile_not_met:{effective_profile}")

    optional_packages = {
        name: value
        for name in (
            "torch",
            "transformers",
            "llama-cpp-python",
            "openai",
            "anthropic",
        )
        if (value := _package_version(name)) is not None
    }
    local_model_tools = {
        name: value
        for name, value in {
            "ollama": _tool("ollama"),
            "llama-cli": _tool("llama-cli"),
        }.items()
        if value
    }
    model_ids = [value.strip() for value in (model_ids or []) if value.strip()]
    external_visual_services = [
        value.strip()
        for value in (external_visual_services or [])
        if value.strip()
    ]
    if model_mode in {"local", "hybrid", "cloud"} and not model_ids:
        warnings.append("model_mode_declared_without_model_id")
    if model_mode in {"local", "hybrid"}:
        warnings.append(
            "local_model_capacity_not_assessed:GPU_VRAM_weights_context_runtime"
        )

    profile = RESOURCE_PROFILES[effective_profile]
    report = {
        "schema": 1,
        "captured_at_utc": utc_now(),
        "status": "PASS" if not hard_failures else "FAIL",
        "anchor": str(existing_anchor),
        "runtime": {
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "python_executable": sys.executable,
            "python_64bit": sys.maxsize > 2**32,
            "toolkit_source_version": source_version,
            "toolkit_version_file": version_file_value,
            "filesystem_encoding": sys.getfilesystemencoding(),
            "preferred_encoding": locale.getpreferredencoding(False),
            "stdout_encoding": stdout_encoding,
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "resources": {
            "logical_cpus": logical_cpus,
            "ram_bytes": ram_bytes,
            "ram_gib": None if ram_bytes is None else round(ram_bytes / GIB, 2),
            "disk_total_bytes": disk.total,
            "disk_free_bytes": disk.free,
            "disk_free_gib": round(disk.free / GIB, 2),
        },
        "dependencies": {
            "factory-trace-toolkit": {
                "installed_version": toolkit_version,
                "required": "current checked-out source or installed package",
            },
            "pip": {
                "installed_version": pip_version,
                "tested": "==26.1.2",
            },
            "Pillow": {
                "installed_version": pillow_version,
                "required": ">=10.0,<13",
                "codec_features": _pillow_features(),
            },
            "jsonschema": {
                "installed_version": _package_version("jsonschema"),
                "required": ">=4.23,<5",
            },
            "openpyxl": {
                "installed_version": _package_version("openpyxl"),
                "required_for": "optional XLSX reports",
            },
            "python-docx": {
                "installed_version": _package_version("python-docx"),
                "required_for": "optional DOCX reports",
            },
            "numpy": {
                "installed_version": _package_version("numpy"),
                "required_for": "optional OpenCV media fingerprinting",
            },
            "opencv-python-headless": {
                "installed_version": _package_version("opencv-python-headless"),
                "required_for": "optional media fingerprinting and visual comparison",
            },
            "PyYAML": {
                "installed_version": _package_version("PyYAML"),
                "required_for": "optional YAML process-pack loading",
            },
            "setuptools-build-backend": {
                "installed_in_runtime": _package_version("setuptools"),
                "required_in_isolated_build": "==83.0.0",
            },
            "installed_distribution_inventory": _installed_distribution_inventory(),
        },
        "network_runtime": {
            "tls_default_verify_paths": {
                "cafile": ssl_paths.cafile,
                "capath": ssl_paths.capath,
                "openssl_cafile_env": ssl_paths.openssl_cafile_env,
                "openssl_capath_env": ssl_paths.openssl_capath_env,
            },
            "proxy_variables_present": {
                "http_proxy_any_case": bool(
                    os.environ.get("HTTP_PROXY")
                    or os.environ.get("http_proxy")
                ),
                "https_proxy_any_case": bool(
                    os.environ.get("HTTPS_PROXY")
                    or os.environ.get("https_proxy")
                ),
                "no_proxy_any_case": bool(
                    os.environ.get("NO_PROXY")
                    or os.environ.get("no_proxy")
                ),
            },
            "secrets_recorded": False,
        },
        "optional_tools": {
            "exiftool": _tool("exiftool"),
            "ffmpeg": _tool("ffmpeg"),
            "ffprobe": _tool("ffprobe"),
            "tesseract": _tool("tesseract"),
            "git": _tool("git"),
            "browser_candidates": {
                name: value
                for name, value in {
                    "chrome": _tool("chrome", "google-chrome", "chromium"),
                    "edge": _tool("msedge", "microsoft-edge"),
                    "firefox": _tool("firefox"),
                    "safari": _tool("safari"),
                }.items()
                if value
            },
        },
        "model": {
            "required_by_core": False,
            "declared_mode": model_mode,
            "declared_model_ids": model_ids,
            "external_visual_search_services": external_visual_services,
            "detected_optional_python_packages": optional_packages,
            "detected_local_model_tools": local_model_tools,
            "audit_note": (
                "Detection only reports installed runtimes. It cannot prove that a "
                "model was or was not used. Record every model call in "
                "logs/model_usage_log.csv."
            ),
        },
        "profile": {
            "requested": requested_profile,
            "recommended": recommended_profile,
            "effective": effective_profile,
            "requirements_met": profile_ok,
            "settings": profile,
            "commands": {
                "ingest": f"--workers {profile['ingest_workers']}",
                "compare": f"--workers {profile['compare_workers']}",
                "fetch": (
                    f"--workers {profile['fetch_workers']} "
                    f"--per-host {profile['per_host']} "
                    f"--delay {profile['delay_seconds']}"
                ),
            },
        },
        "checks": core_checks,
        "hard_failures": hard_failures,
        "warnings": warnings
        + ([f"unicode_path_probe:{path_error}"] if path_error else []),
    }
    return report


def run(args: object) -> int:
    output = args.output
    if output is None and args.case_root is not None:
        output = args.case_root / "output" / "environment.json"
    anchor = output.parent if output is not None else (args.case_root or Path.cwd())
    report = build_environment_report(
        anchor=anchor,
        requested_profile=args.profile,
        model_mode=args.model_mode,
        model_ids=args.model_id,
        external_visual_services=args.external_visual_service,
    )
    if output is not None:
        atomic_write_json(output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        return 1
    if args.strict and not report["profile"]["requirements_met"]:
        return 2
    return 0
