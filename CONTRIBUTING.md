# Contributing to AION OS

## How to contribute
1. Fork the repository.
2. Create a feature branch.
3. Make the change, add or update tests, and run the validation suite:
   ```bash
   uv sync --extra dev
   uv run pytest
   uv run ruff check .
   uv run pyright
   ```
4. Push to the branch and open a Pull Request. The PR template asks for
   evidence (what you actually ran and its output), not just a claim.

## Code standards
- Python, typed, `pyright`-clean, `ruff`-clean.
- No new dependency without calling it out in the PR description.
- Real capability changes need a matching test. See
  `docs/PROJECT_STATUS.md` before claiming something works — "the code
  was written" and "it runs and was verified" are different bars.

## Safety invariants
See `AGENTS.md` and `docs/SAFETY_CONSTITUTION.md`. In short: intelligence
proposes, only the deterministic TCB authorizes; no model-produced
free-form shell execution on the host; every action is typed,
capability-scoped, time-bounded, auditable, and reversible. Changes to
`src/tcb/`, `policies/`, audit, rollback, or security workflows need
human review.
