#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Run as root" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
source /etc/os-release

case "$ID" in
  ubuntu)
    docker_repo="https://download.docker.com/linux/ubuntu"
    ;;
  debian)
    docker_repo="https://download.docker.com/linux/debian"
    ;;
  *)
    echo "Unsupported OS: $ID" >&2
    exit 1
    ;;
esac

apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release git rsync ufw
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/${ID}/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

cat > /etc/apt/sources.list.d/docker.list <<EOF
deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] $docker_repo $VERSION_CODENAME stable
EOF

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker

if ! id -u deploy >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash deploy
fi
usermod -aG docker deploy
mkdir -p /opt/aion-os /opt/aion-os/deploy
chown -R deploy:deploy /opt/aion-os

ufw allow OpenSSH || true
ufw allow 80/tcp || true
ufw allow 443/tcp || true
ufw --force enable || true

echo "Server prepared. Copy the repository into /opt/aion-os and run docker compose -f deploy/docker-compose.prod.yml up -d"
