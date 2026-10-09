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
    pinned: bool  # pinned anchor from a preset (ADR 0007)
    rank: int  # 1 = first within the source


class Selection(BaseModel):  # file selection_spec.json or selection_arch.json
    audit_type: AuditType
    model_id: str
    selected: list[SelectedRequirement]


class Verdict(BaseModel):  # local report for the checkpoint: what the LLM said, what the code did
    source: SourceName
    requirement_id: str
    title: str
    testable: bool
    rationale: str
    cfn_resource_types: list[str]
    outcome: Literal[
        "pinned", "selected", "over_cap", "not_relevant", "not_testable", "llm_error"
    ]
