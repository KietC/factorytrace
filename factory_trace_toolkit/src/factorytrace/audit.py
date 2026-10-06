"""English: Audit case integrity and stage-specific evidence gates before delivery.

中文：交付前核验案件完整性与分阶段证据门槛；流程 PASS 不等于已确认厂家，缺失与反证必须区分。
"""

from __future__ import annotations

import csv
import json
import urllib.parse
from pathlib import Path
from typing import Any

from .common import (
    atomic_write_json,
    atomic_write_text,
    load_json,
    path_within,
    sha256_file,
    utc_now,
)
from .scoring import score_candidate, source_cluster_key
from .schema_validation import validation_report
from .ledger import FIELDS as LEDGER_FIELDS


REQUIRED_DIRS = (
    "artifacts/original",
    "work/variants",
    "work/queries",
    "evidence/web",
    "evidence/factory",
    "evidence/certificates",
    "evidence/communications",
    "candidates",
    "output",
    "logs",
)
REQUIRED_FILES = (
    "case.json",
    "manifest.json",
    "notes.md",
    "STATUS.md",
    "claims.jsonl",
    "work/product_profile.json",
    "work/crop_plan.json",
    "work/research_round.json",
    "work/materials_plan.json",
    "evidence/evidence_register.csv",
    "evidence/url_queue.csv",
    "evidence/contacts.csv",
    "output/search_log.csv",
    "output/environment.json",
    "logs/model_usage_log.csv",
    "logs/execution_log.csv",
)
COMMAND_LOG_PATHS = ("commands.log", "logs/commands.log")
V2_REQUIRED_DIRS = (
    "evidence/government",
    "evidence/social",
    "evidence/trade",
    "evidence/structured",
)
V2_REQUIRED_FILES = (
    "evidence/access_receipts.jsonl",
    "evidence/structured/parties.json",
    "evidence/structured/sites.json",
    "evidence/structured/cert_records.json",
    "evidence/structured/supply_events.json",
    "evidence/structured/social_records.json",
)
MODEL_LOG_FIELDS = {
    "timestamp_utc",
    "run_id",
    "mode",
    "provider_or_runtime",
    "model_id",
    "model_revision",
    "quantization",
    "endpoint_class",
    "prompt_id",
    "input_artifact_ids",
    "output_path",
    "human_verified",
    "evidence_eligible",
    "notes",
}
EXECUTION_LOG_FIELDS = {
    "timestamp_utc",
    "command_id",
    "actor",
    "tool",
    "tool_version",
    "command_or_action",
    "working_directory",
    "input_artifact_ids",
    "output_paths",
    "exit_code",
    "status",
    "notes",
}
SEARCH_LOG_FIELDS = {
    "run_id",
    "cycle_id",
    "action_id",
    "query_id",
    "engine",
    "input_variant",
    "query",
    "searched_at_utc",
    "status",
    "failure_reason",
    "http_or_tool_status",
    "retry_count",
    "next_retry_at_utc",
    "result_url",
    "result_type",
    "candidate_id",
    "evidence_id",
    "tool_receipt_path",
    "notes",
}


def _valid_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _read_csv_rows(
    path: Path, required_fields: set[str]
) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = set(reader.fieldnames or [])
        missing = sorted(required_fields - fields)
        return list(reader), missing


def audit_case(case_root: Path, stage: str) -> dict[str, Any]:
    """Return stage-specific errors, warnings, and checks without inventing evidence.

    中文：按研究、流程或确认阶段返回错误、警告与检查项；最终确认需要完整产品、地点、工序与批次链，流程通过不能越级。
    """
    root = case_root.resolve(strict=True)
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[str] = []
    try:
        case_document = load_json(root / "case.json")
        case_version = int(
            case_document.get("schema_version", case_document.get("schema", 1))
        )
        if case_version == 2:
            case_validation = validation_report(
                case_document, "case.v2.schema.json"
            )
            if not case_validation["valid"]:
                errors.append(
                    f"case.json failed v2 schema validation: {case_validation['errors']}"
                )
        elif stage == "confirmed":
            errors.append("confirmed stage requires schema_version=2")
    except Exception as error:  # noqa: BLE001
        case_version = -1
        errors.append(f"case.json schema inspection failed: {error}")
    required_dirs = (
        (*REQUIRED_DIRS, *V2_REQUIRED_DIRS)
        if case_version == 2
        else REQUIRED_DIRS
    )
    required_files = (
        (*REQUIRED_FILES, *V2_REQUIRED_FILES)
        if case_version == 2
        else REQUIRED_FILES
    )
    for relative in required_dirs:
        if not (root / relative).is_dir():
            errors.append(f"missing directory: {relative}")
        else:
            checks.append(f"directory:{relative}")
    for relative in required_files:
        if not (root / relative).is_file():
            errors.append(f"missing file: {relative}")
        else:
            checks.append(f"file:{relative}")
    command_log = next(
        (relative for relative in COMMAND_LOG_PATHS if (root / relative).is_file()),
        None,
    )
    if command_log is None:
        errors.append("missing file: commands.log (compatible path: logs/commands.log)")
    else:
        checks.append(f"file:{command_log}")
        if command_log != "commands.log":
            warnings.append(
                "legacy logs/commands.log accepted for compatibility; migrate it to "
                "the canonical root commands.log path"
            )

    try:
        environment = load_json(root / "output" / "environment.json")
        if environment.get("status") != "PASS":
            errors.append("output/environment.json: core environment status is not PASS")
        model_section = environment.get("model", {})
        model_mode = str(model_section.get("declared_mode", "undeclared"))
        if model_mode not in {"undeclared", "none", "cloud", "local", "hybrid"}:
            errors.append(f"output/environment.json: invalid model mode {model_mode}")
    except Exception as error:  # noqa: BLE001
        environment = {}
        model_mode = "undeclared"
        errors.append(f"invalid output/environment.json: {error}")

    try:
        model_log_rows, missing = _read_csv_rows(
            root / "logs" / "model_usage_log.csv", MODEL_LOG_FIELDS
        )
        if missing:
            errors.append(f"model_usage_log.csv missing columns: {', '.join(missing)}")
        for row_number, row in enumerate(model_log_rows, start=2):
            if str(row.get("evidence_eligible", "")).strip().lower() not in {
                "",
                "false",
                "no",
                "0",
            }:
                errors.append(
                    f"model_usage_log.csv:{row_number}: model output cannot be evidence eligible"
                )
    except Exception as error:  # noqa: BLE001
        model_log_rows = []
        errors.append(f"model_usage_log.csv invalid: {error}")

    try:
        execution_log_rows, missing = _read_csv_rows(
            root / "logs" / "execution_log.csv", EXECUTION_LOG_FIELDS
        )
        if missing:
            errors.append(f"execution_log.csv missing columns: {', '.join(missing)}")
    except Exception as error:  # noqa: BLE001
        execution_log_rows = []
        errors.append(f"execution_log.csv invalid: {error}")

    try:
        search_log_rows, missing = _read_csv_rows(
            root / "output" / "search_log.csv", SEARCH_LOG_FIELDS
        )
        if missing:
            errors.append(f"search_log.csv missing columns: {', '.join(missing)}")
    except Exception as error:  # noqa: BLE001
        search_log_rows = []
        errors.append(f"search_log.csv invalid: {error}")

    try:
        research_round = load_json(root / "work" / "research_round.json")
        if not research_round.get("cycle_id"):
            errors.append("work/research_round.json: cycle_id is required")
    except Exception as error:  # noqa: BLE001
        errors.append(f"invalid work/research_round.json: {error}")

    try:
        manifest = load_json(root / "manifest.json")
        if not isinstance(manifest.get("artifacts"), list):
            raise ValueError("artifacts is not a list")
    except Exception as error:  # noqa: BLE001
        manifest = {"artifacts": []}
        errors.append(f"invalid manifest.json: {error}")

    by_path = {
        item.get("relative_path"): item
        for item in manifest.get("artifacts", [])
        if item.get("relative_path")
    }
    originals = [
        path for path in (root / "artifacts" / "original").rglob("*") if path.is_file()
    ]
    for original in originals:
        relative = original.relative_to(root).as_posix()
        record = by_path.get(relative)
        if record is None:
            errors.append(f"unmanifested original: {relative}")
            continue
        actual_hash = sha256_file(original)
        if actual_hash.lower() != str(record.get("sha256", "")).lower():
            errors.append(f"original hash mismatch: {relative}")
        if original.stat().st_size != record.get("size"):
            errors.append(f"original size mismatch: {relative}")
        checks.append(f"artifact:{relative}")
    for relative, record in by_path.items():
        target = (root / relative).resolve()
        if not path_within(target, root):
            errors.append(f"manifest path escapes case root: {relative}")
        elif not target.is_file():
            errors.append(f"manifested artifact missing: {relative}")

    score_results = []
    candidates_by_id: dict[str, dict[str, Any]] = {}
    evidence_by_id: dict[str, tuple[str, dict[str, Any]]] = {}
    for candidate_path in sorted((root / "candidates").glob("*.json")):
        try:
            candidate = load_json(candidate_path)
            result = score_candidate(candidate)
            candidate_version = int(
                candidate.get("schema_version", candidate.get("schema", 1))
            )
            if candidate_version == 2:
                candidate_validation = validation_report(
                    candidate, "candidate.v2.schema.json"
                )
                if not candidate_validation["valid"]:
                    errors.append(
                        f"{candidate_path.name}: v2 schema validation failed: "
                        f"{candidate_validation['errors']}"
                    )
                assessment_validation = validation_report(
                    result, "assessment.v2.schema.json"
                )
                if not assessment_validation["valid"]:
                    errors.append(
                        f"{candidate_path.name}: regenerated assessment is invalid: "
                        f"{assessment_validation['errors']}"
                    )
            elif stage == "confirmed":
                errors.append(
                    f"{candidate_path.name}: confirmed stage requires schema_version=2"
                )
            score_results.append(result)
            candidate_id = str(result["candidate_id"])
            if candidate_id in candidates_by_id:
                errors.append(f"duplicate candidate_id: {candidate_id}")
            candidates_by_id[candidate_id] = candidate
            declared = candidate.get("declared_verdict")
            if declared and declared != result["verdict"]:
                errors.append(
                    f"{candidate_path.name}: declared verdict conflicts with computed verdict"
                )
            for item in candidate.get("evidence", []):
                evidence_id = str(item.get("evidence_id", "")).strip()
                if not evidence_id:
                    errors.append(f"{candidate_path.name}: evidence_id is required")
                    evidence_id = "UNKNOWN"
                elif evidence_id in evidence_by_id:
                    errors.append(
                        f"duplicate evidence_id across candidates: {evidence_id}"
                    )
                else:
                    evidence_by_id[evidence_id] = (candidate_path.name, item)
                url = item.get("source_url", "")
                if url and not _valid_url(url):
                    errors.append(
                        f"{candidate_path.name}/{evidence_id}: invalid source_url"
                    )
                local = item.get("local_path", "")
                if local:
                    evidence_path = (root / local).resolve()
                    if not path_within(evidence_path, root):
                        errors.append(
                            f"{candidate_path.name}/{evidence_id}: local_path escapes case"
                        )
                    elif not evidence_path.is_file():
                        errors.append(
                            f"{candidate_path.name}/{evidence_id}: local evidence missing"
                        )
                    elif item.get("sha256") and sha256_file(evidence_path).lower() != str(
                        item["sha256"]
                    ).lower():
                        errors.append(
                            f"{candidate_path.name}/{evidence_id}: evidence hash mismatch"
                        )
                elif item.get("strength") in {"direct", "strong"}:
                    warnings.append(
                        f"{candidate_path.name}/{evidence_id}: strong evidence has no frozen local artifact"
                    )
            checks.append(f"candidate:{candidate_path.name}")
        except Exception as error:  # noqa: BLE001
            errors.append(f"candidate invalid: {candidate_path.name}: {error}")

    claims: list[dict[str, Any]] = []
    claim_ids: set[str] = set()
    try:
        for line_number, line in enumerate(
            (root / "claims.jsonl").read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            claim = json.loads(line)
            claims.append(claim)
            if not claim.get("claim_id") or not claim.get("source_ids"):
                errors.append(
                    f"claims.jsonl:{line_number}: claim_id and source_ids are required"
                )
                continue
            claim_id = str(claim["claim_id"])
            if claim_id in claim_ids:
                errors.append(f"claims.jsonl:{line_number}: duplicate claim_id {claim_id}")
            claim_ids.add(claim_id)
            candidate_id = str(claim.get("candidate_id", ""))
            if candidate_id and candidate_id not in candidates_by_id:
                errors.append(
                    f"claims.jsonl:{line_number}: unknown candidate_id {candidate_id}"
                )
            for source_id in claim.get("source_ids", []):
                if str(source_id) not in evidence_by_id:
                    errors.append(
                        f"claims.jsonl:{line_number}: unknown source_id {source_id}"
                    )
            if stage == "confirmed":
                for field in ("role", "component", "physical_site", "process"):
                    if not str(claim.get(field, "")).strip():
                        errors.append(
                            f"claims.jsonl:{line_number}: confirmed claim missing {field}"
                        )
    except Exception as error:  # noqa: BLE001
        errors.append(f"claims.jsonl invalid: {error}")

    for evidence_id, (candidate_name, item) in evidence_by_id.items():
        claim_id = str(item.get("claim_id", "")).strip()
        if claim_id and claim_id not in claim_ids:
            message = (
                f"{candidate_name}/{evidence_id}: unknown claim_id {claim_id}"
            )
            (errors if stage == "confirmed" else warnings).append(message)

    ledger_by_id: dict[str, dict[str, str]] = {}
    ledger_path = root / "evidence" / "evidence_register.csv"
    try:
        with ledger_path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            missing_ledger_fields = sorted(
                set(LEDGER_FIELDS) - set(reader.fieldnames or [])
            )
            if missing_ledger_fields:
                errors.append(
                    "evidence_register.csv missing columns: "
                    + ", ".join(missing_ledger_fields)
                )
            for row_number, row in enumerate(reader, start=2):
                evidence_id = str(row.get("evidence_id", "")).strip()
                if not evidence_id:
                    continue
                if evidence_id in ledger_by_id:
                    errors.append(
                        f"evidence_register.csv:{row_number}: duplicate evidence_id {evidence_id}"
                    )
                    continue
                ledger_by_id[evidence_id] = row
                canonical = evidence_by_id.get(evidence_id)
                if canonical is None:
                    message = (
                        f"evidence_register.csv:{row_number}: orphan evidence_id {evidence_id}"
                    )
                    (errors if stage == "confirmed" else warnings).append(message)
                    continue
                candidate_name, item = canonical
                compared_fields = (
                    "claim_id",
                    "role",
                    "component",
                    "legal_entity",
                    "physical_site",
                    "process",
                    "source_class",
                    "source_url",
                    "local_path",
                    "stance",
                    "strength",
                    "independence_group",
                    "entity_bind",
                    "site_bind",
                    "sku_bind",
                    "exact_sku_or_revision",
                    "batch_id",
                    "sha256",
                )
                for field in compared_fields:
                    ledger_value = str(row.get(field, "")).strip()
                    canonical_value = str(item.get(field, "")).strip()
                    if (
                        ledger_value
                        and canonical_value
                        and ledger_value != canonical_value
                    ):
                        message = (
                            f"{candidate_name}/{evidence_id}: ledger conflict in {field}"
                        )
                        (errors if stage == "confirmed" else warnings).append(message)
    except Exception as error:  # noqa: BLE001
        errors.append(f"evidence_register.csv invalid: {error}")

    for evidence_id in evidence_by_id:
        if evidence_id not in ledger_by_id:
            message = f"candidate evidence missing from evidence_register.csv: {evidence_id}"
            (errors if stage == "confirmed" else warnings).append(message)

    if stage in {"operational", "confirmed"}:
        if model_mode == "undeclared":
            errors.append(
                "operational stage requires an explicit model mode in environment.json"
            )
        if model_mode in {"cloud", "local", "hybrid"}:
            declared_ids = environment.get("model", {}).get(
                "declared_model_ids", []
            )
            if not declared_ids:
                errors.append(
                    f"model mode {model_mode} requires at least one declared model ID"
                )
            if not model_log_rows:
                errors.append(
                    f"model mode {model_mode} requires model_usage_log.csv entries"
                )
            declared_id_set = {str(value) for value in declared_ids}
            allowed_modes = (
                {"cloud", "local", "hybrid"}
                if model_mode == "hybrid"
                else {model_mode}
            )
            for row_number, row in enumerate(model_log_rows, start=2):
                if str(row.get("mode", "")) not in allowed_modes:
                    errors.append(
                        f"model_usage_log.csv:{row_number}: mode conflicts with environment"
                    )
                if str(row.get("model_id", "")) not in declared_id_set:
                    errors.append(
                        f"model_usage_log.csv:{row_number}: model_id not declared in environment"
                    )
        if not execution_log_rows:
            warnings.append(
                "execution_log.csv has no action rows; exact reproducibility is incomplete"
            )
        if not search_log_rows:
            warnings.append(
                "search_log.csv has no executed/failed search rows"
            )
        image_records = [item for item in manifest.get("artifacts", []) if item.get("image")]
        if not image_records:
            errors.append("operational stage requires at least one manifested source image")
        if not list((root / "work" / "variants").rglob("variant_manifest.json")):
            errors.append("operational stage requires generated image variants")
        if not list((root / "work" / "queries").glob("*.csv")):
            errors.append("operational stage requires generated text query matrix")
        if not evidence_by_id:
            warnings.append(
                "no candidate evidence recorded; operational PASS means pipeline readiness only"
            )
    if stage == "confirmed":
        if not claims:
            errors.append("confirmed stage requires at least one evidence-backed claim")
        if not execution_log_rows:
            errors.append("confirmed stage requires at least one execution log row")
        materials_report_path = root / "output" / "materials_confirmed.json"
        if not materials_report_path.is_file():
            errors.append(
                "confirmed stage requires output/materials_confirmed.json"
            )
        else:
            try:
                materials_report = load_json(materials_report_path)
                if (
                    materials_report.get("status") != "PASS"
                    or materials_report.get("stage") != "confirmed"
                ):
                    errors.append("materials_confirmed.json is not a confirmed PASS")
            except Exception as error:  # noqa: BLE001
                errors.append(f"materials_confirmed.json invalid: {error}")
        for evidence_id, (candidate_name, item) in evidence_by_id.items():
            for field in (
                "captured_at_utc",
                "observed_fact",
                "limitations",
                "review_status",
            ):
                if not str(item.get(field, "")).strip():
                    errors.append(
                        f"{candidate_name}/{evidence_id}: confirmed evidence missing {field}"
                    )
        confirmed = [
            result
            for result in score_results
            if result.get("trace_stage") == "S4_BATCH_LINKED"
        ]
        if not confirmed:
            errors.append(
                "confirmed stage requires a freshly recomputed trace_stage=S4_BATCH_LINKED"
            )
        for result in confirmed:
            candidate = candidates_by_id.get(str(result["candidate_id"]))
            if candidate is not None:
                direct_groups = {
                    source_cluster_key(item, index)
                    for index, item in enumerate(candidate.get("evidence", []))
                    if item.get("strength") == "direct"
                    and item.get("stance") == "support"
                    and item.get("local_path")
                    and item.get("sha256")
                }
                if len(direct_groups) < 2:
                    errors.append(
                        f"{result['candidate_id']}: confirmed requires two frozen independent direct evidence groups"
                    )

    public_assessments = [
        {
            key: value
            for key, value in result.items()
            if key
            not in {
                "confidence_index",
                "manufacturer_probability",
                "source_factory_probability",
            }
        }
        for result in score_results
    ]
    report = {
        "schema": 2,
        "schema_version": 2,
        "case_root": str(root),
        "stage": stage,
        "status": "PASS" if not errors else "FAIL",
        "created_at_utc": utc_now(),
        "checks_passed": len(checks),
        "errors": errors,
        "warnings": warnings,
        "computed_candidate_scores": public_assessments,
        "computed_candidate_assessments": public_assessments,
        "policy": (
            "CSV labels, manually typed verdicts and percentages are not trusted. "
            "Candidate JSON is canonical for the multi-axis assessment; confirmation "
            "requires S4_BATCH_LINKED. Operational PASS means pipeline readiness only."
        ),
    }
    return report


def run(args: object) -> int:
    report = audit_case(args.case_root, args.stage)
    output = args.json_output or (
        args.case_root / "output" / f"audit_{args.stage}.json"
    )
    atomic_write_json(output, report)
    if report["status"] == "PASS":
        case_path = args.case_root / "case.json"
        case = load_json(case_path)
        output_resolved = output.resolve()
        case_resolved = args.case_root.resolve()
        audit_reference = (
            output_resolved.relative_to(case_resolved).as_posix()
            if path_within(output_resolved, case_resolved)
            else str(output_resolved)
        )
        current_status = str(case.get("status", "open"))
        if current_status not in {"superseded", "closed"}:
            if args.stage == "confirmed" or current_status != "confirmed":
                case["status"] = args.stage
                case["last_audit_stage"] = args.stage
                case["last_audit_at_utc"] = report["created_at_utc"]
                case["last_audit_path"] = audit_reference
                atomic_write_json(case_path, case)
                summary = (
                    "# Current status\n\n"
                    f"- Structured status: `{case['status']}`\n"
                    f"- Last audit: `{args.stage}` PASS at "
                    f"`{report['created_at_utc']}`\n"
                    f"- Audit report: `{audit_reference}`\n\n"
                )
                if args.stage == "operational":
                    summary += (
                        "Operational PASS means the preprocessing pipeline is ready. "
                        "It does not confirm any manufacturer.\n"
                    )
                elif args.stage == "confirmed":
                    names = [
                        str(item.get("display_name") or item.get("candidate_id"))
                        for item in report["computed_candidate_scores"]
                        if item.get("trace_stage") == "S4_BATCH_LINKED"
                    ]
                    summary += "Confirmed candidates from this audit: " + ", ".join(
                        names
                    ) + "\n"
                else:
                    summary += "No source factory is confirmed by a research audit.\n"
                atomic_write_text(args.case_root / "STATUS.md", summary)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1
