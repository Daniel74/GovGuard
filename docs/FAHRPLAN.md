# GovGuard – Fahrplan

Ein Eintrag je Ticket, in Bearbeitungsreihenfolge. Jeder Eintrag steht für sich: Du brauchst kein anderes Dokument, um ihn abzuarbeiten. Hake die Kästchen im Editor ab.

**Legende:** 👤 du · 🤖 Claude · 🛠 Junie (PyCharm) · ✂ fällt zuerst weg (Schnittlinie) · `/…` Befehl zum Eintippen. `/verstehen N <Schwerpunkt>` erklärt das Ticket als Lernkarte und fragt sie ab. Claude zeigt pro Ticket einen Plan und arbeitet nach deinem **Go** am Stück (CLAUDE.md). Junie baut nur die UI und gibt bei #12 und #9 eine zweite Meinung. Alles läuft direkt auf `main`, ohne Branches.

**Rhythmus jedes Eintrags:** _Starten → Bauen → Prüfen → Verstehen → Abschließen._

**Tagesabschluss:** 👤 `/devlog`

**Modell und Session:**

- **Sonnet baut, Opus urteilt.** Sonnet 5.5 für TDD-Zyklen mit klaren Kriterien; Opus 5.5 für Grilling, Review, Security-Review, Diagnose und IHK-Check. Opus baut auch die heiklen Tickets #1 (Fundament), #7 (Freigabe-Schleife) und #9 (IAM, KMS). Wechsel mit `/model sonnet` bzw. `/model opus`.
- **🆕 = neue Session** (`/clear`). Erste Nachricht: „Lies docs/FAHRPLAN.md Schritt N und Issue #X.“ Jeder Schritt startet frisch. Das Review läuft in einer zweiten frischen Session, damit keine Sitzung ihren eigenen Code prüft (Vier-Augen-Prinzip).
- Zusätzlich neu starten, wenn eine Session lang wird und Claude Absprachen vergisst oder sich wiederholt. Vorher den Stand committen.
- **Junie ist zweite Meinung, nicht Bauer.** Bei #4 und #5 lieferte Junie (GPT-5.2) grüne Tests mit falschen Daten; der Neubau kostete mehr Claude-Budget, als er sparte. Junie baut deshalb nur noch die Streamlit-UI (Fehler sieht man sofort) und prüft bei #12 und #9 den Diff als zweite Modellfamilie (Vier-Augen-Prinzip). Junie liest `AGENTS.md` und committet nicht. Wird das Claude-Budget knapp, bekommt Junie ein Ticket nur mit vorab geschriebenen roten Tests.

**Priorität:** Erst die Audits, dann die Architektur-Generierung.

- **A – Audits (Pflicht):** Spec-Audit und Architektur-Audit laufen Ende-zu-Ende, mit vollständigem Katalog (ADR 0011), Deploy, Selbst-Audit und Demo-UI; dazu passt die Doku. Schritte 6–14; 15–16 nur, wenn ein Tag frei wird (✂).
- **B – Golden Archetypes (entfällt, ADR 0019):** Archetypen bauen und freigeben (#7), Archetyp-Auswahl (#10). Schritte 17–18 bleiben als Ausbau stehen.
- **Stichtag:** B beginnt nur, wenn A fertig ist und bis zur Abgabe am 21.10. noch mindestens 3 Arbeitstage bleiben, also spätestens am Freitag, 16.10. Sonst gehen die Resttage in Stabilisierung und Präsentation. Im Fachgespräch ist B dann Ausbau: Steckbriefe, ADR 0003 und 0009 liegen vor.
- **Stand 14.10.:** B entfällt. Der Deploy (#9, #11) wird voll gebaut und braucht 3–4 Tage, A ist also nicht bis 16.10. fertig.

**Zeitplan bis zur Präsentation:**

| Tag                | Arbeit                                                                                                                                                                    |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Mi 14.10.          | Schritt 10: #14 abschließen. Schritt 10a vorgezogen: TDD-Umbau Beleg per Zeilenverweis, Nachschärfen, Messungen.                                                          |
| Do 15.10.          | Schritt 10a: Diagnose fail closed und Messung mit Durchlauf. Schritte 10b–10c: #27 KI-Governance, #28 Bewertung. Wird es knapp, #27 auf die Herabstufung im Report kürzen |
| Fr 16. – Sa 17.10. | Schritt 11: #9 Stack und Endpunkte, Deploy und Messung am Samstag                                                                                                         |
| So 18.10.          | Schritt 12: #11 Pipeline und Wizard; Junie baut parallel die UI                                                                                                           |
| Mo 19.10.          | #11 fertig und live (das Claude-Wochenlimit setzt zurück)                                                                                                                 |
| Di 20.10.          | Schritte 13–14: Doku #22 und #16. Damit ist A fertig.                                                                                                                     |
| Mi 21.10.          | Abgabe, Puffer                                                                                                                                                            |
| 22.–25.10.         | Verstehen: `/verstehen` für #14, #26, #9, #11, Schritt 19 Lehrbuch #23, Generalprobe                                                                                      |
| Mo 26.10.          | Präsentation und Fachgespräch                                                                                                                                             |

**Schnittlinie:** Wird es knapp, fällt zuerst #8 weg, weil der Build der Wissensbasis auch lokal per `python -m kb_build` läuft. Danach fällt #24 weg; es zählt nur bei einem neuen Build. Beide machen nur dann weiter, wenn ein Tag frei wird. Im Fachgespräch sind sie Ausbau.

**Wer baut was:**

| Schritt | Prio | Ticket                          | Baut                                             | Prüft                      |
| ------- | ---- | ------------------------------- | ------------------------------------------------ | -------------------------- |
| 1       | –    | #1 Prüfkern                     | 🤖 Opus                                          | 🤖 Opus                    |
| 2       | –    | #3 Presets                      | 👤 + 🤖 Opus                                     | 👤                         |
| 3       | –    | #2 Bedrock + CLI                | 🤖 Sonnet                                        | 🤖 Opus                    |
| 4       | –    | #4 BSI + CIS                    | 🛠 Junie                                         | 🤖 Opus                    |
| 5       | –    | #5 DSGVO + SDM                  | 🛠 Junie                                         | 🤖 Opus                    |
| 6       | A    | #13 Quellen FSBP + C5           | 🤖 Sonnet                                        | 🤖 Opus                    |
| 7       | A    | #6 Bounded Catalog              | 🤖 Sonnet                                        | 👤 Kontrollpunkt + 🤖 Opus |
| 8       | A    | #15 5. Preset                   | 👤 + 🤖 Opus                                     | 👤                         |
| 9       | A    | #12 Prüfregeln + Gate           | 🤖 Opus                                          | 🤖 Opus · 🛠 Junie         |
| 9a      | A    | #18 Kontoweite Pflichten        | 🤖 Sonnet                                        | 👤 Kontrollpunkt + 🤖 Opus |
| 9b      | A    | #17 Gate Eigenschaftsnamen      | 🤖 Sonnet                                        | 🤖 Opus                    |
| 9c      | A    | #20 Ordnerstruktur              | 🤖 Opus                                          | 🤖 Opus                    |
| 9d      | A    | #19 Typen im Prüfumfang         | 🤖 Sonnet                                        | 🤖 Opus                    |
| 9e      | A    | #21 Groq als Build-Standard     | 🤖 Sonnet                                        | 🤖 Opus                    |
| 9g      | A    | #25 ADR 0015 Terraform-Grenze   | 🤖 Sonnet                                        | 👤                         |
| 10      | A    | #14 Ressourceninventar + Pakete | 🤖 Opus                                          | 🤖 Opus                    |
| 10a     | A    | #26 Belege bei großen Eingaben  | 🤖 Opus                                          | 🤖 Opus                    |
| 10b     | A    | #27 KI-Governance sichtbar      | 🤖 Sonnet                                        | 🤖 Opus                    |
| 10c     | A    | #28 FAIL nur bei Verstoß        | 🤖 Opus                                          | 🤖 Opus                    |
| 11      | A    | #9 Stack + Endpunkte            | 🤖 Opus                                          | 🤖 Opus · 🛠 Junie         |
| 12      | A    | #11 Deploy + UI                 | 🛠 Junie (UI) · 🤖 Sonnet (`deploy.yml`, Wizard) | 🤖 Opus                    |
| 13      | A    | #22 Doku zu kb_build nachziehen | 🤖 Sonnet                                        | 👤                         |
| 14      | A    | #16 Doku nachziehen             | 👤 + 🤖 Sonnet                                   | 👤                         |
| 15      | A ✂  | #24 Pflichtanker stabil         | 🤖 Sonnet                                        | 🤖 Opus                    |
| 16      | A ✂  | #8 Preset-Gate + Workflow       | 🤖 Sonnet                                        | 🤖 Opus                    |
| 17      | B    | #7 Golden Archetypes            | 🤖 Opus                                          | 🤖 Opus                    |
| 18      | B    | #10 Archetyp-Auswahl            | 🤖 Sonnet                                        | 🤖 Opus                    |
| 19      | –    | #23 Lehrbuch fertigstellen      | 👤 + Claude Web                                  | 👤                         |

---

### Schritt 0 – Stand sichern

**Ziel:** Die Tickets verlinken auf ADR 0011 und den Fahrplan; beides muss auf GitHub liegen.

- [x] 👤 Alle Doku-Änderungen committen und pushen, z. B. `ADR 0011: full catalog, scope, FSBP and C5; FAHRPLAN priorities`

**Fertig, wenn:** `git status` sauber ist und ADR 0011 auf GitHub lesbar ist.

---

### Schritt 1 – #1 Prüfkern: Modelle und audit_engine

**Ziel:** Die Prüflogik läuft komplett ohne AWS und ist getestet: Modelle, Validierungskette, Gesamtstatus, N/A durch Code.
**Voraussetzung:** Schritt 0. Schritt 2 kann parallel laufen.

- [x] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #1 umsetzen`. 🤖 legt je Zyklus erst einen roten Test an, dann den Code, bis der Test grün ist. 👤 sagt Go. Wiederholen, bis alle Kriterien grün sind.
      Reihenfolge: `pyproject.toml` + ruff → `text.py` (`normalize`, `contains_quote`, `template_resource_types`) → Gesamtstatus → Validator → `run_audit()` mit `FunctionModel` → boto3-Importtest und Test der Modulgröße
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #1`
- [x] **Verstehen** 👤 `/verstehen 1` (Schwerpunkt: Halluzinationsschutz)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** `pytest` und `ruff check` grün sind, die Lernkarte steht und der Commit gepusht ist.
**Fürs Fachgespräch:** Draft-Pattern, Fail closed, Beleg-Pflicht, warum der Code N/A setzt.

---

### Schritt 2 – #3 Presets mit Soll-Ergebnis (deine Handarbeit)

**Ziel:** 4 fiktive Presets mit einem Soll, das du festlegst. Das Soll ist der Maßstab für alle späteren Tests.
**Voraussetzung:** keine; parallel zu Schritt 1.

- [x] **Starten** 🆕 _Opus_ · 👤 `/grilling Presets für #3: 4 fiktive Behördenszenarien, Aufteilung Spec/Architektur, Soll-Gesamtstatus, Pflichtanker (höchstens 4 je Audit-Art)`
- [x] **Bauen** 👤 „Lege die Presets nach unseren Antworten an“ → Go → 🤖 schreibt die Eingaben unter `data/presets/<id>/`, den Bauplan nach `data/presets/BAUPLAN.local.md` (gitignored) und `data/sources/bsi_gspp_auszug.txt`. Formate: OpenAPI, Freitext, CloudFormation-JSON (damit „N/A durch Code“ mitgetestet wird).
- [x] **Blind prüfen** 👤 Gemini (normaler Chat, nicht Deep Research), ein Chat je Preset: Eingabe + Quellen hochladen, Prompt aus `BAUPLAN.local.md`. Ein Anker bleibt nur, wenn Gemini dieselbe Norm mit demselben Status nennt (bei CIS genügt der Titel, wenn Gemini keine v7-Nummer kennt). Ein ungeplanter FAIL in einem WARN-Preset → 🤖 korrigiert die Eingabe.
- [x] **Soll festlegen** 👤 nennt je Preset Gesamtstatus und bestätigte Anker → 🤖 schreibt die `preset.json`, Tests grün.
- [x] **Verstehen** 👤 `/verstehen 3` (Kernfrage: warum das Soll von dir kommt und nicht aus einem früheren Lauf)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** 4 Ordner unter `data/presets/` liegen, die Pflichtanker auf Normen zeigen und die Lernkarte steht.
**Fürs Fachgespräch:** Testorakel, zirkulärer Test, gesetzte Plätze.

---

### Schritt 3 – #2 Bedrock-Anbindung und CLI

**Ziel:** Ein echtes Spec-Audit läuft lokal über Bedrock. Laufzeit und Kosten sind gemessen.
**Voraussetzung:** Schritt 1. AWS-Login aktiv (`aws sso login`), Zugang zu Claude Haiku 4.5 in Bedrock eu-central-1.

- [x] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #2 umsetzen` (Stubber-Test: Request enthält `toolChoice`; CLI-Ausgabe als JSON)
- [x] **Bauen** 👤 „Prüfe die Modell-ID mit `aws bedrock list-inference-profiles --region eu-central-1`“ → 🤖 korrigiert die ID, falls nötig, auch in ADR 0001 und ARCHITECTURE 2.1.
- [x] **Messen** 👤 `/run CLI-Audit mit 100.000 Zeichen und 20 Prüfregeln, Laufzeit und Kosten messen` → Go → 🤖 notiert das Ergebnis im Issue
- [x] Falls über 29 s: 👤 `/model opus`, dann `/diagnosing-bugs Audit überschreitet 29 s` und den Plan B aus der offenen Frage in #2 entscheiden
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #2`
- [x] **Verstehen** 👤 `/verstehen 2` (Schwerpunkt: Tool-Choice und EU-Inferenz)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** `python -m govguard.cli spec <datei>` einen gültigen Audit-Report liefert und Messwerte im Issue stehen.
**Fürs Fachgespräch:** Inferenzprofil `eu.`, Art. 44 DSGVO, erzwungene Tool-Nutzung, Dependency Injection.

---

### Schritt 4 – #4 Extraktion BSI und CIS

**Ziel:** BSI Grundschutz++ und CIS AWS v7 sind deterministisch in Anforderungen zerlegt und vorgefiltert.
**Voraussetzung:** Schritt 1 (`normalize()`).

- [x] **Spike** 🛠 _Junie_ · 👤 „Zeig mir die Struktur von Prowler `cis_7.0_aws.json` und dem BSI-OSCAL: Felder, IDs, Markdown-Zeichen im Text. Nur anschauen, nichts ändern.“
- [x] **Starten** 🛠 _Junie_ · 👤 „Lies docs/FAHRPLAN.md Schritt 4 und `gh issue view 4`. Setze es per TDD um (ADR 0008).“ Reihenfolge: `data/sources.json` + `source_fetch.py` (Hash-Prüfung, Test mit Fake) → BSI → CIS. Stichproben-Tests: `DET.3.1`, CIS `3.1.4`, jede ID genau einmal, CIS genau 70 Empfehlungen
- [x] **Bauen** 🛠 erzeugt `data/extracted/bsi.json` und `cis.json` (nur lokal). 👤 Prüfe: Bleiben beim BSI nach dem Vorfilter 380 Anforderungen? Stimmen 3 CIS-Texte mit dem lokalen PDF überein?
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #4`
- [x] **Verstehen** 👤 `/verstehen 4` (Kernfrage: warum der Vorfilter MUSS **und** SOLLTE nimmt)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** `bsi.json` eingecheckt ist, `cis.json` per `.gitignore` draußen bleibt, alle Tests grün sind und die CIS-Zahl im Issue steht.
**Fürs Fachgespräch:** OSCAL, Commit-SHA plus SHA-256, Reproduzierbarkeit, Lizenz (keine CIS-Volltexte im Repo).

---

### Schritt 5 – #5 Extraktion DSGVO und SDM

**Ziel:** DSGVO und die SDM-Bausteine sind deterministisch in Anforderungen zerlegt und vorgefiltert.
**Voraussetzung:** Schritt 1 (`normalize()`).

- [x] **Spike** 🛠 _Junie_ · 👤 „Zeig mir die Struktur des DSGVO-Formex-XML (`ARTICLE`, `PARAG`, Berichtigungs-Markierungen) und der SDM-Bausteine (Kopfzeilen, Maßnahmen-IDs). Nur anschauen.“
- [x] **Starten** 🛠 _Junie_ · 👤 „Lies docs/FAHRPLAN.md Schritt 5 und `gh issue view 5`. Setze es per TDD um (ADR 0008).“ DSGVO und SDM kommen in `data/sources.json`. Stichproben-Tests: `Art. 32`, `M60.D01`, jede ID genau einmal, DSGVO genau 99 Artikel
- [x] **Bauen** 🛠 erzeugt `data/extracted/dsgvo.json` und `sdm.json`
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #5`
- [x] **Verstehen** 👤 `/verstehen 5` (Kernfrage: warum SDM Protokollieren (M43) bewusst fehlt)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Beide JSON-Dateien eingecheckt sind und alle Tests grün sind.
**Fürs Fachgespräch:** SDM als Umsetzung der DSGVO-Grundsätze, Bußgeldstufen nach Art. 83.

---

## Priorität A – Audits

### Schritt 6 – #13 Quellen FSBP und C5

**Ziel:** FSBP und C5 sind deterministisch in Anforderungen zerlegt und vorgefiltert; CIS, FSBP und C5 teilen einen Prowler-Parser.
**Voraussetzung:** Schritt 0.

- [x] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #13 umsetzen` → Plan → Go
      Reihenfolge: `prowler.py` (gemeinsamer Parser, CIS-Tests bleiben grün) → `fsbp.py` → `c5.py` → Vorfilter aller Quellen mit Begründungssatz → `sources.json` auf Prowler `5.44.0`
- [x] **Bauen** 🤖 erzeugt `fsbp.json` und `c5.json` (nur lokal). 👤 Prüfe: Wie viele Anforderungen bleiben je Quelle nach dem Vorfilter? Steht die Zahl im Issue?
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #13`
- [x] **Verstehen** 👤 `/verstehen 13` (Kernfrage: warum wir nur die Texte aus Prowler nehmen, nicht die Check-Zuordnung)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Alle Tests grün sind, `fsbp.json` und `c5.json` per `.gitignore` draußen bleiben und die Zahlen im Issue stehen.
**Fürs Fachgespräch:** abgeleitete Quelle, gepinnter Commit, Lizenz, Rezept „neue Quelle“.

---

### Schritt 7 – #6 Bounded Catalog und Auswahlprotokoll (Kontrollpunkt)

**Ziel:** Es steht fest, welche Anforderungen in den Bounded Catalog kommen, und zu jeder Anforderung gibt es eine Begründung. Du hast das Auswahlprotokoll gelesen und freigegeben.
**Voraussetzung:** Schritt 6.

- [x] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #6 umsetzen` → Plan → Go (der Prompt von Stufe ② ist eine Weichenstellung)
      Reihenfolge: `data/scope.json` → Relevanz (erster Typ im Prüfumfang) → Ranking und Obergrenzen entfernen → Auswahlprotokoll für alle Anforderungen → Cache → Gates (Pflichtanker, Abdeckung)
- [x] **Echter Lauf** 🤖 👤 „Erzeuge Auswahlliste und Auswahlprotokoll“ (Groq, ADR 0010, bis Bedrock läuft)
- [x] **Kontrollpunkt** 👤 Lies `verdicts_arch.json` und `verdicts_spec.json` (ca. 15 Minuten):
      Hat jede Komponente (API Gateway, Lambda, DynamoDB, SQS, S3, Firehose) Prüfregeln? Sind Art. 32 und Art. 17 drin? Sind die Begründungen bei `not_testable` und `not_relevant` plausibel?
      Falls nein: 🆕 _Opus_ · 👤 `/grilling Auswahlprotokoll nachschärfen`, bevor es weitergeht.
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #6`
- [x] **Verstehen** 👤 `/verstehen 6` (Schwerpunkt: Bounded Catalog, Prüfumfang und Auswahlprotokoll)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Auswahlliste und Auswahlprotokoll eingecheckt sind, du sie freigegeben hast und Kosten und Regelanzahl im Issue stehen.
**Fürs Fachgespräch:** Vollständigkeit statt Top-K und statt Obergrenze, „Das LLM urteilt, der Code wählt aus“, Begründung je Anforderung.

---

### Schritt 8 – #15 5. Preset: fremde Serverless-Architektur (deine Handarbeit)

**Ziel:** Ein Preset belegt, dass GovGuard auch Architekturen auditiert, die keinem Archetyp ähneln.
**Voraussetzung:** Schritt 6 (Anker-Format `AWS FSBP …`). Parallel zu Schritt 7.

- [x] **Starten** 🆕 _Opus_ · 👤 `/grilling Preset für #15: Step Functions + SNS ohne KMS, Soll-Gesamtstatus, Pflichtanker`
- [x] **Bauen** 👤 „Lege das Preset nach unseren Antworten an“ → Go → 🤖 schreibt das CloudFormation-Template unter `data/presets/<id>/`
- [x] **Blind prüfen** 👤 Gemini wie in Schritt 2
- [x] **Soll festlegen** 👤 nennt Gesamtstatus und bestätigte Anker → 🤖 schreibt `preset.json`, Tests grün
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Das Preset liegt vor, und sein Pflichtanker steht im Bounded Catalog.

---

### Schritt 9 – #12 Prüfregeln formulieren und Gate

**Ziel:** `rules_spec.json` und `rules_arch.json` liegen vor; jede Prüfregel hat das Gate bestanden.
**Voraussetzung:** Schritt 7 inklusive Kontrollpunkt.

- [x] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #12 umsetzen` → Plan → Go (Prompt-Design ist eine Weichenstellung)
      Reihenfolge: `gates.py` (Schema, Anker, Zitat, Querverweise) → `formulate_rule` mit `FunctionModel`
- [x] **Echter Lauf** 🤖 👤 „Formuliere die Prüfregeln“
- [x] **Stichprobe** 👤 Lies 5 Prüfregeln, davon mindestens eine aus FSBP und eine aus C5: Sind `compliant_if` und `violation_if` prüfbar? Passt `source_quote` zur Norm?
- [-] **Zweite Meinung** 🛠 _Junie_ · 👤 „Lies AGENTS.md → Review und `gh issue view 12`. Prüfe `git diff`.“ Befunde nimmst du ins Opus-Review mit.
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #12`
- [x] **Verstehen** 👤 `/verstehen 12` (Kernfrage: warum der Code den Primäranker setzt und nicht das LLM)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Beide Kataloge eingecheckt sind, das Gate grün ist und die Stichprobe gepasst hat.
**Fürs Fachgespräch:** Zitat statt Behauptung, erfundene Fundstellen, Draft-Pattern im Build.

---

### Schritt 9a – #18 Stufe ② verwirft kontoweite Pflichten (CloudTrail-Lücke)

**Ziel:** In den Bounded Catalog kommen nur Anforderungen, deren Pflicht am Template hängt, nicht an Konto, Organisation, Personen oder Cloud-Anbieter (Stichprobe aus #12: CIS 4.4, C5 OPS-16.01B).
**Voraussetzung:** Schritt 9.

- [x] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #18 umsetzen` → Plan → Go (der Prompt von Stufe ② ist eine Weichenstellung)
      Reihenfolge: Feld `scope_level` in `Classification` → Code setzt `not_relevant` mit festem Satz → Prompt von Stufe ②
- [x] **Echter Lauf** 🤖 👤 „Erzeuge die Architektur-Auswahl neu“ (`--provider groq`, Schlüssel aus `.env`; die Prompt-Version ändert sich, alle ca. 884 Urteile werden neu bezahlt)
- [x] **Kontrollpunkt** 👤 `git diff data/knowledge_base/selection_arch.json`: Sind CIS 4.4 und C5 OPS-16.01B raus? Was ist sonst noch herausgefallen, und ist die Begründung plausibel?
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #18`
- [x] **Verstehen** 👤 `/verstehen 18` (Kernfrage: warum „prüfbar“ und „relevant“ nicht reichen, wenn die Pflicht für jemand anderen gilt)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Die neue Auswahl eingecheckt ist, beide Gates grün sind und du den Diff freigegeben hast.
**Fürs Fachgespräch:** Shared Responsibility Model (Anbieter, Konto, Workload), „Das LLM urteilt, der Code wählt aus“.

---

### Schritt 9b – #17 Gate gegen erfundene CloudFormation-Eigenschaften

**Ziel:** Architektur-Prüfregeln nennen nur Eigenschaften, die es am Ressourcentyp wirklich gibt (Stichprobe aus #12: CIS 4.4 verlangt `TargetPrefix` statt `LogFilePrefix`).
**Voraussetzung:** Schritt 9a. Der Lauf hier formuliert die Prüfregeln für die neue Auswahl aus 9a.

- [x] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #17 umsetzen` → Plan → Go (die Erkennung der Eigenschaftsnamen im Freitext ist eine Weichenstellung, siehe offene Fragen im Issue)
      Reihenfolge: Schnappschuss `data/cfn_properties.json` → reine Prüffunktion → Validator von `formulate_rule` → Qualitätsbericht `unknown_properties`
- [x] **Echter Lauf** 🤖 👤 „Formuliere die Architektur-Prüfregeln neu“ (`--provider bedrock-global`, falls `eu.` keine Kapazität hat, ADR 0012). 👤 Prüfe: Zeigt der Qualitätsbericht 0 unbekannte Eigenschaften und `account_level` 0?
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #17`
- [x] **Verstehen** 👤 `/verstehen 17` (Kernfrage: warum ein Schema-Abgleich mehr beweist als ein strengerer Prompt)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** `rules_arch.json` neu eingecheckt ist und der Qualitätsbericht 0 unbekannte Eigenschaften zeigt.
**Fürs Fachgespräch:** deterministische Gegenprobe gegen eine Referenz (wie Zitat und Typliste), Grenzen von Prompt-Regeln.

---

### Schritt 9c – #20 Ordnerstruktur: data/ nach Herkunft, kb_build/ nach Build-Schritt

**Ziel:** `data/` trennt Eingaben (`input/`), Zwischenergebnisse (`intermediate/`) und Endergebnis (`knowledge_base/`, nur `rules_*.json`); `kb_build/` hat je Build-Kommando einen Unterordner. Reines Refactoring.
**Voraussetzung:** Schritt 9b.

- [x] **Starten** _Opus_ · 👤 `/implement 20` → Plan → Go. Alle Datenpfade stehen in `kb_build/paths.py`; ein Test verbietet sie anderswo.
- [x] **Prüfen** _Opus_ · `/code-review` (Standards + Spec als Sub-Agents), Befunde behoben
- [x] **Echter Lauf** → verschoben in Schritt 9d, weil der Judgement-Cache für beide Audit-Arten nicht mehr zum Prompt passt und #19 den Lauf ohnehin wiederholt.
- [x] **Verstehen** 👤 `/verstehen 20` (Kernfrage: warum Daten nach Herkunft getrennt werden und was davon nach S3 geht)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** pytest und ruff grün sind und der echte Lauf in 9d in `data/intermediate/` schreibt.
**Fürs Fachgespräch:** Trennung Eingabe / Zwischenergebnis / Artefakt, eine Quelle für Pfade, Refactoring ohne Verhaltensänderung.

---

### Schritt 9d – #19 Ressourcentypen auf den Prüfumfang begrenzen

**Ziel:** Architektur-Prüfregeln nennen nur Typen aus `data/input/scope.json`, damit das Gate aus #17 jede Eigenschaft prüft. Nach dem Review von #17 bleiben 16 Regeln ungeprüft (`unjudged_properties`), z. B. mit CloudTrail, CloudFront, Classic ELB oder WAF Classic.
**Voraussetzung:** Schritt 9c.

- [x] **Klären** 🆕 _Opus_ · 👤 `/grilling Offene Fragen in #19: Backup, EFS, EBS-Volume und SSM in den Prüfumfang?`
- [x] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #19 umsetzen` → Plan → Go
      Reihenfolge: Prüfumfang erweitern (`scope.json`, Snapshot `cfn_properties.json`, ADR 0013, `CONTEXT.md`, `AUSBAU.md`) → Validator von Stufe ② streicht Typen außerhalb des Prüfumfangs → Validator von `formulate_rule` → `check_rules`
- [x] **Echter Lauf** 🤖 👤 „Erzeuge Auswahl und Prüfregeln für **beide** Audit-Arten neu“: `select` ohne `--audit-type` (`--provider groq`), dann `rules` (`bedrock-global`, falls `eu.` keine Kapazität hat). Der Cache ist für Spec und Architektur veraltet (siehe 9c), alle Urteile werden neu bezahlt. 👤 Prüfe: Schreibt `select` nach `data/intermediate/` (Nachweis für #20)? Zeigt der Qualitätsbericht `unjudged_properties` 0? Welche Regeln haben Typen verloren? Behalten FSBP DynamoDB.4 und RDS.26 ihre Backup-Typen? Was hat sich in `git diff data/intermediate/selection_spec.json` geändert?
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #19`
- [-] **Verstehen** 👤 `/verstehen 19` (Kernfrage: warum ein Gate nur so weit prüft, wie seine Referenz reicht)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Beide Auswahllisten und beide `rules_*.json` neu eingecheckt sind und der Qualitätsbericht überall 0 zeigt.
**Fürs Fachgespräch:** sichtbare statt stiller Lücken, Prüfumfang als bewusste Entscheidung, Shared Responsibility.

---

### Schritt 9e – #21 Groq als Standard-Provider für kb_build

**Ziel:** `python -m kb_build` nutzt ohne Flag Groq für `select` und `rules` (ADR 0014). Haiku über Bedrock `eu.` bleibt für alles mit Nutzereingaben: Audits, Preset-Gate, Archetyp-Generierung.
**Voraussetzung:** Schritt 9d abgeschlossen (Review von #19 auf ruhigem Stand).

- [x] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #21 umsetzen` → Plan → Go
      Reihenfolge: Test Standard-Provider in `tests/test_main.py` → `default="groq"` in `kb_build/__main__.py` → Test „kein Ausweichen ohne `GROQ_API_KEY`“ → Docstring `groq_services.py`, `README.md` → Text von Issue #8 (Secret `GROQ_API_KEY`, OIDC-Rolle nur fürs Preset-Gate)
- [x] **Freigabe** 👤 Leitplanke in `CLAUDE.md` anpassen lassen („Ausnahme im Build: Groq als Standard, ADR 0014“)
- [x] **Entscheiden** 👤 Offene Frage im Issue: Prüfregeln jetzt mit Groq neu formulieren oder erst über #8? Falls jetzt: 🤖 `python -m kb_build rules` ohne Flag, 👤 prüft, ob der Qualitätsbericht weiter überall 0 zeigt und alle Pflichtanker drin sind.
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #21`
- [-] **Verstehen** 👤 `/verstehen 21` (Kernfrage: warum Datenresidenz zur Laufzeit gilt, aber nicht für öffentliche Normtexte im Build)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** pytest und ruff grün sind, ein Lauf ohne Flag Groq nutzt und #8 den neuen Stand beschreibt.
**Fürs Fachgespräch:** Trennung Build/Laufzeit, Kosten-Trade-off (FinOps), Gates machen die Qualität vom Modell unabhängig.

---

### Schritt 9g – #25 ADR 0015: CloudFormation als einziges Format mit Code-Inventar, Terraform ungetestet

**Ziel:** Nur CloudFormation-JSON hat ein Ressourceninventar per Code. Terraform und YAML laufen als Freitext, ohne Test durch ein Preset. ADR 0015, `CONTEXT.md`, `SPEC.md` und `AUSBAU.md` (Szenario 9) halten diese Einschränkung fest.
**Voraussetzung:** Schritt 9e. Kein Code, nur Doku.

- [x] **Starten** 🆕 _Sonnet_ · 👤 „Lies `gh issue view 25` und setze es um“ → Plan → Go
      Reihenfolge: ADR 0015 → `CONTEXT.md` und `SPEC.md` → `AUSBAU.md` Szenario 9 (IaC Generator vorher gegen AWS-Doku prüfen)
- [x] **Prüfen** 👤 ADR 0015 und Szenario 9 querlesen (je ca. 2 Minuten)
- [-] **Verstehen** 👤 `/verstehen 25` (Kernfrage: warum eine LLM-Übersetzung nach CloudFormation die Beleg-Pflicht bricht)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** ADR 0015 vorliegt und `CONTEXT.md`, `SPEC.md` und `AUSBAU.md` dazu passen.
**Fürs Fachgespräch:** eine Sprache für Wissensbasis, Archetypen und Selbst-Audit; Terraform als bewusst dokumentierte, ungetestete Grenze.

---

### Schritt 10 – #14 Audit-Engine: Ressourceninventar und parallele Pakete

**Ziel:** Die Audit-Engine bewertet den vollständigen Katalog: N/A über das Ressourceninventar, die anwendbaren Prüfregeln in parallelen Paketen.
**Voraussetzung:** Schritt 9.

- [x] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #14 umsetzen` → Plan → Go (der Freitext-Vorlauf ist eine Prompt-Weiche)
      Reihenfolge: Freitext-Vorlauf mit Beleg → N/A-Verbot für erkannte Typen → Pakete parallel → Zusammenführen (ein Befund je Prüfregel) → Sortierung nach Ressourcentyp
- [x] **Messen** 👤 `/run CLI-Audit des größten Presets mit vollem Katalog, Laufzeit und Kosten messen` → 🤖 notiert das Ergebnis im Issue.
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #14`
- [-] **Verstehen** 👤 `/verstehen 14` (Kernfrage: warum ein übersehener Dienst sichtbar bleiben muss)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Alle Tests grün sind und Laufzeit und Kosten im Issue stehen.
**Fürs Fachgespräch:** Pruning per Code, Map-Reduce, Vollständigkeit trotz Aufteilung.

---

### Schritt 10a – #26 Belege bei großen Eingaben

**Ziel:** Das größte Preset läuft mit vollem Katalog durch, und jeder Beleg steht nachweislich wörtlich in der Eingabe, mit Bedrock (Haiku 4.5) und mit Groq (gpt-oss-120b) als günstigem Fallback. Die Messung aus Schritt 10 zeigt: Beide Modelle setzen Zitate zusammen oder formatieren sie um, gpt-oss hält zudem das Tool-Schema nicht ein. Haiku kostet ca. 0,90 $ je großem Audit, Groq ca. ein Zehntel.
**Voraussetzung:** Schritt 10.

- [x] **Recherche** 🆕 _Opus_ · 👤 `/research Belege ohne Abschreiben: Citations der Bedrock Converse API (Haiku 4.5, eu., mit Tool-Choice nach ADR 0005)? Strict Tool Use / Structured Outputs für gpt-oss-120b auf Groq?`
- [x] **Prototyp** 🆕 _Opus_ · 👤 `/prototype Beleg per Verweis für #26` (Citations verworfen, siehe Recherche).
- [x] **Entscheiden** 👤 Beleg per Verweis, FAIL ohne Zeilenbereich stuft der Code auf WARN herab, Bereichsgrenze ca. 200 Zeilen → ADR 0017, Nachtrag in ADR 0016 (Groq mit `NativeOutput` statt erzwungenem Tool)
- [x] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #26 umsetzen` → Plan → Go. Dazu die veralteten Groq-Hinweise im Skill `audit-messen` korrigieren (Tokens werden gemeldet; Groq zur Laufzeit erlaubt, ADR 0016)
- [x] **Messen** 👤 `/audit-messen spec-wohngeld-openapi mit vollem Katalog, Bedrock und Groq` → 🤖 notiert beide Ergebnisse im Issue.
- [x] **Abschließen (Zwischenstand)** 👤 committet den TDD-Umbau, z. B. `#26 evidence by line reference (ADR 0017), measurement`
- [x] **Nachschärfen** 🆕 _Opus_ · 👤 „Lies docs/FAHRPLAN.md Schritt 10a und Issue #26 mit dem letzten Messkommentar.“ Dann `/tdd Issue #26 nachschärfen` → Plan → Go (Gate-Design und Drosselung sind Weichenstellungen)
      Reihenfolge: zu großer Bereich bei WARN/FAIL gilt als „kein Bereich“ (FAIL → WARN, kein Retry), nur PASS mit zu großem Bereich → Retry → Groq-Pakete gedrosselt (höchstens 4 gleichzeitig), Bedrock voll parallel → `measure.py` loggt die Probleme des letzten Versuchs → Nachtrag ADR 0017, DESIGN 2.2
- [x] **Neu messen** 👤 `/audit-messen spec-wohngeld-openapi, Bedrock und Groq` → 🤖 notiert beide Ergebnisse im Issue.
- [x] **Plan B entscheiden** 🆕 _Opus_ · 👤 `/grilling Plan B aus ADR 0011: Lambda Function URL statt API Gateway wegen 29 s?` → 🤖 schreibt das ADR. Muss vor #9 stehen, weil #9 den Stack baut.
- [x] **Diagnose** 🆕 _Opus_ · 👤 „Lies docs/FAHRPLAN.md Schritt 10a und Issue #26 mit dem letzten Messkommentar.“ Dann `/diagnosing-bugs fail closed bei spec-wohngeld-openapi` → Plan → Go (Gate-Design und Drosselung sind Weichenstellungen)
      Kandidaten aus der Messung: umgedrehter Bereich bei WARN/FAIL gilt wie ein zu großer als „kein Bereich“ → Bereich bei N/A ignorieren statt prüfen → Groq höchstens 2 Pakete gleichzeitig oder Token-Budget je Minute → fehlende Befunde (bis zu 7 je Paket) beobachten. Falsche FAILs mit Beleg gehören zu #28, nicht hierher.
- [x] **Messen (Durchlauf)** 👤 `/audit-messen spec-wohngeld-openapi mit Bedrock und Groq, arch-antragseingang-fehlerhaft mit Bedrock` → 🤖 notiert die Ergebnisse gegen `expected` im Issue, setzt das Kostenziel in SPEC und bestätigt den Lambda-Timeout in ADR 0018
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #26 seit 46e91b0` (TDD-Umbau, Nachschärfen und Diagnose zusammen)
- [-] **Verstehen** 👤 `/verstehen 26` (Kernfrage: warum der Beleg bleibt, auch wenn das LLM ihn nicht mehr abschreibt)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Das Preset mit beiden Modellen ohne fail closed durchläuft, jeder Beleg wörtlich in der Eingabe steht, das ADR vorliegt und Laufzeit, Kosten und das Ergebnis gegen `expected` je Modell im Issue stehen.
**Fürs Fachgespräch:** Grounding, Halluzinationsschutz durch Code statt Prompt, Output-Tokens als Laufzeittreiber, Modell-Unabhängigkeit durch Gates, Kosten gegen Datenresidenz.

---

### Schritt 10b – #27 KI-Governance: Korrekturen der KI sichtbar machen

**Ziel:** Report, fail-closed-Meldung, `AuditEvent` und der Qualitätsbericht von `kb_build` zeigen, wo die KI danebenlag und der Code eingegriffen hat (Retry-Gründe, Herabstufungen). Anlass: Im Prototyp zu #26 hatten 14 von 16 Paketen einen Retry, unsichtbar für den Nutzer.
**Voraussetzung:** Schritt 10a (die Herabstufung FAIL → WARN entsteht dort). Vor #9, weil Handler und UI den Report-Vertrag übernehmen.

- [x] **Klären** 🆕 _Opus_ · 👤 `/grilling Offene Fragen in #27: Detailtiefe im Report, Anzeige in der UI, Begriff fürs Glossar`
- [x] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #27 umsetzen` → Plan → Go (Report-Vertrag und Datenminimierung im Log sind Weichenstellungen)
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #27`
- [-] **Verstehen** 👤 `/verstehen 27` (Kernfrage: warum ein Audit-Werkzeug seine eigenen KI-Fehler zeigen muss)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Ein Report mit Retry die Korrekturen nennt, ein fail closed die Gründe in Alltagssprache zeigt und `AuditEvent` keine Eingabe enthält.
**Fürs Fachgespräch:** Transparenz und Nachvollziehbarkeit von KI-Entscheidungen, Human Oversight, Datenminimierung im Protokoll.

---

### Schritt 10c – #28 Bewertung: FAIL nur bei belegtem Verstoß

**Ziel:** FAIL gibt es nur, wenn der Beleg einen Verstoß zeigt; was fehlt oder unklar ist, bleibt WARN. Im Prototyp zu #26 vergeben beide Modelle FAILs mit Beleg, die keinen Verstoß zeigen, deshalb verfehlt `spec-wohngeld-openapi` sein `expected` (WARN).
**Voraussetzung:** Schritt 10a (Beleg per Verweis, Herabstufung von FAIL ohne Beleg).

- [x] **Klären** 🆕 _Opus_ · 👤 `/grilling Offene Fragen in #28: Prompt, Feld oder Gate?` (Prompt-Design ist eine Weichenstellung)
- [x] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #28 umsetzen` → Plan → Go
- [] **Messen** 👤 `/audit-messen spec-wohngeld-openapi und spec-meldeportal-gesundheit, Bedrock und Groq` → 🤖 notiert die Ergebnisse gegen `expected` im Issue
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #28`
- [ ] **Verstehen** 👤 `/verstehen 28` (Kernfrage: warum ein Beleg allein noch keinen Verstoß beweist)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Beide Spec-Presets mit beiden Modellen ihr `expected` erfüllen und `spec-meldeportal-gesundheit` seine Pflicht-FAILs behält.
**Fürs Fachgespräch:** Testorakel mit Gegenprobe, Grenzen von Prompt-Regeln, „Das LLM urteilt, der Code prüft“.

---

### Schritt 11 – #9 GovGuard-Stack und Audit-Endpunkte

**Ziel:** Die Audit-API läuft in eu-central-1 über eine Lambda Function URL mit IAM-Auth (ADR 0018), protokolliert jeden Aufruf und bleibt im Lambda-Timeout.
**Voraussetzung:** Schritte 10b und 10c, Durchlauf aus Schritt 10a.

- [ ] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #9 umsetzen`
      Reihenfolge: `Trace` und `AuditEvent` bauen → `handler.py` → CDK-Stack mit Assertions-Tests (Tests auf das erzeugte Template)
- [ ] **Sicherheit** 👤 `/security-review` vor dem ersten Deploy
- [ ] **Einrichten** falls nötig: 👤 `/wizard cdk bootstrap für eu-central-1` → 👤 Wizard ausführen
- [ ] **Deploy + Test** 👤 „Deploye den Stack und ruf /audit/architecture mit dem größten Preset auf“ → Go → 👤 `/run`. Läuft es in den Lambda-Timeout: 👤 `/model opus`, dann `/diagnosing-bugs`
- [ ] **Zweite Meinung** 🛠 _Junie_ · 👤 „Lies AGENTS.md → Review und `gh issue view 9`. Prüfe `git diff`.“ Befunde nimmst du ins Opus-Review mit.
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #9`
- [ ] **Verstehen** 👤 `/verstehen 9` (Schwerpunkt: IAM, KMS und Audit-Protokoll)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Ein Aufruf einen Audit-Report liefert, das Audit-Ereignis in CloudWatch Logs steht (ohne Eingabetext) und die Laufzeit im Issue steht.
**Fürs Fachgespräch:** Least Privilege, KMS-CMK, Datenminimierung, Rückverfolgung, 0 € Leerlaufkosten.

---

### Schritt 12 – #11 Deploy-Pipeline und Demo-UI

**Ziel:** Jeder Push auf `main` rollt GovGuard nach dem Selbst-Audit aus; die Demo-UI auditiert Spezifikationen und Architekturen öffentlich.
**Voraussetzung:** Schritte 9 und 11.

- [ ] **Einrichten** 🆕 _Sonnet_ · 👤 `/wizard Einmalige AWS-Einrichtung für deploy.yml: OIDC-Deploy-Rolle, IAM-User für Streamlit, Secrets` → 👤 Wizard ausführen. Der Wizard ist zugleich die Anleitung, die das Ticket verlangt.
- [ ] **Bauen Pipeline** 🤖 _Sonnet_ · 👤 „Setze aus Issue #11 die `deploy.yml` um“ → Plan → Go. Die Ausnahmen für Prüfregeln (z. B. FSBP `APIGateway.4`, `Lambda.3`) entstehen hier, mit Begründung (Weichenstellung).
- [ ] **Bauen UI** 🛠 _Junie_ · 👤 „Lies docs/FAHRPLAN.md Schritt 12 und `gh issue view 11`. Baue nur die Streamlit-UI in `ui/`, ohne Archetyp-Abruf.“
- [ ] **Ausprobieren** 👤 `/run Streamlit-UI lokal starten, Preset auditieren, Screenshot`
- [ ] **Sicherheit** 🆕 _Opus_ · 👤 `/security-review`
- [ ] **Live** 👤 Pushen → Pipeline beobachten → UI auf Streamlit Community Cloud öffnen
- [ ] **Prüfen** 👤 `/code-review gegen Issue #11`
- [ ] **Verstehen** 👤 `/verstehen 11`, danach `/verstehen probe` (Generalprobe)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Ein Push den Deploy mit Selbst-Audit auslöst und die öffentliche UI ein Preset auditiert.
**Fürs Fachgespräch:** Dogfooding, begründete Ausnahmen, ein einziger Weg in die Produktion, bewusstes US-Hosting nur mit fiktiven Daten.

---

### Schritt 13 – #22 Doku zu kb_build nachziehen

**Ziel:** `ARCHITECTURE.md`, `SPEC.md`, `METHODIK.md` und die Lernkarten stimmen mit dem Code nach #19, #20 und #21 überein (Relevanzregel nach ADR 0013, Korrekturrunden, kein Ranking mehr, Pfade nach #20). Ergänzt #16, das README und die drei Erklär-Dokumente übernimmt.
**Voraussetzung:** Schritt 9e. Kein Code, nur Doku. Läuft nach dem Deploy (Zeitplan: Di 20.10.).

- [ ] **Starten** 🆕 _Sonnet_ · 👤 „Lies `gh issue view 22` und zieh die Dokumente und Lernkarten auf den Code-Stand nach“ → Plan → Go
- [ ] **Prüfen** 👤 `grep` aus dem Issue, jeden Markdown-Link in `learning/lessons/` anklicken (oder per Skript prüfen lassen), ARCHITECTURE 1.1 querlesen
- [ ] **Abschließen** 👤 committet und pusht, danach den Ordner `learning/lehrbuch/` einchecken

**Fertig, wenn:** Das `grep` aus #22 nichts Veraltetes mehr findet und alle Links der Lernkarten auf vorhandene Dateien zeigen.
**Fürs Fachgespräch:** Doku und Code müssen übereinstimmen; ADRs sind verbindlich, ältere Texte werden nachgezogen oder als überholt markiert.

---

### Schritt 14 – #16 Doku nachziehen

**Ziel:** README und die drei Erklär-Dokumente beschreiben den gebauten Stand nach ADR 0011.
**Voraussetzung:** Schritte 7, 9, 10 und 10a (#6, #12, #14, #26).

- [ ] **Starten** 🆕 _Sonnet_ · 👤 „Lies `gh issue view 16` und zieh die vier Dokumente auf den Code-Stand nach“ → Plan → Go
- [ ] **Prüfen** 👤 `grep` aus dem Issue, dann jedes Dokument querlesen (je ca. 2 Minuten)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Das `grep` aus #16 nichts Veraltetes mehr findet. Damit ist Priorität A erledigt.

---

## Nur wenn ein Tag frei wird (Schnittlinie ✂)

Start nur, wenn Schritt 14 fertig ist und vor der Abgabe ein Tag frei bleibt. Sonst sind beide im Fachgespräch Ausbau.

### Schritt 15 – #24 Pflichtanker ohne Nachwürfeln auswählen

**Ziel:** Ein `select`-Lauf ohne Cache besteht das Pflichtanker-Gate ohne Handeingriff. Bei #19 wurden CIS 3.1.4 und BSI BER.4.1 von Hand neu beurteilt; in der Probe vom 14.10. kippt CIS 3.1.4 in 1 von 5 Läufen auf `account`.
**Voraussetzung:** Schritt 9e. Kommt vor #8: Ohne diese Regel bricht ein voller Architektur-Lauf im Workflow etwa jedes fünfte Mal am Pflichtanker-Gate ab; der Cache ist seit 38b3128 ungültig.

- [ ] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #24 umsetzen` → Plan → Go (Gate-Design ist eine Weichenstellung)
      Reihenfolge: Test in `tests/test_curation.py` → Pflichtanker übersteuern `scope_level` auf `template` mit festem Satz im Auswahlprotokoll → ADR
- [ ] **Echter Lauf** 🤖 👤 „Erzeuge die Architektur-Auswahl neu“ (`select --audit-type architecture`, ohne Flag = Groq). 👤 Prüfe: Beide Gates grün, kein Cache-Eintrag von Hand gelöscht?
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #24`
- [ ] **Verstehen** 👤 `/verstehen 24` (Kernfrage: warum ein Preset das Urteil des LLM übersteuern darf, aber nur beim `scope_level`)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Ein Lauf ohne Cache beide Gates besteht und das ADR die Regel festhält.
**Fürs Fachgespräch:** Reproduzierbarkeit, Testorakel als Quelle der Wahrheit, „Das LLM urteilt, der Code wählt aus“.

---

### Schritt 16 – #8 Preset-Gate und Build-Workflow

**Ziel:** Der Build der Wissensbasis läuft per Knopfdruck in GitHub Actions und öffnet nur bei Grün einen Pull Request.
**Voraussetzung:** Schritte 8, 9e, 10 und 15.

- [ ] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #8 umsetzen` → Plan → Go
      Reihenfolge: Preset-Gate (Gesamtstatus, Pflicht-Befunde, Hash-Check; den Soll-Archetyp prüft erst #10) → `python -m kb_build` → `build-kb.yml` ohne Logik
- [ ] **Einrichten** 🆕 _Sonnet_ · 👤 `/wizard OIDC-Provider und Rolle für build-kb.yml, nur Bedrock eu.-Profil (Preset-Gate), Secret GROQ_API_KEY` → 👤 Wizard ausführen
- [ ] **Ausprobieren** 👤 Workflow in GitHub Actions starten → PR lesen, Kosten prüfen
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #8`
- [ ] **Verstehen** 👤 `/verstehen 8` (Kernfrage: warum OIDC besser ist als ein Access Key in GitHub)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Ein Workflow-Lauf einen grünen PR mit Kostenangabe geöffnet hat.
**Fürs Fachgespräch:** OIDC statt langlebiger Keys, Gate vor Merge, alte Version bleibt bei Rot aktiv.

---

## Priorität B – Golden Archetypes (entfällt, Stand 14.10.)

Im Fachgespräch Ausbau: Steckbriefe, ADR 0003 und 0009 liegen vor.

### Schritt 17 – #7 Golden Archetypes mit Freigabe

**Ziel:** ARCH-01 bis -03 sind als CDK gebaut und freigegeben, mit dokumentierten Ausnahmen.
**Voraussetzung:** Schritt 14. Node.js und CDK CLI lokal installiert.

- [ ] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #7 umsetzen`
      Reihenfolge: Allowlist-Filter (cdk-nag und Prüfregeln, aus Schritt 12) → Struktur-Soll → Compliance-Soll (N/A-Sperre) → Schleife mit höchstens 3 Runden (mit Fakes) → `cdk_runner.py`
- [ ] **Echter Build** 👤 „Baue die 3 Archetypen“ → Go. Bei Fehlern von synth oder cdk-nag: 👤 `/diagnosing-bugs`
- [ ] **Offene Frage** 👤 „Klär, ob Lambda-Logging `log-group:NAME:*` braucht“ → bei Ja: Ausnahme mit Begründung in `data/input/nag_allowlist.json`
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #7`
- [ ] **Verstehen** 👤 `/verstehen 7` (Schwerpunkt: cdk-nag und Ausnahmen)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** `archetypes.json` 3 freigegebene Archetypen mit `approval` enthält.
**Fürs Fachgespräch:** Vier-Augen-Prinzip, Risikoakzeptanz, Funktionstrennung, Least Privilege.

---

### Schritt 18 – #10 Archetyp-Auswahl

**Ziel:** Bei einer Spezifikation ohne FAIL liefert GovGuard ARCH-01, -02, -03 oder „keiner“; die UI zeigt den Archetyp.
**Voraussetzung:** Schritt 17.

- [ ] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #10 umsetzen` → Plan → Go (Auswahl, Ablehnung bei FAIL, `NONE`, Soll-Archetyp im Preset-Gate)
- [ ] **UI** 🛠 _Junie_ · 👤 „Ergänze in `ui/` den Archetyp-Abruf nach Issue #10.“
- [ ] **Deploy + Test** 🆕 _Sonnet_ · 👤 „Deploye und ruf /archetype/select mit einem Spec-Preset auf“ → Go → 👤 `/run`
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #10`
- [ ] **Verstehen** 👤 `/verstehen 10` (Kernfrage: warum „keiner passt“ eine erlaubte Antwort ist)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Das Preset liefert den Soll-Archetyp, und ein Report mit FAIL wird mit HTTP 422 abgelehnt.
**Fürs Fachgespräch:** geschlossene Antwortmenge, keine Generierung zur Laufzeit.

---

## Abschluss

### Schritt 19 – #23 Lehrbuch fertigstellen und korrigieren

**Ziel:** Das Lehrbuch aus `learning/lehrbuch/` (Faktenbasis, Stand 13.10.2026) beschreibt den gebauten Stand, ist in Claude Web ausformuliert, von dir korrigiert und in NotebookLM geladen.
**Voraussetzung:** Schritt 13 (#22), Schritt 16 (#8) nur, falls gebaut; sonst steht #8 wie Priorität B als Ausbau im Lehrbuch. Läuft vom 22. bis 25.10. als Vorbereitung auf das Fachgespräch (siehe Zeitplan).

- [ ] **Faktenbasis aktualisieren** 🆕 _Sonnet_ · 👤 „Lies `gh issue view 23` und `learning/lehrbuch/README.md` und zieh die Kapitel auf den Code-Stand nach“ → Plan → Go (Kapitel zu #8 nur, falls gebaut; Kapitel 00, 08, 10, 99; Archetypen-Kapitel nur, falls #7 gebaut ist)
- [ ] **Ausformulieren** 👤 Claude Web, ein Chat je Kapitel: Faktenbasis, `CONTEXT.md` und `docs/adr/` in ein Project laden, mit Kapitel 05 beginnen und den Stil-Prompt für alle Kapitel wiederverwenden. Zum Schluss fragen: „Welche Aussagen stehen nicht in den Dateien?“
- [ ] **Korrigieren** 👤 Zahlen, ADR-Nummern und `Datei:Funktion`-Belege gegen das Repo prüfen; alle [OFFEN] klären
- [ ] **NotebookLM** 👤 Kapitel hochladen, drei Stichprobenfragen stellen (z. B. zu Gates, Cache, Provider)
- [ ] **Abschließen** 👤 committet und pusht (Faktenbasis; ob auch die Lesetexte, entscheidet die offene Frage im Issue)

**Fertig, wenn:** Alle Kapitel ausformuliert und korrigiert sind und NotebookLM die Stichprobenfragen richtig beantwortet.
**Fürs Fachgespräch:** Du erklärst die kb-build-Pipeline ohne Notizen: LLM urteilt, Code wählt aus, Gates fangen Erfundenes ab.
