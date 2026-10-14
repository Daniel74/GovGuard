# 0020 – FAIL nur bei festgelegtem Verstoß

_Ergänzt [ADR 0017](0017-beleg-per-zeilenverweis.md). Umsetzung und Messungen: #28, Umbau des Katalogs: #29._

## Kontext

- Seit #26 wird ein FAIL ohne Beleg WARN. Trotzdem verfehlt `spec-wohngeld-openapi` sein `expected` (WARN): Beide Modelle vergeben FAILs *mit* Beleg, die keinen Verstoß zeigen, z. B. Bedrock zu Art. 12 mit dem Abschnitt „Rechte der betroffenen Personen“. Ob ein Beleg einen Verstoß zeigt, ist eine Bedeutungsfrage, die kein Code-Gate entscheidet.
- Bei der Architektur gilt das Gegenteil: Ein Template ist ein Bauplan. Fehlt eine Einstellung, gilt der Standardwert, und das ist oft der Verstoß.
- 130 von 151 `violation_if` im Spec-Katalog beschreiben ein Fehlen, z. B. „Die Spezifikation enthält kein Verfahren …“. Auch mit der Regel der offenen Welt vergibt Groq noch 50 FAILs, fast alle mit „keine/fehlt“ (Messung Anlauf 1b, #28).

## Entscheidung

- Eine Spezifikation ist eine **offene Welt**: Was sie nicht erwähnt, kann anderswo geregelt sein. Ein Template ist eine **geschlossene Welt**: Was fehlt, ist der Standardwert. Welche Welt gilt, entscheidet der Code über die Audit-Art, nicht das Modell.
- Nur im Spec-Audit gilt die Prompt-Regel (`SPEC_FAIL_RULE`): Beschreibt `violation_if` ein Fehlen, belegt fehlender Text nur „nicht beschrieben“, also WARN. FAIL gibt es nur, wenn die Belegzeilen etwas festlegen, das der Prüfregel widerspricht. `rationale` nennt diese Festlegung.
- Die gemeinsame WARN-Zeile heißt nur noch „Aus der Eingabe nicht entscheidbar“, weil „was fehlt, ist WARN“ für Templates falsch ist. Audit und Inventar-Vorlauf laufen mit `temperature: 0` und höchstens 8.000 Output-Tokens je Aufruf.
- Kein Gate und kein neues Feld: Ein Feld für das erfüllte Kriterium hilft nicht, solange das Kriterium selbst ein Fehlen beschreibt. Deshalb formuliert #29 `violation_if` im Spec-Katalog als Festlegung um.

## Konsequenzen

- Die Regel steht nur im Prompt, auch die Pflicht für `rationale`. Ein falsches FAIL mit Beleg bleibt möglich und fällt nur in der Messung gegen `expected` auf. Allein reicht die Regel nicht, erst mit #29 kann `expected` grün werden.
- Gemessen werden in #29 auch die Gegenproben (Art. 9 bleibt FAIL) und die Schwankung: die Zahl der Prüfregeln, deren Status sich zwischen zwei Läufen ändert. `temperature: 0` macht Läufe nicht identisch.
- Ein Bedrock-Retry lief in einer Schleife bis 64.000 Output-Tokens (204 s). Mit der Obergrenze bricht eine Schleife nach ca. 25 s ab, normal sind unter 4.000 Tokens. Der abgeschnittene Tool-Call beendet das Audit sofort fail closed, ohne Retry, aber innerhalb der 180 s (ADR 0018).
- Offen: Eine Architektur als Freitext ist eigentlich auch offene Welt, wird aber heute wie ein Template geprüft.

## Nachtrag (#29)

- Der Formulier-Prompt fürs Spec-Audit verlangt als `violation_if` eine Festlegung, auch einen erklärten Verzicht oder Aufschub. Im Build prüft ein **LLM-Prüfer** (`judge_violation`) jedes Spec-`violation_if`. Beschreibt es ein Fehlen, geht seine Begründung als Retry an den Formulierer. Scheitert der Prüfer, bricht der Build ab (fail closed).
- Verworfen: eine Sperrliste („kein“, „fehlt“, „vage“). Sie schließt aus Wörtern auf die Bedeutung. „legt nicht fest“ und „legt fest, dass … nicht“ unterscheiden sich nur in der Wortstellung, und jede neue Umschreibung bräuchte einen neuen Eintrag.
- Konsequenz: Ein LLM prüft ein LLM, das Urteil ist nicht reproduzierbar. Deshalb läuft der Prüfer nur im Build, die Zeile `spec quality judge` zählt seine Treffer, und den Beweis liefert weiter die Messung gegen `expected`. Er kostet einen Request je gültigen Entwurf, im ersten Lauf 245 von 619 Requests des Spec-Builds.

## Fachgespräch-Satz

„Eine Spezifikation ist eine offene Welt: Was sie nicht erwähnt, ist Prüfbedarf, also WARN. Ein Template ist eine geschlossene Welt, dort bedeutet eine fehlende Einstellung den unsicheren Standardwert, also FAIL.“
