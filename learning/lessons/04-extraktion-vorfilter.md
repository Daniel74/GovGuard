# #4 Extraktion und Vorfilter BSI/CIS

## Was es tut
`python -m kb_build` lädt BSI Grundschutz++ (OSCAL) und CIS AWS v7 (Prowler-JSON) gepinnt vom Herausgeber, prüft die SHA-256 und zerlegt jede Quelle in **alle** Anforderungen (BSI 1000, CIS 70). Ein Vorfilter aus reinem Code markiert die Kandidaten (BSI 380, CIS 45).
`sources.json → source_fetch (HTTP + SHA-256) → Adapter extract() → prefilter() → data/extracted/bsi.json, cis.json`

## Wo im Code
- [source_fetch.py](../../src/kb_build/source_fetch.py): der einzige Ort für HTTP; bricht bei falscher Prüfsumme ab, auch bei manipuliertem Cache.
- [bsi.py](../../src/kb_build/sources/bsi.py) / [cis.py](../../src/kb_build/sources/cis.py): reine Adapter ohne I/O; die Kriterien stehen als Konstanten nach ARCHITECTURE 1.1.
- [__main__.py](../../src/kb_build/__main__.py): verbindet nur (lesen, Adapter aufrufen, schreiben).

## Entscheidung und Warum
- **Wo die Dateien entstehen:** Es gibt nur einen Befehl, `python -m kb_build`. Heute läuft er lokal, ab #8 auch im manuellen Workflow `build-kb.yml` auf GitHub Actions. Dort ist er Stufe 1 der Kette. Der Workflow-Runner ist eine Wegwerf-Maschine: `cis.json` entsteht dort und wird danach gelöscht. Ins Repo und in den PR kommen nur Prüfregeln mit kurzem Zitat, denn die CIS-Lizenz verbietet die Weitergabe (ADR 0008). `bsi.json` steht unter CC BY-SA und ist eingecheckt. Weil die Quelle gepinnt ist, liefert jeder Lauf dieselbe Datei.
- **Vorfilter nach Metadaten statt Textsuche:** Er liest `modal_verb` aus dem Statement-Part, `sec_level` = normal-SdT und die Praktik. MUSS und SOLLTE kommen beide durch, weil das BSI alle technischen Anforderungen wie DET.3.1 als SOLLTE führt (ADR 0007).

## Prüfungsbegriffe
- **Reproduzierbarer Build**: Quelle auf Commit und Prüfsumme gepinnt, also gleiche Eingabe und gleiches Ergebnis.
- **Golden-Test**: ein Test gegen echte Daten mit fester Sollzahl (1000/380, 70/45). Er schützt die Regel davor, auf die Zahl hingebogen zu werden.
- **Reine Funktion**: kein I/O, gleiche Eingabe ergibt immer dieselbe Ausgabe. Deshalb sind die Adapter mit kleinen Fakes testbar.

## Merksatz
„Der Code wählt deterministisch aus gepinnten Quellen aus: Erst die Metadaten filtern, dann urteilt das LLM, und CIS-Volltexte verlassen nie den Build-Runner.“

## Abruffragen
1. Wo entsteht `cis.json` im fertigen System, und warum landet sie nie im Repo?
2. Warum lässt der BSI-Vorfilter SOLLTE durch und nicht nur MUSS?
3. Was ist ein Golden-Test, und wovor hat er uns in #4 geschützt?
