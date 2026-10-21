"""Audit packages: about 10 rules per model call, in parallel; the same gates for every model.

Pure logic, the model is injected (ADR 0005, 0011, 0016).
"""

import asyncio
import json
from collections.abc import Coroutine
from typing import Any

from pydantic_ai import RunContext
from pydantic_ai.models import Model

from govguard.calls.model_call import Answer, CallDeps, agents_for, ask, count_retry, send_back
from govguard.checks.audit_gates import answer_problems
from govguard.checks.corrections import Corrections, downgrades_of
from govguard.checks.evidence import MAX_SPAN, NUMBERED_LINES, numbered, without_unproven_verdict
from govguard.checks.repairs import with_rule_recommendations, worst_of_duplicates
from govguard.checks.token_budget import GROQ_TOKENS_PER_MINUTE, TokenBudget, estimated_tokens
from govguard.models import AuditResponse, FindingDraft, Provider, Rule, provider_of
from govguard.open_world import AuditInput, OpenWorld

SYSTEM_PROMPT = f"""\
Du bist ein Compliance-Prüfer für Behörden-IT. Bewerte die Eingabe gegen jede Prüfregel.
- PASS: Einhaltung ist in der Eingabe belegt.
- FAIL: Ein Verstoß ist in der Eingabe belegt.
- WARN: Aus der Eingabe nicht entscheidbar.
- N/A: Die Prüfregel ist auf die Eingabe nicht anwendbar.
{NUMBERED_LINES} Belege per Zeilenbereich:
"line_start" und "line_end" nennen die Zeilen, die den Befund belegen (höchstens {MAX_SPAN} Zeilen).
Bei PASS und FAIL sind sie Pflicht, sonst null.
Bei WARN und FAIL ist "recommendation" Pflicht. Schreibe Begründungen auf Deutsch."""
# Open world only; a template is a closed world: missing means default (ADR 0020, #46)
OPEN_WORLD_FAIL_RULE = """\
{subject} (offene Welt): Was die Eingabe nicht erwähnt, kann anderswo geregelt sein. \
Beschreibt "violation_if" ein Fehlen, belegt fehlender Text nur "nicht beschrieben": WARN. FAIL \
nur, wenn die Belegzeilen etwas festlegen, das der Prüfregel widerspricht; "rationale" nennt es."""

type PackageRequest = Coroutine[Any, Any, list[FindingDraft]]  # one model call, not yet awaited
PACKAGE_SIZE = 10  # rules per model call; 166 architecture rules -> 17 parallel calls
GROQ_MAX_PARALLEL = 2  # ~110,000 tokens/min per slot measured (#26), Groq tier allows 250,000


class AuditDeps(CallDeps):  # deps_type of the audit agent, input for the code checks
    rules: list[Rule]
    input_text: str
    na_forbidden: str | None  # prompt hint; set when N/A was already decided by code (ADR 0011)
    world: OpenWorld | None  # None: closed world, a template (ADR 0020, #46)


_SETTINGS = {"temperature": 0, "max_tokens": 8000}  # same status; a loop ends in ~25 s (#28)
# Bedrock: no limit, all packages at once
_MAX_PARALLEL: dict[Provider, int] = {"groq": GROQ_MAX_PARALLEL}


def _budget_for(provider: Provider) -> TokenBudget | None:
    """Groq also needs a token budget per minute: a large input breaks the tier limit (#53)."""
    return TokenBudget(GROQ_TOKENS_PER_MINUTE) if provider == "groq" else None


def _validate(ctx: RunContext[AuditDeps], response: AuditResponse) -> AuditResponse:
    """Repair and downgrade first, then check: what the code can fix needs no retry (ADR 0017)."""
    text, last, rules = ctx.deps.input_text, ctx.last_attempt, ctx.deps.rules
    count_retry(ctx)  # once per package: one retry at most
    kept, contradictions = worst_of_duplicates(response.findings)
    checked = [without_unproven_verdict(f, text, last) for f in kept]
    filled, filled_in = with_rule_recommendations(checked, rules)
    expected = {rule.id for rule in rules}
    problems = answer_problems(expected, filled, text, ctx.deps.na_forbidden)
    ctx.deps.corrections.record_repairs(expected, contradictions + filled_in)
    ctx.deps.corrections.record_attempt(
        sorted(expected), downgrades_of(kept, checked), problems, last)
    if problems:
        send_back(ctx, "\n".join(p.text for p in problems))
    return AuditResponse(findings=filled)


def _status_rule(ctx: RunContext[AuditDeps]) -> str:
    world = ctx.deps.world
    return OPEN_WORLD_FAIL_RULE.format(subject=world.subject) if world else ""


_AGENTS = agents_for(
    Answer(AuditResponse, "submit_audit", "Gib genau einen Befund je Prüfregel ab.",
           strict=True),  # static schema, every field required (ADR 0017)
    deps_type=AuditDeps, instructions=[SYSTEM_PROMPT, _status_rule], validator=_validate,
    settings=_SETTINGS)


def package_requests(
    rules: list[Rule], given: AuditInput, na_forbidden: str | None, model: Model,
    corrections: Corrections,
) -> list[PackageRequest]:
    """One request per package, run in parallel within the 300 s (ADR 0023); Groq throttled by
    parallel slots and a token budget per minute (#53).
    """
    packages = [rules[i:i + PACKAGE_SIZE] for i in range(0, len(rules), PACKAGE_SIZE)]
    slots = asyncio.Semaphore(_MAX_PARALLEL.get(provider_of(model), len(packages) or 1))
    budget = _budget_for(provider_of(model))  # one per audit; retries are not counted

    async def ask(package: list[Rule]) -> list[FindingDraft]:
        async with slots:
            deps = AuditDeps(rules=package, input_text=given.text, na_forbidden=na_forbidden,
                             world=given.world, corrections=corrections)
            if budget is not None:
                prompt = SYSTEM_PROMPT + _user_prompt(deps)
                await budget.take(estimated_tokens(prompt, _SETTINGS["max_tokens"]))
            return await _ask_model(deps, model)

    return [ask(p) for p in packages]


async def _ask_model(deps: AuditDeps, model: Model) -> list[FindingDraft]:
    answer = await ask(_AGENTS, model, _user_prompt(deps), deps)
    return answer.findings


def _user_prompt(deps: AuditDeps) -> str:
    rules = [
        r.model_dump(include={"id", "title", "compliant_if", "violation_if"})
        for r in deps.rules
    ]
    hint = f"{deps.na_forbidden}\n\n" if deps.na_forbidden else ""
    return (
        f"Prüfregeln:\n{json.dumps(rules, ensure_ascii=False, indent=1)}\n\n{hint}"
        f"Eingabe:\n<eingabe>\n{numbered(deps.input_text)}\n</eingabe>"
    )
