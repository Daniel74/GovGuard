"""Which texts the code wrote itself stays on the finding: `by_code` (#83).

The "KI" marker belongs only to text the model wrote. The model never sees the field: it is not
in the schema of submit_audit.
"""

from test_run_audit import PASS_32, WARN_9, answer_in_turns, answer_with
from test_run_audit_conditions import audit as conditions_audit
from test_run_audit_conditions import conditions_answer, fake
from test_run_audit_template import S3_PASS
from test_run_audit_template import fake as template_fake

from govguard.audit_engine import run_audit
from govguard.models import AuditResponse
from govguard_ui.gallery import load_gallery
from govguard_ui.paths import GALLERY, PRESETS


def test_the_schema_of_the_model_does_not_know_by_code() -> None:
    assert "by_code" not in str(AuditResponse.model_json_schema())


def test_what_the_model_wrote_is_not_by_code(spec_catalog, spec_input, trace) -> None:
    report = run_audit(spec_catalog, spec_input, answer_with(PASS_32, WARN_9), trace)

    assert [f.by_code for f in report.findings] == [[], []]


def test_na_by_code_in_a_template_names_the_rationale(arch_catalog, bucket_template, trace) -> None:
    report = run_audit(arch_catalog, bucket_template, template_fake(S3_PASS, []), trace)

    by_rule = {f.rule_id: f for f in report.findings}
    assert by_rule["ARCH-CIS-3.3.1"].by_code == ["rationale"]  # N/A: type not in the template
    assert by_rule["ARCH-CIS-3.1.4"].by_code == []  # the model's PASS


def test_na_from_a_denied_condition_names_the_rationale(trace) -> None:
    report = conditions_audit(fake(conditions_answer({"ki_system": 1}), []), trace)

    by_rule = {f.rule_id: f for f in report.findings}
    assert by_rule["SPEC-DSGVO-R1"].by_code == ["rationale"]
    assert by_rule["SPEC-DSGVO-R3"].by_code == []  # WARN from the model


def test_an_unproven_pass_names_the_recommendation_only(spec_catalog, spec_input, trace) -> None:
    unproven = {**PASS_32, "line_start": None, "line_end": None}

    report = run_audit(spec_catalog, spec_input,
                       answer_in_turns([unproven, WARN_9], seen=[]), trace)

    tls = report.findings[0]
    assert (tls.status, tls.rationale, tls.by_code) == ("WARN", "TLS.", ["recommendation"])


def test_a_recommendation_from_the_rule_keeps_the_marker(
    spec_catalog, spec_input, trace
) -> None:
    no_recommendation = {**WARN_9, "recommendation": None}

    report = run_audit(spec_catalog, spec_input,
                       answer_in_turns([PASS_32, no_recommendation], seen=[]), trace)

    # the build model wrote the rule's recommendation, the code only adds a prefix
    assert report.findings[1].recommendation == "Falls nicht erfüllt: Maßnahme ergänzen."
    assert [f.by_code for f in report.findings] == [[], []]


def test_the_stored_reports_name_the_na_texts_the_code_wrote() -> None:
    """The gallery was filled once with the provenance (#83): no code N/A is left unmarked."""
    code_texts = ("Ressourcentyp nicht im Template", "Dienst in der Eingabe nicht erkannt")
    for entry in load_gallery(PRESETS, GALLERY):
        for f in entry.report.findings:
            if f.status == "N/A" and (f.rationale in code_texts
                                      or f.rationale.startswith("Die Spezifikation verneint: ")):
                assert f.by_code == ["rationale"], (entry.preset_id, f.rule_id)
