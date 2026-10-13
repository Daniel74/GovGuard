# 05 – Bounded Catalog: Der Code wählt aus

## Zweck

Aus den Urteilen des LLM macht der Code den **Bounded Catalog**: die Auswahlliste aller prüfbaren und relevanten Anforderungen, ohne Obergrenze. Dazu schreibt er das **Auswahlprotokoll**: für **jede** Anforderung jeder Quelle ein Ergebnis mit Begründung. Das Protokoll ist der Kontrollpunkt, den ein Mensch liest, bevor Prüfregeln formuliert werden. Code: `select/curation.py`, `gates.py`, `select/run.py`. Befehl: `python -m kb_build select [--audit-type spec|architecture]`.

## Die Entscheidung je Anforderung (`curation._decide`)

Reihenfolge, die erste zutreffende gewinnt:

| Ergebnis (`Outcome`) | Wann | Begründung |
|---|---|---|
| `prefiltered` | Vorfilter hat verworfen | fester Satz des Vorfilters (Kapitel 02) |
| `llm_error` | Antwort blieb ungültig | fester Satz: „Die Antwort des Modells blieb auch nach zwei Wiederholungen ungültig.“ |
| `not_testable` | LLM: nicht prüfbar | Begründung des LLM |
| `not_relevant` | nur Architektur: Ebene ≠ `template`, oder kein Typ im Prüfumfang übrig | fester Satz des Codes |
| `selected` | alles andere | Begründung des LLM |

Feste Sätze für die Ebene (`LEVEL_SENTENCES`): „Die Pflicht liegt beim Konto oder der Organisation, nicht am Template.“ (account), „… bei Personen oder Prozessen …“ (people), „… beim Cloud-Anbieter …“ (provider). Und „Kein Ressourcentyp der Anforderung liegt im Prüfumfang.“, wenn Stufe ② alle Typen gestrichen hat.

**Relevant** heißt (ADR 0013): Nach dem Streichen der Typen außerhalb des Prüfumfangs bleibt mindestens einer übrig, und die Ebene ist `template`. Bei **Spec** gibt es keine Relevanzprüfung und keine Typen.

## Die Dateien

- `data/intermediate/verdicts_arch.json`, `verdicts_spec.json`: das **Auswahlprotokoll** (`Verdict`: Quelle, ID, Titel, Ergebnis, Begründung, Typen). Jede Anforderung genau einmal, in Quellreihenfolge.
- `data/intermediate/selection_arch.json`, `selection_spec.json`: die **Auswahlliste** (`Selection`: Audit-Art, `model_id`, die aufgenommenen Anforderungen mit Begründung und Typen). Sie ist versioniert im Repo; zwischen zwei Builds zeigt `git diff`, was sich geändert hat.
- Beide werden erst nach erfolgreichem Lauf geschrieben (`select/run.py:_select`).

## Die zwei Gates (`kb_build/gates.py`)

Ein Gate stoppt den Build mit `ValueError`, statt eine Lücke auszuliefern.

1. **Pflichtanker-Gate** (`check_pinned`): Jeder Pflichtanker der Presets muss gefunden und `selected` sein. Fehlt ein Anker in den Quellen oder hat er ein anderes Ergebnis (z. B. `not_relevant`), bricht der Build ab und nennt Anker und Ergebnis. Das Gate läuft **zuerst** (fail fast, `_pinned_outcomes`): Erst werden nur die Pflichtanker entschieden, danach die übrigen rund 800 Anforderungen bezahlt.
2. **Abdeckungs-Gate** (`check_coverage`, nur Architektur): Jede Komponente der Archetypen (Kapitel 03) braucht mindestens eine ausgewählte Anforderung. Ein Typ zählt **an jeder Stelle** der Typliste, nicht nur vorn, wie das Pruning zur Laufzeit: Dort geht eine Regel an das Modell, sobald einer ihrer Typen im Template steht (ADR 0007).

## Vom ersten Entwurf zum Heute (Lehrstück)

- **ADR 0002 (überholt):** feste Obergrenze, z. B. 12 BSI + 12 CIS; Ranking reihum je Gruppe; gesetzte Plätze für Preset-Anker (ADR 0007).
- **Befund 09.10./11.10.2026:** Der erste Lauf füllte nur 20 von 24 Plätzen im Architektur-Katalog und deckte kein API Gateway, Lambda, DynamoDB, SQS oder Firehose ab. Im Spec-Katalog lagen Art. 32, 17, 30, 33, 35 über der Grenze, Art. 27 und 47 dagegen drin, weil innerhalb eines Kapitels die ID entschied.
- **ADR 0011 (heute):** keine Obergrenze, kein Ranking, kein gesetzter Platz. Das Ziel: GovGuard soll auch Spezifikationen und Architekturen prüfen, die keinem Archetyp ähneln. Die Gates ersetzen die künstliche Begrenzung.

## Eigenschaften und Garantien

- **Vollständig und nachvollziehbar:** Jede Anforderung hat genau ein Ergebnis mit Begründung. Die Gates sichern Pflichtanker und Komponenten.
- **Reproduzierbarkeit durch Cache:** Der zweite Lauf stellt keine LLM-Anfrage; ein geänderter Text, Prompt oder anderes Modell wird neu gefragt.
- **Teilausfall bricht nicht alles:** Ein `llm_error` schließt nur diese Anforderung aus (Test `test_one_unusable_answer_excludes_that_requirement_but_not_the_whole_run`).
- **Kein Ranking, keine Obergrenze** (Test `test_there_is_no_cap_every_testable_relevant_requirement_is_selected`).

## Beispiele (echte Daten)

`selected`: BSI `ARCH.2.2` „Einschränkung von Verbindungen zwischen Segmenten“, Typen `AWS::EC2::SecurityGroup`, `AWS::EC2::NetworkAcl`, `AWS::EC2::VPC`, `AWS::EC2::Subnet`, `AWS::EC2::RouteTable`.

`not_relevant` (Ebene): CIS `4.4` „server access logging on the CloudTrail S3 bucket“ → „Die Pflicht liegt beim Konto oder der Organisation, nicht am Template.“ Und C5 `OPS-16.01B` → „… bei Personen oder Prozessen …“. Beide verursachten vor Issue #18 dauerhaft falsche Befunde (WARN bei jedem Bucket, FAIL bei jeder Lambda-Rolle).

`not_testable`: BSI `BES.1.1` „Verfahren und Regelungen“ (Beschaffungsprozesse). `prefiltered`: BSI `GC.1.1`. `llm_error`: BSI `BER.6.4`.

## Zahlen (Stand 13.10.2026)

| Katalog | Anforderungen im Protokoll | aufgenommen |
|---|---|---|
| Architektur (BSI, C5, CIS, FSBP) | 1.966 | **166** (BSI 34, C5 6, CIS 20, FSBP 106) |
| Spec (DSGVO, SDM) | 246 | **151** (DSGVO 35, SDM 116) |

Architektur-Protokoll: 1.082 vorgefiltert, 707 nicht prüfbar, 9 nicht relevant, 2 `llm_error`, 166 ausgewählt. Spec: 53 vorgefiltert, 42 nicht prüfbar, 151 ausgewählt.

## Fachbegriffe

- **Bounded Catalog:** feste, vollständig bewertete Menge Prüfregeln (kein Top-K-Retrieval).
- **Auswahlprotokoll / Auswahlliste:** Protokoll = alle Anforderungen mit Ergebnis; Liste = nur die aufgenommenen.
- **Fail fast:** das billigste Gate zuerst, damit ein Fehler früh und günstig auffällt.
- **Fail closed:** im Zweifel abbrechen, nicht still durchlassen.
- **Kontrollpunkt:** Stelle, an der ein Mensch das Zwischenergebnis liest, bevor weitergebaut wird.

## Grenzen

- Die Auswahl ändert sich zwischen Läufen (siehe Kapitel 04); `git diff` macht das sichtbar.
- Hat eine Anforderung mehrere Dienste, entschied früher die vom LLM gewählte Reihenfolge (z. B. CIS 4.10: CloudFront vor API Gateway). Seit ADR 0013 genügt ein übrig gebliebener Typ im Prüfumfang; die Ebene (`scope_level`) fängt Konto-Pflichten ab.
- Dubletten über Quellen bleiben getrennte Befunde, denn jede Prüfregel hat genau einen Primäranker.

## Fragen für das Fachgespräch

1. Warum gibt es keine Obergrenze mehr, und was ersetzt sie?
2. Was bedeutet „Das LLM urteilt, der Code wählt aus“ konkret an einem Beispiel?
3. Welche zwei Gates gibt es, und was passiert, wenn sie nicht erfüllt sind?
