from kb_build.decompose.models import Decomposition, Group
from kb_build.decompose.parts import decompose_source, decomposition_problems, parts
from kb_build.extract.models import ExtractedSource, Requirement, Section

LEAD_IN = "Die Verarbeitung ist nur rechtmäßig, wenn eine der Bedingungen erfüllt ist:"
ART_6 = Requirement(
    id="Art. 6", title="Rechtmäßigkeit der Verarbeitung", text="(1) ...",
    primary_anchor="DSGVO Art. 6", attributes={"chapter": 2, "fine_tier": 4},
    prefilter_passed=True,
    sections=[
        Section(mark="Art. 6 Abs. 1 lit. a", text="Einwilligung;", lead_in=LEAD_IN),
        Section(mark="Art. 6 Abs. 1 lit. b", text="Vertrag.", lead_in=LEAD_IN),
        Section(mark="Art. 6 Abs. 1 UAbs. 2", text="Buchstabe f gilt nicht für Behörden."),
        Section(mark="Art. 6 Abs. 2", text="Die Mitgliedstaaten können Bestimmungen erlassen."),
    ],
)


def group(kind: str, *marks: str) -> Group:
    return Group(marks=list(marks), kind=kind, rationale="Ein Satz.")


ANSWER = Decomposition(groups=[
    group("eine_genuegt", "Art. 6 Abs. 1 lit. a", "Art. 6 Abs. 1 lit. b"),
    group("alle_gelten", "Art. 6 Abs. 1 UAbs. 2"),
    group("keine_pflicht", "Art. 6 Abs. 2"),
])


def test_a_complete_answer_has_no_problems() -> None:
    assert decomposition_problems(ART_6, ANSWER) == []


def test_unknown_missing_and_repeated_marks_are_sent_back() -> None:
    answer = Decomposition(groups=[
        group("alle_gelten", "Art. 6 Abs. 1 lit. a", "Abs. 9"),
        group("alle_gelten", "Art. 6 Abs. 1 lit. a", "Art. 6 Abs. 1 UAbs. 2", "Art. 6 Abs. 2"),
    ])
    assert decomposition_problems(ART_6, answer) == [
        "Diese Marken gibt es nicht: ['Abs. 9'].",
        "Diese Marken fehlen: ['Art. 6 Abs. 1 lit. b'].",
        "Diese Marken stehen in mehr als einer Gruppe: ['Art. 6 Abs. 1 lit. a'].",
    ]


def test_eine_genuegt_stays_within_one_paragraph() -> None:
    answer = Decomposition(groups=[
        group("eine_genuegt", "Art. 6 Abs. 1 lit. a", "Art. 6 Abs. 2"),
        group("alle_gelten", "Art. 6 Abs. 1 lit. b", "Art. 6 Abs. 1 UAbs. 2"),
    ])
    assert decomposition_problems(ART_6, answer) == [
        "Eine Gruppe „eine_genuegt“ darf nur Abschnitte eines Absatzes enthalten: "
        "['Art. 6 Abs. 1 lit. a', 'Art. 6 Abs. 2'].",
    ]


def test_two_eine_genuegt_groups_of_one_paragraph_would_share_an_anchor() -> None:
    answer = Decomposition(groups=[
        group("eine_genuegt", "Art. 6 Abs. 1 lit. a", "Art. 6 Abs. 1 UAbs. 2"),
        group("eine_genuegt", "Art. 6 Abs. 1 lit. b", "Art. 6 Abs. 1 lit. a"),
        group("alle_gelten", "Art. 6 Abs. 2"),
    ])
    assert "Dieser Anker entstünde doppelt: ['Art. 6 Abs. 1']." in decomposition_problems(
        ART_6, answer)


def test_eine_genuegt_becomes_one_requirement_of_its_paragraph() -> None:
    first = parts("DSGVO", ART_6, ANSWER)[0]
    assert (first.id, first.primary_anchor) == ("Art. 6 Abs. 1", "DSGVO Art. 6 Abs. 1")
    assert first.text == f"{LEAD_IN} a) Einwilligung; b) Vertrag."
    assert first.title == "Rechtmäßigkeit der Verarbeitung"
    assert first.attributes == {"chapter": 2, "fine_tier": 4, "article": "Art. 6",
                                "kind": "eine_genuegt", "quote": "a) Einwilligung; b) Vertrag."}
    assert first.prefilter_passed and first.sections == []


def test_each_section_of_alle_gelten_and_je_nach_risiko_is_a_requirement() -> None:
    answer = Decomposition(groups=[
        group("je_nach_risiko", "Art. 6 Abs. 1 lit. a", "Art. 6 Abs. 1 lit. b"),
        group("alle_gelten", "Art. 6 Abs. 1 UAbs. 2", "Art. 6 Abs. 2"),
    ])
    found = parts("DSGVO", ART_6, answer)
    assert [r.primary_anchor for r in found] == [
        "DSGVO Art. 6 Abs. 1 lit. a", "DSGVO Art. 6 Abs. 1 lit. b",
        "DSGVO Art. 6 Abs. 1 UAbs. 2", "DSGVO Art. 6 Abs. 2"]
    assert found[0].text == f"{LEAD_IN} a) Einwilligung;"
    assert found[0].attributes["quote"] == "a) Einwilligung;"  # the code quotes, not the LLM
    assert found[2].text == "Buchstabe f gilt nicht für Behörden."
    assert found[2].attributes["quote"] == found[2].text


def test_a_section_too_short_to_prove_anything_is_quoted_with_its_lead_in() -> None:
    short = ART_6.model_copy(update={"sections": [
        Section(mark="Art. 6 Abs. 1 lit. a", text="Vertrag;", lead_in=LEAD_IN)]})
    answer = Decomposition(groups=[group("alle_gelten", "Art. 6 Abs. 1 lit. a")])
    [part] = parts("DSGVO", short, answer)
    assert part.attributes["quote"] == f"{LEAD_IN} a) Vertrag;"


def test_keine_pflicht_is_carried_on_as_rejected_with_its_reason() -> None:
    last = parts("DSGVO", ART_6, ANSWER)[-1]
    assert last.id == "Art. 6 Abs. 2" and not last.prefilter_passed
    assert last.prefilter_reason == "Keine Pflicht laut Zerlegung: Ein Satz."


def test_parts_follow_the_order_of_the_act_not_of_the_answer() -> None:
    reversed_answer = Decomposition(groups=list(reversed(ANSWER.groups)))
    assert [r.id for r in parts("DSGVO", ART_6, reversed_answer)] == [
        "Art. 6 Abs. 1", "Art. 6 Abs. 1 UAbs. 2", "Art. 6 Abs. 2"]


def source_with(*requirements: Requirement) -> ExtractedSource:
    return ExtractedSource(source="DSGVO", version="v", origin="o", requirements=list(requirements))


def test_a_source_is_decomposed_article_by_article_with_a_protocol() -> None:
    art_1 = Requirement(id="Art. 1", title="t", text="x", primary_anchor="DSGVO Art. 1",
                        attributes={}, prefilter_passed=False, sections=ART_6.sections)
    decomposed, protocol = decompose_source(source_with(art_1, ART_6), lambda s, a: ANSWER)
    assert [r.id for r in decomposed.requirements] == [
        "Art. 1", "Art. 6 Abs. 1", "Art. 6 Abs. 1 UAbs. 2", "Art. 6 Abs. 2"]
    assert decomposed.requirements[0].sections == []  # rejected by the prefilter: not asked
    [entry] = protocol
    assert (entry.requirement_id, entry.outcome) == ("Art. 6", "decomposed")
    assert entry.groups[0].anchors == ["DSGVO Art. 6 Abs. 1"]
    assert entry.groups[1].anchors == ["DSGVO Art. 6 Abs. 1 UAbs. 2"]


def test_an_article_the_model_could_not_decompose_stays_whole() -> None:
    decomposed, [entry] = decompose_source(source_with(ART_6), lambda s, a: None)
    assert [r.primary_anchor for r in decomposed.requirements] == ["DSGVO Art. 6"]
    assert (entry.outcome, entry.groups) == ("llm_error", [])
