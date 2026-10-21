# UI und Hosting – Ergebnisse (Eingang für `/grill-with-docs`, Schritt 10i)

Rohmaterial aus einem Chat. Verbindlich wird es erst als ADR 0023 und als neu geschnittene Tickets.

## Entschieden (vom Nutzer)
1. **Demo:** Die Streamlit-UI auf Community Cloud ruft `run_audit` selbst mit Groq auf, die Galerie liest gespeicherte Reports aus dem Repo. Kommt AWS zurück, kommen Lambda und Bedrock Haiku als Option dazu.
2. **Recruiter-Stand:** eigenes AWS-Konto mit Lambda Function URL und Groq; S3 hält Wissensbasis, Galerie-Reports und Audit-Jobs. Fortschritt per asynchronem Job (`audits/<id>/progress.json`, UI fragt nach). Einen KMS-CMK gibt es von Anfang an (ca. 1 $/Monat).
3. **#34 wird Priorität A:** GovGuard prüft sich selbst. Eine GovGuard-Spezifikation (noch zu schreiben) und das CloudFormation-Template des eigenen Stacks werden Audit-Ziele für Demo und Recruiter. Die übrige Priorität B (#7, #8, #10) fällt aus dem Fahrplan.

## Anforderungen an die UI (Nutzer)
Datenwarnung · Hilfe zu Bedienung und Lesen der Reports · Audit erstellen (Groq/Haiku, nach der Demo mit Passwort) · gespeicherte Audits mit Quelldokument ansehen, Befund springt zur Textstelle (`line_start`/`line_end`) · Fortschritt während des Audits · Streamlit (React nur, wenn nötig).

## Fakten
- Messung mit Groq: `spec-meldeportal-gesundheit` 55 s, 0,03 $, `expected` erfüllt; `arch-antragseingang-fehlerhaft` 20 s, 0,02 $, **BSI BER.4.1 PASS statt FAIL** (`expected` verfehlt). Reports in `beispiel-reports/`.
- Das Free Tier von Groq (ca. 8.000 Tokens/min, 200.000/Tag, Sekundärquelle) reicht für kein volles Audit; nötig ist das Developer Tier.
- Lambda und CloudWatch Logs liegen im dauerhaft freien Kontingent, Fixkosten macht nur KMS. Teuer ist allein Bedrock Haiku (ca. 0,90 $ je großem Audit).
- Python-Lambdas streamen nicht (ADR 0018): Fortschritt geht nur im Streamlit-Prozess oder über einen asynchronen Job.

## Offene Fragen fürs Grilling
1. Passwort auch in der Demo? (Empfehlung: ja, selbst eintippen)
2. Galerie: Nur Reports, die `expected` erfüllen? Speichert die Demo neue Audits oder gibt es nur den Download?
3. #34 neu schneiden: Zweck (Nachweis für den Auditor, Galerie, Job-Ablage), ein oder mehrere Buckets, Löschfrist, Reports mit oder ohne `evidence`?
4. GovGuard-Spezifikation: Umfang, wer setzt `expected` (Testorakel), Preset oder nur Galerie?
5. Fortschritt: Wie meldet `run_audit` Fortschritt, ohne die Prüflogik unrein zu machen (Callback)?
6. Selbst-Audit in der CI mit Groq (ca. 3 Cent je Push) oder nur cdk-nag?
