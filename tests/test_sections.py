"""Splitting a document into Dokumentabschnitte without gap and overlap, at a fixed level per
format (#84). Pure: no model, no Streamlit."""

import pytest

from govguard.checks.sections import DocSection, split_sections


def spans(name: str, text: str) -> list[tuple[str, int, int]]:
    return [(s.name, s.line_start, s.line_end) for s in split_sections(name, text)]


def test_markdown_is_split_at_the_headings_the_text_before_the_first_is_the_preamble() -> None:
    text = "intro\n\n## One\na\nb\n\n## Two\nc"

    assert spans("input.md", text) == [("Vorspann", 1, 2), ("One", 3, 6), ("Two", 7, 8)]


def test_a_title_above_the_chapters_is_a_section_of_its_own() -> None:
    text = "# Title\nintro\n\n## One\na\n## Two\nb"

    assert spans("input.md", text) == [("Title", 1, 3), ("One", 4, 5), ("Two", 6, 7)]


def test_the_level_is_the_most_frequent_one_that_occurs_twice() -> None:
    text = "# T\n## A\n## B\n## C\n### x"

    assert spans("input.md", text) == [("T", 1, 1), ("A", 2, 2), ("B", 3, 3), ("C", 4, 5)]


def test_a_higher_heading_starts_a_section_too_so_its_intro_stands_alone() -> None:
    """### is the most frequent level: each ## ends the part before it and is a section of its
    own up to its first ###, e.g. "4 Rollen" next to "Für Architekturen"."""
    text = "# T\n## A\nintro\n### a1\nx\n### a2\ny\n## B\nintro b\n### b1\nz"

    assert spans("input.md", text) == [
        ("T", 1, 1), ("A", 2, 3), ("a1", 4, 5), ("a2", 6, 7), ("B", 8, 9), ("b1", 10, 11)]


def test_with_equal_counts_the_deeper_level_decides() -> None:
    text = "## A\n### a\n## B\n### b"

    assert spans("input.md", text) == [("A", 1, 1), ("a", 2, 2), ("B", 3, 3), ("b", 4, 4)]


def test_a_level_used_once_is_no_level_of_its_own() -> None:
    text = "# T\ntext\n## Only\ntext\n### x\n### y"

    assert spans("input.md", text) == [("T", 1, 2), ("Only", 3, 4), ("x", 5, 5), ("y", 6, 6)]


def test_a_hash_line_inside_a_code_fence_is_no_heading() -> None:
    text = "## A\n```\n## not a chapter\n```\n## B\nx"

    assert spans("input.md", text) == [("A", 1, 4), ("B", 5, 6)]


def test_text_without_headings_is_split_into_paragraphs_blank_lines_go_to_the_one_before() -> None:
    text = "\none\nline\n\n\ntwo\n\nthree"

    assert spans("input.txt", text) == [
        ("Absatz 1", 1, 5), ("Absatz 2", 6, 7), ("Absatz 3", 8, 8)]


def test_one_paragraph_is_one_section_and_an_empty_text_has_none() -> None:
    assert spans("input.txt", "just\ntext") == [("Absatz 1", 1, 2)]
    assert split_sections("input.txt", "") == []


def test_sections_are_a_partition_without_gap_and_overlap() -> None:
    texts = ["x\n## A\n\ny\n## B", "a\n\nb\n\n\nc\n", "## A\n## B\n## C"]
    for text in texts:
        sections = split_sections("input.md", text)
        assert sections[0].line_start == 1
        assert sections[-1].line_end == len(text.splitlines())
        assert all(a.line_end + 1 == b.line_start for a, b in zip(sections, sections[1:]))


def test_a_section_knows_its_name_and_lines() -> None:
    [first, _] = split_sections("a.md", "## A\nx\n## B")

    assert first == DocSection(name="A", line_start=1, line_end=2)


TEMPLATE = """{
  "AWSTemplateFormatVersion": "2010-09-09",
  "Resources": {
    "Key": {
      "Type": "AWS::KMS::Key"
    },
    "Bucket": {
      "Type": "AWS::S3::Bucket",
      "Properties": {
        "BucketName": "x"
      }
    }
  },
  "Outputs": {
    "Arn": {}
  }
}"""


def test_a_template_has_a_section_per_resource_and_one_per_other_top_level_key() -> None:
    assert spans("template.json", TEMPLATE) == [
        ("AWSTemplateFormatVersion", 1, 2), ("Key", 3, 6), ("Bucket", 7, 13), ("Outputs", 14, 17)]


def test_the_closing_brace_belongs_to_the_last_section() -> None:
    assert spans("template.json", TEMPLATE)[-1][2] == len(TEMPLATE.splitlines())


def test_json_that_is_not_pretty_printed_falls_back_to_paragraphs() -> None:
    assert spans("template.json", '{"Resources": {"A": {}}}') == [("Absatz 1", 1, 1)]


def test_a_template_without_resources_is_split_by_its_top_level_keys() -> None:
    text = '{\n  "A": 1,\n  "B": {\n    "c": 2\n  }\n}'

    assert spans("template.json", text) == [("A", 1, 2), ("B", 3, 6)]


OPENAPI = """openapi: 3.1.0
info:
  title: Demo
  description: |
    ## not a chapter
    text
paths:
  /a:
    get:
      summary: A
  /b:
    post:
      summary: B
components:
  parameters:
    P:
      name: p
  schemas:
    One:
      type: object
    Two:
      type: string
x-betrieb:
  region: eu
"""


def test_openapi_has_a_section_per_path_and_per_schema_and_one_per_other_top_level_key() -> None:
    assert spans("openapi.yaml", OPENAPI) == [
        ("openapi", 1, 1), ("info", 2, 6), ("/a", 7, 10), ("/b", 11, 13),
        ("components/parameters", 14, 17), ("Schema One", 18, 20), ("Schema Two", 21, 22),
        ("x-betrieb", 23, 24)]


def test_a_comment_line_at_the_left_edge_belongs_to_the_section_before() -> None:
    text = "a:\n  x: 1\n# note\nb:\n  y: 2"

    assert spans("x.yaml", text) == [("a", 1, 3), ("b", 4, 5)]


def test_yaml_is_recognised_by_its_content_too() -> None:
    assert spans("pasted.txt", "openapi: 3.1.0\ninfo:\n  title: x") == [
        ("openapi", 1, 1), ("info", 2, 3)]


SCALAR = """openapi: 3.1.0
info:
  title: Demo
  description: |
    # Fachkonzept

    ## 1 Zweck

    text
    ## 2 Ablauf

    more
paths:
  /a:
    get:
      description: |
        ## 1 not split
        ## 2 not split
x-betrieb:
  region: eu
"""


def test_a_top_level_block_with_markdown_in_a_block_scalar_is_split_by_its_headings() -> None:
    """info.description holds a whole Fachkonzept: its chapters are the sections, named by the
    heading without the indentation."""
    assert spans("openapi.yaml", SCALAR) == [
        ("openapi", 1, 1), ("info", 2, 4), ("Fachkonzept", 5, 6), ("1 Zweck", 7, 9),
        ("2 Ablauf", 10, 12), ("/a", 13, 18), ("x-betrieb", 19, 20)]


def test_yaml_is_recognised_after_a_document_marker_comments_and_blank_lines() -> None:
    text = "---\n# generated\n\nopenapi: 3.1.0\ninfo:\n  title: x"

    assert spans("pasted.txt", text) == [("openapi", 1, 4), ("info", 5, 6)]


def test_a_markdown_line_that_merely_contains_openapi_is_no_yaml() -> None:
    assert spans("notes.txt", "see the openapi: file\n\nand more") == [
        ("Absatz 1", 1, 2), ("Absatz 2", 3, 3)]


def test_a_text_of_blank_lines_is_one_section() -> None:
    assert spans("input.txt", "\n  \n") == [("Vorspann", 1, 2)]


def test_block_scalar_indicators_with_a_digit_a_chomping_sign_or_a_comment_still_open_one() -> None:
    for marker in ("|2-", "|+", ">-", "| # note"):
        text = f"info:\n  description: {marker}\n    ## A\n    x\n    ## B\n    y"

        assert spans("x.yaml", text) == [("info", 1, 2), ("A", 3, 4), ("B", 5, 6)], marker


def test_a_path_with_a_colon_is_one_key() -> None:
    text = "paths:\n  /v1/{name}:cancel:\n    post: {}\n  /v1/b:\n    get: {}"

    assert spans("x.yaml", text) == [("/v1/{name}:cancel", 1, 3), ("/v1/b", 4, 5)]


def test_a_key_after_the_markdown_scalar_does_not_belong_to_its_last_chapter() -> None:
    text = ("openapi: 3.1.0\ninfo:\n  description: |\n    ## A\n    x\n    ## B\n    y\n"
            "  title: Demo\nx-b:\n  r: 1")

    assert spans("x.yaml", text) == [
        ("openapi", 1, 1), ("info", 2, 3), ("A", 4, 5), ("B", 6, 7), ("info", 8, 8),
        ("x-b", 9, 10)]


def test_a_fence_is_closed_only_by_its_own_marker() -> None:
    text = "```\n~~~\n## in the fence\n```\n## A\n## B"

    assert spans("input.md", text) == [("Vorspann", 1, 4), ("A", 5, 5), ("B", 6, 6)]


def test_a_template_indented_with_tabs_is_split_too() -> None:
    text = '{\n\t"Resources": {\n\t\t"A": {\n\t\t\t"Type": "x"\n\t\t},\n\t\t"B": {}\n\t}\n}'

    assert spans("template.json", text) == [("A", 1, 5), ("B", 6, 8)]


ODD_INPUTS = {
    "crlf": "# T\r\n\r\n## A\r\ntext\r\n## B\r\ntext\r\n",
    "setext": "Title\n=====\n\nintro\n\nChapter A\n---------\ntext\n\nChapter B\n---------\ntext",
    "closing hashes": "## A ##\ntext\n## B ###\ntext",
    "hash without space": "#Heading\ntext\n#Other\ntext",
    "one heading": "## Only\ntext\nmore",
    "no headings": "just\ntext\n\nin two paragraphs",
    "numbered chapters without hash": "1 Einleitung\ntext\n\n2 Ablauf\ntext",
    "html blocks": "<h2>A</h2>\n<div>\n## not a heading in html? it is one\n</div>\n<h2>B</h2>",
    "front matter only": "---\ntitle: x\ndate: 2026-10-28\n---",
    "front matter and chapters": "---\ntitle: x\n---\n## A\ntext\n## B\ntext",
    "horizontal rule": "## A\ntext\n\n---\n\n## B\ntext",
    "very long": "\n".join(f"## Chapter {n}\ntext\n" for n in range(1700)),
    "only blank lines": "\n\n\n",
    "single line": "x",
    "yaml in a fence": "# Spec\n\n```yaml\nopenapi: 3.0.3\ninfo:\n  x: 1\n```\n\n## A\nt\n## B\nt",
    "key in a text": "Bitte prüfen.\nswagger: ja\n\n## A\nx\n## B\ny",
}


@pytest.mark.parametrize("text", ODD_INPUTS.values(), ids=ODD_INPUTS)
def test_odd_pasted_input_is_split_without_gap_and_with_names(text: str) -> None:
    sections = split_sections("Eingabe", text)

    covered = [n for s in sections for n in range(s.line_start, s.line_end + 1)]
    assert covered == list(range(1, len(text.splitlines()) + 1))
    assert all(s.name.strip() for s in sections)


def test_setext_headings_are_headings_of_level_one_and_two() -> None:
    text = "Title\n=====\n\nChapter A\n---------\ntext\n\nChapter B\n---------\ntext"

    assert spans("Eingabe", text) == [("Title", 1, 3), ("Chapter A", 4, 7), ("Chapter B", 8, 10)]


def test_closing_hashes_are_no_part_of_the_name_but_a_hash_in_a_word_is() -> None:
    assert [n for n, *_ in spans("Eingabe", "## C# ##\nx\n## C#\ny")] == ["C#", "C#"]


def test_a_hash_without_a_space_is_no_heading() -> None:
    assert spans("Eingabe", "#A\nx\n#B\ny") == [("Absatz 1", 1, 4)]


def test_front_matter_is_no_heading_and_does_not_make_the_text_yaml() -> None:
    text = "---\ntitle: x\n---\n## A\ntext\n## B\ntext"

    assert spans("Eingabe", text) == [("Vorspann", 1, 3), ("A", 4, 5), ("B", 6, 7)]


def test_a_horizontal_rule_after_a_blank_line_is_no_setext_underline() -> None:
    assert spans("Eingabe", "## A\ntext\n\n---\n\n## B\ntext") == [("A", 1, 5), ("B", 6, 7)]


def test_a_markdown_file_is_markdown_even_if_it_starts_like_openapi() -> None:
    assert spans("input.md", "openapi: 3.1.0\ninfo:\n  title: x") == [("Absatz 1", 1, 3)]


def test_an_openapi_key_in_a_fence_or_in_a_text_does_not_make_the_text_yaml() -> None:
    fenced = "# Spec\n\n```yaml\nopenapi: 3.0.3\n```\n\n## A\nx\n## B\ny"
    prose = "Bitte prüfen.\nswagger: ja\n\n## A\nx\n## B\ny"

    assert [n for n, *_ in spans("Eingabe", fenced)] == ["Spec", "A", "B"]
    assert [n for n, *_ in spans("Eingabe", prose)] == ["Vorspann", "A", "B"]


def test_a_title_over_several_lines_is_one_heading_named_by_all_its_lines() -> None:
    text = "Foo\nBar\n---\ntext\n\nBaz\n---\nx"

    assert spans("Eingabe", text) == [("Foo Bar", 1, 5), ("Baz", 6, 8)]


def test_a_list_item_or_indented_code_over_dashes_is_no_heading() -> None:
    for line in ("1. item", "2) item", "    code"):
        text = f"## X\n{line}\n---\ntext\n## Y\nz"

        assert spans("Eingabe", text) == [("X", 1, 4), ("Y", 5, 6)], line


def test_a_bold_line_over_an_underline_is_a_heading() -> None:
    text = "**Fett**\n===\ntext\n\n**Zwei**\n===\nx"

    assert spans("Eingabe", text) == [("**Fett**", 1, 4), ("**Zwei**", 5, 7)]


def test_front_matter_holds_only_keys_else_the_first_dashes_are_a_rule() -> None:
    prose = "---\nHello world\n---\n## A\nx\n## B\ny"
    keys = "---\ntitle: x\ntags:\n  - a\n---\n## A\nx\n## B\ny"

    assert spans("Eingabe", prose) == [
        ("Vorspann", 1, 1), ("Hello world", 2, 3), ("A", 4, 5), ("B", 6, 7)]
    assert spans("Eingabe", keys) == [("Vorspann", 1, 5), ("A", 6, 7), ("B", 8, 9)]
