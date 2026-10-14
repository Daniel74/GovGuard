"""Corrections of the code in the model's answer become visible in the report (#27)."""

import pytest
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse, RetryPromptPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from test_run_audit import PASS_32, WARN_9, answer_in_turns
from test_run_audit_freetext import FREE_TEXT, S3_SEEN, fake
from test_run_audit_packages import INPUT as PACKAGE_INPUT
from test_run_audit_packages import catalog_of, rule_ids_in

from govguard.audit_engine import AuditValidationError, run_audit


def test_fail_without_lines_shows_its_downgrade_and_reason(spec_catalog, spec_input, trace) -> None:
    missing = {**WARN_9, "status": "FAIL", "rationale": "Rechtsgrundlage fehlt."}

    report = run_audit(spec_catalog, spec_input, answer_in_turns([PASS_32, missing]), trace)

    tls, legal = report.findings
    assert (tls.downgraded_from, tls.corrections) == (None, [])  # untouched finding
    assert (legal.status, legal.downgraded_from) == ("WARN", "FAIL")
    assert len(legal.corrections) == 1
    assert "SPEC-DSGVO-Art.9" in legal.corrections[0]
    assert "FAIL" in legal.corrections[0]


def test_pass_unproven_after_the_retry_shows_retry_reason_and_downgrade(
    spec_catalog, spec_input, trace
) -> None:
    seen: list = []
    unproven = {**PASS_32, "line_start": None, "line_end": None}

    report = run_audit(spec_catalog, spec_input,
                       answer_in_turns([unproven, WARN_9], seen=seen), trace)

    tls = report.findings[0]
    assert tls.downgraded_from == "PASS"
    retry_reason, downgrade_reason = tls.corrections
    retry_prompt = "\n".join(p.model_response() for p in seen[1][-1].parts
                             if isinstance(p, RetryPromptPart))
    assert retry_reason in retry_prompt  # the reader sees what the model read
    assert "Zeilenbereich fehlt" in retry_reason
    assert "WARN" in downgrade_reason


def test_retry_reason_of_a_rule_lands_in_its_finding_even_when_the_retry_fixes_it(
    spec_catalog, spec_input, trace
) -> None:
    no_recommendation = {**WARN_9, "recommendation": None}

    report = run_audit(spec_catalog, spec_input,
                       answer_in_turns([PASS_32, no_recommendation], [PASS_32, WARN_9], seen=[]),
                       trace)

    legal = report.findings[1]
    assert (legal.status, legal.downgraded_from) == ("WARN", None)
    assert [c for c in legal.corrections if "Empfehlung fehlt" in c]
    assert report.findings[0].corrections == []  # PASS_32 was fine in both attempts


def test_reason_without_a_finding_stands_in_unassigned_corrections(
    spec_catalog, spec_input, trace
) -> None:
    unknown = {**WARN_9, "rule_id": "SPEC-DSGVO-Art.99"}

    report = run_audit(spec_catalog, spec_input,
                       answer_in_turns([PASS_32, WARN_9, unknown], [PASS_32, WARN_9], seen=[]),
                       trace)

    assert len(report.unassigned_corrections) == 1
    assert "SPEC-DSGVO-Art.99" in report.unassigned_corrections[0]
    assert all(f.corrections == [] for f in report.findings)  # no finding carries it


def test_clean_audit_has_no_corrections_at_all(spec_catalog, spec_input, trace) -> None:
    report = run_audit(spec_catalog, spec_input, answer_in_turns([PASS_32, WARN_9]), trace)

    assert report.unassigned_corrections == []
    assert all(f.corrections == [] and f.downgraded_from is None for f in report.findings)


def test_fail_closed_carries_the_reasons_of_the_last_attempt_as_a_list(
    spec_catalog, spec_input, trace
) -> None:
    no_recommendation = {**WARN_9, "recommendation": None}

    with pytest.raises(AuditValidationError) as failure:
        run_audit(spec_catalog, spec_input, answer_in_turns([PASS_32, no_recommendation]), trace)

    assert failure.value.problems == [
        ("SPEC-DSGVO-Art.9", "SPEC-DSGVO-Art.9: Empfehlung fehlt (Pflicht bei WARN)")]
    assert not failure.value.api_error


def test_api_error_is_its_own_case_without_the_library_text(
    spec_catalog, spec_input, trace
) -> None:
    def throttled(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        raise ModelHTTPError(status_code=429, model_name="fake-model", body="ThrottlingException")

    with pytest.raises(AuditValidationError) as failure:
        run_audit(spec_catalog, spec_input, FunctionModel(throttled), trace)

    assert failure.value.api_error
    assert failure.value.problems == []
    assert "ThrottlingException" not in str(failure.value)


def test_answer_that_breaks_the_schema_fails_closed_with_one_plain_reason(
    spec_catalog, spec_input, trace
) -> None:
    def broken(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": "keine Liste"})])

    with pytest.raises(AuditValidationError) as failure:
        run_audit(spec_catalog, spec_input, FunctionModel(broken), trace)

    assert not failure.value.api_error
    assert [rule_id for rule_id, _ in failure.value.problems] == [""]  # no rule is meant
    assert "Schema" in failure.value.problems[0][1]


def test_report_counts_packages_with_a_retry(trace) -> None:
    asked: set[str] = set()

    def forgetful(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        rule_ids = rule_ids_in(messages)
        first_time = rule_ids[0] not in asked
        asked.add(rule_ids[0])
        answered = rule_ids[1:] if first_time and "SPEC-DSGVO-Art.11" in rule_ids else rule_ids
        findings = [{"rule_id": r, "status": "WARN", "line_start": None, "line_end": None,
                     "rationale": "Unklar.", "recommendation": "Nachweisen."} for r in answered]
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": findings})])

    report = run_audit(catalog_of(23), PACKAGE_INPUT, FunctionModel(forgetful), trace)

    assert report.retries == 1  # only the second package of three was sent back


def test_report_without_a_retry_counts_zero(spec_catalog, spec_input, trace) -> None:
    report = run_audit(spec_catalog, spec_input, answer_in_turns([PASS_32, WARN_9]), trace)

    assert report.retries == 0


def test_pre_run_retry_reason_stands_in_unassigned_corrections(arch_catalog, trace) -> None:
    invented = {"resource_type": "AWS::EC2::Instance", "evidence": S3_SEEN["evidence"]}

    report = run_audit(arch_catalog, FREE_TEXT, fake([invented], [S3_SEEN], audit_prompts=[]),
                       trace)

    assert report.unassigned_corrections == ["AWS::EC2::Instance: Typ steht nicht in der Liste"]
    assert report.retries == 1  # the pre-run counts like a package


def test_pre_run_fail_closed_names_its_reason_not_the_schema(arch_catalog, trace) -> None:
    invented = {"resource_type": "AWS::EC2::Instance", "evidence": S3_SEEN["evidence"]}

    with pytest.raises(AuditValidationError) as failure:
        run_audit(arch_catalog, FREE_TEXT, fake([invented], audit_prompts=[]), trace)

    assert failure.value.problems == [("", "AWS::EC2::Instance: Typ steht nicht in der Liste")]


def test_schema_retry_that_succeeds_leaves_a_plain_reason(spec_catalog, spec_input, trace) -> None:
    calls: list[int] = []

    def broken_once(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        calls.append(1)
        findings = "keine Liste" if len(calls) == 1 else [PASS_32, WARN_9]
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": findings})])

    report = run_audit(spec_catalog, spec_input, FunctionModel(broken_once), trace)

    assert report.retries == 1
    assert len(report.unassigned_corrections) == 1
    assert "Schema" in report.unassigned_corrections[0]


def test_http_400_is_an_invalid_answer_not_an_api_error(spec_catalog, spec_input, trace) -> None:
    def malformed(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        raise ModelHTTPError(status_code=400, model_name="fake-model", body="tool_use_failed")

    with pytest.raises(AuditValidationError) as failure:
        run_audit(spec_catalog, spec_input, FunctionModel(malformed), trace)

    assert not failure.value.api_error  # Groq rejects a broken tool call with 400 (#26)
    assert "Schema" in failure.value.problems[0][1]
    assert "tool_use_failed" not in str(failure.value)
