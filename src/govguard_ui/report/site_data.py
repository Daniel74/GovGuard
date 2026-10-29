"""Plain values for the document of "nach Fundstelle": bars, lines and the findings behind them.
LLM text stays raw, the component sets it as textContent (#81, #84). Pure view logic, no
Streamlit."""

from collections.abc import Callable

from govguard.checks.sites import Site, Sites
from govguard.models import Finding
from govguard_ui.report.ai_label import ai_texts
from govguard_ui.report.review import category
from govguard_ui.report.site_box import box_parts
from govguard_ui.report.site_lines import line_rows
from govguard_ui.style import LOOKS, status_text


def place(start: int | None, end: int | None) -> str:
    if start is None:
        return "keine Zeilen"
    return f"Zeile {start}" if start == end else f"Zeilen {start}–{end}"


def _finding(finding: Finding) -> dict:
    return {"id": finding.rule_id, "look": LOOKS[category(finding)].css,
            "status": status_text(finding), "title": finding.title,
            "anchor": finding.primary_anchor,
            "lines": place(finding.line_start, finding.last_line),
            "rationale": finding.rationale, "recommendation": finding.recommendation or "",
            "by_code": finding.by_code}  # texts without the "KI" marker (#83)


def _site(site: Site, suggest: Callable[[Site], dict | None], selected: str) -> dict:
    offered = suggest(site)  # button and proposal, None below two WARN/FAIL (#82)
    block = offered and offered["block"]
    measures = [] if not block or block["failed"] else block["measures"]
    where = place(site.line_start, site.line_end)
    mix = " · ".join(f"{LOOKS[s].symbol} {n}" for s, n in site.status_counts)
    counts = ", ".join(f"{n} × {LOOKS[s].label}" for s, n in site.status_counts)
    return {"label": f"{site.name} · {where} · {len(site.findings)} Befunde · {mix}",
            "tip": f"{site.name}, {where}: {counts}. Klick öffnet die Befunde unter dem Abschnitt.",
            "look": LOOKS[site.worst].css, "count": str(len(site.findings)),
            "start": site.line_start, "end": site.line_end,
            "findings": [_finding(f) for f in site.findings],
            **box_parts(site, selected, measures),  # what the box shows where (#86)
            "suggest": offered}


def site_data(
    sites: Sites, text: str, selected: Finding, closed: bool,
    suggest: Callable[[Site], dict | None] = lambda site: None,
) -> dict:
    """closed: the reader closed the box of this selection; it opens again with the next click.
    suggest: the measure proposal of a site (remediation_data.suggest_data, #82)."""
    current = next((i for i, s in enumerate(sites.placed) if selected in s.findings), None)
    span = None if selected.line_start is None else (selected.line_start, selected.last_line)
    rows = line_rows(text, sites.placed, current, span)
    back = None
    if current is None and span:  # over several sections: the way back to its place in the group
        back = {"title": selected.title, "lines": place(*span)}
    return {
        "lines": [{"n": r.number, "text": r.text, "bar": r.bar and r.bar.model_dump(),
                   "tint": r.tint and LOOKS[r.tint].css, "in_site": r.in_site,
                   "in_finding": r.in_finding} for r in rows],
        "sites": [_site(s, suggest, selected.rule_id) for s in sites.placed],
        "current": current, "open": not closed, "selected": selected.rule_id, "back": back,
        "ai": ai_texts(),  # marker and tip of the AI label, one source with the Python views (#83)
    }
