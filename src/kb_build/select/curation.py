"""Bounded catalog: the LLM judges, the code selects (ADR 0011).

Pure logic: gets the Judge injected (ADR 0005), no boto3. No ranking and no cap.
"""

import logging
from dataclasses import dataclass

from govguard.models import SourceName
from kb_build.extract.models import ExtractedSource, Requirement
from kb_build.select.classify import Judge
from kb_build.select.gates import check_coverage, check_pinned
from kb_build.select.models import (
    Classification,
    Outcome,
    ScopeLevel,
    SelectedRequirement,
    Selection,
    Verdict,
)

logger = logging.getLogger("kb_build")

LLM_ERROR = "Die Antwort des Modells blieb auch nach zwei Wiederholungen ungültig."
NO_REASON = "Vom Vorfilter verworfen."
# Shared Responsibility: the duty is not the workload's (issue #18)
LEVEL_SENTENCES: dict[ScopeLevel, str] = {
    "account": "Die Pflicht liegt beim Konto oder der Organisation, nicht am Template.",
    "people": "Die Pflicht liegt bei Personen oder Prozessen, nicht am Template.",
    "provider": "Die Pflicht liegt beim Cloud-Anbieter, nicht am Template.",
}
# A preset proves a pinned anchor is visible at the template, so the code overrides the level (#24)
PINNED_LEVEL_SENTENCE = (
    "Pflichtanker eines Presets: Der Code setzt die Ebene auf „template“, "
    "denn das Preset belegt, dass der Befund am Template erkennbar ist.")


def _decide(
    source: SourceName, requirement: Requirement, judge: Judge, is_pinned: bool
) -> Verdict:
    """One verdict per requirement; only the testable question goes to the LLM.

    A pinned anchor keeps `testable` and the types from the LLM, but its level is `template` (#24).
    """
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
    rationale = answer.rationale
    if judge.audit_type == "architecture" and is_pinned and answer.scope_level != "template":
        answer = answer.model_copy(update={"scope_level": "template"})
        rationale = f"{rationale.rstrip('.')}. {PINNED_LEVEL_SENTENCE}"
    if judge.audit_type == "architecture" and (reason := _not_relevant_reason(answer)):
        return Verdict(**fields, outcome="not_relevant", rationale=reason)
    return Verdict(**fields, outcome="selected", rationale=rationale)


def _not_relevant_reason(answer: Classification) -> str | None:
    """Fixed sentence why the code drops a testable architecture requirement (ADR 0011).

    The judge already stripped the types outside the scope: any type left makes it relevant,
    the first one left being the most important (ADR 0013).
    """
    if answer.scope_level != "template":
        return LEVEL_SENTENCES[answer.scope_level]
    if not answer.cfn_resource_types:  # the judge stripped every type outside the scope (#19)
        return "Kein Ressourcentyp der Anforderung liegt im Prüfumfang."
    return None


def _pinned_outcomes(
    pinned: set[str], sources: list[ExtractedSource], judge: Judge
) -> dict[str, Outcome]:
    """Fail fast: pinned anchors are decided first, before ~800 other requirements are paid."""
    by_anchor = {r.primary_anchor: (s.source, r) for s in sources for r in s.requirements}
    found = sorted(pinned & by_anchor.keys())
    return {a: _decide(*by_anchor[a], judge, is_pinned=True).outcome for a in found}


def _source_verdicts(source: ExtractedSource, judge: Judge, pinned: set[str]) -> list[Verdict]:
    total, asked = sum(r.prefilter_passed for r in source.requirements), 0
    verdicts = []
    for requirement in source.requirements:
        is_pinned = requirement.primary_anchor in pinned
        verdict = _decide(source.source, requirement, judge, is_pinned=is_pinned)
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
    judge: Judge, sources: list[ExtractedSource], pinned: set[str], components: frozenset[str],
) -> CurationResult:
    """The LLM judges, the code selects: prefilter, testable, relevant; then the two gates."""
    check_pinned(pinned, _pinned_outcomes(pinned, sources, judge))
    verdicts = [v for s in sources for v in _source_verdicts(s, judge, pinned)]
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

