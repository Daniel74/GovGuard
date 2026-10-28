"""Plain values for the document of "nach Fundstelle": bars, lines and the findings behind them.
LLM text stays raw, the component sets it as textContent (#81). Pure view logic, no Streamlit."""

from govguard.checks.sites import Site, Sites
from govguard.models import Finding
from govguard_ui.report.review import category
from govguard_ui.report.site_lines import line_rows
from govguard_ui.style import LOOKS, status_text


def place(start: int | None, end: int | None) -> str:
    if start is None:
        return "keine Zeilen"
    return f"Zeile {start}" if start == end else f"Zeilen {start}–{end}"


def _finding(finding: Finding) -> dict[str, str]:
    return {"id": finding.rule_id, "look": LOOKS[category(finding)].css,
            "status": status_text(finding), "title": finding.title,
            "anchor": finding.primary_anchor,
            "lines": place(finding.line_start, finding.last_line),
            "rationale": finding.rationale, "recommendation": finding.recommendation or ""}


def _site(site: Site) -> dict:
    where = place(site.line_start, site.line_end)
    mix = " · ".join(f"{LOOKS[s].symbol} {n}" for s, n in site.status_counts)
    counts = ", ".join(f"{n} × {LOOKS[s].label}" for s, n in site.status_counts)
    return {"label": f"{where} · {len(site.findings)} Befunde · {mix}",
            "tip": f"{where}: {counts}. Klick öffnet die Befunde unter der Stelle.",
            "look": LOOKS[site.worst].css, "count": str(len(site.findings)),
            "start": site.line_start, "end": site.line_end,
            "findings": [_finding(f) for f in site.findings]}


def site_data(sites: Sites, text: str, selected: Finding, closed: bool) -> dict:
    """closed: the reader closed the box of this selection; it opens again with the next click."""
    current = next((i for i, s in enumerate(sites.placed) if selected in s.findings), None)
    rows = line_rows(text, sites.placed, current)
    return {
        "lines": [{"n": r.number, "text": r.text, "bars": [b and b.model_dump() for b in r.bars],
                   "owner": r.owner, "tint": r.tint and LOOKS[r.tint].css, "selected": r.selected}
                  for r in rows],
        "lanes": max((len(r.bars) for r in rows), default=0),
        "sites": [_site(s) for s in sites.placed],
        "current": current, "open": not closed, "selected": selected.rule_id,
    }
