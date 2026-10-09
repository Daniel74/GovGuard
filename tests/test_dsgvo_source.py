import pytest

from kb_build.sources.dsgvo import CHAPTERS, extract

# Shape of the CELLAR Formex file 02016R0679-20160504 (fragment, ADR 0008)
FORMEX = """<?xml version="1.0" encoding="utf-8"?>
<CONS.ACT><CONS.DOC><ENACTING.TERMS>
<DIVISION><TITLE><TI><P>KAPITEL I</P></TI><STI><P>Allgemeine Bestimmungen</P></STI></TITLE>
<ARTICLE IDENTIFIER="004"><TI.ART>Artikel 4</TI.ART><STI.ART>Begriffsbestimmungen</STI.ART>
<ALINEA>Im Sinne dieser Verordnung bezeichnet der Ausdruck:</ALINEA></ARTICLE>
</DIVISION>
<DIVISION><TITLE><TI><P>KAPITEL IV</P></TI><STI><P>Verantwortlicher</P></STI></TITLE>
<DIVISION><TITLE><TI><P>Abschnitt 2</P></TI></TITLE>
<ARTICLE IDENTIFIER="032"><TI.ART>Artikel 32</TI.ART><STI.ART>Sicherheit der Verarbeitung</STI.ART>
<PARAG IDENTIFIER="032.001"><NO.PARAG>(1)</NO.PARAG><ALINEA><P>Diese Maßnahmen<?PAGE NO='52'?>
schließen ein:</P><LIST TYPE="alpha"><ITEM><NP><NO.P>a)</NO.P><TXT>die Pseudonymisierung
(<QUOT.START CODE="201E"/>Verschlüsselung<QUOT.END CODE="201C"/>);</TXT></NP></ITEM></LIST>
</ALINEA></PARAG></ARTICLE>
</DIVISION></DIVISION>
</ENACTING.TERMS></CONS.DOC></CONS.ACT>""".encode()


def extract_by_id() -> dict:
    return {r.id: r for r in extract("memory://dsgvo.xml", FORMEX, "000.003").requirements}


def test_art_32_has_heading_text_and_anchor() -> None:
    art = extract_by_id()["Art. 32"]
    assert art.title == "Sicherheit der Verarbeitung"
    assert art.text == (
        '(1) Diese Maßnahmen schließen ein: a) die Pseudonymisierung ("Verschlüsselung");'
    )
    assert art.primary_anchor == "DSGVO Art. 32"


def test_processing_instructions_leave_no_trace() -> None:
    assert "PAGE" not in extract_by_id()["Art. 32"].text


def test_chapter_comes_from_division_and_drives_prefilter() -> None:
    reqs = extract_by_id()
    assert reqs["Art. 4"].attributes["chapter"] == 1
    assert reqs["Art. 32"].attributes["chapter"] == 4
    assert not reqs["Art. 4"].prefilter_passed
    assert reqs["Art. 32"].prefilter_passed


def test_chapters_are_pinned_to_architecture_1_1() -> None:
    # Changing this set changes the rule, not just the code: update ARCHITECTURE 1.1 first.
    assert CHAPTERS == {2, 3, 4, 5}


@pytest.mark.parametrize(
    ("article", "tier"),
    [(5, 4), (9, 4), (17, 4), (44, 4), (58, 4), (8, 2), (32, 2), (41, 2), (43, 2), (1, 0), (50, 0)],
)
def test_fine_tier_follows_art_83_paragraphs_4_and_5(article: int, tier: int) -> None:
    xml = FORMEX.replace(b'"032"', f'"{article:03d}"'.encode())
    reqs = {r.id: r for r in extract("memory://dsgvo.xml", xml, "000.003").requirements}
    assert reqs[f"Art. {article}"].attributes["fine_tier"] == tier
