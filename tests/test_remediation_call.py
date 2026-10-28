"""The measure proposal: one LLM call for one site, one retry, then "kein Vorschlag" (#82)."""

import asyncio
import json

import pytest
from conftest import GroqFake
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from test_remediation_checks import DOCUMENT, GOOD, SITE

from govguard.calls.remediation import REMEDIATION_PROMPT, suggest_measures
from govguard.checks.remediation_models import Measure

GOOD_ANSWER = {"measures": [d.model_dump() for d in GOOD]}
BAD_ANSWER = {"measures": [GOOD_ANSWER["measures"][0]]}  # finding C belongs to no measure


def fake(answers: list[dict | Exception], model_class: type[FunctionModel] = FunctionModel,
         ) -> FunctionModel:
    turns: list[int] = []
    sent: list[list[ModelMessage]] = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        sent.append(messages)
        answer = answers[min(len(turns), len(answers) - 1)]
        turns.append(1)
        if isinstance(answer, Exception):
            raise answer
        if info.model_request_parameters.output_mode == "native":
            return ModelResponse(parts=[TextPart(json.dumps(answer))])
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, answer)])

    model = model_class(respond, model_name="fake-model")
    model.sent = sent  # type: ignore[attr-defined]
    return model


def run(model: FunctionModel) -> list[Measure] | None:
    return asyncio.run(suggest_measures(SITE, DOCUMENT, model))


def test_a_valid_answer_becomes_checked_measures_after_one_call() -> None:
    model = fake([GOOD_ANSWER])

    measures = run(model)

    assert [m.line_start for m in measures] == [5, 7]
    assert len(model.sent) == 1


@pytest.mark.parametrize("model_class", [FunctionModel, GroqFake])
def test_both_providers_get_the_same_answer_type(model_class: type[FunctionModel]) -> None:
    assert run(fake([GOOD_ANSWER], model_class)) is not None


def test_the_model_sees_the_whole_document_with_the_site_marked_and_the_open_findings() -> None:
    model = fake([GOOD_ANSWER])

    run(model)

    [first] = model.sent[0]
    assert first.instructions == REMEDIATION_PROMPT
    request = str(first.parts[0].content)
    assert "  1| # Vorspann" in request and " 11|     Resource: *" in request  # whole document
    assert ">  5|     Resource: *" in request and ">  2| ## Speicher" in request  # site marked
    assert ">  1|" not in request and "> 10|" not in request
    assert '"rule_id": "A"' in request and '"status": "FAIL"' in request
    assert "why A" in request and "do A" in request  # rationale and recommendation
    assert '"rule_id": "P"' not in request  # a PASS is no work


def test_the_prompt_asks_for_line_numbers_not_a_copy_and_for_german() -> None:
    assert '"from_line", "to_line"' in REMEDIATION_PROMPT
    assert '"before"' not in REMEDIATION_PROMPT  # the code cuts it
    assert "mit derselben Einrückung" in REMEDIATION_PROMPT
    assert "Schreibe Satz und Platzhalter auf Deutsch." in REMEDIATION_PROMPT


def test_the_model_is_asked_for_line_numbers_in_the_schema() -> None:
    seen: list[AgentInfo] = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.append(info)
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, GOOD_ANSWER)])

    run(FunctionModel(respond, model_name="fake-model"))

    fields = seen[0].output_tools[0].parameters_json_schema["$defs"]["MeasureDraft"]["properties"]
    assert set(fields) == {"sentence", "from_line", "to_line", "after", "rule_ids"}


def test_a_wrong_answer_is_sent_back_once_with_every_reason_then_it_works() -> None:
    model = fake([BAD_ANSWER, GOOD_ANSWER])

    measures = run(model)

    assert measures is not None and len(model.sent) == 2
    retry = str(model.sent[1][-1].parts[0].content)
    assert "Keiner Maßnahme zugeordnet: C" in retry


def test_an_answer_still_wrong_after_the_retry_is_no_proposal_and_no_crash() -> None:
    model = fake([BAD_ANSWER])

    assert run(model) is None
    assert len(model.sent) == 2


def test_a_broken_schema_is_no_proposal_either() -> None:
    assert run(fake([{"measures": "nein"}])) is None


def test_an_unreachable_service_is_no_proposal_and_no_crash() -> None:
    assert run(fake([ModelHTTPError(503, "fake-model", "overloaded")])) is None
