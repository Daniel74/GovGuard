"""Pydantic contracts of the audit (DESIGN 1.2, 1.4, 2.1, 2.4). Names follow CONTEXT.md.

Draft pattern: the LLM fills only *Draft models; the code adds what it already knows.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Status = Literal["PASS", "WARN", "FAIL", "N/A"]
# Worst status wins; N/A only if every finding is N/A (DESIGN 2.1)
SEVERITY: dict[Status, int] = {"N/A": 0, "PASS": 1, "WARN": 2, "FAIL": 3}
AuditType = Literal["spec", "architecture"]
SourceName = Literal["BSI", "C5", "CIS", "DSGVO", "FSBP", "SDM"]
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


class RuleCatalog(BaseModel):  # file rules_spec.json or rules_arch.json
    audit_type: AuditType
    source_versions: dict[str, str]
    model_id: str
    rules: list[Rule] = Field(min_length=1)  # an empty catalog has no overall status


class FindingDraft(BaseModel):  # written by the LLM, one item of submit_audit; no defaults (strict)
    rule_id: str
    status: Status
    line_start: int | None  # evidence by line reference (ADR 0017); required for PASS and FAIL
    line_end: int | None
    rationale: str
    recommendation: str | None  # required for WARN and FAIL


class AuditResponse(BaseModel):  # schema of tool submit_audit
    findings: list[FindingDraft]


class RecognizedType(BaseModel):  # written by the LLM, one item of tool submit_inventory
    resource_type: str  # must be a type of the catalog
    evidence: str  # verbatim quote from the input that names the service


class InventoryResponse(BaseModel):  # schema of tool submit_inventory (free-text pre-run)
    resource_types: list[RecognizedType]


class Finding(FindingDraft):  # completed by the code from the input and the catalog
    evidence: str | None  # cut from the input lines by the code: verbatim by construction
    title: str
    primary_anchor: str
    cross_references: list[CrossReference]
    downgraded_from: Status | None = None  # original status if the code downgraded it (ADR 0017)
    corrections: list[str] = []  # readable reasons for retry and downgrade, same text as the retry


class Trace(BaseModel):  # links a report to input, knowledge base and deploy (ADR 0006)
    audit_id: str
    input_sha256: str  # hash only, never the input itself
    catalog_sha256: str
    kb_commit: str


class FailJudgeCount(BaseModel):  # verdicts of the FAIL judge in one spec audit (#31)
    checked: int = 0
    confirmed: int = 0
    downgraded: int = 0  # set to WARN, the reason stands in the finding's corrections
    unavailable: int = 0  # judge failed or gave no verdict: the FAIL stays unchecked


class Progress(BaseModel):  # reported while an audit runs, for UI and audit job (ADR 0023)
    phase: Literal["inventory", "packages", "fail_judge"]
    packages_done: int = 0
    packages_total: int = 0  # counts belong to phase "packages" only, known after the inventory


class AuditReport(BaseModel):
    audit_type: AuditType
    overall_status: Status
    findings: list[Finding]  # exactly one per rule, sorted by first resource type (ADR 0011)
    model_id: str
    trace: Trace
    unassigned_corrections: list[str] = []  # reasons without a finding, e.g. an unknown rule_id
    retries: int = 0  # packages and the FAIL judge sent back once; no per-package view (#27)
    fail_judge: FailJudgeCount = FailJudgeCount()


class AuditEvent(BaseModel):  # one JSON line in CloudWatch Logs, no evidence (DSGVO Art. 5(1)(c))
    event: Literal["audit_event"] = "audit_event"
    timestamp: datetime  # UTC
    endpoint: Literal["/audit/spec", "/audit/architecture", "/archetype/select"]
    outcome: Literal["ok", "rejected", "validation_failed"]
    trace: Trace
    model_id: str
    overall_status: Status | None
    statuses: dict[str, Status]  # rule_id -> status
    retries: int  # packages with a retry, a count only (#27)
    downgrades: int  # findings the code set to WARN (#27)
    archetype: str | None


class RequiredFinding(BaseModel):  # set by a human, never by a previous run
    anchor: str  # primary anchor, e.g. "DSGVO Art. 9" - stable across builds
    status: Literal["PASS", "FAIL"]  # never WARN: judgement would make the preset gate flicker


class Expected(BaseModel):
    overall_status: Status
    required_findings: list[RequiredFinding]
    archetype: ArchetypeId | None = None


class Preset(BaseModel):  # file data/input/presets/<id>/preset.json
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
