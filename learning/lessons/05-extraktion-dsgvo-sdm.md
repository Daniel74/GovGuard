# #5 Extraktion und Vorfilter DSGVO/SDM

## Was es tut
`python -m kb_build` zerlegt die DSGVO (Formex-XML aus CELLAR) in 99 Artikel und die drei SDM-Bausteine (PDF) in 147 Maßnahmen. Der Vorfilter markiert Kandidaten: DSGVO Kapitel II–V (46 Artikel), SDM Ebenen Daten und Systeme (55 Maßnahmen).
`sources.json → source_fetch (SHA-256) → read_cached → extract() → prefilter() → merge_sources → dsgvo.json, sdm.json`

## Wo im Code
- [dsgvo.py](../../src/kb_build/sources/dsgvo.py): Kapitel aus `DIVISION`, Titel aus `STI.ART`, `fine_tier` als Konstante nach Art. 83.
- [sdm.py](../../src/kb_build/sources/sdm.py): liest nur die Maßnahmentabelle; eine Zeile endet an der Spalte PDCA/Gültigkeit.
- [extracted_models.py](../../src/kb_build/extracted_models.py): `merge_sources` macht aus drei PDFs eine `sdm.json`.

## Entscheidung und Warum
- **Tabelle statt Fließtext:** Im Fließtext steht `(M60.D01)` nur als Verweis hinter einem Satz. Nur die Tabelle verbindet ID und Maßnahme eindeutig. Das ist wichtig, weil das Gate jedes `source_quote` wörtlich gegen diesen Text prüft (DSGVO-Rechenschaftspflicht: Zitat statt Behauptung).
- **Protokollieren (M43) fehlt bewusst:** Der Baustein hat ein eigenes ID-Schema (`M43.21.04`), keine Ebenen D/S und durchgestrichene ungültige Maßnahmen. Er bräuchte einen eigenen Parser (FinOps: Aufwand im Zeitbudget). Protokollierung prüft trotzdem das Architektur-Audit über BSI DET und CIS Kapitel 4.

## Prüfungsbegriffe
- **Ebene D/S/P**: SDM-Einteilung in Daten, Systeme und Prozesse. P ist organisatorisch (z. B. Löschkonzept) und fällt im Vorfilter heraus.
- **Beweisgrundlage**: Das Extrakt ist der Originaltext der Quelle. Kein LLM korrigiert ihn, sonst beweist ein Zitat nichts mehr.
- **Golden-Test mit Beispieltext**: Er prüft feste Zahlen (147/55) **und** einen erwarteten Text. Nur Zahlen hätten Junies falschen Parser nicht erkannt.

## Merksatz
„Der Code liest jede Anforderung genau dort, wo die Quelle ID und Text eindeutig verbindet. Das LLM urteilt später nur über diesen Originaltext.“

## Abruffragen
1. Warum liest der SDM-Adapter nur die Maßnahmentabelle und nicht den Fließtext?
2. Warum fehlt der Baustein Protokollieren (M43), und wo wird Protokollierung trotzdem geprüft?
3. Wofür stehen D, S und P, und welche Ebenen lässt der Vorfilter durch?
