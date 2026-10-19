"""Touchstones of the decomposition (#53) against the checked-in protocol, set before the run.

Red until `python -m kb_build decompose` has written data/intermediate/decompositions_spec.json.
"""

import pytest
from pydantic import TypeAdapter

from kb_build.decompose.models import ArticleDecomposition, DecomposedGroup
from kb_build.paths import BuildPaths


def protocol() -> list[ArticleDecomposition]:
    raw = BuildPaths().out_file("decompositions", "spec").read_bytes()
    return TypeAdapter(list[ArticleDecomposition]).validate_json(raw)


def group_of(source: str, mark: str) -> DecomposedGroup:
    return next(g for e in protocol() if e.source == source for g in e.groups if mark in g.marks)


def marks(article: str, letters: str) -> list[str]:
    return [f"{article} lit. {letter}" for letter in letters]


@pytest.mark.parametrize(("source", "paragraph", "letters", "kind"), [
    ("DSGVO", "Art. 5 Abs. 1", "abcdef", "alle_gelten"),
    ("DSGVO", "Art. 32 Abs. 1", "abcd", "je_nach_risiko"),
    ("KI-VO", "Art. 6 Abs. 1", "ab", "alle_gelten"),
])
def test_each_item_is_a_duty_of_its_own(source: str, paragraph: str, letters: str,
                                        kind: str) -> None:
    for mark in marks(paragraph, letters):
        group = group_of(source, mark)
        assert group.kind == kind, mark
        assert f"{source} {mark}" in group.anchors


@pytest.mark.parametrize(("source", "paragraph", "letters"), [
    ("DSGVO", "Art. 6 Abs. 1", "abcdef"),
    ("DSGVO", "Art. 9 Abs. 2", "abcdefghij"),
    ("KI-VO", "Art. 6 Abs. 3", "abcd"),
])
def test_alternatives_become_one_requirement_of_their_paragraph(source: str, paragraph: str,
                                                                letters: str) -> None:
    group = group_of(source, f"{paragraph} lit. a")
    assert group.kind == "eine_genuegt"
    assert set(marks(paragraph, letters)) <= set(group.marks)
    assert group.anchors == [f"{source} {paragraph}"]


def test_a_prohibition_with_its_own_exceptions_is_carried_by_the_exceptions() -> None:
    # Wohngeld names Art. 9 Abs. 2 lit. b, yet the rule of Abs. 1 alone said FAIL (19.10.2026)
    assert group_of("DSGVO", "Art. 9 Abs. 1").kind == "keine_pflicht"


def test_the_prohibited_ai_practices_stay_duties() -> None:
    for mark in marks("Art. 5 Abs. 1", ["a", "b", "ba", "bb", "c", "d", "e", "f", "g", "h"]):
        assert group_of("KI-VO", mark).kind == "alle_gelten", mark
