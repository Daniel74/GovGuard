"""Applicable rules run in parallel packages of about 10 (ADR 0011)."""

import asyncio

import pytest
from conftest import make_rule
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from govguard.audit_engine import AuditValidationError, run_audit
from govguard.models import RuleCatalog

INPUT = "Alle Zugriffe erfolgen ausschließlich über TLS 1.3."


def catalog_of(n: int) -> RuleCatalog:
    return RuleCatalog(audit_type="spec", source_versions={"DSGVO": "2016/679"},
                       model_id="fake-model",
                       rules=[make_rule(f"Art.{i}", f"Regel {i}") for i in range(1, n + 1)])


def rule_ids_in(messages: list[ModelMessage]) -> list[str]:
    return [r.split('"')[0] for r in str(messages[0]).split('"id": "')[1:]]


class Recorder:
    """Fake LLM: answers WARN for each rule ID in its prompt, records packages and concurrency."""

    def __init__(self) -> None:
        self.packages: list[list[str]] = []
        self.running = self.max_running = 0

    async def respond(self, messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        self.running += 1
        self.max_running = max(self.max_running, self.running)
        await asyncio.sleep(0.01)
        self.running -= 1
        rule_ids = rule_ids_in(messages)
        self.packages.append(rule_ids)
        findings = [{"rule_id": r, "status": "WARN", "line_start": None, "line_end": None,
                     "rationale": "Unklar.", "recommendation": "Nachweisen."} for r in rule_ids]
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": findings})])


def test_rules_are_audited_in_parallel_packages_of_ten(trace) -> None:
    recorder = Recorder()

    report = run_audit(catalog_of(23), INPUT, FunctionModel(recorder.respond), trace)

    assert sorted(len(p) for p in recorder.packages) == [3, 10, 10]
    assert recorder.max_running == 3
    assert [f.rule_id for f in report.findings] == [f"SPEC-DSGVO-Art.{i}" for i in range(1, 24)]


class ForgetsOneRule(Recorder):
    """Leaves out the last rule in every turn, so its package stays invalid after the retry."""

    async def respond(self, messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        response = await super().respond(messages, info)
        findings = response.parts[0].args["findings"]
        kept = [f for f in findings if f["rule_id"] != "SPEC-DSGVO-Art.23"]
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": kept})])


def test_one_invalid_package_fails_the_whole_audit(trace) -> None:
    with pytest.raises(AuditValidationError):
        run_audit(catalog_of(23), INPUT, FunctionModel(ForgetsOneRule().respond), trace)


def test_throttling_fails_closed(trace) -> None:
    def throttled(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        raise ModelHTTPError(status_code=429, model_name="fake-model", body="ThrottlingException")

    with pytest.raises(AuditValidationError):
        run_audit(catalog_of(23), INPUT, FunctionModel(throttled), trace)


def test_merged_packages_are_checked_for_one_finding_per_rule(trace) -> None:
    catalog = catalog_of(11)  # rule 11 repeats the ID of rule 1 in the second package
    catalog.rules[10] = make_rule("Art.1", "Regel 1 doppelt")

    with pytest.raises(AuditValidationError, match="Mehr als ein Befund für: SPEC-DSGVO-Art.1"):
        run_audit(catalog, INPUT, FunctionModel(Recorder().respond), trace)
