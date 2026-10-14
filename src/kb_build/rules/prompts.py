"""Prompts of the formulate step: one per audit type, plus the user prompt (#29).

Only the spec prompt asks for a stipulation as violation: open world (ADR 0020).
"""

from govguard.models import AuditType

PROMPT = """\
Du formulierst aus genau einer Anforderung eines Regelwerks für Behörden-IT genau eine
Prüfregel für ein {audit}. Inhalte auf Deutsch, außer dem Zitat.
- "source_quote": wörtlicher Auszug aus dem Text in <anforderung>, der die Kernpflicht trägt:
  ein Satz oder Satzteil, mind. 15 Zeichen und höchstens 25 Wörter, Zeichen für Zeichen
  kopiert. Original-Sprache, nichts übersetzen, kürzen, ergänzen oder grammatisch anpassen.
- "title": kurzer Titel, höchstens 8 Wörter.
- "compliant_if" / "violation_if": je ein Satz, woran man {subject} Einhaltung bzw. Verstoß
  erkennt.
- "recommendation": ein Satz zur Abhilfe.
- "cross_references": nur Anforderungen einer anderen Quelle, die du sicher kennst, im exakten
  Format, z. B. "BSI GS++ DET.3.1", "DSGVO Art. 32", "AWS FSBP S3.1". Im Zweifel leer lassen."""

ARCHITECTURE_CRITERIA = """
- Architektur: "compliant_if" und "violation_if" nennen mindestens einen der Ressourcentypen
  wörtlich (z. B. AWS::RDS::DBInstance) und die konkrete Eigenschaft mit Wert (z. B.
  DeletionProtection: true). Keine Wörter, die Wissen außerhalb des Templates brauchen, z. B.
  "relevant", "erforderlich", "angemessen", "entsprechend". Gilt die Pflicht nur für eine
  Variante (z. B. bestimmte Engines oder Protokolle), nenne diese Bedingung."""

SPEC_CRITERIA = """
- Spezifikation (offene Welt): Was sie nicht erwähnt, kann anderswo geregelt sein. Deshalb
  beschreibt "violation_if" eine Festlegung, die der Anforderung widerspricht, auch einen
  erklärten Verzicht oder Aufschub, nie ein Fehlen. Beispiel DSGVO Art. 20: "Die
  Spezifikation legt als Exportformat nur PDF fest oder erklärt, dass ein Datenexport
  entfällt oder erst später kommt.\""""

# Per audit type: the system prompt
PROMPTS: dict[AuditType, str] = {
    "architecture": PROMPT.format(audit="Architektur-Audit eines CloudFormation-Templates",
                                  subject="am Template") + ARCHITECTURE_CRITERIA,
    "spec": PROMPT.format(audit="Spec-Audit einer fachlichen Spezifikation",
                          subject="an der Spezifikation") + SPEC_CRITERIA,
}

USER_PROMPT = (
    "Quelle: {source}\nID: {id}\nTitel: {title}\nBegründung der Auswahl: {rationale}\n{types}"
    "<anforderung>\n{text}\n</anforderung>"
)
