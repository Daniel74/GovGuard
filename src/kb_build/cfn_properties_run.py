"""Writes data/cfn_properties.json from a folder of `describe-type` schemas (see README)."""

import json
import sys
from pathlib import Path

from kb_build.cfn_properties import CFN_PROPERTIES_FILE, build_snapshot
from kb_build.scope import Scope


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


if __name__ == "__main__":
    scope = Scope(json.loads(Path("data/scope.json").read_text(encoding="utf-8")))
    write_snapshot(Path(sys.argv[1]), scope.types, CFN_PROPERTIES_FILE)
