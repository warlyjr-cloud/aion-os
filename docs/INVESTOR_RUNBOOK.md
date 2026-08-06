# Investor runbook

This runbook is intended for reviewers, partners, and investors who want to validate the current AION OS MVP locally.

## 1. Prerequisites
- Python 3.12+
- Internet access only to install dependencies from PyPI

## 2. Local validation
```bash
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python scripts/verify_public_release.py
```

Expected outcome:
- The verification script prints a JSON payload with `status: "ok"`.
- The CLI daemon run completes in simulation mode.
- The health check reports the local service as ready.

## 3. Docker validation
```bash
docker compose up --build
```

Expected outcome:
- The container runs the same public verification flow and exits successfully.

## 4. What the verification covers
- Unit and integration tests
- README workflow smoke checks
- CLI daemon startup in simulation mode
- Health status reporting

## 5. Limits of the current MVP
The current repository is a credible prototype rather than a hardened production operating system. The validation focuses on reproducibility, local execution, and investor-facing proof that the project can be exercised end to end.
