"""Presets in data/input/presets/ (DESIGN 1.4, issue #3). The expected result comes from a human."""

import json
from pathlib import Path

import pytest

from govguard.models import Preset
from kb_build.paths import BuildPaths

PATHS = BuildPaths()
PRESETS = PATHS.presets
PRESET_DIRS = sorted(path for path in PRESETS.iterdir() if path.is_dir())
MAX_INPUT_CHARS = 100_000


def load(preset_dir: Path) -> Preset:
    return Preset.model_validate_json((preset_dir / "preset.json").read_text(encoding="utf-8"))


def test_six_presets_with_expected_result() -> None:
    assert [path.name for path in PRESET_DIRS if (path / "preset.json").is_file()] == [
        path.name for path in PRESET_DIRS
    ]
    assert len(PRESET_DIRS) == 6


def test_self_audit_preset_is_exactly_the_spec() -> None:  # dogfooding, issue #36
    preset_dir = PRESETS / "spec-govguard"
    preset = load(preset_dir)
    spec = Path("docs/SPEC.md").read_text(encoding="utf-8")

    assert (preset.audit_type, preset.input_file) == ("spec", "SPEC.md")
    assert (preset_dir / preset.input_file).read_text(encoding="utf-8") == spec


def test_self_audit_expects_only_anchors_of_the_catalog() -> None:  # issue #36
    catalog = json.loads((PATHS.knowledge_base / "rules_spec.json").read_text(encoding="utf-8"))
    anchors = {rule["primary_anchor"] for rule in catalog["rules"]}
    expected = load(PRESETS / "spec-govguard").expected

    assert expected.required_findings
    assert {finding.anchor for finding in expected.required_findings} <= anchors


def test_self_audit_expects_its_own_ai_act_classification() -> None:  # issue #52
    expected = load(PRESETS / "spec-govguard").expected

    assert any(finding.anchor.startswith("KI-VO ") for finding in expected.required_findings)


@pytest.mark.parametrize("preset_dir", PRESET_DIRS, ids=lambda path: path.name)
def test_input_is_small_enough(preset_dir: Path) -> None:
    inputs = [path for path in preset_dir.iterdir() if path.name != "preset.json"]
    assert len(inputs) == 1
    assert len(inputs[0].read_text(encoding="utf-8")) <= MAX_INPUT_CHARS


@pytest.mark.parametrize("preset_dir", PRESET_DIRS, ids=lambda path: path.name)
def test_preset_points_to_its_input(preset_dir: Path) -> None:
    assert (preset_dir / load(preset_dir).input_file).is_file()


def resources(preset_id: str) -> dict[str, dict]:
    template = json.loads((PRESETS / preset_id / "template.json").read_text(encoding="utf-8"))
    return template["Resources"]


def test_foreign_preset_shares_no_component_with_the_archetypes() -> None:  # ADR 0011, issue #15
    profiles = json.loads((PATHS.archetype_profiles).read_text(encoding="utf-8"))
    components = {t for profile in profiles for t in profile["required_types"]}
    types = {resource["Type"] for resource in resources("arch-fristenwecker").values()}
    assert not types & components
    assert "AWS::KMS::Key" not in types


def test_foreign_preset_carries_its_required_findings_as_properties() -> None:
    template = resources("arch-fristenwecker")
    topic, state_machine = template["FristTopic"], template["Fristenwecker"]
    assert "KmsMasterKeyId" not in topic["Properties"]  # FSBP SNS.1 = FAIL
    assert state_machine["Properties"]["LoggingConfiguration"]["Level"] == "ALL"  # StepFunctions.1
