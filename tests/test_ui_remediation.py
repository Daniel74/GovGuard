"""Maßnahme vorschlagen in the report "nach Fundstelle": button, password dialog, proposal (#82).

The component cannot be clicked in AppTest: its event `suggest` is replaced by the session value
the callback writes (<key>_suggest_pending). The model call is replaced at its seam
(suggest_measures); its checks and retry are tested in test_remediation_call.py.
"""

import json

import pytest
from streamlit.testing.v1 import AppTest
from ui_helpers import ARCH, create_script, gallery_entry, gallery_script, report_page

from govguard.adapters.groq_services import MissingApiKeyError
from govguard.checks.remediation_models import Measure
from govguard.checks.sites import Site
from govguard_ui.report.remediation_data import document_digest, notice
from govguard_ui.screens.password_gate import CONFIRMED

NOTICE = notice("GPT-OSS 120B")
KEY = f"gallery_{ARCH}"
PENDING = f"{KEY}_suggest_pending"
PASSWORD = f"{KEY}_measure_password"
GO = f"{KEY}_measure_go"


def measure_for(site: Site, sentence: str = "Ziel eintragen.") -> Measure:
    first = site.findings[0]
    return Measure(sentence=sentence, before="alt", after="neu [Bucket-ARN]",
                   line_start=first.line_start, line_end=first.last_line,
                   rule_ids=[f.rule_id for f in site.findings if f.status != "PASS"],
                   anchors=[first.primary_anchor])


def fake_suggest(monkeypatch: pytest.MonkeyPatch, answer: str = "ok") -> list[tuple[Site, str]]:
    """The model call replaced: notes (site, document) and returns one measure, or None."""
    calls: list[tuple[Site, str]] = []

    async def suggest(site: Site, document: str, model: object) -> list[Measure] | None:
        calls.append((site, document))
        return None if answer == "none" else [measure_for(site, f"Antwort {len(calls)}.")]

    monkeypatch.setattr("govguard_ui.screens.measure_runner.suggest_measures", suggest)
    monkeypatch.setattr("govguard_ui.screens.measure_runner.secret",
                        {"APP_PASSWORD": "geheim"}.get)  # a local secrets.toml would win
    monkeypatch.setattr("govguard_ui.screens.measure_runner.groq_model", lambda: object())
    return calls


def gallery(confirmed: bool = False) -> AppTest:
    app = AppTest.from_function(gallery_script, default_timeout=30)
    if confirmed:
        app.session_state[CONFIRMED] = True
    app.run()
    app.selectbox(key="gallery_preset").select(ARCH).run()
    return app


def document(app: AppTest) -> dict:
    [data] = [json.loads(n.proto.json) for n in app.get("bidi_component")
              if "sites" in json.loads(n.proto.json)]
    return data


def offered(app: AppTest) -> list[int]:
    return [i for i, s in enumerate(document(app)["sites"]) if s["suggest"]]


def request(app: AppTest, index: int) -> AppTest:
    app.session_state[PENDING] = index
    return app.run()


def type_password(app: AppTest, password: str) -> AppTest:
    app.text_input(key=PASSWORD).input(password)
    return app.button(key=GO).click().run()


def test_only_sites_with_two_warn_or_fail_offer_the_button_and_the_page_calls_no_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = fake_suggest(monkeypatch)

    app = gallery()

    sites = document(app)["sites"]
    assert offered(app) and len(offered(app)) < len(sites)
    for site in sites:
        open_findings = [f for f in site["findings"] if f["look"] in ("fail", "warn")]
        assert bool(site["suggest"]) == (len(open_findings) >= 2)
    assert calls == []


def test_without_the_password_in_the_session_a_dialog_asks_and_no_model_is_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = fake_suggest(monkeypatch)
    app = gallery()

    request(app, offered(app)[0])

    assert not app.exception
    assert NOTICE in [m.value for m in app.markdown]
    assert app.text_input(key=PASSWORD).value == "" and app.button(key=GO).label == "Vorschlagen"
    assert calls == []


def form_script() -> None:
    """The content of the dialog on its own: AppTest reruns the whole script on a click, a
    dialog only its own function, so the script stands in for the open dialog."""
    from site_factories import finding

    from govguard.checks.sites import Site
    from govguard_ui.screens.measure_runner import password_form

    site = Site(name="s", line_start=1, line_end=3,
                findings=[finding("A", "FAIL", 1, 1), finding("B", "WARN", 2, 2)])
    password_form(site, "eins\nzwei\ndrei", "k")


def open_form(monkeypatch: pytest.MonkeyPatch, secret: str | None = "geheim") -> AppTest:
    """The secret is replaced at the module: AppTest secrets outlive a test and a local
    .streamlit/secrets.toml would win."""
    monkeypatch.setattr("govguard_ui.screens.measure_runner.secret", {"APP_PASSWORD": secret}.get)
    return AppTest.from_function(form_script, default_timeout=30).run()


def submit(app: AppTest, password: str) -> AppTest:
    app.text_input(key="k_measure_password").input(password)
    return app.button(key="k_measure_go").click().run()


def test_a_wrong_password_calls_no_model_and_confirms_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = fake_suggest(monkeypatch)

    app = submit(open_form(monkeypatch), "falsch")

    assert app.error[0].value == "Passwort falsch. Ohne Passwort kein Vorschlag."
    assert calls == [] and CONFIRMED not in app.session_state


@pytest.mark.parametrize("password", ["", "geheim"])
def test_without_a_configured_password_nobody_gets_a_proposal_fail_closed(
    monkeypatch: pytest.MonkeyPatch, password: str,
) -> None:
    calls = fake_suggest(monkeypatch)

    app = submit(open_form(monkeypatch, secret=None), password)

    assert "nicht eingerichtet" in app.error[0].value
    assert calls == [] and CONFIRMED not in app.session_state


def test_the_right_password_confirms_the_session_and_asks_the_model_once_with_the_whole_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = fake_suggest(monkeypatch)

    app = submit(open_form(monkeypatch), "geheim")

    assert not app.exception and app.session_state[CONFIRMED] is True
    [(site, text)] = calls
    assert (site.line_start, site.line_end, text) == (1, 3, "eins\nzwei\ndrei")
    [(key, [measure])] = app.session_state["k_measures"].items()
    assert key == f"{document_digest(text)}:1-3:A,B"
    assert measure.sentence == "Antwort 1."


def test_without_a_groq_key_the_dialog_says_so(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_key() -> object:
        raise MissingApiKeyError("fehlt")

    monkeypatch.setattr("govguard_ui.screens.measure_runner.groq_model", no_key)

    app = submit(open_form(monkeypatch), "geheim")

    assert not app.exception and "GROQ_API_KEY fehlt" in app.error[0].value


def test_a_proposal_shows_in_the_box_and_the_findings_stay_as_they_are(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_suggest(monkeypatch)
    app = gallery(confirmed=True)
    index = offered(app)[0]
    before = document(app)["sites"][index]["findings"]

    request(app, index)

    shown = document(app)["sites"][index]["suggest"]
    assert shown["label"] == "✦ neu vorschlagen" and shown["note"] == NOTICE
    assert [m["sentence"] for m in shown["block"]["measures"]] == ["Antwort 1."]
    assert document(app)["sites"][index]["findings"] == before


def test_a_confirmed_session_gets_no_dialog_the_model_runs_at_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = fake_suggest(monkeypatch)
    app = gallery(confirmed=True)

    request(app, offered(app)[0])

    assert len(calls) == 1 and not app.text_input
    assert document(app)["sites"][offered(app)[0]]["suggest"]["block"]["measures"]


def test_neu_vorschlagen_replaces_the_proposal(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = fake_suggest(monkeypatch)
    app = gallery(confirmed=True)
    index = offered(app)[0]
    request(app, index)

    request(app, index)

    block = document(app)["sites"][index]["suggest"]["block"]
    assert len(calls) == 2 and [m["sentence"] for m in block["measures"]] == ["Antwort 2."]


def test_when_no_proposal_is_possible_the_block_says_so_and_nothing_crashes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_suggest(monkeypatch, "none")
    app = gallery(confirmed=True)

    request(app, offered(app)[0])

    block = document(app)["sites"][offered(app)[0]]["suggest"]["block"]
    assert not app.exception and block["failed"] and "Kein Vorschlag möglich" in block["text"]


def test_a_request_for_a_site_below_two_warn_or_fail_is_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = fake_suggest(monkeypatch)
    app = gallery(confirmed=True)
    other = next(i for i in range(len(document(app)["sites"])) if i not in offered(app))

    request(app, other)

    assert calls == [] and not app.exception


def test_the_proposal_is_for_this_session_a_new_session_starts_without_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_suggest(monkeypatch)
    app = gallery(confirmed=True)
    request(app, offered(app)[0])
    assert any(s["suggest"] and s["suggest"]["block"] for s in document(app)["sites"])

    fresh = gallery()

    assert not any(s["suggest"] and s["suggest"]["block"] for s in document(fresh)["sites"])
    assert CONFIRMED not in fresh.session_state


def created_of(entry) -> dict:
    return {"report": entry.report, "title": entry.preset.title, "seconds": 1,
            "source": (entry.source_name, entry.source_text), "expected": None}


def created_page() -> AppTest:
    """The page "Audit erstellen" with a finished audit and the password given."""
    app = AppTest.from_function(create_script, default_timeout=30)
    app.session_state["created"] = created_of(gallery_entry(ARCH))
    app.session_state[CONFIRMED] = True
    return app.run()


def test_the_report_of_audit_erstellen_offers_it_too(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = fake_suggest(monkeypatch)
    app = created_page()
    index = offered(app)[0]

    app.session_state["created_suggest_pending"] = index
    app.run()

    assert len(calls) == 1
    assert document(app)["sites"][index]["suggest"]["block"]["measures"]


def test_a_new_audit_never_shows_the_proposal_of_the_one_before(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Under "Audit erstellen" the key of the report is always "created" (#82 review)."""
    fake_suggest(monkeypatch)
    app = created_page()
    index = offered(app)[0]
    app.session_state["created_suggest_pending"] = index
    app.run()
    assert document(app)["sites"][index]["suggest"]["block"]

    app.button(key="new_audit").click().run()
    assert "created_measures" not in app.session_state
    entry = gallery_entry(ARCH)
    app.session_state["created"] = created_of(entry)
    app.run()

    assert not any(s["suggest"] and s["suggest"]["block"] for s in document(app)["sites"])


def test_a_report_without_a_hook_offers_no_button() -> None:
    app = report_page(gallery_entry(ARCH), view=None)

    assert all(s["suggest"] is None for s in document(app)["sites"])


def test_in_a_confirmed_session_a_missing_password_secret_still_stops_the_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail closed like start_problem: the flag alone does not open the door (#82 review)."""
    calls = fake_suggest(monkeypatch)
    monkeypatch.setattr("govguard_ui.screens.measure_runner.secret", {}.get)
    app = gallery(confirmed=True)

    request(app, offered(app)[0])

    assert calls == [] and "nicht eingerichtet" in app.error[0].value


def test_the_notice_names_the_model_in_use(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_suggest(monkeypatch)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    assert document(gallery(confirmed=True))["sites"][0]["suggest"]["note"] == NOTICE
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")

    app = gallery(confirmed=True)

    assert document(app)["sites"][0]["suggest"]["note"] == notice("openai/gpt-oss-20b")
