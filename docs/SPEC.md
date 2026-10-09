# GovGuard – Spezifikation (MVP)

**Ziel:** GovGuard prüft Spezifikationen gegen DSGVO/SDM und Architekturen gegen BSI Grundschutz++/CIS AWS und liefert einen Audit-Report mit belegten Befunden. Ohne FAIL im Spec-Audit schlägt er einen freigegebenen Golden Archetype vor. Begriffe: [CONTEXT.md](../CONTEXT.md), Entscheidungen: [adr/](adr/).

## User Stories

1. Als Architekt lasse ich eine Spezifikation auditieren und sehe pro Prüfregel Status, Beleg und Empfehlung.
2. Als Architekt lasse ich eine Architektur (Freitext, Terraform oder CloudFormation) auditieren.
3. Als Architekt erhalte ich bei einer Spezifikation ohne FAIL einen Golden Archetype (CDK-Code + Template) mit Begründung – oder „kein passender Archetyp“.
4. Als CI-Pipeline rufe ich die Audit-API (IAM-Auth) auf und werte den Gesamtstatus maschinell aus.
5. Als Projektbetreiber starte ich den Build der Wissensbasis manuell; nur bei grünen Gates öffnet er einen Pull Request, und erst dessen Merge rollt die Wissensbasis aus.
6. Als Auditor kann ich zu jedem Aufruf nachvollziehen, wann er lief, mit welcher Wissensbasis und welchem Modell geprüft wurde und mit welchem Ergebnis.

## Akzeptanzkriterien

- Die 4 Presets liefern ihren Soll-Gesamtstatus und ihre Pflicht-Befunde.
- Jeder Audit-Report hat genau einen Befund je Prüfregel; jeder Beleg steht wörtlich in der Eingabe.
- Jede Architektur-Prüfregel betrifft mindestens einen Ressourcentyp der Golden Archetypes, und die Pflichtanker der Presets stehen im Bounded Catalog (ADR 0007).
- Das größte Preset (≤ 100.000 Zeichen) ist in unter 29 Sekunden ausgewertet.
- Ein Audit des größten Presets kostet unter 10 Cent (Haiku 4.5: ca. 1 $ Input / 5 $ Output je Mio. Token); im Leerlauf fallen keine variablen Kosten an, Fixkosten nur für den KMS-Schlüssel (ca. 1 $/Monat).
- Alle 3 Golden Archetypes sind freigegeben: Architektur-Audit ohne FAIL und WARN, cdk-nag ohne Errors außer Ausnahmen (ADR 0007).
- Jeder Aufruf erzeugt ein Audit-Ereignis in CloudWatch Logs mit `audit_id`, Zeit, `input_sha256`, `catalog_sha256`, `kb_commit`, `model_id` und Ergebnis, ohne Eingabetext.

## Offene Fragen

- Reicht das Standard-Timeout von 29 Sekunden? Das zeigt die Messung an Tag 2.
- Wie viele Anforderungen bleiben nach Vorfilter und Relevanzfilter übrig? Gemessen: BSI 380 nach dem Vorfilter.
