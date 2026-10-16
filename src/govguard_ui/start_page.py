"""Page "Start & Hilfe": what GovGuard does, data warning, how to read a report (#11)."""

import streamlit as st

from govguard.audit_engine import MAX_INPUT_CHARS, with_thousand_dots
from govguard_ui import navigation
from govguard_ui.review import CATEGORIES, Category
from govguard_ui.style import CSS, LOOKS, badge
from govguard_ui.texts import DATA_FLOW_US, DATA_RULE

INTRO = ("GovGuard prüft Spezifikationen gegen DSGVO und das Standard-Datenschutzmodell (SDM) und "
         "AWS-Architekturen gegen BSI IT-Grundschutz, BSI C5, CIS und AWS FSBP. Für jede "
         "Prüfregel des Katalogs liefert ein Sprachmodell einen Befund mit Beleg aus der Eingabe; "
         "der Code prüft jeden Befund nach und korrigiert ihn, wo nötig. Das Ergebnis ist ein "
         "Audit-Report mit PASS, WARN, FAIL oder N/A je Prüfregel.")
STEPS = f"""1. Audit-Art wählen: **Spezifikation** (Fachkonzept, OpenAPI) oder **Architektur**
   (CloudFormation-JSON, Terraform oder Freitext).
2. Preset laden oder eigenen Text einfügen, höchstens {with_thousand_dots(MAX_INPUT_CHARS)} Zeichen.
3. Passwort eingeben und „Audit starten“ wählen. Ein Audit dauert 20 bis 60 Sekunden.
4. Report lesen und bei Bedarf als JSON herunterladen. Er bleibt nur in dieser Sitzung."""
GALLERY = "  \n".join([  # one sentence per line (#41)
    "Die Galerie zeigt Presets, also fiktive Beispiel-Eingaben mit festgelegtem Soll-Ergebnis.",
    "Links steht die Befundliste, rechts das geprüfte Dokument.",
    "Wählen Sie einen Befund, dann springt das Dokument zu seinen Belegzeilen: Es beginnt wenige "
    "Zeilen darüber und markiert sie blau.",
    "„Ganzes Dokument“ zeigt alle Zeilen.",
])
TERMS = {
    "Beleg": "Die Zeilen der Eingabe, auf die sich der Befund stützt, z. B. „Zeilen 46–49“. Im "
             "Dokument sind sie blau markiert.",
    "↓ herabgestuft von FAIL": "Der FAIL-Prüfer, ein zweiter Modellaufruf, hat das FAIL nicht "
                               "bestätigt. Der Befund steht deshalb als WARN im Report.",
    "Warum so viele Lücken?": "GovGuard prüft jede Prüfregel des Katalogs. Eine Spezifikation "
                              "ist eine offene Welt: Was sie nicht erwähnt, ist kein Verstoß, "
                              "sondern eine Lücke.",
    "Korrektur": "Lesbarer Grund, warum der Code in die KI-Antwort eingegriffen hat: Retry, "
                 "Herabstufung, Reparatur aus der Prüfregel oder Urteil des FAIL-Prüfers.",
    "Primäranker": "Die Norm, aus der die Prüfregel stammt, z. B. „DSGVO Art. 9“ oder "
                 "„BSI GS++ BER.4.1“.",
    "Soll-Abweichung": "Nur bei Presets: Gesamtstatus oder ein Pflichtbefund weicht vom "
                       "festgelegten Soll ab. GovGuard zeigt das offen, statt neu zu würfeln.",
}


def render() -> None:
    st.html(CSS)
    st.title("GovGuard – Compliance Copilot für Behörden-IT")
    st.markdown(INTRO)
    st.warning(f"**{DATA_RULE}**  \n{DATA_FLOW_US} Alle Beispiele in GovGuard sind erfunden.",
               icon=":material/warning:")
    left, right = st.columns(2)
    with left.container(border=True, height="stretch"):  # both cards as high as the taller
        st.subheader("Audit erstellen")
        st.markdown(STEPS)
        if st.button("Zu „Audit erstellen“", type="primary", key="to_create"):
            st.switch_page(navigation.create())
    with right.container(border=True, height="stretch"):
        st.subheader("Gespeicherte Audits ansehen")
        st.markdown(GALLERY)
        if st.button("Zu „Audits ansehen“", key="to_gallery"):
            st.switch_page(navigation.gallery())
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
            f"<th>Bedeutung</th><th>Was ist zu tun?</th></tr>{rows}</table></div>")


def _status_row(category: Category) -> str:
    look = LOOKS[category]
    return f"<tr><td>{badge(category)}</td><td>{look.meaning}</td><td>{look.todo}</td></tr>"
