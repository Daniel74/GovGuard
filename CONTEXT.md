# GovGuard

Compliance-Copilot, der Spezifikationen gegen DSGVO/SDM und Architekturen gegen BSI/CIS prüft und einen passenden Golden Archetype vorschlägt.

## Wissensbasis

- **Wissensbasis**: Gesamtheit aller Prüfregeln und Golden Archetypes. _Vermeiden_: Knowledge Base, Index, Seeds
- **Quelle**: Regelwerk, aus dem Prüfregeln abgeleitet werden (DSGVO, SDM, BSI Grundschutz++, CIS AWS). _Vermeiden_: Framework, Datensatz
- **Anforderung**: Einzelne, zitierfähige Vorgabe innerhalb einer Quelle, z. B. BSI DET.3.1 oder DSGVO Art. 9. _Vermeiden_: Control, Kontrolle, Baustein
- **Prüfregel**: Atomare, prüfbare Regel aus genau einer Anforderung, mit Kriterien für „konform“ und „Verstoß“. _Vermeiden_: Chunk, Unified Audit Rule, Regel
- **Primäranker**: Die eine Anforderung, aus der eine Prüfregel abgeleitet ist. _Vermeiden_: Anchor, Referenz
- **Querverweis**: KI-vorgeschlagener, nicht verifizierter Bezug einer Prüfregel auf eine Anforderung einer anderen Quelle; beeinflusst keinen Status. _Vermeiden_: Mapping
- **Bounded Catalog**: Fest begrenzte Menge an Prüfregeln je Audit-Art, die in jedem Audit vollständig bewertet wird. _Vermeiden_: Top-K, Retrieval-Set
- **Golden Archetype**: Vorab auditierte und freigegebene Referenzarchitektur für ein wiederkehrendes Behörden-Workload-Muster. _Vermeiden_: Pattern, Blueprint, Vorlage
- **Freigabe**: Zustand eines Golden Archetype, der das Architektur-Audit und eine unabhängige deterministische Prüfung ohne Beanstandung bestanden hat.

## Audit

- **Spezifikation**: Fachliche Beschreibung eines Vorhabens (Freitext oder OpenAPI); Eingabe des Spec-Audits. _Vermeiden_: Spec-Dokument, Anforderungsdokument
- **Architektur**: Technische Beschreibung eines Systems (Freitext, Terraform oder CloudFormation); Eingabe des Architektur-Audits. _Vermeiden_: Design, Infrastruktur
- **Spec-Audit**: Prüfung einer Spezifikation gegen die Prüfregeln aus DSGVO und SDM. _Vermeiden_: Spec Review, Evaluation
- **Architektur-Audit**: Prüfung einer Architektur gegen die Prüfregeln aus BSI und CIS. _Vermeiden_: Architecture Review, Evaluation
- **Befund**: Ergebnis genau einer Prüfregel in einem Audit, mit Status, Beleg und Empfehlung. _Vermeiden_: Finding, Issue
- **Status**: PASS (Einhaltung belegt), WARN (aus der Eingabe nicht entscheidbar, Prüfbedarf), FAIL (Verstoß belegt) oder N/A (nicht anwendbar).
- **Beleg**: Wörtliches Zitat aus der Eingabe, auf das sich ein Befund stützt. _Vermeiden_: Evidence, Nachweis
- **Gesamtstatus**: Der schlechteste Status aller Befunde eines Audits.
- **Audit-Report**: Gesamtstatus plus genau ein Befund je Prüfregel des Bounded Catalog. _Vermeiden_: Prüfbericht, Ergebnis
- **Preset**: Fiktive Beispiel-Eingabe mit festgelegtem Soll-Ergebnis für Demo und Test. _Vermeiden_: Testfall, Beispiel
