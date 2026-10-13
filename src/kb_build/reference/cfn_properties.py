"""Real CloudFormation properties per type: the LLM must not invent them (#17). Pure code."""

import json
import re
from dataclasses import dataclass

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
    "OpenSearch", "ElastiCache", "SecretsManager", "EventBridge", "GuardDuty",
    "PostgreSQL", "MySQL", "WinRM", "StringEquals", "StringLike", "NotPrincipal",
    "AdministratorAccess", "PublicRead", "PublicReadWrite", "AuthenticatedRead",
    "BucketOwnerRead", "BucketOwnerFullControl", "LogDeliveryWrite",
})




@dataclass(frozen=True)
class PropertyIndex:
    """What a rule may name: real property paths per scope type, read by the entry point."""

    paths: dict[str, frozenset[str]]  # data/input/cfn_properties.json
    # `BucketPolicy` from `AWS::S3::BucketPolicy`: a resource of its own, not a property
    resource_names: frozenset[str] = frozenset()


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


def property_candidates(text: str, resource_names: frozenset[str] = frozenset()) -> list[str]:
    """Names in `text` that look like CloudFormation properties, each once, in order."""
    skipped = NOT_PROPERTIES | resource_names
    found = _CANDIDATE.findall(TYPE_PATTERN.sub(" ", text))
    return list(dict.fromkeys(
        c for c in found if c not in skipped and not c.startswith("AWS")
    ))


def _rule_types(text: str, resource_types: list[str]) -> list[str]:
    """The rule's types plus those named in `text`, each once."""
    return list(dict.fromkeys([*resource_types, *TYPE_PATTERN.findall(text)]))


def unjudged_types(text: str, resource_types: list[str], index: PropertyIndex) -> list[str]:
    """Types outside the snapshot: their properties are unknown, so the rule stays unjudged."""
    return [t for t in _rule_types(text, resource_types) if t not in index.paths]


def unknown_properties(text: str, resource_types: list[str], index: PropertyIndex) -> list[str]:
    """Candidates that none of the rule's types, nor a type named in `text`, knows.

    Empty for an unjudged rule (see `unjudged_types`): the report counts it separately.
    """
    if not resource_types or unjudged_types(text, resource_types, index):
        return []
    paths = _paths_of(index, _rule_types(text, resource_types))
    return [c for c in property_candidates(text, index.resource_names)
            if not _has_property(paths, c)]


def _paths_of(index: PropertyIndex, types: list[str]) -> frozenset[str]:
    return frozenset().union(*(index.paths[t] for t in types if t in index.paths))


def _has_property(paths: frozenset[str], name: str) -> bool:
    """`name` may start below the top level: `LogFilePrefix` is found in `LoggingConfiguration`."""
    return any(p == name or p.endswith(f".{name}") for p in paths)


def alternatives(candidate: str, resource_types: list[str], index: PropertyIndex) -> list[str]:
    """What the model may use instead: siblings below the same parent, else the top level."""
    parent = candidate.rpartition(".")[0]
    paths = sorted(_paths_of(index, resource_types))

    def is_below_parent(path: str) -> bool:
        above = path.rpartition(".")[0]
        return above == parent or above.endswith(f".{parent}")

    siblings = [p for p in paths if is_below_parent(p)] if parent else []
    return siblings or [p for p in paths if "." not in p]


def owners(candidate: str, index: PropertyIndex) -> list[str]:
    """The snapshot types that have `candidate`, e.g. RotationSchedule for `RotationRules`."""
    return [t for t, paths in sorted(index.paths.items()) if _has_property(paths, candidate)]
