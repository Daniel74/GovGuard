"""formulate_rules(): the LLM writes the rule, the code adds what it knows (ARCHITECTURE 1.2)."""

import re

import pytest
from conftest import make_requirement
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    RetryPromptPart,
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from kb_build.extract.models import ExtractedSource
from kb_build.reference.cfn_properties import PropertyIndex
from kb_build.reference.scope import Scope
from kb_build.rules.formulate import FORMULATE_RETRIES, formulate_rules
from kb_build.rules.violation_judge import JUDGE_TOOL_NAME
from kb_build.select.models import SelectedRequirement, Selection

SOURCES = [
    ExtractedSource(source="CIS", version="v7.0.0", origin="o",
                    requirements=[make_requirement("3.1.4", "CIS AWS v7.0.0 3.1.4")]),
    ExtractedSource(source="BSI", version="sha", origin="o",
                    requirements=[make_requirement("DET.3.1", "BSI GS++ DET.3.1")]),
]


PROPERTIES = PropertyIndex({  # stands in for data/input/cfn_properties.json
    "AWS::S3::Bucket": frozenset({"BucketEncryption", "LoggingConfiguration",
                                  "LoggingConfiguration.LogFilePrefix"}),
    "AWS::KMS::Key": frozenset({"KeyPolicy"}),
})


SCOPE = Scope({"S3": ["AWS::S3::Bucket"], "KMS": ["AWS::KMS::Key"]})


def run_formulate(model, selection, sources):
    return formulate_rules(model, selection, sources, PROPERTIES, SCOPE)


def draft(rid: str, **changes) -> dict:
    return {"source_quote": f"The text of {rid}", "title": f"Titel {rid}",
            "compliant_if": "AWS::S3::Bucket setzt BucketEncryption.",
            "violation_if": "BucketEncryption fehlt.", "recommendation": "Abhilfe",
            "cross_references": []} | changes


def fake_llm(answers: dict[str, list[dict]], asked: list[str] | None = None) -> FunctionModel:
    """Answers per requirement ID (read from the prompt), one answer per attempt."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        prompt = next(
            p.content for m in messages for p in m.parts if isinstance(p, UserPromptPart)
        )
        rid = prompt.split("ID: ")[1].splitlines()[0]
        if asked is not None:
            asked.append(rid)
        return ModelResponse(parts=[ToolCallPart("formulate_rule", answers[rid].pop(0))])

    return FunctionModel(respond, model_name="fake-model")


def arch_selection(*ids: str) -> Selection:
    selected = [
        SelectedRequirement(requirement_id=i, source="CIS", rationale=f"prüfbar {i}",
                            cfn_resource_types=["AWS::S3::Bucket", "AWS::KMS::Key"])
        for i in ids
    ]
    return Selection(audit_type="architecture", model_id="selector", selected=selected)


DSGVO = ExtractedSource(source="DSGVO", version="000.003", origin="o",
                        requirements=[make_requirement("Art. 32", "DSGVO Art. 32")])
SPEC_SELECTION = Selection(audit_type="spec", model_id="selector", selected=[SelectedRequirement(
    requirement_id="Art. 32", source="DSGVO", rationale="prüfbar", cfn_resource_types=[])])


def test_the_code_adds_identity_origin_and_types_from_the_selection() -> None:
    catalog = run_formulate(fake_llm({"3.1.4": [draft("3.1.4")]}), arch_selection("3.1.4"),
                              SOURCES)

    assert (catalog.audit_type, catalog.model_id) == ("architecture", "fake-model")
    assert catalog.source_versions == {"CIS": "v7.0.0"}  # only sources with rules
    rule = catalog.rules[0]
    assert rule.id == "ARCH-CIS-3.1.4"
    assert (rule.audit_type, rule.source) == ("architecture", "CIS")
    assert rule.primary_anchor == "CIS AWS v7.0.0 3.1.4"
    assert rule.selection_rationale == "prüfbar 3.1.4"
    assert rule.cfn_resource_types == ["AWS::S3::Bucket", "AWS::KMS::Key"]
    assert (rule.source_quote, rule.title) == ("The text of 3.1.4", "Titel 3.1.4")


def retry_prompts(messages: list[str], first: dict) -> FunctionModel:
    """Answers `first`, then a valid draft; records what the validator sends back."""

    def respond(history: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        retries = [p.model_response() for m in history for p in m.parts
                   if isinstance(p, RetryPromptPart)]
        messages[:] = retries
        attempt = draft("3.1.4") if retries else first
        return ModelResponse(parts=[ToolCallPart("formulate_rule", attempt)])

    return FunctionModel(respond, model_name="fake-model")


def test_a_quote_not_in_the_requirement_is_sent_back_and_the_second_attempt_counts() -> None:
    sent_back: list[str] = []
    first = draft("3.1.4", source_quote="erfundener Normtext")

    catalog = run_formulate(retry_prompts(sent_back, first), arch_selection("3.1.4"), SOURCES)

    assert catalog.rules[0].source_quote == "The text of 3.1.4"
    assert "wörtlich" in sent_back[0]


def test_an_invented_cross_reference_is_sent_back_and_named() -> None:
    sent_back: list[str] = []
    invented = [{"anchor": "BSI GS++ DET.3.99", "origin": "ai_suggested"}]
    first = draft("3.1.4", cross_references=invented)

    catalog = run_formulate(retry_prompts(sent_back, first), arch_selection("3.1.4"), SOURCES)

    assert catalog.rules[0].cross_references == []
    assert "BSI GS++ DET.3.99" in sent_back[0]


def test_an_answer_that_stays_invalid_aborts_the_build_and_names_the_requirement() -> None:
    wrong = draft("3.1.4", source_quote="erfundener Normtext")

    with pytest.raises(ValueError, match="CIS 3.1.4"):
        run_formulate(fake_llm({"3.1.4": [wrong] * (FORMULATE_RETRIES + 1)}),
                      arch_selection("3.1.4"), SOURCES)


def test_a_spec_rule_drops_spaces_from_the_id_and_has_no_resource_types() -> None:
    seen: list[str] = []
    llm = spec_llm([draft("Art. 32", violation_if=STIPULATION)], instructions=seen)

    catalog = run_formulate(llm, SPEC_SELECTION, [DSGVO, *SOURCES])

    rule = catalog.rules[0]
    assert (rule.id, rule.audit_type, rule.cfn_resource_types) == (
        "SPEC-DSGVO-Art.32", "spec", [])
    assert catalog.source_versions == {"DSGVO": "000.003"}
    assert "Spec-Audit einer fachlichen Spezifikation" in seen[0]


def test_the_retry_names_where_the_quote_deviates_and_what_the_text_says() -> None:
    # DSGVO Art. 46: the model wrote "der Verantwortlicher" three times instead of "Verantwortliche"
    sent_back: list[str] = []
    first = draft("3.1.4", source_quote="The text of 3.1.4 should be quoted.")

    run_formulate(retry_prompts(sent_back, first), arch_selection("3.1.4"), SOURCES)

    assert "„should be quoted.“" in sent_back[0]
    assert "„must be quoted.“" in sent_back[0]


def test_vague_words_in_architecture_criteria_are_sent_back_and_named() -> None:
    # BSI KONF.6.1: "nicht erforderlich" cannot be decided from a template
    sent_back: list[str] = []
    first = draft("3.1.4", violation_if="Policies gewähren Rechte, die nicht erforderlich sind.")

    catalog = run_formulate(retry_prompts(sent_back, first), arch_selection("3.1.4"), SOURCES)

    assert catalog.rules[0].violation_if == "BucketEncryption fehlt."
    assert "„erforderlich“" in sent_back[0]


def test_architecture_criteria_without_a_resource_type_of_the_rule_are_sent_back() -> None:
    sent_back: list[str] = []
    first = draft("3.1.4", compliant_if="Alle Daten sind verschlüsselt.",
                  violation_if="Daten liegen im Klartext.")

    run_formulate(retry_prompts(sent_back, first), arch_selection("3.1.4"), SOURCES)

    assert "AWS::S3::Bucket, AWS::KMS::Key" in sent_back[0]


ABSENCE = "Die Spezifikation nennt kein maschinenlesbares Exportformat."
STIPULATION = "Die Spezifikation legt als Exportformat nur PDF fest."


def spec_llm(drafts: list[dict], sent_back: list[str] | None = None,
             judged: list[str] | None = None,
             instructions: list[str] | None = None) -> FunctionModel:
    """Formulates `drafts` one per attempt; the judge calls every 'nennt kein' an absence."""

    def respond(history: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if instructions is not None:
            instructions.append(str(info.instructions))
        prompt = next(p.content for m in history for p in m.parts if isinstance(p, UserPromptPart))
        if info.output_tools[0].name == JUDGE_TOOL_NAME:
            if judged is not None:
                judged.append(prompt)
            absence = "nennt kein" in prompt
            check = {"describes_absence": absence, "reason": "Der Satz beschreibt ein Fehlen."
                     if absence else "Der Satz beschreibt eine Festlegung."}
            return ModelResponse(parts=[ToolCallPart(JUDGE_TOOL_NAME, check)])
        if sent_back is not None:
            sent_back[:] = [p.model_response() for m in history for p in m.parts
                            if isinstance(p, RetryPromptPart)]
        return ModelResponse(parts=[ToolCallPart("formulate_rule", drafts.pop(0))])

    return FunctionModel(respond, model_name="fake-model")


def test_a_spec_violation_describing_an_absence_is_sent_back_with_the_judges_reason() -> None:
    # open world (ADR 0020): silence is WARN, so violation_if must describe a stipulation
    sent_back: list[str] = []
    drafts = [draft("Art. 32", violation_if=ABSENCE), draft("Art. 32", violation_if=STIPULATION)]

    catalog = run_formulate(spec_llm(drafts, sent_back), SPEC_SELECTION, [DSGVO])

    assert catalog.rules[0].violation_if == STIPULATION
    assert "Der Satz beschreibt ein Fehlen." in sent_back[0]


def test_only_the_spec_prompt_asks_for_a_stipulation_as_violation() -> None:
    spec, arch = [], []

    run_formulate(spec_llm([draft("Art. 32", violation_if=STIPULATION)], instructions=spec),
                  SPEC_SELECTION, [DSGVO])
    run_formulate(spec_llm([draft("3.1.4")], instructions=arch), arch_selection("3.1.4"), SOURCES)

    assert "offene Welt" in spec[0] and "erklärten Verzicht oder Aufschub" in spec[0]
    assert "offene Welt" not in arch[0]


def test_the_run_reports_how_often_the_judge_sent_an_absence_back(
    caplog: pytest.LogCaptureFixture
) -> None:
    drafts = [draft("Art. 32", violation_if=ABSENCE), draft("Art. 32", violation_if=STIPULATION)]

    with caplog.at_level("INFO", logger="kb_build"):
        run_formulate(spec_llm(drafts), SPEC_SELECTION, [DSGVO])

    assert "spec quality judge: retries=1 llm_error=0" in [r.getMessage() for r in caplog.records]


def test_the_run_logs_the_tokens_of_every_request_retries_and_judge_included(
    caplog: pytest.LogCaptureFixture
) -> None:
    drafts = [draft("Art. 32", violation_if=ABSENCE), draft("Art. 32", violation_if=STIPULATION)]

    with caplog.at_level("INFO", logger="kb_build"):
        run_formulate(spec_llm(drafts), SPEC_SELECTION, [DSGVO])

    usage = [r.getMessage() for r in caplog.records if "tokens" in r.getMessage()]
    # two drafts, each judged once
    assert len(usage) == 1
    assert re.fullmatch(r"spec: 4 requests, [1-9]\d* input tokens, [1-9]\d* output tokens",
                        usage[0])


def test_an_aborted_run_still_logs_its_tokens(caplog: pytest.LogCaptureFixture) -> None:
    wrong = draft("3.1.4", source_quote="erfundener Normtext")

    with caplog.at_level("INFO", logger="kb_build"), pytest.raises(ValueError):
        run_formulate(fake_llm({"3.1.4": [wrong] * (FORMULATE_RETRIES + 1)}),
                      arch_selection("3.1.4"), SOURCES)

    assert any(r.getMessage().startswith(f"architecture: {FORMULATE_RETRIES + 1} requests")
               for r in caplog.records)


def test_the_log_names_each_retry_with_its_reason_and_the_rejected_violation(
    caplog: pytest.LogCaptureFixture
) -> None:
    # the same text the model reads as retry prompt (CONTEXT.md: Korrektur)
    drafts = [draft("Art. 32", violation_if=ABSENCE), draft("Art. 32", violation_if=STIPULATION)]

    with caplog.at_level("INFO", logger="kb_build"):
        run_formulate(spec_llm(drafts), SPEC_SELECTION, [DSGVO])

    retries = [r.getMessage() for r in caplog.records if " retry " in r.getMessage()]
    assert len(retries) == 1
    assert retries[0].startswith("spec DSGVO Art. 32 retry 1: ")
    assert ABSENCE in retries[0] and "Der Satz beschreibt ein Fehlen." in retries[0]


def test_an_architecture_retry_is_logged_with_its_reason(caplog: pytest.LogCaptureFixture) -> None:
    first = draft("3.1.4", source_quote="erfundener Normtext")

    with caplog.at_level("INFO", logger="kb_build"):
        run_formulate(retry_prompts([], first), arch_selection("3.1.4"), SOURCES)

    assert any(r.getMessage().startswith("architecture CIS 3.1.4 retry 1: Das Zitat steht nicht")
               for r in caplog.records)


def test_a_judge_that_stays_invalid_aborts_the_build_and_names_the_requirement(
    caplog: pytest.LogCaptureFixture
) -> None:
    # fail closed: an unjudged spec rule could carry an absence into the catalog
    def respond(history: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if info.output_tools[0].name == JUDGE_TOOL_NAME:
            return ModelResponse(parts=[ToolCallPart(JUDGE_TOOL_NAME, {"reason": "ohne Urteil"})])
        return ModelResponse(parts=[ToolCallPart("formulate_rule",
                                                 draft("Art. 32", violation_if=STIPULATION))])

    with (caplog.at_level("INFO", logger="kb_build"),
          pytest.raises(ValueError, match="DSGVO Art. 32")):
        run_formulate(FunctionModel(respond), SPEC_SELECTION, [DSGVO])

    assert "spec quality judge: retries=0 llm_error=1" in [r.getMessage() for r in caplog.records]


def test_an_architecture_violation_may_describe_a_missing_setting_the_judge_is_not_asked() -> None:
    # closed world (ADR 0020): a missing setting is the default value, often the violation
    judged: list[str] = []

    catalog = run_formulate(spec_llm([draft("3.1.4")], judged=judged), arch_selection("3.1.4"),
                            SOURCES)

    assert catalog.rules[0].violation_if == "BucketEncryption fehlt."
    assert judged == []


def test_spec_criteria_may_use_the_words_of_the_law() -> None:
    # DSGVO Art. 32 itself demands "geeignete" and "angemessene" measures
    lawful = draft("Art. 32", compliant_if="Die Spezifikation nennt angemessene Maßnahmen.",
                   violation_if=STIPULATION)
    sent_back: list[str] = []

    run_formulate(spec_llm([lawful], sent_back), SPEC_SELECTION, [DSGVO])

    assert sent_back == []  # accepted at the first attempt


def test_an_invented_property_is_sent_back_and_named_with_the_known_ones() -> None:
    # CIS 4.4: CloudFormation knows LogFilePrefix at the bucket, not TargetPrefix
    sent_back: list[str] = []
    first = draft("3.1.4", compliant_if="AWS::S3::Bucket setzt LoggingConfiguration.TargetPrefix.")

    catalog = run_formulate(retry_prompts(sent_back, first), arch_selection("3.1.4"), SOURCES)

    assert catalog.rules[0].compliant_if == "AWS::S3::Bucket setzt BucketEncryption."
    assert "LoggingConfiguration.TargetPrefix" in sent_back[0]
    assert "LoggingConfiguration.LogFilePrefix" in sent_back[0]


def test_the_retry_names_the_type_that_really_has_the_property() -> None:
    # FSBP SecretsManager.1: rotation is set at RotationSchedule, not at the Secret
    schedule = {"AWS::SecretsManager::RotationSchedule": frozenset({"RotationRules"})}
    properties = PropertyIndex(PROPERTIES.paths | schedule)
    sent_back: list[str] = []
    first = draft("3.1.4", compliant_if="AWS::S3::Bucket setzt RotationRules.")

    formulate_rules(retry_prompts(sent_back, first), arch_selection("3.1.4"), SOURCES, properties,
                    SCOPE)

    assert "AWS::SecretsManager::RotationSchedule" in sent_back[0]


def test_criteria_naming_a_type_outside_the_scope_are_sent_back_and_name_it() -> None:
    # CIS 3.1.4 named AWS::CloudTrail::Trail; no property check can judge a type outside the scope
    sent_back: list[str] = []
    first = draft("3.1.4", violation_if="AWS::CloudTrail::Trail schreibt nicht ins Bucket.")

    catalog = run_formulate(retry_prompts(sent_back, first), arch_selection("3.1.4"), SOURCES)

    assert catalog.rules[0].violation_if == "BucketEncryption fehlt."
    assert "AWS::CloudTrail::Trail" in sent_back[0]
    assert "Prüfumfang" in sent_back[0]


def test_a_stubborn_model_gets_every_retry_before_the_build_stops() -> None:
    # Groq (ADR 0014) repeats an invented quote or property; the gate stays strict, not the count
    calls = []

    def respond(history: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        calls.append(1)
        invented = len(calls) <= FORMULATE_RETRIES
        attempt = draft("3.1.4", source_quote="erfunden") if invented else draft("3.1.4")
        return ModelResponse(parts=[ToolCallPart("formulate_rule", attempt)])

    catalog = run_formulate(FunctionModel(respond, model_name="fake-model"),
                            arch_selection("3.1.4"), SOURCES)

    assert catalog.rules[0].source_quote == "The text of 3.1.4"
    assert len(calls) == FORMULATE_RETRIES + 1


def test_the_run_reports_the_retries_of_the_formulate_gate(
    caplog: pytest.LogCaptureFixture
) -> None:
    first = draft("3.1.4", source_quote="The text of 3.1.4 should be quoted.")

    with caplog.at_level("INFO", logger="kb_build"):
        run_formulate(retry_prompts([], first), arch_selection("3.1.4"), SOURCES)

    # llm_error stays 0: the retry made the rule valid
    assert "architecture quality formulate: retries=1 llm_error=0" in [
        r.getMessage() for r in caplog.records]


def test_an_aborted_run_still_reports_retries_and_the_llm_error(
    caplog: pytest.LogCaptureFixture
) -> None:
    def invents(history: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        return ModelResponse(parts=[ToolCallPart("formulate_rule",
                                                 draft("3.1.4", source_quote="erfunden"))])

    with caplog.at_level("INFO", logger="kb_build"), pytest.raises(ValueError):
        run_formulate(FunctionModel(invents, model_name="fake-model"),
                      arch_selection("3.1.4"), SOURCES)

    expected = f"architecture quality formulate: retries={FORMULATE_RETRIES} llm_error=1"
    assert expected in [r.getMessage() for r in caplog.records]
