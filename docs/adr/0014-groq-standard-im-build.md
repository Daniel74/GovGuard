# 0014 – Groq ist Standard für den Build der Wissensbasis

_Ersetzt [ADR 0010](0010-groq-build-fallback.md). Weicht für den Build von [ADR 0001](0001-eu-inferenzprofil.md) ab._

## Kontext

- Bedrock läuft inzwischen, aber Haiku 4.5 ist im Lauf vom 13.10.2026 (#19) deutlich teurer als Groq `openai/gpt-oss-120b`. Ein voller Neulauf von Stufe ② kostet rund 960 Anfragen und wird bei jeder Prompt-Änderung fällig.
- Im Build gehen nur öffentliche Normtexte raus, keine Eingaben von Nutzern. Erfundene Typen, Eigenschaften und Zitate fangen die Gates per Code ab (#12, #17, #19), egal welches Modell schreibt.
- `select` lief bisher mit Groq, `rules` mit Haiku. Zwei Modelle in einem Build sind schwerer zu erklären, und keines der beiden ist zwischen zwei Läufen stabil (ADR 0011).

## Entscheidung

- `python -m kb_build` nutzt ohne Flag Groq (`--provider groq` ist Standard), für `select` und für `rules`. Ein Test prüft den Standard.
- Bedrock bleibt als ausdrückliche Option: `--provider bedrock` (`eu.`) und `--provider bedrock-global` (ADR 0012), z. B. wenn Groq ausfällt.
- Haiku über Bedrock `eu.` bleibt für alles mit Nutzereingaben: Audits zur Laufzeit, Preset-Gate (es ruft die Audit-Engine auf) und Archetyp-Generierung (#7).
- Kein stilles Umschalten: Fehlt `GROQ_API_KEY`, bricht der Build ab. Das Modell steht als `model_id` in Auswahlliste und Katalog.

## Konsequenzen

- Die Ausnahme von „Inferenz nur in der EU“ gilt im Build dauerhaft, nicht mehr befristet. `groq_services.py` und die Abhängigkeit in der Gruppe `build` bleiben.
- Der CIS-Volltext (lizenziert, ADR 0008) geht bei jedem Build an Groq (US). Das nehmen wir für einen Prototyp ohne Weitergabe des Textes in Kauf.
- `build-kb.yml` (#8) braucht `GROQ_API_KEY` als GitHub-Secret. Die OIDC-Rolle braucht trotzdem Bedrock `eu.` für das Preset-Gate.
- Der Wechsel macht den Katalog nicht stabiler: Auch Groq tauscht bei einem Neulauf rund 10 % der Auswahl aus (#19). Die Pflichtanker-Gates bleiben die Absicherung.

## Fachgespräch-Satz

„Nutzerdaten verarbeitet nur Bedrock in der EU; die Wissensbasis entsteht aus öffentlichen Normtexten mit dem günstigsten Modell, und die Gates im Code machen die Qualität vom Modell unabhängig.“
