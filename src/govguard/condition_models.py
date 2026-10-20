"""Pydantic contracts of the condition pre-run (#60, ADR 0028). Names follow CONTEXT.md.

A condition ("Bedingung") is a fact about the project that some rules depend on, e.g. "an AI system
is in use". Draft pattern as in models.py: the LLM fills only the *Draft models.
"""

from typing import Literal

from pydantic import BaseModel

ConditionValue = Literal["yes", "no", "unstated"]


class LineRange(BaseModel):  # evidence by line reference (ADR 0017); no defaults (strict)
    line_start: int
    line_end: int


class ConditionDef(BaseModel):  # one entry of data/input/conditions.json, maintained by hand
    id: str
    name: str  # German, used in "Die Spezifikation verneint: <name>."
    only_if: str  # "<rule group> only if <only_if>"
    meaning: str  # explains the condition to the model and to the user
    yes: str  # criterion for "yes"
    no: str  # criterion for "no"
    anchors: list[str] = []  # article anchors, e.g. "DSGVO Art. 4": exact article, not "Art. 44"
    rule_ids: list[str] = []  # explicit rules without an article anchor (SDM)


class ConditionDraft(BaseModel):  # written by the LLM, one item of submit_conditions
    condition_id: str
    affirming: list[LineRange]  # lines that satisfy the "yes" criterion
    denying: list[LineRange]  # lines that satisfy the "no" criterion


class ConditionsResponse(BaseModel):  # schema of tool submit_conditions
    conditions: list[ConditionDraft]


class ConditionResult(BaseModel):  # decided by the code from the evidence, stored in the report
    value: ConditionValue
    affirming: list[LineRange] = []
    denying: list[LineRange] = []
    note: str | None = None  # e.g. "Widerspruch", or why the pre-run could not decide
    derived_from: str | None = None  # id of the condition whose denial decided this "no"
