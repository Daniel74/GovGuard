# 0009 – Golden Archetypes als End-to-End-Ketten, ohne Portal

_Ergänzt [ADR 0003](0003-cdk-solutions-constructs.md)._

## Kontext

Presets sollen vollständige Vorhaben einer Behörde zeigen, z. B. Portal → API Gateway → Lambda → SQS → S3. In ADR 0003 waren zwei Archetypen nur Teilketten: ARCH-02 begann beim S3-Upload, ARCH-03 hatte keinen Aufrufer. Ein statisches Portal bräuchte in AWS CloudFront, denn S3-Website-Hosting kann nur HTTP und braucht einen öffentlichen Bucket. CloudFront hat keine Preisklasse nur für die EU: TLS endet an der Edge, möglicherweise in einem Drittland. Die AWS European Sovereign Cloud (GA 01/2026) plant CloudFront erst für Ende 2026 und bietet auf Bedrock kein Claude.

## Entscheidung

- Jeder Archetyp ist eine vollständige Kette ab API Gateway mit IAM-Auth (SigV4). Er besteht aus mehreren Solutions Constructs und wird zur Build-Zeit freigegeben, nie zur Laufzeit zusammengesetzt (ADR 0003).
- ARCH-01 Sync REST bleibt. ARCH-02 wird **Antragseingang** (API Gateway → Lambda → SQS → Lambda → S3). ARCH-03 Audit-Log-Archiv erhält vor Firehose den Eingang API Gateway → Lambda.
- Das Portal der Behörde liegt außerhalb jedes Archetyps. Eine Spezifikation nennt es nur als Aufrufer.

## Konsequenzen

- 2–4 Constructs je Archetyp: Der LLM-Code in #7 wird länger, das Risiko für Korrekturrunden steigt.
- COG4 gilt für die API-Methoden aller Archetypen. Die Ausnahme IAM4 `BucketNotificationsHandler` entfällt voraussichtlich mit `aws-s3-sqs`. Gestrichen wird sie erst, wenn #7 das zeigt.
- Ein Portal-Archetyp kommt erst, wenn CloudFront ohne Drittlandtransfer verfügbar ist ([AUSBAU](../AUSBAU.md), Szenario 5).

## Fachgespräch-Satz

„Unsere Archetypen decken das Backend vom API-Eingang bis zur Ablage vollständig ab – das Portal lassen wir bewusst draußen, weil CloudFront Daten heute an Edge-Standorten außerhalb der EU entschlüsseln kann.“
