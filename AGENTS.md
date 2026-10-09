# GovGuard – Regeln für Coding-Agents (Junie)

GovGuard ist ein Compliance-Copilot (DSGVO, BSI IT-Grundschutz) in Python auf AWS. Verbindlich sind `CONTEXT.md` (Begriffe und ihre Code-Namen), `docs/adr/` und `docs/ARCHITECTURE.md` → *Code-Struktur*. Du hast zwei Rollen (`docs/FAHRPLAN.md`): Du baust die Streamlit-UI (#11), oder du prüfst als zweite Meinung einen Diff (Abschnitt *Review*). Dein Auftrag ist der genannte Schritt plus das Issue (`gh issue view N`).

- **Git:** Arbeite direkt auf `main` und lass deine Änderungen uncommittet; der Mensch committet nach dem Review. Keine Pushes, keine PRs.
- **TDD:** Schreib erst einen roten Test, dann den Code; zu jedem Akzeptanzkriterium gehört mindestens ein Test. Fertig ist ein Schritt, wenn `pytest` und `ruff check` grün sind.
- **I/O nur in Adaptern:** boto3 und das Bedrock-Modell nur in `src/govguard/aws_services.py`, subprocess nur in `src/kb_build/cdk_runner.py`, HTTP-Downloads nur in `src/kb_build/source_fetch.py`. Die Prüflogik bleibt rein; Tests nutzen Fakes bzw. Pydantic AI `FunctionModel`/`TestModel`.
- **Kleine Einheiten:** Ein Modul hat ca. 200 Zeilen, eine Funktion ca. 30 Zeilen. Wird es größer, teile auf.
- **Sprache:** Code, Bezeichner, JSON-Felder und Kommentare sind englisch (Normbezug als Kürzel, z. B. `# Enforces BSI OPS.1.1.2.A3`). LLM-Prompts, UI-Texte und Report-Inhalte sind deutsch.
- **AWS:** nur `eu-central-1`, Bedrock nur mit `eu.`-Inferenzprofil (ADR 0001). Tests rufen AWS nie auf. Bedrock-Läufe startest du nur auf ausdrückliche Anweisung; deployen darfst du nie.
- **Daten:** Keine Quelldateien und keine CIS-Volltexte ins Repo (ADR 0008).
- **Workflow-YAML:** keine Logik, nur `python -m …`.
- **Nicht ändern:** `docs/`, `CLAUDE.md`, `AGENTS.md` und `data/presets/` (die Soll-Ergebnisse legt der Mensch fest).
- **Stopp statt Anpassen:** Regeln und Konstanten aus `docs/ARCHITECTURE.md` und `docs/adr/` (z. B. Vorfilter-Kriterien) übernimmst du unverändert. Passt eine erwartete Zahl oder ein Test nach zwei Anläufen nicht, hörst du auf und meldest die Abweichung mit deinen Messwerten; du biegst nie Code oder Konstanten auf die Zielzahl hin.
- **Abschluss:** Fasse kurz zusammen, welche Dateien du geändert hast und welche Kriterien noch offen sind. Füge die letzten Zeilen der Ausgabe von `pytest -q` und `ruff check .` unverändert ein.

## Review (zweite Meinung)

Lautet dein Auftrag „Prüfe `git diff`“, änderst du keine Datei.

- Prüfe den Diff gegen jedes Akzeptanzkriterium des Issues und gegen die Regeln oben. Schau dir echte Ergebnisse an (erzeugte Dateien, `pytest -q`), nicht nur den Code: Grüne Tests mit falschen Daten sind der häufigste Fehler.
- Melde höchstens 10 Befunde, schwerste zuerst, je Befund: `Datei:Zeile`, was falsch ist und die zitierte Issue-Zeile oder Regel. Unsicheres kennzeichnest du als Vermutung.
- Keine Stilfragen, die `ruff` schon prüft.
