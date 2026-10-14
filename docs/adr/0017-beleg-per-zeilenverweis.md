# 0017 – Beleg per Zeilenverweis

_Ergänzt [ADR 0005](0005-pydantic-ai.md) und [ADR 0016](0016-groq-zur-laufzeit-im-prototyp.md). Umsetzung und Messungen: #26._

## Kontext

- Bisher schreibt das LLM jeden Beleg als wörtliches Zitat ab. Beim größten Preset (`spec-wohngeld-openapi`, 151 Regeln) hat der Code 52 Belege abgelehnt, weil die Modelle Zitate zusammensetzen oder umformatieren. Ergebnis: fail closed (Messung 14.10.2026, #14).
- Citations der Converse API hängen nur an Text-Blöcken. Mit erzwungenem Tool entsteht kein Text, und Pydantic AI unterstützt Citations nicht (Recherche zu #26). Sie scheiden aus.
- Prototyp und vier Messungen vom 14.10.2026 (#26): Mit Zeilenverweis gibt es 0 umformulierte Belege und 0 Schema-Retries. Die neuen Fehler: zu große Bereiche (oft das ganze Dokument), umgedrehte Bereiche, FAIL oder PASS ohne Bereich, doppelte Befunde.

## Entscheidung

- Der Code nummeriert die Eingabe zeilenweise (`12| …`). Das LLM liefert je Befund nur `line_start` und `line_end`, der Code schneidet den Beleg aus. Im Report steht weiter `evidence`.
- Ein Bereich ist brauchbar, wenn er in der Eingabe liegt, höchstens 200 Zeilen umfasst (etwa ein Abschnitt) und der Ausschnitt mindestens 15 Zeichen hat.
- **Nur PASS braucht einen brauchbaren Bereich.** Fehlt er, gibt es einen Retry. Bleibt PASS auch im letzten Versuch (`ctx.last_attempt`) unbelegt, wird er WARN mit fester Empfehlung („Einhaltung selbst prüfen …“).
- Bei WARN, FAIL und N/A zählt ein unbrauchbarer Bereich als „kein Bereich“. FAIL ohne Bereich wird WARN. Beides geschieht ohne Retry; so setzt der Code die Prompt-Regel „Was fehlt, ist WARN“ durch.
- Doppelte Befunde zu einer Prüfregel mit gleichem Status fasst der Code zum ersten zusammen; widersprechen sie sich, gibt es einen Retry. Der Validator bereinigt immer zuerst und prüft danach.
- Das Schema ist strikt und statisch: keine Aufzählungen oder Grenzen je Eingabe, alle Felder in `required`. Bedrock nutzt `ToolOutput(..., strict=True)` mit erzwungenem Tool (ADR 0005), Groq `NativeOutput` (Nachtrag in ADR 0016).

## Konsequenzen

- Jeder Beleg ist per Konstruktion wörtlich, auch mit Windows-Zeilenenden. Das Modell kann keine Zitate mehr erfinden, nur noch auf falsche Zeilen zeigen.
- Fail closed gibt es für Belege nicht mehr, nur bei fehlenden, unbekannten oder widersprüchlichen Befunden, fehlender Empfehlung, N/A trotz Inventar und Fehlern der API.
- **WARN hat zwei Bedeutungen:** aus der Eingabe nicht entscheidbar, oder vom Code herabgestuft. Der Report muss beides unterscheiden (#27). Falsche FAILs *mit* Beleg fängt das nicht ab (#28).
- Ein Beleg kann grob sein, bis zu einem Abschnitt. Die Grenze zählt Zeilen, nicht Zeichen: Bei Eingaben ohne Umbrüche (minifiziertes JSON) ist `1-1` die ganze Eingabe. Die Presets sind formatiert, deshalb bleibt das eine bekannte Grenze.
- Die Nummern machen die Eingabe ca. 17 % größer, der Output sinkt um ca. 10–20 %, weil vor allem Begründung und Empfehlung ihn treiben.

## Fachgespräch-Satz

„Das Modell zeigt nur noch auf Zeilen, den Beleg schneidet mein Code aus. So ist jedes Zitat per Konstruktion wörtlich, und was das Modell nicht belegen kann, wird höchstens WARN, nie PASS oder FAIL.“
