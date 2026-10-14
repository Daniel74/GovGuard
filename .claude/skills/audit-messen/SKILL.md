---
name: audit-messen
description: CLI-Audit gegen echtes Bedrock oder Groq laufen lassen und Laufzeit, Tokens, Kosten und Retry-Gründe messen. Für Messläufe mit Presets, Kostenschätzungen und Diagnose von fail-closed-Abbrüchen.
---

Jeder Lauf kostet echtes Geld (Kosten-Weiche, CLAUDE.md). Die CLI kennt nur `spec`; Architektur-Audits misst dieser Weg noch nicht.

1. **Kosten schätzen, Go holen.** Pakete = ⌈Prüfregeln / 10⌉ (`PACKAGE_SIZE` in `audit_engine.py`). Jedes Paket schickt die ganze Eingabe mit Zeilennummern mit: ca. 2,2 Zeichen je Token (Nummern kosten ca. 17 % mehr). Kosten Bedrock ≈ Pakete × (Eingabe-Tokens × 1,10 $ + 2.500 × 5,50 $) / 1 Mio.; Groq ≈ Pakete × (Eingabe-Tokens × 0,15 $ + 2.500 × 0,60 $) / 1 Mio. Nenne die Schätzung und warte auf das Go. Für eine billige Diagnose reicht ein Katalog mit 10 Regeln (ein Paket, ca. 0,05 $): `rules[:10]` aus `data/knowledge_base/rules_spec.json` in eine Scratchpad-Datei schreiben und mit `--catalog` übergeben.
2. **Anmeldung prüfen.** `aws sts get-caller-identity --profile Student-919519434628`. Bei „Token has expired“ den Nutzer bitten, `aws sso login --profile Student-919519434628` selbst auszuführen (Browser), und warten.
3. **Messen.** Ausgaben in den Scratchpad:

   ```bash
   PYDANTIC_AI_NO_BANNER=1 AWS_PROFILE=Student-919519434628 \
     uv run python .claude/skills/audit-messen/measure.py spec <eingabe> [--catalog <json>] \
     > <scratchpad>/report.json 2> <scratchpad>/stats.txt
   ```

4. **Berichten.** Fertig ist der Bericht, wenn er nennt: Modell, Exit-Code, Gesamtzeit, langsamsten Aufruf gegen die 29-s-Grenze von API Gateway, Aufrufe, Tokens, Output-Tokens je Aufruf, Kosten, Retry-Prompts (davon Schema) und bei Exit 2 die Retry-Gründe. Bei Exit 0 den Report mit `expected` aus `preset.json` vergleichen.

## Fallstricke

- Groq: `MEASURE_MODEL=groq` nimmt `groq_model()` aus dem Build (Key per `set -a; source .env`). Groq ist zur Laufzeit eine ausdrückliche Option, nur mit fiktiven Presets (ADR 0016). Tokens meldet Groq inkl. Denk-Tokens. Limit 250.000 Tokens/min: Der volle Katalog (16 Pakete, ca. 460.000) endet sonst mit HTTP 429.
- Belege per Zeilenverweis (ADR 0017): Ein FAIL ohne Zeilenbereich stuft der Code still auf WARN herab, ohne Retry. Im Report ist das noch nicht sichtbar (#27).

- Scheitert ein Paket endgültig, bricht `asyncio.run` die übrigen ab. `calls` zählt dann nur fertige Aufrufe; Bedrock berechnet abgebrochene trotzdem. Die Zahl der Retry-Prompts zeigt, wie viele Pakete wirklich Probleme hatten.
- Preise: Haiku 4.5 kostet 1 $ / 5 $ je Mio. Tokens, das `eu.`-Profil 10 % mehr (Anthropic-Preisdoku). Ändert sich `MODEL_ID` in `aws_services.py`, die Preiszeile in `measure.py` anpassen.
- Basislinie 14.10.2026, `spec-wohngeld-openapi` (84 KB, 151 Regeln, 16 Pakete), noch mit wörtlichen Zitaten: ca. 39 s, 32 Tsd. Input-Tokens und ca. 3.000 Output-Tokens je Aufruf, langsamster Aufruf 37 s, ca. 0,90 $, fail closed wegen zusammengesetzter Belege.
