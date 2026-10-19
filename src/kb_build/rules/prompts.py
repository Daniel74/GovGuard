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
- Architektur: "compliant_if" und "violation_if" beschreiben zuerst den Sachverhalt in Worten,
  dann woran man ihn im Template erkennt: mindestens einen der Ressourcentypen wörtlich und die
  Eigenschaft mit Wert, z. B. "Die Datenbank ist gegen Löschen geschützt
  (AWS::RDS::DBInstance mit DeletionProtection: true)."
- Gibt es mehrere übliche Umsetzungen, zähle sie auf; ein Verstoß liegt erst vor, wenn keine
  davon vorliegt. Konkrete Werte wie IP-Bereiche, Ports, ARNs, Tags oder Regionen nur, wenn
  die Anforderung sie nennt.
- Bedingungen in Policies erfüllen eine Pflicht in zwei Formen: Allow nur mit der Bedingung
  oder Deny mit der umgekehrten Bedingung. Zähle beide auf.
- Verlangt die Anforderung, etwas einzuschränken oder zu blockieren, prüfe das Gegenteil: was
  uneingeschränkt offen ist. "violation_if" nennt dann nur das Offene, nie das Fehlen einer
  zusätzlichen Sperr-Regel oder Ressource. Beispiel BSI ARCH.5.1 "Verbindungen zwischen IT-Systemen
  einschränken": Verstoß ist eine AWS::EC2::SecurityGroup mit einer Ingress-Regel für CidrIp
  0.0.0.0/0, nicht das Fehlen einer Security Group ohne Regeln.
- Keine Wörter, die Wissen außerhalb des Templates brauchen, z. B. "relevant",
  "erforderlich", "angemessen", "entsprechend", "gleichwertig". Gilt die Pflicht nur für eine
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
    "{kind}<anforderung>\n{text}\n</anforderung>"
)

# Per kind of a decomposed part (#53, ADR 0026); "alle_gelten" needs no hint: one duty, one rule
KIND_LINES: dict[str, str] = {
    "eine_genuegt": (
        "Art der Pflicht: Alternativen, eine genügt. \"compliant_if\": Die Spezifikation legt "
        "mindestens eine der Alternativen fest. \"violation_if\": Sie stützt sich auf etwas, "
        "das keine der Alternativen ist, oder schließt alle aus.\n"),
    "je_nach_risiko": (
        "Art der Pflicht: Maßnahme, soweit das Risiko sie erfordert. \"compliant_if\": Die "
        "Spezifikation sieht die Maßnahme vor oder begründet, warum das Risiko sie nicht "
        "erfordert. \"violation_if\": Sie schließt die Maßnahme trotz eines genannten Risikos "
        "aus.\n"),
}
