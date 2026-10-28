"""The sites of the six presets with their gallery reports: no line belongs to two sites, and a
finding with lines stands in exactly one site or in the group of several sections (#84)."""

import pytest

from govguard.checks.sections import split_sections
from govguard.checks.sites import group_sites
from govguard_ui.gallery import GalleryEntry, load_gallery
from govguard_ui.paths import GALLERY, PRESETS

ENTRIES = [e for e in load_gallery(PRESETS, GALLERY) if e.report]


def test_all_six_presets_have_a_gallery_report() -> None:
    assert len(ENTRIES) == 6


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e.preset_id)
def test_no_line_belongs_to_two_sites(entry: GalleryEntry) -> None:
    sections = split_sections(entry.source_name, entry.source_text)
    sites = group_sites(entry.report.findings, sections)

    owners: dict[int, str] = {}
    for site in sites.placed:
        for line in range(site.line_start, site.line_end + 1):
            assert line not in owners, f"line {line} in {owners[line]} and {site.name}"
            owners[line] = site.name


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e.preset_id)
def test_every_located_finding_stands_in_exactly_one_place(entry: GalleryEntry) -> None:
    sections = split_sections(entry.source_name, entry.source_text)
    findings = entry.report.findings
    sites = group_sites(findings, sections)

    placed = [f.rule_id for s in sites.placed for f in s.findings]
    located = [f.rule_id for f in findings if f.line_start is not None]
    assert sorted(placed + [f.rule_id for f in sites.multi]) == sorted(located)
    assert len(sites.without_lines) == len(findings) - len(located)
    for site in sites.placed:  # the lines of each finding lie inside its site
        assert all(site.line_start <= f.line_start and f.last_line <= site.line_end
                   for f in site.findings)


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: e.preset_id)
def test_the_sections_cover_the_document_without_gap(entry: GalleryEntry) -> None:
    sections = split_sections(entry.source_name, entry.source_text)

    assert sections[0].line_start == 1
    assert sections[-1].line_end == len(entry.source_text.splitlines())
    assert all(a.line_end + 1 == b.line_start for a, b in zip(sections, sections[1:]))
