import pytest

from kb_build.sources.sdm import LAYERS, extract_from_text

# pypdf text of the measure tables (section 5 of each module), cut to the tricky rows
TABLE = """Einleitung mit Verweis im Fließtext
M60.D01 Bitte nicht als Zeile lesen, denn hier fehlt die Tabelle.
Nr. Maßnahme PDCA Gültigkeit
M60.D01 Datenstrukturen und Speicherarten, die das Löschen der
Inhalte einzelner Datenfelder ermöglichen
P, D V1.0
Ebene Systeme
M60.S02 Schreddern zur Vernichtung von Datenträgern jeder Art D V1.0
M50.S08 Mandantentrennung innerhalb einer relationalen
Datenbank
P, D  V1.0
Seite 14
M51.S12 Verwalten von Benutzern für Computer für spezielle
Zwecke (oft „Stand-Alone-Computer“)
 V1.0
M51.P32 Berücksichtigung ggf. der besonderen Anforderungen
im Falle einer Auftragsverarbeitung bei der Maßnahme
M51.P31
P, D, C V1.0
6. Bezug zum Datenschutzmanagement"""


def parse(text: str):
    return extract_from_text("memory://sdm.pdf", text, "V1.0").requirements


def parse_by_id(text: str = TABLE) -> dict:
    return {r.id: r for r in parse(text)}


def test_m60_d01_is_the_table_row_not_the_prose_reference() -> None:
    d01 = parse_by_id()["M60.D01"]
    assert d01.text == (
        "Datenstrukturen und Speicherarten, die das Löschen der "
        "Inhalte einzelner Datenfelder ermöglichen"
    )
    assert d01.title == d01.text
    assert d01.primary_anchor == "SDM Löschen M60.D01"
    assert d01.attributes == {"module": "M60", "layer": "D"}


def test_pdca_and_validity_columns_are_cut_off() -> None:
    reqs = parse_by_id()
    assert reqs["M60.S02"].text == "Schreddern zur Vernichtung von Datenträgern jeder Art"
    assert reqs["M50.S08"].text == "Mandantentrennung innerhalb einer relationalen Datenbank"
    assert reqs["M51.S12"].text.endswith('Zwecke (oft "Stand-Alone-Computer")')


def test_id_reference_on_its_own_line_continues_the_row() -> None:
    reqs = parse_by_id()
    assert list(reqs) == ["M60.D01", "M60.S02", "M50.S08", "M51.S12", "M51.P32"]
    assert reqs["M51.P32"].text.endswith("bei der Maßnahme M51.P31")


def test_prefilter_keeps_data_and_systems_but_not_processes() -> None:
    reqs = parse_by_id()
    assert reqs["M60.S02"].prefilter_passed
    assert not reqs["M51.P32"].prefilter_passed


def test_layers_are_pinned_to_architecture_1_1() -> None:
    # Changing this set changes the rule, not just the code: update ARCHITECTURE 1.1 first.
    assert LAYERS == {"D", "S"}


def test_duplicate_ids_are_rejected() -> None:
    row = "M60.S02 Schreddern D V1.0\n"
    with pytest.raises(ValueError, match="M60.S02"):
        parse("Nr. Maßnahme PDCA Gültigkeit\n" + row + row)


def test_missing_measure_table_fails_loudly() -> None:
    with pytest.raises(ValueError, match="measure table"):
        parse("M60.D01 nur Fließtext")
