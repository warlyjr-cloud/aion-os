#!/usr/bin/env bash
set -e

echo "==========================================="
echo " AION OS - Construindo Alpha ISO Image "
echo "==========================================="

# Verifica dependencias
if ! command -v nix &> /dev/null; then
    echo "Nix is not installed. Por favor instale o Nix via Determinate Systems."
    exit 1
fi

PROJECT_ROOT=$(pwd)
echo "Project Root: $PROJECT_ROOT"

# Prepara a ISO via flakes
echo "Executando flake build para aion-iso..."
nix build .#nixosConfigurations.aion-iso.config.system.build.isoImage --print-build-logs

# Copia o artefato gerado para o root
echo "Copiando a imagem gerada..."
cp result/iso/*.iso aion-os-alpha1.iso
chmod 644 aion-os-alpha1.iso

echo "==========================================="
echo " SUCCESSO! Imagem ISO gerada: aion-os-alpha1.iso "
echo "==========================================="
