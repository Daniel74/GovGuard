"""Cache of LLM verdicts (ADR 0011): same text, prompt version and model_id -> no new call."""

from pathlib import Path

import pytest
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from kb_build.classify import Judge
from kb_build.extracted_models import Requirement
from kb_build.judgement_cache import JudgementCache

ANSWER = {"testable": True, "rationale": "prüfbar", "cfn_resource_types": ["AWS::S3::Bucket"]}


def counting_model(calls: list[int], name: str = "model-a", answer: dict = ANSWER):
    def respond(messages, info):
        calls.append(1)
        return ModelResponse(parts=[ToolCallPart("classify_requirement", answer)])

    return FunctionModel(respond, model_name=name)


def requirement(text: str = "Ensure that S3 blocks public access.") -> Requirement:
    return Requirement(id="3.1.4", title="t", text=text, primary_anchor="A 3.1.4",
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


def test_another_prompt_is_asked_again() -> None:
    cache, calls = JudgementCache(), []
    scope = {"S3": ["AWS::S3::Bucket"]}

    Judge("architecture", counting_model(calls), cache=cache)("CIS", requirement())
    Judge("architecture", counting_model(calls), scope, cache)("CIS", requirement())

    assert len(calls) == 2


def test_an_unusable_answer_is_not_cached() -> None:
    cache, calls = JudgementCache(), []
    invented = {"testable": True, "rationale": "x", "cfn_resource_types": ["AWS::SES::DomainDKIM"]}

    Judge("architecture", counting_model(calls, answer=invented), cache=cache)(
        "CIS", requirement())
    Judge("architecture", counting_model(calls), cache=cache)("CIS", requirement())

    assert len(calls) == 4  # the first judge retried twice, the second one had to ask again


def test_the_cache_survives_a_file_roundtrip(tmp_path: Path) -> None:
    path, calls = tmp_path / "cache.json", []
    cache = JudgementCache()
    Judge("architecture", counting_model(calls), cache=cache)("CIS", requirement())
    cache.save(path)

    Judge("architecture", counting_model(calls), cache=JudgementCache.load(path))(
        "CIS", requirement())

    assert len(calls) == 1


def test_a_missing_cache_file_gives_an_empty_cache(tmp_path: Path) -> None:
    assert JudgementCache.load(tmp_path / "nope.json").size == 0


def refusing_model(status_code: int) -> FunctionModel:
    def respond(messages, info):
        raise ModelHTTPError(status_code, "model-a", {"error": {"code": "output_parse_failed"}})

    return FunctionModel(respond, model_name="model-a")


def test_a_rejected_generation_excludes_the_requirement_but_not_the_run() -> None:
    # Groq answers HTTP 400 output_parse_failed if the model talks instead of calling the tool
    judge = Judge("architecture", refusing_model(400), cache=JudgementCache())

    judge("CIS", requirement())

    assert ("CIS", "3.1.4") in judge.failed


def test_other_http_errors_still_abort_the_run() -> None:
    judge = Judge("architecture", refusing_model(401), cache=JudgementCache())

    with pytest.raises(ModelHTTPError):
        judge("CIS", requirement())
