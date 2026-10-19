# Lehrbuch kb-build – Faktenbasis (Stand 13.10.2026)

Diese Dateien sind die **Faktenbasis** für ein Lehrbuch über die Wissensbasis-Pipeline `kb_build` von GovGuard. Sie sind aus dem Code, den ADRs, den Issues #1–#21 und den Daten im Repo abgeleitet (Commit `28b62e7`, Arbeitsbaum sauber). Jede Aussage nennt ihren Beleg als `Datei:Funktion` oder ADR-Nummer.

## Zielgruppe und Zweck

- Leser: Daniel (Cloud Business Expert, IHK-Fachgespräch Modul 4) und Menschen, die GovGuard verstehen wollen. Später Lernmaterial in NotebookLM.
- Ziel: Verhalten und Eigenschaften der Pipeline verstehen und im Fachgespräch verteidigen können, nicht nur nachlesen.

## Kapitel

| Datei | Thema |
|---|---|
| `00-uebersicht.md` | Was die Pipeline tut, Ablauf, Arbeitsteilung LLM und Code |
| `01-quellen.md` | Sechs Regelwerke, Pinning, SHA-256, Lizenz |
| `02-extraktion.md` | Aus Rohdateien werden Anforderungen, Vorfilter |
| `03-pruefumfang.md` | Handgepflegte Referenzdaten: Prüfumfang, Typen, Eigenschaften, Archetyp-Steckbriefe, Presets |
| `04-auswahl-stufe2.md` | Das LLM urteilt „prüfbar?“, Cache, Ebene (`scope_level`) |
| `05-bounded-catalog.md` | Der Code wählt aus: Auswahlprotokoll, Pflichtanker- und Abdeckungs-Gate |
| `06-pruefregeln.md` | Das LLM formuliert Prüfregeln, der Code setzt die Herkunft |
| `07-schutzmechanismen.md` | Querschnitt: welche Halluzination wird wo abgefangen |
| `08-llm-anbindung.md` | Pydantic AI, Tool-Choice, Provider Groq und Bedrock |
| `09-code-struktur.md` | Module, Pfade, Tests, Qualitätsgrenzen |
| `10-zahlen-und-beispiele.md` | Alle Zahlen und echte Datenbeispiele auf einen Blick |
| `99-offen-und-grenzen.md` | Was fehlt, bekannte Grenzen, veraltete Stellen in anderen Dokumenten |

## Hinweise für das Ausformulieren

- **Nichts erfinden.** Zahlen, Namen und Abläufe nur aus diesen Dateien. Fehlt etwas, offen lassen und markieren.
- **Code-Namen englisch lassen** (`Requirement`, `scope_level`, `check_rules`), Erklärungen deutsch. Fachwort beim ersten Auftreten in einem eigenen ganzen Satz erklären.
- **ADR-Nummern als Begründung nennen**, denn das Lehrbuch soll das Warum tragen. Gilt: ADR 0011 ersetzt ADR 0002; ADR 0014 ersetzt ADR 0010.
- **Nur Gebautes als Gebautes beschreiben.** Preset-Gate, `build-kb.yml` und Golden Archetypes sind noch nicht gebaut (siehe `99-offen-und-grenzen.md`).
- Jedes Kapitel hat dieselben Abschnitte: Zweck · Ablauf · Eigenschaften und Garantien · Warum so · Beispiel · Fachbegriffe · Grenzen · Fragen für das Fachgespräch.
- Wünschenswert beim Ausformulieren: eine Analogie je Kapitel, ein Merksatz, 3 Übungsfragen mit Musterantwort.
