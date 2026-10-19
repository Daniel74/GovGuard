"""decompose_all(): extracted acts in, decomposed acts, protocol and cache out (#53)."""

import json
import re
from pathlib import Path

from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from test_decompose_parts import ART_6

from kb_build.decompose.run import decompose_all
from kb_build.extract.models import ExtractedSource
from kb_build.paths import BuildPaths


def every_mark_its_own_duty(calls: list[int]) -> FunctionModel:
    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        calls.append(1)
        prompt = next(p for p in messages[-1].parts if isinstance(p, UserPromptPart)).content
        marks = re.findall(r"^\[(.+?)\]", prompt, flags=re.MULTILINE)
        answer = {"groups": [{"marks": marks, "kind": "alle_gelten", "rationale": "Alle."}]}
        return ModelResponse(parts=[ToolCallPart("decompose_article", answer)])

    return FunctionModel(respond, model_name="fake-model")


def paths_in(tmp: Path) -> BuildPaths:
    paths = BuildPaths(Path("data/input"), tmp / "intermediate", tmp / "knowledge_base")
    paths.extracted.mkdir(parents=True)
    for name in ("DSGVO", "KI-VO"):
        act = ExtractedSource(source=name, version="v", origin="o", requirements=[ART_6])
        (paths.extracted / f"{name.lower()}.json").write_text(act.model_dump_json())
    return paths


def test_both_acts_are_decomposed_and_the_second_run_is_free(tmp_path: Path) -> None:
    paths, calls = paths_in(tmp_path), []
    decompose_all(every_mark_its_own_duty(calls), paths)
    decompose_all(every_mark_its_own_duty(calls), paths)

    assert len(calls) == 2  # one article per act, then the cache
    ki_vo = ExtractedSource.model_validate_json(paths.source_file("KI-VO").read_text())
    assert [r.primary_anchor for r in ki_vo.requirements][-1] == "KI-VO Art. 6 Abs. 2"
    protocol = json.loads(paths.out_file("decompositions", "spec").read_text())
    assert [(e["source"], e["outcome"]) for e in protocol] == [
        ("DSGVO", "decomposed"), ("KI-VO", "decomposed")]


def test_the_checked_in_paths() -> None:
    paths = BuildPaths()
    assert paths.source_file("DSGVO") == Path("data/intermediate/decomposed/dsgvo.json")
    assert paths.source_file("SDM") == Path("data/intermediate/extracted/sdm.json")
    assert paths.out_file("decompositions", "spec") == Path(
        "data/intermediate/decompositions_spec.json")
