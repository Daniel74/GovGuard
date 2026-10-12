"""Real CloudFormation properties per type: the LLM must not invent them (#17). Pure code."""

import json
import re
from functools import cache
from pathlib import Path

from kb_build.cfn_types import load_cfn_types

CFN_PROPERTIES_FILE = Path("data/cfn_properties.json")  # snapshot of describe-type, see README

TYPE_PATTERN = re.compile(r"AWS::\w+::\w+")
# A dot path (`RedirectConfig.Protocol`), a name with a lowercase and a later capital letter
# (`SecurityPolicy`, `MultiAZ`) or one led by an acronym (`SSEEnabled`). Single words stay out:
# German nouns are capitalised anyway.
_NAME = r"[A-Z][A-Za-z0-9]*"
_CANDIDATE = re.compile(
    rf"(?<![\w:.])(?:{_NAME}(?:\.{_NAME})+|{_NAME}[a-z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*"
    r"|[A-Z]{2,}[a-z]{2,}[A-Za-z0-9]*)"
)
# Look like properties but are product names, IAM policy words or values (hand-maintained);
# `AWS…` names (managed policies, rule groups) and names of resource types are skipped as well
NOT_PROPERTIES = frozenset({
    "CloudFormation", "CloudTrail", "CloudWatch", "CloudFront", "CloudShell", "DynamoDB",
    "PostgreSQL", "MySQL", "WinRM", "StringEquals", "StringLike", "NotPrincipal",
    "AdministratorAccess", "PublicRead", "PublicReadWrite", "AuthenticatedRead",
    "BucketOwnerRead", "BucketOwnerFullControl", "LogDeliveryWrite",
})


def _resolve(schema: dict, node: dict) -> tuple[dict, str | None]:
    """Follow array items and a `$ref` to the definition; returns it with its name."""
    node = node.get("items", node)
    ref = node.get("$ref", "")
    if ref.startswith("#/definitions/"):
        name = ref.removeprefix("#/definitions/")
        return schema.get("definitions", {}).get(name, {}), name
    return node, None


def _walk(schema: dict, node: dict, prefix: str, open_refs: frozenset[str]) -> set[str]:
    paths = set()
    for name, child in node.get("properties", {}).items():
        path = f"{prefix}.{name}" if prefix else name
        paths.add(path)
        target, ref = _resolve(schema, child)
        if ref not in open_refs:  # a recursive definition is expanded only once
            paths |= _walk(schema, target, path, open_refs | {ref})
    return paths


def property_paths(schema: dict) -> set[str]:
    """All property paths of a `describe-type` schema, e.g. `RedirectConfig.Protocol`."""
    return _walk(schema, schema, "", frozenset())


def build_snapshot(schemas: dict[str, str]) -> dict[str, list[str]]:
    """Type name -> sorted property paths; `schemas` holds the `describe-type` Schema strings."""
    return {t: sorted(property_paths(json.loads(s))) for t, s in sorted(schemas.items())}


@cache
def load_cfn_properties(path: Path = CFN_PROPERTIES_FILE) -> dict[str, frozenset[str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {type_name: frozenset(paths) for type_name, paths in raw.items()}


def _resource_names() -> frozenset[str]:
    """`BucketPolicy` from `AWS::S3::BucketPolicy`: a resource of its own, not a property."""
    return frozenset(t.rpartition("::")[2] for t in load_cfn_types())


def property_candidates(text: str) -> list[str]:
    """Names in `text` that look like CloudFormation properties, each once, in order."""
    skipped = NOT_PROPERTIES | _resource_names()
    found = _CANDIDATE.findall(TYPE_PATTERN.sub(" ", text))
    return list(dict.fromkeys(
        c for c in found if c not in skipped and not c.startswith("AWS")
    ))


def unknown_properties(
    text: str, resource_types: list[str], known: dict[str, frozenset[str]]
) -> list[str]:
    """Candidates that none of the rule's types, nor a type named in `text`, knows.

    A type outside the snapshot makes the rule unjudged: its properties are unknown to us.
    """
    types = list(dict.fromkeys([*resource_types, *TYPE_PATTERN.findall(text)]))
    if not resource_types or any(t not in known for t in types):
        return []
    paths = frozenset().union(*(known[t] for t in types))
    return [
        c for c in property_candidates(text)
        if not any(p == c or p.endswith(f".{c}") for p in paths)
    ]


def alternatives(
    candidate: str, resource_types: list[str], known: dict[str, frozenset[str]]
) -> list[str]:
    """What the model may use instead: siblings below the same parent, else the top level."""
    parent = candidate.rpartition(".")[0]
    paths = sorted(frozenset().union(*(known[t] for t in resource_types if t in known)))

    def is_below_parent(path: str) -> bool:
        above = path.rpartition(".")[0]
        return above == parent or above.endswith(f".{parent}")

    siblings = [p for p in paths if is_below_parent(p)] if parent else []
    return siblings or [p for p in paths if "." not in p]


def owners(candidate: str, known: dict[str, frozenset[str]]) -> list[str]:
    """The snapshot types that have `candidate`, e.g. RotationSchedule for `RotationRules`."""
    return [t for t, paths in sorted(known.items())
            if any(p == candidate or p.endswith(f".{candidate}") for p in paths)]
