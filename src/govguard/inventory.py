"""Resource inventory of an architecture: code for CloudFormation JSON, else an LLM pre-run.

Rules without a type from the inventory never reach the audit model (ADR 0007, 0011, 0015).
"""

import json
from dataclasses import dataclass

from pydantic import BaseModel
from pydantic_ai import Agent, ModelRetry, RunContext, ToolOutput
from pydantic_ai.models import Model

from govguard.corrections import Corrections, Problem
from govguard.models import InventoryResponse, RecognizedType, Rule
from govguard.text import MIN_QUOTE_LENGTH, contains_quote, template_resource_types

INVENTORY_PROMPT = """\
Du erkennst AWS-Dienste in einer Architekturbeschreibung.
Nenne jeden Ressourcentyp aus der Liste, den die Eingabe verwendet.
"evidence" ist ein wörtliches Zitat aus der Eingabe (mindestens 15 Zeichen), das den Dienst belegt.
Nenne keinen Typ ohne Beleg."""

NA_BY_CODE = "Ressourcentyp nicht im Template"
NA_NOT_RECOGNIZED = "Dienst in der Eingabe nicht erkannt"  # a gap stays visible (ADR 0011)
NA_FORBIDDEN = ("Die Eingabe ist ein CloudFormation-Template. Jede Prüfregel betrifft einen "
                "Ressourcentyp im Template: N/A ist hier verboten.")
NA_FORBIDDEN_FREE_TEXT = ("Jede Prüfregel betrifft einen Dienst, der in der Eingabe belegt ist "
                          "oder immer geprüft wird (IAM, KMS, Logs): N/A ist hier verboten.")


# Free text: rarely named, but present in every workload, so never N/A (ADR 0011)
ALWAYS_APPLICABLE = ("AWS::IAM::", "AWS::KMS::", "AWS::Logs::")


@dataclass(frozen=True)
class Inventory:
    types: set[str]
    na_rationale: str  # rationale of the N/A set by code
    na_forbidden: str  # prompt hint: rules sent to the model must not get N/A
    always: tuple[str, ...] = ()  # type prefixes that apply without being recognized

    def applies(self, rule: Rule) -> bool:
        return any(t in self.types or t.startswith(self.always) for t in rule.cfn_resource_types)


class InventoryDeps(BaseModel):  # deps_type of the pre-run agent, input for the code checks
    candidate_types: list[str]
    input_text: str
    corrections: Corrections  # the pre-run reports into it like a package (#27)
    reason_sent: bool = False  # the code sent the answer back with reasons (#27)


inventory_agent = Agent(
    output_type=ToolOutput(InventoryResponse, name="submit_inventory",
                           description="Gib die erkannten Ressourcentypen mit Beleg ab."),
    instructions=INVENTORY_PROMPT,
    deps_type=InventoryDeps,
    retries=1,  # exactly one retry, like the audit
)


@inventory_agent.output_validator
def _validate(ctx: RunContext[InventoryDeps], response: InventoryResponse) -> InventoryResponse:
    """The code checks type and evidence of every recognized service (ADR 0011)."""
    problems = [Problem("", p) for seen in response.resource_types  # names no rule
                if (p := _problem(seen, ctx.deps))]
    if ctx.retry:
        ctx.deps.corrections.record_retry(ctx.deps.reason_sent)
    ctx.deps.corrections.record_attempt([], {}, problems, ctx.last_attempt)
    if problems:
        ctx.deps.reason_sent = True
        raise ModelRetry("\n".join(p.text for p in problems))
    return response


def _problem(seen: RecognizedType, deps: InventoryDeps) -> str | None:
    if seen.resource_type not in deps.candidate_types:
        return f"{seen.resource_type}: Typ steht nicht in der Liste"
    if not contains_quote(deps.input_text, seen.evidence):
        return (f"{seen.resource_type}: Beleg ist kein wörtliches Zitat aus der Eingabe "
                f"(mind. {MIN_QUOTE_LENGTH} Zeichen)")
    return None


async def resource_inventory(
    rules: list[Rule], input_text: str, model: Model, corrections: Corrections
) -> Inventory:
    """Architecture audit only; the spec audit sends every rule to the model."""
    types = template_resource_types(input_text)
    if types is not None:
        return Inventory(types, NA_BY_CODE, NA_FORBIDDEN)
    candidates = sorted({t for rule in rules for t in rule.cfn_resource_types})
    deps = InventoryDeps(candidate_types=candidates, input_text=input_text,
                         corrections=corrections)
    result = await inventory_agent.run(_user_prompt(deps), model=model, deps=deps)
    seen = {item.resource_type for item in result.output.resource_types}
    return Inventory(seen, NA_NOT_RECOGNIZED, NA_FORBIDDEN_FREE_TEXT, ALWAYS_APPLICABLE)


def _user_prompt(deps: InventoryDeps) -> str:
    return (
        f"Ressourcentypen:\n{json.dumps(deps.candidate_types, indent=1)}\n\n"
        f"Eingabe:\n<eingabe>\n{deps.input_text}\n</eingabe>"
    )
