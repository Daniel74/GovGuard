"""Reading a report in the UI: expected result, categories, document window (#11)."""

from govguard.models import Expected, RequiredFinding
from govguard_ui.gallery import load_gallery
from govguard_ui.paths import GALLERY, PRESETS
from govguard_ui.report.review import (
    Sorting,
    category,
    category_counts,
    document_window,
    expected_checks,
    no_evidence_note,
    of_source,
    sorted_findings,
    source_counts,
    source_of,
    visible_findings,
    warn_caption,
)

ENTRIES = {entry.preset_id: entry for entry in load_gallery(PRESETS, GALLERY)}


def deviations(preset_id: str) -> list[tuple[str, str, str]]:
    entry = ENTRIES[preset_id]
    checks = expected_checks(entry.report, entry.preset.expected)
    return [(c.label, c.expected, c.actual) for c in checks if not c.ok]


def test_meldeportal_report_meets_art_9_and_misses_the_sdm_deletion_fail() -> None:
    """Regenerated with #61 (350 rules): SDM Löschen M60.P01 came out WARN instead of FAIL, a
    swing of the model. Shown by the expected-result check, not rerolled (ADR 0023)."""
    entry = ENTRIES["spec-meldeportal-gesundheit"]
    checks = {c.label: c for c in expected_checks(entry.report, entry.preset.expected)}

    assert deviations("spec-meldeportal-gesundheit") == [("SDM Löschen M60.P01", "FAIL", "WARN")]
    assert checks["Gesamtstatus"].ok and checks["DSGVO Art. 9 Abs. 2"].ok
    assert not checks["SDM Löschen M60.P01"].ok


def test_wohngeld_report_of_19_october_shows_only_the_overall_status_deviation() -> None:
    """Five false FAIL after #53 (Art. 27, 30, SDM M60.S04/S05), shown, not rerolled (ADR 0023)."""
    assert deviations("spec-wohngeld-openapi") == [("Gesamtstatus", "WARN", "FAIL")]


def test_arch_reports_of_the_catalog_of_47_show_only_the_det_3_1_deviation() -> None:
    """Measured for #47 (catalog f97cc6bf): only DET.3.1 of arch-protokollarchiv misses."""
    assert deviations("arch-antragseingang-fehlerhaft") == []
    assert deviations("arch-fristenwecker") == []
    assert deviations("arch-protokollarchiv") == [("BSI GS++ DET.3.1", "PASS", "WARN")]


def test_overall_status_comes_first_and_a_check_points_to_its_finding() -> None:
    entry = ENTRIES["spec-meldeportal-gesundheit"]

    overall, art9, _ = expected_checks(entry.report, entry.preset.expected)

    assert (overall.label, overall.rule_id) == ("Gesamtstatus", None)
    assert art9.rule_id == "SPEC-DSGVO-Art.9Abs.2"


def test_a_required_anchor_missing_in_the_report_is_a_deviation() -> None:
    report = ENTRIES["spec-meldeportal-gesundheit"].report
    expected = Expected(overall_status="FAIL",
                        required_findings=[RequiredFinding(anchor="DSGVO Art. 99", status="PASS")])

    [_, missing] = expected_checks(report, expected)

    assert (missing.actual, missing.ok, missing.rule_id) == ("fehlt", False, None)


def counts(preset_id: str) -> dict[str, int]:
    return category_counts(ENTRIES[preset_id].report.findings)


def test_spec_report_separates_gaps_from_warnings_with_evidence() -> None:
    """Groq run on the catalog of 350 rules with the condition pre-run (#61)."""
    assert counts("spec-meldeportal-gesundheit") == {
        "FAIL": 33, "WARN": 17, "GAP": 234, "PASS": 28, "N/A": 38}


def test_arch_report_counts_every_category_even_when_empty() -> None:
    assert counts("arch-antragseingang-fehlerhaft") == {
        "FAIL": 36, "WARN": 1, "GAP": 0, "PASS": 27, "N/A": 111}


def test_a_downgraded_finding_without_lines_needs_review_and_is_no_gap() -> None:
    finding = ENTRIES["spec-meldeportal-gesundheit"].report.findings[0]
    downgraded = finding.model_copy(update={
        "status": "WARN", "line_start": None, "line_end": None, "downgraded_from": "PASS"})
    gap = downgraded.model_copy(update={"downgraded_from": None})

    assert (category(downgraded), category(gap)) == ("WARN", "GAP")


def test_a_warn_whose_lines_the_code_dropped_needs_review_and_is_no_gap() -> None:
    """The model pointed somewhere, only the range was unusable: no gap (#74)."""
    finding = ENTRIES["spec-meldeportal-gesundheit"].report.findings[0]
    dropped = finding.model_copy(update={
        "status": "WARN", "line_start": None, "line_end": None, "range_dropped": True})

    assert category(dropped) == "WARN"


def test_stored_reports_from_before_74_load_without_dropped_ranges() -> None:
    """The field has a default: old gallery reports stay readable (#74)."""
    findings = [f for entry in ENTRIES.values() for f in entry.report.findings]
    assert findings and not any(f.range_dropped for f in findings)


def test_the_warn_tile_counts_downgrades_and_dropped_ranges_once_each() -> None:
    findings = ENTRIES["spec-meldeportal-gesundheit"].report.findings
    warn = findings[0].model_copy(update={"status": "WARN", "line_start": None,
                                          "line_end": None, "downgraded_from": None})
    dropped = warn.model_copy(update={"range_dropped": True})
    both = dropped.model_copy(update={"downgraded_from": "FAIL"})  # counts as downgrade only

    assert warn_caption([warn]) == "mit Beleg"
    assert warn_caption([dropped, both]) == (
        "mit Beleg · davon 1 herabgestuft, 1 mit gestrichenem Bereich")


def test_a_dropped_range_explains_the_missing_evidence() -> None:
    finding = ENTRIES["spec-meldeportal-gesundheit"].report.findings[0]
    plain = finding.model_copy(update={"line_start": None, "line_end": None})

    assert "keine Stelle" in no_evidence_note(plain)
    assert "gestrichen" in no_evidence_note(plain.model_copy(update={"range_dropped": True}))


def test_source_filter_names_come_from_the_rule_id() -> None:
    findings = ENTRIES["arch-antragseingang-fehlerhaft"].report.findings

    assert {source_of(f) for f in findings} == {"BSI", "C5", "CIS", "FSBP"}


def test_the_source_of_ki_vo_keeps_its_hyphen() -> None:
    finding = ENTRIES["spec-meldeportal-gesundheit"].report.findings[0]

    assert source_of(finding.model_copy(update={"rule_id": "SPEC-KI-VO-Art.6Abs.2"})) == "KI-VO"


def test_each_source_counts_its_findings_with_na_but_without_gaps() -> None:
    """Gaps stand in their own list below the table: DSGVO 169-101, KI-VO 65-45, SDM 116-88."""
    findings = ENTRIES["spec-meldeportal-gesundheit"].report.findings

    assert source_counts(findings) == {"Alle": 116, "DSGVO": 68, "KI-VO": 20, "SDM": 28}


def test_of_source_keeps_the_findings_of_one_source_or_all() -> None:
    findings = ENTRIES["spec-meldeportal-gesundheit"].report.findings

    assert (len(of_source(findings, "DSGVO")), len(of_source(findings, None))) == (169, 350)


TEN_LINES = "\n".join(f"Zeile {n}" for n in range(1, 11)) + "\n"


def with_lines(start: int | None, end: int | None):
    finding = ENTRIES["spec-meldeportal-gesundheit"].report.findings[0]
    return finding.model_copy(update={"line_start": start, "line_end": end})


def test_window_starts_four_lines_above_the_evidence_and_marks_it() -> None:
    window = document_window(TEN_LINES, with_lines(7, 8), full=False)

    assert window.hidden_above == 2
    assert [(line.number, line.marked) for line in window.lines][:5] == [
        (3, False), (4, False), (5, False), (6, False), (7, True)]
    assert [line.text for line in window.lines if line.marked] == ["Zeile 7", "Zeile 8"]
    assert window.lines[-1].number == 10  # the trailing newline adds no empty line


def test_whole_document_on_request_still_marks_the_evidence() -> None:
    window = document_window(TEN_LINES, with_lines(7, 8), full=True)

    assert (window.hidden_above, len(window.lines)) == (0, 10)
    assert [line.number for line in window.lines if line.marked] == [7, 8]


def test_without_evidence_lines_the_whole_document_shows_unmarked() -> None:
    window = document_window(TEN_LINES, with_lines(None, None), full=False)

    assert (window.hidden_above, len(window.lines)) == (0, 10)
    assert not any(line.marked for line in window.lines)


def test_list_shows_chosen_categories_fail_first_then_by_line_and_never_gaps() -> None:
    findings = ENTRIES["spec-meldeportal-gesundheit"].report.findings

    shown = visible_findings(findings, {"FAIL", "WARN", "GAP"}, source="SDM")

    assert {category(f) for f in shown} == {"FAIL", "WARN"}
    assert {source_of(f) for f in shown} == {"SDM"}
    keys = [(f.status != "FAIL", f.line_start) for f in shown]
    assert keys == sorted(keys)


def test_source_alle_keeps_every_source() -> None:
    findings = ENTRIES["spec-meldeportal-gesundheit"].report.findings

    assert len(visible_findings(findings, {"PASS", "N/A"}, source=None)) == 28 + 38



def row(rule_id: str, status: str, anchor: str, start: int | None):
    """A finding of the table; title follows the anchor, so both sort the same (#80)."""
    return with_lines(start, start).model_copy(update={
        "rule_id": rule_id, "status": status, "primary_anchor": anchor, "title": anchor.lower(),
        "downgraded_from": None, "range_dropped": False})


TABLE = [row("A", "FAIL", "Art. 10", 30), row("B", "FAIL", "Art. 9", None),
         row("C", "WARN", "Art. 2", 5), row("D", "PASS", "Art. 9", 12)]  # default order


def ids(findings) -> list[str]:
    return [f.rule_id for f in findings]


def test_by_default_the_table_is_sorted_by_status_ascending_the_order_of_the_list() -> None:
    assert Sorting() == Sorting(column="status", descending=False)
    assert ids(sorted_findings(TABLE, Sorting())) == ["A", "B", "C", "D"]


def test_a_click_on_the_sorted_column_flips_it_another_column_starts_ascending() -> None:
    flipped = Sorting().clicked("status")

    assert flipped == Sorting(column="status", descending=True)
    assert flipped.clicked("status") == Sorting()
    assert flipped.clicked("lines") == Sorting(column="lines", descending=False)


def test_status_descending_starts_with_the_mildest_and_keeps_the_order_within_a_status() -> None:
    assert ids(sorted_findings(TABLE, Sorting(column="status", descending=True))) == [
        "D", "C", "A", "B"]


def test_anchor_and_title_sort_naturally_equal_values_keep_the_default_order() -> None:
    """Art. 9 before Art. 10, like OPS.1.1.2 before OPS.1.1.10; B (FAIL) stays before D (PASS)."""
    for column in ("primary_anchor", "title"):
        assert ids(sorted_findings(TABLE, Sorting(column=column))) == ["C", "B", "D", "A"]
        assert ids(sorted_findings(TABLE, Sorting(column=column, descending=True))) == [
            "A", "B", "D", "C"]


def test_lines_sort_as_numbers_and_findings_without_lines_stay_last_both_ways() -> None:
    assert ids(sorted_findings(TABLE, Sorting(column="lines"))) == ["C", "D", "A", "B"]
    assert ids(sorted_findings(TABLE, Sorting(column="lines", descending=True))) == [
        "A", "D", "C", "B"]
