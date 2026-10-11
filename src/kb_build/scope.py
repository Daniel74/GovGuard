"""The Prüfumfang (ADR 0011): hand-maintained AWS services of the architecture audit."""

import json
from pathlib import Path

SCOPE_FILE = Path("data/scope.json")  # service name -> CloudFormation resource types


def load_scope(path: Path = SCOPE_FILE) -> dict[str, list[str]]:
    return json.loads(path.read_text(encoding="utf-8"))


def scope_types(path: Path = SCOPE_FILE) -> frozenset[str]:
    return frozenset(t for types in load_scope(path).values() for t in types)
