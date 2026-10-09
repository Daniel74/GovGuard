"""Selection of the bounded catalog: the LLM judges, the code selects (ADR 0007).

Pure logic: gets the Pydantic AI model injected (ADR 0005), no boto3.
"""

import logging
from dataclasses import dataclass

from pydantic_ai.models import Model

from govguard.models import AuditType, Preset, SourceName
from kb_build.archetype_profiles import ArchetypeProfile, relevant_resource_types
from kb_build.classify import Judge
from kb_build.extracted_models import ExtractedSource
from kb_build.ranking import Candidate, is_relevant, rank_source
from kb_build.selection_models import SelectedRequirement, Selection, Verdict

logger = logging.getLogger("kb_build")

MAX_PINNED = 4  # pinned anchors per audit type (ADR 0007)


def pinned_anchors(presets: list[Preset], audit_type: AuditType) -> set[str]:
    """Required findings of the presets are the pinned slots of their audit type."""
    return {
        finding.anchor
        for preset in presets if preset.audit_type == audit_type
        for finding in preset.expected.required_findings
    }


def _classified(source: ExtractedSource, pinned: set[str], judge: Judge) -> list[Candidate]:
    """Only prefiltered and pinned requirements are asked; the rest never reaches the LLM."""
    asked = [r for r in source.requirements if r.prefilter_passed or r.primary_anchor in pinned]
    candidates = []
    for number, requirement in enumerate(asked, start=1):
        classification = judge(source.source, requirement)
        verdict = "testable" if classification.testable else "not testable"
        logger.info("%s %d/%d %s %s", source.source, number, len(asked), requirement.id, verdict)
        candidates.append(Candidate(requirement, classification))
    return candidates


def _check_pinned(pinned: set[str], sources: list[ExtractedSource], judge: Judge) -> None:
    """Fail fast: pinned anchors are classified first, before ~500 other requirements are paid."""
    if len(pinned) > MAX_PINNED:
        raise ValueError(f"{len(pinned)} pinned anchors, at most {MAX_PINNED} allowed")
    known = {r.primary_anchor for s in sources for r in s.requirements}
    if pinned - known:
        raise ValueError(f"pinned anchors not found in the sources: {sorted(pinned - known)}")
    untestable = [
        r.primary_anchor for s in sources for r in s.requirements
        if r.primary_anchor in pinned and not judge(s.source, r).testable
    ]
    if untestable:
        raise ValueError(f"pinned anchors are not testable: {sorted(untestable)}")


def _verdict(
    source: SourceName, candidate: Candidate, kept: dict[str, SelectedRequirement], judge: Judge,
    relevant: set[str] | None,
) -> Verdict:
    classification, requirement = candidate.classification, candidate.requirement
    if requirement.id in kept:
        outcome = "pinned" if kept[requirement.id].pinned else "selected"
    elif (source, requirement.id) in judge.failed:
        outcome = "llm_error"
    elif not classification.testable:
        outcome = "not_testable"
    elif relevant is not None and not is_relevant(candidate, relevant):
        outcome = "not_relevant"
    else:
        outcome = "over_cap"
    return Verdict(
        source=source, requirement_id=requirement.id, title=requirement.title,
        testable=classification.testable, rationale=classification.rationale,
        cfn_resource_types=classification.cfn_resource_types, outcome=outcome,
    )


def _select_source(
    source: ExtractedSource, pinned: set[str], relevant: set[str] | None, judge: Judge
) -> tuple[list[SelectedRequirement], list[Verdict]]:
    candidates = _classified(source, pinned, judge)
    pinned_ids = {c.requirement.id for c in candidates if c.requirement.primary_anchor in pinned}
    testable = [c for c in candidates if c.classification.testable]
    selected = rank_source(source.source, testable, relevant, pinned_ids=pinned_ids)
    kept = {s.requirement_id: s for s in selected}
    return selected, [_verdict(source.source, c, kept, judge, relevant) for c in candidates]


@dataclass(frozen=True)
class CurationResult:
    selection: Selection
    verdicts: list[Verdict]  # every requirement the LLM saw, for the human checkpoint


def curate(
    audit_type: AuditType,
    sources: list[ExtractedSource],
    pinned_anchors: set[str],
    profiles: list[ArchetypeProfile],
    model: Model,
) -> CurationResult:
    """The LLM judges, the code selects: relevance, pinned slots, ranking, cap (ADR 0007)."""
    judge = Judge(audit_type, model)
    _check_pinned(pinned_anchors, sources, judge)
    relevant = relevant_resource_types(profiles) if audit_type == "architecture" else None
    per_source = [_select_source(s, pinned_anchors, relevant, judge) for s in sources]
    selection = Selection(
        audit_type=audit_type, model_id=model.model_name,
        selected=[entry for selected, _ in per_source for entry in selected],
    )
    return CurationResult(selection, [v for _, verdicts in per_source for v in verdicts])
