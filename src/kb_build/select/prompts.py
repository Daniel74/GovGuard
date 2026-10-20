"""Prompts of the classification: one per audit type, the scope sentence and the user prompt."""

from govguard.models import AuditType

PROMPTS: dict[AuditType, str] = {
    "architecture": """\
Du bewertest genau eine Anforderung aus einem Regelwerk für Behörden-IT.
Frage: Lässt sich ein Verstoß oder die Einhaltung an der Konfiguration von Ressourcen in einem
einzelnen CloudFormation-Template erkennen (z. B. IAM-Policies, Verschlüsselung, Logging,
Netzwerk, Zugriffsrechte)? Auch allgemeine Prinzipien wie "geringste Berechtigungen" zählen,
wenn sie sich an Ressourcen festmachen lassen. Nein gilt bei Verträgen und Prozessen.
- "testable": ja oder nein. "rationale": ein deutscher Satz zur Begründung.
- "scope_level": Wessen Pflicht ist das? "template" = das Workload selbst, am Template
  erkennbar (Bucket, Rolle, Funktion). "account" = Konto oder Organisation (CloudTrail-Bucket,
  Support-Rolle, Passwort-Richtlinie, Root-MFA). "people" = Personen und Prozesse
  (MFA für Administratoren, Schulung, Verträge). "provider" = Cloud-Anbieter (Rechenzentrum,
  Hypervisor).
  Hängt die Pflicht nur an Konto, Personen oder Anbieter, wähle das, auch wenn eine Ressource
  sie technisch umsetzen könnte, z. B. an einer bestimmten Konto-Ressource wie dem
  CloudTrail-Bucket. Gilt sie zugleich für jede Ressource des Workloads (z. B. Block Public
  Access an jedem Bucket), wähle "template", auch wenn es dafür eine Konto-Ressource wie
  AWS::S3::AccountPublicAccessBlock gibt.
- "cfn_resource_types": alle CloudFormation-Typen, an deren Konfiguration sich die Anforderung
  zeigt (z. B. bei Verschlüsselung jeder Speicher- und Transportdienst wie AWS::S3::Bucket,
  AWS::KinesisFirehose::DeliveryStream), der wichtigste zuerst. Nur Typen, die es in
  CloudFormation gibt. Ist die Anforderung nicht prüfbar, bleibt die Liste leer.""",
    "spec": """\
Du bewertest genau eine Anforderung aus einem Regelwerk für Behörden-IT.
Eine Spezifikation ist die fachliche Beschreibung eines Vorhabens, nicht nur die technische:
Sie nennt z. B. Zwecke, Rechtsgrundlagen, Rollen, Abläufe und Auftragsverarbeiter.
Frage: Kann eine Spezifikation (Freitext oder OpenAPI) Hinweise enthalten, ob die Anforderung
erfüllt oder verletzt wird, oder sich dazu bewusst ausschweigen? Dann ist sie prüfbar; fehlende
Angaben ergeben später eine Warnung. Beispiele: Rechtsgrundlagen, Zwecke, Löschfristen,
Verschlüsselung, Zugriffsrechte, Auftragsverarbeiter, Übermittlung in Drittländer; bei
KI-Systemen auch die Einstufung (z. B. Hochrisiko oder nicht), ausgeschlossene verbotene
Praktiken und die KI-Kompetenz der Nutzenden.
Nein gilt nur für Pflichten der Behörde, die keine Spezifikation berühren (z. B.
Bußgeldverfahren, Befugnisse der Aufsicht, Zertifizierung).
- "testable": ja oder nein. "rationale": ein deutscher Satz zur Begründung.
- "scope_level" bleibt "template". "cfn_resource_types" bleibt leer.""",
}

SCOPE_PROMPT = """\
Der Prüfumfang (Dienste, für die wir Prüfregeln führen) umfasst: {services}.
Typen außerhalb des Prüfumfangs verwirft der Code; nenne sie nicht. Bleibt kein Typ übrig,
gilt die Anforderung als nicht relevant."""

USER_PROMPT = "Quelle: {source}\nID: {id}\nTitel: {title}\n<anforderung>\n{text}\n</anforderung>"
