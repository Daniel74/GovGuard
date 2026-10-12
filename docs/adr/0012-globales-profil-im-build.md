# 0012 – Globales Bedrock-Profil als Build-Option

_Weicht für den Build von [ADR 0001](0001-eu-inferenzprofil.md) ab._

## Kontext

Am 12.10.2026 brach das Formulieren der Prüfregeln (#12) dreimal mit HTTP 503 ab: Bedrock hatte für Haiku 4.5 über das Profil `eu.` keine Kapazität frei, auch nach 4 Wiederholungen von botocore. Das Kontingent (50 Anfragen pro Minute) war nicht erreicht. Das Profil `global.` antwortete. Ein Abbruch kostet den ganzen Lauf, denn geschrieben wird erst nach dem Gate.

## Entscheidung

- `python -m kb_build … --provider bedrock-global` nutzt das Profil `global.anthropic.claude-haiku-4-5-…`. Standard bleibt `eu.`.
- Das gilt nur im Build, nie im Lambda. Dort gehen nur öffentliche Normtexte raus, keine Eingaben von Nutzern.
- Kein automatisches Umschalten: Wer `global.` will, sagt es ausdrücklich (wie bei Groq, ADR 0010).
- Nur `aws_services.py` kennt die Modell-ID (`GLOBAL_MODEL_ID`). Die genutzte ID steht als `model_id` im Katalog.

## Konsequenzen

- Die Inferenz im Build kann außerhalb der EU laufen. GovGuard ist ein Prototyp ohne echte Daten, und Normtexte sind öffentlich.
- Der CIS-Volltext (lizenziert, ADR 0008) kann dabei die EU verlassen. Das nehmen wir wie bei Groq in Kauf.
- `model_id` im Katalog zeigt, ob ein Lauf mit `global.` erzeugt wurde.

## Fachgespräch-Satz

„Die Laufzeit mit Nutzereingaben bleibt in der EU; nur öffentliche Normtexte dürfen im Build ausdrücklich über das globale Profil laufen, wenn das EU-Profil keine Kapazität hat.“
