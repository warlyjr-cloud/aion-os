.PHONY: bootstrap test smoke health lint verify-public

bootstrap:
	python -m pip install --upgrade pip
	python -m pip install -e '.[dev]'

test:
	python -m pytest -q

smoke:
	python scripts/smoke_check.py

health:
	python scripts/health_check.py

verify-public:
	python scripts/verify_public_release.py

lint:
	ruff check src tests scripts
