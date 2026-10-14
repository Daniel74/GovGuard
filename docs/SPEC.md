# GovGuard – Spezifikation (MVP)

**Ziel:** GovGuard prüft Spezifikationen gegen DSGVO/SDM und Architekturen gegen BSI Grundschutz++, BSI C5, CIS AWS und AWS FSBP und liefert einen Audit-Report mit belegten Befunden. Ohne FAIL im Spec-Audit schlägt er einen freigegebenen Golden Archetype vor. Begriffe: [CONTEXT.md](../CONTEXT.md), Entscheidungen: [adr/](adr/). **Priorität:** erst die Audits, die Golden Archetypes nur, wenn Zeit bleibt (FAHRPLAN).

## User Stories

1. Als Architekt lasse ich eine Spezifikation auditieren und sehe pro Prüfregel Status, Beleg und Empfehlung.
2. Als Architekt lasse ich eine Architektur (Freitext, Terraform oder CloudFormation) auditieren, auch wenn sie keinem Golden Archetype ähnelt. Nur CloudFormation-JSON hat ein Ressourceninventar per Code; Terraform und YAML gelten als Freitext und sind nicht getestet (ADR 0015).
3. Als Architekt erhalte ich bei einer Spezifikation ohne FAIL einen Golden Archetype (CDK-Code + Template) mit Begründung – oder „kein passender Archetyp“. _(Priorität B)_
4. Als CI-Pipeline rufe ich die Audit-API (IAM-Auth) auf und werte den Gesamtstatus maschinell aus.
5. Als Projektbetreiber starte ich den Build der Wissensbasis manuell; nur bei grünen Gates öffnet er einen Pull Request, und erst dessen Merge rollt die Wissensbasis aus.
6. Als Auditor kann ich zu jedem Aufruf nachvollziehen, wann er lief, mit welcher Wissensbasis und welchem Modell geprüft wurde und mit welchem Ergebnis.

## Akzeptanzkriterien

- Die 5 Presets liefern ihren Soll-Gesamtstatus und ihre Pflicht-Befunde.
- Jede extrahierte Anforderung hat genau einen Eintrag im Auswahlprotokoll mit Begründung; die aufgenommenen ergeben genau den Bounded Catalog.
- Jeder `cfn_resource_type` im Auswahlprotokoll ist ein echter CloudFormation-Typ (`data/input/cfn_resource_types.json`); das LLM kann keine erfinden.
- Jeder Audit-Report hat genau einen Befund je Prüfregel; jeder Beleg steht wörtlich in der Eingabe.
- Jede Architektur-Prüfregel ist relevant (erster Ressourcentyp im Prüfumfang), jede Komponente der Golden Archetypes hat mindestens eine Prüfregel, und die Pflichtanker der Presets stehen im Bounded Catalog (ADR 0011).
- Das größte Preset (≤ 100.000 Zeichen) ist innerhalb des Lambda-Timeouts von 180 Sekunden ausgewertet (ADR 0018).
- Ein Audit des größten Presets kostet höchstens 1,20 $ mit Bedrock (Haiku 4.5 `eu.`) bzw. 0,15 $ mit Groq (gemessen 14.10.2026: 0,95–1,05 $ bzw. 0,10 $, #26). GovGuard hat 0 € Leerlaufkosten; Fixkosten fallen nur für Sicherheit an (KMS-Schlüssel ca. 1 $/Monat).
- Das Selbst-Audit des GovGuard-Stacks hat kein FAIL und kein WARN, außer Ausnahmen (ADR 0011).
- _(Priorität B)_ Alle 3 Golden Archetypes sind freigegeben: Architektur-Audit ohne FAIL und WARN, cdk-nag ohne Errors, jeweils außer Ausnahmen (ADR 0007, ADR 0011).
- Jeder Aufruf erzeugt ein Audit-Ereignis in CloudWatch Logs mit `audit_id`, Zeit, `input_sha256`, `catalog_sha256`, `kb_commit`, `model_id` und Ergebnis, ohne Eingabetext.

## Aufnahme in den Bounded Catalog

Jede Anforderung jeder Quelle bekommt genau einen Eintrag im **Auswahlprotokoll** (`data/intermediate/verdicts_<arch|spec>.json`, versioniert). Das LLM urteilt nur über „prüfbar“, Ebene der Pflicht und Ressourcentypen. Über die Aufnahme entscheidet der Code (ADR 0011).

| Ergebnis | Bedeutung | Entscheidet |
|---|---|---|
| `selected` | prüfbar und relevant, steht im Bounded Catalog | Code |
| `prefiltered` | vom Vorfilter verworfen, mit festem Begründungssatz (z. B. „Praktik SENS liegt außerhalb des Architektur-Audits“) | Code |
| `not_relevant` | Architektur: die Pflicht liegt nicht am Template, sondern bei Konto, Personen oder Anbieter (z. B. CIS 4.4, MFA für Admins), oder der erste Ressourcentyp liegt nicht im Prüfumfang (z. B. EC2-Instanz) | Code |
| `not_testable` | an einer Spezifikation bzw. einem Template nicht entscheidbar | LLM |
| `llm_error` | Antwort auch nach zwei Retries ungültig (z. B. erfundener Ressourcentyp); die Anforderung ist ausgeschlossen und im Protokoll sichtbar. Bei einem Pflichtanker bricht der Build ab | Code |

Vor den Prüfregeln liest der Projektbetreiber das Auswahlprotokoll (Kontrollpunkt, FAHRPLAN Schritt 6). Fehlt etwas Wichtiges bei `not_testable` oder `not_relevant`, werden Prompt oder Prüfumfang angepasst.

## Offene Fragen

- Wie viele Prüfregeln umfasst der Katalog mit FSBP und C5, und was kostet damit ein Audit? Das zeigt der erste Lauf.
- Dürfen kurze Zitate aus FSBP (AWS-Doku) und C5 (© BSI) ins Repo? Bis zur Klärung gilt die Regel für CIS (ADR 0008).
