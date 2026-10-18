"""Free-text architecture is an open world: FAIL only for a violation the lines lay down (#46)."""

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from test_run_audit_freetext import FREE_TEXT, S3_SEEN, arch_rule, by_id

from govguard.audit_engine import run_audit
from govguard.models import FailJudgeCount, RuleCatalog

JUDGE_TOOL = "submit_fail_verdicts"
FAIL_S3 = {"rule_id": "ARCH-CIS-3.1.4", "status": "FAIL", "line_start": 1, "line_end": 1,
           "rationale": "Keine LifecycleConfiguration erwähnt.", "recommendation": "Ergänzen."}
REJECTED = {"rule_id": "ARCH-CIS-3.1.4", "confirmed": False,
            "reason": "Zeile 1 schweigt zur Konfiguration."}


@pytest.fixture
def s3_catalog() -> RuleCatalog:
    return RuleCatalog(audit_type="architecture", source_versions={"CIS": "v7.0.0"},
                       model_id="fake-model", rules=[arch_rule("3.1.4", "AWS::S3::Bucket")])


def fake(audit_prompts: list[str], judged: list, fail: dict = FAIL_S3) -> FunctionModel:
    """Inventory sees S3, the audit answers `fail`, the judge rejects it."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        tool = info.output_tools[0].name
        if tool == "submit_inventory":
            return ModelResponse(parts=[ToolCallPart(tool, {"resource_types": [S3_SEEN]})])
        if tool == JUDGE_TOOL:
            judged.append(messages)
            return ModelResponse(parts=[ToolCallPart(tool, {"verdicts": [REJECTED]})])
        audit_prompts.append(messages[0].instructions)
        return ModelResponse(parts=[ToolCallPart(tool, {"findings": [fail]})])

    return FunctionModel(respond, model_name="fake-model")


def test_free_text_prompt_names_the_open_world_of_an_architecture(s3_catalog, trace) -> None:
    prompts: list[str] = []

    run_audit(s3_catalog, FREE_TEXT, fake(prompts, []), trace)

    assert "Architekturbeschreibung (offene Welt): Was die Eingabe nicht erwähnt" in prompts[0]


def test_free_text_fail_for_a_missing_setting_becomes_warn(s3_catalog, trace) -> None:
    judged: list = []

    report = run_audit(s3_catalog, FREE_TEXT, fake([], judged), trace)

    s3 = by_id(report, "ARCH-CIS-3.1.4")
    assert (s3.status, s3.downgraded_from) == ("WARN", "FAIL")
    assert report.overall_status == "WARN"
    assert report.fail_judge == FailJudgeCount(checked=1, downgraded=1)
    prompt = judged[0][0].instructions
    assert "aus dem Audit einer Architekturbeschreibung in Freitext" in prompt
    assert "Die Bescheide liegen in einem S3-Bucket." in prompt  # the example pair
    assert report.closed_world is False  # the UI shows the judge tile (#46)


def test_template_fail_for_a_missing_setting_stays_and_the_report_says_closed(
    s3_catalog, bucket_template, trace
) -> None:
    judged: list = []
    on_line_7 = FAIL_S3 | {"line_start": 7, "line_end": 7}  # line 1 is "{", no evidence

    report = run_audit(s3_catalog, bucket_template, fake([], judged, on_line_7), trace)

    assert by_id(report, "ARCH-CIS-3.1.4").status == "FAIL"
    assert judged == []  # same as test_architecture_audit_asks_no_judge (fail_judge)
    assert report.closed_world is True
