# GovGuard – Fahrplan

Ein Eintrag je Ticket, in Bearbeitungsreihenfolge. Jeder Eintrag steht für sich: Du brauchst kein anderes Dokument, um ihn abzuarbeiten. Hake die Kästchen im Editor ab.

**Legende:** 👤 du · 🤖 Claude · 🛠 Junie (PyCharm) · `/…` Befehl zum Eintippen. Claude skizziert jeden kleinen Schritt und wartet auf dein **Go** (CLAUDE.md). Junie arbeitet ein Ticket am Stück ab; dort ersetzt das Claude-Review das Go.

**Rhythmus jedes Eintrags:** _Starten → Bauen → Prüfen → Verstehen → Abschließen._

**Tagesabschluss:** 👤 `/devlog`

**Modell und Session:**

- **Sonnet baut, Opus urteilt.** Sonnet 5.5 für TDD-Zyklen mit klaren Kriterien; Opus 5.5 für Grilling, Review, Security-Review, Diagnose und IHK-Check. Opus baut auch die heiklen Tickets #1 (Fundament), #7 (Freigabe-Schleife) und #9 (IAM, KMS). Wechsel mit `/model sonnet` bzw. `/model opus`.
- **🆕 = neue Session** (`/clear`). Erste Nachricht: „Lies docs/FAHRPLAN.md Schritt N und Issue #X.“ Jeder Schritt startet frisch. Das Review läuft in einer zweiten frischen Session, damit keine Sitzung ihren eigenen Code prüft (Vier-Augen-Prinzip).
- Zusätzlich neu starten, wenn eine Session lang wird und Claude Absprachen vergisst oder sich wiederholt. Vorher den Stand committen.
- **Junie baut Routine, Claude prüft.** 🛠-Schritte laufen in PyCharm mit Junie, Modell GPT-5.2; das spart Claude-Budget ([SCHAETZUNG.md](SCHAETZUNG.md)). Junie liest `AGENTS.md`, arbeitet nur auf dem Ticket-Branch und committet nicht. Erste Nachricht an Junie: „Lies docs/FAHRPLAN.md Schritt N und `gh issue view X`. Setze es per TDD um.“ Befunde aus dem Claude-Review gibst du an Junie zurück. Zwei Modellfamilien ergeben ein echtes Vier-Augen-Prinzip.

**Wer baut was:**

| Schritt | Ticket                    | Baut                                             | Prüft                      |
| ------- | ------------------------- | ------------------------------------------------ | -------------------------- |
| 1       | #1 Prüfkern               | 🤖 Opus                                          | 🤖 Opus                    |
| 2       | #3 Presets                | 👤 + 🤖 Opus                                     | 👤                         |
| 3       | #2 Bedrock + CLI          | 🤖 Sonnet                                        | 🤖 Opus                    |
| 4       | #4 BSI + CIS              | 🛠 Junie                                         | 🤖 Opus                    |
| 5       | #5 DSGVO + SDM            | 🛠 Junie                                         | 🤖 Opus                    |
| 6       | #6 Auswahlliste           | 🛠 Junie                                         | 👤 Kontrollpunkt + 🤖 Opus |
| 7       | #12 Prüfregeln + Gate     | 🛠 Junie                                         | 🤖 Opus                    |
| 8       | #7 Golden Archetypes      | 🤖 Opus                                          | 🤖 Opus                    |
| 9       | #8 Preset-Gate + Workflow | 🛠 Junie (Wizard: 🤖)                            | 🤖 Opus                    |
| 10      | #9 Stack + Endpunkte      | 🤖 Opus                                          | 🤖 Opus                    |
| 11      | #10 Archetyp-Auswahl      | 🛠 Junie (Deploy-Test: 🤖)                       | 🤖 Opus                    |
| 12      | #11 Deploy + UI           | 🛠 Junie (UI) · 🤖 Sonnet (`deploy.yml`, Wizard) | 🤖 Opus                    |

---

### Schritt 0 – Stand sichern

**Ziel:** Die Tickets verlinken auf ADR 0007 und den Fahrplan; beides muss auf GitHub liegen.

- [ ] 👤 Alle Doku-Änderungen committen und pushen, z. B. `ADR 0007: relevance filter, pinned anchors, cdk-nag exceptions`

**Fertig, wenn:** `git status` sauber ist und ADR 0007 auf GitHub lesbar ist.

---

### Schritt 1 – #1 Prüfkern: Modelle und audit_engine

**Ziel:** Die Prüflogik läuft komplett ohne AWS und ist getestet: Modelle, Validierungskette, Gesamtstatus, N/A durch Code.
**Voraussetzung:** Schritt 0. Schritt 2 kann parallel laufen.

- [x] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #1 umsetzen`. 🤖 legt je Zyklus erst einen roten Test an, dann den Code, bis der Test grün ist. 👤 sagt Go. Wiederholen, bis alle Kriterien grün sind.
      Reihenfolge: `pyproject.toml` + ruff → `text.py` (`normalize`, `contains_quote`, `template_resource_types`) → Gesamtstatus → Validator → `run_audit()` mit `FunctionModel` → boto3-Importtest und Test der Modulgröße
- [x] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #1`
- [x] **Verstehen** 👤 `/ihk-check Halluzinationsschutz`
- [x] **Abschließen** 👤 „Schreib die Fachgespräch-Notiz für #1“ → Go → 🤖 postet ins Issue; 👤 committet und pusht

**Fertig, wenn:** `pytest` und `ruff check` grün sind, die Notiz im Issue steht und der Commit gepusht ist.
**Fürs Fachgespräch:** Draft-Pattern, Fail closed, Beleg-Pflicht, warum der Code N/A setzt.

---

### Schritt 2 – #3 Presets mit Soll-Ergebnis (deine Handarbeit)

**Ziel:** 4 fiktive Presets mit einem Soll, das du festlegst. Das Soll ist der Maßstab für alle späteren Tests.
**Voraussetzung:** keine; parallel zu Schritt 1.

- [ ] **Starten** 🆕 _Opus_ · 👤 `/grilling Presets für #3: 4 fiktive Behördenszenarien, Aufteilung Spec/Architektur, Soll-Gesamtstatus, Pflichtanker (höchstens 4 je Audit-Art)`
- [ ] **Bauen** 👤 „Lege die Presets nach unseren Antworten an“ → Go → 🤖 schreibt `data/presets/<id>/` (Eingabe + `preset.json`). Ein Architektur-Preset ist CloudFormation-JSON, damit „N/A durch Code“ mitgetestet wird.
- [ ] **Prüfen** 👤 Lies jede Eingabe und jedes Soll selbst. Die Eingaben enthalten nur fiktive Daten, die größte höchstens 100.000 Zeichen.
- [ ] **Verstehen** 👤 Erkläre in 2 Sätzen, warum das Soll von dir kommt und nicht aus einem früheren Lauf.
- [ ] **Abschließen** 👤 „Schreib die Fachgespräch-Notiz für #3“ → Go → 🤖 postet; 👤 committet und pusht

**Fertig, wenn:** 4 Ordner unter `data/presets/` liegen, die Pflichtanker auf Normen zeigen und die Notiz im Issue steht.
**Fürs Fachgespräch:** Testorakel, zirkulärer Test, gesetzte Plätze.

---

### Schritt 3 – #2 Bedrock-Anbindung und CLI

**Ziel:** Ein echtes Spec-Audit läuft lokal über Bedrock. Laufzeit und Kosten sind gemessen.
**Voraussetzung:** Schritt 1. AWS-Login aktiv (`aws sso login`), Zugang zu Claude Haiku 4.5 in Bedrock eu-central-1.

- [ ] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #2 umsetzen` (Stubber-Test: Request enthält `toolChoice`; CLI-Ausgabe als JSON)
- [ ] **Bauen** 👤 „Prüfe die Modell-ID mit `aws bedrock list-inference-profiles --region eu-central-1`“ → 🤖 korrigiert die ID, falls nötig, auch in ADR 0001 und ARCHITECTURE 2.1.
- [ ] **Messen** 👤 `/run CLI-Audit mit 100.000 Zeichen und 20 Prüfregeln, Laufzeit und Kosten messen` → Go → 🤖 notiert das Ergebnis im Issue
- [ ] Falls über 29 s: 👤 `/model opus`, dann `/diagnosing-bugs Audit überschreitet 29 s` und den Plan B aus der offenen Frage in #2 entscheiden
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #2`
- [ ] **Verstehen** 👤 `/ihk-check Tool-Choice und EU-Inferenz`
- [ ] **Abschließen** 👤 „Schreib die Fachgespräch-Notiz für #2“ → Go → 🤖 postet; 👤 committet und pusht

**Fertig, wenn:** `python -m govguard.cli spec <datei>` einen gültigen Audit-Report liefert und Messwerte im Issue stehen.
**Fürs Fachgespräch:** Inferenzprofil `eu.`, Art. 44 DSGVO, erzwungene Tool-Nutzung, Dependency Injection.

---

### Schritt 4 – #4 Extraktion BSI und CIS

**Ziel:** BSI Grundschutz++ und CIS AWS v7 sind deterministisch in Anforderungen zerlegt und vorgefiltert.
**Voraussetzung:** Schritt 1 (`normalize()`).

- [ ] **Branch** 👤 `git switch -c ticket-4`
- [ ] **Spike** 🛠 _Junie_ · 👤 „Zeig mir die Struktur von Prowler `cis_7.0_aws.json` und dem BSI-OSCAL: Felder, IDs, Markdown-Zeichen im Text. Nur anschauen, nichts ändern.“
- [ ] **Starten** 🛠 _Junie_ · 👤 „Lies docs/FAHRPLAN.md Schritt 4 und `gh issue view 4`. Setze es per TDD um (ADR 0008).“ Reihenfolge: `data/sources.json` + `source_fetch.py` (Hash-Prüfung, Test mit Fake) → BSI → CIS. Stichproben-Tests: `DET.3.1`, CIS `3.1.4`, jede ID genau einmal, CIS genau 70 Empfehlungen
- [ ] **Bauen** 🛠 erzeugt `data/extracted/bsi.json` und `cis.json` (nur lokal). 👤 Prüfe: Bleiben beim BSI nach dem Vorfilter 380 Anforderungen? Stimmen 3 CIS-Texte mit dem lokalen PDF überein?
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #4`
- [ ] **Verstehen** 👤 Erkläre in 2 Sätzen, warum der Vorfilter MUSS **und** SOLLTE nimmt.
- [ ] **Abschließen** 👤 „Schreib die Fachgespräch-Notiz für #4“ → Go → 🤖 postet; 👤 committet, merged den Ticket-Branch nach `main` und pusht

**Fertig, wenn:** `bsi.json` eingecheckt ist, `cis.json` per `.gitignore` draußen bleibt, alle Tests grün sind und die CIS-Zahl im Issue steht.
**Fürs Fachgespräch:** OSCAL, Commit-SHA plus SHA-256, Reproduzierbarkeit, Lizenz (keine CIS-Volltexte im Repo).

---

### Schritt 5 – #5 Extraktion DSGVO und SDM

**Ziel:** DSGVO und die SDM-Bausteine sind deterministisch in Anforderungen zerlegt und vorgefiltert.
**Voraussetzung:** Schritt 1 (`normalize()`).

- [ ] **Branch** 👤 `git switch -c ticket-5`
- [ ] **Spike** 🛠 _Junie_ · 👤 „Zeig mir die Struktur des DSGVO-Formex-XML (`ARTICLE`, `PARAG`, Berichtigungs-Markierungen) und der SDM-Bausteine (Kopfzeilen, Maßnahmen-IDs). Nur anschauen.“
- [ ] **Starten** 🛠 _Junie_ · 👤 „Lies docs/FAHRPLAN.md Schritt 5 und `gh issue view 5`. Setze es per TDD um (ADR 0008).“ DSGVO und SDM kommen in `data/sources.json`. Stichproben-Tests: `Art. 32`, `M60.D01`, jede ID genau einmal, DSGVO genau 99 Artikel
- [ ] **Bauen** 🛠 erzeugt `data/extracted/dsgvo.json` und `sdm.json`
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #5`
- [ ] **Verstehen** 👤 Erkläre in 2 Sätzen, warum SDM Protokollieren (M43) bewusst fehlt.
- [ ] **Abschließen** 👤 „Schreib die Fachgespräch-Notiz für #5“ → Go → 🤖 postet; 👤 committet, merged den Ticket-Branch nach `main` und pusht

**Fertig, wenn:** Beide JSON-Dateien eingecheckt sind und alle Tests grün sind.
**Fürs Fachgespräch:** SDM als Umsetzung der DSGVO-Grundsätze, Bußgeldstufen nach Art. 83.

---

### Schritt 6 – #6 Auswahlliste (Kontrollpunkt)

**Ziel:** Es steht fest, welche Anforderungen in den Bounded Catalog kommen. Du hast die Auswahl gelesen und freigegeben.
**Voraussetzung:** Schritte 2–5.

- [ ] **Branch** 👤 `git switch -c ticket-6`
- [ ] **Starten** 🛠 _Junie_ · 👤 „Lies docs/FAHRPLAN.md Schritt 6 und `gh issue view 6`. Setze es per TDD um.“
      Reihenfolge: `archetype_profiles.json` → `ranking.py` (reihum, Gleichstand, gesetzte Plätze) → Relevanzfilter → `curation.py` mit `FunctionModel`
- [ ] **Echter Lauf** 🛠 👤 „Erzeuge die Auswahllisten mit Bedrock“ (ca. 0,50 $)
- [ ] **Kontrollpunkt** 👤 Lies `selection_arch.json` und `selection_spec.json` (ca. 10 Minuten):
      Betrifft jede Regel einen Baustein unserer Archetypen? Stimmen die Ressourcentypen? Sind Verschlüsselung, Logging, Zugriffsrechte und die Pflichtanker drin?
      Falls nein: 🆕 _Opus_ · 👤 `/grilling Auswahlliste nachschärfen`, bevor es weitergeht.
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #6`
- [ ] **Verstehen** 👤 `/ihk-check Bounded Catalog und Ranking`
- [ ] **Abschließen** 👤 „Schreib die Fachgespräch-Notiz für #6“ → Go → 🤖 postet; 👤 committet, merged den Ticket-Branch nach `main` und pusht

**Fertig, wenn:** Beide Auswahllisten eingecheckt sind, du sie freigegeben hast und die Kosten im Issue stehen.
**Fürs Fachgespräch:** Vollständigkeit statt Top-K, „Das LLM urteilt, der Code wählt aus“, gesetzte Plätze.

---

### Schritt 7 – #12 Prüfregeln formulieren und Gate

**Ziel:** `rules_spec.json` und `rules_arch.json` liegen vor; jede Prüfregel hat das Gate bestanden.
**Voraussetzung:** Schritt 6 inklusive Kontrollpunkt.

- [ ] **Branch** 👤 `git switch -c ticket-12`
- [ ] **Starten** 🛠 _Junie_ · 👤 „Lies docs/FAHRPLAN.md Schritt 7 und `gh issue view 12`. Setze es per TDD um.“
      Reihenfolge: `gates.py` (Schema, Anker, Zitat, Querverweise) → `formulate_rule` mit `FunctionModel`
- [ ] **Echter Lauf** 🛠 👤 „Formuliere die Prüfregeln mit Bedrock“
- [ ] **Stichprobe** 👤 Lies 5 Prüfregeln: Sind `compliant_if` und `violation_if` prüfbar? Passt `source_quote` zur Norm?
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #12`
- [ ] **Verstehen** 👤 Erkläre in 2 Sätzen, warum der Code den Primäranker setzt und nicht das LLM.
- [ ] **Abschließen** 👤 „Schreib die Fachgespräch-Notiz für #12“ → Go → 🤖 postet; 👤 committet, merged den Ticket-Branch nach `main` und pusht

**Fertig, wenn:** Beide Kataloge eingecheckt sind, das Gate grün ist und die Stichprobe gepasst hat.
**Fürs Fachgespräch:** Zitat statt Behauptung, erfundene Fundstellen, Draft-Pattern im Build.

---

### Schritt 8 – #7 Golden Archetypes mit Freigabe

**Ziel:** ARCH-01 bis -03 sind als CDK gebaut und freigegeben, mit dokumentierten Ausnahmen.
**Voraussetzung:** Schritt 7. Node.js und CDK CLI lokal installiert.

- [ ] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #7 umsetzen`
      Reihenfolge: Allowlist-Filter → Struktur-Soll → Compliance-Soll (N/A-Sperre) → Schleife mit höchstens 3 Runden (mit Fakes) → `cdk_runner.py`
- [ ] **Echter Build** 👤 „Baue die 3 Archetypen“ → Go. Bei Fehlern von synth oder cdk-nag: 👤 `/diagnosing-bugs`
- [ ] **Offene Frage** 👤 „Klär, ob Lambda-Logging `log-group:NAME:*` braucht“ → bei Ja: Ausnahme mit Begründung in `data/nag_allowlist.json`
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #7`
- [ ] **Verstehen** 👤 `/ihk-check cdk-nag und Ausnahmen`
- [ ] **Abschließen** 👤 „Schreib die Fachgespräch-Notiz für #7“ → Go → 🤖 postet; 👤 committet und pusht

**Fertig, wenn:** `archetypes.json` 3 freigegebene Archetypen mit `approval` enthält.
**Fürs Fachgespräch:** Vier-Augen-Prinzip, Risikoakzeptanz, Funktionstrennung, Least Privilege.

---

### Schritt 9 – #8 Preset-Gate und Build-Workflow

**Ziel:** Der Build der Wissensbasis läuft per Knopfdruck in GitHub Actions und öffnet nur bei Grün einen Pull Request.
**Voraussetzung:** Schritte 2 und 8.

- [ ] **Branch** 👤 `git switch -c ticket-8`
- [ ] **Starten** 🛠 _Junie_ · 👤 „Lies docs/FAHRPLAN.md Schritt 9 und `gh issue view 8`. Setze es per TDD um.“
      Reihenfolge: Preset-Gate (Gesamtstatus, Pflicht-Befunde, Archetyp, Hash-Check) → `python -m kb_build` → `build-kb.yml` ohne Logik
- [ ] **Einrichten** 🆕 _Sonnet_ · 👤 `/wizard OIDC-Provider und Rolle für build-kb.yml, nur Bedrock eu.-Profil` → 👤 Wizard ausführen
- [ ] **Ausprobieren** 👤 Workflow in GitHub Actions starten → PR lesen, Kosten prüfen
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #8`
- [ ] **Verstehen** 👤 Erkläre in 2 Sätzen, warum OIDC besser ist als ein Access Key in GitHub.
- [ ] **Abschließen** 👤 „Schreib die Fachgespräch-Notiz für #8“ → Go → 🤖 postet; 👤 committet, merged den Ticket-Branch nach `main` und pusht

**Fertig, wenn:** Ein Workflow-Lauf einen grünen PR mit Kostenangabe geöffnet hat.
**Fürs Fachgespräch:** OIDC statt langlebiger Keys, Gate vor Merge, alte Version bleibt bei Rot aktiv.

---

### Schritt 10 – #9 GovGuard-Stack und Audit-Endpunkte

**Ziel:** Die Audit-API läuft in eu-central-1 und protokolliert jeden Aufruf.
**Voraussetzung:** Schritt 3. Für Ausnahmen Schritt 8 abgeschlossen.

- [ ] **Starten** 🆕 _Opus_ · 👤 `/tdd Issue #9 umsetzen`
      Reihenfolge: `Trace` und `AuditEvent` bauen → `handler.py` → CDK-Stack mit Assertions-Tests (Tests auf das erzeugte Template)
- [ ] **Sicherheit** 👤 `/security-review` vor dem ersten Deploy
- [ ] **Einrichten** falls nötig: 👤 `/wizard cdk bootstrap für eu-central-1` → 👤 Wizard ausführen
- [ ] **Deploy + Test** 👤 „Deploye den Stack und ruf /audit/spec mit einem Preset auf“ → Go → 👤 `/run`
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #9`
- [ ] **Verstehen** 👤 `/ihk-check IAM, KMS und Audit-Protokoll`
- [ ] **Abschließen** 👤 „Schreib die Fachgespräch-Notiz für #9“ → Go → 🤖 postet; 👤 committet und pusht

**Fertig, wenn:** Ein Aufruf einen Audit-Report liefert und das Audit-Ereignis in CloudWatch Logs steht, ohne Eingabetext.
**Fürs Fachgespräch:** Least Privilege, KMS-CMK, Datenminimierung, Rückverfolgung, 0 € im Leerlauf.

---

### Schritt 11 – #10 Archetyp-Auswahl

**Ziel:** Bei einer Spezifikation ohne FAIL liefert GovGuard ARCH-01, -02, -03 oder „keiner“.
**Voraussetzung:** Schritte 8 und 10.

- [ ] **Branch** 👤 `git switch -c ticket-10`
- [ ] **Starten** 🛠 _Junie_ · 👤 „Lies docs/FAHRPLAN.md Schritt 11 und `gh issue view 10`. Setze es per TDD um.“ (Auswahl, Ablehnung bei FAIL, `NONE`)
- [ ] **Deploy + Test** 🆕 _Sonnet_ · 👤 „Deploye und ruf /archetype/select mit einem Spec-Preset auf“ → Go → 👤 `/run`
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #10`
- [ ] **Verstehen** 👤 Erkläre in 2 Sätzen, warum „keiner passt“ eine erlaubte Antwort ist.
- [ ] **Abschließen** 👤 „Schreib die Fachgespräch-Notiz für #10“ → Go → 🤖 postet; 👤 committet, merged den Ticket-Branch nach `main` und pusht

**Fertig, wenn:** Das Preset liefert den Soll-Archetyp, und ein Report mit FAIL wird mit HTTP 422 abgelehnt.
**Fürs Fachgespräch:** geschlossene Antwortmenge, keine Generierung zur Laufzeit.

---

### Schritt 12 – #11 Deploy-Pipeline und Demo-UI

**Ziel:** Jeder Push auf `main` rollt GovGuard nach dem Selbst-Audit aus; die Demo-UI ist öffentlich erreichbar.
**Voraussetzung:** Schritte 7, 10 und 11.

- [ ] **Einrichten** 🆕 _Sonnet_ · 👤 `/wizard Einmalige AWS-Einrichtung für deploy.yml: OIDC-Deploy-Rolle, IAM-User für Streamlit, Secrets` → 👤 Wizard ausführen. Der Wizard ist zugleich die Anleitung, die das Ticket verlangt.
- [ ] **Bauen Pipeline** 🤖 _Sonnet_ · 👤 „Setze aus Issue #11 die `deploy.yml` um“ → Schritt für Schritt mit Go
- [ ] **Bauen UI** 👤 `git switch -c ticket-11-ui` → 🛠 _Junie_ · 👤 „Lies docs/FAHRPLAN.md Schritt 12 und `gh issue view 11`. Baue nur die Streamlit-UI in `ui/`.“
- [ ] **Ausprobieren** 👤 `/run Streamlit-UI lokal starten, Preset auditieren, Screenshot`
- [ ] **Sicherheit** 🆕 _Opus_ · 👤 `/security-review`
- [ ] **Live** 👤 Pushen → Pipeline beobachten → UI auf Streamlit Community Cloud öffnen
- [ ] **Prüfen** 👤 `/code-review gegen Issue #11`
- [ ] **Verstehen** 👤 `/ihk-check Gesamtprojekt`
- [ ] **Abschließen** 👤 „Schreib die Fachgespräch-Notiz für #11“ → Go → 🤖 postet; 👤 committet, merged den Ticket-Branch nach `main` und pusht

**Fertig, wenn:** Ein Push den Deploy mit Selbst-Audit auslöst und die öffentliche UI ein Preset auditiert.
**Fürs Fachgespräch:** Dogfooding, ein einziger Weg in die Produktion, bewusstes US-Hosting nur mit fiktiven Daten.
