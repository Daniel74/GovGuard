"""The LLM groups the sections of an article (#53); the code checks marks and caches."""

from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from test_decompose_parts import ANSWER, ART_6, LEAD_IN

from kb_build.decompose.split import INSTRUCTIONS, DecompositionCache, Splitter, user_prompt

WRONG = {"groups": [{"marks": ["Abs. 9"], "kind": "alle_gelten", "rationale": "x"}]}


def answer_in_turns(*turns: dict, seen: list | None = None) -> FunctionModel:
    """Fake LLM calling decompose_article turn by turn; repeats the last turn."""
    calls: list[list[ModelMessage]] = seen if seen is not None else []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        calls.append(messages)
        return ModelResponse(parts=[ToolCallPart("decompose_article",
                                                 turns[min(len(calls), len(turns)) - 1])])

    return FunctionModel(respond, model_name="fake-model")


def test_the_prompt_shows_every_mark_and_each_lead_in_once() -> None:
    prompt = user_prompt("DSGVO", ART_6)
    assert prompt.count(LEAD_IN) == 1
    assert "[Art. 6 Abs. 1 lit. b] Vertrag." in prompt
    assert prompt.index(LEAD_IN) < prompt.index("[Art. 6 Abs. 1 lit. a]")


def test_unknown_marks_go_back_to_the_model() -> None:
    seen: list = []
    answer = Splitter(answer_in_turns(WRONG, ANSWER.model_dump(), seen=seen))("DSGVO", ART_6)
    assert answer == ANSWER
    assert "Diese Marken gibt es nicht: ['Abs. 9']" in str(seen[1])


def test_missing_marks_go_back_to_the_model() -> None:
    seen: list = []
    missing = {"groups": ANSWER.model_dump()["groups"][:2]}  # without Art. 6 Abs. 2
    answer = Splitter(answer_in_turns(missing, ANSWER.model_dump(), seen=seen))("DSGVO", ART_6)
    assert answer == ANSWER
    assert "Diese Marken fehlen: ['Art. 6 Abs. 2']" in str(seen[1])


def test_an_answer_that_stays_invalid_leaves_the_article_whole_and_is_not_cached() -> None:
    cache = DecompositionCache()
    splitter = Splitter(answer_in_turns(WRONG), cache)
    assert splitter("DSGVO", ART_6) is None
    assert splitter.counts.llm_errors == 1
    assert cache.to_json() == b"{}\n"


def test_the_second_run_asks_the_llm_nothing() -> None:
    cache, seen = DecompositionCache(), []
    Splitter(answer_in_turns(ANSWER.model_dump(), seen=seen), cache)("DSGVO", ART_6)
    again = DecompositionCache.from_json(cache.to_json().decode())
    assert Splitter(answer_in_turns(WRONG, seen=seen), again)("DSGVO", ART_6) == ANSWER
    assert len(seen) == 1


def test_rights_and_classification_rules_are_no_keine_pflicht() -> None:
    # Early run: KI-VO Art. 6 Abs. 2 (Annex III) and DSGVO Art. 22 Abs. 1 were dropped
    assert "Rechte der betroffenen Person und Regeln zur Einstufung" in INSTRUCTIONS


def test_a_prohibition_with_listed_exceptions_is_named() -> None:
    # Wohngeld run: DSGVO Art. 9 Abs. 1 alone was FAIL despite Abs. 2 lit. b
    assert "Ein Verbot, dessen Ausnahmen der Artikel in einem eigenen Absatz aufzählt" in (
        INSTRUCTIONS)


def test_measures_listed_with_gegebenenfalls_are_no_alternatives() -> None:
    # Early run: DSGVO Art. 32 Abs. 1 lit. a-d flipped to eine_genuegt
    assert 'mit\n  "gegebenenfalls" oder "unter anderem" ist "je_nach_risiko"' in INSTRUCTIONS
