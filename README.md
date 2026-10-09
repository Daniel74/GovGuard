# GovGuard

## Wissensbasis bauen (`kb_build`)

Build-Werkzeug, läuft lokal: `uv run python -m kb_build <befehl>`. Hintergrund: [ARCHITECTURE](docs/ARCHITECTURE.md) 1.

| Befehl | Was passiert | Ergebnis |
|---|---|---|
| `extract` (Standard) | Lädt die Quellen (SHA-256 geprüft) und zerlegt sie in Anforderungen. Kein LLM. | `data/extracted/*.json` |
| `select` | Das LLM klassifiziert „prüfbar ja/nein“, der Code wählt aus (Relevanz, gesetzte Plätze, Ranking). | `data/knowledge_base/selection_<arch\|spec>.json`, dazu `verdicts_*.json` (Urteil je Anforderung: gesetzt, gewählt, nicht prüfbar, nicht relevant, über der Obergrenze; [SPEC](docs/SPEC.md)) |

- **Modell:** Standard ist Bedrock (`eu-central-1`, Profil `eu.`), mit `AWS_PROFILE=…` und gültigem Login. `--provider groq` ist ein befristeter Ausweg ([ADR 0010](docs/adr/0010-groq-build-fallback.md)): `export GROQ_API_KEY=…`, Modell optional über `GROQ_MODEL`.
- **Nur eine Audit-Art:** `select --audit-type spec` oder `architecture` rechnet nur diese Liste neu (ca. 100 bzw. 425 Aufrufe nacheinander).
- **Fortschritt:** pro Anforderung eine Zeile mit Uhrzeit. Scheitert ein gesetzter Anker (Preset), bricht der Lauf in den ersten Sekunden ab.
- **Tests:** `uv run pytest` und `uv run ruff check` brauchen weder AWS noch Groq.
- **Echte Ressourcentypen:** `data/cfn_resource_types.json` (1926 Typen) stammt aus `aws cloudformation list-types --visibility PUBLIC --type RESOURCE --filters Category=AWS_TYPES --query 'TypeSummaries[].TypeName'`. Das LLM darf keine anderen Typen nennen; sonst gibt es einen Retry.
