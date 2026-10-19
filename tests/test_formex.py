from kb_build.extract.formex import articles

# Shape of the CELLAR Formex file 02024R1689-20260727: inserted articles, chapters up to XIII
FORMEX = """<?xml version="1.0" encoding="utf-8"?>
<CONS.ACT><CONS.DOC><ENACTING.TERMS>
<DIVISION><TITLE><TI><P>KAPITEL I</P></TI></TITLE>
<ARTICLE IDENTIFIER="004A"><TI.ART>Artikel 4a</TI.ART><STI.ART>Verzerrungen</STI.ART>
<PARAG IDENTIFIER="004A.001"><NO.PARAG>(1)</NO.PARAG><ALINEA>Soweit erforderlich.</ALINEA>
</PARAG></ARTICLE>
</DIVISION>
<DIVISION><TITLE><TI><P>KAPITEL XIII</P></TI></TITLE>
<ARTICLE IDENTIFIER="113"><TI.ART>Artikel 113</TI.ART><STI.ART>Geltungsbeginn</STI.ART>
<ALINEA>Sie gilt ab dem 2. August 2026.</ALINEA></ARTICLE>
</DIVISION>
</ENACTING.TERMS></CONS.DOC></CONS.ACT>""".encode()


def test_inserted_article_keeps_its_letter_without_leading_zeros() -> None:
    first = articles(FORMEX)[0]
    assert (first.number, first.chapter, first.title) == ("4a", 1, "Verzerrungen")
    assert first.text == "(1) Soweit erforderlich."


def test_chapters_reach_xiii() -> None:
    assert [(a.number, a.chapter) for a in articles(FORMEX)] == [("4a", 1), ("113", 13)]


# DSGVO Art. 6 in short: a list with lead-in, a closing subparagraph, a plain paragraph
ART_6 = """<?xml version="1.0" encoding="utf-8"?>
<CONS.ACT><CONS.DOC><ENACTING.TERMS>
<DIVISION><TITLE><TI><P>KAPITEL II</P></TI></TITLE>
<ARTICLE IDENTIFIER="006"><TI.ART>Artikel 6</TI.ART><STI.ART>Rechtmäßigkeit</STI.ART>
<PARAG IDENTIFIER="006.001"><NO.PARAG>(1)</NO.PARAG><ALINEA><P>Rechtmäßig, wenn eine
der nachstehenden Bedingungen erfüllt ist:</P><LIST TYPE="alpha">
<ITEM><NP><NO.P>a)</NO.P><TXT>Einwilligung;</TXT></NP></ITEM>
<ITEM><NP><NO.P>ba)</NO.P><TXT>Vertrag.</TXT></NP></ITEM></LIST></ALINEA>
<ALINEA>Buchstabe f gilt nicht für Behörden.</ALINEA></PARAG>
<PARAG IDENTIFIER="006.002"><NO.PARAG>(2)</NO.PARAG><ALINEA>Die Mitgliedstaaten können.</ALINEA>
</PARAG></ARTICLE>
<ARTICLE IDENTIFIER="011"><TI.ART>Artikel 11</TI.ART><STI.ART>Ohne Absatz</STI.ART>
<ALINEA>Erster Satz.</ALINEA></ARTICLE>
</DIVISION>
</ENACTING.TERMS></CONS.DOC></CONS.ACT>""".encode()


def test_sections_split_paragraphs_list_items_and_subparagraphs() -> None:
    art_6 = articles(ART_6)[0]
    assert [(s.mark, s.text, s.lead_in) for s in art_6.sections] == [
        ("Art. 6 Abs. 1 lit. a", "Einwilligung;",
         "Rechtmäßig, wenn eine der nachstehenden Bedingungen erfüllt ist:"),
        ("Art. 6 Abs. 1 lit. ba", "Vertrag.",
         "Rechtmäßig, wenn eine der nachstehenden Bedingungen erfüllt ist:"),
        ("Art. 6 Abs. 1 UAbs. 2", "Buchstabe f gilt nicht für Behörden.", ""),
        ("Art. 6 Abs. 2", "Die Mitgliedstaaten können.", ""),
    ]


def test_an_article_without_paragraphs_is_one_section() -> None:
    art_11 = articles(ART_6)[1]
    assert [(s.mark, s.text) for s in art_11.sections] == [("Art. 11", "Erster Satz.")]


def test_paragraph_numbers_lose_brackets_and_trailing_dots() -> None:
    art_6 = articles(ART_6.replace(b"(2)", b"(1b.)"))[0]
    assert art_6.sections[-1].mark == "Art. 6 Abs. 1b"
