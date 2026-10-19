"""Status words of the UI: German on screen, the JSON report keeps its codes (#51)."""

from pathlib import Path

from govguard_ui.style import LOOKS, badge, status_word


def test_the_ui_shows_german_status_words() -> None:
    assert {category: look.label for category, look in LOOKS.items()} == {
        "FAIL": "Verstoß belegt", "WARN": "Prüfbedarf", "GAP": "Lücke",
        "PASS": "Einhaltung belegt", "N/A": "Nicht anwendbar"}


def test_each_look_names_its_status_in_the_json_report() -> None:
    assert {category: look.code for category, look in LOOKS.items()} == {
        "FAIL": "FAIL", "WARN": "WARN", "GAP": "WARN ohne Belegzeilen",
        "PASS": "PASS", "N/A": "N/A"}


def test_a_badge_shows_symbol_and_german_word() -> None:
    assert badge("FAIL") == '<span class="gg-badge gg-fail">✕ Verstoß belegt</span>'


def test_a_status_reads_german_and_other_words_stay() -> None:
    assert status_word("PASS") == "Einhaltung belegt"
    assert status_word("fehlt") == "fehlt"  # the anchor has no finding in the report


def test_the_spec_names_every_status_word_and_its_code_in_g2() -> None:
    """SPEC.md is the input of the self-audit: it must say what the UI shows (#36)."""
    spec = (Path(__file__).parents[1] / "docs/SPEC.md").read_text(encoding="utf-8")
    g2 = spec[spec.index("### G2"):spec.index("### G3")]

    assert [look.label for look in LOOKS.values() if look.label not in g2] == []
    assert [look.code for look in LOOKS.values() if look.code not in g2] == []
