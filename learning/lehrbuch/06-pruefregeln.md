# 06 – Prüfregeln formulieren

## Zweck

Aus jeder ausgewählten Anforderung entsteht **genau eine Prüfregel** (`Rule`): ein wörtliches Zitat, ein Titel, ein Kriterium für „konform“, eines für „Verstoß“ und eine Empfehlung. Das LLM formuliert, der Code setzt Identität und Herkunft, und ein Gate prüft den ganzen Katalog, bevor etwas geschrieben wird. Code: `rules/formulate.py`, `rules/criteria.py`, `rules/quality.py`, `rules/run.py`, `gates.py`. Befehl: `python -m kb_build rules [--audit-type …]`.

## Das Draft-Pattern (`govguard/models.py`)

Das LLM füllt nur `RuleDraft`: `source_quote`, `title`, `compliant_if`, `violation_if`, `recommendation`, `cross_references`. `Rule` erweitert den Entwurf um Felder, die **der Code** setzt:

| Feld | Herkunft |
|---|---|
| `id` = `ARCH-<Quelle>-<Anforderungs-ID ohne Leerzeichen>` bzw. `SPEC-…` (z. B. `SPEC-DSGVO-Art.32`) | Code (`_complete_rule`) |
| `audit_type`, `source`, `primary_anchor` | Code, aus Auswahl und Extraktion |
| `selection_rationale`, `cfn_resource_types` | Code, aus der Auswahlliste (Stufe ②) |
| `source_quote`, `title`, `compliant_if`, `violation_if`, `recommendation` | LLM, vom Code geprüft |
| `cross_references` | LLM, Code prüft die Existenz; nur `origin: ai_suggested` |

Was der Code schon weiß, erzeugt das LLM nicht. So bleibt der Teil klein, der halluzinieren kann.

## Ablauf

1. `formulate_rules()` geht die Auswahlliste der Reihe nach durch und baut je Anforderung `FormulateDeps` (Auswahl, Anforderung, alle Anker, `PropertyIndex`, `Scope`).
2. `formulate_agent` ruft das erzwungene Tool `formulate_rule` (`ToolOutput(RuleDraft, …)`), Temperatur 0, **bis zu 6 Retries** (`FORMULATE_RETRIES`; nur im Build, ADR 0014).
3. Der Output-Validator `_validate` prüft den Entwurf. Fehler gehen als `ModelRetry` mit konkretem Hinweis zurück.
4. `_complete_rule` ergänzt Identität und Herkunft. Bleibt der Entwurf nach allen Retries ungültig, wirft es `ValueError` („no valid rule“): **fail closed**, keine Regel darf still fehlen.
5. Am Ende läuft `check_rules()` über den ganzen Katalog. Erst danach schreibt `rules/run.py:formulate_all` die Datei. Fällt das Gate durch, bleibt der alte Katalog.
6. Der Katalog trägt `model_id` und `source_versions` (je Quelle die Version aus `sources.json`).

## Die Prüfungen im Validator (`_validate`)

1. **Zitat wörtlich:** `is_quoted()` – das Zitat muss im Text **genau dieser** Anforderung stehen. Bei Abweichung nennt `_deviation()` die Stelle, an der das Zitat vom Text abweicht („Ab … weicht es ab; im Text steht dort …“).
2. **Querverweise:** `invalid_cross_references()` – jeder Querverweis muss als Anker existieren und zu einer **anderen** Quelle gehören.
3. **Nur Architektur, Kriterien** (`criteria_problems`):
   - **Vage Wörter** (Regex `_VAGUE`: relevant, erforderlich, notwendig, angemessen, entsprechend, geeignet, ausreichend, gegebenenfalls, ggf., unnötig, übermäßig, regelmäßig, sensibel): am Template nicht entscheidbar.
   - **Typen außerhalb des Prüfumfangs** in den Kriterien (`Scope.outside` auf alle `AWS::…::…`-Treffer).
   - **Mindestens ein Ressourcentyp der Regel** muss wörtlich in den Kriterien stehen.
   - **Erfundene Eigenschaften** (`unknown_properties`): Der Retry-Text nennt echte Alternativen (`alternatives()`: Geschwister unter demselben Elternpfad, sonst Top-Level) und, falls der Name zu einem anderen Typ gehört, diesen Typ (`owners()`, höchstens 3).

Der Architektur-Prompt (`ARCHITECTURE_CRITERIA`) verlangt vorab: Kriterien nennen mindestens einen Ressourcentyp wörtlich plus Eigenschaft mit Wert (z. B. `DeletionProtection: true`), keine Wörter, die Wissen außerhalb des Templates brauchen, und die Bedingung, wenn die Pflicht nur für eine Variante gilt.

## Das Gate (`gates.py:check_rules`)

Läuft über den fertigen Katalog und sammelt **alle** Fehler, bevor es abbricht:

- Primäranker existiert in den Quellen.
- `source_quote` steht wörtlich im Text der verankerten Anforderung.
- Querverweise existieren und gehören zu einer anderen Quelle.
- Keine Ressourcentypen außerhalb des Prüfumfangs (in `cfn_resource_types` und in den Kriterien).
- **Vollständigkeit** (`_completeness_errors`): ausgewählte Anforderung ohne Regel, Anforderung mit mehr als einer Regel, Regel für nicht ausgewählte Anforderung. Der Bounded Catalog verliert nichts und erfindet nichts.

Warum Validator **und** Gate? Der Validator gibt dem Modell eine zweite Chance (billig, früh); das Gate ist die harte Endkontrolle mit denselben Prüfungen, auch gegen Fehler außerhalb des Modells.

## Der Qualitätsbericht (`rules/quality.py`)

Nach jedem Lauf zählt `quality_report()` je Quelle: `rules`, `vague`, `account_level` (Regex auf CloudTrail, AWS Organizations, Root-Konto, Passwortrichtlinie, nachdem `AWS::…`-Typnamen entfernt sind), `unknown_properties` und `unjudged_properties` (Typ außerhalb des Schnappschusses, den niemand prüft). Ziel: überall 0. **Eine 0 bei `unknown_properties` allein genügt nicht**, wenn `unjudged_properties` hoch ist: Dann ist die Lücke nur unsichtbar. Genau das war der Befund nach Issue #17 (16 ungeprüfte Regeln), den ADR 0013 schloss. Stand des Laufs vom 13.10.2026 (Issue #19): alle Werte 0.

## Beispiele (echte Daten)

`ARCH-FSBP-SNS.1` (Auszug):

```json
{ "id": "ARCH-FSBP-SNS.1", "primary_anchor": "AWS FSBP SNS.1", "source": "FSBP",
  "source_quote": "This control checks whether an SNS topic is encrypted at rest using AWS KMS.",
  "title": "SNS-Topic-Verschlüsselung mit KMS",
  "compliant_if": "Ein AWS::SNS::Topic enthält das Attribut KmsMasterKeyId mit einem nicht‑leeren Schlüssel‑ARN.",
  "violation_if": "Ein AWS::SNS::Topic fehlt das Attribut KmsMasterKeyId oder es ist leer.",
  "cfn_resource_types": ["AWS::SNS::Topic"] }
```

Man sieht die Aufgabenteilung: Typ und Eigenschaft (`AWS::SNS::Topic`, `KmsMasterKeyId`) sind prüfbar und im Schnappschuss vorhanden; das Zitat steht wörtlich im Text von SNS.1.

`SPEC-DSGVO-Art.32`: Zitat „die Fähigkeit, die Vertraulichkeit, Integrität, Verfügbarkeit und Belastbarkeit der Systeme und Dienste im Zusammenhang mit der Verarbeitung auf Dauer sicherzustellen“; Kriterien verlangen konkrete technische Maßnahmen in der Spezifikation. Bei Spec ist `cfn_resource_types` leer.

## Warum so

- **Zitat statt Behauptung** (ADR 0005, Issue #12): Jede Regel ist auf den Normtext rückführbar; das entspricht der Rechenschaftspflicht (DSGVO Art. 5 Abs. 2) und der Nachvollziehbarkeit eines BSI-Audits.
- **Der Code setzt den Primäranker, nicht das LLM:** Er kennt die ID aus der Extraktion; ein vom LLM geschriebener Anker könnte erfunden sein.
- **Gleiche Prüffunktionen wie zur Laufzeit:** `contains_quote()` ist dieselbe Funktion, die später den Beleg im Audit prüft (Kapitel 07).
- **Mehr Retries bei Groq** (ADR 0014): Groq wiederholt erfundene Zitate öfter als Haiku; das Gate bleibt gleich streng.

## Fachbegriffe

- **Draft-Pattern:** LLM schreibt das `*Draft`-Modell, Code ergänzt den Rest.
- **Primäranker:** die eine Anforderung, aus der die Regel stammt.
- **Querverweis:** KI-vorgeschlagener, nicht verifizierter Bezug auf eine andere Quelle; beeinflusst keinen Status.
- **Fail closed:** keine Regel geht still verloren.
- **Qualitätsbericht:** Zähler je Quelle, die sichtbar machen, was ein Gate nicht abdeckt.

## Grenzen

- Querverweise sind KI-Vorschläge. Das Gate prüft nur, dass der Anker existiert und zu einer anderen Quelle gehört, nicht ob er inhaltlich passt.
- Die Kriterien prüft der Code auf Form (Typ, echte Eigenschaft, keine vagen Wörter), nicht auf fachliche Richtigkeit. Dafür gibt es die Stichprobe von Hand (Fahrplan, Schritt 9).
- Heuristik bei Eigenschaftsnamen: Einzelwörter wie `Encrypted` werden nicht geprüft.

## Fragen für das Fachgespräch

1. Welche Felder einer Prüfregel setzt der Code und nicht das LLM, und warum?
2. Was passiert, wenn das Zitat nicht im Text steht: erst im Validator, dann im Gate?
3. Warum beweist der Schema-Abgleich mehr als ein strengerer Prompt?
