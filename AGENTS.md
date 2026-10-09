# GovGuard – Regeln für Coding-Agents (Junie)

GovGuard ist ein Compliance-Copilot (DSGVO, BSI IT-Grundschutz) in Python auf AWS. Verbindlich sind `CONTEXT.md` (Begriffe und ihre Code-Namen), `docs/adr/` und `docs/ARCHITECTURE.md` → *Code-Struktur*. Dein Auftrag ist der genannte Schritt in `docs/FAHRPLAN.md` plus das Issue (`gh issue view N`).

- **Branch:** Arbeite nur auf dem Ticket-Branch. Nie auf `main` committen, nicht pushen, keine PRs anlegen.
- **TDD:** Schreib erst einen roten Test, dann den Code; zu jedem Akzeptanzkriterium gehört mindestens ein Test. Fertig ist ein Schritt, wenn `pytest` und `ruff check` grün sind.
- **I/O nur in Adaptern:** boto3 und das Bedrock-Modell nur in `src/govguard/aws_services.py`, subprocess nur in `src/kb_build/cdk_runner.py`, HTTP-Downloads nur in `src/kb_build/source_fetch.py`. Die Prüflogik bleibt rein; Tests nutzen Fakes bzw. Pydantic AI `FunctionModel`/`TestModel`.
- **Kleine Einheiten:** Ein Modul hat ca. 200 Zeilen, eine Funktion ca. 30 Zeilen. Wird es größer, teile auf.
- **Sprache:** Code, Bezeichner, JSON-Felder und Kommentare sind englisch (Normbezug als Kürzel, z. B. `# Enforces BSI OPS.1.1.2.A3`). LLM-Prompts, UI-Texte und Report-Inhalte sind deutsch.
- **AWS:** nur `eu-central-1`, Bedrock nur mit `eu.`-Inferenzprofil (ADR 0001). Tests rufen AWS nie auf. Bedrock-Läufe startest du nur auf ausdrückliche Anweisung; deployen darfst du nie.
- **Daten:** Keine Quelldateien und keine CIS-Volltexte ins Repo (ADR 0008).
- **Workflow-YAML:** keine Logik, nur `python -m …`.
- **Nicht ändern:** `docs/`, `CLAUDE.md`, `AGENTS.md` und `data/presets/` (die Soll-Ergebnisse legt der Mensch fest).
- **Abschluss:** Fasse kurz zusammen, welche Dateien du geändert hast und welche Kriterien noch offen sind.
