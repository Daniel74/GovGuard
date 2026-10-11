"""Cache of LLM verdicts (ADR 0011): same text, prompt version and model_id -> no new call."""

import pytest
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from kb_build import classify
from kb_build.classify import Judge
from kb_build.extracted_models import Requirement
from kb_build.judgement_cache import JudgementCache
from kb_build.scope import Scope

ANSWER = {"testable": True, "rationale": "prüfbar", "cfn_resource_types": ["AWS::S3::Bucket"]}


def counting_model(calls: list[int], name: str = "model-a", answer: dict = ANSWER):
    def respond(messages, info):
        calls.append(1)
        return ModelResponse(parts=[ToolCallPart("classify_requirement", answer)])

    return FunctionModel(respond, model_name=name)


def requirement(text: str = "Ensure that S3 blocks public access.", rid: str = "3.1.4"):
    return Requirement(id=rid, title="t", text=text, primary_anchor=f"A {rid}",
                       attributes={}, prefilter_passed=True)


def test_the_second_run_asks_the_llm_nothing() -> None:
    cache, calls = JudgementCache(), []

    first = Judge("architecture", counting_model(calls), cache=cache)("CIS", requirement())
    second = Judge("architecture", counting_model(calls), cache=cache)("CIS", requirement())

    assert len(calls) == 1
    assert second == first


def test_a_changed_text_is_asked_again() -> None:
    cache, calls = JudgementCache(), []
    judge = Judge("architecture", counting_model(calls), cache=cache)

    judge("CIS", requirement())
    Judge("architecture", counting_model(calls), cache=cache)("CIS", requirement("New text."))

    assert len(calls) == 2


def test_another_model_id_is_asked_again() -> None:
    cache, calls = JudgementCache(), []

    Judge("architecture", counting_model(calls, "model-a"), cache=cache)("CIS", requirement())
    Judge("architecture", counting_model(calls, "model-b"), cache=cache)("CIS", requirement())

    assert len(calls) == 2


def test_other_instructions_are_asked_again() -> None:
    cache, calls = JudgementCache(), []
    scope = Scope({"S3": ["AWS::S3::Bucket"]})

    Judge("architecture", counting_model(calls), cache=cache)("CIS", requirement())
    Judge("architecture", counting_model(calls), scope, cache)("CIS", requirement())

    assert len(calls) == 2


@pytest.mark.parametrize("part", ["USER_PROMPT", "TOOL_NAME", "TOOL_DESCRIPTION"])
def test_a_changed_request_template_is_asked_again(
    part: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The model sees more than the instructions: user message and tool definition count too
    cache, calls = JudgementCache(), []
    Judge("architecture", counting_model(calls), cache=cache)("CIS", requirement())

    monkeypatch.setattr(classify, part, getattr(classify, part) + " ")
    Judge("architecture", counting_model(calls), cache=cache)("CIS", requirement())

    assert len(calls) == 2


def test_an_unusable_answer_is_not_cached() -> None:
    cache, calls = JudgementCache(), []
    invented = {"testable": True, "rationale": "x", "cfn_resource_types": ["AWS::SES::DomainDKIM"]}

    Judge("architecture", counting_model(calls, answer=invented), cache=cache)(
        "CIS", requirement())
    Judge("architecture", counting_model(calls), cache=cache)("CIS", requirement())

    assert len(calls) == 4  # the first judge retried twice, the second one had to ask again


def test_the_cache_survives_a_json_roundtrip() -> None:
    calls: list[int] = []
    cache = JudgementCache()
    Judge("architecture", counting_model(calls), cache=cache)("CIS", requirement())

    restored = JudgementCache.from_json(cache.to_json())
    Judge("architecture", counting_model(calls), cache=restored)("CIS", requirement())

    assert len(calls) == 1


def refusing_model(status_code: int) -> FunctionModel:
    def respond(messages, info):
        raise ModelHTTPError(status_code, "model-a", {"error": {"code": "output_parse_failed"}})

    return FunctionModel(respond, model_name="model-a")


def test_a_rejected_generation_gives_no_answer_but_does_not_abort_the_run() -> None:
    # Groq answers HTTP 400 output_parse_failed if the model talks instead of calling the tool
    judge = Judge("architecture", refusing_model(400), cache=JudgementCache())

    assert judge("CIS", requirement()) is None


def test_other_http_errors_still_abort_the_run() -> None:
    judge = Judge("architecture", refusing_model(401), cache=JudgementCache())

    with pytest.raises(ModelHTTPError):
        judge("CIS", requirement())


def test_the_judge_sums_up_the_tokens_of_all_calls() -> None:
    calls: list[int] = []
    judge = Judge("architecture", counting_model(calls), cache=JudgementCache())

    judge("CIS", requirement())
    judge("CIS", requirement("Another text.", "3.1.5"))

    assert judge.usage.requests == 2
    assert judge.usage.input_tokens > 0
