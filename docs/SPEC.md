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
- Zu jeder vom LLM beurteilten Anforderung gibt es ein Verdikt; `selected` und `pinned` ergeben genau die Auswahlliste.
- Jeder `cfn_resource_type` der Auswahlliste ist ein echter CloudFormation-Typ (`data/cfn_resource_types.json`); das LLM kann keine erfinden.
- Jeder Audit-Report hat genau einen Befund je Prüfregel; jeder Beleg steht wörtlich in der Eingabe.
- Jede Architektur-Prüfregel betrifft mindestens einen Ressourcentyp der Golden Archetypes, und die Pflichtanker der Presets stehen im Bounded Catalog (ADR 0007).
- Das größte Preset (≤ 100.000 Zeichen) ist in unter 29 Sekunden ausgewertet.
- Ein Audit des größten Presets kostet unter 10 Cent (Haiku 4.5: ca. 1 $ Input / 5 $ Output je Mio. Token); im Leerlauf fallen keine variablen Kosten an, Fixkosten nur für den KMS-Schlüssel (ca. 1 $/Monat).
- Alle 3 Golden Archetypes sind freigegeben: Architektur-Audit ohne FAIL und WARN, cdk-nag ohne Errors außer Ausnahmen (ADR 0007).
- Jeder Aufruf erzeugt ein Audit-Ereignis in CloudWatch Logs mit `audit_id`, Zeit, `input_sha256`, `catalog_sha256`, `kb_commit`, `model_id` und Ergebnis, ohne Eingabetext.

## Aufnahme in den Bounded Catalog

Jede Anforderung, die das LLM beurteilt hat, bekommt genau ein **Verdikt** (Bericht `data/knowledge_base/verdicts_<arch|spec>.json`, versioniert wie die Auswahlliste). Das LLM urteilt nur über „prüfbar“ und Ressourcentypen. Über die Aufnahme entscheidet der Code (ARCHITECTURE 1.1, ADR 0007).

| Verdikt | Bedeutung | Entscheidet |
|---|---|---|
| `pinned` | Pflichtanker eines Presets, immer im Katalog (höchstens 4 je Audit-Art); ist er nicht prüfbar, bricht der Build ab | Mensch |
| `selected` | prüfbar, relevant, Platz unter der Obergrenze (BSI 12, CIS 12, DSGVO 16, SDM 8) | Code |
| `over_cap` | prüfbar und relevant, aber kein Platz mehr frei | Code |
| `not_relevant` | Architektur: der erste Ressourcentyp gehört zu keinem Steckbrief (z. B. CloudTrail, RDS) | Code |
| `not_testable` | an einer Spezifikation bzw. einem Template nicht entscheidbar | LLM |
| `llm_error` | Antwort auch nach zwei Retries ungültig (z. B. erfundener Ressourcentyp); die Anforderung ist ausgeschlossen und im Bericht sichtbar. Bei einem Pflichtanker bricht der Build ab | Code |

Vor den Prüfregeln liest der Projektbetreiber Auswahlliste und Bericht (Kontrollpunkt, FAHRPLAN Schritt 6): Fehlt etwas Wichtiges bei `over_cap` oder `not_testable`, wird die Obergrenze oder der Prompt angepasst.

## Offene Fragen

- Reicht das Standard-Timeout von 29 Sekunden? Das zeigt die Messung an Tag 2.
- Wie viele Anforderungen bleiben nach Vorfilter und Relevanzfilter übrig? Gemessen (09.10.2026, gpt-oss-120b): Architektur von 425 beurteilten BSI 12 gewählt, 6 `over_cap`, 53 `not_relevant`; CIS nur 7 gewählt (Kandidaten erschöpft). Spec: DSGVO 19 und SDM 35 `over_cap`, darunter Art. 32.
- Reichen die Obergrenzen? Art. 32 (Verschlüsselung) lag über der alten DSGVO-Grenze von 12; sie ist jetzt 16. Die Grenze hängt am 29-s-Timeout (eine Antwort mit allen Befunden).
