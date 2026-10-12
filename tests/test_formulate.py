"""formulate_rules(): the LLM writes the rule, the code adds what it knows (ARCHITECTURE 1.2)."""

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

from kb_build.cfn_properties import PropertyIndex
from kb_build.extracted_models import ExtractedSource
from kb_build.formulate import formulate_rules
from kb_build.selection_models import SelectedRequirement, Selection

SOURCES = [
    ExtractedSource(source="CIS", version="v7.0.0", origin="o",
                    requirements=[make_requirement("3.1.4", "CIS AWS v7.0.0 3.1.4")]),
    ExtractedSource(source="BSI", version="sha", origin="o",
                    requirements=[make_requirement("DET.3.1", "BSI GS++ DET.3.1")]),
]


PROPERTIES = PropertyIndex({  # stands in for data/cfn_properties.json
    "AWS::S3::Bucket": frozenset({"BucketEncryption", "LoggingConfiguration",
                                  "LoggingConfiguration.LogFilePrefix"}),
    "AWS::KMS::Key": frozenset({"KeyPolicy"}),
})


def run_formulate(model, selection, sources):
    return formulate_rules(model, selection, sources, PROPERTIES)


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
        run_formulate(fake_llm({"3.1.4": [wrong] * 4}), arch_selection("3.1.4"), SOURCES)


def test_a_spec_rule_drops_spaces_from_the_id_and_has_no_resource_types() -> None:
    seen: list[str] = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.extend(str(m.instructions) for m in messages if hasattr(m, "instructions"))
        return ModelResponse(parts=[ToolCallPart("formulate_rule", draft("Art. 32"))])

    catalog = run_formulate(FunctionModel(respond), SPEC_SELECTION, [DSGVO, *SOURCES])

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


def test_spec_criteria_may_use_the_words_of_the_law() -> None:
    # DSGVO Art. 32 itself demands "geeignete" and "angemessene" measures
    lawful = draft("Art. 32", compliant_if="Die Spezifikation nennt angemessene Maßnahmen.")
    asked: list[str] = []

    run_formulate(fake_llm({"Art. 32": [lawful]}, asked), SPEC_SELECTION, [DSGVO])

    assert asked == ["Art. 32"]  # accepted at the first attempt


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

    formulate_rules(retry_prompts(sent_back, first), arch_selection("3.1.4"), SOURCES, properties)

    assert "AWS::SecretsManager::RotationSchedule" in sent_back[0]
