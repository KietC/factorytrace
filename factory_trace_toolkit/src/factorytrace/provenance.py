"""English: Record model usage and generated-file links as provenance, not source evidence.

中文：记录模型使用与生成文件关联，仅作可追溯元信息；模型输出不能升级为制造或认证证据。
"""

from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path
from typing import Any

from .common import FileLock, path_within, sha256_file, utc_now


MODEL_FIELDS = [
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
]


def log_model_use(
    case_root: Path,
    *,
    mode: str,
    provider_or_runtime: str,
    model_id: str,
    model_revision: str,
    quantization: str,
    endpoint_class: str,
    prompt_id: str,
    input_artifact_ids: list[str],
    output_path: Path | None,
    human_verified: bool,
    notes: str,
    run_id: str | None = None,
) -> dict[str, str]:
    """Append model-run provenance and hash an optional in-case generated output.

    中文：记录模型运行信息，并可对案件内生成输出记哈希；人工复核标记不把模型结论变成外部原始证据。
    """
    root = case_root.resolve(strict=True)
    rendered_output = ""
    output_note = ""
    if output_path is not None:
        resolved_output = output_path.resolve(strict=True)
        if not path_within(resolved_output, root):
            raise ValueError("model output must be stored inside the case root")
        rendered_output = resolved_output.relative_to(root).as_posix()
        output_note = f"output_sha256={sha256_file(resolved_output)}"
    combined_notes = "; ".join(
        value for value in (notes.strip(), output_note) if value
    )
    row = {
        "timestamp_utc": utc_now(),
        "run_id": run_id or f"MODEL-{uuid.uuid4().hex[:12]}",
        "mode": mode,
        "provider_or_runtime": provider_or_runtime,
        "model_id": model_id,
        "model_revision": model_revision,
        "quantization": quantization,
        "endpoint_class": endpoint_class,
        "prompt_id": prompt_id,
        "input_artifact_ids": json.dumps(
            input_artifact_ids, ensure_ascii=False
        ),
        "output_path": rendered_output,
        "human_verified": "true" if human_verified else "false",
        "evidence_eligible": "false",
        "notes": combined_notes,
    }
    log_path = root / "logs" / "model_usage_log.csv"
    with FileLock(root / "logs" / ".model_usage_log.lock"):
        write_header = not log_path.is_file() or log_path.stat().st_size == 0
        encoding = "utf-8-sig" if write_header else "utf-8"
        with log_path.open("a", encoding=encoding, newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=MODEL_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow(row)
    return row


def run(args: object) -> int:
    row = log_model_use(
        args.case_root,
        mode=args.mode,
        provider_or_runtime=args.provider_or_runtime,
        model_id=args.model_id,
        model_revision=args.model_revision,
        quantization=args.quantization,
        endpoint_class=args.endpoint_class,
        prompt_id=args.prompt_id,
        input_artifact_ids=args.input_artifact_id,
        output_path=args.output_path,
        human_verified=args.human_verified,
        notes=args.notes,
        run_id=args.run_id,
    )
    print(json.dumps(row, ensure_ascii=False))
    return 0
