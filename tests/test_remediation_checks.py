"""The code checks the measures of the model before the reader sees them (#82): the model names
line numbers inside the site, the code cuts the "before" from the document; the measures do not
overlap, every WARN/FAIL belongs to exactly one."""

import pytest
from site_factories import finding

from govguard.checks.remediation import MeasureProblem, offers_measures, resolve_measures
from govguard.checks.remediation_models import MeasureDraft
from govguard.checks.sites import Site

DOCUMENT = "\n".join([
    "# Vorspann",                       # 1
    "## Speicher",                      # 2  site: 2-9
    "Bucket: antrag",                   # 3
    "  Policy:",                        # 4
    "    Resource: *",                  # 5
    "    Action: s3:*",                 # 6
    "  Logging: aus",                   # 7
    "  Logging: aus",                   # 8
    "",                                 # 9  blank
    "## Danach",                        # 10
    "    Resource: *",                  # 11
])
SITE = Site(name="Speicher", line_start=2, line_end=9, findings=[
    finding("A", "FAIL", 5, 5), finding("B", "WARN", 6, 6), finding("C", "FAIL", 7, 7),
    finding("P", "PASS", 3, 3)])


def draft(from_line: int, to_line: int, rule_ids: list[str], after: str = "neu",
          sentence: str = "Satz.") -> MeasureDraft:
    return MeasureDraft(sentence=sentence, from_line=from_line, to_line=to_line, after=after,
                        rule_ids=rule_ids)


GOOD = [draft(5, 6, ["A", "B"], after="    Resource: [Bucket-ARN]"), draft(7, 8, ["C"])]


def problem_of(drafts: list[MeasureDraft]) -> str:
    with pytest.raises(MeasureProblem) as error:
        resolve_measures(drafts, SITE, DOCUMENT)
    return str(error.value)


def test_a_valid_answer_becomes_measures_with_the_before_cut_by_the_code() -> None:
    first, second = resolve_measures(GOOD, SITE, DOCUMENT)

    assert (first.line_start, first.line_end) == (5, 6)
    assert first.before == "    Resource: *\n    Action: s3:*"  # cut from the document
    assert first.after == "    Resource: [Bucket-ARN]"
    assert first.rule_ids == ["A", "B"] and first.anchors == ["BSI OPS.1.1.2.A3"]  # once
    assert (second.line_start, second.line_end, second.before) == (
        7, 8, "  Logging: aus\n  Logging: aus")  # the same text twice is no problem: numbers


def test_one_line_is_enough() -> None:
    [measure, _] = resolve_measures([draft(5, 5, ["A", "B"]), GOOD[1]], SITE, DOCUMENT)

    assert measure.before == "    Resource: *"


def test_line_numbers_copied_from_the_marked_document_leave_the_after() -> None:
    copied = ">  5|     Resource: [Bucket-ARN]\n  6|     Action: s3:GetObject"
    [measure, _] = resolve_measures([draft(5, 6, ["A", "B"], after=copied), GOOD[1]],
                                    SITE, DOCUMENT)

    assert measure.after == "    Resource: [Bucket-ARN]\n    Action: s3:GetObject"


def test_an_after_where_only_some_lines_look_numbered_stays_as_it_is() -> None:
    mixed = "    Resource: [Bucket-ARN]\n 12| Tabelle"
    [measure, _] = resolve_measures([draft(5, 6, ["A", "B"], after=mixed), GOOD[1]],
                                    SITE, DOCUMENT)

    assert measure.after == mixed


def test_from_line_must_not_come_after_to_line() -> None:
    assert "Maßnahme 1" in problem_of([draft(6, 5, ["A", "B"]), GOOD[1]])


@pytest.mark.parametrize(("start", "end"), [(1, 6), (5, 10), (10, 11), (0, 5)])
def test_both_lines_must_lie_inside_the_site(start: int, end: int) -> None:
    reason = problem_of([draft(start, end, ["A", "B"]), GOOD[1]])

    assert "Maßnahme 1" in reason and "2–9" in reason


def test_lines_that_are_all_blank_are_refused_in_this_ticket() -> None:
    assert "leer" in problem_of([GOOD[0], draft(9, 9, ["C"])])


def test_two_measures_must_not_change_the_same_line() -> None:
    reason = problem_of([draft(6, 8, ["A", "B"]), draft(5, 6, ["C"])])

    assert "überschneiden" in reason and "Maßnahme 1" in reason and "Maßnahme 2" in reason


def test_measures_that_only_touch_do_not_overlap() -> None:
    assert resolve_measures([draft(5, 6, ["A", "B"]), draft(7, 7, ["C"])], SITE, DOCUMENT)


def test_every_warn_and_fail_of_the_site_belongs_to_a_measure() -> None:
    assert "C" in problem_of([draft(5, 6, ["A", "B"])])


def test_a_finding_belongs_to_exactly_one_measure() -> None:
    reason = problem_of([GOOD[0], draft(7, 8, ["C", "A"])])

    assert "A" in reason and "mehreren Maßnahmen" in reason


@pytest.mark.parametrize("rule_id", ["X", "P"])  # not in the report / a PASS of the site
def test_an_unknown_rule_id_or_a_pass_is_sent_back(rule_id: str) -> None:
    assert rule_id in problem_of([*GOOD, draft(3, 3, [rule_id])])


def test_a_measure_without_a_rule_id_is_sent_back() -> None:
    reason = problem_of([*GOOD, draft(3, 3, [])])

    assert "Maßnahme 3" in reason and "mindestens" in reason


def test_at_most_three_measures() -> None:
    four = [draft(5, 5, ["A"]), draft(6, 6, ["B"]), draft(7, 7, ["C"]), draft(3, 3, [])]

    assert "höchstens 3" in problem_of(four).lower()


def test_all_problems_come_in_one_reason_so_one_retry_can_fix_them() -> None:
    reason = problem_of([draft(8, 1, ["A"]), draft(3, 3, ["X"])])

    assert reason.count("\n") >= 2


def test_the_button_is_offered_from_two_warn_or_fail() -> None:
    one = Site(name="s", line_start=1, line_end=9, findings=[
        finding("A", "FAIL", 1, 1), finding("P", "PASS", 2, 2), finding("N", "N/A", 3, 3)])
    assert not offers_measures(one)
    assert offers_measures(SITE)
