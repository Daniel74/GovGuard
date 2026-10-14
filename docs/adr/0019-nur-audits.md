# 0019 – Scope-Schnitt: nur Audits, keine Golden Archetypes

_Ersetzt in [ADR 0009](0009-end-to-end-archetypen.md) und [ADR 0003](0003-cdk-solutions-constructs.md) Bau und Auswahl der Archetypen. Betrifft #7 und #10._

## Kontext

- Bis zur Präsentation am 26.10.2026 bleiben 12 Tage, #26, #27, #28, #9 und #11 sind offen. Die Archetypen hatten schon Priorität B (FAHRPLAN).
- Die Generierung braucht CDK-Code vom LLM, `cdk synth` und eine Freigabe-Schleife (#7). `/archetype/select` (#10) ist nur sinnvoll, wenn es freigegebene Archetypen gibt.
- Das Abdeckungs-Gate (ADR 0011) liest die Komponenten aus den Steckbriefen in `archetype_profiles.json`.

## Entscheidung

- GovGuard auditiert Spezifikationen und Architekturen. Golden Archetypes werden weder gebaut noch ausgewählt: Build-Schritt 6, `cdk_runner.py`, `archetypes.json` und `POST /archetype/select` entfallen.
- Die Steckbriefe bleiben, aber nur als Eingabe des Abdeckungs-Gates: Jede dort genannte Komponente braucht mindestens eine Prüfregel.
- Das Feld `archetype` in den Presets bleibt stehen, wird aber nicht geprüft.

## Konsequenzen

- Die API hat zwei Endpunkte. Die UI zeigt nur den Audit-Report.
- cdk-nag läuft nur noch für den eigenen Stack (Selbst-Audit). Die Ausnahmen der Archetypen (IAM4, IAM5) werden nicht gebraucht.
- #7 und #10 werden Ausbau. Steckbriefe, ADR 0003 und 0009 belegen im Fachgespräch, wie der Schritt aussähe.

## Fachgespräch-Satz

„Ich habe den Kern fertig gebaut statt die Kür halb: GovGuard prüft Spezifikationen und Architekturen vollständig und nachvollziehbar, die Archetypen sind entworfen, aber bewusst nicht gebaut.“
