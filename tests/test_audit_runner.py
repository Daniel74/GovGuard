"""Audit erstellen in the demo: guard, progress and local run with Groq (ADR 0023, #11)."""

import hashlib
from pathlib import Path

import pytest
from pydantic_ai.models.function import FunctionModel
from test_run_audit_progress import warn_for_every_rule

from govguard.models import Progress, RuleCatalog
from govguard_ui.audit_runner import backend_problem, progress_view, run_local, start_problem

SECRET = "korrekt-pferd"


def test_right_password_and_a_text_start_the_audit() -> None:
    assert start_problem("Ein Fachkonzept.", password=SECRET, secret=SECRET) is None


@pytest.mark.parametrize("password", ["", "falsch", "korrekt-pferd "])
def test_without_the_right_password_no_audit_starts(password: str) -> None:
    assert "Passwort" in start_problem("Ein Fachkonzept.", password=password, secret=SECRET)


@pytest.mark.parametrize("secret", [None, ""])
def test_without_a_configured_password_nobody_can_start(secret: str | None) -> None:
    """Fail closed: an empty secret must not let an empty password through."""
    assert "nicht eingerichtet" in start_problem("Text", password="", secret=secret)


def test_an_empty_input_does_not_start() -> None:
    assert "Eingabe" in start_problem("  \n", password=SECRET, secret=SECRET)


def test_more_than_100_000_characters_do_not_start() -> None:
    assert start_problem("x" * 100_000, password=SECRET, secret=SECRET) is None
    assert "100.000" in start_problem("x" * 100_001, password=SECRET, secret=SECRET)


def test_local_run_audits_with_trace_and_reports_progress(
    spec_catalog: RuleCatalog, spec_input: str, tmp_path: Path
) -> None:
    catalog_file = tmp_path / "rules_spec.json"
    catalog_file.write_text(spec_catalog.model_dump_json(), encoding="utf-8")
    seen: list[Progress] = []

    report = run_local("spec", spec_input, FunctionModel(warn_for_every_rule), seen.append,
                       catalog_file=catalog_file)

    assert [f.rule_id for f in report.findings] == ["SPEC-DSGVO-Art.32", "SPEC-DSGVO-Art.9"]
    assert report.trace.input_sha256 == hashlib.sha256(spec_input.encode()).hexdigest()
    assert report.trace.catalog_sha256 == hashlib.sha256(catalog_file.read_bytes()).hexdigest()
    assert (seen[-1].packages_done, seen[-1].packages_total) == (1, 1)


@pytest.mark.parametrize(("progress", "fraction", "text"), [
    (Progress(phase="inventory"), 0.0, "Ressourcen erkennen (KI-Vorlauf oder Template) …"),
    (Progress(phase="packages", packages_total=16), 0.0, "Paket 0 von 16 geprüft"),
    (Progress(phase="packages", packages_done=4, packages_total=16), 0.225,
     "Paket 4 von 16 geprüft"),
    (Progress(phase="packages"), 0.9, "Alle Prüfregeln vom Code entschieden"),
    (Progress(phase="fail_judge"), 0.95, "Verstoß-Prüfer prüft jeden Verstoß nach …"),
])
def test_progress_becomes_bar_and_text(progress: Progress, fraction: float, text: str) -> None:
    assert progress_view(progress) == (pytest.approx(fraction), text)


@pytest.mark.parametrize("backend", [None, "", "local"])
def test_demo_backend_runs_in_the_streamlit_process(backend: str | None) -> None:
    assert backend_problem(backend) is None


@pytest.mark.parametrize(("backend", "hint"), [("lambda", "#38"), ("bedrock", "unbekannt")])
def test_other_backends_are_not_available_in_the_demo(backend: str, hint: str) -> None:
    assert hint in backend_problem(backend)
