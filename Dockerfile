FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    AION_PROJECT_ROOT=/app \
    AION_RUNTIME_MODE=simulation \
    AION_ALLOW_HOST_MUTATION=0 \
    AION_DASHBOARD_HOST=0.0.0.0 \
    AION_DASHBOARD_PORT=8000

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY tests ./tests
COPY scripts ./scripts
COPY pytest.ini ./pytest.ini
COPY .env.example ./.env.example

RUN python -m pip install --upgrade pip && python -m pip install -e '.[dev]'

RUN mkdir -p /app/.aion-state && chown -R app:app /app

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=5).read()" || exit 1

CMD ["python", "-m", "src.dashboard"]
