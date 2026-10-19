"""From the LLM's groups to requirements (#53): the code sets anchor, text and quote. Pure code.

A mark is the address of a section, e.g. "Art. 32 Abs. 1 lit. b"; the source name in front
makes it an anchor. Only an eine_genuegt group becomes one requirement: its anchor is the
paragraph, its text holds every alternative.
"""

import re
from collections.abc import Callable

from govguard.models import SourceName
from govguard.text import too_short_to_prove
from kb_build.decompose.models import ArticleDecomposition, DecomposedGroup, Decomposition, Group
from kb_build.extract.models import ExtractedSource, Requirement, Section

SUBDIVISION = re.compile(r" (lit\. \w+|UAbs\. \d+)$")
NO_DUTY = "Keine Pflicht laut Zerlegung: {rationale}"


def paragraph(mark: str) -> str:
    """ "Art. 6 Abs. 1 lit. a" -> "Art. 6 Abs. 1"; an article without paragraphs stays itself."""
    return SUBDIVISION.sub("", mark)


def _members(group: Group) -> list[tuple[str, list[str]]]:
    """Each requirement a group becomes: its id and the marks of its sections."""
    if group.kind == "eine_genuegt" and len(group.marks) > 1:
        return [(paragraph(group.marks[0]), list(group.marks))]
    return [(mark, [mark]) for mark in group.marks]


def group_marks(group: Group) -> list[str]:
    """The ids of the requirements a group becomes."""
    return [mark for mark, _ in _members(group)]


def _repeated(items: list[str]) -> list[str]:
    return sorted({item for item in items if items.count(item) > 1})


def decomposition_problems(article: Requirement, answer: Decomposition) -> list[str]:
    """What the model must redo: every mark exactly once, alternatives within one paragraph,
    no anchor twice. The text reaches the model as retry prompt.
    """
    known = [s.mark for s in article.sections]
    given = [m for g in answer.groups for m in g.marks]
    repeated = _repeated(given)
    checks = {
        "Diese Marken gibt es nicht": list(dict.fromkeys(m for m in given if m not in known)),
        "Diese Marken fehlen": [m for m in known if m not in given],
        "Diese Marken stehen in mehr als einer Gruppe": repeated,
    }
    problems = [f"{label}: {marks}." for label, marks in checks.items() if marks]
    problems += [
        f"Eine Gruppe „eine_genuegt“ darf nur Abschnitte eines Absatzes enthalten: {g.marks}."
        for g in answer.groups
        if g.kind == "eine_genuegt" and len({paragraph(m) for m in g.marks}) > 1
    ]
    doubled = [a for a in _repeated([a for g in answer.groups for a in group_marks(g)])
               if a not in repeated]
    if doubled:
        problems.append(f"Dieser Anker entstünde doppelt: {doubled}.")
    return problems


def _text(sections: list[Section], lead_in: bool = True) -> str:
    """Lead-in once, then each section with its list letter: verbatim words of the act."""
    words: list[str] = []
    for section in sections:
        if lead_in and section.lead_in and section.lead_in not in words:
            words.append(section.lead_in)
        _, lit, letter = section.mark.rpartition(" lit. ")
        words.append(f"{letter}) {section.text}" if lit else section.text)
    return " ".join(words)


def _part(source: SourceName, article: Requirement, group: Group, mark: str,
          sections: list[Section]) -> Requirement:
    rejected, text, own = group.kind == "keine_pflicht", _text(sections), _text(sections, False)
    quote = text if too_short_to_prove(own) else own  # the code quotes, never the LLM (ADR 0026)
    return Requirement(
        id=mark, title=article.title, text=text, primary_anchor=f"{source} {mark}",
        attributes={**article.attributes, "article": article.id, "kind": group.kind,
                    "quote": quote},
        prefilter_passed=not rejected,
        prefilter_reason=NO_DUTY.format(rationale=group.rationale) if rejected else None,
    )


def parts(source: SourceName, article: Requirement, answer: Decomposition) -> list[Requirement]:
    """The requirements of a valid answer, in the order of the act: stable across answers."""
    sections = {s.mark: s for s in article.sections}
    position = {mark: n for n, mark in enumerate(sections)}
    found = []
    for group in sorted(answer.groups, key=lambda g: min(position[m] for m in g.marks)):
        found += [_part(source, article, group, mark, [sections[m] for m in members])
                  for mark, members in _members(group)]
    return found


Split = Callable[[SourceName, Requirement], Decomposition | None]  # the Splitter, or a fake


def _protocol(source: SourceName, article: Requirement,
              answer: Decomposition | None) -> ArticleDecomposition:
    groups = [] if answer is None else [
        DecomposedGroup(**g.model_dump(), anchors=[f"{source} {m}" for m in group_marks(g)])
        for g in answer.groups
    ]
    outcome = "llm_error" if answer is None else "decomposed"
    return ArticleDecomposition(source=source, requirement_id=article.id, outcome=outcome,
                                groups=groups)


def decompose_source(
    source: ExtractedSource, split: Split
) -> tuple[ExtractedSource, list[ArticleDecomposition]]:
    """Each article that passed the prefilter becomes its parts; an article the model could
    not decompose stays whole, as before #53. The rest is kept as is, for the protocol of select.
    """
    requirements, protocol = [], []
    for article in source.requirements:
        whole = article.model_copy(update={"sections": []})
        if not (article.prefilter_passed and article.sections):
            requirements.append(whole)
            continue
        answer = split(source.source, article)
        protocol.append(_protocol(source.source, article, answer))
        requirements += [whole] if answer is None else parts(source.source, article, answer)
    return source.model_copy(update={"requirements": requirements}), protocol
