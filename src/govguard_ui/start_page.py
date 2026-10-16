"""Page "Start & Hilfe": what GovGuard does, data warning, how to read a report (#11)."""

import streamlit as st

from govguard_ui.review import CATEGORIES
from govguard_ui.style import CSS, badge
from govguard_ui.texts import DATA_WARNING

INTRO = ("GovGuard prüft Spezifikationen gegen DSGVO und das Standard-Datenschutzmodell (SDM) und "
         "AWS-Architekturen gegen BSI IT-Grundschutz, BSI C5, CIS und AWS FSBP. Für jede "
         "Prüfregel des Katalogs liefert ein Sprachmodell einen Befund mit Beleg aus der Eingabe; "
         "der Code prüft jeden Befund nach und korrigiert ihn, wo nötig. Das Ergebnis ist ein "
         "Audit-Report mit PASS, WARN, FAIL oder N/A je Prüfregel.")
STEPS = """1. Audit-Typ wählen: **Spezifikation** (Fachkonzept, OpenAPI) oder **Architektur**
   (CloudFormation-JSON, Terraform oder Freitext).
2. Preset laden oder eigenen Text einfügen, höchstens 100.000 Zeichen.
3. Passwort eingeben und „Audit starten“ wählen. Ein Audit dauert 20 bis 60 Sekunden.
4. Report lesen und bei Bedarf als JSON herunterladen. Er bleibt nur in dieser Sitzung."""
GALLERY = ("Die Galerie zeigt Presets, also fiktive Beispiel-Eingaben mit festgelegtem "
           "Soll-Ergebnis. Links steht die Befundliste, rechts das geprüfte Dokument. Wählen Sie "
           "einen Befund, dann markiert GovGuard seine Belegzeilen im Dokument.")
MEANING = {  # category -> (meaning, what to do)
    "FAIL": ("Verstoß belegt: Die Belegzeilen zeigen, dass die Anforderung verletzt ist.",
             "Beheben. Die Empfehlung im Befund nennt einen Weg."),
    "WARN": ("Prüfbedarf mit Beleg: Die Zeilen reichen für kein klares Urteil, oder der Code "
             "hat ein PASS oder FAIL herabgestuft.", "Fachlich nachprüfen."),
    "GAP": ("Die Eingabe beschreibt die Anforderung nicht. Kein Verstoß; im Report steht WARN "
            "ohne Belegzeilen.", "Als Checkliste nutzen: vor der Umsetzung klären oder bewusst "
            "ausschließen. Steht unter der Befundliste."),
    "PASS": ("Einhaltung belegt: Die Belegzeilen zeigen, dass die Anforderung erfüllt ist.",
             "Nichts. Der Beleg dient als Nachweis."),
    "N/A": ("Nicht anwendbar, z. B. weil der Ressourcentyp in der Architektur nicht vorkommt.",
            "Nichts. In der Liste standardmäßig ausgeblendet."),
}
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
    "Normanker": "Die Norm, aus der die Prüfregel stammt, z. B. „DSGVO Art. 9“ oder "
                 "„BSI GS++ BER.4.1“.",
    "Soll-Abweichung": "Nur bei Presets: Gesamtstatus oder ein Pflichtbefund weicht vom "
                       "festgelegten Soll ab. GovGuard zeigt das offen, statt neu zu würfeln.",
}


def render() -> None:
    st.html(CSS)
    st.title("GovGuard – Compliance Copilot für Behörden-IT")
    st.markdown(INTRO)
    st.warning(f"**{DATA_WARNING}** Alle Beispiele in GovGuard sind erfunden.", icon="⚠️")
    left, right = st.columns(2)
    with left.container(border=True):
        st.subheader("Audit erstellen")
        st.markdown(STEPS)
    with right.container(border=True):
        st.subheader("Gespeicherte Audits ansehen")
        st.markdown(GALLERY)
    st.header("So lesen Sie einen Audit-Report")
    st.html(_status_table())
    for column, (term, text) in zip(st.columns(3) * 2, TERMS.items(), strict=True):
        with column.container(border=True):
            st.markdown(f"**{term}**  \n{text}")


def _status_table() -> str:
    rows = "".join(f"<tr><td>{badge(c)}</td><td>{MEANING[c][0]}</td><td>{MEANING[c][1]}</td></tr>"
                   for c in CATEGORIES)
    return ('<table class="gg-table"><tr><th>Status</th><th>Bedeutung</th>'
            f"<th>Was ist zu tun?</th></tr>{rows}</table>")
