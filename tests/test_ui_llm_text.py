"""LLM text stays text on the whole page "Audits ansehen": a poisoned report (#43).

Titles, anchors and reasons come from the LLM. Markdown renders links and images, HTML renders
tags; the test looks at every text of the page, so a forgotten spot fails too. The finding
table is an own component: tests/visual/test_browser_findings.py checks its cells (#45).
"""

import pytest
from streamlit.testing.v1 import AppTest
from ui_helpers import gallery_entry, report_page

from govguard.models import CrossReference, Finding

LINK, IMAGE, TAG = "[evil](https://evil.example)", "![evil](x.png)", "<b>evil</b>"
POISON = f"{LINK} {IMAGE} {TAG}"


def poisoned(finding: Finding) -> Finding:
    """The link stands first in the anchor: the gap list groups by its first word."""
    return finding.model_copy(update={
        "title": POISON, "primary_anchor": f"{LINK} {finding.primary_anchor}",
        "rationale": POISON, "recommendation": POISON, "corrections": [POISON],
        "cross_references": [CrossReference(anchor=POISON, origin="ai_suggested")]})


def poisoned_page(preset_id: str) -> AppTest:
    entry = gallery_entry(preset_id)
    report = entry.report.model_copy(update={"findings": [poisoned(f) for f in
                                                          entry.report.findings]})
    return report_page(entry.model_copy(update={"report": report}))


def markdown_texts(app: AppTest) -> list[str]:
    """Every text Streamlit renders as Markdown: elements and widget labels."""
    parts = [*app.markdown, *app.caption, *app.title, *app.header, *app.subheader, *app.info]
    return ([str(part.value) for part in parts] + [b.label for b in app.button]
            + [e.label for e in app.expander])


@pytest.mark.parametrize("preset_id", ["spec-meldeportal-gesundheit", "arch-fristenwecker"])
def test_llm_text_becomes_neither_link_nor_image_nor_tag_anywhere(preset_id: str) -> None:
    app = poisoned_page(preset_id)
    texts = markdown_texts(app)

    assert any(r"\[evil\]" in text for text in texts)  # the poison reached the page
    assert [text for text in texts if "[evil](" in text] == []
    assert [node.proto.body for node in app.get("html") if TAG in node.proto.body] == []
