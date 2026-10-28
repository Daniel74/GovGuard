# 0016 – Groq als ausdrückliche Laufzeit-Option im Prototyp

_Weicht für die Laufzeit von [ADR 0001](0001-eu-inferenzprofil.md) ab. Ergänzt [ADR 0004](0004-streamlit-community-cloud.md) und [ADR 0014](0014-groq-standard-im-build.md). Umsetzung: #26. Seit [ADR 0023](0023-demo-und-recruiter-stand.md) einziger Provider in UI und Lambda; Bedrock `eu.` nur noch per CLI. **Für echte Daten ersetzt durch [ADR 0029](0029-kein-us-anbieter-fuer-echte-daten.md) (CLOUD Act).**_

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

## Nachtrag 14.10.2026: strukturierte Ausgabe mit Groq (#26, ADR 0017)

- Groq liefert strukturierte Ausgaben über `NativeOutput`: `response_format` mit json_schema und `strict`, also Constrained Decoding. Ein erzwungenes Tool gibt es dafür nicht. Groq kombiniert Structured Outputs nicht mit Tools, und Pydantic AI überträgt `strict` bei Groq-Tools nicht. Für Groq weicht das von ADR 0005 ab. Validator, Retry und fail closed bleiben gleich.
- Im Prototyp gab es mit `NativeOutput` 0 Schema-Retries. Vollständigkeit garantiert das Schema aber nicht: In einem Paket fehlten 5 von 10 Befunden. Das fängt weiter der Validator ab.
- Groq begrenzt den Durchsatz auf 250.000 Tokens pro Minute. Der volle Katalog mit 16 parallelen Paketen braucht ca. 460.000 und läuft daher nur gedrosselt, also in ca. 2 Minuten statt unter 29 s.

## Fachgespräch-Satz

„Im Prototyp darf ich bewusst auf Groq ausweichen, weil nur fiktive Daten fließen und die UI ohnehin in den USA läuft; Standard bleibt Bedrock in der EU, jeder Report nennt sein Modell, und für echte Behördendaten gilt wieder ‚Inferenz nur in der EU'.“
