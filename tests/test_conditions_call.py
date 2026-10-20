"""The condition pre-run: one LLM call, one retry, no fail closed (#60, ADR 0028)."""

import asyncio
import json

import pytest
from conftest import GroqFake
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from govguard.audit_setup import conditions_for
from govguard.calls.conditions import CONDITIONS_PROMPT, find_conditions
from govguard.checks.corrections import Corrections
from govguard.condition_models import ConditionDef, ConditionResult

INPUT = ("Das Portal nutzt ein Sprachmodell für Zusammenfassungen.\n"
         "Alle Daten bleiben ausschließlich in der EU und werden nicht übermittelt.\n"
         "Kein externer Dienstleister verarbeitet die Daten im Auftrag.\n")
DEFS = [
    ConditionDef(id="ki_system", name="KI-System", only_if="x", meaning="Software mit KI.",
                 yes="Ja-Kriterium", no="Nein-Kriterium"),
    ConditionDef(id="third_country", name="Drittlandübermittlung", only_if="x", meaning="m",
                 yes="y", no="n"),
]


def item(condition_id: str, affirming=(), denying=()) -> dict:
    return {"condition_id": condition_id,
            "affirming": [{"line_start": a, "line_end": a} for a in affirming],
            "denying": [{"line_start": d, "line_end": d} for d in denying]}


GOOD = {"conditions": [item("ki_system", affirming=[1]), item("third_country", denying=[2])]}


def fake(answers: list[dict | Exception], seen: list[AgentInfo] | None = None,
         model_class: type[FunctionModel] = FunctionModel) -> FunctionModel:
    turns: list[int] = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        info_messages.append(messages)
        if seen is not None:
            seen.append(info)
        answer = answers[min(len(turns), len(answers) - 1)]
        turns.append(1)
        if isinstance(answer, Exception):
            raise answer
        if info.model_request_parameters.output_mode == "native":
            return ModelResponse(parts=[TextPart(json.dumps(answer))])
        return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name, answer)])

    info_messages: list[list[ModelMessage]] = []
    model = model_class(respond, model_name="fake-model")
    model.messages = info_messages  # type: ignore[attr-defined]
    return model


def run(model: FunctionModel, corrections: Corrections | None = None
        ) -> tuple[dict[str, ConditionResult], Corrections]:
    corrections = corrections or Corrections()
    return asyncio.run(find_conditions(DEFS, INPUT, model, corrections)), corrections


def test_a_valid_answer_becomes_values_and_costs_one_call() -> None:
    seen: list[AgentInfo] = []

    results, corrections = run(fake([GOOD], seen))

    assert (results["ki_system"].value, results["third_country"].value) == ("yes", "no")
    assert len(seen) == 1 and corrections.retries == 0


@pytest.mark.parametrize("model_class", [FunctionModel, GroqFake])
def test_both_providers_get_the_same_answer_type(model_class: type[FunctionModel]) -> None:
    results, _ = run(fake([GOOD], model_class=model_class))

    assert results["third_country"].denying[0].line_start == 2


def test_the_model_reads_the_prompt_the_criteria_and_the_numbered_lines() -> None:
    model = fake([GOOD])

    run(model)

    first = model.messages[0][0]  # type: ignore[attr-defined]
    assert first.instructions.startswith(
        "Du stellst fest, was eine Spezifikation zu Bedingungen sagt")
    prompt = str(first)
    assert "Jede Zeile der Eingabe beginnt mit ihrer Nummer" in first.instructions
    assert '"id": "ki_system"' in prompt and "Nein-Kriterium" in prompt
    assert "2| Alle Daten bleiben" in prompt
    assert "only_if" not in prompt  # the model needs the criteria, not the rule grouping


def test_the_pre_run_is_deterministic_and_has_room_for_all_lines() -> None:
    seen: list[AgentInfo] = []

    run(fake([GOOD], seen))

    assert seen[0].model_settings["temperature"] == 0
    assert seen[0].model_settings["max_tokens"] == 8000


def test_the_prompt_asks_for_denial_of_the_whole_project_and_never_infers_from_silence() -> None:
    assert "Schweigt die Spezifikation" in CONDITIONS_PROMPT
    assert "nur für einen Teil des Vorhabens" in CONDITIONS_PROMPT
    assert CONDITIONS_PROMPT.endswith("Gib jede Bedingung der Liste genau einmal ab.")


@pytest.mark.parametrize(("bad", "reason"), [
    ({"conditions": [item("ki_system", affirming=[1])]}, "Bedingung fehlt: third_country"),
    ({"conditions": [*GOOD["conditions"], item("ki_system", denying=[2])]},
     "Bedingung mehrfach: ki_system"),
    ({"conditions": [*GOOD["conditions"], item("invented")]}, "Unbekannte Bedingung: invented"),
    ({"conditions": [item("ki_system", affirming=[99]), item("third_country")]},
     "ki_system: Zeilenbereich 99-99 ungültig"),
])
def test_one_retry_with_the_reason_then_the_answer_counts(bad: dict, reason: str) -> None:
    model = fake([bad, GOOD])

    results, corrections = run(model)

    assert results["ki_system"].value == "yes"
    assert corrections.retries == 1
    retry_prompt = str(model.messages[1][-1])  # type: ignore[attr-defined]
    assert reason in retry_prompt


def test_an_answer_that_stays_invalid_leaves_every_condition_unstated_without_failing() -> None:
    bad = {"conditions": [item("ki_system", affirming=[99])]}

    results, corrections = run(fake([bad]))

    assert {r.value for r in results.values()} == {"unstated"}
    assert all("Bedingungs-Vorlauf" in (r.note or "") for r in results.values())
    assert any("Bedingungs-Vorlauf" in text for text in corrections.unassigned(set()))
    reasons = [t for t in corrections.unassigned(set()) if "Zeilenbereich 99-99" in t]
    assert len(reasons) == 1  # the same reason of the first and the last attempt counts once


def test_a_broken_schema_after_the_retry_is_unstated_too() -> None:
    results, corrections = run(fake([{"conditions": "kaputt"}]))

    assert {r.value for r in results.values()} == {"unstated"}
    assert corrections.retries == 1


def test_a_failed_service_leaves_every_condition_unstated_with_its_own_reason() -> None:
    down = ModelHTTPError(503, "fake-model", {"error": "overloaded"})

    results, corrections = run(fake([down]))

    assert {r.value for r in results.values()} == {"unstated"}
    assert "nicht erreichbar" in (results["ki_system"].note or "")
    assert corrections.failed == []  # no fail closed, the audit goes on


def test_a_contradiction_is_reported_in_the_corrections() -> None:
    both = {"conditions": [item("ki_system", affirming=[1], denying=[3]), item("third_country")]}

    results, corrections = run(fake([both]))

    assert results["ki_system"].value == "yes"
    assert any("KI-System" in t and "Widerspruch" in t for t in corrections.unassigned(set()))


def test_the_spec_audit_has_seven_conditions_the_architecture_audit_none() -> None:
    assert len(conditions_for("spec")) == 7
    assert conditions_for("architecture") == []
