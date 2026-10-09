# #1 Prüfkern: Modelle und audit_engine

## Was es tut
`run_audit()` prüft einen Text gegen einen Katalog von Prüfregeln und liefert einen Audit-Report mit einem Befund je Regel. Das LLM schlägt die Befunde vor, der Code prüft sie und ergänzt alles, was er schon weiß. Bei einem CloudFormation-Template setzt der Code N/A selbst, ohne das LLM zu fragen.
`Katalog + Eingabe → N/A durch Code → LLM (Tool submit_audit) → Validator (bei Fehler 1 Retry) → Befunde ergänzen → Gesamtstatus → AuditReport`

## Wo im Code
- [models.py](../../src/govguard/models.py): Pydantic-Verträge; das LLM füllt nur `*Draft`-Modelle (Draft-Pattern).
- [audit_engine.py](../../src/govguard/audit_engine.py): Agent, Validator, `run_audit()`, `overall_status()`.
- [text.py](../../src/govguard/text.py): `contains_quote()` prüft das Zitat, `template_resource_types()` liest das Template.

## Entscheidung und Warum
- **Das LLM bewertet, der Code prüft.** Jeder Beleg muss wörtlich in der Eingabe stehen. Sonst gibt es genau einen Retry, danach bricht das Audit ab (HTTP 502). So bleibt jeder Befund nachweisbar (DSGVO Art. 5 Abs. 2, Rechenschaftspflicht).
- **N/A durch Code:** Kommt der Ressourcentyp einer Regel im Template nicht vor, setzt der Code N/A ohne LLM-Aufruf. Das ist deterministisch und spart Tokens (FinOps).

## Prüfungsbegriffe
- **Grounding**: Eine Aussage zählt nur, wenn sie an der Quelle verankert ist; hier per wörtlichem Zitat.
- **Fail-closed**: Im Zweifel gibt es kein Ergebnis statt eines falschen Ergebnisses.
- **Dependency Injection**: `run_audit()` bekommt das Modell als Parameter; Tests reichen ein `FunctionModel` hinein, ohne AWS.

## Merksatz
„Das Modell darf nur zitieren, nicht behaupten. Was der Code nicht wörtlich in der Eingabe findet, kommt nie in den Report.“

## Abruffragen
1. Was passiert, wenn das LLM einen Beleg liefert, der nicht in der Eingabe steht?
2. Warum fragt GovGuard das LLM bei einer Regel nicht, deren Ressourcentyp im Template fehlt?
3. Wie lässt sich `run_audit()` testen, ohne Bedrock aufzurufen?
