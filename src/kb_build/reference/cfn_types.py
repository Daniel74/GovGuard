"""Real CloudFormation resource types: the LLM must not invent type names (SPEC)."""

import json
from functools import cache
from pathlib import Path

from kb_build.paths import BuildPaths


@cache
def load_cfn_types(path: Path = BuildPaths().cfn_types) -> frozenset[str]:
    return frozenset(json.loads(path.read_text(encoding="utf-8")))
