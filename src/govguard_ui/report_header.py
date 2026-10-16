"""Head of a report view: meta, overall status, counters, expected result (#11)."""

import streamlit as st

from govguard.models import AuditReport, Expected
from govguard_ui.review import category_counts, expected_checks
from govguard_ui.style import LOOKS, badge
from govguard_ui.texts import HELP, TYPE_LABELS


def render_header(report: AuditReport, title: str, key: str) -> None:
    meta, overall = st.columns([3, 1])
    with meta:
        st.subheader(title)
        st.caption(f"{TYPE_LABELS[report.audit_type]} · Modell {report.model_id} · "
                   f"{len(report.findings)} Befunde · Retries {report.retries}")
        st.download_button("Report als JSON herunterladen", report.model_dump_json(indent=2),
                           file_name=f"govguard-{report.trace.audit_id[:8]}.json",
                           mime="application/json", key=f"{key}_download")
        with st.expander("Nachvollziehbarkeit (Trace)"):
            trace = report.trace
            st.caption(f"audit_id `{trace.audit_id}`  \ninput_sha256 `{trace.input_sha256}`  \n"
                       f"catalog_sha256 `{trace.catalog_sha256}`  \nkb_commit `{trace.kb_commit}`")
    with overall.container(border=True):
        st.caption("Gesamtstatus", help=HELP["overall"])
        st.html(badge(report.overall_status, big=True))
        st.caption(LOOKS[report.overall_status].word)
    _counters(report)


def _counters(report: AuditReport) -> None:
    counts = category_counts(report.findings)
    downgraded = sum(1 for f in report.findings if f.downgraded_from)
    subs = {"FAIL": "Verstoß belegt", "WARN": f"mit Beleg · davon {downgraded} herabgestuft",
            "PASS": "Einhaltung belegt", "N/A": "nicht anwendbar",
            "GAP": "nicht beschrieben · kein Verstoß"}
    *tiles, judge_tile = st.columns(6)
    for tile, (name, sub) in zip(tiles, subs.items(), strict=True):
        look = LOOKS[name]
        tile.metric(f"{look.symbol} {look.label}", counts[name], help=HELP[name], border=True)
        tile.caption(sub)
    judge = report.fail_judge
    if report.audit_type == "spec":
        judge_tile.metric("FAIL-Prüfer", judge.checked, help=HELP["judge"], border=True)
        judge_tile.caption(f"geprüft · {judge.confirmed} bestätigt · {judge.downgraded} "
                           f"herabgestuft · {judge.unavailable} nicht verfügbar")
    else:
        judge_tile.metric("FAIL-Prüfer", "–", help=HELP["judge"], border=True)
        judge_tile.caption("entfällt · nur bei Spezifikationen")


def render_expected(report: AuditReport, expected: Expected, key: str) -> None:
    """Shown, never re-rolled (ADR 0023); a click on a required finding selects it."""
    checks = expected_checks(report, expected)
    with st.container(border=True):
        if all(check.ok for check in checks):
            st.success("Soll-Abgleich: wie erwartet", icon=":material/check:")
        else:
            st.error("Soll-Abweichung", icon=":material/close:")
        st.caption(HELP["expected"])
        for check in checks:
            st.button(f"{check.label}: Soll {check.expected}, Ist {check.actual}",
                      icon=":material/check:" if check.ok else ":material/close:",
                      type="tertiary", disabled=check.rule_id is None,
                      key=f"{key}_expected_{check.label}",
                      on_click=_select, args=(key, check.rule_id))


def _select(key: str, rule_id: str | None) -> None:
    st.session_state[f"{key}_selected"] = rule_id
