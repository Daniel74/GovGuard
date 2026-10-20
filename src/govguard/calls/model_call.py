"""One model call at runtime: the agent per provider and the retry booking (ADR 0005, 0016, #56).

The three callers (audit packages, inventory, FAIL judge) bring prompt, answer schema and their
own check. Where the provider-specific output type and the retry count live is decided here.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, NoReturn

from pydantic import BaseModel
from pydantic_ai import Agent, ModelRetry, NativeOutput, RunContext, ToolOutput
from pydantic_ai.models import Model

from govguard.checks.corrections import Corrections
from govguard.models import Provider, provider_of

RETRIES = 1  # one retry: within the 180 s (ADR 0018)

type Agents[T] = dict[Provider, Agent[Any, T]]


class CallDeps(BaseModel):  # base of the deps_type of every caller; the validator reports into it
    corrections: Corrections  # shared by all calls of one audit (#27)
    reason_sent: bool = False  # the code sent the answer back with reasons (#27)


@dataclass(frozen=True)
class Answer[T: BaseModel]:  # what the model must hand in: the schema and how it reaches the code
    schema: type[T]
    name: str  # tool name under ToolOutput, schema name under NativeOutput
    description: str
    strict: bool | None = None  # of the Bedrock tool; Groq NativeOutput is always strict


def agents_for[T: BaseModel](
    answer: Answer[T], *, deps_type: type[CallDeps], instructions: Any,
    validator: Callable[..., Any], settings: dict[str, Any],
) -> Agents[T]:
    """One agent per provider with the same validator: the gates are equal for both models.

    Bedrock: forced tool, `ToolOutput` (ADR 0005). Groq: json_schema with constrained decoding,
    `NativeOutput` (ADR 0016): Groq has no forced tool with `strict`, so NativeOutput.
    """
    spec = {"name": answer.name, "description": answer.description, "strict": answer.strict}
    outputs = {"bedrock": ToolOutput(answer.schema, **spec),
               "groq": NativeOutput(answer.schema, **{**spec, "strict": True})}  # ADR 0017
    agents: Agents[T] = {}
    for provider, output in outputs.items():
        agent = Agent(output_type=output, instructions=instructions, deps_type=deps_type,
                      model_settings=settings, retries=RETRIES)
        agent.output_validator(validator)
        agents[provider] = agent
    return agents


async def ask[T](agents: Agents[T], model: Model, prompt: str, deps: CallDeps) -> T:
    """Run the agent of the model's provider and return the validated answer."""
    result = await agents[provider_of(model)].run(prompt, model=model, deps=deps)
    return result.output


def count_retry(ctx: RunContext[CallDeps]) -> None:
    """First thing in a validator. Only a retry counts; without a reason from the code before it
    the schema broke (#27)."""
    if ctx.retry:
        ctx.deps.corrections.record_retry(ctx.deps.reason_sent)


def count_invalid_answer(deps: CallDeps) -> None:
    """The answer stayed invalid after the retry and the validator never saw it (#27)."""
    deps.corrections.record_retry(deps.reason_sent)


def send_back(ctx: RunContext[CallDeps], reason: str) -> NoReturn:
    """Send the answer back to the model with the reason the code found (one retry, #27)."""
    ctx.deps.reason_sent = True
    raise ModelRetry(reason)
