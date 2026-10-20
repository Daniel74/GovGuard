"""Pure view logic of the conditions in a spec report: no Streamlit (#61, ADR 0028)."""

from govguard.checks.conditions import affects
from govguard.condition_models import ConditionDef, ConditionResult, LineRange
from govguard.models import Finding
from govguard_ui.report.condition_review import (
    effect_text,
    evidence_of,
    group_gaps,
    lines_label,
    rules_text,
)
from govguard_ui.report.quote import quote


def definition(condition_id: str, anchors: list[str] | None = None,
               rule_ids: list[str] | None = None) -> ConditionDef:
    return ConditionDef(id=condition_id, name=f"Name {condition_id}",
                        only_if=f"{condition_id} gilt", meaning="m", yes="Kriterium ja",
                        no="Kriterium nein",
                        anchors=anchors or [], rule_ids=rule_ids or [])


def gap(rule_id: str, anchor: str) -> Finding:
    return Finding(rule_id=rule_id, status="WARN", line_start=None, line_end=None, rationale="r",
                   recommendation="e", evidence=None, title=f"Titel {rule_id}",
                   primary_anchor=anchor, cross_references=[])


def r(lines: tuple[int, int]) -> LineRange:
    return LineRange(line_start=lines[0], line_end=lines[1])


def test_an_anchor_ends_at_the_article_and_a_listed_rule_id_belongs_too() -> None:
    cond = definition("third_country", anchors=["DSGVO Art. 4"], rule_ids=["SPEC-SDM-M50.S02"])

    assert affects(cond, "SPEC-DSGVO-Art.4Abs.2", "DSGVO Art. 4 Abs. 2")
    assert not affects(cond, "SPEC-DSGVO-Art.44", "DSGVO Art. 44")
    assert affects(cond, "SPEC-SDM-M50.S02", "SDM Trennen M50.S02")


DEFS = [definition("consent", anchors=["DSGVO Art. 7"]),
        definition("third_country", anchors=["DSGVO Art. 44"])]
CONSENT_GAP = gap("SPEC-DSGVO-Art.7", "DSGVO Art. 7")
TRANSFER_GAP = gap("SPEC-DSGVO-Art.44", "DSGVO Art. 44")
PLAIN_GAP = gap("SPEC-DSGVO-Art.5", "DSGVO Art. 5")


def results(**values: str) -> dict[str, ConditionResult]:
    return {k: ConditionResult(value=v) for k, v in values.items()}  # type: ignore[arg-type]


def test_a_gap_of_an_unstated_condition_waits_under_that_condition_all_others_are_common() -> None:
    groups = group_gaps([CONSENT_GAP, TRANSFER_GAP, PLAIN_GAP], DEFS,
                        results(consent="unstated", third_country="yes"))

    assert groups.by_condition == {"consent": [CONSENT_GAP]}
    assert groups.common == [TRANSFER_GAP, PLAIN_GAP]  # "yes": the rule counts for this project


def test_every_gap_lands_in_exactly_one_group() -> None:
    gaps = [CONSENT_GAP, TRANSFER_GAP, PLAIN_GAP]

    groups = group_gaps(gaps, DEFS, results(consent="unstated", third_country="unstated"))

    listed = [*groups.common, *(f for items in groups.by_condition.values() for f in items)]
    assert sorted(f.rule_id for f in listed) == sorted(f.rule_id for f in gaps)


def test_a_condition_without_a_gap_gets_no_group() -> None:
    groups = group_gaps([PLAIN_GAP], DEFS, results(consent="unstated", third_country="unstated"))

    assert groups.by_condition == {}


def test_the_groups_follow_the_order_of_the_condition_file() -> None:
    groups = group_gaps([TRANSFER_GAP, CONSENT_GAP], DEFS,
                        results(consent="unstated", third_country="unstated"))

    assert list(groups.by_condition) == ["consent", "third_country"]


def test_a_one_line_quote_without_sentence_ends_is_the_line_without_table_and_list_signs() -> None:
    assert quote("| a | b |", [r((1, 1))]) == "a | b"
    assert quote("- Punkt   mit  Raum", [r((1, 1))]) == "Punkt mit Raum"


PORTAL = (  # lines 1-8 of the portal example: line 3 is the denial, it starts mid-sentence
    "## 4 Rechtsgrundlagen\n"
    "\n"
    "Dafür werden die Daten mit Name und\n"
    "Anschrift ausgewertet. Eine Einwilligung der Eltern wird für diese Auswertung nicht "
    "eingeholt; die\n"
    "Verarbeitung der Gesundheitsangaben für die Auswertung stützt das Gesundheitsamt auf "
    "berechtigte\n"
    "Interessen nach Art. 6 Abs. 1 lit. f DSGVO.\n"
    "\n"
    "## 5 Analyse\n")


def test_a_quote_starts_at_the_first_whole_sentence_of_the_line_and_ends_with_the_last() -> None:
    quoted = quote(PORTAL, [r((4, 4))])

    assert quoted == ("Eine Einwilligung der Eltern wird für diese Auswertung nicht eingeholt; die "
                      "Verarbeitung der Gesundheitsangaben für die Auswertung stützt das "
                      "Gesundheitsamt auf berechtigte Interessen nach Art. 6 Abs. 1 lit. f DSGVO.")


def test_abbreviations_and_numbers_do_not_end_a_sentence() -> None:
    text = "Bei z. B. Art. 6 Abs. 1 lit. f gilt das. Danach nicht mehr."

    assert quote(text, [r((1, 1))]) == text  # one line: both sentences touch it


def test_a_sentence_across_lines_is_quoted_whole_from_its_first_line() -> None:
    text = ("Davor ist Schluss.\nDer Satz beginnt hier und\nläuft über drei Zeilen\n"
            "bis zum Punkt. Danach.")

    assert quote(text, [r((3, 3))]) == (
        "Der Satz beginnt hier und läuft über drei Zeilen bis zum Punkt.")


def test_a_sentence_longer_than_two_lines_around_the_evidence_is_cut_with_an_ellipsis() -> None:
    text = "\n".join(f"wort{n}" for n in range(1, 10)) + "."

    assert quote(text, [r((5, 5))]) == "… wort3 wort4 wort5 wort6 wort7 …"


def test_two_ranges_are_two_quotes_with_an_ellipsis_between() -> None:
    assert quote("Eins. Zwei.\n\nDrei. Vier.", [r((1, 1)), r((3, 3))]) == (
        "Eins. Zwei. … Drei. Vier.")


def test_a_long_quote_is_cut_at_240_characters_with_an_ellipsis() -> None:
    cut = quote("wort " * 100, [r((1, 1))])

    assert len(cut) == 240 and cut.endswith(" …")


def test_lines_are_named_in_singular_or_plural() -> None:
    assert lines_label([r((47, 47))]) == "Zeile 47"
    assert lines_label([r((53, 55))]) == "Zeilen 53–55"
    assert lines_label([r((5, 5)), r((9, 10))]) == "Zeilen 5, 9–10"


def test_yes_has_one_evidence_and_a_contradiction_adds_the_counter_evidence() -> None:
    plain = ConditionResult(value="yes", affirming=[r((3, 3))])
    both = ConditionResult(value="yes", affirming=[r((3, 3))], denying=[r((9, 9))])

    assert [(e.kind, e.ranges) for e in evidence_of(plain)] == [("affirming", [r((3, 3))])]
    assert [(e.kind, e.ranges) for e in evidence_of(both)] == [
        ("affirming", [r((3, 3))]), ("denying", [r((9, 9))])]


def test_no_has_the_denying_lines_and_unstated_has_none() -> None:
    assert [e.kind for e in evidence_of(ConditionResult(value="no", denying=[r((2, 2))]))] == [
        "denying"]
    assert evidence_of(ConditionResult(value="unstated")) == []


def test_the_rules_of_a_condition_read_as_articles_and_a_count_of_listed_rules() -> None:
    assert rules_text(definition("a", anchors=["KI-VO Art. 4", "KI-VO Art. 50", "DSGVO Art. 7"])) \
        == "KI-VO Art. 4 und 50, DSGVO Art. 7"
    assert rules_text(definition("a", rule_ids=["x", "y"])) == "2 ausgewählte Prüfregeln"
    assert rules_text(definition("a", anchors=["DSGVO Art. 22"], rule_ids=["x"])) \
        == "DSGVO Art. 22 und 1 ausgewählte Prüfregeln"


def test_the_effect_follows_the_value() -> None:
    cond = definition("consent", anchors=["DSGVO Art. 7"])

    assert effect_text(cond, "no", rules=4, gaps=0) == \
        "4 Prüfregeln (DSGVO Art. 7) sind nicht anwendbar."
    assert effect_text(cond, "yes", rules=4, gaps=1) == \
        "4 Prüfregeln (DSGVO Art. 7) werden geprüft."
    assert effect_text(cond, "unstated", rules=4, gaps=3) == (
        "4 Prüfregeln (DSGVO Art. 7) werden geprüft. Ihre 3 Lücken stehen unter „Nur wenn …“.")


TEN_LINES = "\n".join(f"Zeile {n}" for n in range(1, 11)) + "\n"


def test_the_document_marks_every_range_of_a_condition_and_starts_above_the_first() -> None:
    from govguard_ui.report.review import document_window

    window = document_window(TEN_LINES, gap("x", "y"), full=False, marks=[r((8, 8)), r((6, 7))])

    assert [line.number for line in window.lines if line.marked] == [6, 7, 8]
    assert window.hidden_above == 1  # four lines above the first range, which starts at 6


def test_per_condition_the_rules_and_the_gaps_among_them_are_counted() -> None:
    from govguard_ui.report.condition_review import rule_counts

    answered = CONSENT_GAP.model_copy(update={"status": "PASS", "line_start": 3, "line_end": 3})

    counts = rule_counts(DEFS, [CONSENT_GAP, answered, TRANSFER_GAP, PLAIN_GAP])

    assert counts == {"consent": (2, 1), "third_country": (1, 1)}


def test_a_derived_no_is_satisfied_by_the_criterion_of_its_source_condition() -> None:
    from govguard_ui.report.condition_review import criterion

    ki = definition("ki").model_copy(update={"no": "Kein KI-System"})
    high = definition("high")
    derived = ConditionResult(value="no", denying=[r((2, 2))], derived_from="ki")
    by_id = {"ki": ki, "high": high}

    assert criterion(high, derived, "denying", by_id) == "Kein KI-System"
    assert criterion(high, ConditionResult(value="yes"), "affirming", by_id) == "Kriterium ja"
