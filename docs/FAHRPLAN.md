# GovGuard – Fahrplan

Ein Eintrag je Ticket, in Bearbeitungsreihenfolge. Jeder Eintrag steht für sich: Du brauchst kein anderes Dokument, um ihn abzuarbeiten. Hake die Kästchen im Editor ab.

**Legende:** 👤 du · 🤖 Claude · 🛠 Junie (PyCharm) · ☁ braucht AWS-Zugriff · `/…` Befehl zum Eintippen. `/verstehen N <Schwerpunkt>` erklärt das Ticket als Lernkarte und fragt sie ab. Claude zeigt pro Ticket einen Plan und arbeitet nach deinem **Go** am Stück (CLAUDE.md). Die UI baut Claude Code nach einem Design-Artefakt, das Claude Code selbst anlegt und nach deinen Kommentaren überarbeitet; Junie gibt bei #9 eine zweite Meinung. Alles läuft direkt auf `main`, ohne Branches.

**Rhythmus jedes Eintrags:** _Starten → Bauen → Prüfen → Verstehen → Abschließen._

**Tagesabschluss:** 👤 `/devlog`

**Modell und Session:**

- **Sonnet baut, Opus urteilt.** Sonnet 5.5 für TDD-Zyklen mit klaren Kriterien; Opus 5.5 für Grilling, Review, Security-Review, Diagnose und IHK-Check. Opus baut auch die heiklen Tickets #1 (Fundament), #7 (Freigabe-Schleife) und #9 (IAM). Wechsel mit `/model sonnet` bzw. `/model opus`.
- **🆕 = neue Session** (`/clear`). Erste Nachricht: „Lies docs/FAHRPLAN.md Schritt N und Issue #X.“ Jeder Schritt startet frisch. Das Review läuft in einer zweiten frischen Session, damit keine Sitzung ihren eigenen Code prüft (Vier-Augen-Prinzip).
- Zusätzlich neu starten, wenn eine Session lang wird und Claude Absprachen vergisst oder sich wiederholt. Vorher den Stand committen.
- **Junie ist zweite Meinung, nicht Bauer.** Bei #4 und #5 lieferte Junie (GPT-5.2) grüne Tests mit falschen Daten; der Neubau kostete mehr Claude-Budget, als er sparte. Junie prüft deshalb nur noch bei #9 den Diff als zweite Modellfamilie (Vier-Augen-Prinzip). Junie liest `AGENTS.md` und committet nicht. Wird das Claude-Budget knapp, bekommt Junie ein Ticket nur mit vorab geschriebenen roten Tests.

**Priorität:** Nur noch Audits. Was nicht in Priorität A steht, ist aus dem Fahrplan gestrichen.

- **A – Audits (Pflicht):** Spec-Audit und Architektur-Audit laufen Ende-zu-Ende, mit vollständigem Katalog (ADR 0011), Demo-UI und Selbst-Audit (GovGuard prüft die Spezifikation seines Demo-Stands). Offene Schritte in dieser Reihenfolge: Rest von 12b, 12p–12s (#55–#58, Ordner nach ADR 0027), 12t–12v (#59–#61, Bedingungen im Spec-Audit), 12o (#54), zuletzt die Doku 13–14. Mit #36 ist der Prototyp fertig.
- **Eingefroren ab Schritt 12l:** `kb_build` und Audit-Engine werden nicht mehr geändert, Katalog und Prompts bleiben. Ausnahme ist 12n (#52, #53): Die KI-VO kommt als Quelle dazu, DSGVO und KI-VO werden in Einzelpflichten zerlegt. Das bricht G13 für den Spec-Katalog bewusst: Spec-Regeln, Spec-Galerie und Spec-Soll entstehen neu, der Architektur-Katalog bleibt. Zweite Ausnahme ist ADR 0027 (#55–#57): umstrukturieren ohne neues Verhalten, Prompts, Cache-Keys und `data/` bleiben. #58 ändert nur das LLM-Inventar des Architektur-Audits und wird gemessen. Dritte Ausnahme sind #59–#61: Vorfilter Behörde und Bedingungs-Vorlauf ändern Spec-Katalog, Spec-Audit und Spec-Galerie; der Architektur-Katalog bleibt. Bekannte Grenzen stehen im README; #48 (YAML), #49 (Build-Abbrüche) und #50 (Allow/Deny, Platzhalter) sind Ausbau.
- **Gestrichen:** Preset-Gate und Build-Workflow (#8; der Build läuft lokal per `python -m kb_build`), Golden Archetypes (#7, #10, ADR 0019). Im Fachgespräch Ausbau: Steckbriefe, ADR 0003 und 0009 liegen vor.
- **Stand 19.10.:** Kaum Budget. Die Demo-Architektur bleibt (Streamlit und Groq), kein AWS-Deploy, kein CDK. Außerhalb des Umfangs (Label `ausbau`): Haiku/Bedrock, CDK-Stack #9, Audit-Jobs #34, Pipeline #37, Recruiter-Stand #38.

**Zeitplan bis zur Präsentation:**

| Tag        | Arbeit                                                                                                                                                                                                      |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Mi 14.10.  | Schritt 10: #14 abschließen. Schritt 10a vorgezogen: TDD-Umbau Beleg per Zeilenverweis, Nachschärfen, Messungen.                                                                                            |
| Do 15.10.  | Schritt 10e: #30 Build-Log. Schritt 10f: #31 klären, Diagnose, Prüfer bauen. Schritt 15: #24 Pflichtanker (komplett, Groq)                                                                                  |
| Fr 16.10.  | Schritt 10g: #32 (bis ☁). Schritt 10i: UI und Hosting klären, Tickets neu schneiden, Design-Artefakt anlegen                                                                                                |
| Sa 17.10.  | Schritt 11: Groq-Adapter, `provider`, Fortschritt. Schritt 12: UI beginnen                                                                                                                                  |
| So 18.10.  | Schritte 12i, 12j: #46, #47. Schritt 12l: Galerie, bekannte Grenzen. Danach sind `kb_build` und Audit eingefroren                                                                                           |
| Mo 19.10.  | Schritt 12b: GovGuard-Spezifikation schreiben, Soll festlegen. Schritt 12m: #51 UI-Texte deutsch. Das Claude-Wochenlimit setzt zurück                                                                       |
| Di 20.10.  | Schritt 12n: Teil 1 Zwischenstand committen, Teil 2 Stufe „Zerlegen“ bauen (#53)                                                                                                                            |
| Mi 21.10.  | 12n: Teil 2 Wissensbasis, Spec-Galerie neu; Teil 3 SPEC und Soll. 12b: Audit, Galerie. 12p–12s: Ordner #55–#58. 12t–12v: Bedingungen #59–#61. 12o: Messkampagne #54. 13–14: Doku #22, #16. A fertig. Abgabe |
| 22.–25.10. | Verstehen: `/verstehen` für #14, #26, #24, #32, #9, #11, Schritt 19 Lehrbuch #23, Generalprobe                                                                                                              |
| Mo 26.10.  | Präsentation und Fachgespräch                                                                                                                                                                               |

**Wer baut was:**

| Schritt | Prio | Ticket                            | Baut                             | Prüft                       |
| ------- | ---- | --------------------------------- | -------------------------------- | --------------------------- |
| 1       | –    | #1 Prüfkern                       | 🤖 Opus                          | 🤖 Opus                     |
| 2       | –    | #3 Presets                        | 👤 + 🤖 Opus                     | 👤                          |
| 3       | –    | #2 Bedrock + CLI                  | 🤖 Sonnet                        | 🤖 Opus                     |
| 4       | –    | #4 BSI + CIS                      | 🛠 Junie                         | 🤖 Opus                     |
| 5       | –    | #5 DSGVO + SDM                    | 🛠 Junie                         | 🤖 Opus                     |
| 6       | A    | #13 Quellen FSBP + C5             | 🤖 Sonnet                        | 🤖 Opus                     |
| 7       | A    | #6 Bounded Catalog                | 🤖 Sonnet                        | 👤 Kontrollpunkt + 🤖 Opus  |
| 8       | A    | #15 5. Preset                     | 👤 + 🤖 Opus                     | 👤                          |
| 9       | A    | #12 Prüfregeln + Gate             | 🤖 Opus                          | 🤖 Opus · 🛠 Junie          |
| 9a      | A    | #18 Kontoweite Pflichten          | 🤖 Sonnet                        | 👤 Kontrollpunkt + 🤖 Opus  |
| 9b      | A    | #17 Gate Eigenschaftsnamen        | 🤖 Sonnet                        | 🤖 Opus                     |
| 9c      | A    | #20 Ordnerstruktur                | 🤖 Opus                          | 🤖 Opus                     |
| 9d      | A    | #19 Typen im Prüfumfang           | 🤖 Sonnet                        | 🤖 Opus                     |
| 9e      | A    | #21 Groq als Build-Standard       | 🤖 Sonnet                        | 🤖 Opus                     |
| 9g      | A    | #25 ADR 0015 Terraform-Grenze     | 🤖 Sonnet                        | 👤                          |
| 10      | A    | #14 Ressourceninventar + Pakete   | 🤖 Opus                          | 🤖 Opus                     |
| 10a     | A    | #26 Belege bei großen Eingaben    | 🤖 Opus                          | 🤖 Opus                     |
| 10b     | A    | #27 KI-Governance sichtbar        | 🤖 Sonnet                        | 🤖 Opus                     |
| 10c     | A    | #28 FAIL nur bei Verstoß          | 🤖 Opus                          | 🤖 Opus                     |
| 10d     | A    | #29 Spec-Katalog Festlegungen     | 🤖 Opus                          | 🤖 Opus                     |
| 10e     | A    | #30 Build-Log Retry-Gründe        | 🤖 Sonnet                        | 🤖 Opus                     |
| 10f     | A    | #31 FAIL-Prüfer zur Laufzeit      | 🤖 Opus                          | 🤖 Opus                     |
| 15      | A    | #24 Pflichtanker stabil           | 🤖 Sonnet                        | 🤖 Opus                     |
| 10g     | A    | #32 Fail closed nach Retry        | 🤖 Opus                          | 🤖 Opus                     |
| 10i     | A    | UI und Hosting klären             | 👤 + 🤖 Opus (Design-Artefakt)   | 👤                          |
| 11      | A    | #35 Laufzeit: Groq, Fortschritt   | 🤖 Opus                          | 🤖 Opus                     |
| 12      | A    | #11 Demo-UI                       | 🤖 Sonnet (nach Design-Artefakt) | 🤖 Opus                     |
| 12c     | A    | #40 Screenshot-Regression         | 🤖 Opus                          | 🤖 Opus                     |
| 12d     | A    | #41 Breite, Start, Erstellen      | 🤖 Sonnet                        | 👤 Vergleichsbild + 🤖 Opus |
| 12e     | A    | #42 Kopf und Kacheln              | 🤖 Sonnet                        | 👤 Vergleichsbild + 🤖 Opus |
| 12g     | A    | #44 UI-Interaktionen testen       | 🤖 Sonnet                        | 🤖 Opus                     |
| 12f     | A    | #43 Befundtabelle, Quelle, Lücken | 🤖 Opus                          | 👤 Vergleichsbild + 🤖 Opus |
| 12h     | A    | #45 Befundtabelle mit Spalten     | 🤖 Opus                          | 👤 Vergleichsbild + 🤖 Opus |
| 12a     | A    | #39 Zitatprüfung ohne Markdown    | 🤖 Sonnet                        | 🤖 Opus                     |
| 12i     | A    | #46 Arch-Freitext: offene Welt    | 🤖 Opus                          | 🤖 Opus                     |
| 12j     | A    | #47 Arch-Katalog zu wörtlich      | 🤖 Opus                          | 🤖 Opus                     |
| 12k     | A    | #48 CloudFormation-YAML           | 🤖 Sonnet                        | 🤖 Opus                     |
| 11b     | –    | #9 CDK-Stack (Ausbau)             | 🤖 Opus                          | 🤖 Opus · 🛠 Junie          |
| 11a     | –    | #34 Audit-Jobs (Ausbau)           | 🤖 Opus                          | 🤖 Opus                     |
| 12m     | A    | #51 UI-Texte deutsch              | 🤖 Sonnet                        | 👤 Vergleichsbild + 🤖 Opus |
| 12n     | A    | #52 KI-VO, #53 Zerlegen           | 🤖 Opus                          | 🤖 Opus                     |
| 12b     | A    | #36 Selbst-Audit Spec, Galerie    | 👤 + 🤖 Opus                     | 👤                          |
| 12p     | A    | #55 Ordner govguard + UI          | 🤖 Sonnet                        | 🤖 Opus                     |
| 12q     | A    | #57 kb_build LLM-Schritt, Gates   | 🤖 Sonnet                        | 👤 Gegenprobe + 🤖 Opus     |
| 12r     | A    | #56 Modellaufrufe Laufzeit        | 🤖 Sonnet                        | 🤖 Opus                     |
| 12s     | A    | #58 Inventar NativeOutput         | 👤 Messung + 🤖 Sonnet           | 👤                          |
| 12o     | A    | #54 Messkampagne Stabilität       | 👤 Messung + 🤖 Sonnet           | 🤖 Opus                     |
| 10h     | A    | #33 Gegenprobe (Groq, erledigt)   | 👤 Messung                       | 👤                          |
| 13      | A    | #22 Doku zu kb_build nachziehen   | 🤖 Sonnet                        | 👤                          |
| 14      | A    | #16 Doku nachziehen               | 👤 + 🤖 Sonnet                   | 👤                          |
| 19      | –    | #23 Lehrbuch fertigstellen        | 👤 + Claude Web                  | 👤                          |
| R       | –    | #38 Recruiter-Stand (Ausbau)      | 🤖 Opus                          | 🤖 Opus                     |

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
- [x] **Bauen** 👤 „Prüfe die Modell-ID mit `aws bedrock list-inference-profiles --region eu-central-1`“ → 🤖 korrigiert die ID, falls nötig, auch in ADR 0001 und ARCHITECTURE 2.1 (heute DESIGN 2.5).
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
- [x] **Messen** 👤 `/audit-messen spec-wohngeld-openapi je 2× mit Bedrock und Groq, spec-meldeportal-gesundheit mit Bedrock und Groq, arch-antragseingang-fehlerhaft mit Bedrock` → 🤖 notiert die Ergebnisse gegen `expected` im Issue
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #28` (Messkriterien sind nach #29 gewandert)
- [x] **Verstehen** 👤 `/verstehen 28` (Kernfrage: warum ein Beleg allein noch keinen Verstoß beweist)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Prompt-Regel der offenen Welt, `temperature: 0` und die Obergrenze für Output-Tokens getestet sind und ADR 0020 vorliegt. Die Messkriterien prüft Schritt 10d.
**Fürs Fachgespräch:** Testorakel mit Gegenprobe, Grenzen von Prompt-Regeln, „Das LLM urteilt, der Code prüft“.

---

### Schritt 10d – #29 Wissensbasis: `violation_if` beschreibt im Spec-Katalog nur festgelegte Verstöße

**Ziel:** `violation_if` im Spec-Katalog beschreibt eine Festlegung, kein Fehlen (offene Welt, ADR 0020), damit `spec-wohngeld-openapi` sein `expected` (WARN) erfüllt.
**Voraussetzung:** Schritt 10c. Schritt 11 hängt nicht davon ab, der Katalog ist JSON in S3 (ADR 0011). Wird es knapp, rutscht 10d hinter Schritt 11.

- [x] **Klären** 🆕 _Opus_ · 👤 `/grilling Offene Fragen in #29: Regeln, die nur ein Fehlen kennen` (Prompt-Design ist eine Weichenstellung) → 🤖 übernimmt die Messkriterien aus #28 ins Issue: Gegenprobe `arch-antragseingang-fehlerhaft`, Schwankung
- [x] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #29 umsetzen` → Plan → Go
- [x] **Echter Lauf** 🤖 👤 `python -m kb_build rules --audit-type spec` (Groq, ADR 0014) → 👤 prüft: Qualitätsbericht überall 0, in `git diff data/knowledge_base/rules_spec.json` kommt keine Regel-ID dazu und keine fällt weg (Auswahl unverändert) → 🤖 notiert Requests, Input- und Output-Tokens und die Retries des Prüfers aus `data/intermediate/logs/rules_spec.log` im Issue → 👤 committet das Log zusammen mit `rules_spec.json`
- [x] **Messen** 👤 `/audit-messen spec-wohngeld-openapi je 2× mit Bedrock und Groq, spec-meldeportal-gesundheit mit Bedrock und Groq, arch-antragseingang-fehlerhaft mit Bedrock` → 🤖 notiert im Issue die Ergebnisse gegen `expected` und die Schwankung je Modell (Prüfregeln mit anderem Status zwischen Lauf 1 und 2)
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #29`
- [-] **Verstehen** 👤 `/verstehen 29` (Kernfrage: warum ein Verstoßkriterium in der offenen Welt eine Festlegung beschreiben muss)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** `spec-wohngeld-openapi` mit Bedrock in zwei Läufen WARN zeigt und die Schwankung im Issue steht. Groq und M60.P01 folgen in #31, die Gegenproben mit Bedrock in #32.
**Fürs Fachgespräch:** Offene und geschlossene Welt, Datenqualität der Wissensbasis vor Prompt-Tricks.

---

### Schritt 10e – #30 Build-Log: Grund jedes Retries in select (und Schema-Retries in rules)

**Ziel:** Das Build-Log nennt zu jedem Retry von `select` und `rules` die Anforderung und den Grund, auch bei Schema-Fehlern. Heute steht für `select` nur die Zahl im Log.
**Voraussetzung:** Schritt 10d (Retry-Zeile in `rules`). Klein, Schritt 11 hängt nicht davon ab. Wird es knapp, rutscht 10e hinter Schritt 11.

- [x] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #30 umsetzen` → Plan → Go (offene Frage im Issue: Deps oder `capture_run_messages`)
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #30`
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Jeder Retry in `select` und `rules` mit Anforderung und Grund im Build-Log steht und Antworten aus dem Cache keine Zeile erzeugen.
**Fürs Fachgespräch:** Nachvollziehbarkeit auch im Build, nicht nur im Audit-Report.

---

### Schritt 10f – #31 Spec-Audit: LLM-Prüfer bestätigt jedes FAIL zur Laufzeit (offene Welt)

**Ziel:** Ein LLM-Prüfer bestätigt jedes FAIL im Spec-Audit oder stuft es auf WARN herab, für Bedrock und Groq. Groq bleibt Option, notfalls mit bekannter Grenze (ADR 0016).
**Voraussetzung:** Schritt 10d (neuer Spec-Katalog). Schritt 11 hängt nicht davon ab, die UI in Schritt 12 zeigt aber den Zähler des Prüfers. Wird es knapp, rutscht 10f hinter Schritt 11.

- [x] **Klären** 🆕 _Opus_ · 👤 `/grilling Offene Fragen in #31: Prompt, Gate, Prüfer zur Laufzeit oder Groq streichen?` (Prompt-Design und Kosten sind Weichenstellungen)
- [x] **Diagnose** 👤 `/audit-messen spec-wohngeld-openapi mit Groq und einem Katalog nur aus den 12 Regeln in #31`
- [x] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #31 umsetzen` → Plan → Go. Halt beim Prompt des Prüfers (Weichenstellung Prompt-Design), danach weiter bis zur Integration in `run_audit`.
- [x] **Messen** 👤 `/audit-messen spec-wohngeld-openapi 2× mit Groq, spec-meldeportal-gesundheit mit Groq` → 🤖 notiert im Issue die Ergebnisse gegen `expected`. Die Gegenprobe mit Bedrock folgt in Schritt 10h (#33).
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #31`
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Art. 9 bei `spec-meldeportal-gesundheit` mit Groq FAIL bleibt (Bedrock in #33), jedes Urteil des Prüfers in `corrections` steht und Wohngeld mit Groq entweder WARN zeigt oder die Grenze in ADR 0016 steht.
**Fürs Fachgespräch:** LLM-as-a-Judge zur Laufzeit, Herabstufen statt Retry, im Zweifel bleibt der strengere Status. Überanpassung an das Testorakel vermeiden.

---

### Schritt 15 – #24 Pflichtanker ohne Nachwürfeln auswählen

**Ziel:** Ein `select`-Lauf ohne Cache besteht das Pflichtanker-Gate ohne Handeingriff. Bei #19 wurden CIS 3.1.4 und BSI BER.4.1 von Hand neu beurteilt; in der Probe vom 14.10. kippt CIS 3.1.4 in 1 von 5 Läufen auf `account`.
**Voraussetzung:** Schritt 9e. Läuft komplett ohne AWS (Groq, ADR 0014). Ohne diese Regel bricht ein voller Architektur-Lauf etwa jedes fünfte Mal am Pflichtanker-Gate ab; der Cache ist seit 38b3128 ungültig.

- [x] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #24 umsetzen` → Plan → Go (Gate-Design ist eine Weichenstellung)
      Reihenfolge: Test in `tests/test_curation.py` → Pflichtanker übersteuern `scope_level` auf `template` mit festem Satz im Auswahlprotokoll → ADR
- [x] **Echter Lauf** 🤖 👤 „Erzeuge die Architektur-Auswahl neu“ (`select --audit-type architecture`, ohne Flag = Groq). 👤 Prüfe: Beide Gates grün, kein Cache-Eintrag von Hand gelöscht?
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #24`
- [-] **Verstehen** 👤 `/verstehen 24` (Kernfrage: warum ein Preset das Urteil des LLM übersteuern darf, aber nur beim `scope_level`)
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Ein Lauf ohne Cache beide Gates besteht und das ADR die Regel festhält.
**Fürs Fachgespräch:** Reproduzierbarkeit, Testorakel als Quelle der Wahrheit, „Das LLM urteilt, der Code wählt aus“.

---

### Schritt 10g – #32 Audit fail closed nach Retry: Modell korrigiert den Status, aber nicht die Pflichtfelder

**Ziel:** Die Gegenproben `arch-antragseingang-fehlerhaft` und `spec-meldeportal-gesundheit` liefern wieder einen Audit-Report, statt nach einem Retry fail closed abzubrechen.
**Voraussetzung:** Schritt 10d (Messungen in #29). Schritt 11 hängt nicht davon ab, aber die Demo braucht Gegenproben mit Ergebnis.

- [x] **Klären** 🆕 _Opus_ · 👤 `/grilling Offene Fragen in #32: Retry-Prompt mit Pflichtfeldern oder Empfehlung aus der Prüfregel; doppelte Befunde` (Prompt-Design ist eine Weichenstellung)
- [x] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #32 umsetzen` → Plan → Go
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #32` (Code-Stand, ohne Messung)
- [x] ~~☁ **Messen** mit Bedrock~~ entfällt (ADR 0023: Bedrock abbestellt); Messung mit Groq steht im Issue
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Beide Gegenproben mit Groq ohne fail closed durchlaufen und kein Befund ohne Pflichtfelder in den Report kommt.
**Fürs Fachgespräch:** Fail closed als Sicherheitsprinzip und seine Kosten für die Verfügbarkeit, „Was der Code weiß, fragt man das Modell nicht“.

---

### Schritt 10i – UI und Hosting klären (Demo und Recruiter-Stand)

**Ziel:** ADR 0023 hält Hosting, Datenfluss und Kosten für Demo und Recruiter-Stand fest; #9, #11 und #34 sind danach neu geschnitten, ohne offene Fragen.
**Voraussetzung:** keine. Eingang: `docs/research/ui-hosting/ergebnisse-2026-10-16.md` (Entscheidungen, Fakten und offene Fragen vom 16.10.). Datenresidenz, Verschlüsselung und Kosten sind Weichenstellungen.

- [x] **Klären** 🆕 _Opus_ · 👤 `/grill-with-docs UI und Hosting: Lies docs/research/ui-hosting/ergebnisse-2026-10-16.md und gh issue view 9, 11, 34. Kläre die offenen Fragen, schreib ADR 0023, ergänze CONTEXT.md`
- [x] **Tickets** 🤖 _Opus_ (gleiche Session) · 👤 `/to-tickets nach ADR 0023: #9 in Laufzeit und Stack teilen, #11 auf Demo-UI, #34 neu, Ticket Recruiter-Stand` → 🤖 passt die Ticketnummern in den Schritten 11–12b und R an
- [x] **Design** 🆕 _Opus_ · 👤 „Lege nach `docs/research/ui-hosting/claude-design-brief.md` das Design-Artefakt für die UI an, mit Daten aus `beispiel-reports/`“ → 🤖 baut die drei Seiten als Artboards (nur baubar mit Streamlit) und schreibt den Link in #11 → 👤 kommentiert im Artefakt → 👤 „Arbeite meine Kommentare im Design-Artefakt ein“, bis es passt
- [-] **Recherche** (optional) 👤 Gemini Deep Research mit `docs/research/ui-hosting/gemini-research-fragen.md` → Ergebnis in denselben Ordner
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** ADR 0023 steht, die Tickets keine offenen Fragen mehr haben und das Design-Artefakt alle drei Seiten der UI zeigt, ohne offene Kommentare und mit Link in #11.
**Fürs Fachgespräch:** Bewusster Trade-off zwischen Datenresidenz, Kosten und Verfügbarkeit; teuer ist nicht AWS, sondern das Modell.

---

### Schritt 11 – #35 Laufzeit: Groq-Adapter, Provider und Fortschritt

**Ziel:** `run_audit` läuft mit Groq als Standard (Bedrock nur per CLI) und meldet seinen Fortschritt; die UI kann es ohne AWS direkt aufrufen.
**Voraussetzung:** Schritt 10i. Läuft komplett ohne AWS.

- [x] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #35 umsetzen` → Plan → Go
      Reihenfolge: Groq-Adapter von `kb_build` nach `govguard` → Flag `--provider` in der CLI → Fortschritt aus `run_audit` (Prüflogik bleibt rein, Test mit `FunctionModel`)
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #35`
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** `python -m govguard.cli spec --provider groq …` einen Report liefert und der Test die Fortschrittsmeldungen in der richtigen Reihenfolge sieht.
**Fürs Fachgespräch:** Kein stilles Umschalten, `model_id` im Report, Fortschritt als Naht ohne Seiteneffekt in der Prüflogik.

---

### Schritt 12 – #11 Demo-UI auf Streamlit Community Cloud

**Ziel:** Die UI zeigt gespeicherte Audits samt Quelldokument (Befund → Textstelle) und erstellt Audits mit Fortschrittsanzeige; sie läuft öffentlich auf Streamlit Community Cloud.
**Voraussetzung:** Schritte 10i (Design-Artefakt) und 11.

- [x] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #11 umsetzen, das Design-Artefakt aus #11 ist die Vorlage` → Plan → Go
- [x] **Ausprobieren** 👤 `/run Streamlit-UI lokal mit Beispiel-Report starten, Screenshot`
- [x] **Sicherheit** 🆕 _Opus_ · 👤 `/security-review` (Passwort, Secrets, Eingabelänge)
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #11`
- [x] **Live** 👤 App auf Streamlit Community Cloud anlegen, `GROQ_API_KEY` und Passwort als Secrets eintragen → ein Preset auditieren
- [-] **Verstehen** 👤 `/verstehen 11`
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Die öffentliche UI ein gespeichertes Audit mit Sprung zur Textstelle zeigt und ein neues Audit mit Fortschrittsanzeige erstellt.
**Fürs Fachgespräch:** Bewusstes US-Hosting nur mit fiktiven Daten (ADR 0004, 0016), Passwort als Kostenbremse.

---

### Schritt 12c – #40 Demo-UI: Screenshot-Regression mit Playwright

**Ziel:** Ein Test fotografiert die vier Ansichten der UI und vergleicht sie mit freigegebenen Referenzbildern; je Ansicht entsteht ein Vergleichsbild „Design | Streamlit“.
**Voraussetzung:** Schritt 12. Läuft komplett ohne AWS.

- [x] **Soll-Bilder** 🤖 _Opus_ · 👤 loggt sich in einem Chrome mit eigenem Profil ein, 🤖 fotografiert die Artboards per Playwright über CDP → `tests/visual/design/start.png`, `gallery-spec.png`, `gallery-arch.png`, `create.png`. Ändert sich das Design: 👤 `/design-screenshots`
- [x] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #40 umsetzen` → Plan → Go
      Reihenfolge: Abhängigkeiten und Marker → Server-Fixture → Bildvergleich (Unit-Test ohne Browser) → vier Ansichten → Vergleichsbilder → zweimal stabil grün
- [x] **Freigeben** 👤 Referenzbilder in `tests/visual/` ansehen: Sie zeigen bewusst den heutigen Stand
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #40`
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** `uv run pytest -m visual` zweimal hintereinander grün ist und normales `uv run pytest` ohne Browser läuft.
**Fürs Fachgespräch:** Regressionstest als Sicherheitsnetz, Referenzbild als freigegebener Soll-Stand, warum ein Mockup kein Pixel-Orakel ist.

---

### Schritt 12d – #41 Demo-UI: Rahmen der App, Start & Hilfe und Audit erstellen

**Ziel:** Rahmen der App (Breite, Sidebar, Theme), Start-Seite und das Formular „Audit erstellen“ entsprechen dem Design-Artefakt.
**Voraussetzung:** Schritt 12c.

- [x] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #41 umsetzen, Soll-Bilder in tests/visual/design/` → Plan → Go
- [x] **Ansehen** 👤 alle vier Vergleichsbilder `tests/visual/output/*-design.png` prüfen, dann `uv run pytest -m visual --update-snapshots`
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #41`
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Alle Referenzbilder nach Sichtvergleich neu freigegeben sind und `pytest -m visual` zweimal grün ist.
**Fürs Fachgespräch:** Native Streamlit-Mittel (Theme, Rahmen) vor eigenem CSS.

---

### Schritt 12e – #42 Demo-UI: Audits ansehen – Kopf und Kacheln

**Ziel:** Titel, Download und Gesamtstatus in einem Rahmen, farbige Statuskacheln, Soll-Abgleich als Kachel.
**Voraussetzung:** Schritt 12d.

- [x] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #42 umsetzen, Soll-Bilder in tests/visual/design/` → Plan → Go
- [x] **Ansehen** 👤 Vergleichsbilder für Audits ansehen prüfen, dann Referenzbilder nur dieser Seite neu schreiben
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #42`
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Nur die Referenzbilder von Audits ansehen sich geändert haben und `pytest -m visual` grün ist.
**Fürs Fachgespräch:** Nie Farbe allein: Symbol, Wort und Farbe je Status (WCAG AA).

---

### Schritt 12g – #44 Demo-UI: Interaktionen automatisiert testen

**Ziel:** Jede Interaktion der Demo-UI hat einen Test auf der billigsten Ebene, die sie sieht; ein Wächter-Test findet neue Bedienelemente ohne Test (ADR 0024).
**Voraussetzung:** Schritt 12e.

- [x] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #44 umsetzen` → Plan → Go
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #44`
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Der Wächter-Test grün ist, `uv run pytest` ohne Browser läuft und `pytest -m visual` zweimal grün ist.
**Fürs Fachgespräch:** Testpyramide (ADR 0024): Logik ohne UI, Widgets mit AppTest, nur CSS und eigenes HTML im Browser.

---

### Schritt 12f – #43 Demo-UI: Audits ansehen – Befundtabelle, Quellenfilter und Lücken

**Ziel:** Befundtabelle mit Zeilenumbruch und Klick auf die Zeile, Quellenfilter mit „Alle“, Lückenliste mit Scrollbalken.
**Voraussetzung:** Schritt 12g.

- [x] **Klick-Technik** 🆕 _Opus_ · 👤 `/prototype Klick auf Tabellenzeile: eigene Komponente gegen gestylte Streamlit-Widgets, mit einem Galerie-Report` → beide Varianten ausprobieren, Wahl als Kommentar in #43
- [x] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #43 umsetzen, Soll-Bilder in tests/visual/design/` → Plan → Go
- [x] **Ansehen** 👤 Vergleichsbilder für Audits ansehen prüfen, dann Referenzbilder nur dieser Seite neu schreiben
- [x] **Sicherheit** 🆕 _Opus_ · 👤 `/security-review` (Button-Labels zeigen LLM-Text als Markdown)
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #43`
- [x] **Live** 👤 Streamlit Community Cloud neu laden, ein Preset ansehen
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Ein Klick auf eine Tabellenzeile den Befund wählt, lange Texte umbrechen und `pytest -m visual` grün ist.
**Fürs Fachgespräch:** LLM-Text escaped ins Label (Schutz vor Injection), native Widgets vor eigener Komponente (ADR 0024).

---

### Schritt 12h – #45 Demo-UI: Befundtabelle mit Spalten und Pfeiltasten wie im Design

**Ziel:** Spec- und Architektur-Audit zeigen die Befunde als Tabelle wie im Design; Klick, ↑/↓ und Enter wählen einen Befund; der Quellenfilter mit „Alle“ sieht aus wie im Design.
**Voraussetzung:** Schritt 12f. Grundlage ist Variante A im Branch `prototype/43-row-click`.

- [x] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #45 umsetzen, Soll-Bilder in tests/visual/design/` → Plan → Go
- [x] **Ansehen** 👤 Vergleichsbilder für Audits ansehen prüfen, ↑/↓ und Enter in Chrome ausprobieren, dann Referenzbilder nur dieser Seite neu schreiben
- [x] **Sicherheit** 🆕 _Opus_ · 👤 `/security-review` (eigenes HTML und JS zeigen LLM-Text)
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #45`
- [x] **Live** 👤 Streamlit Community Cloud neu laden, ein Spec- und ein Architektur-Preset ansehen
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Beide Audit-Arten aussehen wie die Soll-Bilder, ↑/↓ + Enter einen Befund wählt und `pytest -m visual` grün ist.
**Fürs Fachgespräch:** Roving Tabindex (nur eine Zeile ist per Tab erreichbar, die Pfeile wandern darin, WAI-ARIA) und `textContent` statt `innerHTML` für LLM-Text.

---

### Schritt 12a – #39 Inventur: Zitatprüfung ignoriert Markdown-Hervorhebung

**Ziel:** Ein Architektur-Audit von Freitext mit `**…**` bricht nicht mehr fail closed ab, weil das Modell ohne Sternchen zitiert.
**Voraussetzung:** Schritt 12. Läuft komplett ohne AWS.

- [x] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #39 umsetzen` → Plan → Go
      Reihenfolge: Test für `contains_quote` mit und ohne `**` → Umsetzung in `text.py` → Gate-Tests von `kb_build` grün
- [x] **Messen** 🆕 _Opus_ · 👤 `/audit-messen arch-protokollarchiv mit Groq, Report nach data/gallery/`
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #39`
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** `arch-protokollarchiv` mit Groq durchläuft und sein Report in der Galerie liegt.
**Fürs Fachgespräch:** Fail closed ist richtig, aber die Prüfung muss dieselbe Normalisierung wie das Lesen haben: Formatierung ist kein Inhalt.

---

### Schritt 12i – #46 Architektur-Freitext: FAIL nur bei festgelegtem Verstoß (offene Welt)

**Ziel:** Ein Architektur-Audit von Freitext vergibt FAIL nur für einen festgelegten Verstoß, nicht für eine fehlende Angabe. Ein CloudFormation-Template bleibt geschlossene Welt (ADR 0020).
**Voraussetzung:** Schritt 12a (#39). Läuft komplett ohne AWS.

- [x] **Klären** 🆕 _Opus_ · 👤 `/grilling Offene Frage in #46: Prompt-Regel oder FAIL-Prüfer für Architektur-Freitext?` (Prompt-Design ist eine Weichenstellung)
- [x] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #46 umsetzen` → Plan → Go. Prompt laut Akzeptanzkriterien in #46, Spec-Text bleibt zeichengleich.
- [x] **Messen** 🆕 _Opus_ · 👤 `/audit-messen arch-protokollarchiv 2× mit Groq, Report nach data/gallery/` → 🤖 notiert im Issue die FAILs wegen Fehlens, CIS 3.1.4, DET.3.1 und die Schwankung.
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #46`
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** `arch-protokollarchiv` mit Groq in zwei Läufen kein FAIL wegen Fehlens zeigt, CIS 3.1.4 PASS ist und Templates weiter FAIL für fehlende Einstellungen zeigen. DET.3.1 PASS und `expected` folgen in Schritt 12j (#47).
**Fürs Fachgespräch:** Offene und geschlossene Welt: Bei Freitext ist eine fehlende Angabe Prüfbedarf (WARN), bei einem Template der unsichere Standardwert (FAIL). Das entscheidet der Code, nicht das Modell.

---

### Schritt 12j – #47 Architektur-Katalog: zu wörtliche Prüfregeln (S3.5, KONF.11.7.2.1)

**Ziel:** Prüfregeln im Architektur-Katalog werten eine gleichwertige Umsetzung nicht als Verstoß. Behoben im Build, nicht von Hand im Katalog.
**Voraussetzung:** Schritt 12i (#46). Läuft komplett ohne AWS.

- [x] **Klären** 🆕 _Opus_ · 👤 `/grilling Offene Fragen in #47: Einzelfälle oder Muster, Teil- oder Voll-Rebuild?` (Prompt-Design ist eine Weichenstellung)
- [x] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #47 umsetzen` → Plan → Go. Halt beim Prompt (Weichenstellung Prompt-Design).
- [x] **Bauen** 🆕 _Opus_ · 👤 `python -m kb_build` für den Architektur-Katalog (Umfang laut Klären)
- [x] **Messen** 🆕 _Opus_ · 👤 `/audit-messen arch-protokollarchiv 2× mit Groq, Report nach data/gallery/`, danach `arch-fristenwecker` und `arch-antragseingang-fehlerhaft` je 1× → 🤖 notiert im Issue die Ergebnisse gegen `expected` und die Schwankung.
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #47`
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** `arch-protokollarchiv` mit Groq zweimal `expected` erreicht und beide Templates weiter `expected` erreichen.
**Fürs Fachgespräch:** Eine Prüfregel prüft das Schutzziel, nicht eine Schreibweise: Deny bei `false` und Allow nur bei `true` erzwingen beide TLS.

---

### Schritt 12l – Audit und kb_build abschließen: Galerie und bekannte Grenzen (#47–#50)

**Ziel:** Die Galerie zeigt die Architektur-Reports zum neuen Katalog aus #47. #48, #49 und #50 sind als bekannte Grenzen dokumentiert und mit Label `ausbau` geschlossen. Danach bleiben `kb_build` und Audit-Engine unverändert.
**Voraussetzung:** Schritt 12j (#47) committet. Kein LLM-Lauf, keine Kosten: Die Reports stammen aus den Messläufen von #47 und liegen in `data/intermediate/reports_47/` (gleicher Katalog-Hash wie `rules_arch.json`).

- [x] **Galerie** 🆕 _Sonnet_ · 👤 „Lies FAHRPLAN Schritt 12l. Ersetze die drei Architektur-Reports in `data/gallery/` durch die Reports aus `data/intermediate/reports_47/` und zieh die Tests nach“ → Plan → Go
      Zuordnung: `report_protokoll1` → `arch-protokollarchiv`, `report_fristenwecker` → `arch-fristenwecker`, `report_antragseingang` → `arch-antragseingang-fehlerhaft`. Neun Tests schreiben Zahlen der alten Reports fest (`test_review`, `test_ui_gallery_arch`, `test_ui_gallery_selection`, `test_ui_pages`, `test_ui_report_header`). `preset.json` bleibt unverändert: Die UI zeigt die Abweichung DET.3.1 (Soll PASS, Ist WARN) ehrlich an.
- [x] **Ansehen** 👤 `uv run pytest -m visual`, Vergleichsbilder der Architektur-Galerie ansehen, dann `--update-snapshots`
- [x] **Bekannte Grenzen** 🤖 im selben Lauf: README → _Bekannte Grenzen_ um drei Punkte ergänzen (je ein Satz mit Ticket): YAML gilt als offene Welt (#48); der Build bricht mit Groq oft an einer Regel ab, Wiederholen hilft (#49); S3.5, DLS.2.2, IAM-09.01AC und BER.5.9 werten Deny bei `false` als Verstoß, 12 Regeln enthalten Platzhalter (#50)
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen FAHRPLAN Schritt 12l`
- [x] **Live** 👤 Streamlit Community Cloud neu laden, `arch-protokollarchiv` ansehen
- [x] **Abschließen** 👤 committet und pusht, schließt #47; #48, #49 und #50 bekommen das Label `ausbau`, einen Kommentar mit Verweis auf README _Bekannte Grenzen_ und werden geschlossen (`gh issue close N --reason "not planned"`)

**Fertig, wenn:** Die Galerie die Reports zum Katalog-Hash von `rules_arch.json` zeigt, `pytest` und `pytest -m visual` grün sind und das README die drei Grenzen nennt.
**Fürs Fachgespräch:** Bewusst eingefroren: Ein bekannter, dokumentierter Fehler mit Ticket ist besser als eine letzte Änderung ohne Messung. Jeder Report trägt `catalog_sha256`, damit ist nachweisbar, mit welchem Katalog er entstand.

---

### Schritt 11b – #9 Stack per CDK (Ausbau)

Am 19.10. aus dem Umfang genommen (Budget): Die Demo bleibt bei Streamlit und Groq, ohne AWS und ohne CDK. #9 ist mit Label `ausbau` geschlossen.
**Fürs Fachgespräch:** Ausbau: Lambda mit Function URL, KMS-CMK, Least Privilege und cdk-nag als Gate (ADR 0018, 0023).

---

### Schritt 11a – #34 Audit-Jobs in S3 (Ausbau)

Am 19.10. aus dem Umfang genommen (Budget). #34 ist mit Label `ausbau` geschlossen; die Demo läuft synchron.
**Fürs Fachgespräch:** Asynchroner Job mit Job-ID statt HTTP-Timeout, Löschfrist 1 Tag statt Object Lock (Art. 17 DSGVO).

---

### Schritt 12m – #51 UI-Texte deutsch: Musterfall und Status-Bezeichnungen

**Ziel:** Die Oberfläche sagt „Musterfall“ statt „Preset“ und zeigt die Status deutsch (Einhaltung belegt, Prüfbedarf, Verstoß belegt, Nicht anwendbar). JSON-Report, Code und Prompts behalten PASS/WARN/FAIL/N/A.
**Voraussetzung:** Schritt 12b bis „Soll festlegen“. Muss vor „Erzeugen“ in 12b fertig sein, denn #51 ändert `docs/SPEC.md` (G2), und der Galerie-Report hängt an ihrer Prüfsumme. Kein LLM-Lauf.

- [x] **Klären** 👤 offene Frage in #51 beantworten („Erfüllt“ oder „Einhaltung belegt“), dann Label `ready-for-agent`
- [x] **Bauen** 🆕 _Sonnet_ · 👤 „Lies FAHRPLAN Schritt 12m und Issue #51“ → Plan → Go
      Zuordnung nur in `style.LOOKS`. In `docs/SPEC.md` die Tabelle in G2 um die deutsche Bezeichnung ergänzen und nach `data/input/presets/spec-govguard/SPEC.md` kopieren; ein Test prüft, dass jede Bezeichnung aus `LOOKS` in `SPEC.md` steht. Zeilenangabe im Soll-Kommentar von #36 nachziehen.
- [x] **Ansehen** 👤 `uv run pytest -m visual`, Vergleichsbilder ansehen (die Design-Bilder zeigen noch die alten Kürzel), dann `--update-snapshots`
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #51`
- [x] **Abschließen** 👤 committet und pusht, schließt #51

**Fertig, wenn:** Kein UI-Text „Preset“ enthält, die Status deutsch erscheinen, der JSON-Report unverändert ist und `pytest`, `pytest -m visual` und ruff grün sind.
**Fürs Fachgespräch:** Anzeige und Datenwert sind getrennt: Die Oberfläche spricht die Sprache der Behörde, der JSON-Report bleibt maschinenlesbar und stabil.

---

### Schritt 12n – #52 und #53 KI-Verordnung als Quelle, DSGVO und KI-VO zerlegt

**Ziel:** Die KI-Verordnung kommt als Quelle ins Spec-Audit (#52). Eine Bau-Stufe „Zerlegen“ macht aus DSGVO- und KI-VO-Artikeln Einzelpflichten mit Anker auf Absatz oder Buchstabe (#53): Der Code liefert Abschnitte und Zitate, das LLM gruppiert sie (`alle_gelten`, `eine_genuegt`, `je_nach_risiko`, `keine_pflicht`). `spec-govguard` prüft GovGuards eigene Einstufung.
**Voraussetzung:** Schritt 12m. Muss vor „Erzeugen“ in 12b fertig sein. Prototyp der Zerlegung: Branch `prototype/zerlegen-rechtsquellen`, Ergebnis im ersten Kommentar von #53. Groq-Bau kostet wenige Cent.

**Teil 1 – Quelle KI-VO (#52)**

- [x] **Quelle** 🆕 _Opus_ · 👤 „Lies FAHRPLAN Schritt 12n und Issue #52. Beginne mit der Formex-Datei der KI-Verordnung“ → Plan → Go
- [x] **Bauen** 🤖 _Opus_ (gleiche Session) · Adapter, Verdrahtung, `--only-missing` für `select` und `rules` mit Test, ADR 0025
- [x] **Wissensbasis** 🤖 `select` und `rules --audit-type spec --only-missing` (Groq), Spec-Prompt um Beispiele für KI-Systeme ergänzt (ADR 0025)
- [x] **Zwischenstand** 👤 committet und pusht den Stand von #52; #52 bleibt offen

**Teil 2 – Zerlegen (#53)**

- [x] **Plan** 🆕 _Opus_ · 👤 „Lies FAHRPLAN Schritt 12n Teil 2 und Issue #53“ → Plan → Go
- [x] **Bauen** 🤖 _Opus_ (gleiche Session) · Stufe „Zerlegen“ mit Prüfsteinen als Test, Anker und Gate für Absatz-Anker, ADR 0026. Hält an bei Prompt-Design.
- [x] **Zerlegen** 👤 `uv run python -m kb_build extract`, dann `uv run python -m kb_build decompose` (Groq) → 👤 prüft: Zerlegungsprotokoll `decompositions_spec.json` von DSGVO Art. 5, 9, 32 und KI-VO Art. 6 lesen, `pytest tests/test_decomposition_touchstones.py` grün
- [x] **Soll neu** 🤖 _Opus_ (vor `select`, sonst bricht das Gate der Pflichtanker ab) · legt die Soll-Anker aller drei Spec-Presets auf die neuen Absatz-Anker fest, auch „DSGVO Art. 46“ von `spec-govguard`, Begründung in #53
- [x] **Wissensbasis** 👤 `uv run python -m kb_build select --audit-type spec --only-missing`, dann `uv run python -m kb_build rules --audit-type spec --only-missing` (Groq; nach einem Abbruch denselben Befehl wiederholen, der Checkpoint behält die fertigen Regeln) → 👤 prüft: Architektur-Katalog unverändert, `pytest` und ruff grün bis auf die Galerie-Tests
- [x] **Spec-Galerie neu** 👤 `/audit-messen spec-meldeportal-gesundheit mit Groq`, dann `/audit-messen spec-wohngeld-openapi mit Groq` → 🤖 notiert die Soll-Abweichungen in #53 und zieht die Regelzahlen in `tests/test_review.py` nach, bis `pytest` grün ist
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #53`
- [x] **Abschließen** 👤 committet und pusht, schließt #53

**Teil 3 – SPEC und Soll von `spec-govguard` (#52)**

- [x] **SPEC und Soll** 🆕 _Opus_ · 👤 „Lies FAHRPLAN Schritt 12n Teil 3 und Issue #52 und #53. Ziehe SPEC und Soll nach“ · `docs/SPEC.md` nachziehen laut #52 (Einstufung, Kapitel 3, Kapitel 1, F1, F6, neue Grenze), Kopie ins Preset, Soll von `spec-govguard` um KI-VO-Anker der Zerlegung ergänzen, Begründung in #36
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #52`
- [x] **Abschließen** 👤 Akzeptanzkriterien in #52 anpassen (die Kriterien „151 Regeln unverändert“ und „Spec-Prompts unverändert“ sind durch ADR 0025 und #53 ersetzt), committet und pusht, schließt #52

**Fertig, wenn:** Jede DSGVO- und KI-VO-Regel einen Absatz-Anker hat, die Prüfsteine grün sind, Spec-Galerie, `SPEC.md` und das Soll von `spec-govguard` zum neuen Katalog passen und `pytest` und ruff grün sind.
**Fürs Fachgespräch:** GovGuard ist selbst ein KI-System und muss seine eigene Einstufung belegen. Erst die neue Quelle zeigte, dass eine Regel je Artikel nur einen Aspekt prüft. Format ist nicht Semantik: Ob eine Aufzählung „alle gelten“ oder „eine genügt“ bedeutet, sagt kein Parser. Das LLM urteilt über die Gruppen, der Code prüft Anker und Zitat.

---

### Schritt 12b – #36 GovGuard prüft sich selbst: Spezifikation und Galerie

**Ziel:** `docs/SPEC.md` beschreibt GovGuard im Demo-Stand (Streamlit Community Cloud und Groq, beide in den USA) und ist zugleich die Systembeschreibung für Recruiter: ein gekürztes Fachkonzept, wie es eine Behörden-IT verlangen würde (Länge nach Bedarf, gegliedert mit Unterüberschriften, mit Prüfgrundlagen und Geschäftsregeln zu PASS, WARN und FAIL), verständlich ohne Fachwissen, jedes Fachwort in einem eigenen Satz erklärt, vom README verlinkt. Als Preset `spec-govguard` steht ihr Audit mit Soll-Ergebnis in der Galerie.
**Voraussetzung:** Schritt 12n abgeschlossen (#52 geschlossen). Kein AWS nötig.

- [x] **Schreiben** 🆕 _Opus_ · 👤 „Lies FAHRPLAN Schritt 12b und Issue #36. Schreibe `docs/SPEC.md` neu und lege das Preset `spec-govguard` an“ → Plan → Go
      Gliederung laut #36. Der Abschnitt „Aufnahme in den Bounded Catalog“ wandert nach `ARCHITECTURE.md`. Ein Test stellt sicher, dass das Preset genau `docs/SPEC.md` prüft.
- [x] **Soll festlegen** 🤖 _Opus_ (gleiche Session, vor dem ersten Audit-Lauf) · legt `expected` in `preset.json` fest: `overall_status` und `required_findings` mit Anker und Status. Nur Anker, die schon in `rules_spec.json` stehen; nach #53 neu festgelegt (12n Teil 3). Begründung je Anker (DSGVO-Artikel, Textstelle in SPEC.md) als Kommentar in #36.
- [x] **Lesen** 👤 SPEC.md als Recruiter lesen: in 10 Minuten verstanden, nichts Unklares? Dann die Soll-Begründung im Issue querlesen. Seit 12n sind Kapitel 3, 7 und 8 neu.
- [x] **Erzeugen** 👤 `/audit-messen spec-govguard mit Groq` → Report kommt in die Galerie, Soll-Abweichungen sichtbar (ADR 0023) → 🤖 notiert die Abweichungen in #36, bis `pytest` grün ist
- [x] **Ausprobieren** 👤 `/run` → nur die Galerie-Seite `spec-govguard` öffnen
- [x] ~~**Prüfen** `/code-review gegen Issue #36`~~ entfällt: SPEC und Soll sind mit `/code-review gegen Issue #52` geprüft, „Erzeugen“ schreibt nur Daten
- [x] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** `pytest` und ruff grün sind, die Galerie `spec-govguard` mit Report und Dokument zeigt und die Abweichungen vom Soll in #36 stehen.
**Fürs Fachgespräch:** Dogfooding: Ein Prüfwerkzeug muss seine eigenen Befunde aushalten, auch die Drittlandübermittlung der eigenen Demo. Das Soll steht vor dem ersten Lauf fest, sonst wäre es kein Testorakel, sondern eine Kopie des Ergebnisses.

---

### Schritt 12p – #55 Ordner für govguard und UI, Report-Ansicht als ein Modul

**Ziel:** `govguard/` bekommt `calls/`, `checks/` und `adapters/`, `govguard_ui/` bekommt `screens/` und `report/` (ADR 0027). Kein neues Verhalten, die Befehle bleiben gleich.
**Voraussetzung:** ADR 0027 committet. Kein AWS, kein LLM-Aufruf.

- [x] **Starten** 🆕 _Sonnet_ · 👤 „Lies FAHRPLAN Schritt 12p, Issue #55 und ADR 0027“ → Plan → Go
- [x ] **Bauen** 🤖 _Sonnet_ (gleiche Session) · Dateien verschieben, `finding_list` in `findings_view`, Richtungsregeln in `tests/test_architecture.py`, Pfade in CLAUDE.md, ARCHITECTURE, DESIGN und Skill `audit-messen` nachziehen
- [x ] **Ausprobieren** 👤 `uv run pytest -m visual` und `/run` → Galerie und „Audit erstellen“ öffnen
- [x ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #55`
- [x ] **Verstehen** 👤 `/verstehen 55 Kohäsion und Import-Richtung`
- [x ] **Abschließen** 👤 committet und pusht, schließt #55

**Fertig, wenn:** Im Root liegen nur Einstiege und Verträge, der Architekturtest prüft die Richtung, und `pytest`, `pytest -m visual` und ruff sind grün.
**Fürs Fachgespräch:** Ein Ordner ist eine Aufgabe, im Root steht die Schnittstelle. Die Laufzeit gliedert nach „spricht mit dem Modell“ oder „prüft rein“, weil die Prüfung in jedem Modellaufruf läuft, nicht danach.

---

### Schritt 12q – #57 kb_build: LLM-Schritt, Gates beim Schritt, geteilte Eingaben

**Ziel:** `llm_step.py` bündelt Cache, Zählung und „aus dem Cache oder fragen“, die Gates ziehen zu ihrem Schritt, `build_inputs.py` bündelt geteilte Eingaben (ADR 0027).
**Voraussetzung:** Keine, unabhängig von #55. Läuft nach 12p, damit zwei Umbauten nicht gleichzeitig offen sind. Kein LLM-Aufruf.

- [x ] **Starten** 🆕 _Sonnet_ · 👤 „Lies FAHRPLAN Schritt 12q, Issue #57 und ADR 0027“ → Plan → Go
- [x ] **Bauen** 🤖 _Sonnet_ (gleiche Session) · generischer Cache, `gates.py` aufteilen, `classify` mit CFN-Typen per Deps, `select/prompts.py`, `build_inputs.py`, Test „kein `run.py` importiert ein anderes“. Prompts und Cache-Keys nicht anfassen.
- [x ] **Gegenprobe** 👤 `git status data/` → keine Änderung an Katalog, Caches oder Protokollen
- [x ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #57`
- [x ] **Abschließen** 👤 committet und pusht, schließt #57

**Fertig, wenn:** `decompose/cache.py` und `kb_build/gates.py` entfallen sind, `data/` unverändert ist und `pytest` und ruff grün sind.
**Fürs Fachgespräch:** Jeder Schritt liest und schreibt nur selbst, geteilte Eingaben liegen an einer Stelle. Ein Refactoring beweist sich über unveränderte Tests und unveränderte Daten, nicht über einen neuen Lauf.

---

### Schritt 12r – #56 Ein Modul für Modellaufrufe zur Laufzeit

**Ziel:** Paket, Inventar und Verstoß-Prüfer teilen `calls/model_call.py`: Agents je Provider (ADR 0005, 0016) und Retry-Buchung an einer Stelle.
**Voraussetzung:** Schritt 12p (#55 geschlossen). Kein LLM-Aufruf.

- [x ] **Starten** 🆕 _Sonnet_ · 👤 „Lies FAHRPLAN Schritt 12r, Issue #56 und ADR 0027“ → Plan → Go
- [x ] **Bauen** 🤖 _Sonnet_ (gleiche Session) · `model_call` per TDD, dann die drei Aufrufer umstellen; das Inventar behält `ToolOutput` per Parameter (Verweis auf #58)
- [x ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #56`
- [x ] **Abschließen** 👤 committet und pusht, schließt #56

**Fertig, wenn:** `ToolOutput`/`NativeOutput` und die Retry-Buchung nur noch in `model_call` stehen, alle `test_run_audit_*` ohne geänderte Erwartung grün sind und ruff grün ist.
**Fürs Fachgespräch:** Eine Regel, die an drei Stellen steht, driftet: Das Inventar nutzte auf Groq noch `ToolOutput`. Ein deep module hält die Provider-Regel an einer Stelle, die Aufrufer behalten nur Prompt und Prüfung.

---

### Schritt 12s – #58 Inventar auf Groq mit NativeOutput (ADR 0016)

**Ziel:** Das Inventar folgt ADR 0016. Eine Messung vorher und nachher entscheidet, ob die Umstellung bleibt.
**Voraussetzung:** Schritt 12r (#56 geschlossen). Groq, 6 Architektur-Audits, wenige Cent.

- [x ] **Messen vorher** 👤 `/audit-messen arch-protokollarchiv 3× mit Groq` → 🤖 notiert erkannte Typen, N/A „Dienst nicht erkannt“ und Retries in #58
- [x ] **Bauen** 🆕 _Sonnet_ · 👤 „Lies FAHRPLAN Schritt 12s und Issue #58“ → Plan → Go · Inventar auf `NativeOutput`, Parameter aus #56 entfernen
- [x ] **Messen nachher** 👤 `/audit-messen arch-protokollarchiv 3× mit Groq` → 🤖 vergleicht in #58; schlechter → zurück auf `ToolOutput`, Nachtrag in ADR 0016
- [x ] **Abschließen** 👤 committet und pusht, schließt #58

**Fertig, wenn:** Der Vergleich in #58 steht, das Inventar der Entscheidung folgt und `pytest` und ruff grün sind.
**Fürs Fachgespräch:** Eine Änderung am Modellaufruf ist eine Verhaltensänderung, auch wenn der Code kleiner wird. Deshalb trennt das Ticket sie vom Refactoring und misst sie.

---

### Schritt 12t–12v – Bedingungen im Spec-Audit (#59, #60, #61) am Stück

**Ziel:** Eine Session arbeitet #59, #60 und #61 nacheinander ab. Du greifst nur an drei Halten ein: Messung, Referenzbilder mit Galerie, Push.
**Voraussetzung:** Schritte 12p–12s abgeschlossen. Kein AWS. Groq für 3 Mess- und 3 Galerie-Läufe, zusammen unter 1 $.

**Freigaben für diese Session** (gelten nur für 12t–12v, CLAUDE.md „sage es explizit“):

- Claude setzt den Tag `vor-bedingungen` und committet nach jedem Ticket auf `main`, **ohne Push**. Gepusht wird erst nach Halt 3, weil Streamlit Community Cloud bei jedem Push neu ausrollt.
- Claude entwirft den Prompt-Text des Bedingungs-Vorlaufs (#60) und lässt ihn von einem frischen Opus-Agenten abnehmen. Die Weiche Prompt-Design braucht dafür kein Go.
- Claude wählt den Schnitt der Agenten und spart Budget und Kontext nach den Regeln unten.

**Halt nur bei:** einem der drei Halte unten, einem Test, der nach zwei Anläufen rot bleibt, einem Akzeptanzkriterium, das nicht erreichbar ist, oder Kosten über 1 $. Ein verfehltes Soll wird gezeigt, nicht nachgewürfelt (ADR 0023).

**Budget und Kontext:**

- Die Hauptsession (_Opus_) plant, entwirft den Prompt und schreibt Commits. Bauen lässt sie je Ticket einen _Sonnet_-Agenten, prüfen je Ticket einen frischen _Opus_-Agenten (Vier-Augen-Prinzip).
- Jeder Agent bekommt nur „Lies FAHRPLAN Schritt 12t–12v und Issue #N“ und seinen Teilauftrag. Er antwortet mit höchstens 15 Zeilen: geänderte Dateien, pytest, ruff, offene Punkte. Die Hauptsession liest keine ganzen Diffs, nur Berichte und Reviews.
- Ein Commit je Ticket und die Häkchen hier sind der Wiederaufsetzpunkt. Bricht die Session ab, startet eine neue mit derselben ersten Nachricht und macht beim ersten offenen Häkchen weiter (`git log`, Häkchen).

**Ablauf:**

- [x] **Starten** 🆕 _Opus_ · 👤 „Lies docs/FAHRPLAN.md Schritt 12t–12v und arbeite ihn ab.“
- [x] **Vorbereiten** 🤖 · Arbeitsbaum prüfen, FAHRPLAN committen, `git tag vor-bedingungen`
- [x] **#59 bauen** 🤖 _Sonnet_-Agent · Vorfilter in `kb_build/extract/dsgvo.py` per TDD, Spec-Katalog neu bauen (ohne neue LLM-Aufrufe, sonst Halt), ADR 0028 (Teil Vorfilter), Tabelle Prüfgrundlagen in SPEC.md. Gegenprobe: `git diff --stat data/knowledge_base/` zeigt nur die Regeln der vier Artikel.
- [x] **#59 prüfen** 🤖 _Opus_-Agent · `/code-review gegen Issue #59` → Befunde beheben → Commit „#59 …“
- [x] **#60 Prompt** 🤖 Hauptsession entwirft den Prompt-Text. Ein frischer _Opus_-Agent nimmt ihn gegen ADR 0020 und #60 ab: Nur eine ausdrückliche Verneinung für das ganze Vorhaben ist `no` (Meldeportal Zeile 47 verneint die Einwilligung nur für die Auswertung), Schweigen ist `unstated`, Belegzeilen für Verneinen und Belegen getrennt. Ergebnis als Kommentar in #60.
- [x] **#60 bauen** 🤖 _Sonnet_-Agent · `conditions.json`, Vorlauf in `calls/`, Gates in `checks/`, N/A vor den Paketen, `AuditReport.conditions`, Soll je Bedingung in `preset.json`, ADR 0028, CONTEXT.md, SPEC B6
- [x] **#60 messen** 🤖 `/audit-messen spec-govguard, spec-meldeportal-gesundheit und spec-wohngeld-openapi je 1× mit Groq` → Tabelle in #60: Bedingungen gegen Soll, Lücken vorher und nachher, Pflichtbefunde
- [x] **Halt 1: Messung** 👤 Tabelle in #60 lesen → „weiter“ oder Korrektur
- [x] **#60 prüfen** 🤖 _Opus_-Agent · `/code-review gegen Issue #60` → Befunde beheben → Commit „#60 …“
- [x] **#61 bauen** 🤖 _Sonnet_-Agent · nach dem Prototyp-Kommentar in #61 neu schreiben, nicht kopieren: Rahmen mit Pills und Popover, Abschnitt „Lücken“, N/A-Detail mit Beleg, Tests mit `AppTest`, Design-Artefakt nachziehen
- [x] **#61 Galerie und Bilder** 🤖 `/audit-messen` der 3 Spec-Musterfälle mit Groq, Reports nach `data/gallery/`; `uv run pytest -m visual` → neue Bilder in einen Ordner zum Ansehen legen, noch nicht übernehmen
- [x] **Halt 2: Referenzbilder und Galerie** 👤 Bilder und Soll-Abweichungen ansehen, `/run` → „übernehmen“ oder Korrektur
- [x] **#61 prüfen** 🤖 _Opus_-Agent · `/code-review gegen Issue #61` → Befunde beheben → Commit „#61 …“
- [x] **Halt 3: Push** 👤 „pushen“ → 🤖 pusht, kommentiert das Ergebnis in #59–#61 und schließt sie, hakt hier ab

**Fertig, wenn:** #59–#61 geschlossen sind, die Galerie neu ist und `pytest`, `pytest -m visual` und ruff grün sind. Zurück zur Demo von vorher: `git checkout vor-bedingungen`.
**Danach:** 👤 `/verstehen 60 offene Welt und Bedingungen`
**Fürs Fachgespräch:** Eine Prüfregel fällt nur mit Beleg weg. Bei einem Widerspruch gilt der strengere Wert, denn ein verborgener Befund ist teurer als eine Lücke zu viel.

---

### Schritt 12o – #54 Messkampagne: Stabilität des Spec-Audits

**Ziel:** Belastbare Zahlen für die Präsentation: Soll-Treffer, stabile Prüfregeln und Wechsel nach Art, je 3 Läufe für die 3 Spec-Presets auf dem Katalog nach #59. Dazu Tokens, Laufzeit und Kosten je Lauf für alle 6 Presets (Grundlage für #64). Reports und Messwerte liegen als Rohdaten im Repo.
**Voraussetzung:** Schritt 12v (#61 geschlossen), damit die Messung den neuen Katalog und den Bedingungs-Vorlauf misst. Kein AWS nötig. Groq, ca. 1,30 $. `src/` bleibt eingefroren, das Auswerteskript liegt beim Skill `audit-messen`.

- [x] **Starten** 🆕 _Sonnet_ · 👤 „Lies FAHRPLAN Schritt 12o und Issue #54“ → Plan → Go
- [x] **Bauen** 🤖 _Sonnet_ (gleiche Session) · `measure.py` schreibt `<preset>-<n>.stats.json` (Tokens, Zeit, Retries, Kosten); Auswerteskript mit Test an kleinen Fixtures (Median, Min, Max), Ablage `data/measurements/`
- [x] **Messen** 👤 `/audit-messen spec-govguard, spec-meldeportal-gesundheit und spec-wohngeld-openapi je 3× mit Groq, dazu die 3 Architektur-Presets je 3×, Reports und Messwerte nach data/measurements/` → 🤖 wertet aus und notiert das Ergebnis in #54
- [x] **Nachziehen** 🤖 _Sonnet_ · SPEC P1 mit den neuen Zahlen, Kopie ins Preset → 👤 `/audit-messen spec-govguard mit Groq`, Report nach `data/gallery/` (G9) → 🤖 notiert Soll-Abweichungen in #36
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #54`
- [x] **Abschließen** 👤 committet und pusht, schließt #54

**Fertig, wenn:** Die 18 Reports mit Messwerten im Repo liegen, das Skript die Kennzahlen je Preset ausgibt, SPEC P1 sie nennt und `pytest` und ruff grün sind.
**Fürs Fachgespräch:** `temperature: 0` macht ein LLM nicht deterministisch. Stabilität programmiert man nicht, man misst sie: Entscheidend ist nicht, wie viele Befunde kippen, sondern welche. Kippen nur Lücken und N/A, während FAIL und Pflichtbefunde stehen, ist das Audit für die Fachleute brauchbar.

---

### Schritt 13 – Doku nach Methodik (#63–#67), unbeaufsichtigt über Nacht

**Ziel:** ARCHITECTURE und DESIGN zeigen das System nach arc42, C4, UML, DFD/STRIDE und Qualitätsszenarien in 15 Diagrammen mit Beschreibung, ARCHITECTURE beginnt mit den Architektur- und Designprinzipien (das _Warum_). METHODIK wird zum Rezept, drei Nachbar-Dokumente entfallen, das README überzeugt Recruiter.
**Voraussetzung:** Ist #54 noch offen, arbeitet die Session zuerst Schritt 12o ab (Freigabe unten), denn Qualität, Kosten und README brauchen die Messwerte. Kein AWS. `.env` mit `GROQ_API_KEY` liegt bereit.

**Freigaben für diese Session** (gelten nur für Schritt 13, CLAUDE.md „sage es explizit“):

- **Unbeaufsichtigt:** Keine Rückfragen. Wo sonst ein Halt oder eine Weiche wäre, entscheidet Claude selbst, schreibt die Begründung als Kommentar ins Issue und macht weiter. Alles bleibt per Commit und Tag umkehrbar.
- Claude committet nach jedem Ticket auf `main`, **ohne Push**. Gepusht wird erst morgens nach Halt 3.
- **Kosten:** nur für Schritt 12o, Groq bis 2 $ ohne Go. Kein Bedrock.
- **Löschen in #66** ist freigegeben. Regel: im Zweifel übernehmen statt verwerfen.
- Schnitt der Agenten wie in 12t–12v: _Sonnet_ baut je Ticket, ein frischer _Opus_-Agent prüft je Ticket.

**Regeln für jeden Agenten:** Lies FAHRPLAN Schritt 13 und das Issue. Code und ADRs sind die Wahrheit, Veraltetes fliegt raus, Entworfenes steht gestrichelt als Zielbild. Jedes Diagramm: Kernaussage → Diagramm → Legende → Beschreibung. **Code-Namen nie allein im Satz:** Alltagswort zuerst, Code-Name in Klammern; Tabellen mit Spalte „im Code“. Antwort höchstens 15 Zeilen.

**Anhalten nur bei:** einem Test, der nach zwei Anläufen rot bleibt, oder einem unerreichbaren Akzeptanzkriterium. Dann: Änderungen des Tickets verwerfen, Stand im Issue kommentieren, Morgenbericht schreiben und enden, denn die Tickets bauen aufeinander auf.

**Ablauf:**

- [x] **Starten** 🆕 _Opus_, Auto-Modus (sonst blockieren Freigabe-Dialoge die Nacht) · 👤 „Lies docs/FAHRPLAN.md Schritt 13 und arbeite ihn ab.“
- [x] **Vorbereiten** 🤖 · Arbeitsbaum prüfen, `git tag vor-doku`; #54 offen → Schritt 12o ohne Halte abarbeiten (👤-Schritte übernimmt Claude, Messung per `/audit-messen`), Commit
- [x] **#63 Konventionen** 🤖 _Sonnet_-Agent · Konventionen, D11 Module und D12 Typen Build in DESIGN.md
- [x] **Konventionen abnehmen** 🤖 frischer _Opus_-Agent · Lesbarkeit für IT-Juniors, Farben, Legende, Code-Namen-Regel → Korrektur, bevor der Rest darauf aufbaut
- [x] **#63 fertig bauen und prüfen** 🤖 _Sonnet_ baut D13–D15, Tabellen, Drift-Test · _Opus_ `/code-review gegen Issue #63` → Commit
- [x] **#64 bauen und prüfen** 🤖 _Sonnet_ · Kapitel 0 Prinzipien, Lesehilfe für Behörden-IT, ARCHITECTURE nach arc42, D1–D10, Build-Kosten aus `git log` der Build-Logs · _Opus_ Review → Commit
- [x] **#65 bauen und prüfen** 🤖 _Sonnet_ · METHODIK als Rezept, CLAUDE.md · _Opus_ Review → Commit
- [x] **#66 ernten und löschen** 🤖 _Sonnet_ · Ernteliste als Kommentar in #66, übernehmen, löschen, Links prüfen · _Opus_ Review → Commit
- [x] **#67 bauen und prüfen** 🤖 _Sonnet_ · README und `docs/ENTWICKLUNG.md` · _Opus_ Review → Commit
- [x] **Prüfer-Lesetest** 🤖 frischer _Opus_-Agent ohne Vorwissen liest nur README, ARCHITECTURE und DESIGN, einmal als IHK-Prüfer und einmal als IT-Sicherheitsbeauftragter einer Behörde, und beantwortet die Fragen aus METHODIK 8.4; Lücken → nachbessern → Commit
- [x] **Morgenbericht** 🤖 letzte Nachricht der Session: je Ticket Commit und offene Punkte, alle Entscheidungen, die sonst ein Halt gewesen wären, Kosten von 12o
- [x] **Halt 3: morgens** 👤 Morgenbericht lesen, Diagramme in der Vorschau ansehen, Ernteliste in #66 prüfen → „pushen“ → 🤖 pusht, schließt #54 und #63–#67, hakt hier ab

**Fertig, wenn:** #63–#67 geschlossen sind, der Lesetest keine Lücke mehr findet und `pytest` und ruff grün sind. Zurück: `git checkout vor-doku`.
**Danach:** 👤 `/verstehen 64 Architektur nach arc42`
**Fürs Fachgespräch:** Für LLM-Systeme gibt es keine eigene Standardmethodik. Ich wende arc42, C4, UML und STRIDE an und modelliere das LLM darin als unvertrauenswürdigen externen Partner.

---

### Schritt 13b – 4+1-Doku und Aufräumen (#70–#72), unbeaufsichtigt

**Ziel:** Ein Concern-Modul macht die LLM-Unsicherheit in jeder Sicht des 4+1-Skills sichtbar (#70). Das Repo zeigt keine Projekttermine und keinen Prüfungsbezug (#71). Eine 4+1-Doku in einem Dokument ersetzt ARCHITECTURE und DESIGN und zeigt nur das Gebaute (#72).
**Voraussetzung:** Schritt 13 (#63–#67 geschlossen). Kein AWS. `.env` mit `GROQ_API_KEY` liegt bereit, nur für den Galerie-Lauf in #71.

**Freigaben für diese Session** (gelten nur für Schritt 13b, CLAUDE.md „sage es explizit“):

- **Unbeaufsichtigt:** Keine Rückfragen und kein Go je Ticket; dieser Schritt ist das Go für #70–#72. Wo sonst ein Halt oder eine Weiche wäre, entscheidet Claude nach den Vorgaben unten, schreibt die Begründung als Kommentar ins Issue und macht weiter.
- Claude committet nach jedem Ticket auf `main`, **ohne Push**.
- **Kosten:** Groq bis 1 $ für den Galerie-Lauf in #71 ohne Go. Kein Bedrock.
- **Löschen** ist freigegeben für `docs/Modul4_Praxisprojekt_Emails.md` (#71, ohne Ernte) und `docs/DESIGN.md` (#72, Inhalt geht in die neue Doku oder nach AUSBAU.md).

**Vorgaben je Ticket:**

| Ticket | Vorgabe                                                                                                                                                                                                                                                                                                |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| #70    | Datei `concerns/llm-uncertainty.md`, englisch wie der übrige Skill. Grundlage BSI AIC4; für Halluzination und Prompt Injection ergänzen das BSI-Papier zu generativen KI-Modellen und OWASP Top 10 for LLM Applications. Jede Quelle am Original prüfen (WebFetch).                                    |
| #71    | FAHRPLAN.md, SCHAETZUNG.md und ADRs bleiben unverändert. Startliste ist der Befehl unter der Tabelle; Treffer einzeln beurteilen (der FAIL-Prüfer ist ein Fachbegriff, kein Prüfungsbezug).                                                                                                            |
| #72    | Ein Dokument unter dem alten Namen `docs/ARCHITECTURE.md`, damit Links gültig bleiben. Skill `architecture-models-4plus1`, Zielgruppe (b) vorab genannt, keine Miro-Prompts, deutsch. Quelle sind die alte ARCHITECTURE.md, DESIGN.md, CONTEXT.md und `docs/adr/`; Code nur lesen, um Namen zu prüfen. |

Startliste für #71:

```bash
P='IHK|Praxisprojekt|Modul ?4|Präsentation|Prüfung|[0-3]?[0-9]\.1[0-2]\.|(Oktober|September) 2026|2026-1[0-2]-'
git grep -nIE "$P" -- . ':!docs/adr' ':!docs/FAHRPLAN.md' ':!docs/SCHAETZUNG.md' ':!docs/ARCHITECTURE.md' \
  ':!docs/DESIGN.md' ':!data' ':!uv.lock' ':!.claude/skills/architecture-models-4plus1'
git grep -nIE "$P" -- data/input/presets/spec-govguard
```

**Regeln für jeden Agenten:** Lies FAHRPLAN Schritt 13b und das Issue. Code und ADRs sind die Wahrheit. CLAUDE.md geht den Vorlagen des Skills vor: jeder Abschnitt in 2 Minuten lesbar, Rule of 3, Code-Namen nie allein im Satz. Antwort höchstens 15 Zeilen.

**Anhalten nur bei:** einem Test, der nach zwei Anläufen rot bleibt, oder einem unerreichbaren Akzeptanzkriterium. Dann: Änderungen des Tickets verwerfen und Stand im Issue kommentieren. Scheitert #70, Bericht schreiben und enden, denn #72 baut darauf auf. Scheitert #71, mit #72 weitermachen.

**Ablauf:**

- [x] **Starten** 🆕 _Opus_, Auto-Modus · 👤 „Lies docs/FAHRPLAN.md Schritt 13b und arbeite ihn ab.“
- [x] **Vorbereiten** 🤖 · Arbeitsbaum prüfen, `git tag vor-4plus1`
- [x] **#70 bauen und prüfen** 🤖 _Sonnet_-Agent · Concern-Modul, Zeile im Katalog `concerns/README.md`, Default-Liste in `SKILL.md` Schritt 4 · frischer _Opus_-Agent `/code-review gegen Issue #70` → Commit
- [x] **#71 bauen und prüfen** 🤖 _Sonnet_ · Startliste abarbeiten, `docs/SPEC.md` korrigieren und ins Preset kopieren, `/audit-messen spec-govguard mit Groq`, Report nach `data/gallery/spec-govguard.json` · _Opus_ `/code-review gegen Issue #71` → Commit
- [x] **#72 bauen und prüfen** 🤖 _Sonnet_ · neue ARCHITECTURE.md, Ausbau nach AUSBAU.md, DESIGN.md löschen, Links und Drift-Tests nachziehen · _Opus_ `/code-review gegen Issue #72` und Skill-Schritt 7 (`validate-views.py` auf die in den Scratchpad geschnittenen Sichten) → Commit
- [x] **Lesetest** 🤖 frischer _Opus_-Agent ohne Vorwissen liest nur README und ARCHITECTURE, einmal als Hiring Manager und einmal als IT-Sicherheitsbeauftragter einer Behörde: Wo antwortet das Modell unsicher, was fängt der Code ab, was ist gemessen? Lücken → nachbessern → Commit
- [x] **Bericht** 🤖 letzte Nachricht der Session: je Ticket Commit und offene Punkte, alle Entscheidungen, die sonst ein Halt gewesen wären, Groq-Kosten
- [x] **Halt: morgens** 👤 Bericht lesen, ARCHITECTURE.md in der Vorschau ansehen → „pushen“ → 🤖 pusht, schließt #70–#72, hakt hier ab

**Fertig, wenn:** #70–#72 geschlossen sind, die Startliste aus #71 außerhalb der Ausnahmen nichts mehr findet, der Lesetest keine Lücke mehr findet und `pytest` und ruff grün sind. Zurück: `git checkout vor-4plus1`.
**Danach:** 👤 `/verstehen 72 4+1-Doku mit LLM-Unsicherheit`
**Fürs Fachgespräch:** Das Modell ist ein probabilistischer Kern. Die Architektur legt eine deterministische Schale darum, und die Szenarien messen, wie viel Unsicherheit trotzdem durchkommt.

---

### Schritt 13c – ARCHITECTURE.md als 4+1 nach Kruchten (#73)

**Ziel:** Eine technische Referenz-Doku nach Kruchten ersetzt die dünne Fassung aus #72: Klassendiagramme je Pipeline, Nebenläufigkeit in der Prozess-Sicht, Sequenzdiagramme in den Szenarien, Anwendungsfälle (1) mit eigenem Dokument FUNKTIONSWEISE für die fachlichen Konzepte zum Nachbauen, Kapitel 7 mit rotem Faden für Leser aus der deterministischen Programmierung, Sicherheit (8), Standards (9) und Referenzen (10) als eigene Kapitel; unter jedem Diagramm Elemente und Verbindungen.
**Voraussetzung:** Schritt 13b (#70–#72 geschlossen), CLAUDE.md mit Ausnahme für ARCHITECTURE.md (fea6e33). Kein AWS, kein Groq.

**Vorgaben:** Entscheidungen, Kruchten-Checkliste und roter Faden für Kapitel 6 stehen im ersten Kommentar von #73, die Gliederung 0–10 in den Akzeptanzkriterien. Opus schreibt selbst, ohne Unteragenten für den Text.

**Ablauf:**

- [x] **Starten** 🆕 _Opus_ · 👤 „Lies docs/FAHRPLAN.md Schritt 13c und Issue #73 mit Kommentaren“ → Plan → Go
- [x] **Gerüst** 🤖 _Opus_ · alle Überschriften mit Leitfrage und ≤ 3 Zeilen Zusammenfassung, alle Diagramme (Mermaid), Typdiagramme aus `git show d3ff19d:docs/DESIGN.md` am Code geprüft
- [x] **Halt: Gerüst** 👤 in der Vorschau ansehen → Korrekturen oder Go
- [x] **Fließtext** 🤖 _Opus_ · Sichten, Szenarien, Kapitel 6–8, Links aus README, ENTWICKLUNG, METHODIK und Lehrbuch nachziehen; `validate-views.py` auf die in den Scratchpad geschnittenen Sichten, Drift-Tests nachziehen, pytest und ruff
- [x] **Prüfen** 🤖 frischer _Opus_-Agent `/code-review gegen Issue #73` mit Kruchten-Checkliste · zwei frische Leser: Senior Engineer (nur deterministische Programmierung) für Kapitel 6, IT-Sicherheitsbeauftragter für Kapitel 7 und 8 → nachbessern → Commit
- [x] **Review** 👤 liest die erste Fassung (a45f977) → Funktionsweise fehlt, Diagramme ohne Beschreibung, Sequenzpfeile, Datenflussdiagramm nicht geschichtet, Referenzen fehlen
- [x] **Nachbessern** 🤖 _Opus_ · neues Kapitel 1 Funktionsweise, Kapitel umnummeriert (1–8 → 2–9), Kapitel 10 Referenzen, Elemente und Verbindungen bzw. Abfolge unter jedem Diagramm, 🤖-Felder in ⚙️-Klassen, Sequenzdiagramme mit Antwort an den Aufrufer, Datenflussdiagramm geschichtet; METHODIK nach `docs/research/`; Links, Drift-Test, `validate-views.py`, pytest und ruff
- [x] **Prüfen 2** 🤖 frischer _Opus_-Agent als Nachbauer: Kann er aus Kapitel 1 bis 3 beschreiben, wie er GovGuard neu baut? Faktenprüfung gegen den Code
- [x] **Halt: Zuschnitt** 👤 Kapitel 1 ist Fachkonzept, nicht Architektur → eigenes Dokument, Ausnahme in CLAUDE.md
- [x] **Aufteilen** 🤖 _Opus_ · `docs/FUNKTIONSWEISE.md` aus Kapitel 1.2–1.7, ARCHITECTURE Kapitel 1 nur Anwendungsfälle, Wiederholungen in den Sichten durch Verweise ersetzt, Befunde des Nachbauers eingearbeitet, Drift-Test über beide Dokumente
- [ ] **Abschließen** 👤 committet und pusht, schließt #73

**Fertig, wenn:** #73 geschlossen ist, jede Sicht die Checkliste erfüllt, beide Leser keine Lücke finden und `pytest` und ruff grün sind.
**Danach:** 👤 `/verstehen 73 4+1 nach Kruchten`
**Fürs Fachgespräch:** Kruchten trennt, was ein System *ist* (logisch), wie es *läuft* (Prozess), wie es *gebaut* ist (Entwicklung) und wo es *steht* (physisch); die Szenarien beweisen, dass die vier Sichten zusammenpassen.

---

## AWS-Nachholblock (entfällt)

Kein AWS-Deploy und kein CDK (19.10., Budget). #9, #34 und die Pipeline #37 sind Ausbau.

### Schritt 10h – #33 Messung: Gegenprobe FAIL-Prüfer (mit Groq erledigt, ADR 0023)

**Ziel:** Der FAIL-Prüfer aus #31 stuft kein echtes FAIL herab und ändert nichts an den Ergebnissen aus #29.
**Voraussetzung:** Schritt 10f (#31).

- [x] ~~☁ **Messen** mit Bedrock~~ entfällt (ADR 0023); erfüllt durch die Groq-Messungen aus #31
- [x] **Abschließen** 👤 schließt #33 (bei Herabstufung von Art. 9: neues Ticket statt Abschluss)

**Fertig, wenn:** Art. 9 FAIL bleibt und vom Prüfer bestätigt ist, Wohngeld WARN zeigt.
**Fürs Fachgespräch:** Ein Prüfer darf echte Verstöße nicht wegdiskutieren.

---

### Schritt 13 – #22 Doku zu kb_build nachziehen

**Ziel:** `ARCHITECTURE.md`, `METHODIK.md` und die Lernkarten (`SPEC.md` schreibt #36 neu) stimmen mit dem Code nach #19, #20 und #21 überein (Relevanzregel nach ADR 0013, Korrekturrunden, kein Ranking mehr, Pfade nach #20). Ergänzt #16, das README und die drei Erklär-Dokumente übernimmt.
**Voraussetzung:** Schritt 9e. Kein Code, nur Doku. Läuft nach dem Deploy (Zeitplan: Di 20.10.).

- [ ] **Starten** 🆕 _Sonnet_ · 👤 „Lies `gh issue view 22` und zieh die Dokumente und Lernkarten auf den Code-Stand nach“ → Plan → Go
- [ ] **Prüfen** 👤 `grep` aus dem Issue, jeden Markdown-Link in `learning/lessons/` anklicken (oder per Skript prüfen lassen), ARCHITECTURE 5.1 und DESIGN 1.1–1.2 querlesen
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

## Ausbau – Recruiter-Stand (#38)

Am 19.10. aus dem Umfang genommen (Budget): Der Recruiter-Stand braucht Audit-Jobs (#34) und dauerhaften Betrieb. #38 ist mit Label `ausbau` geschlossen.
**Fürs Fachgespräch:** Asynchroner Ablauf mit Job-ID statt Timeout, Fortschritt über S3, Live-Audits nur mit Passwort.

---

## Abschluss

### Schritt 19 – #23 Lehrbuch fertigstellen und korrigieren

**Ziel:** Das Lehrbuch aus `learning/lehrbuch/` (Faktenbasis, Stand 13.10.2026) beschreibt den gebauten Stand, ist in Claude Web ausformuliert, von dir korrigiert und in NotebookLM geladen.
**Voraussetzung:** Schritt 13 (#22); #8 steht als Ausbau im Lehrbuch. Läuft vom 22. bis 25.10. als Vorbereitung auf das Fachgespräch (siehe Zeitplan).

- [ ] **Faktenbasis aktualisieren** 🆕 _Sonnet_ · 👤 „Lies `gh issue view 23` und `learning/lehrbuch/README.md` und zieh die Kapitel auf den Code-Stand nach“ → Plan → Go (Kapitel 00, 08, 10, 99; #7, #8 und #10 nur als Ausbau)
- [ ] **Ausformulieren** 👤 Claude Web, ein Chat je Kapitel: Faktenbasis, `CONTEXT.md` und `docs/adr/` in ein Project laden, mit Kapitel 05 beginnen und den Stil-Prompt für alle Kapitel wiederverwenden. Zum Schluss fragen: „Welche Aussagen stehen nicht in den Dateien?“
- [ ] **Korrigieren** 👤 Zahlen, ADR-Nummern und `Datei:Funktion`-Belege gegen das Repo prüfen; alle [OFFEN] klären
- [ ] **NotebookLM** 👤 Kapitel hochladen, drei Stichprobenfragen stellen (z. B. zu Gates, Cache, Provider)
- [ ] **Abschließen** 👤 committet und pusht (Faktenbasis; ob auch die Lesetexte, entscheidet die offene Frage im Issue)

**Fertig, wenn:** Alle Kapitel ausformuliert und korrigiert sind und NotebookLM die Stichprobenfragen richtig beantwortet.
**Fürs Fachgespräch:** Du erklärst die kb-build-Pipeline ohne Notizen: LLM urteilt, Code wählt aus, Gates fangen Erfundenes ab.
