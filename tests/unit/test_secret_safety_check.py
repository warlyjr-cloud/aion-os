from __future__ import annotations

from pathlib import Path

import pytest

import scripts.secret_safety_check as secret_safety_check
from scripts.secret_safety_check import scan


def test_scan_ignores_vendored_dependency_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dependency cache/venv is not our source. Found live in CI: the
    scanner recursed into .venv/.uv-cache with no exclusion, flagging
    real third-party code (e.g. `token: "..."` in pygments' color
    schemes, `api_key: str = "..."` type annotations in anthropic's own
    credential types) as leaked secrets and failing every clean CI run."""
    monkeypatch.setattr(secret_safety_check, "ROOT", tmp_path)

    venv_dir = tmp_path / ".venv" / "site-packages"
    venv_dir.mkdir(parents=True)
    (venv_dir / "vendored.py").write_text('api_key: str = "sk-not-a-real-secret-value"\n')

    cache_dir = tmp_path / ".uv-cache" / "pkg"
    cache_dir.mkdir(parents=True)
    (cache_dir / "vendored.py").write_text('token = "abcd1234efgh5678"\n')

    assert scan(tmp_path) == []


def test_scan_still_flags_secrets_in_our_own_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(secret_safety_check, "ROOT", tmp_path)
    (tmp_path / "leak.py").write_text('password = "hunter22"\n')

    findings = scan(tmp_path)

    assert findings == ["leak.py"]
