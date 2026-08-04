# Project: AION OS

## Architecture
- **Microkernel Subsystem (`kernel/src/`)**: Rust `#![no_std]` bare-metal kernel enforcing hardware attestation (TPM 2.0), post-quantum lattice cryptography (`pqc.rs`), zero-knowledge proof driver verification (`zkp.rs`), and DePIN node hardware cycle metering (`depin.rs`).
- **Distributed Intelligence Engine (`src/`)**: Python P2P gossip mesh (`src/grid/p2p.py`), quantum-relativistic evolutionary mutator (`src/evolution/schrodinger.py`), model council governance (`src/model_council/`), and local TCB capabilities (`src/tcb/`).
- **Documentation & Strategic Layer**: `README.md`, `AION_WHITEPAPER.md`, `INVESTOR_PITCH.md`, and specifications in `docs/`.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | R1 Security Audit Verification | Verify zero central routing, "Oracle", or "Fleet Manager" leaks exist in `src/`, `kernel/`, `docs/` | M1 | survey |
| 2 | R2 Commercial MVP Disclaimer | Insert corporate commercial MVP disclaimer into `README.md` (top) and `AION_WHITEPAPER.md` (intro) | M2 | survey |
| 3 | R3 Investor Pitch Document | Author `INVESTOR_PITCH.md` detailing 2 DeepTech architectural features aligned with AION Labs ecosystem | M3 | survey |
| 4 | Final Gate & Forensic Audit | Verification by Reviewers, Challengers, and Forensic Auditor (`teamwork_preview_auditor`) | M4 | survey |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Security Audit Verification (R1) | Compile audit verification report for R1 | none | IN_PROGRESS |
| 2 | M2: Commercial MVP Disclaimer (R2) | Implement disclaimer in `README.md` & `AION_WHITEPAPER.md` | none | PLANNED |
| 3 | M3: Investor Pitch Creation (R3) | Create `INVESTOR_PITCH.md` | none | PLANNED |
| 4 | M4: Final Gate & Audit | Run Reviewers, Challengers, and Forensic Auditor | M1, M2, M3 | PLANNED |

## Interface Contracts
- `README.md`: Position Commercial MVP Disclaimer directly after `![AION Grid](docs/images/grid.jpg)` banner (between lines 5 and 7).
- `AION_WHITEPAPER.md`: Position Commercial MVP Disclaimer inside `## 1. Introduction` directly after the first intro paragraph (after line 9).
- `INVESTOR_PITCH.md`: Markdown document detailing Proposal 1 (AION Orbital-Mesh & Gravitational Relativistic Synchronization) and Proposal 2 (Photonic-Neuromorphic Kernel & Landauer Thermodynamic Accounting).

## Code Layout
- `README.md` — Project root README
- `AION_WHITEPAPER.md` — Architectural Whitepaper
- `INVESTOR_PITCH.md` — DeepTech Investor Pitch
- `src/` — Python distributed intelligence subsystems
- `kernel/` — Rust `#![no_std]` microkernel
- `docs/` — Specifications and documentation
