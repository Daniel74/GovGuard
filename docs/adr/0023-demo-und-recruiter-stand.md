# 0023 – Demo-Stand ohne AWS, Recruiter-Stand mit Audit-Jobs

_Ändert [ADR 0004](0004-streamlit-community-cloud.md) (Aufrufweg der UI), [ADR 0006](0006-cloudwatch-audit-protokoll.md) (Reports kurz in S3) und [ADR 0018](0018-lambda-function-url.md) (asynchroner Ablauf); kehrt in [ADR 0016](0016-groq-zur-laufzeit-im-prototyp.md) den Standard-Provider um. Umsetzung: #11, #36. **Nachtrag 19.10.2026:** Nur der Demo-Stand wird gebaut, siehe unten. **Seit [ADR 0029](0029-kein-us-anbieter-fuer-echte-daten.md) entfällt der Recruiter-Stand auf AWS.**_

## Kontext

- Seit 15.10.2026 kein AWS-Zugriff; Präsentation am 26.10. Messung 16.10. mit Groq: 20–55 s und 2–3 Cent je Audit, `arch-antragseingang-fehlerhaft` verfehlt das Soll (BER.4.1 PASS statt FAIL).
- Python-Lambdas streamen nicht (ADR 0018); Fortschritt geht nur im Streamlit-Prozess oder über einen asynchronen Job. Das Dateisystem von Streamlit Community Cloud ist flüchtig.
- Teuer ist nur das Modell (Haiku ca. 0,90 $ je großem Audit), Lambda und Logs liegen im freien Kontingent. Der Bedrock-Zugang zu Haiku ist seit 16.10. abbestellt.

## Entscheidung

- **Demo-Stand:** Die UI auf Streamlit Community Cloud ruft `run_audit` selbst mit Groq auf. Kein AWS, kein Deploy nötig.
- **Recruiter-Stand:** Eine Lambda mit Function URL (IAM-Auth). `POST /audit/{spec|architecture}` legt einen Audit-Job an, ruft die Lambda asynchron selbst auf und antwortet `202` mit Job-ID; `GET /audit/<id>` liefert Fortschritt oder Report. Asynchron ohne Wiederholung, Timeout 300 s. Der Streamlit-User darf nur die Function URL aufrufen; Streamlit greift in keinem Stand direkt auf S3 zu.
- **S3:** ein Bucket mit KMS-CMK (ab Tag 1) für `knowledge_base/` und `audits/<id>/` (Fortschritt, Report mit Belegen, ohne Eingabe), Löschfrist für `audits/` 1 Tag. Nachweis für den Auditor bleibt das Audit-Ereignis (365 Tage, ADR 0006).
- **UI:** `AUDIT_BACKEND` (`local` | `lambda`) aus den Secrets; Passwort nur für „Audit erstellen“; Eingabe höchstens 100.000 Zeichen. Neue Audits nur in der Sitzung und als Download.
- **Galerie** aus dem Repo, je Preset Report, Quelldokument und Soll-Abweichung sichtbar; sie wächst nur per Commit. GovGuard prüft sich selbst: Presets `spec-govguard` und `arch-govguard-stack` (#34 wird Priorität A).
- **Provider:** Groq ist der einzige Provider in UI und Lambda; der Stack vergibt kein `bedrock:InvokeModel`. Die CLI behält `--provider bedrock` als Weg zu echten Daten (ADR 0001), ungetestet gegen echtes Bedrock. `model_id` steht im Report.
- **Fortschritt:** `run_audit` nimmt einen Callback `on_progress(Progress)`; die Prüflogik bleibt rein.
- **CI:** Gate sind nur cdk-nag und CDK-Assertions; das LLM-Selbst-Audit läuft von Hand und landet in der Galerie.

## Konsequenzen

- Die Demo verarbeitet Eingaben in den USA (Hosting und Groq, ADR 0004, 0016); nur fiktive Daten, Hinweis in der UI. Groq braucht das Developer Tier.
- Ohne Passwort keine Kosten durch Fremde. Für echte Daten gilt wieder ADR 0001: Bedrock `eu.` als einziger Provider.
- Die Gegenproben aus #32 und #33 laufen mit Groq statt Bedrock; eine Gegenprobe gegen ein zweites Modell entfällt.
- Ein Audit-Job, der am Timeout stirbt, schreibt nichts mehr; die UI meldet nach 300 s plus Puffer selbst „abgebrochen“.
- Die Lambda braucht `lambda:InvokeFunction` auf sich selbst sowie `s3:PutObject`/`GetObject` nur auf `audits/*`. Die Galerie zeigt Abweichungen statt nachzuwürfeln.
- Im Leerlauf zahlt der Recruiter-Stand nur KMS (ca. 1 $/Monat) und Cent-Beträge für S3.

## Nachtrag 19.10.2026: nur Demo-Stand

- AWS ist zurück, aber das Budget reicht nicht für Betrieb und Bau. Recruiter-Stand, Audit-Jobs, CDK-Stack und Pipeline sind Ausbau (#9, #34, #37, #38, Label `ausbau`); Haiku/Bedrock bleibt außen vor.
- Das Selbst-Audit prüft nur `docs/SPEC.md` als Preset `spec-govguard` (#36); `arch-govguard-stack` entfällt. Kein Template, kein KMS-Schlüssel, keine Leerlaufkosten.
- Die Entscheidungen oben zu Recruiter-Stand, S3 und CI gelten als Entwurf für den Ausbau.

## Fachgespräch-Satz

„Teuer ist nicht AWS, sondern das Modell: Die Demo läuft ohne Infrastruktur, der Recruiter-Stand zeigt mit Audit-Jobs, KMS und einem Tag Löschfrist, wie ich Fortschritt ohne Streaming und Nachvollziehbarkeit ohne Datensammlung löse.“ Seit 19.10.: „Den Recruiter-Stand habe ich entworfen, aber aus Budgetgründen bewusst nicht gebaut.“
