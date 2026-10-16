import hashlib
import json
from pathlib import Path

import pytest
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from govguard.cli import main, model_for, parse_args
from govguard.models import AuditReport, RuleCatalog


def fake_model(spec_catalog: RuleCatalog) -> FunctionModel:
    """Fake LLM: WARN for every rule."""
    findings = [
        {"rule_id": rule.id, "status": "WARN", "line_start": None, "line_end": None,
         "rationale": "Nicht entscheidbar.", "recommendation": "Prüfen."}
        for rule in spec_catalog.rules
    ]

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": findings})])

    return FunctionModel(respond, model_name="fake-model")


def test_spec_command_prints_audit_report_as_json(
    spec_catalog: RuleCatalog, spec_input: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec_file = tmp_path / "spec.txt"
    spec_file.write_text(spec_input, encoding="utf-8")
    catalog_file = tmp_path / "rules_spec.json"
    catalog_file.write_text(spec_catalog.model_dump_json(), encoding="utf-8")

    exit_code = main(["spec", str(spec_file), "--catalog", str(catalog_file)],
                     model=fake_model(spec_catalog))

    report = AuditReport.model_validate(json.loads(capsys.readouterr().out))
    assert exit_code == 0
    assert report.overall_status == "WARN"
    assert [f.rule_id for f in report.findings] == [r.id for r in spec_catalog.rules]
    # Trace carries hashes only, never the input itself (ADR 0006)
    assert report.trace.input_sha256 == hashlib.sha256(spec_input.encode()).hexdigest()
    assert report.trace.catalog_sha256 == hashlib.sha256(catalog_file.read_bytes()).hexdigest()


def test_invalid_llm_answer_fails_closed(
    spec_catalog: RuleCatalog, spec_input: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec_file = tmp_path / "spec.txt"
    spec_file.write_text(spec_input, encoding="utf-8")
    catalog_file = tmp_path / "rules_spec.json"
    catalog_file.write_text(spec_catalog.model_dump_json(), encoding="utf-8")

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": []})])  # no findings

    exit_code = main(["spec", str(spec_file), "--catalog", str(catalog_file)],
                     model=FunctionModel(respond, model_name="fake-model"))

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "Audit fehlgeschlagen" in captured.err


def test_arch_command_audits_a_template_against_the_architecture_catalog(
    arch_catalog: RuleCatalog, bucket_template: str, tmp_path: Path,
    capsys: pytest.CaptureFixture[str]
) -> None:
    template_file = tmp_path / "template.json"
    template_file.write_text(bucket_template, encoding="utf-8")
    catalog_file = tmp_path / "rules_arch.json"
    catalog_file.write_text(arch_catalog.model_dump_json(), encoding="utf-8")
    s3_rule = arch_catalog.model_copy(update={"rules": arch_catalog.rules[:1]})

    exit_code = main(["arch", str(template_file), "--catalog", str(catalog_file)],
                     model=fake_model(s3_rule))

    report = AuditReport.model_validate(json.loads(capsys.readouterr().out))
    assert exit_code == 0
    assert report.audit_type == "architecture"
    statuses = {f.rule_id: f.status for f in report.findings}
    assert statuses == {"ARCH-CIS-3.1.4": "WARN", "ARCH-CIS-3.3.1": "N/A"}  # DynamoDB: by code


def run_failing(spec_catalog: RuleCatalog, spec_input: str, tmp_path: Path, model: FunctionModel,
                capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    spec_file = tmp_path / "spec.txt"
    spec_file.write_text(spec_input, encoding="utf-8")
    catalog_file = tmp_path / "rules_spec.json"
    catalog_file.write_text(spec_catalog.model_dump_json(), encoding="utf-8")
    exit_code = main(["spec", str(spec_file), "--catalog", str(catalog_file)], model=model)
    return exit_code, capsys.readouterr().err


def test_fail_closed_names_the_reasons_per_rule_in_plain_language(
    spec_catalog: RuleCatalog, spec_input: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": []})])  # none

    exit_code, err = run_failing(spec_catalog, spec_input, tmp_path,
                                 FunctionModel(respond, model_name="fake-model"), capsys)

    assert exit_code == 2
    assert "nicht verwertbar" in err
    assert "- Befund fehlt für: SPEC-DSGVO-Art.9" in err
    assert "- Befund fehlt für: SPEC-DSGVO-Art.32" in err
    assert "UnexpectedModelBehavior" not in err and "retries" not in err  # no library text


def test_api_error_gets_its_own_sentence_without_library_text(
    spec_catalog: RuleCatalog, spec_input: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def throttled(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        raise ModelHTTPError(status_code=429, model_name="fake-model", body="ThrottlingException")

    exit_code, err = run_failing(spec_catalog, spec_input, tmp_path,
                                 FunctionModel(throttled, model_name="fake-model"), capsys)

    assert exit_code == 2
    assert "nicht erreichbar oder überlastet" in err
    assert "ThrottlingException" not in err and "429" not in err


def test_groq_is_the_default_provider_bedrock_an_explicit_option() -> None:
    # ADR 0023: Groq in UI and Lambda; Bedrock `eu.` only for real data (ADR 0001)
    assert parse_args(["spec", "x.txt"]).provider == "groq"
    assert parse_args(["spec", "x.txt", "--provider", "bedrock"]).provider == "bedrock"


def test_missing_groq_key_aborts_without_falling_back_to_bedrock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    def bedrock_must_not_be_called(**_: object) -> None:
        raise AssertionError("silent fallback to Bedrock")

    monkeypatch.setattr("govguard.cli.bedrock_model", bedrock_must_not_be_called)

    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        model_for("groq")


def test_each_provider_builds_its_own_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test")
    monkeypatch.delenv("GROQ_MODEL", raising=False)

    assert model_for("groq").model_name == "openai/gpt-oss-120b"
    assert model_for("bedrock").model_name.startswith("eu.")  # EU only (ADR 0001)


def test_the_report_names_the_model_of_the_chosen_provider(
    spec_catalog: RuleCatalog, spec_input: str, tmp_path: Path,
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_file = tmp_path / "spec.txt"
    spec_file.write_text(spec_input, encoding="utf-8")
    catalog_file = tmp_path / "rules_spec.json"
    catalog_file.write_text(spec_catalog.model_dump_json(), encoding="utf-8")
    monkeypatch.setattr("govguard.cli.groq_model", lambda: fake_model(spec_catalog))

    exit_code = main(["spec", str(spec_file), "--catalog", str(catalog_file)])

    assert exit_code == 0
    assert AuditReport.model_validate_json(capsys.readouterr().out).model_id == "fake-model"


def test_too_long_input_ends_with_exit_code_1_and_a_plain_sentence(
    spec_catalog: RuleCatalog, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def never_called(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        raise AssertionError("no model call for a rejected input")

    exit_code, err = run_failing(spec_catalog, "x" * 100_001, tmp_path,
                                 FunctionModel(never_called), capsys)

    assert exit_code == 1  # 2 stays fail closed
    assert err.strip() == "Eingabe zu lang: 100.001 Zeichen, erlaubt sind höchstens 100.000."
