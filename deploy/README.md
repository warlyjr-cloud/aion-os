# Deployment scaffold

This directory contains deployment-oriented scaffolding for running AION OS in a containerized environment.

## Files
- `docker-compose.prod.yml` — production-style container compose definition.
- `.env.example` — environment template used by the container and deployment scripts.

## Usage
1. Copy `.env.example` to `.env` and fill the required values.
2. Run `docker compose -f deploy/docker-compose.prod.yml up --build`.
