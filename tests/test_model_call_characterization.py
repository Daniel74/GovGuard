"""Characterization of the model calls at runtime, written before #56 and unchanged by it.
The one change since: #58 switched the inventory on Groq to native.

What it freezes: the output type per caller and provider (ADR 0005, 0016; Groq is
NativeOutput for every caller, #58) and the retry booking (#27). No real model: fake LLMs only.
"""

import asyncio
import json
from collections.abc import Callable

import pytest
from conftest import GroqFake, make_rule
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from govguard.calls.audit_packages import package_requests
from govguard.calls.fail_judge import judge_fails
from govguard.calls.inventory import resource_inventory
from govguard.checks.corrections import SCHEMA_PROBLEM, Corrections
from govguard.models import FindingDraft
from govguard.open_world import SPEC, AuditInput

INPUT = "Alle Zugriffe erfolgen ausschließlich über TLS 1.3."
RULE = make_rule("Art.32", "Sicherheit der Verarbeitung").model_copy(
    update={"cfn_resource_types": ["AWS::S3::Bucket"]})
WARN = {"rule_id": RULE.id, "status": "WARN", "line_start": None, "line_end": None,
        "rationale": "Unklar.", "recommendation": "Nachweisen."}
FAIL = FindingDraft(rule_id=RULE.id, status="FAIL", line_start=1, line_end=1,
                    rationale="Verstoß.", recommendation="Ändern.")
VERDICT = {"rule_id": RULE.id, "confirmed": True, "reason": "Zeile 1 legt es fest."}
BROKEN = "not a list"  # breaks the schema of every caller


def fake(provider: str, payloads: list[dict], seen: list[AgentInfo] | None = None) -> FunctionModel:
    """Answers turn by turn (the last repeats) in the form the agent asked for: tool or JSON."""
    turns: list[int] = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if seen is not None:
            seen.append(info)
        payload = payloads[min(len(turns), len(payloads) - 1)]
        turns.append(1)
        if info.model_request_parameters.output_mode == "native":
            return ModelResponse(parts=[TextPart(json.dumps(payload))])
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, payload)])

    return (GroqFake if provider == "groq" else FunctionModel)(respond, model_name="fake-model")


def ask_package(model: FunctionModel, corrections: Corrections) -> None:
    async def run() -> None:
        await asyncio.gather(*package_requests(
            [RULE], AuditInput(INPUT, SPEC), None, model, corrections))
    asyncio.run(run())


def ask_inventory(model: FunctionModel, corrections: Corrections) -> None:
    asyncio.run(resource_inventory([RULE], INPUT, model, corrections))


def ask_judge(model: FunctionModel, corrections: Corrections) -> None:
    asyncio.run(judge_fails([RULE], [FAIL], AuditInput(INPUT, SPEC), model, corrections))


Caller = Callable[[FunctionModel, Corrections], None]
# caller -> (asker, a valid answer, a schema-breaking answer, tool name under ToolOutput)
CALLERS: dict[str, tuple[Caller, dict, dict, str]] = {
    "package": (ask_package, {"findings": [WARN]}, {"findings": BROKEN}, "submit_audit"),
    "inventory": (ask_inventory, {"resource_types": []}, {"resource_types": BROKEN},
                  "submit_inventory"),
    "judge": (ask_judge, {"verdicts": [VERDICT]}, {"verdicts": BROKEN}, "submit_fail_verdicts"),
}
# Groq: NativeOutput (ADR 0016) for every caller, the inventory too (#58)
OUTPUT_MODE = {("package", "bedrock"): "tool", ("package", "groq"): "native",
               ("judge", "bedrock"): "tool", ("judge", "groq"): "native",
               ("inventory", "bedrock"): "tool", ("inventory", "groq"): "native"}
# strict of the tool: the inventory sets none (ADR 0017: package and judge are strict)
TOOL_STRICT = {"package": True, "inventory": None, "judge": True}


@pytest.mark.parametrize("provider", ["bedrock", "groq"])
@pytest.mark.parametrize("caller", list(CALLERS))
def test_output_type_per_caller_and_provider(caller: str, provider: str) -> None:
    ask, valid, _, tool = CALLERS[caller]
    seen: list[AgentInfo] = []

    ask(fake(provider, [valid], seen), Corrections())

    params = seen[0].model_request_parameters
    assert params.output_mode == OUTPUT_MODE[(caller, provider)]
    if params.output_mode == "tool":
        assert seen[0].output_tools[0].name == tool
        assert seen[0].output_tools[0].strict is TOOL_STRICT[caller]
    else:
        assert seen[0].output_tools == []
        assert params.output_object.strict is True


@pytest.mark.parametrize("caller", list(CALLERS))
def test_the_first_attempt_is_no_retry(caller: str) -> None:
    ask, valid, _, _ = CALLERS[caller]
    corrections = Corrections()

    ask(fake("bedrock", [valid]), corrections)

    assert (corrections.retries, corrections.retry_problems) == (0, [])


@pytest.mark.parametrize("caller", list(CALLERS))
def test_a_retry_after_a_broken_schema_counts_with_the_schema_problem(caller: str) -> None:
    ask, valid, broken, _ = CALLERS[caller]
    corrections = Corrections()

    ask(fake("bedrock", [broken, valid]), corrections)

    assert corrections.retries == 1  # no reason came from the code: the schema broke
    assert SCHEMA_PROBLEM in corrections.retry_problems


# The answer parses, but the code sends it back with a reason: the retry counts, no schema problem
REASONED: dict[str, dict] = {
    "package": {"findings": []},  # a rule without a finding
    "inventory": {"resource_types": [  # a type that is not in the list
        {"resource_type": "AWS::Foo::Bar", "line_start": 1, "line_end": 1}]},
    "judge": {"verdicts": []},  # a FAIL without a verdict
}


@pytest.mark.parametrize("caller", list(CALLERS))
def test_a_retry_with_a_reason_from_the_code_counts_without_the_schema_problem(
    caller: str
) -> None:
    ask, valid, _, _ = CALLERS[caller]
    corrections = Corrections()

    ask(fake("bedrock", [REASONED[caller], valid]), corrections)

    assert corrections.retries == 1
    assert SCHEMA_PROBLEM not in corrections.retry_problems
    assert (caller == "judge") or corrections.retry_problems  # judge: the reason is not recorded


def test_the_judge_counts_a_retry_that_ends_in_an_invalid_answer() -> None:
    ask, _, broken, _ = CALLERS["judge"]
    corrections = Corrections()

    ask(fake("bedrock", [broken]), corrections)  # broken twice: the validator never sees it

    assert corrections.retries == 1
    assert SCHEMA_PROBLEM in corrections.retry_problems
