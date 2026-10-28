"""The one building block of the AI label in the UI: header line and marker (#83)."""

from govguard_ui.report.ai_label import ai_label, ai_texts, disclosure_line, marker


def test_the_header_line_names_the_model_and_what_the_code_checked() -> None:
    assert disclosure_line("openai/gpt-oss-120b") == (
        "Mit KI erstellt · Modell openai/gpt-oss-120b · "
        "Status, Fundstellen und Zitate hat der Code nachgeprüft")


def test_the_marker_is_a_small_ki_with_a_tooltip() -> None:
    html_text = marker()

    assert ">KI<" in html_text
    assert 'title="vom Sprachmodell geschrieben"' in html_text


def test_a_label_carries_the_marker_next_to_its_name() -> None:
    assert ai_label("Begründung").startswith("<strong>Begründung</strong> <span")
    assert marker() in ai_label("Begründung")


def test_the_component_gets_the_same_texts_as_the_python_views() -> None:
    assert ai_texts() == {"marker": "KI", "tip": "vom Sprachmodell geschrieben"}


def test_a_text_the_code_wrote_gets_a_label_without_the_marker() -> None:
    assert ai_label("Begründung", by_code=True) == "<strong>Begründung</strong>"
