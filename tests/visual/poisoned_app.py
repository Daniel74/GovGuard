"""Test app of tests/visual, never part of the demo: the spec gallery report with LLM text that
carries a link, an image and a tag in every title and anchor (#45).

The gallery holds no such report, and src/ has no test hook: the poisoned_url fixture starts this.
"""

from govguard_ui.gallery import load_gallery
from govguard_ui.paths import GALLERY, PRESETS
from govguard_ui.report.report_view import render_report

POISON = '<a href="https://evil.example">link</a> <img src="x.png"> <b>tag</b>'
SPEC = "spec-meldeportal-gesundheit"


def main() -> None:
    entry = next(e for e in load_gallery(PRESETS, GALLERY) if e.preset_id == SPEC)
    findings = [f.model_copy(update={"title": f"{POISON} {f.title}",
                                     "primary_anchor": f"{POISON} {f.primary_anchor}"})
                for f in entry.report.findings]
    report = entry.report.model_copy(update={"findings": findings})
    render_report(report, entry.preset.title, (entry.source_name, entry.source_text), None,
                  key="poisoned")


if __name__ == "__main__":  # Streamlit runs a script as __main__; the test imports POISON only
    main()
