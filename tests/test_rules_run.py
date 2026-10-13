"""formulate_all(): real selection lists and extracts, fake LLM that quotes the whole text."""

import shutil
from pathlib import Path

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from govguard.models import AuditType, RuleCatalog
from kb_build.paths import BuildPaths
from kb_build.reference.run import read_scope
from kb_build.rules.run import formulate_all, read_property_index
from kb_build.select.models import Selection

REAL = BuildPaths()


def paths_in(tmp: Path) -> BuildPaths:
    """Real input, extracts and selection lists; everything written goes to `tmp`."""
    paths = BuildPaths(REAL.input, tmp / "intermediate", tmp / "knowledge_base")
    shutil.copytree(REAL.extracted, paths.extracted)
    for audit_type in ("architecture", "spec"):
        shutil.copy(REAL.out_file("selection", audit_type), paths.out_file("selection", audit_type))
    _keep_scope_types(paths)
    return paths


def _keep_scope_types(paths: BuildPaths) -> None:
    """The checked-in list may predate the scope (#19); rules may name scope types only."""
    scope_types = read_scope(paths.scope).types
    file = paths.out_file("selection", "architecture")
    selection = Selection.model_validate_json(file.read_text("utf-8"))
    for selected in selection.selected:
        selected.cfn_resource_types = [t for t in selected.cfn_resource_types if t in scope_types]
    selection.selected = [s for s in selection.selected if s.cfn_resource_types]
    file.write_text(selection.model_dump_json(), encoding="utf-8")


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


def selected_count(paths: BuildPaths, audit_type: AuditType) -> int:
    raw = paths.out_file("selection", audit_type).read_text("utf-8")
    return len(Selection.model_validate_json(raw).selected)


def test_one_rule_per_selected_requirement_is_written_per_audit_type(tmp_path: Path) -> None:
    paths = paths_in(tmp_path)

    formulate_all(quoting_model(), paths)

    for audit_type in ("architecture", "spec"):
        raw = paths.out_file("rules", audit_type).read_text("utf-8")
        assert len(RuleCatalog.model_validate_json(raw).rules) == selected_count(paths, audit_type)


def test_an_unchanged_build_writes_identical_files_without_timestamp(tmp_path: Path) -> None:
    paths = paths_in(tmp_path)

    formulate_all(quoting_model(), paths, only="spec")
    first = (paths.knowledge_base / "rules_spec.json").read_bytes()
    formulate_all(quoting_model(), paths, only="spec")

    assert (paths.knowledge_base / "rules_spec.json").read_bytes() == first
    assert not (paths.knowledge_base / "rules_arch.json").exists()


def test_a_failed_rule_aborts_the_build_and_writes_no_file(tmp_path: Path) -> None:
    paths = paths_in(tmp_path)

    with pytest.raises(ValueError, match="no valid rule"):
        formulate_all(quoting_model(quote="erfundener Normtext"), paths, only="spec")

    assert not (paths.knowledge_base / "rules_spec.json").exists()


def test_the_property_index_holds_nested_paths_and_names_of_all_resource_types() -> None:
    index = read_property_index(REAL)

    assert "LoggingConfiguration.LogFilePrefix" in index.paths["AWS::S3::Bucket"]
    assert "BucketPolicy" in index.resource_names  # AWS::S3::BucketPolicy, a resource itself
