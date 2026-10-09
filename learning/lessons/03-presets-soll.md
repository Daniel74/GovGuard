# #3 4 Presets mit Soll-Ergebnis

## Was es tut
Vier fiktive Eingaben (OpenAPI, Freitext, CloudFormation) mit einem Soll, das ein Mensch festlegt: Gesamtstatus, Pflicht-Befunde über Primäranker und bei Preset 1 der Archetyp. Ein Anker zählt nur, wenn Bauplan und eine blinde Zweitprüfung durch ein anderes Modell (Gemini) übereinstimmen.
`Bauplan (Claude) → Eingabe → Gemini blind → Abgleich → Mensch legt Soll fest → preset.json → Preset-Gate (#8)`

## Wo im Code
- [models.py](../../src/govguard/models.py): `Preset`, `Expected`, `RequiredFinding` (nur PASS/FAIL; Archetyp nur bei Spec ohne FAIL).
- [data/presets/](../../data/presets/): je Ordner eine Eingabe + `preset.json`.
- [test_presets.py](../../tests/test_presets.py): ≤ 100.000 Zeichen, höchstens 4 gesetzte Plätze je Audit-Art.

## Entscheidung und Warum
- **Soll vom Menschen mit Vier-Augen-Abgleich statt aus einem früheren Lauf:** Sonst prüft das System sich selbst, und ein Fehler wird zum Maßstab. Bei Abweichung wird gestrichen, nicht diskutiert (Nachvollziehbarkeit wie in BSI-Audits).
- **Pflicht-Befunde nie WARN:** WARN ist Ermessen und würde das Gate flackern lassen; PASS und FAIL sind mit einem wörtlichen Zitat belegbar.
- **Archetypen als End-to-End-Kette ohne Portal (ADR 0009):** CloudFront hat keine Preisklasse nur für die EU, TLS endet womöglich im Drittland (DSGVO Kap. V).

## Prüfungsbegriffe
- **Testorakel**: die unabhängige Quelle, die sagt, was richtig ist – hier das Soll des Menschen.
- **Zirkulärer Test**: ein Test, dessen Erwartung aus dem geprüften System selbst stammt; er beweist nichts.
- **Gesetzter Platz**: ein Pflichtanker steht immer im Bounded Catalog, höchstens 4 je Audit-Art.

## Merksatz
„Das Soll unserer Presets kommt von einem Menschen und ist von einem zweiten Modell gegengeprüft – kein Test misst GovGuard an GovGuard.“

## Abruffragen
1. Warum darf das Soll nicht aus einem früheren Lauf von GovGuard stammen, und wie heißt so ein Test?
2. Wann wird ein Anker aus dem Bauplan Pflicht-Befund, und was passiert bei einer Abweichung?
3. Warum ist ein Pflicht-Befund nie WARN?
