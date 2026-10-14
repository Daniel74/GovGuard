# GovGuard

Compliance-Copilot, der Spezifikationen gegen DSGVO/SDM und Architekturen gegen BSI/CIS prüft und einen passenden Golden Archetype vorschlägt.

_Code_ nennt den englischen Bezeichner im Quellcode. _Vermeiden_ gilt für Doku und Gespräch.

## Wissensbasis

- **Wissensbasis**: Gesamtheit aller Prüfregeln und Golden Archetypes. _Code_: `knowledge_base`. _Vermeiden_: Knowledge Base, Index, Seeds
- **Quelle**: Regelwerk, aus dem Prüfregeln abgeleitet werden (DSGVO, SDM, BSI Grundschutz++, BSI C5, CIS AWS, AWS FSBP). _Code_: `Source`. _Vermeiden_: Framework, Datensatz
- **Anforderung**: Einzelne, zitierfähige Vorgabe innerhalb einer Quelle, z. B. BSI DET.3.1 oder DSGVO Art. 9. _Code_: `Requirement`. _Vermeiden_: Control, Kontrolle, Baustein
- **Prüfregel**: Atomare, prüfbare Regel aus genau einer Anforderung, mit Kriterien für „konform“ und „Verstoß“. _Code_: `Rule`. _Vermeiden_: Chunk, Unified Audit Rule, Regel
- **Primäranker**: Die eine Anforderung, aus der eine Prüfregel abgeleitet ist. _Code_: `primary_anchor`. _Vermeiden_: Anchor, Referenz
- **Querverweis**: KI-vorgeschlagener, nicht verifizierter Bezug einer Prüfregel auf eine Anforderung einer anderen Quelle; beeinflusst keinen Status. _Code_: `cross_reference`. _Vermeiden_: Mapping
- **Bounded Catalog**: Zur Build-Zeit festgelegte Menge aller prüfbaren und relevanten Prüfregeln je Audit-Art, die in jedem Audit vollständig bewertet wird. _Code_: `catalog`. _Vermeiden_: Top-K, Retrieval-Set
- **Auswahlprotokoll**: Je Anforderung einer Quelle das Ergebnis der Auswahl (aufgenommen oder verworfen) mit Begründung, vom LLM oder vom Code. _Code_: `verdicts`. _Vermeiden_: Verdict, Log
- **Prüfumfang**: Feste Liste der AWS-Dienste samt Begleittypen (AWS Backup, Application Auto Scaling), für die das Architektur-Audit Prüfregeln führt; Prüfregeln nennen nur Typen daraus. _Code_: `scope`. _Vermeiden_: Scope, Whitelist
- **Begleittyp**: Ressourcentyp, den ein Dienst im Prüfumfang braucht, ohne selbst Workload zu sein (AWS Backup, Application Auto Scaling). _Code_: companion type (Kommentare, Tests)
- **Relevant**: Eine Anforderung ist relevant, wenn nach dem Streichen der Typen außerhalb des Prüfumfangs einer übrig bleibt und ihre Ebene `template` ist; Bedingung für die Aufnahme neben „prüfbar“. _Code_: Ergebnis `not_relevant`, `scope_level`
- **Ebene**: Wessen Pflicht eine Anforderung ist: Workload (`template`), Konto/Organisation (`account`), Personen (`people`) oder Cloud-Anbieter (`provider`); nur `template` kommt ins Architektur-Audit. _Code_: `scope_level`. _Vermeiden_: Scope (gehört dem Prüfumfang)
- **Komponente**: AWS-Dienst, aus dem ein Golden Archetype besteht, z. B. API Gateway, Lambda, SQS. _Code_: `required_types`. _Vermeiden_: Baustein (gehört dem SDM)
- **Golden Archetype**: Vorab auditierte und freigegebene Referenzarchitektur für ein wiederkehrendes Behörden-Workload-Muster, als vollständige Kette vom API-Eingang bis zur Ablage, ohne Portal. _Code_: `Archetype`. _Vermeiden_: Pattern, Blueprint, Vorlage
- **Freigabe**: Zustand eines Golden Archetype, der das Architektur-Audit und eine unabhängige deterministische Prüfung ohne Beanstandung bestanden hat; erlaubt sind nur Ausnahmen. _Code_: `approved`
- **Ausnahme**: Begründeter, von Hand gepflegter Eintrag in einer Allowlist, der einem Golden Archetype oder dem GovGuard-Stack einen nicht behebbaren cdk-nag-Error oder den Verstoß gegen eine bewusst nicht erfüllte Prüfregel erlaubt. _Code_: `NagException`. _Vermeiden_: Suppression, Acknowledge

## Audit

- **Spezifikation**: Fachliche Beschreibung eines Vorhabens (Freitext oder OpenAPI); Eingabe des Spec-Audits. _Code_: `spec`. _Vermeiden_: Spec-Dokument, Anforderungsdokument
- **Architektur**: Technische Beschreibung eines Systems (Freitext, Terraform oder CloudFormation; nur CloudFormation-JSON hat ein Code-Inventar, Terraform ist ungetestet, ADR 0015); Eingabe des Architektur-Audits. _Code_: `architecture`. _Vermeiden_: Design, Infrastruktur
- **Spec-Audit**: Prüfung einer Spezifikation gegen die Prüfregeln aus DSGVO und SDM. _Code_: `spec_audit`. _Vermeiden_: Spec Review, Evaluation
- **Architektur-Audit**: Prüfung einer Architektur gegen die Prüfregeln aus BSI Grundschutz++, BSI C5, CIS und AWS FSBP. _Code_: `architecture_audit`. _Vermeiden_: Architecture Review, Evaluation
- **Befund**: Ergebnis genau einer Prüfregel in einem Audit, mit Status, Beleg und Empfehlung. _Code_: `Finding`. _Vermeiden_: Finding, Issue
- **Status**: PASS (Einhaltung belegt), WARN (aus der Eingabe nicht entscheidbar oder von der KI nicht belegt und herabgestuft, Prüfbedarf), FAIL (Verstoß belegt) oder N/A (nicht anwendbar). _Code_: `Status`
- **Ressourceninventar**: Menge der Ressourcentypen, die in einer Architektur vorkommen; der Code liest sie nur aus CloudFormation-JSON, bei Freitext, YAML und Terraform nennt sie das LLM mit Beleg (ADR 0015). _Code_: `Inventory` (`resource_inventory()`, CloudFormation: `template_resource_types()`). _Vermeiden_: Dienstliste
- **Anwendbar**: Eine Prüfregel ist in einem Audit anwendbar, wenn mindestens einer ihrer Ressourcentypen im Ressourceninventar vorkommt, bei Freitext außerdem immer für IAM, KMS und Logs; sonst setzt der Code N/A. _Code_: `Inventory.applies`. _Vermeiden_: relevant (gilt zur Build-Zeit)
- **Beleg**: Wörtlicher Ausschnitt der Eingabe, auf den sich ein Befund stützt; im Audit nennt das LLM nur den Zeilenbereich, der Code schneidet ihn aus (ADR 0017). _Code_: `evidence` (`line_start`, `line_end`). _Vermeiden_: Evidence, Nachweis
- **Gesamtstatus**: Der schlechteste Status aller Befunde eines Audits. _Code_: `overall_status`
- **Audit-Report**: Gesamtstatus plus genau ein Befund je Prüfregel des Bounded Catalog. _Code_: `AuditReport`. _Vermeiden_: Prüfbericht, Ergebnis
- **Rückverfolgung**: Angaben, die einen Audit-Report eindeutig mit Eingabe (nur als Hash), Wissensbasis-Version und Deploy verbinden. _Code_: `Trace`. _Vermeiden_: Tracing, Metadaten
- **Audit-Ereignis**: Protokolleintrag zu genau einem Aufruf mit Rückverfolgung und Status je Prüfregel, ohne Eingabetext und ohne Belege. _Code_: `AuditEvent`. _Vermeiden_: Log, Logeintrag, Audit-Log
- **Preset**: Fiktive Beispiel-Eingabe mit festgelegtem Soll-Ergebnis für Demo und Test. _Code_: `Preset`. _Vermeiden_: Testfall, Beispiel, Szenario

## Betrieb

- **Leerlaufkosten**: Kosten, die ohne Anfragen allein durch Zeit entstehen; Speicher für gehaltene Daten und Fixkosten für Sicherheit (KMS-Schlüssel, Secret) zählen nicht dazu. GovGuard und jeder Golden Archetype haben 0 € Leerlaufkosten. _Code_: –. _Vermeiden_: Idle-Kosten, Grundgebühr
