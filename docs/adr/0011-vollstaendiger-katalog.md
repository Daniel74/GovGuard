# 0011 – Vollständiger Katalog im Prüfumfang

_Ersetzt [ADR 0002](0002-bounded-catalog.md). Ersetzt in [ADR 0007](0007-relevanz-und-ausnahmen.md) Relevanz, Gesetzte Plätze und Ranking. Prüfumfang ergänzt und Relevanzregel ersetzt in [ADR 0013](0013-begleittypen-im-pruefumfang.md)._

## Kontext

- Der erste Lauf vom 09.10.2026 (gpt-oss-120b) füllte nur 20 von 24 Plätzen im Architektur-Katalog, denn CIS war erschöpft. Alle Prüfregeln betrafen IAM, S3 oder KMS, keine API Gateway, Lambda, DynamoDB, SQS oder Firehose.
- Im Spec-Katalog lagen Art. 32, 17, 30, 33 und 35 über der Obergrenze, Art. 27 und 47 dagegen drin. Grund: Innerhalb eines Kapitels entschied die ID.
- GovGuard soll auch Spezifikationen und Architekturen auditieren, die keinem Archetyp ähneln. Obergrenze und Relevanz „Komponente eines Archetyps“ verhindern das.
- CIS deckt Serverless-Dienste kaum ab, FSBP und C5 schon (ADR 0008).

## Entscheidung

- **Katalog ohne Obergrenze:** alle prüfbaren und relevanten Prüfregeln. Relevant heißt: Der erste Ressourcentyp liegt im Prüfumfang (`data/scope.json`), und die Pflicht hängt am Template, nicht an Konto, Personen oder Anbieter (Ebene, #18). Das sind Serverless-Dienste, dazu RDS/Aurora und Fargate mit dem, was beide brauchen: VPC-Typen, ECR und Application/Network Load Balancer (ELBv2). Nicht dazu gehören EC2-Instanzen, EKS, CloudTrail, CloudFront und der Classic Load Balancer. Der Prompt von Stufe ② nennt den Prüfumfang.
- **Auswahlprotokoll** für jede Anforderung, auch für die vom Vorfilter verworfenen. Code-Entscheidungen bekommen einen festen Begründungssatz.
- **Cache:** LLM-Urteile werden nach Text-Hash, Prompt-Version und `model_id` wiederverwendet.
- **Abdeckungs-Gate:** Jede Komponente der Archetypen hat mindestens eine Prüfregel, sonst bricht der Build ab. Ein Typ zählt an jeder Stelle der Liste, wie beim N/A zur Laufzeit.
- **Laufzeit:** Der Code setzt N/A über das Ressourceninventar. Bei CloudFormation liest er es direkt, bei Terraform über eine Zuordnungstabelle. Bei Freitext nennt es ein LLM-Vorlauf mit Beleg; dort werden IAM, KMS und Logs nie gestrichen, denn sie stecken in jedem Workload, auch wenn der Text sie nicht nennt. Bei CloudFormation ist das Inventar des Codes exakt: Fehlt der Typ im Template, gibt es dort nichts zu prüfen. Die anwendbaren Prüfregeln laufen in Paketen à ca. 10 parallel.
- **Ausnahmen** gibt es auch für Prüfregeln, die ein Archetyp oder der GovGuard-Stack bewusst nicht erfüllt, z. B. FSBP `Lambda.3` (VPC), `APIGateway.3` (X-Ray) und `APIGateway.4` (WAF). Der Code wendet sie im Selbst-Audit und in der Freigabe an.
- **`kb_build` läuft nur manuell**, wenn sich Quelle, Steckbrief, Preset-Anker, Prompt oder Modell ändern.

## Konsequenzen

- Ranking, Gesetzte Plätze und Obergrenzen entfallen. Preset-Anker müssen nur prüfbar und relevant sein (Gate).
- Kosten und Laufzeit je Audit steigen. Das Kostenziel setzt erst die Messung. Unter 29 s bleibt es nur mit parallelen Paketen; Bedrock-Drosselung ist ein Risiko. Plan B ist eine Lambda Function URL mit IAM-Auth.
- Dubletten über Quellen hinweg bleiben getrennte Befunde, denn jede Prüfregel hat genau einen Primäranker. Der Report sortiert nach Ressourcentyp.
- Übersieht der Freitext-Vorlauf einen Dienst, steht „nicht erkannt“ im Befund. Die Lücke bleibt sichtbar.
- Der Code prüft beim Vorlauf, dass der Beleg wörtlich in der Eingabe steht, nicht, dass er zum Typ passt. Ein falsch zugeordneter Beleg führt höchstens zu einem überflüssigen Befund, nie zu einem verlorenen.
- Ein 5. Preset mit einer fremden Architektur sichert die neue Behauptung ab.
- Aurora und Fargate werden auditiert, aber nicht als Archetyp gebaut: Fargate hat Leerlaufkosten, Aurora braucht eine VPC (AUSBAU).
- Das LLM urteilt trotz Temperatur 0 nicht stabil: Im zweiten Lauf (11.10.2026) kippten 41 von 1.077 Urteilen. Der Cache friert die Urteile ein, der Kontrollpunkt bleibt nötig.
- Betrifft eine Anforderung mehrere Dienste, entscheidet die vom LLM gewählte Reihenfolge der Typen über die Relevanz, z. B. CIS 4.10 (CloudFront vor API Gateway). Diese Schwäche nehmen wir bewusst hin.
- Die Grenze zwischen Vorhaben und Betrieb (v. a. SDM Ebene P) klassifiziert das LLM nicht stabil; ein Prompt-Versuch dazu verwarf auch Art. 35. Im Zweifel nehmen wir auf: Ein unnötiger WARN ist sichtbar, eine verlorene Anforderung nicht.

## Fachgespräch-Satz

„Bei uns fällt keine Regel heraus, weder durchs Retrieval noch durch eine Obergrenze: Was nicht anwendbar ist, entscheidet der Code nachvollziehbar, und alles andere bekommt einen Befund.“
