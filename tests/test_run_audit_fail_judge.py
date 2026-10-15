"""The FAIL judge confirms or downgrades every FAIL of a spec audit (open world, ADR 0020, #31)."""

import json

from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from test_run_audit import PASS_32, WARN_9
from test_run_audit_schema import GroqFake

from govguard.audit_engine import run_audit
from govguard.models import FailJudgeCount

JUDGE_TOOL = "submit_fail_verdicts"


def audit_and_judge(
    findings: list[dict], verdicts: list[dict] | Exception, judged: list
) -> FunctionModel:
    """Fake LLM: the audit gets `findings`, the judge `verdicts` (or the error is raised)."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if info.output_tools[0].name == JUDGE_TOOL:
            judged.append(messages)
            if isinstance(verdicts, Exception):
                raise verdicts
            return ModelResponse(parts=[ToolCallPart(JUDGE_TOOL, {"verdicts": verdicts})])
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": findings})])

    return FunctionModel(respond, model_name="fake-model")


FAIL_9 = {"rule_id": "SPEC-DSGVO-Art.9", "status": "FAIL", "line_start": 1, "line_end": 1,
          "rationale": "Gesundheitsdaten liegen im Klartext.", "recommendation": "Verschlüsseln."}


def test_judge_sees_only_the_evidence_lines_and_confirms_the_fail(
    spec_catalog, spec_input, trace
) -> None:
    judged: list = []
    verdict = {"rule_id": "SPEC-DSGVO-Art.9", "confirmed": True,
               "reason": "Zeile 1 legt Klartext fest."}

    report = run_audit(spec_catalog, spec_input,
                       audit_and_judge([PASS_32, FAIL_9], [verdict], judged), trace)

    request = str(judged[0])
    assert len(judged) == 1
    assert "1| Das Bürgerportal speichert Gesundheitsdaten im Klartext" in request
    assert "Die Maßnahme fehlt nachweislich." in request  # violation_if of the rule
    assert "Gesundheitsdaten liegen im Klartext." not in request  # the judge echoed it (#31)
    assert "TLS 1.3" not in request  # line 2 is no evidence of the FAIL
    legal = report.findings[1]
    assert (legal.status, legal.downgraded_from) == ("FAIL", None)
    assert legal.corrections == ["SPEC-DSGVO-Art.9: Prüfer bestätigt das FAIL: "
                                 "Zeile 1 legt Klartext fest."]
    assert report.fail_judge == FailJudgeCount(checked=1, confirmed=1)


def test_fail_the_judge_rejects_becomes_warn_with_its_reason(
    spec_catalog, spec_input, trace
) -> None:
    verdict = {"rule_id": "SPEC-DSGVO-Art.9", "confirmed": False,
               "reason": "Die Begründung nennt nur ein Fehlen."}

    report = run_audit(spec_catalog, spec_input,
                       audit_and_judge([PASS_32, FAIL_9], [verdict], []), trace)

    legal = report.findings[1]
    assert (legal.status, legal.downgraded_from) == ("WARN", "FAIL")
    assert legal.recommendation == "Verschlüsseln."  # a WARN needs one, the FAIL had it
    assert legal.evidence is not None  # the reader sees what the judge saw
    assert legal.corrections == ["SPEC-DSGVO-Art.9: Prüfer bestätigt das FAIL nicht, wird WARN: "
                                 "Die Begründung nennt nur ein Fehlen."]
    assert report.overall_status == "WARN"
    assert report.fail_judge == FailJudgeCount(checked=1, downgraded=1)


def test_fail_stays_unchecked_when_the_judge_is_down(spec_catalog, spec_input, trace) -> None:
    down = ModelHTTPError(503, "fake-model")

    report = run_audit(spec_catalog, spec_input, audit_and_judge([PASS_32, FAIL_9], down, []),
                       trace)

    legal = report.findings[1]
    assert (legal.status, legal.downgraded_from) == ("FAIL", None)  # the stricter status stays
    assert legal.corrections == ["SPEC-DSGVO-Art.9: Prüfer nicht verfügbar (KI-Dienst nicht "
                                 "erreichbar oder überlastet), FAIL ungeprüft"]
    assert report.fail_judge == FailJudgeCount(checked=1, unavailable=1)


def test_fail_without_verdict_stays_unchecked_and_foreign_verdicts_count_nowhere(
    spec_catalog, spec_input, trace
) -> None:
    fail_32 = {**PASS_32, "status": "FAIL", "recommendation": "TLS prüfen."}
    verdicts = [{"rule_id": "SPEC-DSGVO-Art.9", "confirmed": True, "reason": "Klartext."},
                {"rule_id": "SPEC-DSGVO-Art.99", "confirmed": False, "reason": "Erfunden."}]

    report = run_audit(spec_catalog, spec_input,
                       audit_and_judge([fail_32, FAIL_9], verdicts, []), trace)

    tls = report.findings[0]
    assert tls.status == "FAIL"
    assert tls.corrections == ["SPEC-DSGVO-Art.32: Prüfer nicht verfügbar (kein Urteil zu "
                               "diesem Befund), FAIL ungeprüft"]
    assert report.unassigned_corrections == []
    assert report.fail_judge == FailJudgeCount(checked=2, confirmed=1, unavailable=1)


def test_spec_audit_without_fail_asks_no_judge(spec_catalog, spec_input, trace) -> None:
    judged: list = []

    report = run_audit(spec_catalog, spec_input,
                       audit_and_judge([PASS_32, WARN_9], [], judged), trace)

    assert judged == []
    assert report.fail_judge == FailJudgeCount()


def test_architecture_audit_asks_no_judge(arch_catalog, bucket_template, trace) -> None:
    # closed world: a missing setting is the default value, that is the violation (ADR 0020)
    judged: list = []
    fail_s3 = {"rule_id": "ARCH-CIS-3.1.4", "status": "FAIL", "line_start": 7, "line_end": 7,
               "rationale": "IgnorePublicAcls fehlt.", "recommendation": "Setzen."}

    report = run_audit(arch_catalog, bucket_template, audit_and_judge([fail_s3], [], judged),
                       trace)

    assert judged == []
    assert report.overall_status == "FAIL"
    assert report.fail_judge == FailJudgeCount()


def test_groq_judges_with_strict_native_output(spec_catalog, spec_input, trace) -> None:
    seen: list[AgentInfo] = []
    verdict = {"rule_id": "SPEC-DSGVO-Art.9", "confirmed": False, "reason": "Nur ein Fehlen."}

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.append(info)
        answer = {"verdicts": [verdict]} if len(seen) > 1 else {"findings": [PASS_32, FAIL_9]}
        return ModelResponse(parts=[TextPart(json.dumps(answer))])

    report = run_audit(spec_catalog, spec_input, GroqFake(respond, model_name="groq-fake"), trace)

    params = seen[1].model_request_parameters
    assert (params.output_mode, params.output_object.name) == ("native", JUDGE_TOOL)
    assert params.output_object.strict
    assert report.findings[1].status == "WARN"


def test_missing_verdict_is_asked_for_once_more(spec_catalog, spec_input, trace) -> None:
    fail_32 = {**PASS_32, "status": "FAIL", "recommendation": "TLS prüfen."}
    verdict_9 = {"rule_id": "SPEC-DSGVO-Art.9", "confirmed": True, "reason": "Klartext."}
    verdict_32 = {"rule_id": "SPEC-DSGVO-Art.32", "confirmed": False, "reason": "Nur TLS."}
    judged: list = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if info.output_tools[0].name != JUDGE_TOOL:
            return ModelResponse(parts=[ToolCallPart("submit_audit",
                                                     {"findings": [fail_32, FAIL_9]})])
        judged.append(messages)
        verdicts = [verdict_9] if len(judged) == 1 else [verdict_9, verdict_32]
        return ModelResponse(parts=[ToolCallPart(JUDGE_TOOL, {"verdicts": verdicts})])

    report = run_audit(spec_catalog, spec_input, FunctionModel(respond), trace)

    assert len(judged) == 2
    assert "Urteil fehlt für: SPEC-DSGVO-Art.32" in str(judged[1][-1])
    assert report.findings[0].status == "WARN"
    assert report.fail_judge == FailJudgeCount(checked=2, confirmed=1, downgraded=1)
