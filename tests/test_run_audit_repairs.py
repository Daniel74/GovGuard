"""What the code repairs from the knowledge base needs no retry (ADR 0017, #32)."""

from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from test_run_audit import PASS_32, WARN_9, answer_in_turns
from test_run_audit_template import fake

from govguard.audit_engine import run_audit


def test_warn_without_recommendation_gets_the_rule_recommendation_without_retry(
    spec_catalog, spec_input, trace
) -> None:
    seen: list = []
    no_recommendation = {**WARN_9, "recommendation": None}

    report = run_audit(spec_catalog, spec_input,
                       answer_in_turns([PASS_32, no_recommendation], seen=seen), trace)

    assert len(seen) == 1  # the code knows the recommendation of the rule
    legal = report.findings[1]
    assert (legal.status, legal.downgraded_from) == ("WARN", None)
    assert legal.recommendation == "Falls nicht erfüllt: Maßnahme ergänzen."
    assert legal.corrections == ["SPEC-DSGVO-Art.9: Empfehlung aus der Prüfregel ergänzt: "
                                 "Die KI hat bei WARN keine genannt."]
    assert report.retries == 0


def test_repair_counts_only_from_the_last_attempt(spec_catalog, spec_input, trace) -> None:
    unproven = {**PASS_32, "line_start": None, "line_end": None}  # sends the package back
    no_recommendation = {**WARN_9, "recommendation": None}

    report = run_audit(spec_catalog, spec_input,
                       answer_in_turns([unproven, no_recommendation], [PASS_32, WARN_9], seen=[]),
                       trace)

    legal = report.findings[1]
    assert (legal.recommendation, legal.corrections) == ("Rechtsgrundlage nennen.", [])


def test_contradicting_duplicates_keep_the_worst_status_without_retry(
    spec_catalog, spec_input, trace
) -> None:
    seen: list = []
    proven = {**PASS_32, "rule_id": "SPEC-DSGVO-Art.9", "rationale": "Belegt."}

    report = run_audit(spec_catalog, spec_input,
                       answer_in_turns([PASS_32, proven, WARN_9, proven], seen=seen), trace)

    assert len(seen) == 1
    legal = report.findings[1]
    assert (legal.status, legal.rationale) == ("WARN", "Unklar.")
    assert legal.corrections == ["SPEC-DSGVO-Art.9: Widersprüchliche Befunde der KI "
                                 "(PASS, WARN): Der schwerere Status gilt."]


def test_downgrade_belongs_to_the_kept_duplicate(arch_catalog, bucket_template, trace) -> None:
    proven = {"rule_id": "ARCH-CIS-3.1.4", "status": "FAIL", "line_start": 4, "line_end": 7,
              "rationale": "Nur BlockPublicAcls.", "recommendation": "Alle vier setzen."}
    unproven = {**proven, "line_start": None, "line_end": None, "rationale": "Ohne Beleg."}

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[ToolCallPart("submit_audit", {"findings": [proven, unproven]})])

    report = run_audit(arch_catalog, bucket_template, FunctionModel(respond), trace)

    bucket = next(f for f in report.findings if f.rule_id == "ARCH-CIS-3.1.4")
    assert (bucket.status, bucket.rationale, bucket.downgraded_from) == (
        "FAIL", "Nur BlockPublicAcls.", None)


def test_fail_without_recommendation_gets_the_rule_recommendation_as_is(
    arch_catalog, bucket_template, trace
) -> None:
    public = {"rule_id": "ARCH-CIS-3.1.4", "status": "FAIL", "line_start": 4, "line_end": 7,
              "rationale": "Nur BlockPublicAcls.", "recommendation": None}

    report = run_audit(arch_catalog, bucket_template, fake(public, prompts=[]), trace)

    bucket = next(f for f in report.findings if f.rule_id == "ARCH-CIS-3.1.4")
    assert (bucket.status, bucket.recommendation) == ("FAIL", "Maßnahme ergänzen.")
    assert bucket.corrections == ["ARCH-CIS-3.1.4: Empfehlung aus der Prüfregel ergänzt: "
                                  "Die KI hat bei FAIL keine genannt."]
