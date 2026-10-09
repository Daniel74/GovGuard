import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, RetryPromptPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from govguard.audit_engine import NA_FORBIDDEN, AuditValidationError, run_audit


def answer_with(*findings: dict) -> FunctionModel:
    """Fake LLM that always calls submit_audit with the given findings."""
    return answer_in_turns(list(findings))


def answer_in_turns(*turns: list[dict], seen: list | None = None) -> FunctionModel:
    """Fake LLM that answers turn by turn and repeats the last turn; records messages in seen."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if seen is not None:
            seen.append(messages)
        findings = turns[min(len(seen or [messages]) - 1, len(turns) - 1)]
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": findings})])

    return FunctionModel(respond, model_name="fake-model")


PASS_32 = {"rule_id": "SPEC-DSGVO-Art.32", "status": "PASS",
           "evidence": "ausschließlich über TLS 1.3", "rationale": "TLS.", "recommendation": None}
WARN_9 = {"rule_id": "SPEC-DSGVO-Art.9", "status": "WARN", "evidence": None,
          "rationale": "Unklar.", "recommendation": "Rechtsgrundlage nennen."}


def test_run_audit_completes_findings_from_catalog(spec_catalog, spec_input, trace) -> None:
    model = answer_with(
        {"rule_id": "SPEC-DSGVO-Art.9", "status": "FAIL",
         "evidence": "Gesundheitsdaten im Klartext in einem öffentlichen S3-Bucket",
         "rationale": "Klartext.", "recommendation": "Verschlüsseln."},
        {"rule_id": "SPEC-DSGVO-Art.32", "status": "PASS",
         "evidence": "ausschließlich über TLS 1.3", "rationale": "TLS.", "recommendation": None},
    )

    report = run_audit(spec_catalog, spec_input, model, trace)

    assert [f.rule_id for f in report.findings] == ["SPEC-DSGVO-Art.32", "SPEC-DSGVO-Art.9"]
    assert report.findings[1].title == "Gesundheitsdaten"
    assert report.findings[1].primary_anchor == "DSGVO Art. 9"
    assert report.findings[1].cross_references[0].anchor == "BSI GS++ KONF.1.1"
    assert report.overall_status == "FAIL"
    assert report.audit_type == "spec"
    assert report.model_id == "fake-model"
    assert report.trace == trace


def test_spec_prompt_allows_na(spec_catalog, spec_input, trace) -> None:
    seen: list = []

    run_audit(spec_catalog, spec_input, answer_in_turns([PASS_32, WARN_9], seen=seen), trace)

    assert NA_FORBIDDEN not in str(seen[0])


def test_spec_audit_sends_templates_to_the_model(spec_catalog, bucket_template, trace) -> None:
    warn_32 = {**WARN_9, "rule_id": "SPEC-DSGVO-Art.32"}

    report = run_audit(spec_catalog, bucket_template, answer_with(warn_32, WARN_9), trace)

    assert [f.status for f in report.findings] == ["WARN", "WARN"]  # no N/A by code


def test_run_audit_retries_once_with_missing_rule_ids(spec_catalog, spec_input, trace) -> None:
    seen: list = []
    model = answer_in_turns([PASS_32], [PASS_32, WARN_9], seen=seen)

    report = run_audit(spec_catalog, spec_input, model, trace)

    assert [f.status for f in report.findings] == ["PASS", "WARN"]
    retry = [p for p in seen[1][-1].parts if isinstance(p, RetryPromptPart)]
    assert "SPEC-DSGVO-Art.9" in retry[0].model_response()


@pytest.mark.parametrize(
    "findings",
    [
        [PASS_32],  # missing rule
        [PASS_32, WARN_9, WARN_9],  # duplicate finding
        [PASS_32, WARN_9, {**WARN_9, "rule_id": "SPEC-DSGVO-Art.99"}],  # unknown rule
    ],
)
def test_run_audit_fails_closed_when_findings_stay_incomplete(
    spec_catalog, spec_input, trace, findings: list[dict]
) -> None:
    with pytest.raises(AuditValidationError):
        run_audit(spec_catalog, spec_input, answer_with(*findings), trace)


@pytest.mark.parametrize("status", ["PASS", "WARN"])  # optional evidence is checked as well
def test_run_audit_retries_invented_evidence_then_fails_closed(
    spec_catalog, spec_input, trace, status: str
) -> None:
    seen: list = []
    invented = {**PASS_32, "status": status, "evidence": "Alle Daten werden mit KMS verschlüsselt",
                "recommendation": "KMS nachweisen."}
    model = answer_in_turns([invented, WARN_9], seen=seen)

    with pytest.raises(AuditValidationError):
        run_audit(spec_catalog, spec_input, model, trace)

    assert len(seen) == 2  # exactly one retry
    retry = [p for p in seen[1][-1].parts if isinstance(p, RetryPromptPart)]
    assert "SPEC-DSGVO-Art.32" in retry[0].model_response()


@pytest.mark.parametrize(
    "finding",
    [
        {**PASS_32, "evidence": None},  # PASS needs evidence
        {**PASS_32, "status": "FAIL", "evidence": None, "recommendation": "TLS nachweisen."},
        {**PASS_32, "evidence": "TLS 1.3"},  # verbatim, but too short to prove anything
        {**PASS_32, "status": "WARN", "evidence": None},  # WARN needs a recommendation
    ],
)
def test_run_audit_rejects_findings_without_required_fields(
    spec_catalog, spec_input, trace, finding: dict
) -> None:
    with pytest.raises(AuditValidationError):
        run_audit(spec_catalog, spec_input, answer_with(finding, WARN_9), trace)
