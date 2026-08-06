# Deployment scaffold

This directory contains deployment-oriented scaffolding for running AION OS in a containerized environment with an investor-facing dashboard and a production-grade reverse proxy.

## Files
- `docker-compose.prod.yml` — production-style container compose definition with the dashboard and Caddy front-end.
- `Caddyfile` — HTTPS-capable reverse proxy configuration for the dashboard service.
- `.env.example` — environment template used by the container and deployment scripts.

## Usage
1. Copy `.env.example` to `.env` and fill the required values.
2. Set `DOMAIN` to your real domain (for example `demo.aionos.dev`).
3. Run `docker compose -f deploy/docker-compose.prod.yml up --build`.
4. Open `https://<your-domain>/` to reach the public dashboard surface.

## Remote deployment
The repository includes a PowerShell deployment helper at `scripts/deploy.ps1` for shipping the stack to a remote Linux host over SSH and rsync.

Example:
```powershell
powershell.exe -NoProfile -File scripts/deploy.ps1 -RemoteHost root@your-server -RemotePath /opt/aion-os
```

For automated deployments from GitHub Actions, configure these repository secrets:
- `REMOTE_HOST`
- `REMOTE_USER`
- `REMOTE_SSH_PRIVATE_KEY`
- `REMOTE_PATH` (optional; defaults to `/opt/aion-os`)
- `DOMAIN`

Before the first deployment, prepare the server with:
```bash
sudo bash scripts/prepare-server.sh
```

## Container publishing
The repository includes `.github/workflows/deploy.yml`, which builds and pushes the dashboard image to GitHub Container Registry and deploys it to the remote host when the required secrets are configured.
