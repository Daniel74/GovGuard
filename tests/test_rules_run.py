"""formulate_all(): real selection lists and extracts, fake LLM that quotes the whole text."""

import shutil
from pathlib import Path

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from govguard.models import RuleCatalog
from kb_build.rules_run import formulate_all
from kb_build.selection_models import Selection
from kb_build.selection_run import BuildPaths

DATA = Path(__file__).parent.parent / "data"
KB = DATA / "knowledge_base"


def paths_in(tmp: Path) -> BuildPaths:
    out_dir = tmp / "knowledge_base"
    out_dir.mkdir()
    for name in ("selection_arch.json", "selection_spec.json"):
        shutil.copy(KB / name, out_dir / name)
    return BuildPaths(DATA, out_dir, tmp / "judgement_cache.json")


def quoting_model(quote: str | None = None) -> FunctionModel:
    """Quotes the whole requirement text from the prompt, or always `quote`; names the types."""

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        prompt = next(p for p in messages[0].parts if isinstance(p, UserPromptPart)).content
        text = prompt.split("<anforderung>\n")[1].split("\n</anforderung>")[0]
        types = prompt.partition("Ressourcentypen: ")[2].partition("\n")[0]
        answer = {"source_quote": quote or text, "title": "Titel", "compliant_if": f"{types} ok",
                  "violation_if": "Verstoß", "recommendation": "Abhilfe"}
        return ModelResponse(parts=[ToolCallPart("formulate_rule", answer)])

    return FunctionModel(respond, model_name="fake-model")


def selected_count(name: str) -> int:
    return len(Selection.model_validate_json((KB / name).read_text("utf-8")).selected)


def test_one_rule_per_selected_requirement_is_written_per_audit_type(tmp_path: Path) -> None:
    paths = paths_in(tmp_path)

    formulate_all(quoting_model(), paths)

    for rules, selection in [("rules_arch.json", "selection_arch.json"),
                             ("rules_spec.json", "selection_spec.json")]:
        catalog = RuleCatalog.model_validate_json((paths.out_dir / rules).read_text("utf-8"))
        assert len(catalog.rules) == selected_count(selection)


def test_an_unchanged_build_writes_identical_files_without_timestamp(tmp_path: Path) -> None:
    paths = paths_in(tmp_path)

    formulate_all(quoting_model(), paths, only="spec")
    first = (paths.out_dir / "rules_spec.json").read_bytes()
    formulate_all(quoting_model(), paths, only="spec")

    assert (paths.out_dir / "rules_spec.json").read_bytes() == first
    assert not (paths.out_dir / "rules_arch.json").exists()


def test_a_failed_rule_aborts_the_build_and_writes_no_file(tmp_path: Path) -> None:
    paths = paths_in(tmp_path)

    with pytest.raises(ValueError, match="no valid rule"):
        formulate_all(quoting_model(quote="erfundener Normtext"), paths, only="spec")

    assert not (paths.out_dir / "rules_spec.json").exists()
