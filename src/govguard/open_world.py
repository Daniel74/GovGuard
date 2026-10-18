"""Open world: what the input does not mention may be settled elsewhere (ADR 0020, #46).

The code decides the world, never the model. Closed is only a template the code can parse:
there a missing setting means the default. Pure logic.
"""

from dataclasses import dataclass

from govguard.models import AuditType
from govguard.text import template_resource_types


@dataclass(frozen=True)
class OpenWorld:  # wording of the audit prompt rule and the FAIL judge
    subject: str  # rule: "<subject> (offene Welt): ..."
    audit_of: str  # judge: "Du prüfst FAIL-Befunde aus dem Audit <audit_of>."
    subject_sentence: str  # judge: "<subject_sentence> ist eine offene Welt"
    confirmed: str  # judge: example the judge confirms, criterion and evidence lines
    rejected: str  # judge: same criterion, evidence lines that stay silent


SPEC = OpenWorld(
    subject="Spezifikation",
    audit_of="einer fachlichen Spezifikation",
    subject_sentence="Eine Spezifikation",
    confirmed='Kriterium "legt als Exportformat nur PDF fest", Beleg "Der Export erfolgt\n'
              '  ausschließlich als PDF."',
    rejected='gleiches Kriterium, Beleg "Bürger können ihre Daten exportieren."',
)
FREE_TEXT_ARCHITECTURE = OpenWorld(
    subject="Architekturbeschreibung",
    audit_of="einer Architekturbeschreibung in Freitext",
    subject_sentence="Eine Architekturbeschreibung",
    confirmed='Kriterium "legt fest, dass der Bucket unverschlüsselt ist", Beleg "Die\n'
              '  Bescheide liegen unverschlüsselt im S3-Bucket."',
    rejected='gleiches Kriterium, Beleg "Die Bescheide liegen in einem S3-Bucket."',
)


@dataclass(frozen=True)
class AuditInput:  # the input text and the world the code decided for it
    text: str
    world: OpenWorld | None  # None: closed world, a template


def audit_input(audit_type: AuditType, text: str) -> AuditInput:
    """Spec: always open. Architecture: open unless CloudFormation JSON, like the inventory.

    YAML and Terraform count as free text until the code parses them (#48, ADR 0015).
    """
    if audit_type == "spec":
        return AuditInput(text, SPEC)
    closed = template_resource_types(text) is not None
    return AuditInput(text, None if closed else FREE_TEXT_ARCHITECTURE)
