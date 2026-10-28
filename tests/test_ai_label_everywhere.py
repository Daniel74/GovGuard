"""Every place of the UI that shows model text carries the AI label (#83).

The text of the LLM is Finding.rationale and Finding.recommendation (later also the measure of
#82). A module that reads them must use the building block report/ai_label.py; the component in
site_script is JS and takes the marker from its data (`ai.marker`). A new place that forgets
the label fails here.
"""

import re
from pathlib import Path

UI = Path(__file__).parent.parent / "src" / "govguard_ui"
MODEL_TEXT = re.compile(  # an attribute (finding.rationale) or a key ("rationale")
    r"""\.(?:rationale|recommendation)\b|["'](?:rationale|recommendation)["']""")
LABELLED = ("ai_label(", "ai_texts(", "ai.marker")  # a call of the block, or its data in the JS


def unlabelled(root: Path) -> list[str]:
    return [path.relative_to(root).as_posix() for path in sorted(root.rglob("*.py"))
            if MODEL_TEXT.search(source := path.read_text(encoding="utf-8"))
            and not any(mark in source for mark in LABELLED)]


def test_a_place_with_model_text_and_without_the_block_is_found(tmp_path: Path) -> None:
    (tmp_path / "bad.py").write_text("st.write(finding.rationale)\n", encoding="utf-8")
    (tmp_path / "js.py").write_text('el("div", "w", f.recommendation) // ai.marker\n',
                                    encoding="utf-8")
    (tmp_path / "raw.py").write_text(  # imports only the header line, shows the text raw
        "from govguard_ui.report.ai_label import disclosure_html\nst.write(finding.rationale)\n",
        encoding="utf-8")
    (tmp_path / "key.py").write_text('{"recommendation": text}\n', encoding="utf-8")
    (tmp_path / "good.py").write_text(
        "from govguard_ui.report.ai_label import ai_label\n"
        "ai_label('Begründung') + finding.rationale\n", encoding="utf-8")

    assert unlabelled(tmp_path) == ["bad.py", "key.py", "raw.py"]


def test_every_place_of_the_ui_with_model_text_uses_the_ai_label() -> None:
    assert unlabelled(UI) == []
