# GovGuard

Compliance-Copilot, der Spezifikationen gegen DSGVO/SDM und Architekturen gegen BSI/CIS prüft und einen passenden Golden Archetype vorschlägt.

_Code_ nennt den englischen Bezeichner im Quellcode. _Vermeiden_ gilt für Doku und Gespräch.

## Wissensbasis

- **Wissensbasis**: Gesamtheit aller Prüfregeln und Golden Archetypes. _Code_: `knowledge_base`. _Vermeiden_: Knowledge Base, Index, Seeds
- **Quelle**: Regelwerk, aus dem Prüfregeln abgeleitet werden (DSGVO, SDM, BSI Grundschutz++, CIS AWS). _Code_: `Source`. _Vermeiden_: Framework, Datensatz
- **Anforderung**: Einzelne, zitierfähige Vorgabe innerhalb einer Quelle, z. B. BSI DET.3.1 oder DSGVO Art. 9. _Code_: `Requirement`. _Vermeiden_: Control, Kontrolle, Baustein
- **Prüfregel**: Atomare, prüfbare Regel aus genau einer Anforderung, mit Kriterien für „konform“ und „Verstoß“. _Code_: `Rule`. _Vermeiden_: Chunk, Unified Audit Rule, Regel
- **Primäranker**: Die eine Anforderung, aus der eine Prüfregel abgeleitet ist. _Code_: `primary_anchor`. _Vermeiden_: Anchor, Referenz
- **Querverweis**: KI-vorgeschlagener, nicht verifizierter Bezug einer Prüfregel auf eine Anforderung einer anderen Quelle; beeinflusst keinen Status. _Code_: `cross_reference`. _Vermeiden_: Mapping
- **Bounded Catalog**: Fest begrenzte Menge an Prüfregeln je Audit-Art, die in jedem Audit vollständig bewertet wird. _Code_: `catalog`. _Vermeiden_: Top-K, Retrieval-Set
- **Gesetzter Platz**: Platz im Bounded Catalog, den der Pflicht-Befund eines Preset unabhängig vom Ranking sichert, höchstens 4 je Katalog. _Code_: `pinned_anchors`. _Vermeiden_: Pin, Pflichtregel
- **Golden Archetype**: Vorab auditierte und freigegebene Referenzarchitektur für ein wiederkehrendes Behörden-Workload-Muster, als vollständige Kette vom API-Eingang bis zur Ablage, ohne Portal. _Code_: `Archetype`. _Vermeiden_: Pattern, Blueprint, Vorlage
- **Freigabe**: Zustand eines Golden Archetype, der das Architektur-Audit und eine unabhängige deterministische Prüfung ohne Beanstandung bestanden hat; erlaubt sind nur Ausnahmen. _Code_: `approved`
- **Ausnahme**: Begründeter, von Hand gepflegter Eintrag in der Allowlist `data/nag_allowlist.json`, der einen nicht behebbaren cdk-nag-Error erlaubt. _Code_: `NagException`. _Vermeiden_: Suppression, Acknowledge

## Audit

- **Spezifikation**: Fachliche Beschreibung eines Vorhabens (Freitext oder OpenAPI); Eingabe des Spec-Audits. _Code_: `spec`. _Vermeiden_: Spec-Dokument, Anforderungsdokument
- **Architektur**: Technische Beschreibung eines Systems (Freitext, Terraform oder CloudFormation); Eingabe des Architektur-Audits. _Code_: `architecture`. _Vermeiden_: Design, Infrastruktur
- **Spec-Audit**: Prüfung einer Spezifikation gegen die Prüfregeln aus DSGVO und SDM. _Code_: `spec_audit`. _Vermeiden_: Spec Review, Evaluation
- **Architektur-Audit**: Prüfung einer Architektur gegen die Prüfregeln aus BSI und CIS. _Code_: `architecture_audit`. _Vermeiden_: Architecture Review, Evaluation
- **Befund**: Ergebnis genau einer Prüfregel in einem Audit, mit Status, Beleg und Empfehlung. _Code_: `Finding`. _Vermeiden_: Finding, Issue
- **Status**: PASS (Einhaltung belegt), WARN (aus der Eingabe nicht entscheidbar, Prüfbedarf), FAIL (Verstoß belegt) oder N/A (nicht anwendbar). _Code_: `Status`
- **Beleg**: Wörtliches Zitat aus der Eingabe, auf das sich ein Befund stützt. _Code_: `evidence`. _Vermeiden_: Evidence, Nachweis
- **Gesamtstatus**: Der schlechteste Status aller Befunde eines Audits. _Code_: `overall_status`
- **Audit-Report**: Gesamtstatus plus genau ein Befund je Prüfregel des Bounded Catalog. _Code_: `AuditReport`. _Vermeiden_: Prüfbericht, Ergebnis
- **Rückverfolgung**: Angaben, die einen Audit-Report eindeutig mit Eingabe (nur als Hash), Wissensbasis-Version und Deploy verbinden. _Code_: `Trace`. _Vermeiden_: Tracing, Metadaten
- **Audit-Ereignis**: Protokolleintrag zu genau einem Aufruf mit Rückverfolgung und Status je Prüfregel, ohne Eingabetext und ohne Belege. _Code_: `AuditEvent`. _Vermeiden_: Log, Logeintrag, Audit-Log
- **Preset**: Fiktive Beispiel-Eingabe mit festgelegtem Soll-Ergebnis für Demo und Test. _Code_: `Preset`. _Vermeiden_: Testfall, Beispiel, Szenario
