"""Build contract of the selection lists (DESIGN 1.2): the checkpoint before rules are written."""

from typing import Literal

from pydantic import BaseModel

from govguard.models import AuditType, SourceName


class Classification(BaseModel):  # written by the LLM, schema of tool classify_requirement
    testable: bool
    rationale: str
    cfn_resource_types: list[str] = []  # architecture only; always empty for a spec


class SelectedRequirement(BaseModel):
    requirement_id: str  # Requirement.id
    source: SourceName
    rationale: str  # Classification.rationale
    cfn_resource_types: list[str]


class Selection(BaseModel):  # file selection_spec.json or selection_arch.json
    audit_type: AuditType
    model_id: str
    selected: list[SelectedRequirement]


Outcome = Literal["selected", "prefiltered", "not_relevant", "not_testable", "llm_error"]


class Verdict(BaseModel):  # file verdicts_*.json: one entry per requirement of every source (SPEC)
    source: SourceName
    requirement_id: str
    title: str
    outcome: Outcome
    rationale: str  # from the LLM or a fixed sentence of the code
    cfn_resource_types: list[str]
