"""Quality checks of formulated rules: can a criterion be decided from a template? Pure code.

The validator sends violations back to the model; the report counts what is left per source.
"""

import re

from govguard.models import RuleCatalog
from kb_build.reference.cfn_properties import (
    TYPE_PATTERN,
    PropertyIndex,
    unjudged_types,
    unknown_properties,
)

# Words that need knowledge beyond the template, e.g. "nicht erforderlich" (BSI KONF.6.1)
_VAGUE = re.compile(
    r"\b(relevant|erforderlich|notwendig|angemessen|entsprechend|geeignet|ausreichend|"
    r"gegebenenfalls|ggf\.|unnötig|übermäßig|regelmäßig|sensibel|sensibl)\w*",
    re.IGNORECASE,
)


def vague_terms(text: str) -> list[str]:
    """The vague words in `text`, each once, in order of appearance."""
    return list(dict.fromkeys(m.group() for m in _VAGUE.finditer(text)))


# Duties of the account or the organisation: never decidable at one template; baseline for #18
_ACCOUNT_LEVEL = re.compile(
    r"CloudTrail|AWS Organizations|Root-(Benutzer|Konto)|Passwort-?Richtlinie|Password Policy",
    re.IGNORECASE,
)


def quality_report(catalog: RuleCatalog, properties: PropertyIndex) -> dict[str, dict[str, int]]:
    """Per source: rules, vague criteria, account-level duties, invented and unchecked properties.

    `unjudged_properties`: type outside data/input/cfn_properties.json, nobody checks.
    """
    report: dict[str, dict[str, int]] = {}
    for rule in catalog.rules:
        criteria = f"{rule.compliant_if} {rule.violation_if}"
        counts = report.setdefault(
            rule.source, {"rules": 0, "vague": 0, "account_level": 0, "unknown_properties": 0,
                          "unjudged_properties": 0}
        )
        counts["rules"] += 1
        counts["vague"] += bool(vague_terms(criteria))
        counts["account_level"] += bool(_ACCOUNT_LEVEL.search(TYPE_PATTERN.sub(' ', criteria)))
        counts["unknown_properties"] += bool(
            unknown_properties(criteria, rule.cfn_resource_types, properties)
        )
        counts["unjudged_properties"] += bool(
            unjudged_types(criteria, rule.cfn_resource_types, properties)
        )
    return dict(sorted(report.items()))
