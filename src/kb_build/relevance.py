"""Relevance of a requirement for the architecture audit (ADR 0011). Pure code."""

from kb_build.selection_models import Classification


def is_relevant(classification: Classification, scope: frozenset[str]) -> bool:
    """The first listed type is the most important one (ADR 0007); it must be in the scope."""
    types = classification.cfn_resource_types
    return bool(types) and types[0] in scope
