import json

import pytest

from govguard.models import CrossReference, Rule, RuleCatalog, Trace


@pytest.fixture
def spec_input() -> str:
    return (
        "Das Bürgerportal speichert Gesundheitsdaten im Klartext in einem öffentlichen S3-Bucket.\n"
        "Alle Zugriffe erfolgen ausschließlich über TLS 1.3."
    )


def make_rule(requirement_id: str, title: str, cfn_resource_types: list[str] | None = None) -> Rule:
    return Rule(
        id=f"SPEC-DSGVO-{requirement_id}",
        audit_type="spec",
        source="DSGVO",
        primary_anchor=f"DSGVO {requirement_id.replace('.', '. ')}",
        source_quote="Der Verantwortliche trifft geeignete technische Maßnahmen.",
        title=title,
        compliant_if="Die Maßnahme ist beschrieben.",
        violation_if="Die Maßnahme fehlt nachweislich.",
        recommendation="Maßnahme ergänzen.",
        cross_references=[CrossReference(anchor="BSI GS++ KONF.1.1", origin="ai_suggested")],
        selection_rationale="An einer Spezifikation prüfbar.",
        cfn_resource_types=cfn_resource_types or [],
        rank=1,
    )


@pytest.fixture
def spec_catalog() -> RuleCatalog:
    return RuleCatalog(
        audit_type="spec",
        source_versions={"DSGVO": "2016/679"},
        model_id="fake-model",
        rules=[
            make_rule("Art.32", "Sicherheit der Verarbeitung"),
            make_rule("Art.9", "Gesundheitsdaten"),
        ],
    )


@pytest.fixture
def trace() -> Trace:
    return Trace(audit_id="a-1", input_sha256="abc", catalog_sha256="def", kb_commit="4905b01")


@pytest.fixture
def arch_catalog() -> RuleCatalog:
    def arch_rule(requirement_id: str, title: str, cfn_type: str) -> Rule:
        return make_rule(requirement_id, title).model_copy(update={
            "id": f"ARCH-CIS-{requirement_id}", "audit_type": "architecture", "source": "CIS",
            "primary_anchor": f"CIS AWS v7.0.0 {requirement_id}", "cfn_resource_types": [cfn_type],
        })

    return RuleCatalog(
        audit_type="architecture",
        source_versions={"CIS": "v7.0.0"},
        model_id="fake-model",
        rules=[
            arch_rule("3.1.4", "S3 Block Public Access aktiv", "AWS::S3::Bucket"),
            arch_rule("3.3.1", "DynamoDB verschlüsselt", "AWS::DynamoDB::Table"),
        ],
    )


@pytest.fixture
def bucket_template() -> str:
    return json.dumps({"Resources": {"Docs": {
        "Type": "AWS::S3::Bucket",
        "Properties": {"PublicAccessBlockConfiguration": {"BlockPublicAcls": True}},
    }}}, indent=2)


@pytest.fixture(autouse=True)
def fake_aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests never touch real AWS credentials or profiles."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    monkeypatch.delenv("AWS_PROFILE", raising=False)
