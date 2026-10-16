"""Inputs over 100,000 characters are rejected before the first LLM call (ADR 0023)."""

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from govguard.audit_engine import InputTooLongError, run_audit
from govguard.models import RuleCatalog


def never_called(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    raise AssertionError("the model must not be called for a rejected input")


def test_input_over_100000_characters_is_rejected_without_a_model_call(
    spec_catalog: RuleCatalog, trace
) -> None:
    with pytest.raises(InputTooLongError, match="100.001 Zeichen"):
        run_audit(spec_catalog, "x" * 100_001, FunctionModel(never_called), trace)


def test_architecture_input_is_rejected_before_the_inventory(
    arch_catalog: RuleCatalog, trace
) -> None:
    with pytest.raises(InputTooLongError):
        run_audit(arch_catalog, "x" * 100_001, FunctionModel(never_called), trace)


def test_exactly_100000_characters_are_still_audited(spec_catalog: RuleCatalog, trace) -> None:
    findings = [{"rule_id": rule.id, "status": "WARN", "line_start": None, "line_end": None,
                 "rationale": "Unklar.", "recommendation": "Nachweisen."}
                for rule in spec_catalog.rules]

    def warn(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": findings})])

    report = run_audit(spec_catalog, "x" * 100_000, FunctionModel(warn), trace)

    assert report.overall_status == "WARN"
