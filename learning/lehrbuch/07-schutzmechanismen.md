# 07 – Schutzmechanismen: Welche Halluzination wird wo abgefangen

## Zweck

Ein LLM kann Dinge erfinden, die plausibel klingen. Die Pipeline geht damit nicht durch „bitte nicht erfinden“ im Prompt um, sondern durch **deterministische Gegenproben gegen eine feste Referenz**. Dieses Kapitel ist die Übersicht über alle Stellen. Leitgedanke: *Ein Prompt kann Halluzinationen nur seltener machen, ein Abgleich gegen eine Referenz schließt sie aus* (Lernkarte #17).

## Die zwei Verteidigungslinien

- **Validator** (`@agent.output_validator`, billig, früh): schickt die Antwort mit konkretem Hinweis an das Modell zurück (`ModelRetry`) oder bereinigt sie selbst. Das Modell bekommt eine zweite Chance.
- **Gate** (hart, am Ende): Code prüft das Ergebnis; bei einem Fehler bricht der Build ab (`ValueError`), die alte Wissensbasis bleibt aktiv (fail closed).

## Übersicht

| Was das LLM erfinden könnte | Gegenprobe | Referenz | Wo im Code | Linie |
|---|---|---|---|---|
| ein Zitat, das nicht im Normtext steht | wörtlicher Vergleich nach `normalize()`, ohne Leerzeichen, min. 15 Zeichen | Text der verankerten Anforderung | `govguard/text.py:contains_quote`, `gates.py:is_quoted` | Validator + Gate |
| eine Fundstelle (`DET.3.99`) oder ein Querverweis | Anker muss existieren, Querverweis aus anderer Quelle | alle extrahierten Anforderungen | `gates.py:invalid_cross_references`, `requirements_by_anchor` | Validator + Gate |
| einen CloudFormation-Typ | Typ muss echt sein | `cfn_resource_types.json` | `classify.py:_validate`, `reference/cfn_types.py` | Validator (Verwerfen oder Retry) |
| einen Typ außerhalb des Prüfumfangs | Code streicht ihn; Kriterien mit solchen Typen gehen zurück | `scope.json` | `classify.py:_validate`, `rules/criteria.py`, `gates.py:_rule_errors` | Validator + Gate |
| eine Eigenschaft, die der Typ nicht hat (`TargetPrefix`) | Schnappschuss-Abgleich | `cfn_properties.json` | `reference/cfn_properties.py:unknown_properties` | Validator (Retry mit Alternativen) |
| vage Kriterien („angemessen“) | Wortliste | Regex `_VAGUE` | `rules/quality.py`, `rules/criteria.py` | Validator |
| Regeln, die fehlen, doppelt sind oder nicht ausgewählt wurden | Zählung gegen die Auswahlliste | `selection_*.json` | `gates.py:_completeness_errors` | Gate |
| Herkunft und Identität einer Regel | Code setzt sie, nicht das LLM | Extraktion, Auswahl | `rules/formulate.py:_complete_rule` | Entwurf |
| ein Pflichtanker fällt aus der Auswahl | Anker muss `selected` sein | Presets | `gates.py:check_pinned` | Gate (zuerst) |
| eine Komponente der Archetypen hat keine Regel | mindestens eine Regel je Komponente | Steckbriefe | `gates.py:check_coverage` | Gate |
| eine Quelle ändert sich still | SHA-256-Vergleich | `sources.json` | `source_fetch.py:_verify` | Gate beim Laden |
| eine Pflicht, die dem Konto oder Personen gehört | Ebene `scope_level`; Code setzt `not_relevant` | Prompt + Code | `select/curation.py:_not_relevant_reason` | Code-Entscheidung |
| schwankende Urteile | Cache friert Urteile ein | Cache-Schlüssel mit Prompt-Version | `select/judgement_cache.py` | Cache |

## Die gemeinsame Zitatprüfung (`govguard/text.py`)

`normalize()` wendet fünf Schritte in fester Reihenfolge an, Groß-/Kleinschreibung bleibt erhalten:

1. Unicode-Normalisierung NFKC.
2. EUR-Lex-Konsolidierungsmarker wie „►C2“, „▼M1“, „◄“ entfernen.
3. Weiche Trennstriche (`­`) entfernen.
4. Typografische Zeichen vereinheitlichen („ “ ” « » → `"`, ‚ ‘ ’ → `'`, – — → `-`).
5. Whitespace zu einem Leerzeichen zusammenfassen und trimmen.

`contains_quote(text, quote)` ist wahr, wenn das normalisierte Zitat **ohne Leerzeichen** im normalisierten Text steht und mindestens 15 Zeichen lang ist (`MIN_QUOTE_LENGTH`; ein kürzeres Zitat wie „S3“ beweist nichts). **Ohne Leerzeichen**, weil pypdf im SDM-PDF Wörter zerteilt („Protokollie rung“, M60.S06). Preis: Ein Treffer darf über Wortgrenzen gehen; die Zeichenfolge muss trotzdem lückenlos stimmen. `gates.is_quoted` ergänzt: Ist der ganze Text kürzer als 15 Zeichen (SDM `M60.P03`: „Löschkonzept“), muss das Zitat den **ganzen** Text umfassen.

Dieselbe Funktion prüft zur Laufzeit den **Beleg** eines Befunds in der Eingabe des Nutzers. Build und Laufzeit teilen den Mechanismus: „Zitat statt Behauptung“.

## Lücken sichtbar machen statt verschweigen

Ein Gate prüft nur so weit, wie seine Referenz reicht (ADR 0013). Wo die Referenz endet, zählt der Qualitätsbericht die Lücke (`unjudged_properties`), statt sie als sauber zu verbuchen. Zugleich begrenzt der Code die Regeln auf den Prüfumfang, damit das Gate überall greift.

## Fachbegriffe

- **Deterministische Gegenprobe:** Code prüft die LLM-Ausgabe gegen eine feste Quelle; gleiche Eingabe, gleiches Urteil.
- **Fail closed:** im Zweifel abbrechen.
- **Stille Lücke vs. sichtbare Lücke:** Was nicht geprüft werden kann, darf nicht als bestanden zählen.
- **Zirkulärer Test:** ein Test, dessen Soll aus dem getesteten System stammt; GovGuard vermeidet das durch handgesetzte Presets.

## Fragen für das Fachgespräch

1. Nennen Sie drei Dinge, die das LLM erfinden könnte, und die Gegenprobe dazu.
2. Warum gibt es Validator und Gate?
3. Warum vergleicht `contains_quote()` ohne Leerzeichen, und was ist der Preis?
