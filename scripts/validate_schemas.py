from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, cast

from jsonschema.validators import validator_for


class RepositorySchemaError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RepositorySchemaError(f"expected an object: {path}")
    return cast(dict[str, Any], value)


def _validate(instance_path: Path, schema_path: Path) -> None:
    schema = _load(schema_path)
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    errors = sorted(
        validator_class(schema).iter_errors(_load(instance_path)),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        details = "; ".join(
            f"{'/'.join(str(item) for item in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors
        )
        raise RepositorySchemaError(f"{instance_path}: {details}")


def validate_repository(root: Path) -> int:
    schema_paths = sorted((root / "schemas").glob("*.json")) + sorted(
        (root / "benchmarks" / "os_evobench" / "schema").glob("*.json")
    )
    for schema_path in schema_paths:
        schema = _load(schema_path)
        validator_for(schema).check_schema(schema)

    mappings = (
        (
            root / "capabilities" / "registry.json",
            root / "schemas" / "capability-registry.schema.json",
        ),
        (root / "policies" / "base-policy.json", root / "schemas" / "policy-set.schema.json"),
        (root / "tools" / "plugin-lock.json", root / "schemas" / "plugin-lock.schema.json"),
        (root / "tools" / "toolchain-lock.json", root / "schemas" / "toolchain-lock.schema.json"),
    )
    validated = len(schema_paths)
    for instance_path, schema_path in mappings:
        _validate(instance_path, schema_path)
        validated += 1
    intent_schema = root / "schemas" / "intent-contract.schema.json"
    for intent_path in sorted((root / "proofs").glob("mut-*/intent-contract.json")):
        _validate(intent_path, intent_schema)
        validated += 1
    return validated


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        validated = validate_repository(root)
    except (json.JSONDecodeError, RepositorySchemaError) as exc:
        print(f"schema validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"validated {validated} schemas and instances")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
