# AION contributor instructions

## Scope

These instructions apply to the entire repository and complement the user's global instructions.

## Safety invariants

- Treat `docs/SAFETY_CONSTITUTION.md`, `docs/TCB_SPECIFICATION.md`, `src/tcb/`, `policies/`, audit code, rollback code, and security workflows as protected.
- Never execute model-produced free-form shell on the host.
- Keep all runtime actions typed, capability-scoped, auditable, time-bounded, and reversible.
- The default runtime is simulation-only. Host mutation requires a separate, explicit human approval path.
- Do not weaken tests, policies, audit logging, sandboxing, emergency stop, or rollback to make a candidate pass.
- Do not read `.env` files or add secrets to code, fixtures, logs, proofs, or commits.

## Engineering

- Python code, identifiers, docstrings, and commit messages are in English.
- Use Python 3.12 semantics and keep compatibility with newer supported Python releases.
- Prefer small deterministic modules with explicit error handling.
- Add or update tests for behavior changes. Run `python -m pytest`, `ruff check .`, and `pyright` when available.
- Do not claim Nix, VM, container, or security-tool validation unless the corresponding command ran successfully.

## Changes and review

- Never commit or push unless the user explicitly requests it.
- Never force-push or rewrite history.
- A mutation producer cannot be its sole verifier.
- Changes to protected files require explicit human review and must be called out in the handoff.
