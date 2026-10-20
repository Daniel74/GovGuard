"""The spec audit asks the conditions first; a denied condition makes its rules N/A (#60)."""

import json

from conftest import make_rule
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from test_run_audit_progress import as_tuples

from govguard.audit_engine import run_audit
from govguard.audit_setup import conditions_for
from govguard.models import Progress, RuleCatalog

CONDITIONS = conditions_for("spec")


INPUT = ("Das Portal nutzt kein KI-System.\n"
         "Alle Daten bleiben in der EU, es gibt keine Übermittlung in ein Drittland.\n"
         "Die Daten liegen verschlüsselt in der Datenbank des Amts.\n")


def item(condition_id: str, affirming=(), denying=()) -> dict:
    return {"condition_id": condition_id,
            "affirming": [{"line_start": a, "line_end": a} for a in affirming],
            "denying": [{"line_start": d, "line_end": d} for d in denying]}


def conditions_answer(denied: dict[str, int]) -> dict:
    ids = ["ki_system", "high_risk_ai", "third_country", "processor", "consent", "multi_tenant",
           "automated_decision"]
    return {"conditions": [item(i, denying=[denied[i]] if i in denied else []) for i in ids]}


def catalog_of(*anchors: str) -> RuleCatalog:
    """One rule per anchor, e.g. "KI-VO Art. 50": id SPEC-DSGVO-<n> with that anchor."""
    rules = [make_rule(f"R{n}", f"Regel {n}").model_copy(update={"primary_anchor": a})
             for n, a in enumerate(anchors, 1)]
    return RuleCatalog(audit_type="spec", source_versions={"DSGVO": "2016/679"},
                       model_id="fake-model", rules=rules)


def fake(conditions: dict | Exception, audited: list[str]) -> FunctionModel:
    """The pre-run answers `conditions`; the audit marks every rule it gets as WARN."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        tool = info.output_tools[0].name
        if tool == "submit_conditions":
            if isinstance(conditions, Exception):
                raise conditions
            return ModelResponse(parts=[ToolCallPart(tool, conditions)])
        ids = [r.split('"')[0] for r in str(messages[0]).split('"id": "')[1:]]
        audited.extend(ids)
        findings = [{"rule_id": r, "status": "WARN", "line_start": None, "line_end": None,
                     "rationale": "Unklar.", "recommendation": "Nachweisen."} for r in ids]
        return ModelResponse(parts=[ToolCallPart(tool, {"findings": findings})])

    return FunctionModel(respond, model_name="fake-model")


CATALOG = catalog_of("KI-VO Art. 50 Abs. 1", "DSGVO Art. 46 Abs. 1", "DSGVO Art. 32 Abs. 1")


def audit(model: FunctionModel, trace, **kwargs):
    return run_audit(CATALOG, INPUT, model, trace, conditions=CONDITIONS, **kwargs)


def test_a_denied_condition_makes_its_rules_na_with_the_denying_line(trace) -> None:
    audited: list[str] = []

    report = audit(fake(conditions_answer({"ki_system": 1, "third_country": 2}), audited), trace)

    by_rule = {f.rule_id: f for f in report.findings}
    ki, third, other = (by_rule[f"SPEC-DSGVO-R{n}"] for n in (1, 2, 3))
    assert (ki.status, ki.evidence) == ("N/A", "Das Portal nutzt kein KI-System.")
    assert ki.rationale == "Die Spezifikation verneint: KI-System."
    assert (third.status, third.line_start) == ("N/A", 2)
    assert other.status == "WARN"
    assert audited == ["SPEC-DSGVO-R3"]  # the N/A rules never reach the model
    assert report.overall_status == "WARN"


def test_the_report_keeps_value_and_evidence_per_condition(trace) -> None:
    report = audit(fake(conditions_answer({"ki_system": 1}), []), trace)

    assert report.conditions["ki_system"].value == "no"
    assert report.conditions["ki_system"].denying[0].line_start == 1
    assert report.conditions["high_risk_ai"].value == "no"  # follows from no AI system
    assert report.conditions["consent"].value == "unstated"
    assert json.loads(report.model_dump_json())["conditions"]["ki_system"]["value"] == "no"


def test_without_a_denial_every_rule_goes_to_the_model(trace) -> None:
    audited: list[str] = []

    report = audit(fake(conditions_answer({}), audited), trace)

    assert sorted(audited) == ["SPEC-DSGVO-R1", "SPEC-DSGVO-R2", "SPEC-DSGVO-R3"]
    assert {f.status for f in report.findings} == {"WARN"}


def test_the_pre_run_is_reported_before_the_packages(trace) -> None:
    seen: list[Progress] = []

    audit(fake(conditions_answer({}), []), trace, on_progress=seen.append)

    assert as_tuples(seen) == [("conditions", 0, 0), ("packages", 0, 1), ("packages", 1, 1)]


def test_a_failed_pre_run_does_not_fail_the_audit(trace) -> None:
    audited: list[str] = []
    down = ModelHTTPError(503, "fake-model", {"error": "overloaded"})

    report = audit(fake(down, audited), trace)

    assert len(audited) == 3  # no rule was decided by code
    assert {c.value for c in report.conditions.values()} == {"unstated"}
    assert any("Bedingungs-Vorlauf" in text for text in report.unassigned_corrections)


def test_the_high_risk_rules_are_na_with_the_reason_that_no_ai_system_is_used(trace) -> None:
    catalog = catalog_of("KI-VO Art. 14 Abs. 1")

    report = run_audit(catalog, INPUT, fake(conditions_answer({"ki_system": 1}), []), trace,
                       conditions=CONDITIONS)

    finding = report.findings[0]
    assert (finding.status, finding.rationale) == (
        "N/A", "Die Spezifikation verneint: KI-System.")
    assert finding.evidence == "Das Portal nutzt kein KI-System."


def test_without_conditions_there_is_no_pre_run_and_no_report_entry(trace) -> None:
    audited: list[str] = []
    seen: list[Progress] = []

    report = run_audit(CATALOG, INPUT, fake(conditions_answer({"ki_system": 1}), audited), trace,
                       on_progress=seen.append)

    assert len(audited) == 3 and report.conditions == {}
    assert [p.phase for p in seen] == ["packages"] * 2


def test_the_architecture_audit_runs_no_pre_run_even_with_conditions(
    arch_catalog: RuleCatalog, bucket_template: str, trace
) -> None:
    tools: list[str] = []
    seen: list[Progress] = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        tools.append(info.output_tools[0].name)
        ids = [r.split('"')[0] for r in str(messages[0]).split('"id": "')[1:]]
        findings = [{"rule_id": r, "status": "WARN", "line_start": None, "line_end": None,
                     "rationale": "Unklar.", "recommendation": "Nachweisen."} for r in ids]
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": findings})])

    report = run_audit(arch_catalog, bucket_template, FunctionModel(respond), trace,
                       on_progress=seen.append, conditions=CONDITIONS)

    assert tools == ["submit_audit"] and "conditions" not in {p.phase for p in seen}
    assert report.conditions == {}
