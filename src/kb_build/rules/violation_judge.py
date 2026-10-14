"""Second LLM opinion on a spec rule: does `violation_if` describe a stipulation? (#29)

Open world (ADR 0020): silence is WARN, so only a stipulation in the spec can be a violation.
Whether a sentence stipulates is a question of meaning, no word list decides it.
Pure logic: the formulate validator passes in the model and its usage.
"""

from pydantic import BaseModel
from pydantic_ai import Agent, ToolOutput
from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

PROMPT = """\
Du prüfst das Verstoßkriterium ("violation_if") einer Prüfregel für das Spec-Audit einer
fachlichen Spezifikation. Eine Spezifikation ist eine offene Welt: Was sie nicht erwähnt,
kann anderswo geregelt sein. Ein Verstoßkriterium muss deshalb beschreiben, was die
Spezifikation festlegt, nicht, was ihr fehlt.
- Festlegung: Die Spezifikation legt etwas fest, das der Anforderung widerspricht, oder
  erklärt einen Verzicht oder Aufschub. Beispiel: "Die Spezifikation legt als Exportformat
  nur PDF fest." oder "Die Spezifikation erklärt, dass ein Datenexport erst später kommt."
- Fehlen: Der Verstoß besteht darin, dass etwas nicht, nur vage oder unvollständig
  beschrieben ist. Beispiel: "Die Spezifikation nennt kein maschinenlesbares Exportformat."
Enthält das Kriterium beides (z. B. verbunden mit "oder"), gilt es als Fehlen.
"describes_absence": true bei Fehlen, sonst false. "reason": ein Satz, woran du es erkennst."""

USER_PROMPT = "<violation_if>\n{text}\n</violation_if>"
JUDGE_TOOL_NAME = "judge_violation"
JUDGE_RETRIES = 2  # a schema slip only; the verdict itself is never retried


class ViolationCheck(BaseModel):  # schema of tool judge_violation
    describes_absence: bool
    reason: str


judge_agent = Agent(
    output_type=ToolOutput(ViolationCheck, name=JUDGE_TOOL_NAME,
                           description="Gib dein Urteil zum Verstoßkriterium ab."),
    instructions=PROMPT,
    retries=JUDGE_RETRIES,
    model_settings={"temperature": 0},
)


async def judge_violation(violation_if: str, model: Model, usage: RunUsage) -> ViolationCheck:
    """`usage` is the one of the formulate run: the judge's tokens count there too."""
    result = await judge_agent.run(USER_PROMPT.format(text=violation_if), model=model, usage=usage)
    return result.output
