# AION OS

> Verifiable evolution for system configuration: intelligence proposes, a deterministic gate authorizes.

AION OS is a research and engineering project exploring governed, auditable autonomous mutation of system configuration. A model proposes a change; it only ever executes after passing two independent review gates (an LLM council and a non-LLM deterministic verifier), typed capability checks, and a hash-chained audit trail — with real rollback on failure. The repository is structured to support a local MVP workflow, reproducible bootstrap, and production-grade containerization.

## What is available today
- A functional local Python CLI and daemon entrypoint.
- A production-ready FastAPI dashboard with health, readiness, status, and metrics endpoints.
- A basic control-plane command (`aionctl status`) for inspecting local state.
- A deterministic runtime smoke path for local validation.
- A testable state-machine/TCB layer, two independent review gates, and a durable capability store in `src/`.

**See `docs/PROJECT_STATUS.md` for an honest, component-by-component
breakdown of what's proven real (with evidence) vs. functional scaffold
vs. stub/vision** — and `docs/PROOF_OF_REAL_EXECUTION.md` for the first
end-to-end, non-simulated build/promote/rollback cycle. A concrete
proposed product focus is in `docs/VERTICAL_USE_CASE.md`.

## Quick start

### 1. Bootstrap the environment
```bash
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

### 2. Launch the investor dashboard locally
```bash
docker compose up --build
```

The dashboard will be available at http://localhost:8000 with health checks and status endpoints at:
- `/healthz`
- `/readyz`
- `/api/status`
- `/metrics`

### 3. Run the daemon once
```bash
python -m src.cli start --once
```

### 4. Check the local health status
```bash
aionctl status
# or
python scripts/health_check.py
```

### 5. Run the validation suite
```bash
python -m pytest -q
python scripts/smoke_check.py
python scripts/verify_readme.py
python scripts/verify_public_release.py
```

For an investor-oriented end-to-end verification, run:
```bash
aion-verify-public
```

To validate that the public repository does not contain obvious hardcoded secrets, run:
```bash
aion-secret-scan
```

For deployment-oriented validation, run:
```bash
aion-verify-deployment
```

## Production deployment options
- Local demo: `docker compose up --build`
- Remote demo stack: `docker compose -f deploy/docker-compose.prod.yml up --build`
- Remote server deployment: `powershell.exe -NoProfile -File scripts/deploy.ps1 -RemoteHost root@your-server -RemotePath /opt/aion-os`
- GitHub Container Registry publication and remote deployment via `.github/workflows/deploy.yml`
- Server bootstrap for Ubuntu/Debian: `sudo bash scripts/prepare-server.sh`

## Repository map
- `src/` — Python runtime, daemon, governance, mutation, TCB, and proof modules.
- `src/dashboard/` — FastAPI dashboard and operational views.
- `tests/` — unit, integration, security, and runtime-interface coverage.
- `scripts/` — bootstrap, smoke, and health-check helpers.

## Current maturity
This is a functional prototype with two real, executed action types
(`package.propose` via `nix build`, `dependency.bump` via `uv`), a full
CI pipeline (lint, type check, tests, secret scanning, SBOM), and one
real dogfooding pilot against this repository. It is not a distributed
OS, a P2P network, or a hardware/kernel product — see
`docs/PROJECT_STATUS.md` for exactly what's proven vs. scaffold.

## Next milestones
- A third real executor action type, exercised against something other
  than this repository.
- An external user driving a mutation end to end without the maintainer
  in the loop.
- Expand end-to-end governance and proof workflows.

## License
AION OS is released under the Business Source License 1.1 (BSL). See `LICENSE` for details.
