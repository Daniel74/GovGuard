# 0016 – Groq als ausdrückliche Laufzeit-Option im Prototyp

_Weicht für die Laufzeit von [ADR 0001](0001-eu-inferenzprofil.md) ab. Ergänzt [ADR 0004](0004-streamlit-community-cloud.md) und [ADR 0014](0014-groq-standard-im-build.md). Umsetzung: #26._

## Kontext

- Haiku 4.5 über `eu.` kostet für das größte Preset ca. 0,90 $ je Audit (Messung 14.10.2026, #14). Groq `openai/gpt-oss-120b` kostet etwa ein Zehntel.
- GovGuard ist ein Prototyp mit fiktiven Presets. Eingaben verlassen die EU ohnehin schon über die Demo-UI auf Streamlit Community Cloud (ADR 0004). Die UI bittet, keine echten Daten einzugeben.
- Eine Behörde würde echte Daten erst nach einem eigenen Aufbau einpflegen (Konto, Netz, Freigaben). Dabei wird der Provider neu entschieden.
- Bedrock `eu.` hatte im Build schon keine Kapazität frei (ADR 0012).

## Entscheidung

- Bedrock `eu.` bleibt Standard für Audits. Groq ist eine ausdrückliche Option der Laufzeit-Konfiguration, z. B. bei fehlender Kapazität oder für günstige Messläufe. Es gibt kein stilles Umschalten.
- `model_id` im Audit-Report und im Audit-Ereignis zeigt, ob ein Audit über Groq lief.
- Die Gates gelten für beide Modelle gleich: Beleg, genau ein Befund je Prüfregel, fail closed.
- Für echte Daten gilt wieder ADR 0001: Groq aus, Inferenz nur in der EU.

## Konsequenzen

- Mit Groq gehen Eingaben zur Inferenz in die USA (Drittlandtransfer, Art. 44 DSGVO). Für den Prototyp ohne echte Daten akzeptiert. „Nur fiktive Daten“ lässt sich technisch nicht erzwingen (wie ADR 0004).
- Der Groq-Adapter liegt heute in `kb_build/`, die Abhängigkeit in der Gruppe `build`. Für die Laufzeit müssen beide ins Lambda-Paket (`src/govguard`). `GROQ_API_KEY` braucht einen Platz im Stack (#9, Weiche Verschlüsselung).
- Der Weg für Belege (#26) muss mit beiden Modellen funktionieren. Eine reine Bedrock-Funktion wie Citations bräuchte für Groq einen zweiten Weg.

## Fachgespräch-Satz

„Im Prototyp darf ich bewusst auf Groq ausweichen, weil nur fiktive Daten fließen und die UI ohnehin in den USA läuft; Standard bleibt Bedrock in der EU, jeder Report nennt sein Modell, und für echte Behördendaten gilt wieder ‚Inferenz nur in der EU'.“
