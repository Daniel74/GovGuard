# 09 – Code-Struktur, Pfade und Qualitätsgrenzen

## Zweck

`kb_build` ist bewusst **klein und aufgeteilt**: Eine Lösung, die der Autor vollständig verteidigen kann (CLAUDE.md). Dieses Kapitel zeigt, wo was liegt, welche Regeln ein Test erzwingt und wie man eine neue Quelle ergänzt.

## Ordner

```
src/govguard/         Laufzeit-Kern (wird später das Lambda-Paket): models.py, text.py,
                      audit_engine.py, aws_services.py, cli.py
src/kb_build/         Build-Werkzeug, importiert govguard, nie umgekehrt
  __main__.py         Einstieg: Befehle extract | select | rules | cfn-properties
  paths.py            alle Datenpfade (BuildPaths)
  gates.py            Pflichtanker-, Abdeckungs-, Regel-Gate (rein)
  source_fetch.py     einziger Ort für HTTP + SHA-256
  groq_services.py    einziger Ort für Groq
  extract/            bsi, cis, c5, fsbp, dsgvo, sdm, prowler, models, run
  select/             classify, curation, judgement_cache, models, run
  rules/              formulate, criteria, quality, run
  reference/          scope, cfn_types, cfn_properties, archetype_profiles, run
data/input/           von Hand gepflegt
data/intermediate/    Zwischenergebnisse, eingecheckt fürs Review
data/knowledge_base/  nur das Endergebnis rules_*.json (geht später nach S3)
tests/                pytest, flach (rund 35 Testmodule)
```

Insgesamt rund 2.300 Zeilen Code in `src/`, kein Modul über 200 Zeilen.

## Drei Schichten

| Schicht | Aufgabe | Beispiele |
|---|---|---|
| **Einstieg** | verbindet nur | `__main__.py`, `*/run.py` (Dateien lesen und schreiben) |
| **Logik, rein** | keine I/O, gleiche Eingabe gleiche Ausgabe | Adapter, `classify`, `curation`, `formulate`, `gates`, `reference/*` |
| **Adapter** | einziger Ort für Außenwelt | `source_fetch.py` (HTTP), `groq_services.py`, `aws_services.py`, später `cdk_runner.py` (subprocess) |

Von der Logik führt **kein Pfeil** zu den Adaptern. Der Einstieg reicht Adapter hinein (Dependency Injection). Das Muster in jedem Schritt: `run.py` liest Dateien und ruft die reine Funktion; die reine Funktion schreibt nichts.

## Alle Pfade an einer Stelle (`paths.py`, Issue #20)

`BuildPaths` ist ein unveränderliches Dataclass mit `input`, `intermediate`, `knowledge_base` und Properties wie `sources_json`, `scope`, `extracted`, `judgement_cache`. `out_file(kind, audit_type)` liefert z. B. `selection_arch.json`, `verdicts_spec.json`, `rules_arch.json` (`rules` landet im Ordner `knowledge_base`, alles andere in `intermediate`). Ein Test verbietet Datenpfade anderswo.

Warum `data/` nach **Herkunft** getrennt ist (Lernkarte #20): Was von Hand kommt (`input/`), was der Build erzeugt (`intermediate/`), und was ausgeliefert wird (`knowledge_base/`, nur dieses geht nach S3). Zwischenergebnisse liegen eingecheckt im Repo, damit der Git-Diff Änderungen zwischen zwei Läufen zeigt; die Download-Cache-Dateien und lizenzierten Volltexte nicht.

## Qualitätsgrenzen, die ein Test erzwingt (`tests/test_architecture.py`)

- Ein Modul ist höchstens **200 Zeilen** lang.
- Imports mit Außenwirkung nur im jeweiligen Adapter: `boto3`/`botocore`/Bedrock nur in `aws_services.py`, `groq` nur in `groq_services.py`, `subprocess` nur in `cdk_runner.py`, HTTP-Bibliotheken (`urllib.request`, `http.client`, `requests`, `httpx`) nur in `source_fetch.py`.
- `ruff` (Konfiguration in `pyproject.toml`) prüft Stil (Zeilenlänge 100) und die Größe der Funktionen: höchstens 30 Statements (`PLR0915`), höchstens 5 Argumente (`PLR0913`), zyklomatische Komplexität (Anzahl der Verzweigungen) höchstens 8 (`C901`).
- Workflow-YAML enthält keine Logik, nur `python -m …` (gilt für `build-kb.yml`, noch nicht gebaut).

## Tests

- Rund 3.200 Zeilen Tests in rund 35 Modulen; Stand Issue #19: 339 Tests grün.
- **TDD:** erst ein roter Test, dann der Code. Testnamen sind Sätze, die das Verhalten beschreiben, z. B. `test_a_pinned_anchor_with_an_account_duty_aborts_the_build`. Sie sind die genaueste Verhaltensbeschreibung der Pipeline.
- **Fakes statt Netz:** `FunctionModel`/`TestModel` für das LLM, ein Fetcher-Fake für HTTP, `tmp_path` für Dateien.
- **Golden-Tests** gegen echte Extrakte (`test_extracted_golden.py`) mit fester Sollzahl.
- **Das Soll kommt vom Menschen:** Presets mit handgesetztem Soll verhindern zirkuläre Tests.

## Neue Quelle hinzufügen (Rezept, ENTWICKLUNG.md Abschnitt 5)

1. `data/input/sources.json`: URL, Version (Commit oder Tag), SHA-256, Lizenz.
2. Adapter `extract/<quelle>.py` mit `extract()` und `prefilter()` (bei Prowler-Quellen nur ein `ProwlerFormat`).
3. Eintrag in `ADAPTERS` (`extract/run.py`), in `SourceName` (`govguard/models.py`) und in `SELECTIONS` (`select/run.py`).
4. Lizenz: offen → Extrakt einchecken und `NOTICE` ergänzen; sonst Extrakt in `.gitignore`.
5. Test mit kleinem Fixture: Anzahl, Stichprobe, Vorfilter mit Begründung.

## Fachbegriffe

- **Reine Funktion / Logik ohne I/O:** leicht testbar, deterministisch.
- **Adapter:** dünne Schicht um die Außenwelt (Netz, AWS, Prozesse).
- **Dependency Injection:** Abhängigkeiten von außen hineinreichen.
- **Deep Module / kleine Einheiten:** ein Modul, eine Aufgabe.
- **Refactoring ohne Verhaltensänderung:** Struktur ändern, Tests bleiben grün (Issue #20).

## Fragen für das Fachgespräch

1. Wie ist sichergestellt, dass nur ein Modul Netzwerkzugriff hat?
2. Warum liegen Zwischenergebnisse im Repo, aber nur `rules_*.json` geht nach S3?
3. Welche Schritte sind nötig, um eine neue Quelle aufzunehmen?
