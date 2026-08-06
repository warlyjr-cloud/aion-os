FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY tests ./tests
COPY scripts ./scripts
COPY kernel ./kernel
COPY pytest.ini ./pytest.ini
COPY .env.example ./.env.example

RUN python -m pip install --upgrade pip && python -m pip install -e '.[dev]'

CMD ["python", "scripts/verify_deployment.py"]
