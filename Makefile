.PHONY: bootstrap test smoke health lint verify-public dashboard deploy-prod deploy-prod-logs

bootstrap:
	python -m pip install --upgrade pip
	python -m pip install -e '.[dev]'

test:
	python -m pytest -q

smoke:
	python scripts/smoke_check.py

health:
	python scripts/health_check.py

dashboard:
	python -m src.dashboard

deploy-prod:
	powershell.exe -NoProfile -File scripts/deploy.ps1

deploy-prod-logs:
	powershell.exe -NoProfile -File scripts/deploy.ps1 -Logs

verify-public:
	python scripts/verify_public_release.py

lint:
	ruff check src tests scripts
