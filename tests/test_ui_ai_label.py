"""The marker "KI" next to Begründung and Empfehlung, in every view of a finding (#83)."""

import json

from ui_helpers import arch_page, gallery_entry, report_page, spec_page

from govguard_ui.gallery import GalleryEntry
from govguard_ui.report.ai_label import ai_label, ai_texts, marker
from govguard_ui.report.findings_view import BY_RULE


def html_bodies(app) -> list[str]:
    return [node.proto.body for node in app.get("html")]


def test_the_detail_marks_rationale_and_recommendation_as_written_by_the_model() -> None:
    bodies = html_bodies(arch_page(view=BY_RULE))

    assert ai_label("Begründung") in bodies
    assert ai_label("Empfehlung") in bodies


def test_the_findings_over_several_sections_carry_the_marker_in_their_blocks() -> None:
    app = spec_page(view=None)

    blocks = [b for b in html_bodies(app) if "Begründung" in b]
    assert blocks and all(f"<strong>Begründung</strong> {marker()}" in b for b in blocks)
    assert all(f"<strong>Empfehlung</strong> {marker()}" in b
               for b in blocks if "Empfehlung" in b)


def test_the_codes_own_texts_stay_without_the_marker() -> None:
    """Badge, anchor and lines, corrections and the meta table are written by the code: apart
    from the two labels of model text, no marker stands anywhere on the page."""
    for app in (spec_page(view=None), arch_page(view=BY_RULE)):
        bodies = html_bodies(app)
        assert any("gg-meta" in b for b in bodies) and any("Verstoß belegt" in b for b in bodies)
        for body in bodies:
            rest = body.replace(ai_label("Begründung"), "").replace(ai_label("Empfehlung"), "")
            assert marker() not in rest


def test_the_site_component_gets_its_marker_from_the_same_source() -> None:
    app = spec_page(view=None)

    [document] = [json.loads(n.proto.json) for n in app.get("bidi_component")
                  if "sites" in json.loads(n.proto.json)]
    assert document["ai"] == ai_texts()


def written_by_code(preset_id: str, by_code: list[str]) -> GalleryEntry:
    """The stored report as if the code had written these texts of every finding."""
    entry = gallery_entry(preset_id)
    findings = [f.model_copy(update={"by_code": by_code}) for f in entry.report.findings]
    return entry.model_copy(update={"report": entry.report.model_copy(
        update={"findings": findings})})


def test_texts_the_code_wrote_get_no_marker_in_the_detail_and_the_groups() -> None:
    entry = written_by_code("spec-meldeportal-gesundheit", ["rationale", "recommendation"])

    for view in (BY_RULE, None):
        bodies = html_bodies(report_page(entry, view=view))
        assert [b for b in bodies if marker() in b] == []
        assert any("Begründung" in b for b in bodies)  # the labels stay, only the marker goes


def test_only_the_named_text_loses_its_marker() -> None:
    entry = written_by_code("spec-meldeportal-gesundheit", ["recommendation"])

    bodies = html_bodies(report_page(entry, view=None))

    assert any(ai_label("Begründung") in b for b in bodies)
    assert all(ai_label("Empfehlung") not in b for b in bodies)
    assert any(ai_label("Empfehlung", by_code=True) in b for b in bodies)


def test_the_site_component_learns_per_finding_which_texts_the_code_wrote() -> None:
    entry = written_by_code("spec-meldeportal-gesundheit", ["rationale"])

    app = report_page(entry, view=None)

    [document] = [json.loads(n.proto.json) for n in app.get("bidi_component")
                  if "sites" in json.loads(n.proto.json)]
    shown = [f for s in document["sites"] for f in s["findings"]]
    assert shown and {tuple(f["by_code"]) for f in shown} == {("rationale",)}
