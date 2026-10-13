# 00 – Übersicht: Was kb-build tut

## Zweck

`kb_build` erzeugt aus sechs öffentlichen Regelwerken die **Wissensbasis** von GovGuard: zwei JSON-Dateien mit **Prüfregeln**, `rules_spec.json` (für Spezifikationen) und `rules_arch.json` (für Architekturen). Jede Prüfregel stammt aus genau einer **Anforderung** einer Quelle, trägt ein wörtliches Zitat und sagt, woran man Einhaltung und Verstoß erkennt. Zur Laufzeit liest die Audit-Engine diese Dateien und bewertet jede Eingabe gegen alle anwendbaren Regeln.

Der Build läuft nur manuell (Quelle, Prompt oder Modell haben sich geändert), nicht bei jedem Audit. Er verarbeitet nur **öffentliche Normtexte**, nie Nutzereingaben (ADR 0014).

## Ablauf in vier Befehlen

```
python -m kb_build extract          Rohdateien laden, Anforderungen zerlegen, vorfiltern   (kein LLM)
python -m kb_build select           LLM urteilt „prüfbar?“, Code wählt aus + Gates          (LLM)
python -m kb_build rules            LLM formuliert Prüfregeln, Gate prüft alles             (LLM)
python -m kb_build cfn-properties   Schnappschuss der echten CloudFormation-Eigenschaften   (Handbefehl, kein LLM)
```

Datenfluss (Ordner nach Herkunft, `kb_build/paths.py`):

```
data/input/sources.json ──► extract ──► data/intermediate/extracted/*.json   (6 Dateien)
data/input/scope.json,        │
archetype_profiles.json,      ▼
presets/                   select ──► data/intermediate/verdicts_*.json     (Auswahlprotokoll)
                                      data/intermediate/selection_*.json    (Auswahlliste)
                                      data/intermediate/judgement_cache.json
cfn_properties.json,          │
cfn_resource_types.json       ▼
                           rules ──► data/knowledge_base/rules_arch.json, rules_spec.json
```

Nur `data/knowledge_base/rules_*.json` ist das Endergebnis und geht später nach S3. Alles andere ist Eingabe oder Zwischenergebnis, eingecheckt fürs Review (außer den lizenzierten Volltexten).

## Die Grundidee: LLM und Code teilen sich die Arbeit

Testfrage für jede Aufgabe (ARCHITECTURE): **Gibt es genau eine richtige Antwort, die sich ohne Sprachverständnis ermitteln lässt?** Ja: Code. Nein: LLM, und danach prüft der Code das Ergebnis. Das LLM sitzt immer zwischen zwei Code-Schichten.

| Schritt | Code (deterministisch) | LLM (probabilistisch) |
|---|---|---|
| Extraktion | laden, Hash prüfen, zerlegen, Vorfilter | – |
| Auswahl | Relevanz, Aufnahme, Gates, Cache | „Ist die Anforderung prüfbar? Wessen Pflicht? Welche Ressourcentypen?“ |
| Prüfregeln | Identität (`id`, `source`, `primary_anchor`), Zitat-Check, Gate | Titel, Kriterien, Empfehlung, Zitat auswählen |

Leitsatz aus ADR 0011: **„Das LLM urteilt, der Code wählt aus.“**

## Die zwei Audit-Arten

- **Spec-Audit:** prüft eine fachliche Spezifikation (Freitext oder OpenAPI) gegen DSGVO und SDM (Standard-Datenschutzmodell). Quellen: `DSGVO`, `SDM`.
- **Architektur-Audit:** prüft ein CloudFormation- oder Terraform-Template gegen BSI Grundschutz++, BSI C5, CIS AWS v7 und AWS FSBP (Foundational Security Best Practices). Quellen: `BSI`, `C5`, `CIS`, `FSBP`. Festgelegt in `select/run.py:SELECTIONS`.

## Stand der Pipeline (13.10.2026)

| Schritt | Ticket | Stand |
|---|---|---|
| Extraktion DSGVO, SDM, BSI, CIS, FSBP, C5 | #4, #5, #13 | fertig |
| Auswahl mit Auswahlprotokoll, Cache, Gates | #6, #18, #19 | fertig |
| Prüfregeln und Gates | #12, #17, #19 | fertig |
| Ordnerstruktur, Groq als Standard | #20, #21 | fertig |
| Preset-Gate, Workflow `build-kb.yml` | #8 | **noch nicht gebaut** |
| Golden Archetypes (`cdk_runner.py`) | #7 | **noch nicht gebaut** (Priorität B) |

## Fachbegriffe

- **Wissensbasis** (`knowledge_base`): alle Prüfregeln, später auch die Golden Archetypes.
- **Anforderung** (`Requirement`): einzelne zitierfähige Vorgabe einer Quelle, z. B. BSI `DET.3.1`, DSGVO `Art. 32`.
- **Prüfregel** (`Rule`): atomare prüfbare Regel aus genau einer Anforderung.
- **Bounded Catalog** (`catalog`): feste Menge aller prüfbaren und relevanten Prüfregeln je Audit-Art, die in jedem Audit vollständig bewertet wird. Keine Suche, keine Vektor-Datenbank (ADR 0002, 0011).
- **Gate:** automatischer Prüfpunkt im Build, an dem Code das LLM kontrolliert; Fehler bricht den Build ab, die alte Wissensbasis bleibt (**fail closed**).
- **Draft-Pattern:** das LLM füllt nur ein `*Draft`-Modell, der Code ergänzt, was er schon weiß (`govguard/models.py`).

## Fragen für das Fachgespräch

1. Wie entscheiden Sie, was das LLM macht und was der Code?
2. Warum gibt es keine Vektor-Datenbank?
3. Was passiert, wenn ein Gate durchfällt?
