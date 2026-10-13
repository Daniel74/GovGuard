# 03 – Prüfumfang und Referenzdaten

## Zweck

Das LLM darf nichts erfinden: keine Ressourcentypen, keine Eigenschaften, keine Dienste außerhalb dessen, was GovGuard prüfen will. Dafür gibt es **von Hand gepflegte Referenzdaten** in `data/input/`. Sie sind der Maßstab, gegen den Code die LLM-Antworten prüft. Dieses Kapitel erklärt sie, bevor Kapitel 04 bis 06 sie benutzen.

## Die fünf Referenzen

| Datei | Inhalt | Code | Wozu |
|---|---|---|---|
| `scope.json` | der **Prüfumfang**: 23 Dienste, 106 CloudFormation-Typen | `reference/scope.py:Scope` | bestimmt, was als „relevant“ gilt, und begrenzt die Typen der Prüfregeln |
| `cfn_resource_types.json` | alle echten CloudFormation-Typnamen (`aws cloudformation list-types`) | `reference/cfn_types.py:load_cfn_types` | erfundene Typen erkennen |
| `cfn_properties.json` | je Typ des Prüfumfangs alle echten Eigenschaftspfade (106 Typen) | `reference/cfn_properties.py` | erfundene Eigenschaften erkennen |
| `archetype_profiles.json` | Steckbriefe der Golden Archetypes ARCH-01 bis -03 mit Pflicht-Typen | `reference/archetype_profiles.py` | **Komponenten** für das Abdeckungs-Gate |
| `presets/<id>/preset.json` | 5 fiktive Beispiele mit von Hand festgelegtem Soll | `govguard/models.py:Preset` | **Pflichtanker** für das Pflichtanker-Gate |

## Prüfumfang (`scope.json`, ADR 0011 und 0013)

- Ein Dienst-Name zeigt auf eine Liste von CloudFormation-Typen, z. B. `"DynamoDB": ["AWS::DynamoDB::Table", "AWS::DynamoDB::GlobalTable"]`.
- Die 23 Dienste: API Gateway, Lambda, DynamoDB, SQS, SNS, S3, Kinesis Data Firehose, Kinesis Data Streams, Step Functions, EventBridge, Cognito, Secrets Manager, WAF, KMS, IAM, CloudWatch Logs, RDS/Aurora, ECS Fargate, ECR, Application/Network Load Balancer, VPC, AWS Backup, Application Auto Scaling.
- **Serverless plus** RDS/Aurora und Fargate, dazu das, was beide brauchen (VPC-Typen, ECR, ELBv2). Nicht dabei: EC2-Instanzen, EKS, CloudTrail, CloudFront, Classic Load Balancer (ADR 0011).
- **Begleittypen** (ADR 0013): AWS Backup und Application Auto Scaling gehören zum Prüfumfang, weil Dienste im Prüfumfang sie brauchen (FSBP DynamoDB.4 und RDS.26 verlangen Backup, DynamoDB skaliert über Auto Scaling). EFS, EBS-Volume und SSM-Parameter bleiben draußen (`docs/AUSBAU.md`).
- `Scope.types` liefert alle Typen, `Scope.outside(types)` die Typen außerhalb, jeden einmal in Reihenfolge.

## Echte Typen und echte Eigenschaften

- **Typen:** `load_cfn_types()` kennt alle echten Typnamen. Stufe ② verwirft Namen, die dort fehlen.
- **Eigenschaften:** `cfn_properties.json` entsteht aus `aws cloudformation describe-type` (ein Handbefehl, dokumentiert im README) und dem Befehl `python -m kb_build cfn-properties`. `property_paths()` läuft durch das JSON-Schema des Typs und sammelt alle Pfade wie `LoggingConfiguration.LogFilePrefix`; rekursive Definitionen werden nur einmal aufgefaltet. `write_snapshot()` arbeitet **fail closed**: Fehlt für einen Typ des Prüfumfangs das Schema, bricht es ab, weil dessen Prüfung sonst still ausfiele.
- **Warum Handbefehl statt boto3-Code im Build:** kostet nichts, läuft nur bei Bedarf, und boto3 bleibt auf `aws_services.py` beschränkt (Issue #17).
- **Eigenschafts-Kandidaten erkennen** (`property_candidates()`): Gesucht wird in den Kriterien nach Punktpfaden (`RedirectConfig.Protocol`), Namen mit Klein- und späterem Großbuchstaben (`SecurityPolicy`, `MultiAZ`) und Namen mit Akronym vorn (`SSEEnabled`). Einzelwörter bleiben bewusst außen vor, weil deutsche Nomen sonst Fehltreffer auslösen (`Encrypted`). Eine Stoppliste `NOT_PROPERTIES` (CloudFormation, DynamoDB, StringEquals …) und Namen von Ressourcentypen (`BucketPolicy`) sowie alles mit `AWS…` fallen heraus.

## Steckbriefe der Golden Archetypes

`archetype_profiles.json` nennt je Archetyp `required_types`:

- ARCH-01: API Gateway RestApi, Lambda Function, DynamoDB Table
- ARCH-02: RestApi, Lambda Function, SQS Queue, S3 Bucket
- ARCH-03: RestApi, Lambda Function, Firehose DeliveryStream, S3 Bucket

Die Vereinigung dieser Typen sind die **Komponenten** (`select/run.py`). Jede Komponente braucht mindestens eine Prüfregel (Abdeckungs-Gate, Kapitel 05). Die Archetypen selbst sind noch nicht gebaut.

## Presets und Pflichtanker

- 5 Presets: `arch-antragseingang-fehlerhaft`, `arch-fristenwecker`, `arch-protokollarchiv`, `spec-meldeportal-gesundheit`, `spec-wohngeld-openapi`.
- Jedes Preset hat ein **Soll-Ergebnis**: Gesamtstatus und `required_findings` (Anker plus PASS oder FAIL, nie WARN). Das Soll legt ein Mensch fest, nie ein früherer Lauf (sonst wäre der Test zirkulär; `learning/learning-records/0001-zirkulaerer-test.md`).
- `gates.py:pinned_anchors()` sammelt die Anker je Audit-Art. Das sind **7 verschiedene Pflichtanker**: Architektur CIS 3.1.4, CIS 4.6, BSI BER.4.1, AWS FSBP SNS.1, AWS FSBP StepFunctions.1; Spec DSGVO Art. 9, SDM Löschen M60.P01. (In den Presets stehen 8 Einträge, CIS 3.1.4 kommt zweimal vor.)

## Warum so

- **Ein Gate prüft nur so weit, wie seine Referenz reicht** (Merksatz ADR 0013). Deshalb muss der Prüfumfang die Referenz begrenzen: Ohne Schnappschuss für CloudTrail, CloudFront, Classic ELB oder WAF Classic blieben 16 Regeln ungeprüft (`unjudged_properties`).
- **Änderung am Prüfumfang heißt voller Lauf:** Die Typen aus `scope.json` fließen in die Prompt-Version des Caches ein (Kapitel 04). Ein neuer Typ macht den Cache ungültig; kein Nachfiltern.
- **Presets liegen unter `data/input/`,** weil sie von Hand gepflegt sind und als Testorakel dienen.

## Fachbegriffe

- **Prüfumfang** (`scope`): feste Liste der AWS-Dienste samt Begleittypen, für die Prüfregeln geführt werden.
- **Begleittyp:** Ressourcentyp, den ein Dienst braucht, ohne selbst Workload zu sein.
- **Schnappschuss** (Snapshot): eingefrorene Kopie einer externen Referenz im Repo, damit Build und Tests ohne AWS reproduzierbar laufen.
- **Komponente:** AWS-Dienst, aus dem ein Archetyp besteht.
- **Pflichtanker:** Anforderung, die ein Preset zwingend im Katalog verlangt.
- **Testorakel / zirkulärer Test:** Das Soll muss von außen kommen, sonst bestätigt ein Test nur sich selbst.

## Grenzen

- Der Prüfumfang ist eine bewusste Entscheidung, keine Vollständigkeit. Was fehlt, steht in `docs/AUSBAU.md`.
- Der Schnappschuss ist nur so aktuell wie der letzte Handbefehl.

## Fragen für das Fachgespräch

1. Warum gehören AWS Backup und Application Auto Scaling in den Prüfumfang, EFS aber nicht?
2. Woher kommt das Soll der Presets, und warum nicht aus einem früheren Lauf?
3. Wofür braucht der Build `cfn_properties.json`?
