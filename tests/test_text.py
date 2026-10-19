import json

import pytest

from govguard.text import contains_quote, normalize, template_resource_types

SPEC = "Gesundheitsdaten werden\nim Klartext in einem\u00a0öffentlichen S3-Bucket gespeichert."


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Pseudonymi\ufb01zierung", "Pseudonymifizierung"),  # NFKC: ligature "fi"
        ("►C2 Die Verarbeitung◄ ist rechtmäßig", "Die Verarbeitung ist rechtmäßig"),
        ("▼M1 Art. 32", "Art. 32"),
        ("Verarbei\u00adtung", "Verarbeitung"),  # soft hyphen
        ("„Daten“ – ‚sicher‘ — «Cloud»", "\"Daten\" - 'sicher' - \"Cloud\""),
        ("  Daten\n\n werden\t\u00a0gelöscht ", "Daten werden gelöscht"),
        ("S3-Bucket MUSS", "S3-Bucket MUSS"),  # case and real hyphens stay
    ],
)
def test_normalize_produces_comparable_text(raw: str, expected: str) -> None:
    assert normalize(raw) == expected


def test_contains_quote_finds_verbatim_quote_across_line_breaks() -> None:
    assert contains_quote(SPEC, "werden im Klartext in einem öffentlichen S3-Bucket")


def test_contains_quote_ignores_spaces_that_pypdf_puts_into_words() -> None:
    # SDM M60.S06 as extracted by pypdf; the model quotes the intact word
    sdm = "Datensparsame Ausgestaltung der Protokollie rung von Löschungen"
    assert contains_quote(sdm, "Ausgestaltung der Protokollierung von Löschungen")


def test_contains_quote_rejects_rephrased_quote() -> None:
    assert not contains_quote(SPEC, "werden unverschlüsselt in einem öffentlichen S3-Bucket")


def test_contains_quote_rejects_quote_differing_only_in_case() -> None:
    assert not contains_quote(SPEC, "GESUNDHEITSDATEN WERDEN IM KLARTEXT")


def test_contains_quote_rejects_quotes_shorter_than_15_chars() -> None:
    assert not contains_quote(SPEC, "S3-Bucket")
    assert not contains_quote(SPEC, "   S3-Bucket   ")  # padding does not count


ARCH_LINE = "- **API Gateway (REST, regional):** Die Fachanwendung ruft `POST /akten` auf."


def test_contains_quote_accepts_quote_without_markdown_emphasis() -> None:
    assert contains_quote(ARCH_LINE, "API Gateway (REST, regional): Die Fachanwendung")


@pytest.mark.parametrize(
    ("text", "quote"),
    [
        ("Der *Bucket* ist _öffentlich_ erreichbar", "Der Bucket ist öffentlich erreichbar"),
        ("Der Bucket ist öffentlich erreichbar", "Der **Bucket** ist `öffentlich` erreichbar"),
    ],
)
def test_contains_quote_ignores_markdown_emphasis_on_both_sides(text: str, quote: str) -> None:
    assert contains_quote(text, quote)


def test_contains_quote_still_rejects_invented_quote_next_to_markdown() -> None:
    assert not contains_quote(ARCH_LINE, "API Gateway (REST, regional): Die Datenbank speichert")


def test_contains_quote_measures_min_length_without_markdown() -> None:
    assert not contains_quote("**S3-Bucket** ist da", "**S3-Bucket** ist")  # 13 chars stripped
    assert not contains_quote("*" * 40, "*" * 20)  # nothing left to prove


@pytest.mark.parametrize("hyphen", ["\u2010", "\u2011"])
def test_contains_quote_accepts_unicode_hyphens_of_the_model(hyphen: str) -> None:
    # Groq writes "Hochrisiko‐KI‐Systems" with U+2010, EUR-Lex has "-" (KI-VO Art. 13, #52)
    text = "die Zweckbestimmung des Hochrisiko-KI-Systems, einschließlich"
    assert contains_quote(text, f"Zweckbestimmung des Hochrisiko{hyphen}KI{hyphen}Systems")


def test_normalize_keeps_unicode_hyphens_so_the_frozen_extracts_stay() -> None:
    # NFKC turns U+2011 into U+2010; the extracts keep it, only the quote comparison maps it
    assert normalize("Ende\u2011zu\u2010Ende") == "Ende\u2010zu\u2010Ende"


def test_template_resource_types_lists_types_of_cloudformation_json() -> None:
    template = json.dumps({
        "Resources": {
            "Docs": {"Type": "AWS::S3::Bucket"},
            "Logs": {"Type": "AWS::S3::Bucket"},
            "Fn": {"Type": "AWS::Lambda::Function", "Properties": {}},
        }
    })
    assert template_resource_types(template) == {"AWS::S3::Bucket", "AWS::Lambda::Function"}


@pytest.mark.parametrize(
    "text",
    [
        "Die Anwendung speichert Daten in einem S3-Bucket.",  # free text
        "Resources:\n  Docs:\n    Type: AWS::S3::Bucket\n",  # YAML counts as free text
        '{"openapi": "3.1.0", "paths": {}}',  # JSON, but no template
        '["AWS::S3::Bucket"]',  # JSON, but not an object
    ],
)
def test_template_resource_types_returns_none_for_non_templates(text: str) -> None:
    assert template_resource_types(text) is None
