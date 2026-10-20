"""model_call: agents per provider and the retry booking in one place (#56, ADR 0005, 0016)."""

import asyncio

import pytest
from conftest import GroqFake
from pydantic import BaseModel
from pydantic_ai import RunContext
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from govguard.calls.model_call import Answer, CallDeps, agents_for, ask, count_retry, send_back
from govguard.checks.corrections import SCHEMA_PROBLEM, Corrections


class Verdict(BaseModel):
    ok: bool


def validate(ctx: RunContext[CallDeps], answer: Verdict) -> Verdict:
    count_retry(ctx)
    if not answer.ok:
        send_back(ctx, "not ok")
    return answer


def agents():
    return agents_for(Answer(Verdict, "submit_answer", "Answer."), deps_type=CallDeps,
                      instructions="Be brief.", validator=validate, settings={})


def run(model: FunctionModel) -> Corrections:
    deps = CallDeps(corrections=Corrections())
    asyncio.run(ask(agents(), model, "prompt", deps))
    return deps.corrections


def answering(turns: list[dict], seen: list[AgentInfo], model_class=FunctionModel):
    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.append(info)
        payload = turns[min(len(seen), len(turns)) - 1]
        if info.model_request_parameters.output_mode == "native":
            return ModelResponse(parts=[TextPart('{"ok": true}')])
        return ModelResponse(parts=[ToolCallPart("submit_answer", payload)])
    return model_class(respond, model_name="fake-model")


@pytest.mark.parametrize(("model_class", "mode"), [(FunctionModel, "tool"), (GroqFake, "native")])
def test_ask_picks_the_agent_of_the_provider(model_class, mode) -> None:
    seen: list[AgentInfo] = []

    run(answering([{"ok": True}], seen, model_class))

    assert seen[0].model_request_parameters.output_mode == mode


def test_a_good_first_answer_books_no_retry() -> None:
    corrections = run(answering([{"ok": True}], []))

    assert (corrections.retries, corrections.retry_problems) == (0, [])


def test_a_retry_after_send_back_counts_without_the_schema_problem() -> None:
    corrections = run(answering([{"ok": False}, {"ok": True}], []))

    assert corrections.retries == 1
    assert SCHEMA_PROBLEM not in corrections.retry_problems


def test_a_retry_without_a_reason_from_the_code_counts_the_schema_problem() -> None:
    corrections = run(answering([{"ok": "maybe"}, {"ok": True}], []))

    assert corrections.retries == 1
    assert SCHEMA_PROBLEM in corrections.retry_problems
