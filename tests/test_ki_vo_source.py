import io
import zipfile

from kb_build.extract.ki_vo import KEPT, PREFILTER_REASON, extract

# Shape of the CELLAR Formex ZIP 02024R1689-20260727: bibliographic file plus the act (ADR 0008)
ACT = """<?xml version="1.0" encoding="utf-8"?>
<CONS.ACT><CONS.DOC><ENACTING.TERMS>
<DIVISION><TITLE><TI><P>KAPITEL I</P></TI></TITLE>
<ARTICLE IDENTIFIER="003"><TI.ART>Artikel 3</TI.ART><STI.ART>Begriffsbestimmungen</STI.ART>
<ALINEA>Für die Zwecke dieser Verordnung bezeichnet der Ausdruck:</ALINEA></ARTICLE>
</DIVISION>
<DIVISION><TITLE><TI><P>KAPITEL IV</P></TI></TITLE>
<ARTICLE IDENTIFIER="050"><TI.ART>Artikel 50</TI.ART><STI.ART>Transparenzpflichten</STI.ART>
<PARAG IDENTIFIER="050.001"><NO.PARAG>(1)</NO.PARAG><ALINEA>Die Anbieter stellen sicher, dass
die natürlichen Personen informiert werden.</ALINEA></PARAG></ARTICLE>
</DIVISION>
</ENACTING.TERMS></CONS.DOC></CONS.ACT>"""


def archive() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("CL2024R1689DE0010020.0001.doc.xml", "<DOC/>")
        zf.writestr("CL2024R1689DE0010020.0001.xml", ACT)
    return buffer.getvalue()


def extract_by_id() -> dict:
    source = extract("memory://ki-vo.zip", archive(), "001.002.0")
    assert source.source == "KI-VO"
    return {r.id: r for r in source.requirements}


def test_art_50_is_read_from_the_act_inside_the_zip() -> None:
    art = extract_by_id()["Art. 50"]
    assert art.title == "Transparenzpflichten"
    assert art.text == (
        "(1) Die Anbieter stellen sicher, dass die natürlichen Personen informiert werden.")
    assert art.primary_anchor == "KI-VO Art. 50"
    assert art.attributes == {"chapter": 4}


def test_prefilter_keeps_only_the_slim_selection_with_a_fixed_reason() -> None:
    reqs = extract_by_id()
    assert reqs["Art. 50"].prefilter_passed
    assert not reqs["Art. 3"].prefilter_passed
    assert reqs["Art. 3"].prefilter_reason == PREFILTER_REASON
    # the reason is in the checked-in selection protocol: its wording must not drift
    assert PREFILTER_REASON == (
        "Artikel gehört nicht zur Auswahl Art. 4, 5, 6, 13, 14, 26, 27 und 50 (#52)."
    )


def test_kept_articles_are_pinned_to_issue_52() -> None:
    # Changing this set changes the catalog: update SPEC.md and ADR 0025 first.
    assert KEPT == {"4", "5", "6", "13", "14", "26", "27", "50"}


def test_requirement_carries_the_sections_of_its_article() -> None:
    [section] = extract_by_id()["Art. 50"].sections
    assert section.mark == "Art. 50 Abs. 1"
