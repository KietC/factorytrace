#!/usr/bin/env bash
# English: Reuse installed tools or install them via the detected OS package manager.
# 中文：复用现有工具，缺失时通过系统包管理器安装并检查可执行文件；Linux 可能需要 sudo，macOS 需预先安装 Homebrew。
set -euo pipefail

missing=()
for tool in ffmpeg tesseract exiftool; do
  command -v "$tool" >/dev/null 2>&1 || missing+=("$tool")
done

if [[ ${#missing[@]} -eq 0 ]]; then
  printf 'Media tools ready: ffmpeg, tesseract, exiftool\n'
  exit 0
fi

run_privileged() {
  if [[ "$(id -u)" == "0" ]]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    printf 'Root privileges or sudo are required to install: %s\n' "${missing[*]}" >&2
    exit 1
  fi
}

case "$(uname -s)" in
  Darwin)
    if ! command -v brew >/dev/null 2>&1; then
      printf 'Homebrew is required; install ffmpeg, tesseract and exiftool, then rerun.\n' >&2
      exit 1
    fi
    brew install ffmpeg tesseract exiftool
    ;;
  Linux)
    if command -v apt-get >/dev/null 2>&1; then
      run_privileged apt-get update
      run_privileged apt-get install -y ffmpeg tesseract-ocr libimage-exiftool-perl
    elif command -v dnf >/dev/null 2>&1; then
      run_privileged dnf install -y ffmpeg tesseract perl-Image-ExifTool
    elif command -v pacman >/dev/null 2>&1; then
      run_privileged pacman -S --needed --noconfirm ffmpeg tesseract tesseract-data-eng perl-image-exiftool
    else
      printf 'Unsupported package manager; install ffmpeg, tesseract and exiftool manually.\n' >&2
      exit 1
    fi
    ;;
  *)
    printf 'Unsupported OS for automatic media-tool installation.\n' >&2
    exit 1
    ;;
esac

for tool in ffmpeg tesseract exiftool; do
  command -v "$tool" >/dev/null 2>&1 || {
    printf 'Installation verification failed: %s not found\n' "$tool" >&2
    exit 1
  }
done
ffmpeg -version >/dev/null
tesseract --version >/dev/null
exiftool -ver >/dev/null
printf 'Media tools ready: ffmpeg, tesseract, exiftool\n'
