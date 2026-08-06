#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest -q tests/unit/test_state_machine.py tests/unit/test_runtime_interfaces.py
