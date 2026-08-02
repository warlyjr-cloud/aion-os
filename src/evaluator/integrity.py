"""Hash-based immutability checks around every benchmark evaluation."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


class BenchmarkIntegrityError(RuntimeError):
    """Raised when evaluator-owned benchmark assets changed."""


_PROTECTED_DIRECTORIES = ("public", "reserved", "fixtures", "baselines", "schema")


def _protected_files(root: Path) -> tuple[Path, ...]:
    files: list[Path] = []
    for directory_name in _PROTECTED_DIRECTORIES:
        directory = root / directory_name
        if directory.is_dir():
            files.extend(path for path in directory.rglob("*") if path.is_file())
    return tuple(sorted(files, key=lambda path: path.relative_to(root).as_posix()))


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class BenchmarkIntegrityGuard:
    root: Path
    hashes: dict[str, str]
    suite_digest: str

    @classmethod
    def capture(cls, root: Path) -> BenchmarkIntegrityGuard:
        resolved_root = root.resolve()
        hashes = {
            path.relative_to(resolved_root).as_posix(): _hash_file(path)
            for path in _protected_files(resolved_root)
        }
        if not hashes:
            raise BenchmarkIntegrityError("benchmark contains no protected assets")
        canonical = "\n".join(f"{name}:{value}" for name, value in sorted(hashes.items()))
        suite_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return cls(resolved_root, hashes, suite_digest)

    def verify(self) -> None:
        current = {
            path.relative_to(self.root).as_posix(): _hash_file(path)
            for path in _protected_files(self.root)
        }
        if current != self.hashes:
            changed = sorted(set(current) | set(self.hashes))
            changed = [name for name in changed if current.get(name) != self.hashes.get(name)]
            raise BenchmarkIntegrityError(
                "benchmark assets changed during evaluation: " + ", ".join(changed)
            )
