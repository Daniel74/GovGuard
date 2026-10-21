# #60 Bedingungs-Vorlauf im Spec-Audit: N/A nur mit Beleg

## Was es tut
Manche Prüfregeln gelten nur unter einer Bedingung, z. B. die KI-VO nur für ein KI-System. Ein LLM-Aufruf vor den Prüfpaketen nennt je Bedingung Zeilen, die sie belegen, und Zeilen, die sie für das ganze Vorhaben verneinen; den Wert setzt der Code.
`Spezifikation → Vorlauf (Belegzeilen) → Code: yes/no/unstated → bei no: N/A mit Beleg, Rest → Prüfpakete → Report`

## Wo im Code
- [conditions.json](../../data/input/conditions.json): die 7 Bedingungen mit Kriterien und Zuordnung zu Prüfregeln
- [calls/conditions.py](../../src/govguard/calls/conditions.py): Prompt und LLM-Aufruf, ein Retry
- [checks/conditions.py](../../src/govguard/checks/conditions.py): Wert aus Belegen, Widerspruch, N/A-Befunde (rein, ohne I/O)

## Entscheidung und Warum
- **Nur ein ausdrückliches Nein macht N/A.** Schweigt die Spezifikation, bleibt die Bedingung `unstated` und ihre Prüfregeln gehen ans Modell. Eine Spezifikation ist eine offene Welt (ADR 0020): Was sie nicht erwähnt, kann trotzdem zutreffen. Eine Prüfregel fällt also nur mit Beleg weg, sonst verschwände ein DSGVO-Befund unbemerkt.
- **Im Zweifel der strengere Wert.** Belegen und verneinen verschiedene Zeilen dieselbe Bedingung, gilt `yes` mit dem Hinweis „Widerspruch“. Fällt der Vorlauf aus, sind alle Bedingungen `unstated`, ohne fail closed. Der Vorlauf kann nur Regeln wegnehmen, nie ein FAIL erzeugen. FinOps: Verneinte Regeln gehen nicht ans Modell und sparen Tokens.

## Fachbegriffe
- **Offene Welt**: Was die Eingabe nicht sagt, ist offen, nicht verneint; Schweigen ergibt eine Lücke, kein N/A.
- **Bedingungs-Vorlauf**: Ein LLM-Aufruf liefert nur Belegzeilen, und der Code entscheidet daraus den Wert (Trennung von Urteil und Regel).
- **Strengerer Wert**: Bei Widerspruch gilt der Wert, der mehr prüft, denn ein verborgener Befund ist teurer als eine Lücke zu viel.

## Merksatz
Eine Prüfregel fällt nur mit Beleg weg: Nur ein ausdrückliches Nein für das ganze Vorhaben macht sie nicht anwendbar, Schweigen bleibt eine offene Frage.

## Abruffragen
1. Warum wird eine Bedingung nicht „nein“, wenn die Spezifikation zu ihr schweigt?
2. Was gilt, wenn eine Zeile die Bedingung belegt und eine andere sie verneint, und warum?
3. Warum bricht das Audit nicht ab, wenn der Bedingungs-Vorlauf ausfällt?
