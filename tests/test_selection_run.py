"""select_all(): real extracted data and presets, fake LLM that finds everything testable."""

import itertools
import re
import shutil
from pathlib import Path

import pytest
from conftest import retry_lines
from pydantic import TypeAdapter
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    RetryPromptPart,
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from kb_build.paths import BuildPaths
from kb_build.select.models import Selection, Verdict
from kb_build.select.run import chosen, select_all

REAL = BuildPaths()
ARCHITECTURE_SOURCES = ("BSI", "CIS", "FSBP", "C5")
COMPONENTS = [  # the fake LLM names the archetype components in turn, so the coverage gate passes
    "AWS::ApiGateway::RestApi", "AWS::Lambda::Function", "AWS::DynamoDB::Table",
    "AWS::SQS::Queue", "AWS::S3::Bucket", "AWS::KinesisFirehose::DeliveryStream",
]


def paths_in(tmp: Path) -> BuildPaths:
    """Real input and extracts, everything written goes to `tmp`."""
    paths = BuildPaths(REAL.input, tmp / "intermediate", tmp / "knowledge_base")
    if not paths.extracted.exists():
        shutil.copytree(REAL.extracted, paths.extracted)
    return paths


def fake_model(calls: list[int] | None = None) -> FunctionModel:
    turn = itertools.count()

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        if calls is not None:
            calls.append(1)
        prompt = next(p for p in messages[-1].parts if isinstance(p, UserPromptPart)).content
        is_architecture = prompt.startswith(tuple(f"Quelle: {s}" for s in ARCHITECTURE_SOURCES))
        types = [COMPONENTS[next(turn) % len(COMPONENTS)]] if is_architecture else []
        answer = {"testable": True, "rationale": "prüfbar", "cfn_resource_types": types}
        return ModelResponse(parts=[ToolCallPart("classify_requirement", answer)])

    return FunctionModel(respond, model_name="fake-model")


@pytest.fixture(scope="module")
def written(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if not all((REAL.extracted / f"{s.lower()}.json").exists() for s in ARCHITECTURE_SOURCES):
        pytest.skip("cis, fsbp and c5 are not extracted on this machine")  # local only (ADR 0008)
    paths = paths_in(tmp_path_factory.mktemp("build"))
    select_all(fake_model(), paths)
    return paths.intermediate


def load(out: Path, name: str) -> Selection:
    return Selection.model_validate_json((out / name).read_text(encoding="utf-8"))


def verdicts(out: Path, name: str) -> list[Verdict]:
    return TypeAdapter(list[Verdict]).validate_json((out / name).read_text(encoding="utf-8"))


def test_the_architecture_verdicts_cover_every_requirement_of_all_four_sources(written) -> None:
    covered = {s: sum(v.source == s for v in verdicts(written, "verdicts_arch.json"))
               for s in ARCHITECTURE_SOURCES}

    assert covered == {"BSI": 1000, "CIS": 70, "FSBP": 286, "C5": 610}


def test_the_spec_verdicts_cover_every_requirement_of_dsgvo_and_sdm(written) -> None:
    covered = {s: sum(v.source == s for v in verdicts(written, "verdicts_spec.json"))
               for s in ("DSGVO", "SDM")}

    assert covered == {"DSGVO": 99, "SDM": 147}


def test_the_selection_is_exactly_the_selected_verdicts(written) -> None:
    for kind, name in (("arch", "architecture"), ("spec", "spec")):
        selection = load(written, f"selection_{kind}.json")
        kept = {(v.source, v.requirement_id) for v in verdicts(written, f"verdicts_{kind}.json")
                if v.outcome == "selected"}
        assert selection.audit_type == name
        assert {(e.source, e.requirement_id) for e in selection.selected} == kept


def test_the_selection_has_no_cap_and_keeps_the_pinned_anchors(written) -> None:
    arch = {(e.source, e.requirement_id) for e in load(written, "selection_arch.json").selected}
    spec = {(e.source, e.requirement_id) for e in load(written, "selection_spec.json").selected}

    assert {("CIS", "3.1.4"), ("CIS", "4.6"), ("BSI", "BER.4.1")} <= arch
    assert {("DSGVO", "Art. 9"), ("SDM", "M60.P01")} <= spec
    assert len(arch) > 50 and len(spec) > 12  # the former caps were 12 per source and 16 + 8


def test_only_the_requested_audit_type_is_selected(tmp_path: Path) -> None:
    select_all(fake_model(), paths_in(tmp_path), only="spec")

    paths = paths_in(tmp_path)
    written = sorted(p.name for p in paths.intermediate.iterdir() if p.is_file())
    assert written == ["judgement_cache.json", "selection_spec.json", "verdicts_spec.json"]
    assert not paths.knowledge_base.exists()  # nothing of the selection is deployed


def test_a_second_run_with_the_same_cache_asks_the_llm_nothing(tmp_path: Path) -> None:
    calls: list[int] = []
    select_all(fake_model(calls), paths_in(tmp_path), only="spec")
    first = len(calls)

    select_all(fake_model(calls), paths_in(tmp_path), only="spec")

    assert first > 0
    assert len(calls) == first


def test_only_missing_keeps_the_old_selection_and_judges_only_the_new_source(
    tmp_path: Path,
) -> None:
    # ADR 0025: the checked-in selection stays a byte-identical prefix, KI-VO is appended
    paths = paths_in(tmp_path)
    real = load(REAL.intermediate, "selection_spec.json")
    frozen = [e for e in real.selected if e.source != "KI-VO"]  # the state before #52
    old = [v for v in verdicts(REAL.intermediate, "verdicts_spec.json") if v.source != "KI-VO"]
    paths.out_file("selection", "spec").write_text(
        real.model_copy(update={"selected": frozen}).model_dump_json(), "utf-8")
    paths.out_file("verdicts", "spec").write_bytes(TypeAdapter(list[Verdict]).dump_json(old))
    calls: list[int] = []

    select_all(fake_model(calls), paths, only="spec", only_missing=True)

    new = load(paths.intermediate, "selection_spec.json")
    assert new.selected[:len(frozen)] == frozen
    assert {e.source for e in new.selected[len(frozen):]} == {"KI-VO"}
    assert len(calls) == 8  # Art. 4, 5, 6, 13, 14, 26, 27, 50
    assert {v.source for v in verdicts(paths.intermediate, "verdicts_spec.json")} == {
        "DSGVO", "SDM", "KI-VO"}


def test_only_missing_is_not_built_for_the_architecture_audit(tmp_path: Path) -> None:
    # the coverage gate needs the whole selection; architecture keeps the full run
    with pytest.raises(ValueError, match="only for the spec audit"):
        select_all(fake_model(), paths_in(tmp_path), only="architecture", only_missing=True)


def test_the_paid_answers_are_saved_even_if_a_gate_aborts_the_build(tmp_path: Path) -> None:
    def only_s3(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        answer = {"testable": True, "rationale": "x", "cfn_resource_types": ["AWS::S3::Bucket"]}
        return ModelResponse(parts=[ToolCallPart("classify_requirement", answer)])

    with pytest.raises(ValueError, match="components without a selected requirement"):
        select_all(FunctionModel(only_s3, model_name="fake-model"), paths_in(tmp_path),
                   only="architecture")

    assert paths_in(tmp_path).judgement_cache.exists()
    assert not paths_in(tmp_path).out_file("selection", "architecture").exists()


def test_the_run_logs_the_tokens_per_audit_type(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level("INFO", logger="kb_build"):
        select_all(fake_model(), paths_in(tmp_path), only="spec")

    usage = [r.getMessage() for r in caplog.records if "tokens" in r.getMessage()]
    assert len(usage) == 1
    assert re.fullmatch(r"spec: [1-9]\d* requests, [1-9]\d* input tokens, \d+ output tokens",
                        usage[0])


def test_only_the_rules_go_to_the_knowledge_base_the_rest_stays_intermediate() -> None:
    paths = BuildPaths(intermediate=Path("tmp"), knowledge_base=Path("kb"))

    assert paths.out_file("selection", "architecture") == Path("tmp/selection_arch.json")
    assert paths.out_file("verdicts", "spec") == Path("tmp/verdicts_spec.json")
    assert paths.out_file("rules", "architecture") == Path("kb/rules_arch.json")


def test_the_default_paths_follow_the_data_layout() -> None:
    paths = BuildPaths()

    assert paths.sources_json == Path("data/input/sources.json")
    assert paths.presets == Path("data/input/presets")
    assert paths.extracted == Path("data/intermediate/extracted")
    assert paths.judgement_cache == Path("data/intermediate/judgement_cache.json")
    assert paths.out_file("rules", "spec") == Path("data/knowledge_base/rules_spec.json")


def test_the_build_log_has_one_file_per_command_and_audit_type() -> None:
    # checked in next to the result it explains (#29); git keeps the older runs
    paths = BuildPaths()

    assert paths.build_log("rules", "spec") == Path("data/intermediate/logs/rules_spec.log")
    assert paths.build_log("select", None) == Path("data/intermediate/logs/select.log")


def test_only_narrows_the_audit_types() -> None:
    assert chosen(None) == ["architecture", "spec"]
    assert chosen("spec") == ["spec"]


def test_the_run_reports_retries_and_llm_errors_of_the_classify_gate(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level("INFO", logger="kb_build"):
        select_all(fake_model(), paths_in(tmp_path), only="spec")

    assert "spec quality classify: retries=0 llm_error=0" in [
        r.getMessage() for r in caplog.records]


def test_the_build_log_names_every_retry_of_a_paid_answer_and_none_of_a_cached_one(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    def forgetful(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        redo = any(isinstance(p, RetryPromptPart) for p in messages[-1].parts)
        answer = {"testable": True, "cfn_resource_types": []}
        return ModelResponse(parts=[ToolCallPart(
            "classify_requirement", answer | ({"rationale": "prüfbar"} if redo else {}))])

    with caplog.at_level("INFO", logger="kb_build"):
        select_all(FunctionModel(forgetful, model_name="fake-model"), paths_in(tmp_path),
                   only="spec")
        paid = retry_lines(caplog)
        paid_quality = next(
            r.getMessage() for r in caplog.records if "quality classify" in r.getMessage())
        caplog.clear()
        select_all(FunctionModel(forgetful, model_name="fake-model"), paths_in(tmp_path),
                   only="spec")

    assert len(paid) > 0
    assert paid_quality == f"spec quality classify: retries={len(paid)} llm_error=0"
    assert "spec DSGVO Art. 9 retry 1 (schema): rationale: Field required" in paid
    assert retry_lines(caplog) == []


def test_the_build_log_names_what_the_validator_sent_back(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    rotating = fake_model().function

    def invents_once(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        prompt = next(p for p in messages[0].parts if isinstance(p, UserPromptPart)).content
        if not prompt.startswith("Quelle: CIS\nID: 3.1.4\n"):
            return rotating(messages, info)
        redo = any(isinstance(p, RetryPromptPart) for p in messages[-1].parts)
        types = ["AWS::S3::Bucket"] if redo else ["S3 bucket"]
        return ModelResponse(parts=[ToolCallPart("classify_requirement", {
            "testable": True, "rationale": "prüfbar", "cfn_resource_types": types})])

    with caplog.at_level("INFO", logger="kb_build"):
        select_all(FunctionModel(invents_once, model_name="fake-model"), paths_in(tmp_path),
                   only="architecture")

    assert retry_lines(caplog) == [  # the text the model reads (CONTEXT.md: Korrektur)
        "architecture CIS 3.1.4 retry 1 (code): Eine prüfbare Architektur-Anforderung braucht "
        "mindestens einen echten CloudFormation-Typ (Format AWS::Dienst::Ressource). "
        "Diese gibt es nicht: ['S3 bucket']"]


def test_the_build_log_names_why_the_last_answer_was_rejected(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    def never_explains_art_5(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        prompt = next(p for p in messages[0].parts if isinstance(p, UserPromptPart)).content
        answer = {"testable": True, "cfn_resource_types": []}
        if not prompt.startswith("Quelle: DSGVO\nID: Art. 5\n"):
            answer["rationale"] = "prüfbar"
        return ModelResponse(parts=[ToolCallPart("classify_requirement", answer)])

    with caplog.at_level("INFO", logger="kb_build"):
        select_all(FunctionModel(never_explains_art_5, model_name="fake-model"),
                   paths_in(tmp_path), only="spec")

    assert [r.getMessage() for r in caplog.records
            if r.getMessage().startswith("spec DSGVO Art. 5 ")] == [
        "spec DSGVO Art. 5 retry 1 (schema): rationale: Field required",
        "spec DSGVO Art. 5 retry 2 (schema): rationale: Field required",
        "spec DSGVO Art. 5 rejected (schema): rationale: Field required"]  # then llm_error
