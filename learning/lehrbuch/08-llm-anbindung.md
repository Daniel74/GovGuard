# 08 – LLM-Anbindung: Pydantic AI, Tool-Choice und Provider

## Zweck

Die Pipeline ruft ein LLM an zwei Stellen: Stufe ② (`classify_requirement`) und das Formulieren (`formulate_rule`). Dieses Kapitel erklärt, wie diese Aufrufe gebaut sind und warum der Build ein anderes Modell nutzen darf als die Laufzeit.

## Pydantic AI und Tool-Choice (ADR 0005)

- Jeder LLM-Aufruf ist ein **`Agent`** mit einem Draft-Modell als `output_type`, verpackt in `ToolOutput(Modell, name=…, description=…)`. Das Framework erzeugt daraus das Tool-Schema und **erzwingt den Tool-Aufruf** (Tool-Choice). Die Antwort ist also strukturiert (JSON nach Pydantic-Schema), kein Freitext.
- **Validierung als Code:** Fachliche Prüfungen laufen als `@agent.output_validator` und lösen `ModelRetry` aus. Zusätzliche Daten (Prüfumfang, Anker, Schnappschuss) reichen `deps_type`-Objekte hinein (`ClassifyDeps`, `FormulateDeps`).
- **Dependency Injection:** Die Prüflogik **bekommt das Modell übergeben** (`Judge(model=…)`, `formulate_rules(model, …)`), sie baut es nie selbst. Der Einstieg `__main__.py:model_for()` wählt es. Tests reichen `FunctionModel` oder `TestModel` von Pydantic AI hinein, ohne Netz.
- **Retries:** Stufe ② `retries=2`, Formulieren `FORMULATE_RETRIES = 6`. Zur Laufzeit gilt wegen des 29-Sekunden-Timeouts nur `retries=1`.
- **Temperatur 0** in beiden Build-Agenten.

## Provider (`__main__.py:model_for`)

| `--provider` | Modell | Wo gebaut | Wann |
|---|---|---|---|
| `groq` (Standard) | `openai/gpt-oss-120b` (per `GROQ_MODEL` änderbar) | `kb_build/groq_services.py` | Standard im Build (ADR 0014) |
| `bedrock` | Claude Haiku 4.5, Profil `eu.` | `govguard/aws_services.py` | ausdrücklich, z. B. wenn Groq ausfällt |
| `bedrock-global` | Claude Haiku 4.5, Profil `global.` | `aws_services.py` (`GLOBAL_MODEL_ID`) | ausdrücklich, wenn `eu.` keine Kapazität hat (ADR 0012) |

Ein unbekannter Name wirft `ValueError`. Fehlt `GROQ_API_KEY`, bricht der Build ab, ohne auf Bedrock auszuweichen (**kein stilles Umschalten**: sonst verließen Daten unbemerkt die EU). Der Schlüssel liegt nur in der Shell bzw. `.env` (gitignored). `groq_services.py` nutzt `AsyncGroq(max_retries=6)`: Das SDK wartet bei HTTP 429 (Rate Limit) mit Backoff. Die `model_id` steht in `selection_*.json` und `rules_*.json`, so ist jeder Katalog seinem Modell zuordenbar.

## Warum der Build ein anderes Modell nutzen darf (ADR 0001, 0010, 0012, 0014)

- **Daten:** Im Build gehen nur **öffentliche Normtexte** raus, nie Nutzereingaben. Die Laufzeit mit Nutzereingaben bleibt in der EU auf Bedrock (Profil `eu.`, Art. 44 DSGVO: Drittlandtransfer). Haiku über Bedrock `eu.` bleibt für alles mit Nutzereingaben: Audits zur Laufzeit, das Preset-Gate (es ruft die Audit-Engine auf) und die Archetyp-Generierung (ADR 0014). Preset-Gate und Archetypen sind noch nicht gebaut.
- **Kosten:** Ein voller Neulauf von Stufe ② kostet rund 960 Anfragen und wird bei jeder Prompt-Änderung fällig; Groq ist deutlich günstiger als Haiku. Beispiel Issue #6: 1.087 Anfragen, 584.357 Eingabe- und 307.020 Ausgabe-Token, **ca. 0,32 $** (Groq-Listenpreis 0,15 $ / 0,75 $ je Million Token). Issue #18 schätzte Haiku auf ca. 2 $ gegenüber ca. 0,25 $ bei Groq.
- **Ein Modell im ganzen Katalog:** `select` lief zuerst mit Groq, `rules` mit Haiku. Zwei Modelle in einem Build sind schwerer zu erklären; seit #21 stammt der ganze Katalog von `openai/gpt-oss-120b`.
- **Qualität unabhängig vom Modell:** Die Gates fangen Erfundenes per Code ab, egal welches Modell schreibt (ADR 0014).

Geschichte der Entscheidung: ADR 0010 (Groq als befristeter Fallback, weil dem Kurskonto die Marketplace-Rechte fehlten) → ADR 0012 (Bedrock `global.`, weil `eu.` am 12.10.2026 dreimal HTTP 503 lieferte) → ADR 0014 (Groq dauerhaft Standard). Die Ausnahme von „Inferenz nur in der EU“ ist dadurch dauerhaft, aber auf den Build mit öffentlichen Texten begrenzt.

## Eigenschaften und Garantien

- **boto3 und Modellbau nur in Adaptern:** Ein Architekturtest erzwingt, dass `boto3`, `botocore`, Bedrock-Klassen nur in `aws_services.py` und `groq`/Groq-Klassen nur in `groq_services.py` importiert werden. Die Prüflogik bleibt rein und testbar.
- **Fail closed bei Auth- und Serverfehlern:** 401, 429 und 5xx brechen den Lauf ab (`Judge._ask`), sie sind kein Urteil über die Anforderung.
- **Alle Token werden gezählt**, auch von gescheiterten Retries (`Judge.usage`), und am Ende geloggt.

## Fachbegriffe

- **Tool-Choice:** erzwungener Tool-Aufruf mit festem Schema statt Freitext.
- **Dependency Injection:** Abhängigkeiten (das Modell) werden hineingereicht, nicht im Code gebaut.
- **Inferenzprofil `eu.` / `global.`:** Bedrock-Routing; `eu.` hält die Inferenz in der EU, `global.` kann weltweit routen.
- **Rate Limit (HTTP 429):** Dienst bremst bei zu vielen Anfragen.
- **FunctionModel / TestModel:** Test-Fakes von Pydantic AI.

## Grenzen

- `global.` und Groq verlassen die EU; das gilt hier nur für öffentliche Normtexte. Auch der lizenzierte CIS-Volltext geht bei jedem Build an Groq (US); das nimmt ADR 0014 für einen Prototyp ohne Weitergabe des Textes in Kauf.
- Erzwungene Tools auf Groq sind nicht dokumentiert (ADR 0010); der Betrieb im echten Lauf hat funktioniert, Groq wiederholt aber öfter.

## Fragen für das Fachgespräch

1. Warum darf der Build Groq nutzen, die Laufzeit aber nicht?
2. Was bringt Dependency Injection beim Testen der LLM-Aufrufe?
3. Warum schaltet der Build nicht automatisch auf einen anderen Provider um?
