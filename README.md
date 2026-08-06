# AION OS

> The decentralized bare-metal autonomous infrastructure stack.

AION OS is an ambitious research and engineering project that combines a Rust microkernel scaffold, a Python control plane, and a set of governance and mutation primitives for autonomous infrastructure. The repository is now structured to support a local MVP workflow, reproducible bootstrap, and basic investor-facing validation.

## What is available today
- A functional local Python CLI and daemon entrypoint.
- A basic control-plane command (`aionctl status`) for inspecting local state.
- A deterministic runtime smoke path for local validation.
- A Rust kernel scaffold under `kernel/` and a testable state-machine/TCB layer in `src/`.

## Quick start

### 1. Bootstrap the environment
```bash
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

### 2. Run the daemon once
```bash
python -m src.cli start --once
```

### 3. Check the local health status
```bash
aionctl status
# or
python scripts/health_check.py
```

### 4. Run the validation suite
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

If you prefer a containerized check, run:
```bash
docker compose up --build
```

For deployment-oriented validation, run:
```bash
aion-verify-deployment
```

## Repository map
- `kernel/` — Rust microkernel scaffold and target configuration.
- `src/` — Python runtime, daemon, governance, mutation, TCB, and proof modules.
- `tests/` — unit, integration, security, and runtime-interface coverage.
- `scripts/` — bootstrap, smoke, and health-check helpers.

## Current maturity
This is best described as a functional prototype with a credible engineering skeleton. It is no longer just a collection of ideas: the local CLI/daemon flow, control plane, and smoke tests are now runnable in a standard development environment.

## Next milestones
- Harden the Rust kernel build path and hardware-facing abstractions.
- Expand end-to-end governance and proof workflows.
- Add richer observability, deployment automation, and investor demo tooling.

## Documentation
For the broader vision and architecture background, see:
- [AION_WHITEPAPER.md](AION_WHITEPAPER.md)
- [INVESTOR_PITCH.md](INVESTOR_PITCH.md)

## License
AION OS is released under the Business Source License 1.1 (BSL). See `LICENSE` for details.
