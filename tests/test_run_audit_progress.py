"""run_audit reports its progress: phase and finished packages (ADR 0023)."""

from conftest import make_rule
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from test_run_audit import PASS_32
from test_run_audit_fail_judge import FAIL_9, audit_and_judge

from govguard.audit_engine import run_audit
from govguard.models import Progress, RuleCatalog

INPUT = "Alle Zugriffe erfolgen ausschließlich über TLS 1.3."


def spec_catalog_of(n: int) -> RuleCatalog:
    return RuleCatalog(audit_type="spec", source_versions={"DSGVO": "2016/679"},
                       model_id="fake-model",
                       rules=[make_rule(f"Art.{i}", f"Regel {i}") for i in range(1, n + 1)])


def rule_ids_in(messages: list[ModelMessage]) -> list[str]:
    return [r.split('"')[0] for r in str(messages[0]).split('"id": "')[1:]]


def warn_for_every_rule(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    findings = [{"rule_id": r, "status": "WARN", "line_start": None, "line_end": None,
                 "rationale": "Unklar.", "recommendation": "Nachweisen."}
                for r in rule_ids_in(messages)]
    return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": findings})])


def as_tuples(seen: list[Progress]) -> list[tuple[str, int, int]]:
    return [(p.phase, p.packages_done, p.packages_total) for p in seen]


def test_spec_audit_reports_every_finished_package(trace) -> None:
    seen: list[Progress] = []

    run_audit(spec_catalog_of(23), INPUT, FunctionModel(warn_for_every_rule), trace,
              on_progress=seen.append)

    assert as_tuples(seen) == [("packages", 0, 3), ("packages", 1, 3), ("packages", 2, 3),
                               ("packages", 3, 3)]


def test_without_a_callback_the_audit_runs_as_before(trace) -> None:
    report = run_audit(spec_catalog_of(3), INPUT, FunctionModel(warn_for_every_rule), trace)

    assert report.overall_status == "WARN"


def test_architecture_audit_reports_the_inventory_before_the_packages(
    arch_catalog: RuleCatalog, bucket_template: str, trace
) -> None:
    seen: list[Progress] = []

    run_audit(arch_catalog, bucket_template, FunctionModel(warn_for_every_rule), trace,
              on_progress=seen.append)

    # DynamoDB rule is N/A by code, only the S3 rule reaches the model
    assert as_tuples(seen) == [("inventory", 0, 0), ("packages", 0, 1), ("packages", 1, 1)]


def test_the_fail_judge_phase_follows_the_packages_only_when_there_is_a_fail(
    spec_catalog: RuleCatalog, spec_input: str, trace
) -> None:
    seen: list[Progress] = []
    verdict = {"rule_id": "SPEC-DSGVO-Art.9", "confirmed": True, "reason": "Zeile 1 belegt es."}
    model = audit_and_judge([PASS_32, FAIL_9], [verdict], judged=[])

    run_audit(spec_catalog, spec_input, model, trace, on_progress=seen.append)

    assert as_tuples(seen) == [("packages", 0, 1), ("packages", 1, 1), ("fail_judge", 0, 0)]
