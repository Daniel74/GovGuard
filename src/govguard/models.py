"""Pydantic contracts of the audit (DESIGN 1.2, 1.4, 2.1, 2.4). Names follow CONTEXT.md.

Draft pattern: the LLM fills only *Draft models; the code adds what it already knows.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Status = Literal["PASS", "WARN", "FAIL", "N/A"]
AuditType = Literal["spec", "architecture"]
SourceName = Literal["BSI", "CIS", "DSGVO", "SDM"]
ArchetypeId = Literal["ARCH-01", "ARCH-02", "ARCH-03", "NONE"]


class CrossReference(BaseModel):
    anchor: str  # primary anchor format of another source
    origin: Literal["ai_suggested"]


class RuleDraft(BaseModel):  # written by the LLM, schema of tool formulate_rule
    source_quote: str
    title: str
    compliant_if: str
    violation_if: str
    recommendation: str
    cross_references: list[CrossReference] = []


class Rule(RuleDraft):  # completed by the code
    id: str  # "<SPEC|ARCH>-<SOURCE>-<Requirement.id without spaces>"
    audit_type: AuditType
    source: SourceName
    primary_anchor: str
    selection_rationale: str
    cfn_resource_types: list[str] = []  # architecture only
    rank: int
    pinned: bool = False


class RuleCatalog(BaseModel):  # file rules_spec.json or rules_arch.json
    audit_type: AuditType
    source_versions: dict[str, str]
    model_id: str
    rules: list[Rule] = Field(min_length=1)  # an empty catalog has no overall status


class FindingDraft(BaseModel):  # written by the LLM, one item of tool submit_audit
    rule_id: str
    status: Status
    evidence: str | None  # verbatim quote from the input; required for PASS and FAIL
    rationale: str
    recommendation: str | None  # required for WARN and FAIL


class AuditResponse(BaseModel):  # schema of tool submit_audit
    findings: list[FindingDraft]


class Finding(FindingDraft):  # completed by the code from the catalog
    title: str
    primary_anchor: str
    cross_references: list[CrossReference]


class Trace(BaseModel):  # links a report to input, knowledge base and deploy (ADR 0006)
    audit_id: str
    input_sha256: str  # hash only, never the input itself
    catalog_sha256: str
    kb_commit: str


class AuditReport(BaseModel):
    audit_type: AuditType
    overall_status: Status
    findings: list[Finding]  # exactly one per rule, in catalog order
    model_id: str
    trace: Trace


class AuditEvent(BaseModel):  # one JSON line in CloudWatch Logs, no evidence (DSGVO Art. 5(1)(c))
    event: Literal["audit_event"] = "audit_event"
    timestamp: datetime  # UTC
    endpoint: Literal["/audit/spec", "/audit/architecture", "/archetype/select"]
    outcome: Literal["ok", "rejected", "validation_failed"]
    trace: Trace
    model_id: str
    overall_status: Status | None
    statuses: dict[str, Status]  # rule_id -> status
    archetype: str | None


class RequiredFinding(BaseModel):  # set by a human, never by a previous run
    anchor: str  # primary anchor, e.g. "DSGVO Art. 9" - stable across builds
    status: Literal["PASS", "FAIL"]  # never WARN: judgement would make the preset gate flicker


class Expected(BaseModel):
    overall_status: Status
    required_findings: list[RequiredFinding]
    archetype: ArchetypeId | None = None


class Preset(BaseModel):  # file data/presets/<id>/preset.json
    title: str  # shown in the UI, German
    audit_type: AuditType
    input_file: str  # next to preset.json, max. 100,000 characters
    expected: Expected

    @model_validator(mode="after")
    def archetype_only_for_spec_without_fail(self) -> "Preset":
        allowed = self.audit_type == "spec" and self.expected.overall_status != "FAIL"
        if self.expected.archetype is not None and not allowed:
            raise ValueError("archetype is only expected for a spec audit without FAIL")
        return self
