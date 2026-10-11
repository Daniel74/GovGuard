"""Gates of the bounded catalog (ADR 0011): the build stops instead of shipping a gap. Pure code."""

from govguard.models import AuditType, Preset
from kb_build.selection_models import Outcome, SelectedRequirement


def pinned_anchors(presets: list[Preset], audit_type: AuditType) -> set[str]:
    """Required findings of the presets must end up in the catalog."""
    return {
        finding.anchor
        for preset in presets if preset.audit_type == audit_type
        for finding in preset.expected.required_findings
    }


def check_pinned(pinned: set[str], outcomes: dict[str, Outcome]) -> None:
    """`outcomes` holds the verdict per pinned anchor found in the sources."""
    missing = sorted(pinned - outcomes.keys())
    if missing:
        raise ValueError(f"pinned anchors not found in the sources: {missing}")
    rejected = [f"{a} ({o})" for a, o in sorted(outcomes.items()) if o != "selected"]
    if rejected:
        raise ValueError(f"pinned anchors are not selected: {rejected}")


def check_coverage(components: frozenset[str], selected: list[SelectedRequirement]) -> None:
    """Every component of the archetypes needs at least one rule.

    A type counts at any position: at runtime a rule goes to the model as soon as one of
    its types is in the template (ADR 0007), so it covers that component.
    """
    covered = {t for s in selected for t in s.cfn_resource_types}
    uncovered = sorted(components - covered)
    if uncovered:
        raise ValueError(f"components without a selected requirement: {uncovered}")
