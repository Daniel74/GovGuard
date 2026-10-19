"""Frozen selection (ADR 0025, SPEC G13): old verdicts stay, only new requirements are judged.

Pure logic: the checked-in selection and protocol come in, the merged ones go out; run.py does
the I/O. The cache alone is not enough: its key holds the prompt version of today.
"""

from typing import TypeVar

from kb_build.extract.models import ExtractedSource
from kb_build.select.curation import CurationResult
from kb_build.select.models import SelectedRequirement, Verdict

_Item = TypeVar("_Item", Verdict, SelectedRequirement)


def _judged(verdicts: list[Verdict], sources: list[ExtractedSource]) -> set[tuple[str, str]]:
    """Only LLM verdicts on requirements that pass the prefilter today stay frozen.

    An llm_error is no verdict: the next run asks again. The prefilter is code and costs
    nothing: it decides anew, e.g. when the decomposition turns a duty into keine_pflicht (#53).
    """
    passing = {(s.source, r.id) for s in sources for r in s.requirements if r.prefilter_passed}
    return {(v.source, v.requirement_id) for v in verdicts
            if v.outcome not in ("llm_error", "prefiltered")
            and (v.source, v.requirement_id) in passing}


def unjudged(sources: list[ExtractedSource], old: list[Verdict]) -> list[ExtractedSource]:
    """Each source with only the requirements the old protocol has no frozen verdict for."""
    judged = _judged(old, sources)
    todo = [
        s.model_copy(update={"requirements": [
            r for r in s.requirements if (s.source, r.id) not in judged]})
        for s in sources
    ]
    return [s for s in todo if s.requirements]


def merge(
    old: CurationResult, new: CurationResult, sources: list[ExtractedSource]
) -> CurationResult:
    """Old and new verdicts in the order of the sources; an old verdict whose requirement is gone
    drops out, e.g. a whole article that is decomposed now (#53). The old ones keep their content.
    """
    position = {(s.source, r.id): n for n, (s, r) in
                enumerate((s, r) for s in sources for r in s.requirements)}

    def ordered(items: list[_Item]) -> list[_Item]:
        kept = [i for i in items if (i.source, i.requirement_id) in position]
        return sorted(kept, key=lambda i: position[(i.source, i.requirement_id)])

    judged = _judged(old.verdicts, sources)
    kept = [v for v in old.verdicts if (v.source, v.requirement_id) in judged]
    still = [s for s in old.selection.selected if (s.source, s.requirement_id) in judged]
    selected = ordered([*still, *new.selection.selected])
    selection = old.selection.model_copy(update={"selected": selected})
    return CurationResult(selection, ordered([*kept, *new.verdicts]))
