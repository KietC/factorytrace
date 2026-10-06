"""English: Validate JSON against packaged local schemas with explicit dependency errors.

中文：依据打包的本地 Schema 验证 JSON 并显式报告依赖缺失；不把缺少验证器当作验证通过。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ._resources import resource_directory


DEFAULT_SCHEMA_DIR = resource_directory("schemas")


class SchemaDependencyError(RuntimeError):
    """The JSON Schema validation runtime is unavailable.

    中文：缺少Schema验证运行库的显式错误，不应把未执行检查误记为通过。
    """


class DocumentValidationError(ValueError):
    def __init__(self, schema_name: str, errors: list[dict[str, Any]]) -> None:
        self.schema_name = schema_name
        self.errors = errors
        rendered = "; ".join(
            f"{item['path'] or '<root>'}: {item['message']}" for item in errors[:5]
        )
        if len(errors) > 5:
            rendered += f"; and {len(errors) - 5} more"
        super().__init__(f"document does not satisfy {schema_name}: {rendered}")


def _jsonschema_runtime() -> tuple[Any, Any, Any, Any]:
    try:
        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry, Resource
    except ImportError as error:
        raise SchemaDependencyError(
            "JSON Schema validation requires 'jsonschema' and 'referencing'; "
            "install them with: python -m pip install 'jsonschema>=4.23'"
        ) from error
    return Draft202012Validator, FormatChecker, Registry, Resource


def _safe_schema_path(schema_name: str, schema_dir: Path) -> Path:
    root = schema_dir.resolve()
    path = (root / schema_name).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValueError(f"schema path leaves schema directory: {schema_name}") from error
    if not path.is_file():
        raise FileNotFoundError(f"schema not found: {path}")
    return path


def _schema_registry(schema_dir: Path, Registry: Any, Resource: Any) -> Any:
    registry = Registry()
    for path in schema_dir.glob("*.schema.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(schema)
        registry = registry.with_resource(path.resolve().as_uri(), resource)
        if isinstance(schema, dict) and schema.get("$id"):
            registry = registry.with_resource(str(schema["$id"]), resource)
    return registry


def _format_errors(errors: list[Any]) -> list[dict[str, Any]]:
    formatted: list[dict[str, Any]] = []
    for error in errors:
        path = "/".join(str(part) for part in error.absolute_path)
        schema_path = "/".join(str(part) for part in error.absolute_schema_path)
        formatted.append(
            {
                "path": path,
                "schema_path": schema_path,
                "message": error.message,
                "validator": error.validator,
            }
        )
    return formatted


def validate_instance(
    instance: Any,
    schema_name: str,
    *,
    schema_dir: Path | None = None,
    check_formats: bool = True,
) -> None:
    """Validate an instance or raise an explicit dependency/validation error.

    中文：用本地Schema验证输入，依赖缺失与字段错误分别报错；失败时不返回假成功。
    """
    Draft202012Validator, FormatChecker, Registry, Resource = _jsonschema_runtime()
    root = Path(schema_dir or DEFAULT_SCHEMA_DIR)
    schema_path = _safe_schema_path(schema_name, root)
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(
        schema,
        registry=_schema_registry(root, Registry, Resource),
        format_checker=FormatChecker() if check_formats else None,
    )
    errors = sorted(
        validator.iter_errors(instance),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        raise DocumentValidationError(schema_name, _format_errors(errors))


def validation_report(
    instance: Any,
    schema_name: str,
    *,
    schema_dir: Path | None = None,
    check_formats: bool = True,
) -> dict[str, Any]:
    try:
        validate_instance(
            instance,
            schema_name,
            schema_dir=schema_dir,
            check_formats=check_formats,
        )
    except DocumentValidationError as error:
        return {
            "valid": False,
            "schema": schema_name,
            "errors": error.errors,
        }
    return {"valid": True, "schema": schema_name, "errors": []}


def validate_json_file(
    document_path: Path,
    schema_name: str,
    *,
    schema_dir: Path | None = None,
    check_formats: bool = True,
) -> dict[str, Any]:
    document = json.loads(Path(document_path).read_text(encoding="utf-8-sig"))
    return validation_report(
        document,
        schema_name,
        schema_dir=schema_dir,
        check_formats=check_formats,
    )
