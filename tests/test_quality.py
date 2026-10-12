"""quality_report(): counts per source what the validator does not enforce."""

from govguard.models import Rule, RuleCatalog
from kb_build.quality import quality_report, vague_terms


def rule(rid: str, source: str, compliant_if: str) -> Rule:
    return Rule(id=rid, audit_type="architecture", source=source, primary_anchor=rid,
                selection_rationale="r", source_quote="q", title="t", compliant_if=compliant_if,
                violation_if="v", recommendation="r", cfn_resource_types=["AWS::S3::Bucket"])


def test_vague_terms_finds_each_word_once_in_its_written_form() -> None:
    text = "Nur erforderliche Rechte; relevante Dienste; erforderliche Rollen."
    assert vague_terms(text) == ["erforderliche", "relevante"]


def test_the_report_counts_vague_and_account_level_rules_per_source() -> None:
    catalog = RuleCatalog(audit_type="architecture", source_versions={}, model_id="m", rules=[
        rule("a", "CIS", "Der CloudTrail-Bucket AWS::S3::Bucket hat LoggingConfiguration."),
        rule("b", "CIS", "AWS::S3::Bucket hat BucketEncryption."),
        rule("c", "BSI", "AWS::S3::Bucket gewährt nur erforderliche Rechte."),
    ])

    assert quality_report(catalog) == {
        "BSI": {"rules": 1, "vague": 1, "account_level": 0},
        "CIS": {"rules": 2, "vague": 0, "account_level": 1},
    }
