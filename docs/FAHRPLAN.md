# GovGuard – Fahrplan

Ein Eintrag je Ticket, in Bearbeitungsreihenfolge. Jeder Eintrag steht für sich: Du brauchst kein anderes Dokument, um ihn abzuarbeiten. Hake die Kästchen im Editor ab.

**Legende:** 👤 du · 🤖 Claude · 🛠 Junie (PyCharm) · `/…` Befehl zum Eintippen. `/verstehen N <Schwerpunkt>` erklärt das Ticket als Lernkarte und fragt sie ab. Claude zeigt pro Ticket einen Plan und arbeitet nach deinem **Go** am Stück (CLAUDE.md). Junie baut nur die UI und gibt bei #12 und #9 eine zweite Meinung. Alles läuft direkt auf `main`, ohne Branches.

**Rhythmus jedes Eintrags:** _Starten → Bauen → Prüfen → Verstehen → Abschließen._

**Tagesabschluss:** 👤 `/devlog`

**Modell und Session:**

- **Sonnet baut, Opus urteilt.** Sonnet 5.5 für TDD-Zyklen mit klaren Kriterien; Opus 5.5 für Grilling, Review, Security-Review, Diagnose und IHK-Check. Opus baut auch die heiklen Tickets #1 (Fundament), #7 (Freigabe-Schleife) und #9 (IAM, KMS). Wechsel mit `/model sonnet` bzw. `/model opus`.
- **🆕 = neue Session** (`/clear`). Erste Nachricht: „Lies docs/FAHRPLAN.md Schritt N und Issue #X.“ Jeder Schritt startet frisch. Das Review läuft in einer zweiten frischen Session, damit keine Sitzung ihren eigenen Code prüft (Vier-Augen-Prinzip).
- Zusätzlich neu starten, wenn eine Session lang wird und Claude Absprachen vergisst oder sich wiederholt. Vorher den Stand committen.
- **Junie ist zweite Meinung, nicht Bauer.** Bei #4 und #5 lieferte Junie (GPT-5.2) grüne Tests mit falschen Daten; der Neubau kostete mehr Claude-Budget, als er sparte. Junie baut deshalb nur noch die Streamlit-UI (Fehler sieht man sofort) und prüft bei #12 und #9 den Diff als zweite Modellfamilie (Vier-Augen-Prinzip). Junie liest `AGENTS.md` und committet nicht. Wird das Claude-Budget knapp, bekommt Junie ein Ticket nur mit vorab geschriebenen roten Tests.

**Priorität:** Erst die Audits, dann die Architektur-Generierung.

- **A – Audits (Pflicht):** Spec-Audit und Architektur-Audit laufen Ende-zu-Ende, mit vollständigem Katalog (ADR 0011), Deploy, Selbst-Audit und Demo-UI; dazu passt die Doku. Schritte 6–14.
- **B – Golden Archetypes (nur wenn Zeit bleibt):** Archetypen bauen und freigeben (#7), Archetyp-Auswahl (#10). Schritte 15–16.
- **Stichtag:** B beginnt nur, wenn A fertig ist und bis zur Abgabe am 21.10. noch mindestens 3 Arbeitstage bleiben, also spätestens am Freitag, 16.10. Sonst gehen die Resttage in Stabilisierung und Präsentation. Im Fachgespräch ist B dann Ausbau: Steckbriefe, ADR 0003 und 0009 liegen vor.

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
| 10      | A    | #14 Ressourceninventar + Pakete | 🤖 Opus                                          | 🤖 Opus                    |
| 11      | A    | #8 Preset-Gate + Workflow       | 🤖 Sonnet                                        | 🤖 Opus                    |
| 12      | A    | #9 Stack + Endpunkte            | 🤖 Opus                                          | 🤖 Opus · 🛠 Junie         |
| 13      | A    | #11 Deploy + UI                 | 🛠 Junie (UI) · 🤖 Sonnet (`deploy.yml`, Wizard) | 🤖 Opus                    |
| 14      | A    | #16 Doku nachziehen             | 👤 + 🤖 Sonnet                                   | 👤                         |
| 15      | B    | #7 Golden Archetypes            | 🤖 Opus                                          | 🤖 Opus                    |
| 16      | B    | #10 Archetyp-Auswahl            | 🤖 Sonnet                                        | 🤖 Opus                    |

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
**Voraussetzung:** Schritt 6. Der erste Lauf vom 09.10. (mit Ranking und Obergrenze) ist durch ADR 0011 überholt.

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

- [ ] **Starten** 🆕 _Opus_ · 👤 `/grilling Preset für #15: Step Functions + SNS ohne KMS, Soll-Gesamtstatus, Pflichtanker`
- [ ] **Bauen** 👤 „Lege das Preset nach unseren Antworten an“ → Go → 🤖 schreibt das CloudFormation-Template unter `data/presets/<id>/`
- [ ] **Blind prüfen** 👤 Gemini wie in Schritt 2
- [ ] **Soll festlegen** 👤 nennt Gesamtstatus und bestätigte Anker → 🤖 schreibt `preset.json`, Tests grün
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Das Preset liegt vor, und sein Pflichtanker steht im Bounded Catalog.

---

### Schritt 9 – #12 Prüfregeln formulieren und Gate

**Ziel:** `rules_spec.json` und `rules_arch.json` liegen vor; jede Prüfregel hat das Gate bestanden.
**Voraussetzung:** Schritt 7 inklusive Kontrollpunkt.

- [ ] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #12 umsetzen` → Plan → Go (Prompt-Design ist eine Weichenstellung)
      Reihenfolge: `gates.py` (Schema, Anker, Zitat, Querverweise) → `formulate_rule` mit `FunctionModel`
- [ ] **Echter Lauf** 🤖 👤 „Formuliere die Prüfregeln“
- [ ] **Stichprobe** 👤 Lies 5 Prüfregeln, davon mindestens eine aus FSBP und eine aus C5: Sind `compliant_if` und `violation_if` prüfbar? Passt `source_quote` zur Norm?
- [ ] **Zweite Meinung** 🛠 _Junie_ · 👤 „Lies AGENTS.md → Review und `gh issue view 12`. Prüfe `git diff`.“ Befunde nimmst du ins Opus-Review mit.
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #12`
- [ ] **Verstehen** 👤 `/verstehen 12` (Kernfrage: warum der Code den Primäranker setzt und nicht das LLM)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Beide Kataloge eingecheckt sind, das Gate grün ist und die Stichprobe gepasst hat.
**Fürs Fachgespräch:** Zitat statt Behauptung, erfundene Fundstellen, Draft-Pattern im Build.

---

### Schritt 10 – #14 Audit-Engine: Ressourceninventar und parallele Pakete

**Ziel:** Die Audit-Engine bewertet den vollständigen Katalog: N/A über das Ressourceninventar, die anwendbaren Prüfregeln in parallelen Paketen.
**Voraussetzung:** Schritt 9.

- [ ] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #14 umsetzen` → Plan → Go (der Freitext-Vorlauf ist eine Prompt-Weiche)
      Reihenfolge: Terraform-Zuordnungstabelle → Freitext-Vorlauf mit Beleg → Pakete parallel → Zusammenführen (ein Befund je Prüfregel) → Sortierung nach Ressourcentyp
- [ ] **Messen** 👤 `/run CLI-Audit des größten Presets mit vollem Katalog, Laufzeit und Kosten messen` → 🤖 notiert das Ergebnis im Issue und setzt das Kostenziel in SPEC
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #14`
- [ ] **Verstehen** 👤 `/verstehen 14` (Kernfrage: warum ein übersehener Dienst sichtbar bleiben muss)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Alle Tests grün sind und Laufzeit und Kosten im Issue stehen.
**Fürs Fachgespräch:** Pruning per Code, Map-Reduce, Vollständigkeit trotz Aufteilung.

---

### Schritt 11 – #8 Preset-Gate und Build-Workflow

**Ziel:** Der Build der Wissensbasis läuft per Knopfdruck in GitHub Actions und öffnet nur bei Grün einen Pull Request.
**Voraussetzung:** Schritte 8 und 10.

- [ ] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #8 umsetzen` → Plan → Go
      Reihenfolge: Preset-Gate (Gesamtstatus, Pflicht-Befunde, Hash-Check; den Soll-Archetyp prüft erst #10) → `python -m kb_build` → `build-kb.yml` ohne Logik
- [ ] **Einrichten** 🆕 _Sonnet_ · 👤 `/wizard OIDC-Provider und Rolle für build-kb.yml, nur Bedrock eu.-Profil` → 👤 Wizard ausführen
- [ ] **Ausprobieren** 👤 Workflow in GitHub Actions starten → PR lesen, Kosten prüfen
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #8`
- [ ] **Verstehen** 👤 `/verstehen 8` (Kernfrage: warum OIDC besser ist als ein Access Key in GitHub)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Ein Workflow-Lauf einen grünen PR mit Kostenangabe geöffnet hat.
**Fürs Fachgespräch:** OIDC statt langlebiger Keys, Gate vor Merge, alte Version bleibt bei Rot aktiv.

---

### Schritt 12 – #9 GovGuard-Stack und Audit-Endpunkte

**Ziel:** Die Audit-API läuft in eu-central-1, protokolliert jeden Aufruf und bleibt unter 29 s.
**Voraussetzung:** Schritt 10.

- [ ] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #9 umsetzen`
      Reihenfolge: `Trace` und `AuditEvent` bauen → `handler.py` → CDK-Stack mit Assertions-Tests (Tests auf das erzeugte Template)
- [ ] **Sicherheit** 👤 `/security-review` vor dem ersten Deploy
- [ ] **Einrichten** falls nötig: 👤 `/wizard cdk bootstrap für eu-central-1` → 👤 Wizard ausführen
- [ ] **Deploy + Test** 👤 „Deploye den Stack und ruf /audit/architecture mit dem größten Preset auf“ → Go → 👤 `/run`. Über 29 s: 👤 `/model opus`, dann `/diagnosing-bugs` und Plan B aus ADR 0011 entscheiden
- [ ] **Zweite Meinung** 🛠 _Junie_ · 👤 „Lies AGENTS.md → Review und `gh issue view 9`. Prüfe `git diff`.“ Befunde nimmst du ins Opus-Review mit.
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #9`
- [ ] **Verstehen** 👤 `/verstehen 9` (Schwerpunkt: IAM, KMS und Audit-Protokoll)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Ein Aufruf einen Audit-Report liefert, das Audit-Ereignis in CloudWatch Logs steht (ohne Eingabetext) und die Laufzeit im Issue steht.
**Fürs Fachgespräch:** Least Privilege, KMS-CMK, Datenminimierung, Rückverfolgung, 0 € Leerlaufkosten.

---

### Schritt 13 – #11 Deploy-Pipeline und Demo-UI

**Ziel:** Jeder Push auf `main` rollt GovGuard nach dem Selbst-Audit aus; die Demo-UI auditiert Spezifikationen und Architekturen öffentlich.
**Voraussetzung:** Schritte 9 und 12.

- [ ] **Einrichten** 🆕 _Sonnet_ · 👤 `/wizard Einmalige AWS-Einrichtung für deploy.yml: OIDC-Deploy-Rolle, IAM-User für Streamlit, Secrets` → 👤 Wizard ausführen. Der Wizard ist zugleich die Anleitung, die das Ticket verlangt.
- [ ] **Bauen Pipeline** 🤖 _Sonnet_ · 👤 „Setze aus Issue #11 die `deploy.yml` um“ → Plan → Go. Die Ausnahmen für Prüfregeln (z. B. FSBP `APIGateway.4`, `Lambda.3`) entstehen hier, mit Begründung (Weichenstellung).
- [ ] **Bauen UI** 🛠 _Junie_ · 👤 „Lies docs/FAHRPLAN.md Schritt 13 und `gh issue view 11`. Baue nur die Streamlit-UI in `ui/`, ohne Archetyp-Abruf.“
- [ ] **Ausprobieren** 👤 `/run Streamlit-UI lokal starten, Preset auditieren, Screenshot`
- [ ] **Sicherheit** 🆕 _Opus_ · 👤 `/security-review`
- [ ] **Live** 👤 Pushen → Pipeline beobachten → UI auf Streamlit Community Cloud öffnen
- [ ] **Prüfen** 👤 `/code-review gegen Issue #11`
- [ ] **Verstehen** 👤 `/verstehen 11`, danach `/verstehen probe` (Generalprobe)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Ein Push den Deploy mit Selbst-Audit auslöst und die öffentliche UI ein Preset auditiert.
**Fürs Fachgespräch:** Dogfooding, begründete Ausnahmen, ein einziger Weg in die Produktion, bewusstes US-Hosting nur mit fiktiven Daten.

---

### Schritt 14 – #16 Doku nachziehen

**Ziel:** README und die drei Erklär-Dokumente beschreiben den gebauten Stand nach ADR 0011.
**Voraussetzung:** Schritte 7, 9 und 10 (#6, #12, #14).

- [ ] **Starten** 🆕 _Sonnet_ · 👤 „Lies `gh issue view 16` und zieh die vier Dokumente auf den Code-Stand nach“ → Plan → Go
- [ ] **Prüfen** 👤 `grep` aus dem Issue, dann jedes Dokument querlesen (je ca. 2 Minuten)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Das `grep` aus #16 nichts Veraltetes mehr findet. Damit ist Priorität A erledigt.

---

## Priorität B – Golden Archetypes (nur wenn Zeit bleibt)

Start nur nach der Regel _Stichtag_ oben.

### Schritt 15 – #7 Golden Archetypes mit Freigabe

**Ziel:** ARCH-01 bis -03 sind als CDK gebaut und freigegeben, mit dokumentierten Ausnahmen.
**Voraussetzung:** Schritt 14. Node.js und CDK CLI lokal installiert.

- [ ] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #7 umsetzen`
      Reihenfolge: Allowlist-Filter (cdk-nag und Prüfregeln, aus Schritt 13) → Struktur-Soll → Compliance-Soll (N/A-Sperre) → Schleife mit höchstens 3 Runden (mit Fakes) → `cdk_runner.py`
- [ ] **Echter Build** 👤 „Baue die 3 Archetypen“ → Go. Bei Fehlern von synth oder cdk-nag: 👤 `/diagnosing-bugs`
- [ ] **Offene Frage** 👤 „Klär, ob Lambda-Logging `log-group:NAME:*` braucht“ → bei Ja: Ausnahme mit Begründung in `data/nag_allowlist.json`
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #7`
- [ ] **Verstehen** 👤 `/verstehen 7` (Schwerpunkt: cdk-nag und Ausnahmen)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** `archetypes.json` 3 freigegebene Archetypen mit `approval` enthält.
**Fürs Fachgespräch:** Vier-Augen-Prinzip, Risikoakzeptanz, Funktionstrennung, Least Privilege.

---

### Schritt 16 – #10 Archetyp-Auswahl

**Ziel:** Bei einer Spezifikation ohne FAIL liefert GovGuard ARCH-01, -02, -03 oder „keiner“; die UI zeigt den Archetyp.
**Voraussetzung:** Schritt 15.

- [ ] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #10 umsetzen` → Plan → Go (Auswahl, Ablehnung bei FAIL, `NONE`, Soll-Archetyp im Preset-Gate)
- [ ] **UI** 🛠 _Junie_ · 👤 „Ergänze in `ui/` den Archetyp-Abruf nach Issue #10.“
- [ ] **Deploy + Test** 🆕 _Sonnet_ · 👤 „Deploye und ruf /archetype/select mit einem Spec-Preset auf“ → Go → 👤 `/run`
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #10`
- [ ] **Verstehen** 👤 `/verstehen 10` (Kernfrage: warum „keiner passt“ eine erlaubte Antwort ist)
- [ ] **Abschließen** 👤 committet und pusht

**Fertig, wenn:** Das Preset liefert den Soll-Archetyp, und ein Report mit FAIL wird mit HTTP 422 abgelehnt.
**Fürs Fachgespräch:** geschlossene Antwortmenge, keine Generierung zur Laufzeit.
