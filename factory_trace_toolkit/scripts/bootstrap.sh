#!/usr/bin/env bash
# English: Bootstrap a supported Python venv; full mode installs and verifies media tools.
# 中文：建立受支持的 Python 环境；完整模式安装并验证媒体工具，脚本遇错停止，不自动删除旧虚拟环境。
set -euo pipefail
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$TOOLKIT_ROOT/.venv"
FLEXIBLE="${FACTORYTRACE_FLEXIBLE:-0}"
CORE_ONLY=0

for argument in "$@"; do
  case "$argument" in
    --flexible) FLEXIBLE=1 ;;
    --core-only) CORE_ONLY=1 ;;
    *) printf 'Usage: %s [--flexible] [--core-only]\n' "$0" >&2; exit 2 ;;
  esac
done

PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -c 'import sys; assert (3, 11) <= sys.version_info < (3, 15), sys.version'

if [[ ! -d "$VENV_PATH" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_PATH"
fi
if ! "$VENV_PATH/bin/python" -c 'import sys; assert (3, 11) <= sys.version_info < (3, 15), sys.version'; then
  printf 'Existing .venv uses an unsupported Python; recreate it with Python 3.11-3.14.\n' >&2
  exit 1
fi

"$VENV_PATH/bin/python" -m pip install --upgrade \
  'pip==26.1.2' 'setuptools==83.0.0'
INSTALL_TARGET="$TOOLKIT_ROOT"
if [[ "$CORE_ONLY" != "1" ]]; then
  INSTALL_TARGET="$TOOLKIT_ROOT[full]"
fi

if [[ "$FLEXIBLE" == "1" ]]; then
  "$VENV_PATH/bin/python" -m pip install -e "$INSTALL_TARGET"
else
  "$VENV_PATH/bin/python" -m pip install \
    --constraint "$TOOLKIT_ROOT/constraints-tested.txt" \
    -e "$INSTALL_TARGET"
fi
"$VENV_PATH/bin/python" -m factorytrace --help
if [[ "$CORE_ONLY" != "1" ]]; then
  bash "$SCRIPT_DIR/install_media_tools.sh"
  "$VENV_PATH/bin/python" "$SCRIPT_DIR/capability_smoke.py" \
    --output "$TOOLKIT_ROOT/output/dependency_capability_smoke.json"
fi
"$VENV_PATH/bin/python" -m factorytrace doctor \
  --output "$TOOLKIT_ROOT/environment.current.json" \
  --model-mode undeclared
printf 'Ready: %s\n' "$VENV_PATH/bin/python"
