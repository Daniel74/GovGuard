# 10 – Zahlen und Beispiele auf einen Blick

Stand: Commit `28b62e7`. Alle Zahlen aus den Dateien in `data/` und den Issue-Kommentaren; Zahlen aus Läufen sind Momentaufnahmen und ändern sich bei jedem Neulauf.

## Trichter der Architektur-Auswahl (1.966 Anforderungen)

| Quelle | gesamt | Vorfilter verwirft | nicht prüfbar | nicht relevant | `llm_error` | aufgenommen |
|---|---|---|---|---|---|---|
| BSI | 1000 | 620 | 341 | 4 | 1 | **34** |
| C5 | 610 | 310 | 291 | 3 | 0 | **6** |
| CIS | 70 | 16 | 31 | 2 | 1 | **20** |
| FSBP | 286 | 136 | 44 | 0 | 0 | **106** |
| Summe | 1966 | 1082 | 707 | 9 | 2 | **166** |

## Trichter der Spec-Auswahl (246 Anforderungen)

| Quelle | gesamt | Vorfilter verwirft | nicht prüfbar | aufgenommen |
|---|---|---|---|---|
| DSGVO | 99 | 53 | 11 | **35** |
| SDM | 147 | 0 | 31 | **116** |
| Summe | 246 | 53 | 42 | **151** |

Endergebnis: `rules_arch.json` 166 Prüfregeln, `rules_spec.json` 151 Prüfregeln, beide mit Modell `openai/gpt-oss-120b`. Quellversionen im Katalog: BSI Commit `c96d9f57…`, C5 und FSBP `5.44.0`, CIS `v7.0.0`, DSGVO `000.003`, SDM `V1.0a, V1.0, V1.0`.

## Vorfilter-Ergebnis je Quelle (Extraktion)

BSI 1000 → 380 · C5 610 → 300 · CIS 70 → 54 · FSBP 286 → 150 · DSGVO 99 → 46 · SDM 147 → 147.

## Referenzdaten

- Prüfumfang: 23 Dienste, 106 CloudFormation-Typen; Schnappschuss `cfn_properties.json`: 106 Typen.
- Steckbriefe: ARCH-01 (RestApi, Lambda, DynamoDB), ARCH-02 (RestApi, Lambda, SQS, S3), ARCH-03 (RestApi, Lambda, Firehose, S3).
- 5 Presets (3 Architektur, 2 Spec), 7 verschiedene Pflichtanker.
- Judgement-Cache: 4.363 Einträge.
- Häufigste Typen in den Architektur-Regeln: `AWS::RDS::DBInstance` 27, `AWS::S3::Bucket` 21, `AWS::RDS::DBCluster` 21, `AWS::IAM::Policy` 17, `AWS::IAM::Role` 16, `AWS::EC2::SecurityGroup` 15.

## Kosten und Stabilität (aus den Issues)

| Messwert | Wert | Quelle |
|---|---|---|
| Erster echter Lauf, Auswahl (Groq) | 1.087 Anfragen, 584.357 Eingabe-, 307.020 Ausgabe-Token, ca. 0,32 $ | Issue #6 |
| Spec-Läufe nach Prompt-Korrekturen | je 193 Anfragen, ca. 0,06 $ | Issue #6 |
| Rücknahme aus dem Cache | 0 Anfragen | Issue #6 |
| Voller Neulauf Stufe ② | rund 960 Anfragen | ADR 0014 |
| Gekippte Urteile zwischen zwei Läufen | 41 von 1.077 (Arch 24, Spec 17) | ADR 0011, Issue #6 |
| Auswahlwechsel bei Neulauf mit Groq | rund 10 % | ADR 0014 |
| Auswahl nach #18 | 172 statt 189 Anforderungen | Issue #18 |
| Lauf #19: Regeln, die Typen verloren | 32 (15 Typen in 11 Regeln außerhalb des Prüfumfangs) | Issue #19 |
| Bedrock `eu.` Kapazität bei einem Lauf | dreimal HTTP 503 trotz 4 Wiederholungen | ADR 0012 |

## Echte Beispiele

### Anforderung → Verdict → Regel (FSBP SNS.1)

- Anforderung (`extracted/fsbp.json`): `SNS.1`, Titel „SNS topics should be encrypted at rest using AWS KMS“, Attribute `service: SNS`, `severity: medium`, Primäranker `AWS FSBP SNS.1`, Vorfilter bestanden.
- Verdict: `selected`, Typ `AWS::SNS::Topic`.
- Regel: `ARCH-FSBP-SNS.1` mit Kriterium auf `KmsMasterKeyId` (siehe Kapitel 06).
- Pflichtanker im Preset `arch-fristenwecker` (Soll: FAIL).

### CIS 3.1.4 (Block Public Access)

- Regel `ARCH-CIS-3.1.4`, Typ `AWS::S3::Bucket`, Kriterium: `PublicAccessBlockConfiguration` mit allen vier Flags `true`.
- Lehrstück (Issue #19): Als `AWS::S3::AccountPublicAccessBlock` im Prompt nicht genannt war, stufte das LLM die Anforderung als `account` ein und das Pflichtanker-Gate brach ab. Der Prompt nennt diesen Typ jetzt als Beispiel für „gilt zugleich für jede Ressource“ und lässt `template` wählen.

### Konto- und Personenpflichten raus (Issue #18)

- CIS `4.4` (Server Access Logging am CloudTrail-Bucket): `not_relevant`, „Die Pflicht liegt beim Konto oder der Organisation, nicht am Template.“
- C5 `OPS-16.01B`: `not_relevant`, „Die Pflicht liegt bei Personen oder Prozessen, nicht am Template.“

### Erfundene Eigenschaft (Issue #17)

- CIS 4.4 verlangte `TargetPrefix`, CloudFormation kennt am `AWS::S3::Bucket` aber nur `LogFilePrefix` (unter `LoggingConfiguration`). Der Schnappschuss-Abgleich schickt das Modell mit echten Alternativen zurück.

### Spec-Beispiele

- `SPEC-DSGVO-Art.32` (siehe Kapitel 06). Presets: `spec-meldeportal-gesundheit` (Soll FAIL; Pflichtanker DSGVO Art. 9 und SDM Löschen M60.P01), `spec-wohngeld-openapi` (Soll WARN, erwarteter Archetyp ARCH-02).

### Presets (Soll)

| Preset | Art | Soll-Gesamtstatus | Pflichtanker |
|---|---|---|---|
| `arch-antragseingang-fehlerhaft` | Architektur | FAIL | CIS 3.1.4 FAIL, CIS 4.6 FAIL, BSI BER.4.1 FAIL |
| `arch-fristenwecker` | Architektur | FAIL | FSBP SNS.1 FAIL, FSBP StepFunctions.1 PASS |
| `arch-protokollarchiv` | Architektur | WARN | CIS 3.1.4 PASS |
| `spec-meldeportal-gesundheit` | Spec | FAIL | DSGVO Art. 9 FAIL, SDM Löschen M60.P01 FAIL |
| `spec-wohngeld-openapi` | Spec | WARN | – (Archetyp ARCH-02) |

## Hinweis zu den Zahlen

Die Mini-Differenzen zwischen Issue-Kommentaren und Dateien (z. B. 183 aufgenommene im ersten Lauf, 166 heute) erklären sich durch spätere Läufe (#18, #19, #21). Maßgeblich sind die Dateien in `data/`.
