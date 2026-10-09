"""Stage ② of the selection (ARCHITECTURE 1.1): the LLM judges, the code selects."""

import pytest
from pydantic_ai import UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from kb_build.archetype_profiles import load_profiles
from kb_build.classify import classify_requirement
from kb_build.curation import curate
from kb_build.extracted_models import ExtractedSource, Requirement
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


# --- curate(): prefilter, pinned slots, relevance, ranking -------------------------------------


def req(rid: str, prefilter: bool = True, **attributes) -> Requirement:
    return Requirement(
        id=rid, title=f"title {rid}", text=f"text {rid}", primary_anchor=f"A {rid}",
        attributes=attributes, prefilter_passed=prefilter,
    )


def cis_source(*requirements: Requirement) -> ExtractedSource:
    return ExtractedSource(source="CIS", version="v7", origin="o", requirements=list(requirements))


def judge(answers: dict[str, dict], asked: list[str]) -> FunctionModel:
    """Fake LLM answering per requirement ID (read from the prompt); records who was asked."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        prompt = next(  # the retry prompt comes after the original user prompt
            p.content for m in messages for p in m.parts if isinstance(p, UserPromptPart)
        )
        rid = prompt.split("ID: ")[1].splitlines()[0]
        asked.append(rid)
        return ModelResponse(parts=[ToolCallPart("classify_requirement", answers[rid])])

    return FunctionModel(respond, model_name="fake-model")


def can_test(*types: str) -> dict:
    return {"testable": True, "rationale": "prüfbar", "cfn_resource_types": list(types)}


NOT_TESTABLE = {"testable": False, "rationale": "organisatorisch", "cfn_resource_types": []}
CIS_ATTRS = {"level": 1, "automated": True}


def curate_cis(source: ExtractedSource, answers: dict, pinned: set[str] = frozenset()):
    result, asked = curate_cis_result(source, answers, pinned)
    return result.selection, asked


def curate_cis_result(source: ExtractedSource, answers: dict, pinned: set[str] = frozenset()):
    asked: list[str] = []
    result = curate("architecture", [source], pinned, load_profiles(), judge(answers, asked))
    return result, asked


def test_curate_asks_only_prefiltered_requirements_and_keeps_testable_relevant_ones() -> None:
    source = cis_source(
        req("3.1.4", **CIS_ATTRS), req("3.1.9", prefilter=False, **CIS_ATTRS),
        req("2.1.1", **CIS_ATTRS), req("2.1.2", **CIS_ATTRS),
    )
    answers = {"3.1.4": can_test("AWS::S3::Bucket"), "2.1.1": NOT_TESTABLE,
               "2.1.2": can_test("AWS::EC2::Instance")}  # EC2 is no archetype resource type

    selection, asked = curate_cis(source, answers)

    assert sorted(asked) == ["2.1.1", "2.1.2", "3.1.4"]
    assert selection.audit_type == "architecture"
    assert selection.model_id == "fake-model"
    kept = [(s.requirement_id, s.source, s.rank) for s in selection.selected]
    assert kept == [("3.1.4", "CIS", 1)]


def test_curate_pins_an_anchor_even_if_prefilter_and_relevance_would_drop_it() -> None:
    source = cis_source(req("3.1.4", **CIS_ATTRS), req("4.6", prefilter=False, **CIS_ATTRS))
    answers = {"3.1.4": can_test("AWS::S3::Bucket"), "4.6": can_test("AWS::CloudTrail::Trail")}

    selection, _ = curate_cis(source, answers, pinned={"A 4.6"})

    assert [(s.requirement_id, s.pinned, s.rank) for s in selection.selected] == [
        ("4.6", True, 1), ("3.1.4", False, 2)]


def test_curate_rejects_a_pinned_anchor_that_is_not_testable() -> None:
    source = cis_source(req("4.6", **CIS_ATTRS))

    with pytest.raises(ValueError, match="A 4.6"):
        curate_cis(source, {"4.6": NOT_TESTABLE}, pinned={"A 4.6"})


def test_curate_rejects_a_pinned_anchor_missing_in_the_sources() -> None:
    with pytest.raises(ValueError, match="A 9.9"):
        curate_cis(cis_source(req("3.1.4", **CIS_ATTRS)), {}, pinned={"A 9.9"})


def test_curate_allows_at_most_four_pinned_anchors() -> None:
    ids_ = ["1.1", "1.2", "1.3", "1.4", "1.5"]
    source = cis_source(*[req(i, **CIS_ATTRS) for i in ids_])

    with pytest.raises(ValueError, match="at most 4"):
        curate_cis(source, {i: can_test("AWS::S3::Bucket") for i in ids_},
                   pinned={f"A {i}" for i in ids_})


def test_curate_spec_has_no_relevance_filter_and_no_resource_types() -> None:
    source = ExtractedSource(
        source="DSGVO", version="v", origin="o",
        requirements=[req("Art. 32", chapter=4, fine_tier=2)],
    )
    answers = {"Art. 32": can_test("AWS::S3::Bucket")}

    selection = curate("spec", [source], set(), load_profiles(), judge(answers, [])).selection

    assert [(s.requirement_id, s.cfn_resource_types) for s in selection.selected] == [
        ("Art. 32", [])]


def test_curate_logs_progress_per_requirement(caplog: pytest.LogCaptureFixture) -> None:
    source = cis_source(req("3.1.4", **CIS_ATTRS), req("3.1.9", **CIS_ATTRS))
    answers = {"3.1.4": can_test("AWS::S3::Bucket"), "3.1.9": NOT_TESTABLE}

    with caplog.at_level("INFO", logger="kb_build"):
        curate_cis(source, answers)

    assert [r.getMessage() for r in caplog.records] == [
        "CIS 1/2 3.1.4 testable", "CIS 2/2 3.1.9 not testable"]


def test_curate_checks_all_pinned_anchors_before_classifying_anything_else() -> None:
    bsi = ExtractedSource(
        source="BSI", version="v", origin="o",
        requirements=[req("DET.3.1", cia_sum=4), req("BER.4.1", cia_sum=4)],
    )
    cis = cis_source(req("4.6", **CIS_ATTRS))
    asked: list[str] = []
    answers = {"DET.3.1": can_test("AWS::S3::Bucket"), "BER.4.1": can_test("AWS::IAM::Role"),
               "4.6": NOT_TESTABLE}

    with pytest.raises(ValueError, match="A 4.6"):
        curate("architecture", [bsi, cis], {"A BER.4.1", "A 4.6"}, load_profiles(),
               judge(answers, asked))

    assert "DET.3.1" not in asked  # failed fast: the 380 other BSI requirements are never paid for


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


def outcomes(result) -> dict[str, str]:
    return {v.requirement_id: v.outcome for v in result.verdicts}


def test_curate_reports_why_each_asked_requirement_was_kept_or_dropped() -> None:
    source = cis_source(
        req("3.1.4", **CIS_ATTRS), req("3.1.9", prefilter=False, **CIS_ATTRS),
        req("2.1.1", **CIS_ATTRS), req("4.8", **CIS_ATTRS),
        req("4.6", prefilter=False, **CIS_ATTRS),
    )
    answers = {"3.1.4": can_test("AWS::S3::Bucket"), "2.1.1": NOT_TESTABLE,
               "4.8": can_test("AWS::CloudTrail::Trail", "AWS::S3::Bucket"),
               "4.6": can_test("AWS::KMS::Key")}

    result, _ = curate_cis_result(source, answers, pinned={"A 4.6"})

    assert outcomes(result) == {
        "4.6": "pinned", "3.1.4": "selected", "2.1.1": "not_testable", "4.8": "not_relevant"}
    assert "3.1.9" not in outcomes(result)  # the prefilter dropped it, the LLM never saw it


def test_curate_reports_testable_requirements_cut_by_the_cap() -> None:
    ids_ = [f"3.1.{n}" for n in range(1, 14)]  # 13 candidates, cap of CIS is 12
    source = cis_source(*[req(i, **CIS_ATTRS) for i in ids_])

    result, _ = curate_cis_result(source, {i: can_test("AWS::S3::Bucket") for i in ids_})

    assert list(outcomes(result).values()).count("over_cap") == 1
    verdict = next(v for v in result.verdicts if v.outcome == "over_cap")
    assert (verdict.requirement_id, verdict.title, verdict.rationale) == (
        "3.1.13", "title 3.1.13", "prüfbar")


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


def test_one_unusable_answer_excludes_that_requirement_but_not_the_whole_run() -> None:
    # Run 3: the LLM invented AWS::SES::DomainDKIM twice and aborted the run at BSI 371/380
    invented = {"testable": True, "rationale": "x", "cfn_resource_types": ["AWS::SES::DomainDKIM"]}
    source = cis_source(req("3.1.4", **CIS_ATTRS), req("3.9.9", **CIS_ATTRS))
    answers = {"3.1.4": can_test("AWS::S3::Bucket"), "3.9.9": invented}

    result, _ = curate_cis_result(source, answers)

    assert outcomes(result) == {"3.1.4": "selected", "3.9.9": "llm_error"}
    assert [s.requirement_id for s in result.selection.selected] == ["3.1.4"]


def test_a_pinned_anchor_with_an_unusable_answer_still_aborts_the_run() -> None:
    invented = {"testable": True, "rationale": "x", "cfn_resource_types": ["AWS::SES::DomainDKIM"]}
    source = cis_source(req("4.6", **CIS_ATTRS))

    with pytest.raises(ValueError, match="A 4.6"):
        curate_cis_result(source, {"4.6": invented}, pinned={"A 4.6"})


def test_classification_runs_at_temperature_zero_for_reproducible_selections() -> None:
    # Run 3: Art. 9 was testable in run 2 and not testable in run 3 with the default temperature
    settings: list = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        settings.append(info.model_settings)
        return ModelResponse(parts=[ToolCallPart("classify_requirement", BUCKET)])

    classify_requirement(REQUIREMENT, "CIS", "architecture", FunctionModel(respond))

    assert settings[0]["temperature"] == 0
