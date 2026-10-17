"""Finding table of both audit types: plain rows, a click selects (#43, #45)."""

from functools import partial

import streamlit as st

from govguard.models import Finding
from govguard_ui.finding_table import render_table
from govguard_ui.review import category
from govguard_ui.style import LOOKS


def render_rows(findings: list[Finding], key: str, selected: Finding) -> None:
    render_table(table_rows(findings), selected.rule_id, f"{key}_table",
                 on_select=partial(select, key))


def select(key: str, rule_id: str | None) -> None:
    st.session_state[f"{key}_selected"] = rule_id


def table_rows(findings: list[Finding]) -> list[dict[str, str]]:
    """Plain values for the finding table; LLM text stays raw, the cell sets it as textContent."""
    return [{"id": f.rule_id, "look": LOOKS[category(f)].css, "status": status_text(f),
             "title": f.title, "primary_anchor": f.primary_anchor, "lines": lines_text(f)}
            for f in findings]


def status_text(finding: Finding) -> str:
    status = f"{LOOKS[category(finding)].symbol} {finding.status}"
    if finding.downgraded_from:  # a downgrade stays visible in the list (ADR 0017)
        status += f" ↓ von {finding.downgraded_from}"
    return status


def lines_text(finding: Finding) -> str:
    if finding.line_start is None:
        return "–"
    if finding.line_start == finding.line_end:
        return str(finding.line_start)
    return f"{finding.line_start}–{finding.line_end}"
