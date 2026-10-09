# GovGuard – GovCloud Compliance Copilot

Portfolio- und IHK-Praxisprojekt (Cloud Business Expert, Modul 4). Der Copilot prüft Spezifikationen (DSGVO/SDM) und Architekturen (BSI IT-Grundschutz/CIS) und liefert einen Audit-Report mit PASS/WARN/FAIL. Danach schlägt er einen passenden Golden Archetype als CDK-Entwurf (Python, AWS Solutions Constructs) vor.

Das Projekt ist bewusst **simpel**: lieber eine kleine Lösung, die ich vollständig verteidigen kann, als eine große, die ich nur halb verstehe.

## Leitplanken

- AWS: Daten nur in `eu-central-1`, Inferenz nur in der EU (Bedrock-Profil `eu.`, ADR 0001), 100 % serverless, 0 € variable Kosten im Leerlauf; Fixkosten nur für Sicherheit, z. B. KMS-Schlüssel ca. 1 $/Monat (FinOps).
- Python, Pydantic, Pydantic AI auf der Bedrock Converse API mit Tool-Choice (ADR 0005), Streamlit-UI.
- Wissensbasis als JSON in S3 bzw. im Repo, Bounded Catalog ohne Suche, keine Vektor-DB (ADR 0002).
- Code modular nach `docs/ARCHITECTURE.md` → *Code-Struktur*: boto3 und das Bedrock-Modell für Pydantic AI nur in `aws_services.py`, subprocess nur in `src/kb_build/cdk_runner.py`, HTTP-Downloads nur in `src/kb_build/source_fetch.py`, Prüflogik rein, nie vermischt. Workflow-YAML enthält keine Logik, nur `python -m …`.
- Kleine Einheiten: ein Modul = eine Aufgabe, ca. 200 Zeilen; eine Funktion ca. 30 Zeilen. Wird es größer, teile auf. Die Grenzen prüfen ruff (`pyproject.toml`) und ein pytest-Test.

`docs/Modul4_Praxisprojekt_Emails.md` ist **Rohmaterial**, voller älterer und widersprüchlicher Ideen. Verbindlich sind `CONTEXT.md` (Glossar) und `docs/adr/`. Fehlen sie, gilt das Gespräch mit mir.

## Arbeitsweise: ein Go pro Ticket

1. Zeig zu Beginn den Plan des Tickets: die TDD-Zyklen als nummerierte Liste, je eine Zeile (was, welche Datei).
2. Nach meinem **Go** arbeite alle Zyklen am Stück ab. Halte nur an einer **Weichenstellung** an: IAM, Verschlüsselung, Netzwerk, Datenresidenz, Kosten-Trade-off, Prompt-Design. Oder wenn ein Test nach zwei Anläufen rot bleibt.
3. Zum Schluss: geänderte Dateien, Ergebnis von pytest und ruff, offene Kriterien.

Ich arbeite allein und sequentiell direkt auf `main`. Commits mache ich selbst oder sage es explizit.

## Definition of Done je Ticket

- Alle Akzeptanzkriterien erfüllt, Tests und ruff grün, Review ohne offene Punkte.
- Lernkarte über `/verstehen <Issue-Nr.>` in `learning/lessons/`.

## Sprache

- Deutsch, einfach und klar, Niveau pragmatischer Senior Engineer.
- Fachwort beim ersten Auftreten in einem Halbsatz erklären.
- **Rule of 3**: maximal 3 Bulletpoints, Fließtext maximal 3 Zeilen. Code-Erklärungen: Was macht es? Warum so (Bezug BSI/AWS)? Welcher Begriff ist fürs Fachgespräch wichtig?
- **Projektsprache:** Code, Bezeichner, JSON-Felder und Kommentare englisch (Normbezug als Kürzel, z. B. `# Enforces BSI OPS.1.1.2.A3`). LLM-Prompts, Doku, UI und Inhalte der Audit-Reports deutsch. Englische Code-Namen der Fachbegriffe stehen in `CONTEXT.md` (*Code*).

## Doku: lean

Jedes Dokument muss ich in 2 Minuten lesen und verstehen können. Diese Regeln haben Vorrang vor den Templates der Skills (`/to-spec`, `/to-tickets`, `/domain-modeling`):

- **Issue / Spec**: maximal ca. 15 Zeilen. Abschnitte: *Ziel* (1–2 Sätze), *Akzeptanzkriterien* (3–5 prüfbare Punkte), *Offene Fragen*. Höchstens 5 User Stories.
- **ADR** (`docs/adr/NNNN-slug.md`): eine Seite. *Kontext*, *Entscheidung*, *Konsequenzen*, *Fachgespräch-Satz* (1 Satz zur Verteidigung).
- **Glossar** (`CONTEXT.md`): ein Begriff, eine Zeile.
- Dokumente entstehen erst, wenn es etwas Entschiedenes aufzuschreiben gibt.

## Agent skills

### Issue tracker

GitHub Issues im Repo `Daniel74/GovGuard` (öffentlich) über die `gh` CLI. „Publish to the issue tracker“ bedeutet `gh issue create`. Blockierende Tickets stehen als `Blocked by: #NN` im Text.

### Triage labels

Standard-Labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. Fehlt ein Label, frag mich und lege es danach mit `gh label create` an.

### Domain docs

Single-context: `CONTEXT.md` im Root und `docs/adr/`. Lies beide vor der Arbeit an einem Bereich, falls vorhanden. Beide entstehen lazy über `/grill-with-docs`.

### Lern-Workspace

Lernen findet in `learning/` statt: `MISSION.md`, Lernkarten in `lessons/`, Lücken in `learning-records/`. Verständnisfragen gehören in `/verstehen`, nicht in die Bauphase.
