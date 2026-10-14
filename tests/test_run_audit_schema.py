"""Strict, static schema per provider: Bedrock forced tool, Groq native output (ADR 0016, 0017)."""

import json

from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from govguard.audit_engine import run_audit

FINDINGS = [
    {"rule_id": "SPEC-DSGVO-Art.32", "status": "PASS", "line_start": 2, "line_end": 2,
     "rationale": "TLS.", "recommendation": None},
    {"rule_id": "SPEC-DSGVO-Art.9", "status": "WARN", "line_start": None, "line_end": None,
     "rationale": "Unklar.", "recommendation": "Rechtsgrundlage nennen."},
]


class GroqFake(FunctionModel):
    """Fake LLM that reports the Groq provider, like `GroqModel`."""

    @property
    def system(self) -> str:
        return "groq"


def test_bedrock_gets_a_strict_submit_audit_tool(spec_catalog, spec_input, trace) -> None:
    seen: list[AgentInfo] = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.append(info)
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": FINDINGS})])

    run_audit(spec_catalog, spec_input, FunctionModel(respond), trace)

    assert [(t.name, t.strict) for t in seen[0].output_tools] == [("submit_audit", True)]


def test_groq_gets_strict_native_output_instead_of_a_tool(spec_catalog, spec_input, trace) -> None:
    seen: list[AgentInfo] = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.append(info)
        return ModelResponse(parts=[TextPart(json.dumps({"findings": FINDINGS}))])

    report = run_audit(spec_catalog, spec_input, GroqFake(respond, model_name="groq-fake"), trace)

    params = seen[0].model_request_parameters
    assert (params.output_mode, params.output_object.strict) == ("native", True)
    assert seen[0].output_tools == []
    assert report.findings[0].evidence == "Alle Zugriffe erfolgen ausschließlich über TLS 1.3."


def test_both_models_audit_at_temperature_zero(spec_catalog, spec_input, trace) -> None:
    # #28: Groq gave about nine times as many FAILs as Bedrock; the spread is measured per run
    seen: list[AgentInfo] = []

    def bedrock(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.append(info)
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": FINDINGS})])

    def groq(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.append(info)
        return ModelResponse(parts=[TextPart(json.dumps({"findings": FINDINGS}))])

    run_audit(spec_catalog, spec_input, FunctionModel(bedrock), trace)
    run_audit(spec_catalog, spec_input, GroqFake(groq, model_name="groq-fake"), trace)

    assert [info.model_settings["temperature"] for info in seen] == [0, 0]


def test_a_runaway_answer_is_cut_off_within_the_lambda_timeout(
    spec_catalog, spec_input, trace
) -> None:
    # #28: a Bedrock retry looped for 204 s up to 64,000 tokens; normal answers stay below 4,000
    seen: list[AgentInfo] = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.append(info)
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": FINDINGS})])

    run_audit(spec_catalog, spec_input, FunctionModel(respond), trace)

    assert seen[0].model_settings["max_tokens"] == 8000
