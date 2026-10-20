from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from pydantic_ai.models.function import FunctionModel

from govguard.adapters.groq_services import groq_model
from govguard.models import (
    AuditEvent,
    AuditReport,
    Expected,
    Preset,
    Progress,
    RequiredFinding,
    RuleCatalog,
    Trace,
    provider_of,
)


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


def test_audit_event_counts_corrections_but_carries_no_text() -> None:
    event = AuditEvent(
        timestamp=datetime(2026, 10, 15, tzinfo=UTC), endpoint="/audit/spec", outcome="ok",
        trace=Trace(audit_id="a-1", input_sha256="abc", catalog_sha256="def", kb_commit="x"),
        model_id="m", overall_status="WARN", statuses={"SPEC-DSGVO-Art.9": "WARN"},
        archetype=None, retries=1, downgrades=2,
    )

    logged = event.model_dump()
    assert (logged["retries"], logged["downgrades"]) == (1, 2)
    # No input text, no evidence, no reasons (ADR 0006, DSGVO Art. 5(1)(c))
    assert not {"evidence", "input_text", "corrections", "rationale"} & logged.keys()


def test_provider_of_tells_groq_from_bedrock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test")

    assert provider_of(groq_model()) == "groq"
    assert provider_of(FunctionModel(lambda *_: None)) == "bedrock"  # test models like Bedrock


def test_old_gallery_reports_without_conditions_still_load() -> None:
    gallery = sorted(Path("data/gallery").glob("*.json"))
    assert gallery
    for file in gallery:
        report = AuditReport.model_validate_json(file.read_text(encoding="utf-8"))
        assert report.conditions == {}


def test_a_preset_may_expect_a_value_per_condition() -> None:
    expected = Expected(overall_status="WARN", required_findings=[],
                        conditions={"consent": "unstated", "processor": "yes"})
    assert expected.conditions["processor"] == "yes"
    assert Expected(overall_status="WARN", required_findings=[]).conditions == {}
    with pytest.raises(ValidationError):
        Expected(overall_status="WARN", required_findings=[], conditions={"consent": "maybe"})


def test_progress_has_a_conditions_phase() -> None:
    assert Progress(phase="conditions").packages_total == 0
