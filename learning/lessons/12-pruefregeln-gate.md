# #12 Prüfregeln formulieren und Gate

## Was es tut
Für jede Anforderung der Auswahlliste schreibt das LLM genau eine Prüfregel: Zitat, Titel, Kriterien für Einhaltung und Verstoß, Empfehlung. Identität und Herkunft (`id`, `source`, `primary_anchor`, Auswahlbegründung, Ressourcentypen) setzt der Code, nie das LLM. Ein Gate prüft den ganzen Katalog, erst dann wird `rules_*.json` geschrieben.
`selection_*.json + Extrakte → formulate_rule (Tool-Choice) → Validator, max. 2 Retries → Code ergänzt Identität → Gate → rules_spec.json / rules_arch.json`

## Wo im Code
- [formulate.py](../../src/kb_build/rules/formulate.py): Prompt, Agent mit Tool `formulate_rule`, Validator, Regel vervollständigen.
- [gates.py](../../src/kb_build/rules/gates.py): `check_rules()` prüft Anker, Zitat, Querverweise und „genau eine Regel je Anforderung“.
- [rules/run.py](../../src/kb_build/rules/run.py): liest die Auswahllisten, schreibt die Kataloge, protokolliert den Qualitätsbericht.

## Entscheidung und Warum
- **Zitat statt Behauptung, sonst Abbruch:** Jede Regel trägt ein wörtliches Zitat aus genau ihrer Anforderung. Fehlt es, bricht der Build ab (fail closed). So ist jede Regel auf den Normtext rückführbar. Das entspricht der Rechenschaftspflicht (DSGVO Art. 5 Abs. 2) und der Nachvollziehbarkeit, die ein BSI-Audit verlangt.
- **Vergleich ohne Leerzeichen:** pypdf zerteilt im SDM-PDF Wörter („Protokollie rung“). `contains_quote()` vergleicht daher ohne Leerzeichen, im Build und zur Laufzeit gleich.
- **`global.` nur im Build (ADR 0012):** Hatte `eu.` keine Kapazität, darf der Build ausdrücklich das globale Profil nutzen. Dort gehen nur öffentliche Normtexte raus, Nutzereingaben bleiben in der EU, es gibt also keinen Drittlandtransfer personenbezogener Daten (DSGVO Art. 44).

## Prüfungsbegriffe
- **Fail closed**: Im Zweifel bricht der Build ab, statt eine fehlerhafte oder fehlende Regel still durchzulassen.
- **Output-Validator**: Er prüft die Antwort des LLM sofort und schickt Fehler per `ModelRetry` zurück; das Modell bekommt eine zweite Chance, bevor das Gate hart abbricht.
- **Primäranker**: die eine Anforderung, aus der eine Regel stammt; der Code setzt ihn aus der Auswahlliste, damit das LLM keine Herkunft erfinden kann.

## Merksatz
„Das LLM formuliert, der Code setzt die Herkunft, und das Gate lässt nur Regeln mit wörtlichem Zitat aus genau ihrer Anforderung durch, sonst bricht der Build ab.“

## Abruffragen
1. Welche Felder einer Prüfregel setzt der Code und nicht das LLM, und warum?
2. Was passiert, wenn das Zitat eines Entwurfs nicht im Text der Anforderung steht: zuerst im Validator, dann im Gate?
3. Warum vergleicht `contains_quote()` ohne Leerzeichen?
