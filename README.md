# GovGuard

## Wissensbasis bauen (`kb_build`)

Build-Werkzeug, läuft lokal: `uv run python -m kb_build <befehl>`. Hintergrund: [ARCHITECTURE](docs/ARCHITECTURE.md) 1.

| Befehl | Was passiert | Ergebnis |
|---|---|---|
| `extract` (Standard) | Lädt die Quellen (SHA-256 geprüft) und zerlegt sie in Anforderungen. Kein LLM. | `data/intermediate/extracted/*.json` |
| `select` | Das LLM klassifiziert „prüfbar ja/nein“, der Code wählt aus (Relevanz, gesetzte Plätze, Ranking). | `data/intermediate/selection_<arch\|spec>.json`, dazu `verdicts_*.json` (Urteil je Anforderung: gesetzt, gewählt, nicht prüfbar, nicht relevant, über der Obergrenze; [SPEC](docs/SPEC.md)) |

- **Modell:** Standard im Build ist Groq ([ADR 0014](docs/adr/0014-groq-standard-im-build.md)): `export GROQ_API_KEY=…`, Modell optional über `GROQ_MODEL`. Fehlt der Schlüssel, bricht der Lauf ab, ohne auf Bedrock auszuweichen. Bedrock nur ausdrücklich mit `--provider bedrock` (`eu-central-1`, Profil `eu.`, `AWS_PROFILE=…` und gültigem Login) oder `--provider bedrock-global` ([ADR 0012](docs/adr/0012-globales-profil-im-build.md)).
- **Nur eine Audit-Art:** `select --audit-type spec` oder `architecture` rechnet nur diese Liste neu (ca. 100 bzw. 425 Aufrufe nacheinander).
- **Fortschritt:** pro Anforderung eine Zeile mit Uhrzeit. Scheitert ein gesetzter Anker (Preset), bricht der Lauf in den ersten Sekunden ab.
- **Tests:** `uv run pytest` und `uv run ruff check` brauchen weder AWS noch Groq.
- **Echte Ressourcentypen:** `data/input/cfn_resource_types.json` (1926 Typen) stammt aus `aws cloudformation list-types --visibility PUBLIC --type RESOURCE --filters Category=AWS_TYPES --query 'TypeSummaries[].TypeName'`. Das LLM darf keine anderen Typen nennen; sonst gibt es einen Retry.
- **Echte Eigenschaften:** `data/input/cfn_properties.json` hält je Typ des Prüfumfangs alle Eigenschaftspfade (z. B. `RedirectConfig.Protocol`). Neu ziehen: Schemas per `for t in $(jq -r '.[][]' data/input/scope.json); do aws cloudformation describe-type --type RESOURCE --type-name $t --query Schema --output text > schemas/${t//::/-}.json; done` in einen Ordner `schemas/` laden, dann `uv run python -m kb_build cfn-properties` (Ordner per `--schema-dir`). Nennt eine Prüfregel eine Eigenschaft, die keiner ihrer Typen kennt, oder einen Typ außerhalb von `scope.json`, gibt es einen Retry; der Qualitätsbericht zählt `unknown_properties`.

## Audit lokal (`govguard.cli`)

- `uv run python -m govguard.cli spec <datei>` bzw. `arch <datei>`; Standard ist Groq (`GROQ_API_KEY`, nur fiktive Daten). `--provider bedrock` nimmt Bedrock `eu.`, den einzigen Weg für echte Daten ([ADR 0001](docs/adr/0001-eu-inferenzprofil.md)).
- Exit-Codes: 0 Report auf stdout, 1 Eingabe über 100.000 Zeichen (vor jedem LLM-Aufruf), 2 fail closed, 3 `GROQ_API_KEY` fehlt.

## Demo-UI: Screenshot-Regression (#40)

- **Einmalig Browser installieren:** `uv run playwright install chromium`. Normales `uv run pytest` braucht ihn nicht und überspringt den Marker `visual`.
- **Prüfen:** `uv run pytest -m visual` startet `streamlit_app.py` lokal und fotografiert 4 Ansichten bei 1440 px. Es vergleicht sie mit den Referenzbildern in `tests/visual/` (erlaubt sind höchstens 100 geänderte Pixel). In `tests/visual/output/` landen das Foto, bei Abweichung `<ansicht>-diff.png` (Änderungen rot) und `<ansicht>-design.png` („Design | Streamlit“, Design aus `tests/visual/design/`).
- **Freigeben:** War die Änderung gewollt, schreibt `uv run pytest -m visual --update-snapshots` die Referenzbilder neu; danach ansehen und committen. Die Referenzbilder stammen von macOS, auf einem anderen System rendern die Schriften anders.

## Bekannte Grenzen

- **Groq im Audit:** Groq (`openai/gpt-oss-120b`) schwankt stärker als Bedrock. Im Spec-Audit änderten zwischen zwei Läufen 42 von 151 Prüfregeln ihren Status, bei Bedrock 19 (#29). Der FAIL-Prüfer fängt FAILs ohne festgelegten Verstoß ab (#31), PASS und WARN schwanken weiter. Trotzdem ist Groq Standard, denn Bedrock ist für die Demo nicht verfügbar; jeder Report nennt seine `model_id` ([ADR 0023](docs/adr/0023-demo-und-recruiter-stand.md)).
- **YAML:** CloudFormation-YAML gilt als Freitext und damit als offene Welt; ein fehlender Baustein wird dort nur WARN, kein FAIL (#48).
- **Build mit Groq:** `kb_build` bricht mit Groq oft an einer einzelnen Regel ab; Wiederholen hilft (#49).
- **Prüfregeln:** S3.5, DLS.2.2, IAM-09.01AC und BER.5.9 werten Deny bei `false` als Verstoß, 12 Regeln enthalten Platzhalter, nur `<Mindestfrist>` in DET.3.1 verfälscht das Ergebnis (WARN statt PASS, #50).
