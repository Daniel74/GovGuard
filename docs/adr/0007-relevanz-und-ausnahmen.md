# 0007 – Relevante Prüfregeln und begründete Ausnahmen

## Kontext

Messungen vor Beginn der Umsetzung (2026-10-09) zeigen Lücken in ADR 0002 und 0003:

- Grundschutz++ vergibt MUSS nur an 30 organisatorische Controls. Alle technischen Anforderungen, z. B. DET.3.1, stehen auf SOLLTE. Der Vorfilter hätte keine einzige IaC-prüfbare BSI-Anforderung übrig gelassen.
- Der Tiebreak nach ID verzerrt das Ranking: Beim BSI haben 24 von 30 Kandidaten dieselbe CIA-Summe, bei der DSGVO fallen Art. 32 und 44 heraus.
- Kontoweite Regeln wie Root-MFA sind an einem Template nie entscheidbar. Sie liefern dauerhaft WARN und verhindern jede Freigabe.
- Spike mit Solutions Constructs und cdk-nag 3 (AwsSolutions): Es bleiben 4 Errors, ausgelöst durch CDK-interne Ressourcen und durch IAM-Auth (COG4).

## Entscheidung

- **Relevanz:** Stufe ② liefert zusätzlich `cfn_resource_types`. Ins Architektur-Ranking kommt nur, was sich mit `resource_types` der Steckbriefe überschneidet.
- **BSI-Vorfilter:** MUSS und SOLLTE bei `sec_level` = normal-SdT.
- **Gesetzte Plätze:** Die Pflichtanker der Presets stehen immer im Katalog, höchstens 4 je Katalog.
- **Ranking:** Die Obergrenze gilt je Quelle. Architektur reihum je Ressourcentyp, Spezifikation reihum je DSGVO-Kapitel bzw. SDM-Baustein. Innerhalb einer Gruppe gilt Tabelle 1.1, dann die ID.
- **N/A:** Bei CloudFormation setzt der Code N/A, wenn kein `cfn_resource_type` der Prüfregel im Template vorkommt.
- **Ausnahmen:** cdk-nag-Errors sind nur über die von Hand gepflegte Allowlist `data/nag_allowlist.json` erlaubt (Regel-ID, Pfad, Begründung). Angewendet wird sie vom Code, nie vom LLM. Das gilt für Archetypen und den GovGuard-Stack. LLM-Code enthält kein `acknowledge`. Startliste: COG4 (IAM-Auth), IAM4 `BucketNotificationsHandler`, IAM5 Firehose `bucket/*`. X-Ray bleibt aus.

## Konsequenzen

- Kontoweite Pflichten wie Root-MFA oder die Passwort-Policy prüft GovGuard nicht. Dafür gibt es Werkzeuge wie Prowler oder Security Hub.
- #3 kommt vor #6. #6 wird geteilt: Die Auswahlliste ist ein Kontrollpunkt, bevor Prüfregeln formuliert werden.
- Einwand „Katalog auf die Tests zugeschnitten“: Gesetzte Plätze sind auf 4 begrenzt und begründet, der Rest entsteht automatisch.
- Ob Lambda-Logging `log-group:NAME:*` braucht (IAM5), zeigt erst der Deploy. Falls ja, kommt eine weitere Ausnahme dazu.

## Fachgespräch-Satz

„Jede Prüfregel betrifft nachweislich einen Baustein unserer Archetypen, und jede cdk-nag-Ausnahme ist eine dokumentierte Abweichung mit Begründung – das LLM kann weder Regeln noch Ausnahmen erfinden.“
