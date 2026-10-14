# 0017 – Beleg per Zeilenverweis

_Ergänzt [ADR 0005](0005-pydantic-ai.md) und [ADR 0016](0016-groq-zur-laufzeit-im-prototyp.md). Umsetzung: #26._

## Kontext

- Bisher schreibt das LLM jeden Beleg als wörtliches Zitat ab. Beim größten Preset (`spec-wohngeld-openapi`, 151 Regeln) hat der Code 52 Belege abgelehnt, weil die Modelle Zitate zusammensetzen oder umformatieren. Ergebnis: fail closed (Messung 14.10.2026, #14).
- Citations der Converse API hängen nur an Text-Blöcken. Mit erzwungenem Tool entsteht kein Text, und Pydantic AI unterstützt Citations nicht (Recherche zu #26). Sie scheiden aus.
- Prototyp vom 14.10.2026 (Branch `prototype/26-beleg-per-verweis`): Mit Zeilenverweis gab es 0 umformulierte Belege und 0 Schema-Retries, mit Bedrock und Groq. Neue Gründe für Retries waren zu große Zeilenbereiche und FAIL ohne Beleg.

## Entscheidung

- Der Code nummeriert die Eingabe zeilenweise (`12| …`). Das LLM liefert je Befund nur `line_start` und `line_end`, der Code schneidet den Beleg aus. Im Report steht weiter `evidence`.
- Der Code prüft den Bereich: Er muss in der Eingabe liegen, darf höchstens 200 Zeilen umfassen (etwa ein Abschnitt), und der Ausschnitt braucht mindestens 15 Zeichen. Sonst gibt es einen Retry.
- PASS ohne Bereich löst einen Retry aus. FAIL ohne Bereich stuft der Code ohne Retry auf WARN herab. Damit setzt der Code die Prompt-Regel „Was fehlt, ist WARN“ durch.
- Das Schema ist strikt und statisch: keine Aufzählungen oder Grenzen je Eingabe, alle Felder in `required`. Bedrock nutzt `ToolOutput(..., strict=True)` mit erzwungenem Tool (ADR 0005), Groq `NativeOutput` (Nachtrag in ADR 0016).

## Konsequenzen

- Jeder Beleg ist per Konstruktion wörtlich. Das Modell kann keine Zitate mehr erfinden, nur noch auf falsche Zeilen zeigen.
- Ein Beleg kann grob sein, nämlich bis zu einem ganzen Abschnitt. Die Eingabe wächst durch die Nummern um ca. 17 %, der Output sinkt nur um ca. 20 %, weil vor allem Begründung und Empfehlung den Output ausmachen. Die 29-s-Grenze löst das nicht (Plan B aus ADR 0011).
- Die Herabstufung muss im Report sichtbar sein (#27). Falsche FAILs *mit* Beleg fängt sie nicht ab (#28).
- Der Freitext-Vorlauf (`submit_inventory`) kann denselben Weg nutzen. Das ist nur eingeschätzt, nicht gemessen.

## Nachtrag 14.10.2026 – zu großer Bereich bei WARN/FAIL

- Messung nach dem Umbau: Bei 11 Retries nannte Haiku das ganze Dokument als Bereich (z. B. `1-1720`), meist bei WARN/FAIL. Ein Paket blieb ungültig, also fail closed.
- Entscheidung: Bei WARN und FAIL zählt ein Bereich über 200 Zeilen als „kein Bereich“. WARN bleibt WARN ohne Beleg, FAIL wird zu WARN, beides ohne Retry. Nur PASS mit zu großem Bereich bekommt einen Retry. Ungültige oder zu kurze Bereiche lösen weiter bei jedem Status einen Retry aus, denn dort zeigt das Modell auf etwas, das es nicht gibt.
- Der Output-Validator bereinigt die Antwort zuerst und prüft sie danach. Was der Code selbst richten kann, kostet keinen Retry.

## Fachgespräch-Satz

„Das Modell zeigt nur noch auf Zeilen, den Beleg schneidet mein Code aus. So ist jedes Zitat per Konstruktion wörtlich, und was das Modell nicht belegen kann, wird höchstens WARN, nie FAIL.“
