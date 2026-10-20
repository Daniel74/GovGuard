"""The way "from the cache or ask the model" (ADR 0027): one cache, one count, one call path."""

import pytest
from pydantic import BaseModel
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior
from pydantic_ai.usage import RunUsage

from kb_build.llm_step import GateCounts, LlmCache, LlmStep, cache_key, paid_call, usage_line


class Answer(BaseModel):
    text: str


class AnswerCache(LlmCache[Answer]):
    answer_type = Answer


def test_the_key_hashes_the_text_and_names_version_and_model() -> None:
    key = cache_key("prompt text", "v", "m")

    assert key == "86f704a3919a173d7a7020a33a62e7aa2614effb8612f2d4aad41812fae61472|v|m"


def test_a_cache_keeps_its_answers_sorted_in_json_and_reads_them_back() -> None:
    cache = AnswerCache()
    cache.put("b", Answer(text="2"))
    cache.put("a", Answer(text="1"))

    raw = cache.to_json()

    assert raw.index(b'"a"') < raw.index(b'"b"')
    assert raw.endswith(b"}\n")
    assert AnswerCache.from_json(raw.decode()).get("b") == Answer(text="2")


def test_an_empty_cache_is_an_empty_object() -> None:
    assert AnswerCache().to_json() == b"{}\n"


def test_a_known_answer_costs_no_call() -> None:
    cache, calls = AnswerCache({"k": Answer(text="known")}), []

    answer = LlmStep(cache).cached_or_ask("k", lambda: calls.append(1))

    assert answer == Answer(text="known")
    assert calls == []


def test_a_new_answer_is_asked_once_and_cached() -> None:
    cache, calls = AnswerCache(), []
    step = LlmStep(cache)

    def ask() -> Answer:
        calls.append(1)
        return Answer(text="new")

    assert step.cached_or_ask("k", ask) == Answer(text="new")
    assert step.cached_or_ask("k", ask) == Answer(text="new")
    assert len(calls) == 1


def test_no_answer_is_not_cached() -> None:
    cache = AnswerCache()

    assert LlmStep(cache).cached_or_ask("k", lambda: None) is None
    assert cache.get("k") is None


def test_the_tokens_of_a_failed_call_are_paid_too() -> None:
    total = RunUsage()

    with pytest.raises(RuntimeError), paid_call(total) as usage:
        usage.requests = 3
        raise RuntimeError

    assert total.requests == 3


def test_an_invalid_answer_gives_none_and_counts_the_retries_and_the_error() -> None:
    step = LlmStep(AnswerCache())

    def run(usage: RunUsage) -> Answer:
        usage.requests = 3
        raise UnexpectedModelBehavior("invalid")

    assert step.ask("label", run, "%s: invalid: %s", "x") is None
    assert step.counts == GateCounts(retries=2, llm_errors=1)
    assert step.usage.requests == 3


def test_a_valid_answer_without_retry_counts_nothing() -> None:
    step = LlmStep(AnswerCache())

    def run(usage: RunUsage) -> Answer:
        usage.requests = 1
        return Answer(text="ok")

    assert step.ask("label", run, "%s: invalid: %s", "x") == Answer(text="ok")
    assert step.counts == GateCounts()


def test_a_server_error_aborts_the_run() -> None:
    step = LlmStep(AnswerCache())

    def run(usage: RunUsage) -> Answer:
        raise ModelHTTPError(401, "m")

    with pytest.raises(ModelHTTPError):
        step.ask("label", run, "%s: invalid: %s", "x")


def test_counts_add_up_and_print_as_a_quality_line() -> None:
    total = GateCounts(1, 0) + GateCounts(2, 1)

    assert total.line("spec", "classify") == "spec quality classify: retries=3 llm_error=1"


def test_the_usage_line_names_requests_and_tokens() -> None:
    usage = RunUsage(requests=2, input_tokens=10, output_tokens=5)

    assert usage_line("spec", usage) == "spec: 2 requests, 10 input tokens, 5 output tokens"
