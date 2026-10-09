import hashlib
import json
from pathlib import Path

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from govguard.cli import main
from govguard.models import AuditReport, RuleCatalog


def fake_model(spec_catalog: RuleCatalog) -> FunctionModel:
    """Fake LLM: WARN for every rule."""
    findings = [
        {"rule_id": rule.id, "status": "WARN", "evidence": None,
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
