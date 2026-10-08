# GovGuard – Spezifikation (MVP)

**Ziel:** GovGuard prüft Spezifikationen gegen DSGVO/SDM und Architekturen gegen BSI Grundschutz++/CIS AWS und liefert einen Audit-Report mit belegten Befunden. Ohne FAIL im Spec-Audit schlägt er einen freigegebenen Golden Archetype vor. Begriffe: [CONTEXT.md](../CONTEXT.md), Entscheidungen: [adr/](adr/).

## User Stories

1. Als Architekt lasse ich eine Spezifikation auditieren und sehe pro Prüfregel Status, Beleg und Empfehlung.
2. Als Architekt lasse ich eine Architektur (Freitext, Terraform oder CloudFormation) auditieren.
3. Als Architekt erhalte ich bei einer Spezifikation ohne FAIL einen Golden Archetype (CDK-Code + Template) mit Begründung – oder „kein passender Archetyp“.
4. Als CI-Pipeline rufe ich die Audit-API (IAM-Auth) auf und werte den Gesamtstatus maschinell aus.
5. Als Projektbetreiber erzeuge ich die Wissensbasis per Build-Skript neu; sie wird nur übernommen, wenn alle Gates grün sind.

## Akzeptanzkriterien

- Die 4 Presets liefern ihren Soll-Gesamtstatus und ihre Pflicht-Befunde.
- Jeder Audit-Report hat genau einen Befund je Prüfregel; jeder Beleg steht wörtlich in der Eingabe.
- Das größte Preset (≤ 100.000 Zeichen) ist in unter 29 Sekunden ausgewertet.
- Ein Audit kostet unter 1 Cent; im Leerlauf fallen keine variablen Kosten an, Fixkosten nur für den KMS-Schlüssel (ca. 1 $/Monat).
- Alle 3 Golden Archetypes sind freigegeben (Architektur-Audit und cdk-nag ohne Beanstandung).

## Offene Fragen

- Reicht das Standard-Timeout von 29 Sekunden? Das zeigt die Messung an Tag 2.
- Wie viele Anforderungen bleiben nach dem Vorfilter übrig (Basis für die Obergrenzen)?
