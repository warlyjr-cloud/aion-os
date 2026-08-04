#!/usr/bin/env bash
set -e

echo "==========================================="
echo " AION OS - Construindo Microkernel Rust "
echo "==========================================="

cd kernel

echo "[*] Compilando para x86_64 Bare Metal..."
cargo build --target x86_64-aion.json --release

echo "[*] Compilando para ARM64 (aarch64) Bare Metal..."
cargo build --target aarch64-aion.json --release

echo "==========================================="
echo " SUCCESSO! Kernel binários gerados em kernel/target/"
echo " Para testar (QEMU x86_64), você precisaria rodar:"
echo " qemu-system-x86_64 -kernel target/x86_64-aion/release/aion_kernel"
echo " (Nota: isso requer que o binário seja convertido para um arquivo ELF multiboot futuramente)"
echo "==========================================="
