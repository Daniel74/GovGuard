"""Page "Start & Hilfe": what GovGuard does, data warning, how to read a report (#11)."""

import streamlit as st

from govguard.audit_engine import MAX_INPUT_CHARS, with_thousand_dots
from govguard_ui.review import CATEGORIES, Category
from govguard_ui.style import CSS, JUDGE_NAME, LOOKS, badge
from govguard_ui.texts import DATA_RULE

INTRO = "\n".join(f"- {sentence}" for sentence in [  # one per item: spacing like the steps
    "GovGuard prüft Spezifikationen gegen DSGVO und das Standard-Datenschutzmodell (SDM).",
    "AWS-Architekturen prüft es gegen BSI IT-Grundschutz, BSI C5, CIS und AWS FSBP.",
    "Für jede Prüfregel des Katalogs liefert ein Sprachmodell einen Befund mit Beleg aus der "
    "Eingabe.",
    "Der Code prüft jeden Befund nach und korrigiert ihn, wo nötig.",
    "Das Ergebnis ist ein Audit-Report mit einem Status je Prüfregel, z. B. "
    f"„{LOOKS['FAIL'].label}“ oder „{LOOKS['WARN'].label}“.",
])
STEPS = f"""1. Audit-Art wählen: **Spezifikation** (Fachkonzept, OpenAPI) oder **Architektur**
   (CloudFormation-JSON, Terraform oder Freitext).
2. Musterfall laden oder eigenen Text einfügen,
   höchstens {with_thousand_dots(MAX_INPUT_CHARS)} Zeichen.
3. Passwort eingeben und „Audit starten“ wählen. Ein Audit dauert 20 bis 60 Sekunden.
4. Report lesen und bei Bedarf als JSON herunterladen. Er bleibt nur in dieser Sitzung."""
GALLERY = "\n".join(f"- {sentence}" for sentence in [  # one per item (#41, #51)
    "Die Galerie zeigt Musterfälle, also fiktive Beispiel-Eingaben mit festgelegtem "
    "Soll-Ergebnis.",
    "Links steht die Befundliste, rechts das geprüfte Dokument.",
    "Wählen Sie einen Befund, dann springt das Dokument zu seinen Belegzeilen: Es beginnt wenige "
    "Zeilen darüber und markiert sie blau.",
    "„Ganzes Dokument“ zeigt alle Zeilen.",
])
TERMS = {
    "Beleg": "Die Zeilen der Eingabe, auf die sich der Befund stützt, z. B. „Zeilen 46–49“. Im "
             "Dokument sind sie blau markiert.",
    f"↓ herabgestuft von {LOOKS['FAIL'].label}": f"Der {JUDGE_NAME}, ein zweiter "
                                                 "Modellaufruf, hat den Verstoß nicht "
                                                 "bestätigt. Der Befund steht deshalb auf "
                                                 f"{LOOKS['WARN'].label}.",
    "Warum so viele Lücken?": "GovGuard prüft jede Prüfregel des Katalogs. Eine Spezifikation "
                              "ist eine offene Welt: Was sie nicht erwähnt, ist kein Verstoß, "
                              "sondern eine Lücke.",
    "Korrektur": "Lesbarer Grund, warum der Code in die KI-Antwort eingegriffen hat: Retry, "
                 f"Herabstufung, Reparatur aus der Prüfregel oder Urteil durch den {JUDGE_NAME}.",
    "Primäranker": "Die Norm, aus der die Prüfregel stammt, z. B. „DSGVO Art. 9“ oder "
                 "„BSI GS++ BER.4.1“.",
    "Soll-Abweichung": "Nur bei Musterfällen: Gesamtstatus oder ein Pflichtbefund weicht vom "
                       "festgelegten Soll ab. GovGuard zeigt das offen, statt neu zu würfeln.",
}


def render() -> None:
    st.html(CSS)
    st.title("GovGuard – Prüfassistent für Behörden-IT")
    with st.container(border=True):
        st.markdown(INTRO)
    st.warning(f"**{DATA_RULE}**  \nAlle Beispiele in GovGuard sind erfunden.",
               icon=":material/warning:")
    left, right = st.columns(2)
    with left.container(border=True, height="stretch"):  # both cards as high as the taller
        st.subheader("Audit erstellen")
        st.markdown(STEPS)
    with right.container(border=True, height="stretch"):
        st.subheader("Gespeicherte Audits ansehen")
        st.markdown(GALLERY)
    st.header("So lesen Sie einen Audit-Report")
    st.html(_status_table())
    terms = list(TERMS.items())
    for row in (terms[:3], terms[3:]):  # two rows, so cards of one row are equally high
        for column, (term, text) in zip(st.columns(3), row, strict=True):
            with column.container(border=True, height="stretch"):
                st.markdown(f"**{term}**  \n{text}")


def _status_table() -> str:
    rows = "".join(_status_row(c) for c in CATEGORIES)
    return ('<div class="gg-frame"><table class="gg-table"><tr><th>Status</th>'
            "<th>Kürzel im JSON</th><th>Bedeutung</th><th>Was ist zu tun?</th></tr>"
            f"{rows}</table></div>")


def _status_row(category: Category) -> str:
    look = LOOKS[category]
    return (f"<tr><td>{badge(category)}</td><td>{look.code}</td><td>{look.meaning}</td>"
            f"<td>{look.todo}</td></tr>")
