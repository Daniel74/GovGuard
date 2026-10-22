# GovGuard – Blindbewertung (Issue #69)

**Stand:** 22.10.2026, Repo-Stand `f438f60` (main). Kriterien, Gewichte und Skala aus dem freigegebenen Katalog (Abschnitte 1.4 bis 1.6).

## Interessenkonflikt

GovGuard ist mit Unterstützung von Claude gebaut. Diese Bewertung schreibt ebenfalls Claude. Zum Ausgleich gelten drei strenge Regeln:

- Jede Punktzahl stützt sich auf einen Beleg im Repo: Datei mit Zeile, Test oder Commit.
- Was nur entworfen oder geplant ist, zählt nicht (Abschnitt *Zielbild, nicht bewertet*).
- Maßgeblich ist der Demo-Stand: Streamlit Community Cloud mit Groq (ADR 0023). Im Zweifel gilt die niedrigere Stufe.

**Blind:** Die Vergleichsdokumente und die Issues #68 und #69 habe ich nicht gelesen. Ein zu breiter Suchbefehl nach „SARIF“ hat drei Zeilen aus `Markt und Forschung – Audits und Remediation.md` angezeigt: die Kriterienzeile S3, die SARIF-Definition und eine Zeile zu einem Wettbewerber. Diese Zeilen betreffen GovGuard nicht und sind nicht in die Bewertung eingeflossen.

**Geprüft:** Ich habe die Testsuite selbst laufen lassen: `uv run pytest -q` ergibt 970 bestandene Tests und 24 abgewählte Browser-Tests. Das README nennt 965 Tests (README.md:52); die Zahl ist leicht veraltet.

## Punktetabelle

| Nr. | Kriterium | Punkte | Beleg | Begründung (Bezug zum Anker) |
|---|---|---|---|---|
| A1 | Normabdeckung DE/EU | **3** | Prüfregeln in `data/knowledge_base/rules_spec.json` (DSGVO 169, SDM 116, KI-VO 65) und `rules_arch.json` (FSBP 105, BSI Grundschutz++ 39, CIS 20, C5 11); Quellen in `data/input/sources.json:3–59`; SDM nur drei Bausteine (docs/FUNKTIONSWEISE.md:106) | Alle sechs Normen sind mit offenen Regeldateien vertreten (das spräche für 4), aber mit großen Lücken: SDM nur Löschen, Trennen und Zugriffe regeln, C5 nur 11 Kriterien und nur über die Prowler-Abbildung (`src/kb_build/extract/c5.py:1`), alles nur für AWS. |
| A2 | Eingabebreite V-Modell | **3** | Spezifikation als Freitext oder OpenAPI (`data/input/presets/spec-wohngeld-openapi/openapi.yaml`); Architektur als Freitext; Infrastruktur als Code nur bei CloudFormation-JSON mit Code-Inventar, Terraform ungetestet (CONTEXT.md:35, 44) | Drei von vier Stufen (Dokument, Architektur, IaC) sind dokumentiert und getestet, die Laufzeit fehlt ganz, und IaC ist nur für CloudFormation-JSON belastbar. |
| A3 | Belege und Nachvollziehbarkeit | **4** | Beleg per Zeilenverweis, vom Code wörtlich ausgeschnitten (`src/govguard/checks/evidence.py:13–15, 58–59`, ADR 0017:13); Test `test_evidence_spanning_lines_is_verbatim_in_crlf_input` (tests/test_run_audit.py:72); Normanker und Eingriffe des Codes im Befund (`src/govguard/models.py:83–90`, `src/govguard_ui/report/finding_detail.py:34–44`); gepinnte Quellen mit SHA-256 (`src/kb_build/source_fetch.py:88–91`) | Fundstelle im Original und Regel-ID mit Normanker sind belegt und im offenen Code prüfbar; für 5 fehlt das wiederholbare Ergebnis: nur 70 bis 99 % der Prüfregeln behalten ihren Status über Läufe (README.md:57), und die Rückverfolgung zum Wissensbasis-Commit (`kb_commit`) steht in allen sechs Galerie-Reports auf „local“ (`src/govguard/audit_setup.py:36`). |
| A4 | Remediation | **2** | Empfehlung je WARN und FAIL (`src/govguard/models.py:64`); Reparatur aus der Prüfregel (ADR 0017:31–34); Galerie: konkrete Eigenschaft bei Architektur, allgemeiner Satz bei Spezifikation (`data/gallery/arch-antragseingang-fehlerhaft.json`, `spec-meldeportal-gesundheit.json`) | Bei Architekturen nennt die Empfehlung oft Ressource und Eigenschaft in Worten, bei Spezifikationen bleibt sie ein allgemeiner Hinweis; es gibt keinen Patch und keine maschinelle Nachprüfung eines Vorschlags. |
| A5 | Mensch in der Schleife | **1** | Werkzeug ändert nichts selbst, Fachleute entscheiden (docs/SPEC.md:33); Freigabe durch einen Menschen nur für den Bau der Wissensbasis per Git-Commit (docs/SPEC.md:392–397); Audit-Ereignis (`AuditEvent`) nur als Modell definiert, nirgends geschrieben (`src/govguard/models.py:126`, einzige Verwendung in tests/test_models.py:57) | Für Audit-Befunde gibt es weder eine Freigabe noch ein Protokoll der menschlichen Entscheidung; dass GovGuard nichts automatisch ändert, ist nur ein Ansatz, kein Freigabe-Ablauf. |
| A6 | Datenresidenz, On-Prem | **1** | Demo: UI auf Streamlit Community Cloud ruft Groq auf (ADR 0023:13, 18); „Die Demo verarbeitet Eingaben in den USA“ (ADR 0023:24); Groq-Adapter: „user input goes to the USA“ (`src/govguard/adapters/groq_services.py:3`) | Im Demo-Stand laufen Hosting und KI-Verarbeitung in den USA; der EU-Weg über Bedrock `eu.` existiert nur in der Kommandozeile und ist gegen echtes Bedrock ungetestet (ADR 0023:18). |
| S1 | Entwicklungsaktivität und Roadmap | **3** | 199 Commits vom 21.09. bis 21.10.2026, davon 197 im Oktober, ein Autor (`git log`); kein Release (`gh release list` leer); KI-VO am 19.10. neu aufgenommen (Commits zu #52, #53); Grundschutz++ schon Quelle; öffentliche Pläne in docs/AUSBAU.md (18 Szenarien) | Sehr hohe, öffentlich prüfbare Aktivität mit nachgezogenen Normen, aber nur ein Monat, eine Person, keine Releases und ein Ende der Timebox am 21.10.2026. |
| S2 | KI-Strategie mit Kontrollen | **4** | Gleiche Prüfungen im Code (Gates) für beide Anbieter (`src/govguard/calls/model_call.py:36–54`); Abbruch statt ungeprüftem Report (fail closed, `src/govguard/audit_engine.py:76–78`); Verstoß-Prüfer stuft nur herab (ADR 0020:35–36); Tests in tests/test_run_audit.py:147–209 und tests/test_run_audit_corrections.py; offene Grenze „falsches PASS“ (docs/ARCHITECTURE.md:2079) | Trennung von Regel (fester Katalog) und Modell (nur Urteil) sowie Verifikation sind im offenen Code und in Tests prüfbar; für 5 fehlen eine unabhängige Untersuchung und eine Gegenprüfung für PASS, und der Demo-Stand hängt an einem einzigen Modell (`openai/gpt-oss-120b`). |
| S3 | Offenheit | **3** | MIT-Lizenz (LICENSE:1), Wissensbasis unter Quell-Lizenzen (README.md:84–85, NOTICE); Report als JSON herunterladbar (`src/govguard_ui/report/report_header.py:25–27`); Kommandozeile (`src/govguard/cli.py:68–69`) | Offene Lizenz, offene Regeldateien und ein JSON-Report sind belegt; es gibt kein SARIF, kein zweites Austauschformat und keine HTTP-Schnittstelle (die Lambda ist Ausbau, ADR 0023:33). |
| S4 | Preistransparenz | **4** | Kosten je Audit aus 19 Messläufen (README.md:53–57); Modellpreis und 0 € Leerlauf (docs/ARCHITECTURE.md:1439); Software kostenlos (LICENSE) | Kosten sind dokumentiert und mit offenen Messdaten prüfbar; für 5 fehlt eine unabhängige Bestätigung, und ein Betriebs- oder Supportangebot gibt es nicht. |
| M1 | Verbreitung | **0** | GitHub-API am 22.10.2026: 0 Sterne, 0 Forks, 0 Beobachter (`gh api repos/Daniel74/GovGuard`); kein Paket, keine Downloadzahlen | Keine Verbreitung belegt. |
| M2 | Nutzung im öffentlichen Sektor | **0** | Portfolio-Projekt, nur fiktive Daten (README.md:3, `src/govguard_ui/navigation.py:69`) | Kein Einsatz bei einer Behörde belegt. |
| M3 | Ökosystem | **1** | Standard-Eingaben (CloudFormation, OpenAPI); Quellen aus offenen Repos von BSI und Prowler (`data/input/sources.json`) | Nur Anschluss an offene Formate und Quellen; keine Integration in CI oder Ticketsysteme, keine Partner, keine Community. |

## Achsenwerte

| Achse | Rechenweg | Wert (0–5) |
|---|---|---|
| Angebot | 0,20·3 + 0,15·3 + 0,20·4 + 0,15·2 + 0,15·1 + 0,15·1 = 0,60 + 0,45 + 0,80 + 0,30 + 0,15 + 0,15 | **2,45** |
| Strategie | 0,30·3 + 0,25·4 + 0,25·3 + 0,20·4 = 0,90 + 1,00 + 0,75 + 0,80 | **3,45** |
| Marktpräsenz | 0,40·0 + 0,40·0 + 0,20·1 = 0 + 0 + 0,20 | **0,20** |

Nur falls ein Gesamtwert gebraucht wird: 0,5·2,45 + 0,3·3,45 + 0,2·0,20 = 1,225 + 1,035 + 0,04 = **2,30**.

## Stärken

- **Wörtlicher Beleg per Konstruktion:** Das Modell nennt nur Zeilennummern, der Code schneidet das Zitat aus (ADR 0017). Ein erfundenes Zitat ist damit ausgeschlossen, ein falscher Zeilenverweis nicht.
- **Kontrollen um das Modell:** Schema, Vollständigkeit und Belegzeilen prüft der Code; bei ungültiger Antwort bricht das Audit ab (fail closed), ein unbelegtes PASS oder FAIL wird WARN. Eingriffe stehen sichtbar am Befund (Korrekturen, `corrections`).
- **Deutsche Normen im Katalog:** Grundschutz++, C5, SDM, DSGVO und KI-VO als offene JSON-Regeldateien mit gepinnten Quellen (SHA-256).
- **Ehrliche Messung:** Kosten, Dauer, Schwankung und Soll-Treffer (10 von 19 Läufen) sind veröffentlicht, ebenso die Grenzen (docs/ARCHITECTURE.md 7.4).
- **Offen und testbar:** MIT-Lizenz, 970 automatische Tests, lokal ohne AWS lauffähig.

## Lücken

- **Datenresidenz im Demo-Stand:** Eingaben gehen an Streamlit Community Cloud und Groq in den USA; der EU-Weg ist ungetestet.
- **Kein Protokoll und keine Freigabe:** Das Audit-Ereignis ist nur als Datenmodell da; menschliche Entscheidungen zu Befunden werden nirgends festgehalten.
- **Nicht wiederholbar und nicht validiert:** Bis zu 30 % der Prüfregeln wechseln zwischen Läufen den Status; eine Trefferquote gegen Fachleute ist nicht gemessen (README.md:57). Ein falsches PASS hat keine zweite Prüfung.
- **Remediation nur als Text:** Keine Patches, keine maschinelle Nachprüfung, keine Laufzeitprüfung.
- **Keine Marktpräsenz:** Keine Nutzer, kein Release, kein Austauschformat wie SARIF, keine Schnittstelle für andere Werkzeuge.

## Zielbild, nicht bewertet

Diese Punkte sind entworfen oder geplant, aber nicht gebaut. Sie sind in keine Punktzahl eingeflossen:

| Zielbild | Quelle |
|---|---|
| Golden Archetypes mit Freigabe | ADR 0019, docs/AUSBAU.md Szenario 13 (bis 22.10.2026, Git-Verlauf) |
| AWS-Betrieb in `eu-central-1` mit Lambda, KMS, Audit-Jobs (Recruiter-Stand) | ADR 0023 Nachtrag 19.10.2026, AUSBAU Phase 3 |
| Audit-Protokoll in CloudWatch, 365 Tage | ADR 0006 |
| Zweitprüfer für PASS | AUSBAU Phase 2 |
| Terraform mit Code-Inventar, vollständiges C5 | AUSBAU Szenarien 9 und 1 (bis 22.10.2026, Git-Verlauf) |
| Geplante Remediation-Erweiterung | Kriterienkatalog A4 („Thema der geplanten Erweiterung“), im Code nicht vorhanden |
