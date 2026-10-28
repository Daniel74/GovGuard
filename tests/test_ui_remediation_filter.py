"""The measure proposal belongs to ALL WARN/FAIL of a site, whatever the status or source filter
shows (#82, decided by the product owner)."""

import json

import pytest
from streamlit.testing.v1 import AppTest
from test_ui_remediation import fake_suggest
from ui_helpers import ARCH, gallery_entry

from govguard.checks.remediation import offers_measures, open_findings
from govguard.checks.sections import split_sections
from govguard.checks.sites import group_sites
from govguard_ui.gallery import GalleryEntry
from govguard_ui.screens.password_gate import CONFIRMED

STATUS = "report_status"
PENDING = "report_suggest_pending"


def hooked_script(entry_json: str) -> None:
    from govguard_ui.gallery import GalleryEntry
    from govguard_ui.report.report_view import render_report
    from govguard_ui.screens.measure_runner import proposer

    entry = GalleryEntry.model_validate_json(entry_json)
    render_report(entry.report, entry.preset.title, (entry.source_name, entry.source_text),
                  None, key="report", propose=proposer())


def one_fail_one_warn() -> tuple[GalleryEntry, list[str], tuple[int, int]]:
    """The preset with one site that holds exactly 1 FAIL and 1 WARN (the rest PASS)."""
    entry = gallery_entry(ARCH)
    sections = split_sections(entry.source_name, entry.source_text)
    site = next(s for s in group_sites(entry.report.findings, sections).placed
                if offers_measures(s))
    ids = [f.rule_id for f in open_findings(site)]
    status = {rule_id: "FAIL" if n == 0 else "WARN" if n == 1 else "PASS"
              for n, rule_id in enumerate(ids)}
    findings = [f.model_copy(update={"status": status.get(f.rule_id, f.status)})
                for f in entry.report.findings]
    report = entry.report.model_copy(update={"findings": findings})
    return entry.model_copy(update={"report": report}), ids[:2], (site.line_start, site.line_end)


def open_report() -> tuple[AppTest, list[str], tuple[int, int]]:
    entry, ids, span = one_fail_one_warn()
    app = AppTest.from_function(hooked_script, args=(entry.model_dump_json(),),
                                default_timeout=30)
    app.session_state[CONFIRMED] = True
    return app.run(), ids, span


def site_at(app: AppTest, span: tuple[int, int]) -> dict | None:
    [data] = [json.loads(n.proto.json) for n in app.get("bidi_component")
              if "sites" in json.loads(n.proto.json)]
    return next((s for s in data["sites"] if (s["start"], s["end"]) == span), None)


def index_of(app: AppTest, span: tuple[int, int]) -> int:
    [data] = [json.loads(n.proto.json) for n in app.get("bidi_component")
              if "sites" in json.loads(n.proto.json)]
    return next(i for i, s in enumerate(data["sites"]) if (s["start"], s["end"]) == span)


def test_under_the_filter_fail_the_button_stays_for_one_fail_and_one_warn() -> None:
    app, _, span = open_report()
    assert site_at(app, span)["suggest"]

    app.pills(key=STATUS).set_value(["FAIL"]).run()

    shown = site_at(app, span)
    assert [f["look"] for f in shown["findings"]] == ["fail"]  # the WARN is hidden
    assert shown["suggest"]["label"] == "✦ Maßnahme vorschlagen"


def test_the_model_gets_both_findings_although_the_filter_shows_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = fake_suggest(monkeypatch)
    app, ids, span = open_report()
    app.pills(key=STATUS).set_value(["FAIL"]).run()

    app.session_state[PENDING] = index_of(app, span)
    app.run()

    [(site, _)] = calls
    assert [f.rule_id for f in open_findings(site)] == ids
    assert (site.line_start, site.line_end) == span


def test_the_proposal_stays_the_same_when_the_filter_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = fake_suggest(monkeypatch)
    app, _, span = open_report()
    app.pills(key=STATUS).set_value(["FAIL"]).run()
    app.session_state[PENDING] = index_of(app, span)
    app.run()
    asked = site_at(app, span)["suggest"]["block"]

    app.pills(key=STATUS).set_value(["FAIL", "WARN", "PASS"]).run()
    assert site_at(app, span)["suggest"]["block"] == asked
    app.pills(key=STATUS).set_value(["WARN"]).run()

    assert site_at(app, span)["suggest"]["block"] == asked
    assert len(calls) == 1
