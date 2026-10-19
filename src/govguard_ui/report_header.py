"""Head of a report view: meta, overall status, counters, expected result (#11)."""

import html

import streamlit as st

from govguard.models import AuditReport, Expected
from govguard_ui.finding_list import select
from govguard_ui.review import Category, category_counts, expected_checks
from govguard_ui.style import JUDGE_NAME, LOOKS, status_word
from govguard_ui.texts import HELP, OPEN_WORLD_ONLY, TYPE_LABELS

TILES: tuple[Category, ...] = ("FAIL", "WARN", "PASS", "N/A", "GAP")  # gaps last (design)
TILE_LABELS = {"GAP": "Lücken"}  # plural, the tile counts


def render_header(report: AuditReport, title: str, key: str) -> None:
    """One frame: title, meta, download and overall status; the trace stays in the JSON."""
    with st.container(border=True):
        meta, overall = st.columns([3, 1])
        with meta:
            st.subheader(title)
            st.html(_meta_table(report))
            st.download_button("Report als JSON herunterladen", report.model_dump_json(indent=2),
                               file_name=f"govguard-{report.trace.audit_id[:8]}.json",
                               mime="application/json", key=f"{key}_download")
        look = LOOKS[report.overall_status]
        with overall.container(border=True, key=f"{key}_overall_{look.css}"):
            st.markdown("Gesamtstatus", help=HELP["overall"])
            st.html(f'<p class="gg-overall">{look.symbol} {look.label}</p>')
    _counters(report, key)


def _meta_table(report: AuditReport) -> str:
    rows = {"Audit-Art": TYPE_LABELS[report.audit_type], "Modell": report.model_id,
            "Retries": str(report.retries)}
    cells = "".join(f"<tr><th>{term}</th><td>{html.escape(value)}</td></tr>"
                    for term, value in rows.items())
    return f'<table class="gg-meta">{cells}</table>'


def _counters(report: AuditReport, key: str) -> None:
    """One frame per tile, the explanation inside; the key lets CSS colour it (#42)."""
    counts = category_counts(report.findings)
    downgraded = sum(1 for f in report.findings if f.downgraded_from)
    words = {  # FAIL and PASS: "belegt" says it all (#51)
        "WARN": f"mit Beleg · davon {downgraded} herabgestuft" if downgraded else "mit Beleg",
        "N/A": "Regel betrifft das Vorhaben nicht", "GAP": "nicht beschrieben · kein Verstoß"}
    if report.audit_type == "architecture":
        words["N/A"] = "AWS-Dienst der Regel kommt nicht vor"
    shown = [name for name in TILES if name != "GAP" or counts["GAP"]]  # design: no empty gaps
    *tiles, judge_tile = st.columns(len(shown) + 1)
    for tile, name in zip(tiles, shown, strict=True):
        look = LOOKS[name]
        with tile.container(border=True, height="stretch", key=f"{key}_tile_{look.css}"):
            st.metric(f"{look.symbol} {TILE_LABELS.get(name, look.label)}", counts[name],
                      help=look.meaning)
            if name in words:
                st.caption(words[name])
    with judge_tile.container(border=True, height="stretch", key=f"{key}_tile_judge"):
        _judge(report)


def _judge(report: AuditReport) -> None:
    judge = report.fail_judge
    if report.closed_world:  # a template: a missing setting is the default (ADR 0020, #46)
        st.metric(JUDGE_NAME, "entfällt", help=HELP["judge"])
        st.caption(OPEN_WORLD_ONLY)
    else:
        st.metric(JUDGE_NAME, judge.checked, help=HELP["judge"])
        st.caption(f"geprüft · {judge.confirmed} bestätigt · {judge.downgraded} "
                   f"herabgestuft · {judge.unavailable} nicht verfügbar")


def render_expected(report: AuditReport, expected: Expected, key: str) -> None:
    """Shown, never re-rolled (ADR 0023); a click on a required finding selects it."""
    overall, *required = expected_checks(report, expected)
    ok = all(check.ok for check in (overall, *required))
    with st.container(border=True, horizontal=True, vertical_alignment="center",
                      key=f"{key}_expected_{LOOKS['PASS' if ok else 'FAIL'].css}"):
        st.markdown(f"**{'Soll-Abgleich: wie erwartet' if ok else 'Soll-Abweichung'}**",
                    help=HELP["expected"], width="content")
        st.markdown(f"{'✓' if overall.ok else '✕'} Gesamtstatus Soll "
                    f"{status_word(overall.expected)}, Ist {status_word(overall.actual)}",
                    width="content")
        for check in required:  # a link look: a click selects the finding
            st.button(f"{check.label}: Soll {status_word(check.expected)}, "
                      f"Ist {status_word(check.actual)}",
                      icon=":material/check:" if check.ok else ":material/close:",
                      type="tertiary", disabled=check.rule_id is None,
                      key=f"{key}_required_{check.label}",
                      on_click=select, args=(key, check.rule_id))
