"""Bounded catalog: the LLM judges, the code selects (ADR 0011).

Pure logic: gets the Judge injected (ADR 0005), no boto3. No ranking and no cap.
"""

import logging
from dataclasses import dataclass

from govguard.models import SourceName
from kb_build.classify import Judge
from kb_build.extracted_models import ExtractedSource, Requirement
from kb_build.gates import check_coverage, check_pinned
from kb_build.relevance import is_relevant
from kb_build.scope import Scope
from kb_build.selection_models import Outcome, SelectedRequirement, Selection, Verdict

logger = logging.getLogger("kb_build")

LLM_ERROR = "Die Antwort des Modells blieb auch nach zwei Wiederholungen ungültig."
NO_REASON = "Vom Vorfilter verworfen."


def _decide(source: SourceName, requirement: Requirement, judge: Judge, scope: Scope) -> Verdict:
    """One verdict per requirement; only the testable question goes to the LLM."""
    fields = {"source": source, "requirement_id": requirement.id, "title": requirement.title}
    if not requirement.prefilter_passed:
        reason = requirement.prefilter_reason or NO_REASON
        return Verdict(**fields, outcome="prefiltered", rationale=reason, cfn_resource_types=[])
    answer = judge(source, requirement)
    if answer is None:
        return Verdict(**fields, outcome="llm_error", rationale=LLM_ERROR, cfn_resource_types=[])
    fields["cfn_resource_types"] = answer.cfn_resource_types
    if not answer.testable:
        return Verdict(**fields, outcome="not_testable", rationale=answer.rationale)
    if judge.audit_type == "architecture" and not is_relevant(answer, scope):
        first = answer.cfn_resource_types[0]
        sentence = f"Der erste Ressourcentyp {first} liegt nicht im Prüfumfang."
        return Verdict(**fields, outcome="not_relevant", rationale=sentence)
    return Verdict(**fields, outcome="selected", rationale=answer.rationale)


def _pinned_outcomes(
    pinned: set[str], sources: list[ExtractedSource], judge: Judge, scope: Scope
) -> dict[str, Outcome]:
    """Fail fast: pinned anchors are decided first, before ~800 other requirements are paid."""
    by_anchor = {r.primary_anchor: (s.source, r) for s in sources for r in s.requirements}
    found = sorted(pinned & by_anchor.keys())
    return {a: _decide(*by_anchor[a], judge, scope).outcome for a in found}


def _source_verdicts(source: ExtractedSource, judge: Judge, scope: Scope) -> list[Verdict]:
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


@dataclass(frozen=True)
class CurationResult:
    selection: Selection
    verdicts: list[Verdict]  # every requirement of every source, for the human checkpoint


def curate(
    judge: Judge, sources: list[ExtractedSource], pinned: set[str], scope: Scope,
    components: frozenset[str],
) -> CurationResult:
    """The LLM judges, the code selects: prefilter, testable, relevant; then the two gates."""
    check_pinned(pinned, _pinned_outcomes(pinned, sources, judge, scope))
    verdicts = [v for s in sources for v in _source_verdicts(s, judge, scope)]
    selected = [
        SelectedRequirement(
            requirement_id=v.requirement_id, source=v.source, rationale=v.rationale,
            cfn_resource_types=v.cfn_resource_types,
        )
        for v in verdicts if v.outcome == "selected"
    ]
    if judge.audit_type == "architecture":
        check_coverage(components, selected)
    return CurationResult(Selection(audit_type=judge.audit_type, model_id=judge.model_id,
                                    selected=selected), verdicts)

