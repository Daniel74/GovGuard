"""Condition pre-run of the spec audit: what the specification says about the conditions (#60).

One LLM call before the packages collects evidence lines per condition; the code decides yes, no or
unstated (checks/conditions.py). Only an explicit denial turns rules N/A (ADR 0020, 0028). If the
call fails, every condition stays unstated and every rule goes to the model: no fail closed.
"""

import json

from pydantic_ai import RunContext
from pydantic_ai.exceptions import ModelAPIError, UnexpectedModelBehavior
from pydantic_ai.models import Model

from govguard.calls.model_call import (
    Answer,
    CallDeps,
    agents_for,
    ask,
    count_invalid_answer,
    count_retry,
    send_back,
)
from govguard.checks.conditions import (
    CONTRADICTION,
    answer_problems,
    condition_results,
    unstated_results,
)
from govguard.checks.corrections import Corrections, Problem, service_down
from govguard.checks.evidence import NUMBERED_LINES, numbered
from govguard.condition_models import ConditionDef, ConditionResult, ConditionsResponse

CONDITIONS_PROMPT = f"""\
Du stellst fest, was eine Spezifikation zu Bedingungen sagt, von denen Prüfregeln abhängen.
{NUMBERED_LINES}
Die Spezifikation ist eine offene Welt: Was sie nicht erwähnt, kann zutreffen oder nicht.
Nenne je Bedingung zwei Listen von Belegzeilen:
- "affirming": Zeilen, die das Kriterium "ja" erfüllen, also beschreiben, dass die
  Bedingung im Vorhaben zutrifft.
- "denying": Zeilen, die das Kriterium "nein" erfüllen, also ausdrücklich ausschließen,
  dass die Bedingung irgendwo im Vorhaben zutrifft.
Schließt eine Zeile die Bedingung nur für einen Teil des Vorhabens aus, etwa für einen
Zweck, eine Datenart oder eine Phase, gehört sie in keine der beiden Listen. Beispiel:
"Im Pilotbetrieb nutzt nur das Bauamt das System" schließt weitere Mandanten im
Regelbetrieb nicht aus.
Schweigt die Spezifikation zu einer Bedingung oder nennt sie das Thema ohne Festlegung,
bleiben beide Listen leer. Schließe nichts aus dem, was fehlt.
Ein Stichwort allein ist kein Beleg: Die Zeile muss festlegen, dass die Bedingung in
diesem Vorhaben zutrifft oder nicht.
Belegen und verneinen verschiedene Stellen dieselbe Bedingung, nenne beide.
Jeder Eintrag nennt "line_start" und "line_end", meist eine bis drei Zeilen.
Gib jede Bedingung der Liste genau einmal ab."""

_DOWN = ("Der Bedingungs-Vorlauf war nicht erreichbar oder überlastet: keine Bedingung "
         "festgestellt, alle Prüfregeln gehen ans Modell.")
_INVALID = ("Die Antwort des Bedingungs-Vorlaufs war auch nach einer Korrektur nicht verwertbar: "
            "keine Bedingung festgestellt, alle Prüfregeln gehen ans Modell.")


class ConditionsDeps(CallDeps):  # input of the validator; its retry counts like a package retry
    conditions: list[ConditionDef]
    input_text: str


def _validate(ctx: RunContext[ConditionsDeps], response: ConditionsResponse) -> ConditionsResponse:
    """One retry with the reasons; at the last attempt the caller falls back to unstated."""
    count_retry(ctx)
    deps = ctx.deps
    problems = answer_problems(deps.conditions, response.conditions, deps.input_text)
    seen = deps.corrections.retry_problems
    new = [Problem("", p) for p in problems if Problem("", p) not in seen]  # repeated: once
    deps.corrections.record_attempt([], {}, new, False)
    if problems and not ctx.last_attempt:
        send_back(ctx, "\n".join(problems))
    return response


_AGENTS = agents_for(
    Answer(ConditionsResponse, "submit_conditions",
           "Gib je Bedingung die belegenden und die verneinenden Zeilen ab.", strict=True),
    deps_type=ConditionsDeps, instructions=CONDITIONS_PROMPT, validator=_validate,
    settings={"temperature": 0, "max_tokens": 8000})  # a wrong denial hides rules (ADR 0020)


async def find_conditions(
    conditions: list[ConditionDef], input_text: str, model: Model, corrections: Corrections
) -> dict[str, ConditionResult]:
    """Spec audit only. Never raises for a model failure: the audit goes on with `unstated`."""
    deps = ConditionsDeps(conditions=conditions, input_text=input_text, corrections=corrections)
    try:
        answer = await ask(_AGENTS, model, _user_prompt(deps), deps)
    except UnexpectedModelBehavior:  # invalid after the retry; the validator never saw it
        count_invalid_answer(deps)
        return _unstated(conditions, _INVALID, corrections)
    except ModelAPIError as error:  # Groq rejects a broken answer with HTTP 400, no retry
        return _unstated(conditions, _DOWN if service_down(error) else _INVALID, corrections)
    if answer_problems(conditions, answer.conditions, input_text):  # still wrong after the retry
        return _unstated(conditions, _INVALID, corrections)
    results = condition_results(conditions, answer.conditions)
    for condition in conditions:
        if results[condition.id].note == CONTRADICTION:
            corrections.notes.append(f"Bedingung {condition.name}: {CONTRADICTION}")
    return results


def _unstated(
    conditions: list[ConditionDef], note: str, corrections: Corrections
) -> dict[str, ConditionResult]:
    corrections.notes.append(note)
    return unstated_results(conditions, note)


def _user_prompt(deps: ConditionsDeps) -> str:
    criteria = [c.model_dump(include={"id", "name", "meaning", "yes", "no"})
                for c in deps.conditions]
    return (
        f"Bedingungen:\n{json.dumps(criteria, ensure_ascii=False, indent=1)}\n\n"
        f"Eingabe:\n<eingabe>\n{numbered(deps.input_text)}\n</eingabe>"
    )
