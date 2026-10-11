"""Stage ② of the selection (ARCHITECTURE 1.1): one LLM verdict per requirement."""

import pytest
from pydantic_ai import UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from kb_build.classify import classify_requirement
from kb_build.extracted_models import Requirement
from kb_build.selection_models import Classification

REQUIREMENT = Requirement(
    id="3.1.4", title="Block Public Access", text="Ensure that S3 blocks public access.",
    primary_anchor="CIS AWS v7.0.0 3.1.4", attributes={}, prefilter_passed=True,
)


def answer_in_turns(*turns: dict, seen: list | None = None) -> FunctionModel:
    """Fake LLM calling classify_requirement turn by turn; repeats the last turn."""
    calls: list[list[ModelMessage]] = seen if seen is not None else []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        calls.append(messages)
        turn = turns[min(len(calls) - 1, len(turns) - 1)]
        return ModelResponse(parts=[ToolCallPart("classify_requirement", turn)])

    return FunctionModel(respond, model_name="fake-model")


BUCKET = {"testable": True, "rationale": "Am Bucket prüfbar.",
          "cfn_resource_types": ["AWS::S3::Bucket"]}


def test_architecture_classification_keeps_resource_types() -> None:
    seen: list = []

    model = answer_in_turns(BUCKET, seen=seen)
    result = classify_requirement(REQUIREMENT, "CIS", "architecture", model)

    assert result == Classification(**BUCKET)
    assert "Ensure that S3 blocks public access." in str(seen[0])  # the requirement is asked about
    assert "CloudFormation" in str(seen[0])


def test_spec_classification_never_has_resource_types() -> None:
    seen: list = []

    result = classify_requirement(REQUIREMENT, "DSGVO", "spec", answer_in_turns(BUCKET, seen=seen))

    assert result.testable is True
    assert result.cfn_resource_types == []
    assert "CloudFormation" not in str(seen[0])


def test_architecture_answer_without_valid_resource_types_gets_one_retry() -> None:
    seen: list = []
    wrong = {"testable": True, "rationale": "x", "cfn_resource_types": ["S3 bucket"]}

    result = classify_requirement(REQUIREMENT, "CIS", "architecture",
                                  answer_in_turns(wrong, BUCKET, seen=seen))

    assert len(seen) == 2
    assert "AWS::" in str(seen[1])  # the retry names the expected format
    assert result.cfn_resource_types == ["AWS::S3::Bucket"]


def test_architecture_answer_stays_invalid_after_the_retry_fails_closed() -> None:
    wrong = {"testable": True, "rationale": "x", "cfn_resource_types": []}

    with pytest.raises(UnexpectedModelBehavior):
        classify_requirement(REQUIREMENT, "CIS", "architecture", answer_in_turns(wrong))


def test_not_testable_requirement_has_no_resource_types() -> None:
    no = {"testable": False, "rationale": "Organisatorisch.",
          "cfn_resource_types": ["AWS::S3::Bucket"]}

    result = classify_requirement(REQUIREMENT, "CIS", "architecture", answer_in_turns(no))

    assert result.testable is False
    assert result.cfn_resource_types == []


def test_architecture_prompt_counts_general_principles_that_show_in_resources() -> None:
    # BER.4.1 was judged "not testable" with the stricter wording (issue #6, first real run)
    seen: list = []

    classify_requirement(REQUIREMENT, "CIS", "architecture", answer_in_turns(BUCKET, seen=seen))

    assert "geringste Berechtigungen" in str(seen[0])
    assert "IAM-Policies" in str(seen[0])


def test_spec_prompt_counts_requirements_a_spec_can_show_evidence_for() -> None:
    # Art. 9 and M60.P01 were judged "not testable" with the stricter wording (first real run)
    seen: list = []

    classify_requirement(REQUIREMENT, "DSGVO", "spec", answer_in_turns(BUCKET, seen=seen))

    assert "bewusst ausschweigen" in str(seen[0])
    assert "Löschfristen" in str(seen[0])


def test_architecture_answer_with_an_invented_resource_type_gets_one_retry() -> None:
    # The LLM invented AWS::S3::BucketPublicAccessBlock for CIS 3.1.4 (first real run)
    seen: list = []
    invented = {"testable": True, "rationale": "x",
                "cfn_resource_types": ["AWS::S3::BucketPublicAccessBlock"]}

    result = classify_requirement(REQUIREMENT, "CIS", "architecture",
                                  answer_in_turns(invented, BUCKET, seen=seen))

    assert len(seen) == 2
    assert "BucketPublicAccessBlock" in str(seen[1])  # the retry names the invented type
    assert result.cfn_resource_types == ["AWS::S3::Bucket"]


def test_architecture_prompt_excludes_account_wide_duties() -> None:
    seen: list = []

    classify_requirement(REQUIREMENT, "CIS", "architecture", answer_in_turns(BUCKET, seen=seen))

    assert "Support-Rolle" in str(seen[0])


def test_classification_runs_at_temperature_zero_for_reproducible_selections() -> None:
    # Run 3: Art. 9 was testable in run 2 and not testable in run 3 with the default temperature
    settings: list = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        settings.append(info.model_settings)
        return ModelResponse(parts=[ToolCallPart("classify_requirement", BUCKET)])

    classify_requirement(REQUIREMENT, "CIS", "architecture", FunctionModel(respond))

    assert settings[0]["temperature"] == 0


def test_architecture_prompt_names_the_services_of_the_scope() -> None:
    seen: list = []
    scope = {"Lambda": ["AWS::Lambda::Function"], "DynamoDB": ["AWS::DynamoDB::Table"]}

    classify_requirement(REQUIREMENT, "CIS", "architecture",
                         answer_in_turns(BUCKET, seen=seen), scope)

    assert "Prüfumfang" in str(seen[0])
    assert "Lambda, DynamoDB" in str(seen[0])


def test_spec_prompt_does_not_mention_the_scope() -> None:
    seen: list = []
    scope = {"Lambda": ["AWS::Lambda::Function"]}

    classify_requirement(REQUIREMENT, "DSGVO", "spec", answer_in_turns(BUCKET, seen=seen), scope)

    assert "Prüfumfang" not in str(seen[0])
