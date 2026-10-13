# 04 – Auswahl, Stufe ②: Das LLM urteilt

## Zweck

Nach dem Vorfilter bleiben Anforderungen übrig, die ein Mensch erst lesen müsste. Stufe ② fragt das LLM **je Anforderung einzeln**: Ist sie an einer Spezifikation bzw. einem CloudFormation-Template prüfbar? Bei Architektur zusätzlich: Wessen Pflicht ist das, und welche Ressourcentypen betrifft sie? Das LLM zählt und wählt nicht aus. Code: `select/classify.py`.

## Ablauf pro Anforderung

1. Der Code baut den Prompt der Audit-Art (`PROMPTS["architecture"]` oder `PROMPTS["spec"]`). Bei Architektur hängt `SCOPE_PROMPT` die Dienste des Prüfumfangs an.
2. Die User-Nachricht enthält Quelle, ID, Titel und den Text in `<anforderung>…</anforderung>`.
3. Ein Pydantic-AI-`Agent` erzwingt das Tool `classify_requirement` (Tool-Choice) mit dem Schema `Classification`.
4. Ein **Output-Validator** bereinigt oder verwirft die Antwort (siehe unten).
5. Der `Judge` schaut vor dem Aufruf in den **Cache**; eine bekannte Antwort kostet nichts.

## Die Antwort des LLM (`select/models.py:Classification`)

| Feld | Bedeutung |
|---|---|
| `testable` | prüfbar ja oder nein |
| `rationale` | ein deutscher Satz Begründung |
| `scope_level` | wessen Pflicht: `template`, `account`, `people`, `provider` (nur Architektur) |
| `cfn_resource_types` | betroffene CloudFormation-Typen, der wichtigste zuerst (nur Architektur) |

## Die Ebene (`scope_level`, Issue #18)

Prüfbar und relevant reichen nicht, wenn die Pflicht jemand anderem gehört:

- `template`: das Workload selbst, am Template erkennbar (Bucket, Rolle, Funktion).
- `account`: Konto oder Organisation (CloudTrail-Bucket, Passwort-Richtlinie, Root-MFA).
- `people`: Personen und Prozesse (MFA für Administratoren, Schulung, Verträge).
- `provider`: Cloud-Anbieter (Rechenzentrum, Hypervisor).

Der Prompt grenzt ab: Gilt eine Pflicht zugleich für jede Ressource des Workloads (Block Public Access an jedem Bucket), wählt das Modell `template`, auch wenn es dafür eine Konto-Ressource (`AWS::S3::AccountPublicAccessBlock`) gibt. Das ist die Folge einer Korrektur im echten Lauf (Issue #19): Ohne diesen Satz wurde CIS 3.1.4 als `account` eingestuft und das Pflichtanker-Gate brach ab. Das Modell sagt nur die Ebene; die Konsequenz (`not_relevant`) zieht der Code (Kapitel 05). Fachlich ist das das **Shared Responsibility Model** von AWS: Anbieter, Konto und Workload tragen verschiedene Pflichten, GovGuard prüft die Workload-Schicht.

## Der Output-Validator (`_validate`)

Drei Zweige, in dieser Reihenfolge:

1. **Spec:** Der Code erzwingt `cfn_resource_types = []` und `scope_level = "template"`. Die Ebene gilt für Spec nicht.
2. **Nicht prüfbar:** Der Code leert die Typliste.
3. **Architektur prüfbar:** Nur echte Typen (`load_cfn_types`) bleiben. Ist **kein** echter Typ übrig, geht die Antwort per `ModelRetry` zurück („Eine prüfbare Architektur-Anforderung braucht mindestens einen echten CloudFormation-Typ“). Sind nur **einzelne** Typen erfunden und ein echter bleibt, **verwirft der Code die erfundenen ohne Retry** (spart Aufrufe; Fall CIS 3.1.4 mit `AWS::S3::BucketPublicAccessBlock`). Danach streicht der Code alle Typen **außerhalb des Prüfumfangs** (`Scope.outside`), ebenfalls ohne Retry (ADR 0013).

Einstellungen: `temperature: 0` (gleiche Eingabe, möglichst gleiche Auswahl) und `retries=2`. Im Build gilt kein 29-Sekunden-Limit; die Laufzeit-Agenten bleiben bei einem Retry (ADR 0005).

## Der Cache (`select/judgement_cache.py`)

- Schlüssel: `<SHA-256 von Titel+Text>|<Prompt-Version>|<model_id>`.
- **Prompt-Version** (`request_version()`): 12 Zeichen eines Hashs über alles, was das Modell außer der Anforderung sieht: Anweisungen, User-Nachricht, Tool-Name, Tool-Beschreibung, das JSON-Schema von `Classification` und die **Typen des Prüfumfangs**. Ändert sich einer dieser Teile, ändert sich der Schlüssel, und alles wird neu bezahlt. Ein neuer Typ eines bekannten Dienstes zählt (ADR 0013, Test `test_a_new_type_of_a_known_service_changes_the_prompt_version`). Beim Spec-Prompt bleibt die Version vom Prüfumfang unberührt.
- Folge: Der zweite Lauf ohne Änderung stellt **keine** LLM-Anfrage (Test `test_the_second_run_asks_the_llm_nothing`).
- Die Datei wird sortiert geschrieben (`to_json()`), damit der Git-Diff lesbar ist, und auch dann gespeichert, wenn ein Gate den Lauf abbricht: Die Antworten sind schon bezahlt (`select/run.py:select_all`, `try … finally`).
- Eine ungültige Antwort wird **nicht** gecacht.

## Fehlerbehandlung im `Judge`

Bleibt eine Antwort nach den Retries ungültig (`UnexpectedModelBehavior`) oder lehnt der Dienst die Generierung mit HTTP 400 ab, gibt der `Judge` `None` zurück: Ergebnis `llm_error`, der Lauf geht weiter. Andere HTTP-Fehler (401, 429, Serverfehler) sind kein Urteil über die Anforderung und **brechen den Lauf ab**. Die Token aller Aufrufe, auch gescheiterter Retries, summiert `Judge.usage`.

## Beispiel

Eintrag im Cache (Auszug, `judgement_cache.json`):

```json
{ "testable": false,
  "rationale": "Die Anforderung bezieht sich auf Prozesse und Vorgaben zum Schwachstellenscan und ist nicht aus der Konfiguration einzelner CloudFormation‑Ressourcen ableitbar.",
  "scope_level": "people", "cfn_resource_types": [] }
```

Der Cache hat 4.363 Einträge (Stand 13.10.2026), weil er auch Antworten älterer Prompt-Versionen behält.

## Warum so

- **Stufe ② urteilt, der Code zählt** (ADR 0011): Das LLM sieht eine Anforderung, nie die ganze Liste, und kann so keine Regeln erfinden oder aussortieren.
- **Prompt für Spec** (ADR 0011, Issue #6): Eine Spezifikation ist die **fachliche** Beschreibung eines Vorhabens, nicht nur die technische. Zuerst argumentierten 44 von 72 „nicht prüfbar“-Urteilen mit „keine technische Spezifikation“; nach der Prompt-Korrektur 11 von 42.

## Fachbegriffe

- **Tool-Choice:** Die API erzwingt, dass das Modell ein bestimmtes Tool mit festem Schema aufruft; die Antwort ist strukturiert statt Freitext.
- **Output-Validator / `ModelRetry`:** Code prüft die Antwort sofort und schickt einen Fehler an das Modell zurück, damit es einmal korrigiert.
- **Cache-Schlüssel mit Prompt-Version:** gleicher Text, gleicher Prompt, gleiches Modell ergibt dieselbe Antwort ohne neuen Aufruf.
- **Temperatur 0:** möglichst wenig Zufall, aber nicht garantiert deterministisch.

## Grenzen

- **Das LLM urteilt nicht stabil.** Trotz Temperatur 0 kippten im zweiten Lauf (11.10.2026) 41 von 1.077 Urteilen (ADR 0011). Bei Groq tauscht ein Neulauf rund 10 % der Auswahl aus (ADR 0014, Issue #19). Der Cache friert die Urteile ein; Sicherheit geben die Gates, nicht das Modell.
- **Spec-Grenze Vorhaben/Betrieb:** Das LLM trennt SDM-Ebene P (Prozesse) nicht stabil; ein Prompt-Versuch verwarf auch Art. 35. Im Zweifel nimmt der Build auf (ein unnötiger WARN ist sichtbar, eine verlorene Anforderung nicht).
- **Uneinheitliches Protokoll:** Viele Konto- und Personenpflichten landen als `not_testable` mit LLM-Begründung statt als `not_relevant` mit festem Satz. Draußen sind sie in beiden Fällen (Issue #18).
- **Einzelne Fehlurteile**, z. B. C5 CRY-07.01B (Schlüsselrotation) als „nicht prüfbar“.

## Fragen für das Fachgespräch

1. Warum bekommt das LLM jede Anforderung einzeln?
2. Warum steht die Prompt-Version im Cache-Schlüssel, und was gehört hinein?
3. Was ist der Unterschied zwischen „nicht prüfbar“ und „nicht relevant“?
