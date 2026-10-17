"""Finding rows as native buttons: a click selects, long titles wrap (#43, ADR 0024)."""

import re

import streamlit as st

from govguard.models import Finding
from govguard_ui.review import SourceGroup, category
from govguard_ui.style import LOOKS
from govguard_ui.texts import SOURCE_NAMES

BADGE_COLOURS = {"FAIL": "red", "WARN": "orange", "GAP": "gray", "PASS": "green", "N/A": "gray"}
MARKDOWN_SIGNS = set("\\`*_{}[]()#+-.!|<>~$:")  # incl. Streamlit's :colour[...] and $formula$
ROWS_HEIGHT = 560  # the list scrolls inside, like the document next to it


def render_rows(findings: list[Finding], key: str, selected: Finding) -> None:
    _mark(key, selected)
    _buttons(findings, key)


def render_groups(groups: list[SourceGroup], key: str, selected: Finding) -> None:
    """Architecture audit: one group per source, the first and the selected one open."""
    _mark(key, selected)
    for index, group in enumerate(groups):
        with st.expander(group_label(group),
                         expanded=index == 0 or selected in group.listed + group.not_applicable):
            _buttons(group.listed, key)
            if group.not_applicable:
                with st.expander(f"{len(group.not_applicable)} × N/A einblenden "
                                 "(nicht anwendbar)", expanded=selected in group.not_applicable):
                    _buttons(group.not_applicable, key)


def group_label(group: SourceGroup) -> str:
    """Name, size and one badge per status that occurs, e.g. ✕ 10 ✓ 8 – 16."""
    badges = " ".join(f":{BADGE_COLOURS[name]}-badge[{LOOKS[name].symbol} {group.counts[name]}]"
                      for name in ("FAIL", "WARN", "PASS", "N/A") if group.counts[name])
    name = SOURCE_NAMES.get(group.source, group.source)
    return f"**{name}** · {sum(group.counts.values())} Befunde · {badges}"


def _mark(key: str, selected: Finding) -> None:
    """Key and type of a row never change: a remounted button would lose the keyboard focus,
    so the selection is marked by CSS only (prototype of #43)."""
    row = css_class(f"{key}_row_{selected.rule_id}")
    st.html(f"<style>.{row} button,.{row} button:hover"  # hover must not hide the selection
            "{background:#E3EEF9;box-shadow:inset 3px 0 0 #0B4F8A}</style>")


def _buttons(findings: list[Finding], key: str) -> None:
    with st.container(gap="xxsmall"):  # rows close together, like a table
        for finding in findings:
            st.button(row_label(finding), key=f"{key}_row_{finding.rule_id}", type="tertiary",
                      width="stretch", wrap=True, on_click=select, args=(key, finding.rule_id))


def select(key: str, rule_id: str | None) -> None:
    st.session_state[f"{key}_selected"] = rule_id


def css_class(widget_key: str) -> str:
    """The class Streamlit gives a widget with a key: "." becomes "-"."""
    return "st-key-" + re.sub(r"[^a-zA-Z0-9_-]", "-", widget_key.strip())


def row_label(finding: Finding) -> str:
    """Badge, title, anchor and lines; title and anchor are LLM text and stay plain text."""
    kind = category(finding)
    status = f"{LOOKS[kind].symbol} {finding.status}"
    if finding.downgraded_from:  # a downgrade stays visible in the list (ADR 0017)
        status += f" ↓ von {finding.downgraded_from}"
    return (f":{BADGE_COLOURS[kind]}-badge[{status}] **{plain(finding.title)}** · "
            f":gray[{plain(finding.primary_anchor)} · Zeilen {lines_text(finding)}]")


def plain(text: str) -> str:
    """Button labels render Markdown with links and images: escape every sign of it."""
    return "".join(f"\\{sign}" if sign in MARKDOWN_SIGNS else sign
                   for sign in " ".join(text.split()))


def lines_text(finding: Finding) -> str:
    if finding.line_start is None:
        return "–"
    if finding.line_start == finding.line_end:
        return str(finding.line_start)
    return f"{finding.line_start}–{finding.line_end}"
