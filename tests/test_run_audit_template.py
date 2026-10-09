"""N/A by code for CloudFormation JSON (DESIGN 2.2, ADR 0007)."""

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from govguard.audit_engine import NA_FORBIDDEN, AuditValidationError, run_audit

S3_PASS = {"rule_id": "ARCH-CIS-3.1.4", "status": "PASS", "evidence": '"BlockPublicAcls": true',
           "rationale": "Gesetzt.", "recommendation": None}


def fake(finding: dict, prompts: list[str]) -> FunctionModel:
    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        prompts.append(str(messages))
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": [finding]})])

    return FunctionModel(respond, model_name="fake-model")


def test_rules_without_matching_resource_type_get_na_by_code(
    arch_catalog, bucket_template, trace
) -> None:
    prompts: list[str] = []

    report = run_audit(arch_catalog, bucket_template, fake(S3_PASS, prompts), trace)

    dynamo = report.findings[1]
    assert (dynamo.rule_id, dynamo.status) == ("ARCH-CIS-3.3.1", "N/A")
    assert dynamo.rationale == "Ressourcentyp nicht im Template"
    assert report.overall_status == "PASS"
    assert "ARCH-CIS-3.3.1" not in prompts[0]
    assert NA_FORBIDDEN in prompts[0]


def test_model_must_not_answer_na_when_resource_type_is_present(
    arch_catalog, bucket_template, trace
) -> None:
    prompts: list[str] = []
    s3_na = {**S3_PASS, "status": "N/A", "evidence": None}

    with pytest.raises(AuditValidationError):
        run_audit(arch_catalog, bucket_template, fake(s3_na, prompts), trace)

    assert "ARCH-CIS-3.1.4: N/A ist verboten" in prompts[1]


def test_model_is_not_called_when_all_rules_are_na(arch_catalog, trace) -> None:
    prompts: list[str] = []
    template = '{"Resources": {"Fn": {"Type": "AWS::Lambda::Function"}}}'

    report = run_audit(arch_catalog, template, fake(S3_PASS, prompts), trace)

    assert [f.status for f in report.findings] == ["N/A", "N/A"]
    assert report.overall_status == "N/A"
    assert prompts == []
