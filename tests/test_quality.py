"""quality_report(): counts per source what the validator does not enforce."""

from govguard.models import Rule, RuleCatalog
from kb_build.reference.cfn_properties import PropertyIndex
from kb_build.rules.quality import quality_report, vague_terms

PROPERTIES = PropertyIndex({"AWS::S3::Bucket": frozenset({"BucketEncryption",
                                                          "LoggingConfiguration"})})


def rule(rid: str, source: str, compliant_if: str) -> Rule:
    return Rule(id=rid, audit_type="architecture", source=source, primary_anchor=rid,
                selection_rationale="r", source_quote="q", title="t", compliant_if=compliant_if,
                violation_if="v", recommendation="r", cfn_resource_types=["AWS::S3::Bucket"])


def test_vague_terms_finds_each_word_once_in_its_written_form() -> None:
    text = "Nur erforderliche Rechte; relevante Dienste; erforderliche Rollen."
    assert vague_terms(text) == ["erforderliche", "relevante"]


def test_equivalent_is_vague_because_only_listed_implementations_are_decidable() -> None:
    # #47: "oder gleichwertig" needs knowledge beyond the template; list the variants instead
    assert vague_terms("Deny bei false oder eine gleichwertige Policy.") == ["gleichwertige"]


def test_the_report_counts_vague_account_level_and_invented_property_rules_per_source() -> None:
    catalog = RuleCatalog(audit_type="architecture", source_versions={}, model_id="m", rules=[
        rule("a", "CIS", "Der CloudTrail-Bucket AWS::S3::Bucket hat LoggingConfiguration."),
        rule("b", "CIS", "AWS::S3::Bucket hat BucketEncryption.TargetPrefix."),
        rule("c", "BSI", "AWS::S3::Bucket gewährt nur erforderliche Rechte."),
    ])

    assert quality_report(catalog, PROPERTIES) == {
        "BSI": {"rules": 1, "vague": 1, "account_level": 0, "unknown_properties": 0,
                "unjudged_properties": 0},
        "CIS": {"rules": 2, "vague": 0, "account_level": 1, "unknown_properties": 1,
                "unjudged_properties": 0},
    }


def test_a_cloudtrail_resource_in_the_template_is_no_account_level_duty() -> None:
    # AWS::CloudTrail::Trail is decidable at the template; "CloudTrail ist aktiv" is not
    catalog = RuleCatalog(audit_type="architecture", source_versions={}, model_id="m", rules=[
        rule("a", "BSI", "AWS::CloudTrail::Trail hat IsLogging: true und S3BucketName."),
    ])

    assert quality_report(catalog, PROPERTIES)["BSI"]["account_level"] == 0


def test_a_rule_with_a_type_outside_the_snapshot_counts_as_unjudged() -> None:
    catalog = RuleCatalog(audit_type="architecture", source_versions={}, model_id="m", rules=[
        rule("a", "BSI", "AWS::CloudFront::Distribution hat ViewerProtocolPolicy."),
    ])

    counts = quality_report(catalog, PROPERTIES)["BSI"]

    assert (counts["unknown_properties"], counts["unjudged_properties"]) == (0, 1)
