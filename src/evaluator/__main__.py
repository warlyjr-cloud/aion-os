"""Run the deterministic baseline with ``python -m evaluator``."""

from __future__ import annotations

import argparse
from pathlib import Path

from evaluator.runner import EvoBenchRunner


def main() -> int:
    parser = argparse.ArgumentParser(description="Run AION OS-EvoBench offline")
    parser.add_argument("--benchmark-root", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    arguments = parser.parse_args()

    runner = EvoBenchRunner(arguments.benchmark_root)
    report = runner.run_baseline()
    if arguments.output is None:
        print(report.to_json(), end="")
    else:
        runner.write_report(report, arguments.output)
        print(arguments.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
