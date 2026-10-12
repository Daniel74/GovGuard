"""formulate_rules(): the LLM writes the rule, the code adds what it knows (ARCHITECTURE 1.2)."""

import pytest
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    RetryPromptPart,
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from kb_build.curation import formulate_rules
from kb_build.extracted_models import ExtractedSource, Requirement
from kb_build.selection_models import SelectedRequirement, Selection


def req(rid: str, anchor: str) -> Requirement:
    return Requirement(id=rid, title=f"title {rid}", text=f"The text of {rid} must be quoted.",
                       primary_anchor=anchor, attributes={}, prefilter_passed=True)


SOURCES = [
    ExtractedSource(source="CIS", version="v7.0.0", origin="o",
                    requirements=[req("3.1.4", "CIS AWS v7.0.0 3.1.4")]),
    ExtractedSource(source="BSI", version="sha", origin="o",
                    requirements=[req("DET.3.1", "BSI GS++ DET.3.1")]),
]


def draft(rid: str, **changes) -> dict:
    return {"source_quote": f"The text of {rid}", "title": f"Titel {rid}",
            "compliant_if": "konform", "violation_if": "Verstoß", "recommendation": "Abhilfe",
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


def test_the_code_adds_identity_origin_and_types_from_the_selection() -> None:
    catalog = formulate_rules(fake_llm({"3.1.4": [draft("3.1.4")]}), arch_selection("3.1.4"),
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

    catalog = formulate_rules(retry_prompts(sent_back, first), arch_selection("3.1.4"), SOURCES)

    assert catalog.rules[0].source_quote == "The text of 3.1.4"
    assert "wörtlich" in sent_back[0]


def test_an_invented_cross_reference_is_sent_back_and_named() -> None:
    sent_back: list[str] = []
    invented = [{"anchor": "BSI GS++ DET.3.99", "origin": "ai_suggested"}]
    first = draft("3.1.4", cross_references=invented)

    catalog = formulate_rules(retry_prompts(sent_back, first), arch_selection("3.1.4"), SOURCES)

    assert catalog.rules[0].cross_references == []
    assert "BSI GS++ DET.3.99" in sent_back[0]


def test_an_answer_that_stays_invalid_aborts_the_build_and_names_the_requirement() -> None:
    wrong = draft("3.1.4", source_quote="erfundener Normtext")

    with pytest.raises(ValueError, match="CIS 3.1.4"):
        formulate_rules(fake_llm({"3.1.4": [wrong] * 3}), arch_selection("3.1.4"), SOURCES)


def test_a_spec_rule_drops_spaces_from_the_id_and_has_no_resource_types() -> None:
    dsgvo = ExtractedSource(source="DSGVO", version="000.003", origin="o",
                            requirements=[req("Art. 32", "DSGVO Art. 32")])
    selection = Selection(audit_type="spec", model_id="selector", selected=[
        SelectedRequirement(requirement_id="Art. 32", source="DSGVO", rationale="prüfbar",
                            cfn_resource_types=[])])
    seen: list[str] = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.extend(str(m.instructions) for m in messages if hasattr(m, "instructions"))
        return ModelResponse(parts=[ToolCallPart("formulate_rule", draft("Art. 32"))])

    catalog = formulate_rules(FunctionModel(respond), selection, [dsgvo, *SOURCES])

    rule = catalog.rules[0]
    assert (rule.id, rule.audit_type, rule.cfn_resource_types) == (
        "SPEC-DSGVO-Art.32", "spec", [])
    assert catalog.source_versions == {"DSGVO": "000.003"}
    assert "Spec-Audit einer fachlichen Spezifikation" in seen[0]
