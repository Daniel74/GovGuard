"""Plain values for the measure proposal of one site: button, notice and the block above the
findings (#82). LLM text stays raw, the component sets it as textContent. Pure view logic."""

import hashlib

from govguard.checks.remediation import offers_measures, open_findings
from govguard.checks.remediation_models import Measure
from govguard.checks.sites import Site, Sites
from govguard_ui.report.ai_label import ai_texts

BUTTON = "✦ Maßnahme vorschlagen"
REDO = "✦ neu vorschlagen"
HEADING = "Maßnahmen"
HINT = "KI-Vorschlag · gilt nur für diese Sitzung · Befunde und Dokument bleiben unverändert"
NO_PROPOSAL = ("Kein Vorschlag möglich: Das Sprachmodell hat keine prüfbare Antwort geliefert "
               "oder war nicht erreichbar. Die Befunde darunter bleiben.")

type Proposals = dict[str, list[Measure] | None]  # key of the site -> measures; None: none possible


def notice(model_label: str) -> str:
    """What leaves the app for a proposal; shown in the dialog and under the button."""
    return ("Für den Vorschlag gehen das Dokument und die Befunde dieser Fundstelle an ein "
            f"Sprachmodell (Groq, {model_label}).")


def document_digest(text: str) -> str:
    """The model reads the whole document, so a proposal belongs to exactly this text."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def proposal_basis(site: Site, everything: Sites) -> Site:
    """The site a proposal is made for: the same section with ALL its findings, whatever the
    status or source filter shows (decided for #82). everything: the sites of the whole report,
    same section limits, unfiltered."""
    return next((s for s in everything.placed
                 if (s.line_start, s.line_end) == (site.line_start, site.line_end)), site)


def suggestion_key(site: Site, digest: str) -> str:
    """A proposal belongs to the document, the site and the WARN/FAIL it saw: another audit or a
    changed filter hides it, under "Audit erstellen" the key of the report is always "created"."""
    ids = ",".join(sorted(f.rule_id for f in open_findings(site)))
    return f"{digest}:{site.line_start}-{site.line_end}:{ids}"


def _measure(measure: Measure) -> dict:
    where = (f"Zeile {measure.line_start}" if measure.line_start == measure.line_end
             else f"Zeilen {measure.line_start}–{measure.line_end}")
    n = len(measure.rule_ids)
    content = "\n".join([measure.sentence, where, measure.before, measure.after])
    return {"id": hashlib.sha256(content.encode()).hexdigest()[:12],  # the browser's fold key
            "sentence": measure.sentence, "before": measure.before, "after": measure.after,
            "lines": where, "anchors": measure.anchors,
            "covers": f"deckt {n} {'Befund' if n == 1 else 'Befunde'} ab",
            "rule_ids": measure.rule_ids}  # the box puts the visible findings under the measure


def _block(stored: Proposals, key: str) -> dict | None:
    if key not in stored:
        return None
    measures = stored[key]
    return {"heading": HEADING, "hint": HINT, "failed": measures is None,
            "text": NO_PROPOSAL if measures is None else "",
            "measures": [_measure(m) for m in measures or []],
            "ai": ai_texts()}  # the marker of the AI label, one source with the other views


def suggest_data(site: Site, stored: Proposals, note: str, digest: str) -> dict | None:
    """site: the proposal basis (proposal_basis). None: it has fewer than two WARN/FAIL and
    offers no button. note: the notice, when the session gave the password and no dialog comes,
    else empty."""
    if not offers_measures(site):
        return None
    key = suggestion_key(site, digest)
    return {"label": REDO if key in stored else BUTTON, "note": note, "block": _block(stored, key)}
