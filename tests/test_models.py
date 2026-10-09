import pytest
from pydantic import ValidationError

from govguard.models import Preset, RequiredFinding, RuleCatalog


def test_rule_catalog_needs_at_least_one_rule() -> None:
    with pytest.raises(ValidationError):  # no rules would mean no overall status
        RuleCatalog(audit_type="spec", source_versions={}, model_id="fake-model", rules=[])


def make_preset(audit_type: str, overall_status: str, archetype: str | None) -> Preset:
    return Preset(
        title="Fiktives Preset",
        audit_type=audit_type,
        input_file="input.md",
        expected={
            "overall_status": overall_status, "required_findings": [], "archetype": archetype
        },
    )


def test_required_finding_is_never_warn() -> None:
    with pytest.raises(ValidationError):  # WARN is judgement, the preset gate would flicker
        RequiredFinding(anchor="DSGVO Art. 9", status="WARN")


@pytest.mark.parametrize(
    ("audit_type", "overall_status"), [("spec", "FAIL"), ("architecture", "WARN")]
)
def test_archetype_only_for_spec_without_fail(audit_type: str, overall_status: str) -> None:
    with pytest.raises(ValidationError):
        make_preset(audit_type, overall_status, "ARCH-02")


def test_spec_without_fail_may_expect_archetype() -> None:
    assert make_preset("spec", "WARN", "ARCH-02").expected.archetype == "ARCH-02"
