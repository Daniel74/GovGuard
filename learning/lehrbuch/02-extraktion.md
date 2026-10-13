# 02 – Extraktion und Vorfilter

## Zweck

Aus den sechs Rohformaten entsteht ein einheitliches Modell: eine Liste von **Anforderungen** je Quelle, jede mit ID, Titel, Text, Primäranker, Attributen und einem Vorfilter-Urteil. Es wird **alles** extrahiert; der Vorfilter markiert nur (ADR 0011). Kein LLM beteiligt. Der Befehl ist `python -m kb_build extract` (`extract/run.py:extract_all`).

## Ablauf

1. `extract_all()` liest `sources.json`, lädt und prüft jede Datei (Kapitel 01).
2. Je Quelle ein **Adapter** mit `extract(origin, data, version)`: reine Funktion ohne I/O, gleiche Eingabe, gleiche Ausgabe.
3. `mark_prefilter()` ruft den Vorfilter des Adapters auf: `None` heißt behalten, ein fester deutscher Satz heißt verwerfen. Der Satz landet später im Auswahlprotokoll.
4. `merge_sources()` fügt die drei SDM-PDFs zu einer Datei zusammen.
5. Ausgabe: `data/intermediate/extracted/{bsi,cis,fsbp,c5,dsgvo,sdm}.json` (die Zuordnung steht in der Konstante `ADAPTERS`).

## Das Datenmodell (`extract/models.py`)

- `Requirement`: `id`, `title`, `text`, `primary_anchor`, `attributes` (Metadaten je Quelle), `prefilter_passed`, `prefilter_reason`.
- `ExtractedSource`: `source`, `version`, `origin`, `requirements`. Ein Validator verbietet doppelte IDs (jede ID genau einmal).
- Der **Primäranker** ist das stabile Etikett einer Anforderung, z. B. `BSI GS++ DET.3.1`. Der Code setzt ihn hier, nie das LLM.

## Die Adapter im Vergleich

| Quelle | Einheit | Primäranker-Format | Vorfilter (Code) | gesamt → bleibt |
|---|---|---|---|---|
| BSI | Control im OSCAL-Katalog (auch Unter-Controls) | `BSI GS++ DET.3.1` | `modal_verb` ∈ {MUSS, SOLLTE}, `sec_level` = `normal-SdT`, Praktik ∈ {DLS, BER, DET, KONF, BES, ARCH} | 1000 → 380 |
| C5 | Kriterium | `BSI C5 CRY-03.01B` | Bereich ∈ {OPS, IAM, CRY, COS, PSS} | 610 → 300 |
| CIS | Empfehlung | `CIS AWS v7.0.0 3.1.4` | Kapitel 2 IAM, 3 Storage, 4 Logging, 6 Networking | 70 → 54 |
| FSBP | Control | `AWS FSBP SNS.1` | `Service` gehört zum Prüfumfang (Lambda, S3, KMS, RDS, EC2 …) | 286 → 150 |
| DSGVO | Artikel | `DSGVO Art. 32` | Kapitel II–V (Art. 5–49) | 99 → 46 |
| SDM | Maßnahme | `SDM Löschen M60.D01` | keiner, alle Ebenen D, S, P bleiben | 147 → 147 |

Die Zahlen stammen aus `data/intermediate/extracted/*.json` (Stand 13.10.2026).

## Besonderheiten je Adapter

- **BSI** (`extract/bsi.py`): Der Katalog ist verschachtelt, `_controls()` läuft tiefenorientiert durch alle Gruppen und Controls, auch Unter-Controls wie `GC.3.1.1`. OSCAL-Platzhalter `{{ insert: param, … }}` ersetzt der Code durch das Parameter-Label (z. B. „regelmäßig“), damit Zitate später im Text stehen. Attribut `cia_sum` addiert Vertraulichkeit, Integrität, Verfügbarkeit. **Warum SOLLTE durchgelassen wird** (ADR 0007): Grundschutz++ vergibt MUSS nur an 30 organisatorische Controls; alle technischen Anforderungen wie `DET.3.1` stehen auf SOLLTE.
- **Prowler-Familie** (`extract/prowler.py`, `cis.py`, `fsbp.py`, `c5.py`): Ein gemeinsamer Parser; jede Quelle beschreibt nur ihr `ProwlerFormat` (Anker, Titel, Text, Attribute, Vorfilter). `strip_markdown()` entfernt `**` und Backticks und **repariert doppelt kodiertes UTF-8** (Prowler-Text mit `â€™` statt `’`, z. B. FSBP ECS.3). Hintergrund: Der Existenz-Check vergleicht gegen den Prowler-Text ohne Markdown-Zeichen (ADR 0008). C5 hat keinen Titel, deshalb dient die `SubSection` als Titel.
- **DSGVO** (`extract/dsgvo.py`): Das Formex-XML wird mit ElementTree gelesen. Layout-Elemente (`PARAG`, `LIST` …) werden zu Wortgrenzen, Anführungszeichen-Elemente zu „ und “, Fußnoten (`NOTE`) sind kein Artikeltext. Das Attribut `fine_tier` (2 oder 4 oder 0) hält die Bußgeldstufe nach **Art. 83** fest, als Konstante im Code (`FINE_TIER_4`, `FINE_TIER_2`), weil Art. 83 selbst nicht geparst wird. Es sind alle 99 Artikel extrahiert.
- **SDM** (`extract/sdm.py`): Die Fließtexte zitieren Maßnahmen-IDs nur in Klammern. Nur die **Maßnahmentabelle** in Abschnitt 5 stellt jede ID neben ihre Maßnahme, deshalb liest der Adapter nur diese Tabelle. Eine Zeile kann über mehrere Zeilen laufen und endet mit der PDCA-Spalte und der Gültigkeitsspalte (`V1.0`). Fehlt sie, bricht der Parser mit Fehler ab (fail closed). IDs haben das Format `M60.D01` (Modul, Ebene Daten/Systeme/Prozesse, Nummer).

## Eigenschaften und Garantien

- **Vollständig:** Auch verworfene Anforderungen bleiben in der Datei, mit `prefilter_passed: false` und festem Begründungssatz. Das Auswahlprotokoll (Kapitel 05) kann sie so lückenlos aufführen.
- **Deterministisch und reproduzierbar:** gepinnte Quelle, reine Funktionen, keine Zeitstempel.
- **Golden-Tests:** Tests gegen echte Daten mit fester Sollzahl (z. B. DSGVO 99 Artikel, CIS genau 70, BSI 1000/380) schützen davor, die Regel auf die Zahl zurechtzubiegen (`tests/test_extracted_golden.py`, `test_*_source.py`).

## Beispiele (echte Daten)

```json
{ "id": "DET.3.1", "title": "Protokollierung sicherheitsrelevanter Ereignisse",
  "text": "Detektion für Anwendungen SOLLTE Sicherheitsrelevante Ereignisse mindestens für eine bestimmte Frist protokollieren.",
  "primary_anchor": "BSI GS++ DET.3.1",
  "attributes": {"practice": "DET", "modal_verb": "SOLLTE", "sec_level": "normal-SdT", "cia_sum": 5},
  "prefilter_passed": true }
```

Verworfen (BSI `GC.1.1`): `prefilter_reason` = „Praktik gehört nicht zu ARCH, BER, BES, DET, DLS, KONF.“

## Fachbegriffe

- **Adapter** (hier): Modul, das ein Quellformat in das gemeinsame Modell `Requirement` übersetzt.
- **Vorfilter:** billiger deterministischer Filter auf Metadaten, bevor das LLM Geld kostet.
- **Reine Funktion:** kein I/O; deshalb mit kleinen Fakes testbar.
- **Golden-Test:** Test gegen echte Daten mit fester Sollzahl.
- **Modalverb:** MUSS, SOLLTE, KANN – die Verbindlichkeit einer BSI-Anforderung.

## Grenzen

- **SDM ohne Protokollieren (M43):** Das Modul hat ein eigenes ID-Schema und führt ungültige Maßnahmen durchgestrichen weiter; es bräuchte einen eigenen Parser. Protokollierung deckt das Architektur-Audit ab (BSI DET, CIS Kapitel 4).
- **DSGVO-Einheit „Artikel“:** Art. 5 ergibt nur eine Prüfregel, obwohl er sechs Grundsätze enthält. Sie kommen über das SDM ins Spiel.

## Fragen für das Fachgespräch

1. Warum nimmt der BSI-Vorfilter SOLLTE und nicht nur MUSS?
2. Warum liest der SDM-Adapter nur die Tabelle?
3. Was ist ein Golden-Test, und wovor schützt er?
