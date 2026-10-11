"""select_all(): real extracted data and presets, fake LLM that finds everything testable."""

import itertools
import re
from pathlib import Path

import pytest
from pydantic import TypeAdapter
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from kb_build.selection_models import Selection, Verdict
from kb_build.selection_run import BuildPaths, select_all

DATA = Path(__file__).parent.parent / "data"
ARCHITECTURE_SOURCES = ("BSI", "CIS", "FSBP", "C5")
COMPONENTS = [  # the fake LLM names the archetype components in turn, so the coverage gate passes
    "AWS::ApiGateway::RestApi", "AWS::Lambda::Function", "AWS::DynamoDB::Table",
    "AWS::SQS::Queue", "AWS::S3::Bucket", "AWS::KinesisFirehose::DeliveryStream",
]


def paths_in(tmp: Path) -> BuildPaths:
    return BuildPaths(DATA, tmp / "knowledge_base", tmp / "judgement_cache.json")


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
    if not all((DATA / "extracted" / f"{s.lower()}.json").exists() for s in ARCHITECTURE_SOURCES):
        pytest.skip("cis, fsbp and c5 are not extracted on this machine")  # local only (ADR 0008)
    paths = paths_in(tmp_path_factory.mktemp("build"))
    select_all(fake_model(), paths)
    return paths.out_dir


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

    assert sorted(p.name for p in (tmp_path / "knowledge_base").iterdir()) == [
        "selection_spec.json", "verdicts_spec.json"]  # the cache is no part of the deployment
    assert (tmp_path / "judgement_cache.json").exists()


def test_a_second_run_with_the_same_cache_asks_the_llm_nothing(tmp_path: Path) -> None:
    calls: list[int] = []
    select_all(fake_model(calls), paths_in(tmp_path), only="spec")
    first = len(calls)

    select_all(fake_model(calls), paths_in(tmp_path), only="spec")

    assert first > 0
    assert len(calls) == first


def test_the_paid_answers_are_saved_even_if_a_gate_aborts_the_build(tmp_path: Path) -> None:
    def only_s3(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        answer = {"testable": True, "rationale": "x", "cfn_resource_types": ["AWS::S3::Bucket"]}
        return ModelResponse(parts=[ToolCallPart("classify_requirement", answer)])

    with pytest.raises(ValueError, match="components without a selected requirement"):
        select_all(FunctionModel(only_s3, model_name="fake-model"), paths_in(tmp_path),
                   only="architecture")

    assert (tmp_path / "judgement_cache.json").exists()
    assert not (tmp_path / "knowledge_base" / "selection_arch.json").exists()


def test_the_run_logs_the_tokens_per_audit_type(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level("INFO", logger="kb_build"):
        select_all(fake_model(), paths_in(tmp_path), only="spec")

    usage = [r.getMessage() for r in caplog.records if "tokens" in r.getMessage()]
    assert len(usage) == 1
    assert re.fullmatch(r"spec: [1-9]\d* requests, [1-9]\d* input tokens, \d+ output tokens",
                        usage[0])
