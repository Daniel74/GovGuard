# 0005 – Pydantic AI für strukturierte LLM-Ausgaben

## Kontext

Alle vier LLM-Aufrufe (`classify_requirement`, `formulate_rule`, `submit_audit`, `select_archetype`) liefern strukturierte Daten über ein erzwungenes Tool. Mit boto3 direkt müssten wir jedes Mal das Tool-Schema erzeugen, die Antwort herauslösen, validieren und den Retry mit Fehlermeldung selbst schreiben. Pydantic AI erledigt genau das als Bibliothek.

## Entscheidung

- Jeder LLM-Aufruf ist ein Pydantic-AI-`Agent` mit einem Draft-Modell als `output_type` (z. B. `AuditResponse`); das Framework erzeugt daraus das Tool-Schema.
- Fachliche Prüfungen (genau ein Befund je Prüfregel, `contains_quote()`) laufen als `@agent.output_validator` und lösen bei Fehlern `ModelRetry` aus; Katalog und Eingabe kommen über `deps_type`.
- `retries=1` wegen des 29-s-Timeouts; scheitert auch der zweite Versuch, gilt Fail closed (HTTP 502).
- Nur `aws_services.py` baut das Bedrock-Modell (boto3, Profil `eu.`); die Prüflogik bekommt es übergeben.

## Konsequenzen

- Eigener Code für Schema-Mapping, Parsing und Retry entfällt; die Validierungskette bleibt unser Code.
- Tests nutzen `TestModel` bzw. `FunctionModel` von Pydantic AI; das eigene Protokoll `LlmCall` entfällt.
- Neue Abhängigkeit `pydantic-ai-slim[bedrock]` (schlank für das Lambda-Paket), Version fixiert.

## Fachgespräch-Satz

„Pydantic AI nimmt mir den Retry-Boilerplate ab, nicht die Verantwortung: Ob jede Prüfregel einen Befund hat und jeder Beleg wörtlich in der Eingabe steht, prüft weiterhin mein Code – und nach einem Fehlversuch antwortet das System ehrlich mit 502.“
