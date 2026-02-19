#!/usr/bin/env bash
set -euo pipefail
export PYTHONIOENCODING=utf-8

if [[ ! -x ".venv/Scripts/python.exe" ]]; then
  echo "Missing .venv/Scripts/python.exe"
  exit 1
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: ./agents/instructions/model_agnostic/activate_kernel.sh LITE|STANDARD|FULL"
  exit 1
fi

".venv/Scripts/python.exe" agents/tools/activate_kernel.py --profile "$1"
