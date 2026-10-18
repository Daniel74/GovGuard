"""Prompts of the formulate step: what they must not say (#47)."""

import pytest

from kb_build.rules.prompts import PROMPTS


# "DET.3.1" stays out: the shared prompt shows "BSI GS++ DET.3.1" as cross-reference format only
@pytest.mark.parametrize("term", ["S3.5", "SecureTransport", "KONF.11.7.2",
                                  "EndpointConfiguration", "RetentionInDays", "Aufbewahrung"])
def test_the_architecture_prompt_names_no_rule_it_is_measured_by(term: str) -> None:
    # Groq copies examples: a measured rule in the prompt would pass without the rule working
    assert term not in PROMPTS["architecture"]
