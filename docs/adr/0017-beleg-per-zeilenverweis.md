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
- Bei WARN, FAIL und N/A zählt ein unbrauchbarer Bereich als „kein Bereich“. FAIL ohne Bereich wird WARN. Beides geschieht ohne Retry; so setzt der Code die Prompt-Regel „Was fehlt, ist WARN“ durch (seit ADR 0020 nur noch im Spec-Audit).
- Doppelte Befunde zu einer Prüfregel mit gleichem Status fasst der Code zum ersten zusammen; widersprechen sie sich, gibt es einen Retry (seit Nachtrag #32: der schwerste Status gilt). Der Validator bereinigt immer zuerst und prüft danach.
- Das Schema ist strikt und statisch: keine Aufzählungen oder Grenzen je Eingabe, alle Felder in `required`. Bedrock nutzt `ToolOutput(..., strict=True)` mit erzwungenem Tool (ADR 0005), Groq `NativeOutput` (Nachtrag in ADR 0016).

## Konsequenzen

- Jeder Beleg ist per Konstruktion wörtlich, auch mit Windows-Zeilenenden. Das Modell kann keine Zitate mehr erfinden, nur noch auf falsche Zeilen zeigen.
- Fail closed gibt es für Belege nicht mehr, nur bei fehlenden oder unbekannten Befunden, N/A trotz Inventar und Fehlern der API (seit Nachtrag #32).
- **WARN hat zwei Bedeutungen:** aus der Eingabe nicht entscheidbar, oder vom Code herabgestuft. Der Report unterscheidet beides je Befund mit `downgraded_from` und `corrections` (#27). Falsche FAILs *mit* Beleg fängt das nicht ab. Für das Spec-Audit begrenzt sie seit ADR 0020 eine Prompt-Regel: FAIL gibt es nur, wenn die Belegzeilen den Verstoß festlegen.
- Ein Beleg kann grob sein, bis zu einem Abschnitt. Die Grenze zählt Zeilen, nicht Zeichen: Bei Eingaben ohne Umbrüche (minifiziertes JSON) ist `1-1` die ganze Eingabe. Die Presets sind formatiert, deshalb bleibt das eine bekannte Grenze.
- Die Nummern machen die Eingabe ca. 17 % größer, der Output sinkt um ca. 10–20 %, weil vor allem Begründung und Empfehlung ihn treiben.

## Nachtrag (#32): Reparatur aus der Wissensbasis statt Retry

- **Kontext:** Mit Bedrock brach `arch-antragseingang-fehlerhaft` 3× fail closed ab: Der Retry „N/A ist verboten“ führte zu WARN oder FAIL ohne Empfehlung. `spec-meldeportal-gesundheit` scheiterte an wechselnden Gründen, z. B. widersprüchlichen Doppelbefunden oder einer fehlenden Empfehlung (#28, #29). Das Modell korrigiert im Retry das genannte Feld und verletzt ein anderes.
- **Entscheidung:** Was der Code aus der Wissensbasis reparieren kann, braucht keinen Retry (`repairs.py`):
  - Fehlt die Empfehlung bei WARN oder FAIL, setzt der Code die `recommendation` der Prüfregel ein, bei WARN mit „Falls nicht erfüllt: “.
  - Widersprechen sich Doppelbefunde, gilt der schwerste Status (DESIGN 2.1).
  - Beide Fälle bekommen eine Korrekturzeile. Wie eine Herabstufung zählt eine Reparatur nur aus dem letzten Versuch.
- **Konsequenzen:** Fail closed bleibt das Sicherheitsnetz, z. B. wenn auch die Prüfregel keine Empfehlung hat. `downgrades` zählt weiter nur Statusänderungen auf WARN, für Reparaturen gibt es keinen Zähler. `max_tokens` und der Retry des ganzen Pakets bleiben. Die Bedrock-Messung zeigt, ob ein abgeschnittener Retry dasselbe Muster ist.

## Fachgespräch-Satz

„Das Modell zeigt nur noch auf Zeilen, den Beleg schneidet mein Code aus. So ist jedes Zitat per Konstruktion wörtlich, und was das Modell nicht belegen kann, wird höchstens WARN, nie PASS oder FAIL.“
