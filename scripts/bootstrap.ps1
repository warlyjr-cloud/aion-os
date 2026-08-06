$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m pytest -q tests/unit/test_state_machine.py tests/unit/test_runtime_interfaces.py
