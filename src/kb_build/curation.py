"""Selection of the bounded catalog: the LLM judges, the code selects (ADR 0011).

Pure logic: gets the Judge injected (ADR 0005), no boto3. There is no ranking and no cap.
"""

import logging
from dataclasses import dataclass

from govguard.models import AuditType, Preset, SourceName
from kb_build.classify import Judge
from kb_build.extracted_models import ExtractedSource, Requirement
from kb_build.relevance import is_relevant
from kb_build.selection_models import SelectedRequirement, Selection, Verdict

logger = logging.getLogger("kb_build")

LLM_ERROR = "Die Antwort des Modells blieb auch nach zwei Wiederholungen ungültig."
NO_REASON = "Vom Vorfilter verworfen."


def pinned_anchors(presets: list[Preset], audit_type: AuditType) -> set[str]:
    """Required findings of the presets must end up in the catalog (gate, ADR 0011)."""
    return {
        finding.anchor
        for preset in presets if preset.audit_type == audit_type
        for finding in preset.expected.required_findings
    }


def _decide(
    source: SourceName, requirement: Requirement, judge: Judge, scope: frozenset[str]
) -> Verdict:
    """One verdict per requirement; only the testable question goes to the LLM."""
    fields = {"source": source, "requirement_id": requirement.id, "title": requirement.title}
    if not requirement.prefilter_passed:
        reason = requirement.prefilter_reason or NO_REASON
        return Verdict(**fields, outcome="prefiltered", rationale=reason, cfn_resource_types=[])
    answer = judge(source, requirement)
    fields["cfn_resource_types"] = answer.cfn_resource_types
    if (source, requirement.id) in judge.failed:
        return Verdict(**fields, outcome="llm_error", rationale=LLM_ERROR)
    if not answer.testable:
        return Verdict(**fields, outcome="not_testable", rationale=answer.rationale)
    if judge.audit_type == "architecture" and not is_relevant(answer, scope):
        first = answer.cfn_resource_types[0]
        sentence = f"Der erste Ressourcentyp {first} liegt nicht im Prüfumfang."
        return Verdict(**fields, outcome="not_relevant", rationale=sentence)
    return Verdict(**fields, outcome="selected", rationale=answer.rationale)


def _check_pinned(
    pinned: set[str], sources: list[ExtractedSource], judge: Judge, scope: frozenset[str]
) -> None:
    """Fail fast: pinned anchors are decided first, before ~800 other requirements are paid."""
    by_anchor = {r.primary_anchor: (s.source, r) for s in sources for r in s.requirements}
    missing = sorted(pinned - by_anchor.keys())
    if missing:
        raise ValueError(f"pinned anchors not found in the sources: {missing}")
    outcomes = {a: _decide(*by_anchor[a], judge, scope).outcome for a in sorted(pinned)}
    rejected = [f"{a} ({o})" for a, o in outcomes.items() if o != "selected"]
    if rejected:
        raise ValueError(f"pinned anchors are not selected: {rejected}")


def _source_verdicts(source: ExtractedSource, judge: Judge, scope: frozenset[str]) -> list[Verdict]:
    total, asked = sum(r.prefilter_passed for r in source.requirements), 0
    verdicts = []
    for requirement in source.requirements:
        verdict = _decide(source.source, requirement, judge, scope)
        if requirement.prefilter_passed:
            asked += 1
            tested = "not testable" if verdict.outcome == "not_testable" else "testable"
            logger.info("%s %d/%d %s %s", source.source, asked, total, requirement.id, tested)
        verdicts.append(verdict)
    return verdicts


def _check_coverage(components: frozenset[str], selected: list[SelectedRequirement]) -> None:
    """Every component of the archetypes needs at least one rule, else the build stops."""
    covered = {t for s in selected for t in s.cfn_resource_types}
    uncovered = sorted(components - covered)
    if uncovered:
        raise ValueError(f"components without a selected requirement: {uncovered}")


@dataclass(frozen=True)
class CurationResult:
    selection: Selection
    verdicts: list[Verdict]  # every requirement of every source, for the human checkpoint


def curate(
    judge: Judge, sources: list[ExtractedSource], pinned_anchors: set[str], scope: frozenset[str],
    components: frozenset[str] = frozenset(),
) -> CurationResult:
    """The LLM judges, the code selects: prefilter, testable, relevant; then the two gates."""
    _check_pinned(pinned_anchors, sources, judge, scope)
    verdicts = [v for s in sources for v in _source_verdicts(s, judge, scope)]
    selected = [
        SelectedRequirement(
            requirement_id=v.requirement_id, source=v.source, rationale=v.rationale,
            cfn_resource_types=v.cfn_resource_types,
        )
        for v in verdicts if v.outcome == "selected"
    ]
    if judge.audit_type == "architecture":
        _check_coverage(components, selected)
    return CurationResult(Selection(audit_type=judge.audit_type, model_id=judge.model_id,
                                    selected=selected), verdicts)
