"""Frozen selection (ADR 0025): old verdicts stay, only requirements without one are judged."""

from kb_build.extract.models import ExtractedSource, Requirement
from kb_build.select.curation import CurationResult
from kb_build.select.frozen import merge, unjudged
from kb_build.select.models import SelectedRequirement, Selection, Verdict


def requirement(rid: str) -> Requirement:
    return Requirement(id=rid, title="T", text="Text", primary_anchor=f"X {rid}", attributes={},
                       prefilter_passed=True)


def verdict(source: str, rid: str, outcome: str = "selected") -> Verdict:
    return Verdict(source=source, requirement_id=rid, title="T", outcome=outcome,
                   rationale="Prüfbar.", cfn_resource_types=[])


def result(verdicts: list[Verdict], model_id: str) -> CurationResult:
    selected = [SelectedRequirement(requirement_id=v.requirement_id, source=v.source,
                                    rationale=v.rationale, cfn_resource_types=[])
                for v in verdicts if v.outcome == "selected"]
    return CurationResult(Selection(audit_type="spec", model_id=model_id, selected=selected),
                          verdicts)


SOURCES = [
    ExtractedSource(source="DSGVO", version="1", origin="o",
                    requirements=[requirement("Art. 5"), requirement("Art. 12")]),
    ExtractedSource(source="KI-VO", version="1", origin="o", requirements=[requirement("Art. 50")]),
]
OLD = [verdict("DSGVO", "Art. 5"), verdict("DSGVO", "Art. 12", "not_testable")]


def test_unjudged_keeps_only_requirements_without_an_old_verdict() -> None:
    todo = unjudged(SOURCES, OLD)

    assert [(s.source, [r.id for r in s.requirements]) for s in todo] == [("KI-VO", ["Art. 50"])]


def test_merge_appends_the_new_verdicts_and_keeps_the_old_selection_unchanged() -> None:
    old, new = result(OLD, "old"), result([verdict("KI-VO", "Art. 50")], "new")

    merged = merge(old, new, SOURCES)

    assert merged.verdicts == [*OLD, new.verdicts[0]]
    assert merged.selection.selected == [*old.selection.selected, *new.selection.selected]
    assert merged.selection.model_id == "old"  # the frozen part decides the catalog's origin


def test_an_llm_error_is_no_verdict_and_is_asked_again() -> None:
    # e.g. Groq's spend limit answers 400 for every call: the next run must ask again
    failed = [*OLD, verdict("KI-VO", "Art. 50", "llm_error")]

    todo = unjudged(SOURCES, failed)
    merged = merge(result(failed, "old"), result([verdict("KI-VO", "Art. 50")], "new"),
                   SOURCES)

    assert [(s.source, [r.id for r in s.requirements]) for s in todo] == [("KI-VO", ["Art. 50"])]
    assert [v.outcome for v in merged.verdicts] == ["selected", "not_testable", "selected"]


def test_merge_drops_old_verdicts_of_decomposed_articles_and_keeps_the_order_of_the_acts() -> None:
    # #53: DSGVO Art. 5 is now Art. 5 Abs. 1 lit. a ...; the old article verdict is stale
    decomposed = [
        ExtractedSource(source="DSGVO", version="1", origin="o",
                        requirements=[requirement("Art. 5 Abs. 1 lit. a"), requirement("Art. 12")]),
        SOURCES[1],
    ]
    old = result([verdict("DSGVO", "Art. 5"), verdict("DSGVO", "Art. 12"),
                  verdict("KI-VO", "Art. 50")], "old")
    new = result([verdict("DSGVO", "Art. 5 Abs. 1 lit. a")], "new")

    merged = merge(old, new, decomposed)

    expected = ["Art. 5 Abs. 1 lit. a", "Art. 12", "Art. 50"]
    assert [v.requirement_id for v in merged.verdicts] == expected
    assert [s.requirement_id for s in merged.selection.selected] == expected


def test_a_requirement_that_is_prefiltered_now_loses_its_old_verdict_and_vice_versa() -> None:
    # #53: DSGVO Art. 9 Abs. 1 became keine_pflicht, Art. 20 Abs. 4 became a duty
    rejected = requirement("Art. 9 Abs. 1").model_copy(update={"prefilter_passed": False})
    sources = [ExtractedSource(source="DSGVO", version="1", origin="o",
                               requirements=[rejected, requirement("Art. 20 Abs. 4")])]
    old = result([verdict("DSGVO", "Art. 9 Abs. 1"),
                  verdict("DSGVO", "Art. 20 Abs. 4", "prefiltered")], "old")

    todo = unjudged(sources, old.verdicts)
    merged = merge(old, result([verdict("DSGVO", "Art. 9 Abs. 1", "prefiltered"),
                                verdict("DSGVO", "Art. 20 Abs. 4")], "new"), sources)

    assert [r.id for s in todo for r in s.requirements] == ["Art. 9 Abs. 1", "Art. 20 Abs. 4"]
    assert [(v.requirement_id, v.outcome) for v in merged.verdicts] == [
        ("Art. 9 Abs. 1", "prefiltered"), ("Art. 20 Abs. 4", "selected")]
    assert [s.requirement_id for s in merged.selection.selected] == ["Art. 20 Abs. 4"]
