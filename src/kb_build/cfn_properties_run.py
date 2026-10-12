"""Writes data/cfn_properties.json from a folder of `describe-type` schemas (see README)."""

import json
from pathlib import Path

from kb_build.cfn_properties import CFN_PROPERTIES_FILE, build_snapshot
from kb_build.selection_run import read_scope


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


def snapshot_scope(schema_dir: Path, data: Path = Path("data")) -> None:
    """`python -m kb_build cfn-properties`: every type of data/scope.json."""
    write_snapshot(schema_dir, read_scope(data).types, data / CFN_PROPERTIES_FILE.name)
