import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, RetryPromptPart, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from govguard.audit_engine import AuditValidationError, run_audit
from govguard.calls.inventory import NA_FORBIDDEN
from govguard.checks.evidence import UNPROVEN_PASS

SPEC_RULE_BEFORE_46 = (
    "Spezifikation (offene Welt): Was die Eingabe nicht erwähnt, kann anderswo geregelt sein. "
    'Beschreibt "violation_if" ein Fehlen, belegt fehlender Text nur "nicht beschrieben": WARN. '
    'FAIL nur, wenn die Belegzeilen etwas festlegen, das der Prüfregel widerspricht; '
    '"rationale" nennt es.'
)


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


PASS_32 = {"rule_id": "SPEC-DSGVO-Art.32", "status": "PASS", "line_start": 2, "line_end": 2,
           "rationale": "TLS.", "recommendation": None}
WARN_9 = {"rule_id": "SPEC-DSGVO-Art.9", "status": "WARN", "line_start": None, "line_end": None,
          "rationale": "Unklar.", "recommendation": "Rechtsgrundlage nennen."}


def test_run_audit_completes_findings_from_catalog(spec_catalog, spec_input, trace) -> None:
    model = answer_with(
        {"rule_id": "SPEC-DSGVO-Art.9", "status": "FAIL", "line_start": 1, "line_end": 1,
         "rationale": "Klartext.", "recommendation": "Verschlüsseln."},
        PASS_32,
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


def test_code_cuts_evidence_from_the_referenced_lines(spec_catalog, spec_input, trace) -> None:
    seen: list = []

    report = run_audit(spec_catalog, spec_input, answer_in_turns([PASS_32, WARN_9], seen=seen),
                       trace)

    tls = report.findings[0]
    assert tls.evidence == "Alle Zugriffe erfolgen ausschließlich über TLS 1.3."
    assert (tls.line_start, tls.line_end) == (2, 2)
    assert report.findings[1].evidence is None
    assert "2| Alle Zugriffe erfolgen" in str(seen[0])  # the model sees numbered lines


def test_evidence_spanning_lines_is_verbatim_in_crlf_input(spec_catalog, trace) -> None:
    crlf_input = "Gesundheitsdaten im Klartext.\r\nZugriffe erfolgen über TLS 1.3.\r\nEnde.\r\n"
    two_lines = {**PASS_32, "line_start": 1, "line_end": 2}

    report = run_audit(spec_catalog, crlf_input, answer_with(two_lines, WARN_9), trace)

    assert report.findings[0].evidence in crlf_input  # verbatim, not only line by line
    assert report.findings[0].evidence.endswith("TLS 1.3.")


def test_spec_prompt_allows_na(spec_catalog, spec_input, trace) -> None:
    seen: list = []

    run_audit(spec_catalog, spec_input, answer_in_turns([PASS_32, WARN_9], seen=seen), trace)

    assert NA_FORBIDDEN not in str(seen[0])


def test_spec_prompt_allows_fail_only_for_a_violation_the_lines_lay_down(
    spec_catalog, spec_input, trace
) -> None:
    seen: list = []

    run_audit(spec_catalog, spec_input, answer_in_turns([PASS_32, WARN_9], seen=seen), trace)

    # the text of ADR 0020, character for character: open world placeholders filled (#46)
    assert SPEC_RULE_BEFORE_46 in seen[0][0].instructions  # missing or vague is WARN


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
        [PASS_32, WARN_9, {**WARN_9, "rule_id": "SPEC-DSGVO-Art.99"}],  # unknown rule
    ],
)
def test_run_audit_fails_closed_when_findings_stay_incomplete(
    spec_catalog, spec_input, trace, findings: list[dict]
) -> None:
    with pytest.raises(AuditValidationError):
        run_audit(spec_catalog, spec_input, answer_with(*findings), trace)


def test_duplicate_with_the_same_status_is_dropped_without_retry(
    spec_catalog, spec_input, trace
) -> None:
    seen: list = []
    again = {**WARN_9, "rationale": "Nochmal unklar."}

    report = run_audit(spec_catalog, spec_input,
                       answer_in_turns([PASS_32, WARN_9, again], seen=seen), trace)

    assert len(seen) == 1  # the code can keep one of two equal answers itself
    assert [f.rationale for f in report.findings] == ["TLS.", "Unklar."]  # the first one wins


def test_pass_without_lines_is_retried_once_then_downgraded_to_warn(
    spec_catalog, spec_input, trace
) -> None:
    seen: list = []
    unproven = {**PASS_32, "line_start": None, "line_end": None}

    report = run_audit(spec_catalog, spec_input, answer_in_turns([unproven, WARN_9], seen=seen),
                       trace)

    assert len(seen) == 2  # exactly one retry
    retry = [p for p in seen[1][-1].parts if isinstance(p, RetryPromptPart)]
    assert "SPEC-DSGVO-Art.32 (PASS): Zeilenbereich fehlt" in retry[0].model_response()
    tls = report.findings[0]
    assert (tls.status, tls.evidence) == ("WARN", None)  # still unproven after the retry
    assert tls.recommendation == UNPROVEN_PASS


def test_pass_proven_in_the_retry_stays_pass(spec_catalog, spec_input, trace) -> None:
    unproven = {**PASS_32, "line_start": None, "line_end": None}

    report = run_audit(spec_catalog, spec_input,
                       answer_in_turns([unproven, WARN_9], [PASS_32, WARN_9], seen=[]), trace)

    assert report.findings[0].status == "PASS"


def test_fail_closed_names_the_problems_of_the_last_attempt(
    spec_catalog, spec_input, trace
) -> None:
    with pytest.raises(AuditValidationError, match=r"Befund fehlt für: SPEC-DSGVO-Art\.9"):
        run_audit(spec_catalog, spec_input, answer_with(PASS_32), trace)


def test_fail_without_lines_is_downgraded_to_warn_without_retry(
    spec_catalog, spec_input, trace
) -> None:
    seen: list = []
    missing = {**WARN_9, "status": "FAIL", "rationale": "Rechtsgrundlage fehlt."}

    report = run_audit(spec_catalog, spec_input, answer_in_turns([PASS_32, missing], seen=seen),
                       trace)

    assert len(seen) == 1  # what is missing is WARN, not FAIL: no retry needed
    assert report.findings[1].status == "WARN"
    assert report.overall_status == "WARN"


LONG_INPUT = "\n".join(  # 250 lines of one section, then a line too short to prove anything
    [f"Abschnitt {i}: Alle Zugriffe erfolgen über TLS 1.3." for i in range(1, 251)] + ["TLS 1.3"]
)


@pytest.mark.parametrize(
    ("line_start", "line_end", "problem"),
    [
        (0, 1, "ungültig"),
        (250, 252, "ungültig"),  # the input ends at line 251
        (3, 2, "ungültig"),
        (1, 201, "zu groß"),  # more than 200 lines
        (251, 251, "zu kurz"),  # "TLS 1.3" proves nothing
    ],
)
def test_invalid_line_range_at_pass_is_retried_once_then_downgraded_to_warn(
    spec_catalog, trace, line_start: int, line_end: int, problem: str
) -> None:
    seen: list = []
    pointing = {**PASS_32, "line_start": line_start, "line_end": line_end}

    report = run_audit(spec_catalog, LONG_INPUT, answer_in_turns([pointing, WARN_9], seen=seen),
                       trace)

    assert len(seen) == 2  # exactly one retry
    assert (report.findings[0].status, report.findings[0].evidence) == ("WARN", None)
    retry = [p for p in seen[1][-1].parts if isinstance(p, RetryPromptPart)]
    assert f"SPEC-DSGVO-Art.32 (PASS): Zeilenbereich {line_start}-{line_end} {problem}" in (
        retry[0].model_response())


@pytest.mark.parametrize("status", ["FAIL", "WARN", "N/A"])
@pytest.mark.parametrize(
    ("line_start", "line_end"),
    [(1, 251), (154, 67), (250, 252), (251, 251)],  # too large, reversed, outside, too short
)
def test_unusable_range_outside_pass_counts_as_no_range_without_retry(
    spec_catalog, trace, status: str, line_start: int, line_end: int
) -> None:
    seen: list = []
    pointing = {**WARN_9, "status": status, "line_start": line_start, "line_end": line_end}

    report = run_audit(spec_catalog, LONG_INPUT,
                       answer_in_turns([PASS_32, pointing], seen=seen), trace)

    assert len(seen) == 1  # only PASS needs a usable range; elsewhere it is like no range
    downgraded = "WARN" if status == "FAIL" else status
    assert (report.findings[1].status, report.findings[1].evidence) == (downgraded, None)


def test_a_whole_section_of_200_lines_is_valid_evidence(spec_catalog, trace) -> None:
    section = {**PASS_32, "line_start": 1, "line_end": 200}

    report = run_audit(spec_catalog, LONG_INPUT, answer_with(section, WARN_9), trace)

    assert report.findings[0].evidence.splitlines()[-1].startswith("Abschnitt 200:")


def test_warn_without_any_recommendation_still_fails_closed(
    spec_catalog, spec_input, trace
) -> None:
    spec_catalog.rules[0].recommendation = ""  # nothing the code could fill in (#32)
    warn = {**PASS_32, "status": "WARN"}

    with pytest.raises(AuditValidationError, match=r"SPEC-DSGVO-Art\.32: Empfehlung fehlt"):
        run_audit(spec_catalog, spec_input, answer_with(warn, WARN_9), trace)
