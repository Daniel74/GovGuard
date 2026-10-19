"""Frozen selection (ADR 0025, SPEC G13): old verdicts stay, only new requirements are judged.

Pure logic: the checked-in selection and protocol come in, the merged ones go out; run.py does
the I/O. The cache alone is not enough: its key holds the prompt version of today.
"""

from kb_build.extract.models import ExtractedSource
from kb_build.select.curation import CurationResult
from kb_build.select.models import Verdict


def _judged(verdicts: list[Verdict]) -> set[tuple[str, str]]:
    """An llm_error is no verdict on the requirement: the next run asks again."""
    return {(v.source, v.requirement_id) for v in verdicts if v.outcome != "llm_error"}


def unjudged(sources: list[ExtractedSource], old: list[Verdict]) -> list[ExtractedSource]:
    """Each source with only the requirements the old protocol has no verdict for."""
    judged = _judged(old)
    todo = [
        s.model_copy(update={"requirements": [
            r for r in s.requirements if (s.source, r.id) not in judged]})
        for s in sources
    ]
    return [s for s in todo if s.requirements]


def merge(old: CurationResult, new: CurationResult) -> CurationResult:
    """New sources come last in SELECTIONS, so the old part stays a byte-identical prefix."""
    selected = [*old.selection.selected, *new.selection.selected]
    selection = old.selection.model_copy(update={"selected": selected})
    kept = [v for v in old.verdicts if (v.source, v.requirement_id) in _judged(old.verdicts)]
    return CurationResult(selection, [*kept, *new.verdicts])
