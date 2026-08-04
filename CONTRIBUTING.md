# Contributing to AION OS

We welcome contributions to the open-source components of AION OS (The Rust Microkernel and the Python AI Daemon).

## How to Contribute
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/quantum-fs-upgrade`).
3. Commit your changes ensuring mathematical correctness and zero-knowledge compliance.
4. Push to the branch and open a Pull Request.

## Code Standards
- **Rust (Kernel)**: All code must compile under `#![no_std]`. Usage of `unsafe` blocks must be rigorously documented with mathematical proofs of memory safety.
- **Python (Daemon)**: Code must be typed (`mypy` compliant) and support AST metamorphism natively.

## Enterprise Components
Please note that the Fleet Manager, Oracle Router, and Enterprise ZKP Prover are closed-source components owned by AION Labs and are not subject to public contributions.
