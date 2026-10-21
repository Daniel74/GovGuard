"""Gates of the rule catalog (ADR 0011): the build stops instead of shipping a gap. Pure code."""

from collections import Counter

from govguard.models import Rule, RuleCatalog, RuleDraft, SourceName
from govguard.text import contains_quote, normalize
from kb_build.extract.models import ExtractedSource, Requirement
from kb_build.reference.cfn_properties import TYPE_PATTERN
from kb_build.reference.scope import Scope
from kb_build.select.models import Selection

Anchors = dict[str, tuple[SourceName, Requirement]]  # primary anchor -> (source, requirement)


def requirements_by_anchor(sources: list[ExtractedSource]) -> Anchors:
    """All requirements, not only the selected ones: cross references may point anywhere.

    The article of a decomposed part stays a known anchor, e.g. "DSGVO Art. 32" (#53).
    """
    anchors: Anchors = {r.primary_anchor: (s.source, r) for s in sources for r in s.requirements}
    for source in sources:
        for r in source.requirements:
            if "article" in r.attributes:
                anchors.setdefault(f"{source.source} {r.attributes['article']}", (source.source, r))
    return anchors


def is_quoted(requirement: Requirement, quote: str) -> bool:
    """Verbatim in the text of exactly this requirement.

    A text shorter than MIN_QUOTE_LENGTH may be quoted whole, e.g. SDM M60.P03 "Löschkonzept".
    """
    whole = normalize(quote) == normalize(requirement.text)
    return whole or contains_quote(requirement.text, quote)


def quote_deviation(text: str, quote: str) -> str:
    """Where the quote leaves the text: the longest quoted start found, then both continuations."""
    words, text = normalize(quote).split(" "), normalize(text)
    for n in range(len(words) - 1, 0, -1):
        start = text.find(" ".join(words[:n]))
        if start >= 0:
            rest = text[start + len(" ".join(words[:n])):].split()
            return (f"Ab „{' '.join(words[n:n + 5])}“ weicht es ab; im Text steht dort "
                    f"„{' '.join(rest[:5])}“.")
    return "Schon der Anfang des Zitats fehlt im Text."


def invalid_cross_references(draft: RuleDraft, source: SourceName, anchors: Anchors) -> list[str]:
    """A cross reference must exist and belong to another source (CONTEXT.md: Querverweis)."""
    return [
        ref.anchor for ref in draft.cross_references
        if ref.anchor not in anchors or anchors[ref.anchor][0] == source
    ]


def _rule_errors(rule: Rule, anchors: Anchors, scope: Scope) -> list[str]:
    if rule.primary_anchor not in anchors:
        return [f"primary anchor {rule.primary_anchor!r} not found in the sources"]
    errors = []
    if not is_quoted(anchors[rule.primary_anchor][1], rule.source_quote):
        errors.append(f"source_quote is not verbatim in the text of {rule.primary_anchor}")
    for anchor in invalid_cross_references(rule, rule.source, anchors):
        errors.append(f"cross reference {anchor!r} is unknown or of the same source")
    text_naming_types = " ".join([*rule.cfn_resource_types, rule.compliant_if, rule.violation_if])
    outside = scope.outside(TYPE_PATTERN.findall(text_naming_types))  # nothing judges them (#19)
    if outside:
        errors.append(f"resource types outside the scope: {outside}")
    return errors


def _completeness_errors(catalog: RuleCatalog, selection: Selection, anchors: Anchors) -> list[str]:
    """Exactly one rule per selected requirement: the bounded catalog loses nothing (ADR 0011)."""
    rule_counts = Counter(
        f"{source} {requirement.id}" for source, requirement in
        (anchors[r.primary_anchor] for r in catalog.rules if r.primary_anchor in anchors)
    )
    wanted = {f"{s.source} {s.requirement_id}" for s in selection.selected}
    checks = {
        "selected requirements without a rule": sorted(wanted - rule_counts.keys()),
        "requirements with more than one rule": sorted(k for k, n in rule_counts.items() if n > 1),
        "rules for requirements that were not selected": sorted(rule_counts.keys() - wanted),
    }
    return [f"{label}: {keys}" for label, keys in checks.items() if keys]


def check_rules(
    catalog: RuleCatalog, selection: Selection, sources: list[ExtractedSource],
    scope: Scope,
) -> None:
    """Gate before the catalog is written: schema, anchor, quote, cross references, resource
    types in the scope.

    Field types are already checked by Pydantic when `Rule` is built.
    """
    anchors = requirements_by_anchor(sources)
    errors = [f"{r.id}: {e}" for r in catalog.rules for e in _rule_errors(r, anchors, scope)]
    errors += _completeness_errors(catalog, selection, anchors)
    if errors:
        raise ValueError("rules failed the gate:\n" + "\n".join(errors))
