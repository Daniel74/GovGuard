"""Label of a finding row: Streamlit renders Markdown, the LLM text in it stays text (#43)."""

from govguard_ui.finding_list import row_label
from govguard_ui.gallery import load_gallery
from govguard_ui.paths import GALLERY, PRESETS

ART9 = next(f for e in load_gallery(PRESETS, GALLERY) if e.report
            for f in e.report.findings if f.rule_id == "SPEC-DSGVO-Art.9")  # FAIL, lines 46–49


def test_a_row_shows_status_title_anchor_and_lines() -> None:
    assert row_label(ART9) == (":red-badge[✕ FAIL] **Einwilligung für besondere Kategorien** · "
                               r":gray[DSGVO Art\. 9 · Zeilen 46–49]")


def test_llm_text_in_a_row_label_can_become_neither_link_nor_image_nor_formula() -> None:
    finding = ART9.model_copy(update={"title": "[x](y) ![i](z)", "primary_anchor": "$a$ :red[b]"})

    assert row_label(finding) == (r":red-badge[✕ FAIL] **\[x\]\(y\) \!\[i\]\(z\)** · "
                                  r":gray[\$a\$ \:red\[b\] · Zeilen 46–49]")


def test_a_downgrade_stays_visible_in_the_row() -> None:
    """ADR 0017: the original status shows next to the WARN."""
    finding = ART9.model_copy(update={"status": "WARN", "downgraded_from": "FAIL"})

    assert row_label(finding).startswith(":orange-badge[! WARN ↓ von FAIL] ")
