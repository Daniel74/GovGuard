"""Free-text architecture: LLM pre-run names resource types with evidence lines (ADR 0011, 0017)."""

import pytest
from conftest import make_rule
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from govguard.audit_engine import AuditValidationError, run_audit
from govguard.calls.inventory import NA_FORBIDDEN_FREE_TEXT, NA_NOT_RECOGNIZED
from govguard.models import RuleCatalog

FREE_TEXT = (
    "Eine Lambda-Funktion legt die Bescheide in einem S3-Bucket mit Versionierung ab.\n"
    "Der Zugriff ist nur aus dem Behördennetz erlaubt."
)
S3_SEEN = {"resource_type": "AWS::S3::Bucket", "line_start": 1, "line_end": 1}


def arch_rule(requirement_id: str, cfn_type: str):
    return make_rule(requirement_id, f"Regel {requirement_id}").model_copy(update={
        "id": f"ARCH-CIS-{requirement_id}", "audit_type": "architecture", "source": "CIS",
        "primary_anchor": f"CIS AWS v7.0.0 {requirement_id}", "cfn_resource_types": [cfn_type],
    })


@pytest.fixture
def free_catalog() -> RuleCatalog:
    return RuleCatalog(
        audit_type="architecture", source_versions={"CIS": "v7.0.0"}, model_id="fake-model",
        rules=[arch_rule("3.1.4", "AWS::S3::Bucket"), arch_rule("3.3.1", "AWS::DynamoDB::Table")],
    )


def warn(rule_id: str) -> dict:
    return {"rule_id": rule_id, "status": "WARN", "line_start": None, "line_end": None,
            "rationale": "Unklar.", "recommendation": "Nachweisen."}


def fake(*inventories: list[dict], audit_prompts: list[str], status: str = "WARN",
         inventory_prompts: list[str] | None = None) -> FunctionModel:
    """Pre-run answers turn by turn; the audit answers each rule ID it finds in its prompt."""
    inventory_calls: list[str] = [] if inventory_prompts is None else inventory_prompts

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        tool = info.output_tools[0].name
        if tool == "submit_inventory":
            inventory_calls.append(str(messages[0]))
            seen = inventories[min(len(inventory_calls), len(inventories)) - 1]
            return ModelResponse(parts=[ToolCallPart(tool, {"resource_types": seen})])
        prompt = str(messages[0])
        audit_prompts.append(str(messages))
        rule_ids = [r.split('"')[0] for r in prompt.split('"id": "')[1:]]
        findings = [{**warn(rule_id), "status": status} for rule_id in rule_ids]
        return ModelResponse(parts=[ToolCallPart(tool, {"findings": findings})])

    return FunctionModel(respond, model_name="fake-model")


def by_id(report, rule_id: str):
    return next(f for f in report.findings if f.rule_id == rule_id)


def test_rules_for_services_not_recognized_get_na(free_catalog, trace) -> None:
    prompts: list[str] = []

    report = run_audit(free_catalog, FREE_TEXT, fake([S3_SEEN], audit_prompts=prompts), trace)

    dynamo = by_id(report, "ARCH-CIS-3.3.1")
    assert (dynamo.status, dynamo.rationale) == ("N/A", NA_NOT_RECOGNIZED)
    assert by_id(report, "ARCH-CIS-3.1.4").status == "WARN"
    assert "ARCH-CIS-3.3.1" not in prompts[0]
    assert NA_FORBIDDEN_FREE_TEXT in prompts[0]


@pytest.mark.parametrize(
    "invalid",
    [
        {**S3_SEEN, "line_start": 3, "line_end": 3},  # the input has two lines
        {**S3_SEEN, "line_start": 2, "line_end": 1},  # reversed
        {**S3_SEEN, "resource_type": "AWS::EC2::Instance"},  # not in the list
    ],
)
def test_pre_run_retries_once_then_fails_closed(free_catalog, trace, invalid: dict) -> None:
    prompts: list[str] = []

    with pytest.raises(AuditValidationError):
        run_audit(free_catalog, FREE_TEXT, fake([invalid], audit_prompts=prompts), trace)

    assert prompts == []  # the audit model is never asked


def test_pre_run_retry_can_correct_the_answer(free_catalog, trace) -> None:
    invented = {**S3_SEEN, "line_start": 3, "line_end": 3}
    prompts: list[str] = []

    report = run_audit(free_catalog, FREE_TEXT, fake([invented], [S3_SEEN], audit_prompts=prompts),
                       trace)

    assert by_id(report, "ARCH-CIS-3.1.4").status == "WARN"


def test_pre_run_accepts_type_as_field_name_without_a_retry(free_catalog, trace) -> None:
    # Groq writes "type" instead of "resource_type" in nearly every run (#39)
    seen = {"type": S3_SEEN["resource_type"], "line_start": 1, "line_end": 1}

    report = run_audit(free_catalog, FREE_TEXT, fake([seen], audit_prompts=[]), trace)

    assert (report.retries, by_id(report, "ARCH-CIS-3.1.4").status) == (0, "WARN")


def test_pre_run_gets_the_input_with_line_numbers(free_catalog, trace) -> None:
    inventory_prompts: list[str] = []

    run_audit(free_catalog, FREE_TEXT,
              fake([S3_SEEN], audit_prompts=[], inventory_prompts=inventory_prompts), trace)

    assert "1| Eine Lambda-Funktion" in inventory_prompts[0]
    assert "2| Der Zugriff" in inventory_prompts[0]


def test_pre_run_retry_names_the_range_problem(free_catalog, trace) -> None:
    beyond = {**S3_SEEN, "line_start": 3, "line_end": 3}

    with pytest.raises(AuditValidationError) as failure:
        run_audit(free_catalog, FREE_TEXT, fake([beyond], audit_prompts=[]), trace)

    assert failure.value.problems == [
        ("", "AWS::S3::Bucket: Zeilenbereich 3-3 ungültig (die Eingabe hat die Zeilen 1-2)")]


@pytest.mark.parametrize("cfn_type", ["AWS::IAM::Role", "AWS::KMS::Key", "AWS::Logs::LogGroup"])
def test_iam_kms_and_logs_rules_never_get_na(free_catalog, trace, cfn_type: str) -> None:
    catalog = free_catalog.model_copy(update={"rules": [arch_rule("1.1", cfn_type)]})
    prompts: list[str] = []

    report = run_audit(catalog, FREE_TEXT, fake([], audit_prompts=prompts), trace)

    assert report.findings[0].status == "WARN"
    assert "ARCH-CIS-1.1" in prompts[0]


def test_cloudformation_reads_iam_kms_and_logs_from_the_template(free_catalog, trace) -> None:
    catalog = free_catalog.model_copy(update={"rules": [arch_rule("1.1", "AWS::IAM::Role")]})
    template = '{"Resources": {"Docs": {"Type": "AWS::S3::Bucket"}}}'
    prompts: list[str] = []

    report = run_audit(catalog, template, fake([], audit_prompts=prompts), trace)

    assert report.findings[0].status == "N/A"  # the code inventory is exact


def test_model_must_not_answer_na_for_a_recognized_service(free_catalog, trace) -> None:
    prompts: list[str] = []

    with pytest.raises(AuditValidationError):
        run_audit(free_catalog, FREE_TEXT, fake([S3_SEEN], audit_prompts=prompts, status="N/A"),
                  trace)

    assert "ARCH-CIS-3.1.4: N/A ist verboten" in prompts[1]


def test_na_retry_does_not_claim_an_always_applicable_type_is_in_the_input(
    free_catalog, trace
) -> None:
    catalog = free_catalog.model_copy(update={"rules": [arch_rule("1.1", "AWS::IAM::Role")]})
    prompts: list[str] = []

    with pytest.raises(AuditValidationError):
        run_audit(catalog, FREE_TEXT, fake([], audit_prompts=prompts, status="N/A"), trace)

    assert "ARCH-CIS-1.1: N/A ist verboten, die Prüfregel ist laut Ressourceninventar anwendbar" \
        in prompts[1]


def test_pre_run_names_resource_types_at_temperature_zero(free_catalog, trace) -> None:
    # a service seen in one run and missed in the next would flip its rules to N/A (#28)
    settings: list = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        tool = info.output_tools[0].name
        if tool == "submit_inventory":
            settings.append(info.model_settings)
            return ModelResponse(parts=[ToolCallPart(tool, {"resource_types": [S3_SEEN]})])
        return ModelResponse(parts=[ToolCallPart(tool, {"findings": [warn("ARCH-CIS-3.1.4")]})])

    run_audit(free_catalog, FREE_TEXT, FunctionModel(respond), trace)

    assert settings[0]["temperature"] == 0


def test_report_is_sorted_by_resource_type(free_catalog, trace) -> None:
    rules = [*free_catalog.rules, arch_rule("1.1", "AWS::IAM::Role")]  # S3, DynamoDB, IAM
    catalog = free_catalog.model_copy(update={"rules": rules})

    report = run_audit(catalog, FREE_TEXT, fake([S3_SEEN], audit_prompts=[]), trace)

    assert [f.rule_id for f in report.findings] == [
        "ARCH-CIS-3.3.1",  # AWS::DynamoDB::Table
        "ARCH-CIS-1.1",  # AWS::IAM::Role
        "ARCH-CIS-3.1.4",  # AWS::S3::Bucket
    ]
