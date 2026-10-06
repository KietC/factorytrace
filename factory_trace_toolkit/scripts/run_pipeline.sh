#!/usr/bin/env bash
# English: Execute the local evidence pipeline with explicit model provenance and final gates.
# 中文：显式声明模型使用后执行本地证据流程并核验最终门槛；报告成功生成不等于材料充分或厂家已确认。
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  printf 'Usage: %s CASE_ROOT SOURCE_PATH [PRIMARY_IMAGE]\n' "$0" >&2
  exit 2
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
FACTORYTRACE="$TOOLKIT_ROOT/.venv/bin/factorytrace"
CASE_ROOT="$1"
SOURCE_PATH="$2"
PRIMARY_IMAGE="${3:-}"
MODEL_MODE="${FACTORYTRACE_MODEL_MODE:-}"
MODEL_ID="${FACTORYTRACE_MODEL_ID:-}"

if [[ ! -x "$FACTORYTRACE" ]]; then
  printf 'Run scripts/bootstrap.sh first.\n' >&2
  exit 1
fi
if [[ -z "$MODEL_MODE" ]]; then
  printf 'Set FACTORYTRACE_MODEL_MODE=none|cloud|local|hybrid first.\n' >&2
  exit 2
fi
case "$MODEL_MODE" in
  none|cloud|local|hybrid) ;;
  *)
    printf 'Invalid FACTORYTRACE_MODEL_MODE: %s\n' "$MODEL_MODE" >&2
    exit 2
    ;;
esac

DOCTOR_ARGS=(doctor --case-root "$CASE_ROOT" --model-mode "$MODEL_MODE")
if [[ -n "$MODEL_ID" ]]; then
  DOCTOR_ARGS+=(--model-id "$MODEL_ID")
fi
"$FACTORYTRACE" "${DOCTOR_ARGS[@]}"

"$FACTORYTRACE" ingest "$SOURCE_PATH" --recursive --case-root "$CASE_ROOT" --workers 8

if [[ -n "$PRIMARY_IMAGE" ]]; then
  "$FACTORYTRACE" variants "$PRIMARY_IMAGE" \
    --case-root "$CASE_ROOT" \
    --crop-plan "$CASE_ROOT/work/crop_plan.json"
fi

"$FACTORYTRACE" queries \
  --profile "$CASE_ROOT/work/product_profile.json" \
  --case-root "$CASE_ROOT"

"$FACTORYTRACE" ledger --case-root "$CASE_ROOT"
"$FACTORYTRACE" validate --case-root "$CASE_ROOT"
"$FACTORYTRACE" assess --case-root "$CASE_ROOT"
"$FACTORYTRACE" hypotheses --case-root "$CASE_ROOT"
"$FACTORYTRACE" report \
  --case-root "$CASE_ROOT" \
  --format md,json,csv,xlsx,docx
"$FACTORYTRACE" lint-report --case-root "$CASE_ROOT"
"$FACTORYTRACE" audit --case-root "$CASE_ROOT" --stage research

set +e
"$FACTORYTRACE" materials --case-root "$CASE_ROOT" --stage discovery
MATERIALS_EXIT=$?
"$FACTORYTRACE" audit --case-root "$CASE_ROOT" --stage operational
OPERATIONAL_EXIT=$?
set -e
if [[ "$MATERIALS_EXIT" -ne 0 || "$OPERATIONAL_EXIT" -ne 0 ]]; then
  printf 'Evidence gate incomplete: materials exit=%s; operational audit exit=%s. Reports are leads only.\n' \
    "$MATERIALS_EXIT" "$OPERATIONAL_EXIT" >&2
  exit 3
fi
