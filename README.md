# AION OS

> The decentralized bare-metal autonomous infrastructure stack.

AION OS is an ambitious research and engineering project that combines a Rust microkernel scaffold, a Python control plane, and a set of governance and mutation primitives for autonomous infrastructure. The repository is now structured to support a local MVP workflow, reproducible bootstrap, production-grade containerization, and investor-facing validation.

## What is available today
- A functional local Python CLI and daemon entrypoint.
- A production-ready FastAPI dashboard with health, readiness, status, and metrics endpoints.
- A basic control-plane command (`aionctl status`) for inspecting local state.
- A deterministic runtime smoke path for local validation.
- A Rust kernel scaffold under `kernel/` and a testable state-machine/TCB layer in `src/`.

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
- `kernel/` — Rust microkernel scaffold and target configuration.
- `src/` — Python runtime, daemon, governance, mutation, TCB, and proof modules.
- `src/dashboard/` — investor-facing FastAPI dashboard and operational views.
- `tests/` — unit, integration, security, and runtime-interface coverage.
- `scripts/` — bootstrap, smoke, and health-check helpers.

## Current maturity
This is best described as a functional prototype with a credible engineering skeleton and an investor-ready operational surface. The local CLI/daemon flow, control plane, smoke tests, health endpoints, container workflow, and deployment scaffolding are now runnable in a standard development environment.

## Next milestones
- Harden the Rust kernel build path and hardware-facing abstractions.
- Expand end-to-end governance and proof workflows.
- Add richer observability, identity, and multi-region deployment automation.

## Documentation
For the broader vision and architecture background, see:
- [AION_WHITEPAPER.md](AION_WHITEPAPER.md)
- [INVESTOR_PITCH.md](INVESTOR_PITCH.md)

## License
AION OS is released under the Business Source License 1.1 (BSL). See `LICENSE` for details.
