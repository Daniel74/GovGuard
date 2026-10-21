# Belege ohne Abschreiben – Citations und Strict Tool Use

Recherche für #26. Lokal geprüft: `pydantic-ai-slim` 2.54.0, `botocore` 1.43.110, `groq` 1.7.0 (`.venv`). Quellen in eckigen Klammern, Liste am Ende.

## Kurzantwort

- **Citations (Bedrock)**, also Fundstellen, die die API selbst auf den Quelltext zurückführt, liefern Belege mit garantiert gültigen Fundstellen, aber nur in **Text-Blöcken**. Sie schließen sich mit Structured Outputs aus (HTTP 400), und mit erzwungenem Tool entsteht kein Text. Pydantic AI unterstützt sie nicht. Für GovGuard passen sie damit nicht zu ADR 0005 und nicht zu ADR 0016.
- **Strict Tool Use auf Bedrock** (Haiku 4.5, Profil `eu.`; Tool-Argumente werden per Grammatik auf das Schema beschränkt [A2]) ist dokumentiert [B5, B6] und funktioniert mit Pydantic AI: `ToolOutput(..., strict=True)` schickt `strict: true`, `toolChoice` bleibt erzwungen.
- **Groq gpt-oss-120b** hat echtes Constrained Decoding (Erzeugung nur schema-gültiger Tokens) über `response_format: json_schema` mit `strict: true`, aber **nicht zusammen mit Tools**. Strict Tool Use ist bei Groq nicht dokumentiert, und Pydantic AI verwirft `strict` bei Groq-Tools. Der Weg dorthin heißt in Pydantic AI `NativeOutput`.

## 1. Bedrock Converse – Citations

**Anfrage.** Ein `document`-Block bekommt `citations: {enabled: true}`, optional `context` [B1, B2]. Die Quelle kommt als `source.text` oder `source.content` (eigene Textblöcke) [L1]. Anthropic: Klartext wird in Sätze zerlegt, eigene Blöcke (Custom Content) bleiben ungeteilt. Citations müssen für alle Dokumente einer Anfrage an oder aus sein [A1].

**Antwort.** Der Inhaltsblock `citationsContent` enthält `content` (generierter Text) und `citations[]` [B3]. Jede Citation hat `title`, `source`, `sourceContent[].text` (zitierter Originaltext) und `location`. Mögliche Orte: `documentChar` (Zeichen), `documentPage` (Seite), `documentChunk` (Block), außerdem `searchResultLocation` und `web`, jeweils mit `documentIndex`, `start`, `end` [L1]. Beim Streaming kommt ein `citation`-Delta [L1].

**Haiku 4.5 über `eu.`.** AWS sagt allgemein: „Anthropic Claude models support … citations“ [B4]. Anthropic: „All active models support citations“, Bedrock ist GA [A1]. Die Modellkarte von Haiku 4.5 nennt Citations nicht [B5]. Haiku 4.5 + `eu.` + Citations ist also **nicht ausdrücklich belegt**, nur allgemein.

**Mit Tool Use / `toolChoice`.** Das ist der kritische Punkt:
- Citations hängen nur an Text. `ToolUseBlock` hat nur `toolUseId`, `name`, `input`, `type` und kein Citation-Feld [L1, A1]. Citations in Tool-Argumenten gibt es also nicht.
- Erzwungenes Tool (`any`/`tool`): „the models will not emit a natural language response … before `tool_use` content blocks“ [A3]. Damit gibt es keinen Text und folglich keine Citations. Pydantic AI erzwingt für `ToolOutput` aber `toolChoice: {any: {}}` (lokal geprüft, siehe 3.).
- **Dokumentierte Unverträglichkeit**: „Structured outputs is incompatible with citations for Anthropic models … 400 error“ [B6]. Ebenso bei Anthropic [A1]. Structured Outputs umfasst laut AWS beide Mechanismen, JSON-Format **und** Strict Tool Use [B6]. Ob auch `strict: true` allein den 400er auslöst, ist **nicht ausdrücklich belegt**.

**Kosten.** Anthropic: „`cited_text` … does not count toward output tokens“, die Eingabe wächst dafür leicht [A1]. Für Bedrock ist das **nicht eigens belegt**, Bedrock rechnet aber dieselben Token-Zählungen des Modells ab (Annahme).

## 2. Groq – `openai/gpt-oss-120b`

- **Structured Outputs strict**: `response_format: {type: json_schema, json_schema: {…, strict: true}}`. Groq beschreibt das als **Constrained Decoding** und sagt: „Never errors or produces invalid JSON“. `openai/gpt-oss-120b` steht in der Liste für `strict: true` [G1].
- **Einschränkungen** [G1]: „Streaming and tool use are not currently supported with Structured Outputs.“ Im Strict-Modus müssen alle Felder in `required` stehen; optionale Felder gehen als Union mit `null`. Jedes Objekt braucht `additionalProperties: false`. Erlaubte Typen: Primitive, Object, Array, Enum, `anyOf`. Grenzen für Verschachtelung oder Feldzahl nennt die Seite nicht.
- **Strict Tool Use**: Die Groq-Doku zu Tool Use erwähnt `strict` nicht [G2, G3]. Nur ein Schema-Beispiel auf der Structured-Outputs-Seite zeigt `"strict": true` in einer Funktionsdefinition, ohne Erklärung [G1]. Das Groq-SDK kennt das Feld `FunctionDefinition.strict` [L4]. Dass Groq Tool-Argumente per Constrained Decoding erzwingt, ist **nicht belegt**. Zu `tool_choice` mit Funktionsnamen sagt Groq nur, dass ein Aufruf eines anderen oder keines Tools zu HTTP 400 führt [G3].
- Modell: 131.072 Token Kontext, 0,15 $ Eingabe und 0,60 $ Ausgabe je 1 Mio. Token [G4].

## 3. Unterstützung durch Pydantic AI (2.54.0)

| Funktion | Bedrock (`BedrockConverseModel`) | Groq (`GroqModel`) |
| --- | --- | --- |
| Citations | **nein**: Dokumentblock ohne `citations` [L2a], `citationsContent` wird beim Parsen ignoriert [L2b]. Issue #3126 ist offen, PR #3729 wurde ohne Merge geschlossen [P1, P2]. | entfällt |
| `ToolOutput(strict=True)` | **ja**: sendet `toolSpec.strict: true` und `toolChoice: any` [L2c, Probe] | **nein**: `strict` wird nicht übertragen, `tool_choice: required` [L3a, Probe] |
| `NativeOutput` | `outputConfig.textFormat` json_schema [L2d, Probe] | `response_format` json_schema mit `strict: true` [L3b, Probe] |
| Profil Haiku 4.5 `eu.` | `supports_json_schema_output` und `bedrock_supports_strict_tool_definition` = True [L2e] | – |

*Probe*: Ein lokales Skript hat mit Mock-Transport bzw. botocore-Hook die echten Request-Bodies abgefangen, ohne API-Aufruf. Pydantic AI entfernt außerdem Schlüsselwörter, die Bedrock im Strict-Modus ablehnt (`minimum`, `maximum`, `maxItems` u. a.), und warnt vor dem Limit von 20 Strict-Tools je Anfrage [L2f]. Laut Pydantic-Doku ist `ToolOutput` der Standard und läuft auf praktisch allen Modellen. `NativeOutput` nutzt die eingebauten Structured Outputs des Anbieters [P3].

## 4. Empfehlung (keine Entscheidung)

**Citations eher nicht.** Sie verlangen Freitext statt erzwungenem Tool (Konflikt mit ADR 0005) und gibt es nur auf Bedrock (Konflikt mit ADR 0016). Pydantic AI kann sie nicht, also müsste `aws_services.py` boto3 direkt aufrufen und Text-Blöcke selbst parsen.

**Besser passt „Beleg per Verweis“ plus strenges Schema.** Der Code nummeriert die Eingabe (Zeilen oder Blöcke). Das LLM liefert nur Ganzzahlen (`line_start`, `line_end`), der Code schneidet das Zitat aus und prüft den Bereich. Dann kann das Modell kein Zitat mehr erfinden oder umformulieren, und es fallen weniger Output-Tokens an. Das Schema erzwingt pro Modell:
- Bedrock: `ToolOutput(..., strict=True)`. Tool-Choice bleibt, ADR 0005 bleibt gültig.
- Groq: `NativeOutput(...)` mit Constrained Decoding. Das weicht für Groq von „erzwungenes Tool“ ab und gehört ins ADR.

**Für den Prototyp beachten:**
- Das Schema statisch halten, z. B. keine `enum` der Zeilennummern je Eingabe. Jedes neue Schema kompiliert Bedrock erst, „which may take up to a few minutes“, danach liegt es 24 h im Cache [B6]. Das sprengt die 29 s.
- Groq-Strict braucht alle Felder in `required`; `str | None` ohne Default erfüllt das.

**Randnotiz:** Die Modellkarte von Haiku 4.5 nennt „EOL no sooner than: Oct 16, 2026“. Status ist „Active“, ein EOL-Datum steht nicht fest [B5].

## Quellen

- [A1] Anthropic, Citations: https://platform.claude.com/docs/en/build-with-claude/citations (Abschnitte *How citations work*, *Token costs*, *Feature compatibility*, *Response structure*)
- [A2] Anthropic, Strict tool use: https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use
- [A3] Anthropic, Define tools → *Forcing tool use*: https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools
- [B1] AWS, Inference using Converse API: https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html
- [B2] AWS API, DocumentBlock: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_DocumentBlock.html
- [B3] AWS API, CitationsContentBlock: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_CitationsContentBlock.html
- [B4] AWS, Anthropic Claude models: https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html
- [B5] AWS, Modellkarte Claude Haiku 4.5: https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-haiku-4-5.html (Features, Geo EU ab eu-central-1, Hinweis zum Profil `in.`)
- [B6] AWS, Structured outputs: https://docs.aws.amazon.com/bedrock/latest/userguide/structured-output.html (Cross-Region: „Works without any additional setup“; Note zu Citations; Request workflow)
- [G1] Groq, Structured Outputs: https://console.groq.com/docs/structured-outputs
- [G2] Groq, Tool Use: https://console.groq.com/docs/tool-use
- [G3] Groq, Local Tool Calling → *Controlling Tool Use Behavior*: https://console.groq.com/docs/tool-use/local-tool-calling
- [G4] Groq, Modellseite: https://console.groq.com/docs/model/openai/gpt-oss-120b
- [P1] pydantic-ai Issue #3126 „Support structured citations“ (offen): https://github.com/pydantic/pydantic-ai/issues/3126
- [P2] pydantic-ai PR #3729 (geschlossen, nicht gemergt): https://github.com/pydantic/pydantic-ai/pull/3729
- [P3] Pydantic AI, Output: https://pydantic.dev/docs/ai/core-concepts/output/
- [L1] botocore `data/bedrock-runtime/2023-09-30/service-2.json.gz`, Shapes `CitationsConfig`, `DocumentBlock`, `DocumentSource`, `CitationsContentBlock`, `Citation`, `CitationLocation`, `DocumentChar/Chunk/PageLocation`, `ToolUseBlock`, `ToolSpecification.strict`, `OutputConfig`
- [L2] `.venv/…/pydantic_ai/models/bedrock.py`: a) `_make_document_block` Z. 270; b) `_process_response` ab Z. 937 (kein Zweig für `citationsContent`); c) `_map_tool_definition` Z. 812; d) `_native_output_format` Z. 833; `…/providers/bedrock.py`: e) Z. 300 und `profiles/anthropic.py` Z. 206; f) Z. 45–79
- [L3] `.venv/…/pydantic_ai/models/groq.py`: a) `_map_tool_definition` Z. 609 (ohne `strict`); b) `_map_json_schema` Z. 619, Aufruf Z. 344
- [L4] `.venv/…/groq/types/shared_params/function_definition.py` Z. 33
