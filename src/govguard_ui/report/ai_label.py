"""The one building block of the AI label (#83, KI-VO Art. 50): a grey header line under the
report head and a discreet "KI" next to every label above model text (Begründung, Empfehlung).
The component in site_script cannot import Python: it gets the texts and the style from here."""

import html

MARKER = "KI"
TIP = "vom Sprachmodell geschrieben"
MARKER_CSS = ("font-size:11px;font-weight:600;color:#4A5361;border:1px solid #A7AFBA;"
              "border-radius:4px;padding:0 4px")  # grey, small; also the .ai class of the component


def disclosure_line(model_id: str) -> str:
    return (f"Mit KI erstellt · Modell {model_id} · "
            "Status, Fundstellen und Zitate hat der Code nachgeprüft")


def disclosure_html(model_id: str) -> str:
    return (f'<p style="color:#4A5361;font-size:13px;margin:4px 0 0">'
            f"{html.escape(disclosure_line(model_id))}</p>")


def marker() -> str:
    return f'<span title="{TIP}" style="{MARKER_CSS}">{MARKER}</span>'


def ai_label(name: str, by_code: bool = False) -> str:
    """Label above model text, e.g. "Begründung": its name, then the marker. A text the code
    wrote itself (by_code, e.g. N/A by code) gets the label without the marker."""
    return f"<strong>{html.escape(name)}</strong>" + ("" if by_code else f" {marker()}")


def ai_texts() -> dict[str, str]:
    """For the component: it builds the marker itself, with textContent."""
    return {"marker": MARKER, "tip": TIP}
