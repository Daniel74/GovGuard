"""Gaps below the table: split by condition, each gap once; old list without conditions (#61)."""

from collections import Counter

from streamlit.testing.v1 import AppTest
from ui_helpers import (
    SPEC,
    conditions_page,
    gallery_entry,
    report_page,
    with_conditions,
    without_conditions,
)

from govguard_ui.report.review import category, of_source


def gap_lines(app: AppTest) -> list[str]:
    """Every list item in the gap expanders; the grouping heads are no items."""
    return [line for e in app.expander if "Lücken" in e.label for m in e.get("markdown")
            for line in str(m.value).split("\n") if line.startswith("- ")]


def test_a_report_without_conditions_keeps_the_old_checklist() -> None:
    entry = without_conditions(gallery_entry(SPEC))
    app = report_page(entry)

    total = len([f for f in entry.report.findings if category(f) == "GAP"])
    assert [e.label for e in app.expander] == [f"Was die Eingabe nicht beschreibt · {total} Lücken"]
    assert "### Lücken" not in " ".join(m.value for m in app.markdown)


def test_with_conditions_the_gaps_are_a_section_with_help_and_one_sentence_on_the_split() -> None:
    entry = with_conditions(gallery_entry(SPEC))
    app = report_page(entry)
    total = len([f for f in entry.report.findings if category(f) == "GAP"])

    heading = next(m for m in app.markdown if m.value.startswith("### Lücken · "))
    assert heading.value == f"### Lücken · {total}"
    assert "Eine Lücke ist eine Prüfregel, zu der die Eingabe nichts sagt" in heading.proto.help
    assert any(c.value.startswith("Jede Lücke steht genau einmal: ") for c in app.caption)


def test_common_gaps_come_first_then_one_expander_per_open_condition() -> None:
    app = conditions_page()

    labels = [e.label for e in app.expander]
    assert labels[0].startswith("Für jedes Vorhaben zu klären · ")
    assert all(label.startswith(("Nur wenn das System mehrere Mandanten bedient",
                                 "Nur wenn eine Entscheidung ausschließlich automatisiert"))
               for label in labels[1:])


def test_every_gap_stands_exactly_once_in_the_sections() -> None:
    entry = with_conditions(gallery_entry(SPEC))
    app = report_page(entry)

    shown = [line.replace("\\", "") for line in gap_lines(app)]
    gaps = [" ".join(f"- {f.title} · {f.primary_anchor}".split())
            for f in of_source(entry.report.findings, None) if category(f) == "GAP"]
    assert Counter(shown) == Counter(gaps)


def test_a_gap_of_a_denied_condition_is_gone_because_its_rule_is_not_applicable() -> None:
    app = conditions_page()

    assert not any("Einwilligung" in line and "Art. 7" in line for line in gap_lines(app))


def test_the_counts_in_the_labels_add_up_to_the_heading() -> None:
    app = conditions_page()

    counts = [int(e.label.rsplit("· ", 1)[1].split()[0]) for e in app.expander]
    heading = next(m.value for m in app.markdown if m.value.startswith("### Lücken · "))
    assert sum(counts) == int(heading.rsplit("· ", 1)[1])
