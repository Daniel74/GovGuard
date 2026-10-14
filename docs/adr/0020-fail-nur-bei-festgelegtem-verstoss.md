# 0020 – FAIL nur bei festgelegtem Verstoß

_Ergänzt [ADR 0017](0017-beleg-per-zeilenverweis.md). Umsetzung und Messungen: #28._

## Kontext

- Seit #26 wird ein FAIL ohne Beleg WARN. Trotzdem verfehlt `spec-wohngeld-openapi` sein `expected` (WARN): Beide Modelle vergeben FAILs *mit* Beleg, die keinen Verstoß zeigen. Ein Beispiel ist Bedrock zu Art. 12: Es zitiert den Abschnitt „Rechte der betroffenen Personen“ und bemängelt fehlende Prozesse. Groq vergibt ca. neunmal so viele FAILs wie Bedrock (Messung 14.10.2026).
- Ob ein Beleg einen Verstoß zeigt, ist eine Bedeutungsfrage. Ein Code-Gate kann sie nicht entscheiden.
- Bei der Architektur gilt das Gegenteil: Ein Template ist ein Bauplan. Fehlt eine Einstellung, gilt der Standardwert, und das ist oft der Verstoß.

## Entscheidung

- Nur im Spec-Audit gilt diese Prompt-Regel: FAIL gibt es nur, wenn die Belegzeilen einen Verstoß ausdrücklich festlegen, also `violation_if` erfüllen. Fehlt etwas oder ist es vage, ist der Befund WARN. Bei FAIL nennt `rationale` diese Festlegung.
- Die gemeinsame WARN-Zeile heißt nur noch „Aus der Eingabe nicht entscheidbar“. Der Teil „was fehlt, ist WARN“ fällt weg, weil er für Templates falsch ist.
- Audit und Inventar-Vorlauf laufen mit `temperature: 0`. So hängt die Schwankung zwischen zwei Läufen weniger am Zufall des Modells.
- Es gibt kein Gate und kein neues Feld. Bleibt das Ziel rot, ist Anlauf 2 ein Feld für das erfüllte Kriterium. Danach käme der Umbau der Wissensbasis als eigenes Ticket.

## Konsequenzen

- Die Regel steht nur im Prompt. Ein falsches FAIL mit Beleg bleibt möglich und fällt nur in der Messung gegen `expected` auf.
- Gegenproben bleiben Pflicht: Echte Verstöße wie Art. 9 in `spec-meldeportal-gesundheit` müssen FAIL bleiben.
- `temperature: 0` macht Läufe nicht identisch. Gemessen wird die Zahl der Prüfregeln, deren Status sich zwischen zwei Läufen ändert.

## Fachgespräch-Satz

„Im Spec-Audit heißt FAIL, dass die Spezifikation den Verstoß festlegt. Was sie offenlässt, ist Prüfbedarf, also WARN. Im Template ist es umgekehrt, denn dort bedeutet eine fehlende Einstellung den unsicheren Standardwert.“
