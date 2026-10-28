"""What the component of "nach Fundstelle" gets for the measure proposal of a site (#82)."""

from site_factories import finding

from govguard.checks.remediation_models import Measure
from govguard.checks.sites import Site, Sites
from govguard_ui.report.ai_label import ai_texts
from govguard_ui.report.remediation_data import (
    BUTTON,
    REDO,
    document_digest,
    notice,
    proposal_basis,
    suggest_data,
    suggestion_key,
)
from govguard_ui.report.site_data import site_data

TWO = Site(name="Speicher", line_start=2, line_end=9, findings=[
    finding("A", "FAIL", 5, 5), finding("B", "WARN", 6, 6), finding("P", "PASS", 3, 3)])
ONE = Site(name="Speicher", line_start=2, line_end=9, findings=[
    finding("A", "FAIL", 5, 5), finding("P", "PASS", 3, 3), finding("N", "N/A", 4, 4)])
NOTICE = notice("GPT-OSS 120B")
DIGEST = document_digest("das Dokument")
MEASURE = Measure(sentence="Ziel eintragen.", before="  Resource: *", after="  Resource: [ARN]",
                  line_start=5, line_end=6, rule_ids=["A", "B"], anchors=["BSI X", "CIS Y"])


def test_the_button_is_offered_from_two_warn_or_fail_and_only_then() -> None:
    assert suggest_data(ONE, {}, "", DIGEST) is None
    assert suggest_data(TWO, {}, "", DIGEST)["label"] == BUTTON


def test_before_any_proposal_there_is_no_block() -> None:
    assert suggest_data(TWO, {}, "", DIGEST)["block"] is None


def test_a_proposal_shows_its_measures_and_the_button_says_neu_vorschlagen() -> None:
    stored = {suggestion_key(TWO, DIGEST): [MEASURE]}

    data = suggest_data(TWO, stored, "", DIGEST)

    assert data["label"] == REDO
    block = data["block"]
    assert block["failed"] is False
    assert block["measures"] == [{
        "sentence": "Ziel eintragen.", "before": "  Resource: *", "after": "  Resource: [ARN]",
        "lines": "Zeilen 5–6", "anchors": ["BSI X", "CIS Y"]}]
    assert "nur für diese Sitzung" in block["hint"] and "unverändert" in block["hint"]


def test_no_proposal_possible_is_shown_as_such_and_can_be_asked_again() -> None:
    data = suggest_data(TWO, {suggestion_key(TWO, DIGEST): None}, "", DIGEST)

    assert data["label"] == REDO
    assert data["block"]["failed"] is True and "Kein Vorschlag möglich" in data["block"]["text"]


def test_a_confirmed_session_gets_the_notice_under_the_button_instead_of_the_dialog() -> None:
    assert suggest_data(TWO, {}, "", DIGEST)["note"] == ""
    assert suggest_data(TWO, {}, NOTICE, DIGEST)["note"] == NOTICE


def test_the_notice_names_what_leaves_the_app_and_where_it_goes_without_a_cost_hint() -> None:
    assert notice("GPT-OSS 120B") == (
        "Für den Vorschlag gehen das Dokument und die Befunde dieser Fundstelle an ein "
        "Sprachmodell (Groq, GPT-OSS 120B).")


def test_a_proposal_is_for_the_findings_it_saw_a_changed_set_hides_it() -> None:
    stored = {suggestion_key(TWO, DIGEST): [MEASURE]}
    other = Site(name="Speicher", line_start=2, line_end=9, findings=[
        finding("A", "FAIL", 5, 5), finding("C", "WARN", 7, 7)])

    assert suggest_data(TWO, stored, "", DIGEST)["block"] is not None
    assert suggest_data(other, stored, "", DIGEST)["block"] is None


def test_a_proposal_belongs_to_the_document_it_saw_a_new_audit_never_shows_an_old_one() -> None:
    """Under "Audit erstellen" the key of the report is always "created" (#82 review)."""
    stored = {suggestion_key(TWO, DIGEST): [MEASURE]}
    new = document_digest("ein anderes Dokument")

    assert suggestion_key(TWO, new) != suggestion_key(TWO, DIGEST)
    assert suggest_data(TWO, stored, "", new)["block"] is None
    assert suggest_data(TWO, stored, "", DIGEST)["block"] is not None


def test_the_block_carries_the_marker_of_the_ai_label_with_its_tip() -> None:
    block = suggest_data(TWO, {suggestion_key(TWO, DIGEST): [MEASURE]}, "", DIGEST)["block"]

    assert block["ai"] == ai_texts()


def test_llm_text_reaches_the_component_unchanged_it_is_set_as_text() -> None:
    poisoned = MEASURE.model_copy(update={"sentence": "<img src=x onerror=alert(1)>"})

    block = suggest_data(TWO, {suggestion_key(TWO, DIGEST): [poisoned]}, "", DIGEST)["block"]

    assert block["measures"][0]["sentence"] == "<img src=x onerror=alert(1)>"


def test_site_data_puts_the_proposal_into_each_site_and_names_the_marker_of_the_ai_label() -> None:
    from govguard.checks.sites import Sites

    sites = Sites(multi=[], placed=[TWO, ONE], without_lines=[])

    data = site_data(sites, "x\n" * 9, TWO.findings[0], False,
                     suggest=lambda s: suggest_data(s, {}, "", DIGEST))

    assert [s["suggest"] is not None for s in data["sites"]] == [True, False]
    assert data["ai"] == ai_texts()


def test_the_proposal_basis_is_the_same_section_with_all_findings_not_the_filtered_ones() -> None:
    shown = Site(name="Speicher", line_start=2, line_end=9, findings=[TWO.findings[0]])
    elsewhere = Site(name="Danach", line_start=10, line_end=20, findings=[ONE.findings[0]])
    everything = Sites(multi=[], placed=[elsewhere, TWO], without_lines=[])

    assert proposal_basis(shown, everything) is TWO
    assert [f.rule_id for f in proposal_basis(shown, everything).findings] == ["A", "B", "P"]


def test_a_site_unknown_to_the_report_is_its_own_basis() -> None:
    lonely = Site(name="x", line_start=50, line_end=60, findings=[TWO.findings[0]])

    assert proposal_basis(lonely, Sites(multi=[], placed=[TWO], without_lines=[])) is lonely
