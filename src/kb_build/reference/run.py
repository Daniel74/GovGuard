"""Writes data/input/cfn_properties.json from a folder of `describe-type` schemas (see README)."""

import json
from pathlib import Path

from kb_build.build_inputs import read_scope
from kb_build.paths import BuildPaths
from kb_build.reference.cfn_properties import build_snapshot


def write_snapshot(schema_dir: Path, types: frozenset[str], out_file: Path) -> None:
    """Fail closed: a type of the scope without schema would silently skip its check."""
    schemas = {}
    for file in sorted(schema_dir.glob("*.json")):
        text = file.read_text(encoding="utf-8")
        type_name = json.loads(text)["typeName"]
        if type_name in types:
            schemas[type_name] = text
    missing = sorted(types - schemas.keys())
    if missing:
        raise ValueError(f"no schema for scope types: {missing}")
    snapshot = build_snapshot(schemas)
    out_file.write_text(json.dumps(snapshot, indent=1) + "\n", encoding="utf-8")


def snapshot_scope(schema_dir: Path, paths: BuildPaths = BuildPaths()) -> None:
    """`python -m kb_build cfn-properties`: every type of the scope."""
    write_snapshot(schema_dir, read_scope(paths.scope).types, paths.cfn_properties)
