# Deployment runbook

This runbook provides the minimum operational steps needed to build and validate the AION OS runtime in a deployment-oriented environment.

## 1. Prepare the environment
1. Copy `.env.example` to `.env`.
2. Fill in the runtime values you plan to use for the target environment.
3. Keep privileged secrets in a secret manager, not in the repository.

## 2. Build and validate locally
```bash
python -m pip install -e '.[dev]'
aion-verify-deployment
```

## 3. Run in a container
```bash
docker compose -f deploy/docker-compose.prod.yml up --build
```

## 4. Production expectations
- The container should run the deployment validation workflow successfully.
- The runtime must be configured through environment variables.
- Real secrets should be injected through an external secret manager or deployment platform.
