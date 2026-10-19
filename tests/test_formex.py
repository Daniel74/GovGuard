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
