# 0022 – Pflichtanker übersteuern die Ebene

_Ergänzt [ADR 0011](0011-vollstaendiger-katalog.md) (Preset-Anker im Gate) und die Ebene aus #18._

## Kontext

- Ein Pflichtanker ist der Primäranker einer Prüfregel, deren Befund ein Preset im Soll-Ergebnis festlegt. Das Gate bricht den Build ab, wenn er nicht aufgenommen ist.
- Das LLM urteilt die Ebene (`scope_level`) nicht stabil: In der Probe vom 14.10.2026 (Groq, 5 Läufe) kippte CIS 3.1.4 in 1 von 5 Läufen auf `account`. Das Gate brach ab, und bei #19 half nur Nachwürfeln von Hand.

## Entscheidung

- **Der Code setzt die Ebene eines Pflichtankers auf `template`**, wenn das LLM `account`, `people` oder `provider` sagt. Ein Preset belegt, dass der Befund am Template erkennbar ist.
- **Sichtbar statt still:** Die Begründung im Auswahlprotokoll (und in `selection_*.json`) bekommt den festen Satz „Pflichtanker eines Presets: …“ angehängt.
- **Nur die Ebene.** `testable`, die Ressourcentypen und jedes Audit-Urteil bleiben beim LLM. `not_testable`, Typen außerhalb des Prüfumfangs, Vorfilter und `llm_error` bleiben harter Abbruch, sonst prüft das Gate nichts mehr.

## Konsequenzen

- Der Judgement-Cache bleibt gültig: Die Übersteuerung greift nach dem Cache, die Prompt-Version ändert sich nicht.
- Der Satz fließt über die Begründung auch in den Prompt der Regelformulierung ein.
- Schwäche: Ein Mensch legt die Pflichtanker fest, der Test bestätigt sie danach. Das belegt stabile Mechanik, nicht die Güte des Katalogs; das 5. Preset mit fremder Architektur (ADR 0011) sichert das ab.

## Fachgespräch-Satz

„Ein Preset darf die Ebene einer Anforderung festlegen, damit der Katalog reproduzierbar bleibt, aber nie das Ergebnis eines Audits.“
