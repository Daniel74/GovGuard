"""select_all(): real extracted data and presets, fake LLM that finds everything testable."""

from pathlib import Path

import pytest
from pydantic import TypeAdapter
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from kb_build.selection_models import Selection, Verdict
from kb_build.selection_run import select_all

DATA = Path(__file__).parent.parent / "data"


def everything_testable(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    prompt = next(p for p in messages[-1].parts if isinstance(p, UserPromptPart)).content
    is_architecture = prompt.startswith(("Quelle: BSI", "Quelle: CIS"))
    types = ["AWS::S3::Bucket"] if is_architecture else []
    answer = {"testable": True, "rationale": "prüfbar", "cfn_resource_types": types}
    return ModelResponse(parts=[ToolCallPart("classify_requirement", answer)])


@pytest.fixture(scope="module")
def written(tmp_path_factory: pytest.TempPathFactory) -> Path:
    if not (DATA / "extracted" / "cis.json").exists():  # stays local (ADR 0008)
        pytest.skip("cis.json not extracted on this machine")
    out = tmp_path_factory.mktemp("knowledge_base")
    select_all(FunctionModel(everything_testable, model_name="fake-model"), DATA, out)
    return out


def load(out: Path, name: str) -> Selection:
    return Selection.model_validate_json((out / name).read_text(encoding="utf-8"))


def test_architecture_selection_has_at_most_12_per_source_and_all_pinned_anchors(written) -> None:
    selection = load(written, "selection_arch.json")

    per_source = {s: [e for e in selection.selected if e.source == s] for s in ("BSI", "CIS")}
    assert {s: len(entries) for s, entries in per_source.items()} == {"BSI": 12, "CIS": 12}
    pinned = {(e.source, e.requirement_id) for e in selection.selected if e.pinned}
    assert pinned == {("CIS", "3.1.4"), ("CIS", "4.6"), ("BSI", "BER.4.1")}


def test_spec_selection_respects_the_caps_and_pins_art_9_and_m60_p01(written) -> None:
    selection = load(written, "selection_spec.json")

    counts = {s: sum(e.source == s for e in selection.selected) for s in ("DSGVO", "SDM")}
    assert counts == {"DSGVO": 16, "SDM": 8}  # SPEC: Art. 32 must fit
    pinned = {(e.source, e.requirement_id) for e in selection.selected if e.pinned}
    assert pinned == {("DSGVO", "Art. 9"), ("SDM", "M60.P01")}
    assert all(e.cfn_resource_types == [] for e in selection.selected)


def test_only_the_requested_audit_type_is_selected(tmp_path: Path) -> None:
    select_all(FunctionModel(everything_testable, model_name="fake-model"), DATA, tmp_path,
               only="spec")

    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "selection_spec.json", "verdicts_spec.json"]


def test_a_verdict_report_is_written_next_to_each_selection(tmp_path: Path) -> None:
    select_all(FunctionModel(everything_testable, model_name="fake-model"), DATA, tmp_path,
               only="spec")

    verdicts = TypeAdapter(list[Verdict]).validate_json(
        (tmp_path / "verdicts_spec.json").read_text(encoding="utf-8"))
    selection = Selection.model_validate_json(
        (tmp_path / "selection_spec.json").read_text(encoding="utf-8"))
    kept = {(v.source, v.requirement_id) for v in verdicts if v.outcome in ("selected", "pinned")}
    assert kept == {(e.source, e.requirement_id) for e in selection.selected}
    assert any(v.outcome == "over_cap" for v in verdicts)  # 46 DSGVO candidates, cap 12
