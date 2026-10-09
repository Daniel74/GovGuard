# 0006 – CloudWatch Logs als Audit-Protokoll

## Kontext

Ein Auditor soll jeden Aufruf nachvollziehen können: wann, mit welcher Wissensbasis, welchem Modell und welchem Ergebnis (SPEC US 6). Zur Wahl standen CloudWatch Logs, S3 mit Object Lock über den eigenen Archetyp ARCH-03 und „nur im Report“. Eingaben können personenbezogene Daten enthalten.

## Entscheidung

- Je Aufruf schreibt der Lambda-Handler genau ein JSON-Ereignis `AuditEvent` in die Log-Gruppe der Funktion, auch bei 422 und 502.
- Inhalt: IDs, Hashes (`input_sha256`, `catalog_sha256`), `kb_commit`, `model_id` und Status je Prüfregel. Kein Eingabetext, keine Belege und Begründungen, denn sie zitieren die Eingabe.
- Die Log-Gruppe ist mit dem vorhandenen KMS-Schlüssel verschlüsselt und hält die Ereignisse 365 Tage. Ausgewertet wird mit Logs Insights; der Auditor darf per IAM nur diese Log-Gruppe lesen.

## Konsequenzen

- 0 € im Leerlauf, je Ereignis ca. 2 KB, also Bruchteile eines Cents; kein boto3-Aufruf, der Handler loggt nur.
- Nicht revisionssicher: Wer `logs:DeleteLogGroup` darf, kann löschen. In Produktion übernimmt ARCH-03 (S3 Object Lock).
- Die KMS-Key-Policy muss dem Dienst `logs.eu-central-1.amazonaws.com` die Nutzung erlauben.

## Fachgespräch-Satz

„Jedes Urteil ist über `catalog_sha256` und `kb_commit` bis zur Regelwerksversion rückverfolgbar, ohne dass ich die Eingabe speichere – Nachvollziehbarkeit und Datenminimierung schließen sich nicht aus.“
