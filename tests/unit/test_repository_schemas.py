from pathlib import Path

from scripts.validate_schemas import validate_repository


def test_repository_schemas_and_instances_are_valid() -> None:
    root = Path(__file__).resolve().parents[2]
    assert validate_repository(root) >= 19
