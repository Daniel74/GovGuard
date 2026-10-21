import pytest

from kb_build.extract.dsgvo import CHAPTERS, extract

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
    # Changing this set changes the rule, not just the code: update DESIGN 1.1 first.
    assert CHAPTERS == {2, 3, 4, 5}


@pytest.mark.parametrize(
    ("article", "tier"),
    [(5, 4), (9, 4), (17, 4), (44, 4), (58, 4), (8, 2), (32, 2), (41, 2), (43, 2), (1, 0), (50, 0)],
)
def test_fine_tier_follows_art_83_paragraphs_4_and_5(article: int, tier: int) -> None:
    xml = FORMEX.replace(b'"032"', f'"{article:03d}"'.encode())
    reqs = {r.id: r for r in extract("memory://dsgvo.xml", xml, "000.003").requirements}
    assert reqs[f"Art. {article}"].attributes["fine_tier"] == tier


def test_prefilter_reason_names_the_chapter_rule() -> None:
    reqs = extract_by_id()
    assert reqs["Art. 4"].prefilter_reason == "Kapitel gehört nicht zu II–V (Art. 5–49)."
    assert reqs["Art. 32"].prefilter_reason is None


def test_requirement_carries_the_sections_of_its_article() -> None:
    [section] = extract_by_id()["Art. 32"].sections
    assert section.mark == "Art. 32 Abs. 1 lit. a"
    assert section.lead_in == "Diese Maßnahmen schließen ein:"


@pytest.mark.parametrize("article", [20, 27, 41, 47])
def test_prefilter_rejects_articles_that_never_apply_to_an_authority(article: int) -> None:
    # DSGVO Art. 20(3), Art. 27 (controllers outside the EU), Art. 41(6), Art. 47 (#59)
    xml = FORMEX.replace(b'"032"', f'"{article:03d}"'.encode())
    req = {r.id: r for r in extract("memory://dsgvo.xml", xml, "000.003").requirements}[
        f"Art. {article}"]
    assert not req.prefilter_passed
    assert req.prefilter_reason
    assert f"Art. {article}" in req.prefilter_reason
    assert "Kapitel" not in req.prefilter_reason


@pytest.mark.parametrize("article", [19, 21, 26, 28, 40, 42, 46, 48])
def test_prefilter_keeps_neighbours_of_the_rejected_articles(article: int) -> None:
    xml = FORMEX.replace(b'"032"', f'"{article:03d}"'.encode())
    reqs = {r.id: r for r in extract("memory://dsgvo.xml", xml, "000.003").requirements}
    assert reqs[f"Art. {article}"].prefilter_passed is True
