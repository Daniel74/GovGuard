"""Architecture criteria must be decidable from the template alone. Pure code.

The validator of `formulate_rule` sends each problem back to the model (ADR 0005).
"""

from govguard.models import RuleDraft
from kb_build.reference.cfn_properties import (
    TYPE_PATTERN,
    PropertyIndex,
    alternatives,
    owners,
    unknown_properties,
)
from kb_build.rules.quality import vague_terms

MAX_OWNERS = 3  # types named in a retry hint: enough to choose from, short enough to read


def types_outside_scope(text: str, scope_types: frozenset[str]) -> list[str]:
    """The resource types named in `text` that the scope lacks, each once (#19)."""
    return [t for t in dict.fromkeys(TYPE_PATTERN.findall(text)) if t not in scope_types]


def criteria_problems(
    draft: RuleDraft, resource_types: list[str], properties: PropertyIndex,
    scope_types: frozenset[str],
) -> list[str]:
    criteria, problems = f"{draft.compliant_if} {draft.violation_if}", []
    vague = vague_terms(criteria)
    if vague:
        words = ", ".join(f"„{w}“" for w in vague)
        problems.append(f"Die Kriterien enthalten Wörter, die am Template nicht entscheidbar "
                        f"sind: {words}. Nenne stattdessen konkrete Eigenschaften und Werte.")
    outside = types_outside_scope(criteria, scope_types)
    if outside:
        problems.append(f"Diese Ressourcentypen liegen außerhalb des Prüfumfangs: "
                        f"{', '.join(outside)}. Nenne nur Typen der Prüfregel.")
    if not any(t in criteria for t in resource_types):
        problems.append("Die Kriterien nennen keinen Ressourcentyp der Prüfregel. Nenne "
                        f"mindestens einen davon wörtlich: {', '.join(resource_types)}.")
    for name in unknown_properties(criteria, resource_types, properties):
        options = ", ".join(alternatives(name, resource_types, properties))
        elsewhere = owners(name, properties)[:MAX_OWNERS]
        hint = (f" Sie gehört zu {', '.join(elsewhere)}; nenne diesen Typ dann wörtlich."
                if elsewhere else "")
        problems.append(f"„{name}“ gibt es in CloudFormation an den Typen der Prüfregel nicht."
                        f"{hint} Nimm nur echte Eigenschaften, z. B.: {options}.")
    return problems
