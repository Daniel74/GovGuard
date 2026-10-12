"""curate(): the LLM judges, the code selects (ARCHITECTURE 1.1, ADR 0011)."""

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from kb_build.classify import Judge
from kb_build.curation import curate
from kb_build.extracted_models import ExtractedSource, Requirement
from kb_build.scope import Scope

SCOPE = Scope({"S3": ["AWS::S3::Bucket"], "IAM": ["AWS::IAM::Role"], "KMS": ["AWS::KMS::Key"]})
NO_SCOPE = Scope({})
NO_COMPONENTS: frozenset[str] = frozenset()


def req(rid: str, prefilter: bool = True, reason: str | None = None, **attributes) -> Requirement:
    return Requirement(
        id=rid, title=f"title {rid}", text=f"text {rid}", primary_anchor=f"A {rid}",
        attributes=attributes, prefilter_passed=prefilter, prefilter_reason=reason,
    )


def cis_source(*requirements: Requirement) -> ExtractedSource:
    return ExtractedSource(source="CIS", version="v7", origin="o", requirements=list(requirements))


def fake_llm(answers: dict[str, dict], asked: list[str]) -> FunctionModel:
    """Fake LLM answering per requirement ID (read from the prompt); records who was asked."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        prompt = next(  # the retry prompt comes after the original user prompt
            p.content for m in messages for p in m.parts if isinstance(p, UserPromptPart)
        )
        rid = prompt.split("ID: ")[1].splitlines()[0]
        asked.append(rid)
        return ModelResponse(parts=[ToolCallPart("classify_requirement", answers[rid])])

    return FunctionModel(respond, model_name="fake-model")


def can_test(*types: str, level: str = "template") -> dict:
    return {"testable": True, "rationale": "prüfbar", "scope_level": level,
            "cfn_resource_types": list(types)}


NOT_TESTABLE = {"testable": False, "rationale": "organisatorisch", "cfn_resource_types": []}
INVENTED = {"testable": True, "rationale": "x", "cfn_resource_types": ["AWS::SES::DomainDKIM"]}


def curate_cis(source: ExtractedSource, answers: dict, pinned: set[str] = frozenset()):
    asked: list[str] = []
    judge = Judge("architecture", fake_llm(answers, asked))
    return curate(judge, [source], pinned, SCOPE, NO_COMPONENTS), asked


def outcomes(result) -> dict[str, str]:
    return {v.requirement_id: v.outcome for v in result.verdicts}


def test_curate_asks_only_prefiltered_requirements_and_keeps_testable_relevant_ones() -> None:
    source = cis_source(
        req("3.1.4"), req("3.1.9", prefilter=False), req("2.1.1"), req("2.1.2"),
    )
    answers = {"3.1.4": can_test("AWS::S3::Bucket"), "2.1.1": NOT_TESTABLE,
               "2.1.2": can_test("AWS::EC2::Instance")}  # EC2 instances are outside the scope

    result, asked = curate_cis(source, answers)

    assert sorted(asked) == ["2.1.1", "2.1.2", "3.1.4"]
    assert result.selection.audit_type == "architecture"
    assert result.selection.model_id == "fake-model"
    assert [(s.requirement_id, s.source) for s in result.selection.selected] == [("3.1.4", "CIS")]


def test_every_requirement_gets_exactly_one_verdict_in_source_order() -> None:
    source = cis_source(req("3.1.4"), req("3.1.9", prefilter=False), req("2.1.1"))
    answers = {"3.1.4": can_test("AWS::S3::Bucket"), "2.1.1": NOT_TESTABLE}

    result, _ = curate_cis(source, answers)

    assert [v.requirement_id for v in result.verdicts] == ["3.1.4", "3.1.9", "2.1.1"]
    assert outcomes(result) == {
        "3.1.4": "selected", "3.1.9": "prefiltered", "2.1.1": "not_testable"}


def test_a_prefiltered_requirement_keeps_the_sentence_of_the_prefilter() -> None:
    source = cis_source(req("5.1", prefilter=False, reason="Kapitel 5 gehört nicht dazu."))

    result, asked = curate_cis(source, {})

    assert asked == []  # the LLM never saw it
    assert result.verdicts[0].rationale == "Kapitel 5 gehört nicht dazu."


def test_a_requirement_outside_the_scope_gets_a_fixed_sentence_naming_the_type() -> None:
    source = cis_source(req("4.8"))
    answers = {"4.8": can_test("AWS::CloudTrail::Trail", "AWS::S3::Bucket")}

    result, _ = curate_cis(source, answers)

    verdict = result.verdicts[0]
    assert verdict.outcome == "not_relevant"
    assert verdict.rationale == (
        "Der erste Ressourcentyp AWS::CloudTrail::Trail liegt nicht im Prüfumfang.")
    assert verdict.cfn_resource_types == ["AWS::CloudTrail::Trail", "AWS::S3::Bucket"]


# --- Duties of the account, people or provider are not checkable at a template (issue #18) ----


def test_an_account_duty_in_scope_is_not_relevant_with_a_fixed_sentence() -> None:
    # CIS 4.4: the CloudTrail bucket would give a permanent WARN for every S3 bucket
    source = cis_source(req("4.4"))

    result, _ = curate_cis(source, {"4.4": can_test("AWS::S3::Bucket", level="account")})

    verdict = result.verdicts[0]
    assert verdict.outcome == "not_relevant"
    assert verdict.rationale == (
        "Die Pflicht liegt beim Konto oder der Organisation, nicht am Template.")
    assert verdict.cfn_resource_types == ["AWS::S3::Bucket"]
    assert result.selection.selected == []


def test_a_people_duty_is_not_relevant_even_for_a_resource_in_scope() -> None:
    # C5 OPS-16.01B: MFA for admins gave a false FAIL for every Lambda role
    source = ExtractedSource(
        source="C5", version="v", origin="o", requirements=[req("OPS-16.01B")])
    judge = Judge("architecture", fake_llm(
        {"OPS-16.01B": can_test("AWS::IAM::Role", level="people")}, []))

    result = curate(judge, [source], set(), SCOPE, NO_COMPONENTS)

    assert result.verdicts[0].outcome == "not_relevant"
    assert result.verdicts[0].rationale == (
        "Die Pflicht liegt bei Personen oder Prozessen, nicht am Template.")


def test_a_provider_duty_gets_its_own_sentence() -> None:
    answer = can_test("AWS::S3::Bucket", level="provider")

    result, _ = curate_cis(cis_source(req("1.1")), {"1.1": answer})

    assert result.verdicts[0].rationale == (
        "Die Pflicht liegt beim Cloud-Anbieter, nicht am Template.")


def test_not_testable_wins_over_the_level_of_the_duty() -> None:
    source = cis_source(req("1.2"))
    answer = {"testable": False, "rationale": "organisatorisch", "scope_level": "people",
              "cfn_resource_types": []}

    result, _ = curate_cis(source, {"1.2": answer})

    assert outcomes(result) == {"1.2": "not_testable"}


def test_the_spec_audit_ignores_the_level_of_the_duty() -> None:
    source = ExtractedSource(source="DSGVO", version="v", origin="o", requirements=[req("Art. 58")])
    judge = Judge("spec", fake_llm({"Art. 58": can_test(level="provider")}, []))

    result = curate(judge, [source], set(), NO_SCOPE, NO_COMPONENTS)

    assert [s.requirement_id for s in result.selection.selected] == ["Art. 58"]


def test_a_pinned_anchor_with_an_account_duty_aborts_the_build() -> None:
    with pytest.raises(ValueError, match="A 4.4"):
        curate_cis(cis_source(req("4.4")),
                   {"4.4": can_test("AWS::S3::Bucket", level="account")}, pinned={"A 4.4"})


def test_the_llm_rationale_stays_for_selected_and_not_testable_requirements() -> None:
    source = cis_source(req("3.1.4"), req("2.1.1"))
    answers = {"3.1.4": can_test("AWS::S3::Bucket"), "2.1.1": NOT_TESTABLE}

    result, _ = curate_cis(source, answers)

    assert [(v.rationale, v.cfn_resource_types) for v in result.verdicts] == [
        ("prüfbar", ["AWS::S3::Bucket"]), ("organisatorisch", [])]


def test_there_is_no_cap_every_testable_relevant_requirement_is_selected() -> None:
    ids_ = [f"3.1.{n}" for n in range(1, 31)]  # more than any former cap
    source = cis_source(*[req(i) for i in ids_])

    result, _ = curate_cis(source, {i: can_test("AWS::S3::Bucket") for i in ids_})

    assert [s.requirement_id for s in result.selection.selected] == ids_


def test_curate_spec_has_no_relevance_filter_and_no_resource_types() -> None:
    source = ExtractedSource(source="DSGVO", version="v", origin="o", requirements=[req("Art. 32")])
    judge = Judge("spec", fake_llm({"Art. 32": can_test("AWS::S3::Bucket")}, []))

    result = curate(judge, [source], set(), NO_SCOPE, NO_COMPONENTS)

    assert [(s.requirement_id, s.cfn_resource_types) for s in result.selection.selected] == [
        ("Art. 32", [])]


def test_curate_logs_progress_per_asked_requirement(caplog: pytest.LogCaptureFixture) -> None:
    source = cis_source(req("3.1.4"), req("3.1.5", prefilter=False), req("3.1.9"))
    answers = {"3.1.4": can_test("AWS::S3::Bucket"), "3.1.9": NOT_TESTABLE}

    with caplog.at_level("INFO", logger="kb_build"):
        curate_cis(source, answers)

    assert [r.getMessage() for r in caplog.records] == [
        "CIS 1/2 3.1.4 testable", "CIS 2/2 3.1.9 not testable"]


def test_one_unusable_answer_excludes_that_requirement_but_not_the_whole_run() -> None:
    # Run 3: the LLM invented AWS::SES::DomainDKIM twice and aborted the run at BSI 371/380
    source = cis_source(req("3.1.4"), req("3.9.9"))

    result, _ = curate_cis(source, {"3.1.4": can_test("AWS::S3::Bucket"), "3.9.9": INVENTED})

    assert outcomes(result) == {"3.1.4": "selected", "3.9.9": "llm_error"}
    assert [s.requirement_id for s in result.selection.selected] == ["3.1.4"]
    assert result.verdicts[1].rationale == (
        "Die Antwort des Modells blieb auch nach zwei Wiederholungen ungültig.")


# --- Gate: required anchors of the presets must be selected (ADR 0011) -------------------------


def test_a_pinned_anchor_that_is_selected_passes_the_gate() -> None:
    source = cis_source(req("3.1.4"))

    result, _ = curate_cis(source, {"3.1.4": can_test("AWS::S3::Bucket")}, pinned={"A 3.1.4"})

    assert outcomes(result) == {"3.1.4": "selected"}


@pytest.mark.parametrize("answer", [NOT_TESTABLE, can_test("AWS::CloudTrail::Trail"), INVENTED],
                         ids=["not testable", "not relevant", "llm error"])
def test_a_pinned_anchor_that_is_not_selected_aborts_the_build(answer: dict) -> None:
    with pytest.raises(ValueError, match="A 4.6"):
        curate_cis(cis_source(req("4.6")), {"4.6": answer}, pinned={"A 4.6"})


def test_a_pinned_anchor_dropped_by_the_prefilter_aborts_the_build() -> None:
    with pytest.raises(ValueError, match="A 4.6.*prefiltered"):
        curate_cis(cis_source(req("4.6", prefilter=False)), {}, pinned={"A 4.6"})


def test_a_pinned_anchor_missing_in_the_sources_aborts_the_build() -> None:
    with pytest.raises(ValueError, match="A 9.9"):
        curate_cis(cis_source(req("3.1.4")), {}, pinned={"A 9.9"})


def test_pinned_anchors_are_checked_before_anything_else_is_classified() -> None:
    bsi = ExtractedSource(
        source="BSI", version="v", origin="o", requirements=[req("DET.3.1"), req("BER.4.1")],
    )
    cis = cis_source(req("4.6"))
    asked: list[str] = []
    answers = {"DET.3.1": can_test("AWS::S3::Bucket"), "BER.4.1": can_test("AWS::IAM::Role"),
               "4.6": NOT_TESTABLE}
    judge = Judge("architecture", fake_llm(answers, asked))

    with pytest.raises(ValueError, match="A 4.6"):
        curate(judge, [bsi, cis], {"A BER.4.1", "A 4.6"}, SCOPE, NO_COMPONENTS)

    assert "DET.3.1" not in asked  # failed fast: the other requirements are never paid for


# --- Gate: every component of the archetypes has at least one rule (ADR 0011) ------------------


def curate_components(components: set[str], *answers: dict):
    ids_ = [f"3.1.{n}" for n in range(1, len(answers) + 1)]
    source = cis_source(*[req(i) for i in ids_])
    judge = Judge("architecture", fake_llm(dict(zip(ids_, answers)), []))
    return curate(judge, [source], set(), SCOPE, frozenset(components))


def test_the_build_passes_if_every_component_has_a_selected_requirement() -> None:
    curate_components({"AWS::S3::Bucket", "AWS::KMS::Key"},
                      can_test("AWS::S3::Bucket"), can_test("AWS::KMS::Key"))


def test_a_component_in_a_later_position_of_the_types_counts() -> None:
    curate_components({"AWS::KMS::Key"}, can_test("AWS::S3::Bucket", "AWS::KMS::Key"))


def test_the_build_aborts_and_names_every_component_without_a_requirement() -> None:
    with pytest.raises(ValueError, match="AWS::IAM::Role.*AWS::SQS::Queue"):
        curate_components({"AWS::S3::Bucket", "AWS::SQS::Queue", "AWS::IAM::Role"},
                          can_test("AWS::S3::Bucket"))


def test_a_requirement_that_was_not_selected_does_not_cover_its_component() -> None:
    with pytest.raises(ValueError, match="AWS::SQS::Queue"):
        curate_components({"AWS::SQS::Queue"},
                          can_test("AWS::CloudTrail::Trail", "AWS::SQS::Queue"))


def test_the_spec_audit_has_no_components_to_cover() -> None:
    source = ExtractedSource(source="DSGVO", version="v", origin="o", requirements=[req("Art. 32")])
    judge = Judge("spec", fake_llm({"Art. 32": can_test()}, []))

    curate(judge, [source], set(), NO_SCOPE, frozenset({"AWS::SQS::Queue"}))
