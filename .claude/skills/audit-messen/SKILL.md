---
name: audit-messen
description: CLI-Audit gegen echtes Bedrock laufen lassen und Laufzeit, Tokens, Kosten und Retry-Gründe messen. Für Messläufe mit Presets, Kostenschätzungen und Diagnose von fail-closed-Abbrüchen.
---

Jeder Lauf kostet echtes Geld (Kosten-Weiche, CLAUDE.md). Die CLI kennt nur `spec`; Architektur-Audits misst dieser Weg noch nicht.

1. **Kosten schätzen, Go holen.** Pakete = ⌈Prüfregeln / 10⌉ (`PACKAGE_SIZE` in `audit_engine.py`). Jedes Paket schickt die ganze Eingabe mit: ca. 2,6 Zeichen je Token. Kosten ≈ Pakete × (Eingabe-Tokens × 1,10 $ + 3.000 × 5,50 $) / 1 Mio. Nenne die Schätzung und warte auf das Go. Für eine billige Diagnose reicht ein Katalog mit 10 Regeln (ein Paket, ca. 0,05 $): `rules[:10]` aus `data/knowledge_base/rules_spec.json` in eine Scratchpad-Datei schreiben und mit `--catalog` übergeben.
2. **Anmeldung prüfen.** `aws sts get-caller-identity --profile Student-919519434628`. Bei „Token has expired“ den Nutzer bitten, `aws sso login --profile Student-919519434628` selbst auszuführen (Browser), und warten.
3. **Messen.** Ausgaben in den Scratchpad:

   ```bash
   PYDANTIC_AI_NO_BANNER=1 AWS_PROFILE=Student-919519434628 \
     uv run python .claude/skills/audit-messen/measure.py spec <eingabe> [--catalog <json>] \
     > <scratchpad>/report.json 2> <scratchpad>/stats.txt
   ```

4. **Berichten.** Fertig ist der Bericht, wenn er nennt: Exit-Code, Gesamtzeit, langsamsten Aufruf gegen die 29-s-Grenze von API Gateway, Aufrufe, Tokens, Kosten, und bei Exit 2 die Retry-Gründe mit den `REJECTED EVIDENCE`-Zeilen. Bei Exit 0 den Report mit `expected` aus `preset.json` vergleichen.

## Fallstricke

- Modellvergleich: `MEASURE_MODEL=groq` nimmt `groq_model()` aus dem Build (Key per `set -a; source .env`). Nur mit fiktiven Presets; zur Laufzeit ist Groq verboten (ADR 0001). Groq meldet hier 0 Tokens, die Kostenzeile gilt dann nicht.

- Scheitert ein Paket endgültig, bricht `asyncio.run` die übrigen ab. `calls` zählt dann nur fertige Aufrufe; Bedrock berechnet abgebrochene trotzdem. Die Zahl der Retry-Prompts zeigt, wie viele Pakete wirklich Probleme hatten.
- Preise: Haiku 4.5 kostet 1 $ / 5 $ je Mio. Tokens, das `eu.`-Profil 10 % mehr (Anthropic-Preisdoku). Ändert sich `MODEL_ID` in `aws_services.py`, die Preiszeile in `measure.py` anpassen.
- Basislinie 14.10.2026, `spec-wohngeld-openapi` (84 KB, 151 Regeln, 16 Pakete): ca. 39 s, 32 Tsd. Input-Tokens je Aufruf, langsamster Aufruf 37 s, ca. 0,90 $, fail closed wegen zusammengesetzter Belege.
