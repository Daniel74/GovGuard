"""Real CloudFormation resource types: the LLM must not invent type names (SPEC)."""

import json
from functools import cache
from pathlib import Path

CFN_TYPES_FILE = Path("data/cfn_resource_types.json")  # aws cloudformation list-types, AWS_TYPES


@cache
def load_cfn_types(path: Path = CFN_TYPES_FILE) -> frozenset[str]:
    return frozenset(json.loads(path.read_text(encoding="utf-8")))
