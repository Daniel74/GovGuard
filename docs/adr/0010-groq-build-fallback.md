# 0010 – Groq als zeitlich begrenzter Build-Fallback

_Weicht für den Build von [ADR 0001](0001-eu-inferenzprofil.md) ab._

## Kontext

Das Bedrock-Konto des Kurses erlaubt Anthropic-Modelle noch nicht: Der Rolle `Student` fehlen die AWS-Marketplace-Rechte für das Modell-Abonnement. Ohne LLM lässt sich die Auswahlliste (#6) nicht erzeugen, und die Projektzeit ist knapp.

## Entscheidung

- `python -m kb_build select --provider groq` nutzt Groq (Standard `openai/gpt-oss-120b`, per `GROQ_MODEL` änderbar). Ohne Flag bleibt Bedrock der Standard.
- Groq gilt nur im Build, nie im Lambda. Es gehen ausschließlich öffentliche Normtexte raus, keine Eingaben von Nutzern.
- Kein automatisches Umschalten: Wer Groq will, sagt es ausdrücklich, denn sonst verließen Daten unbemerkt die EU.
- Nur `kb_build/groq_services.py` importiert Groq (Test). Die Abhängigkeit liegt in der Gruppe `build`. Das Modell steht als `model_id` in der Auswahlliste.

## Konsequenzen

- Ausnahme von „Inferenz nur in der EU“; sie endet, sobald Bedrock läuft. Dann löschen wir `groq_services.py`, die Abhängigkeit und diesen ADR.
- Der CIS-Volltext ist lizenziert (ADR 0008) und geht beim Lauf an einen weiteren Dienstleister. Das nehmen wir für den einmaligen Lauf in Kauf.
- Der Schlüssel `GROQ_API_KEY` bleibt in der eigenen Shell, nie im Repo.
- Erzwungene Tools auf Groq sind nicht dokumentiert. Der erste echte Lauf zeigt, ob `tool_choice` greift.

## Fachgespräch-Satz

„Groq ist eine bewusst gewählte, dokumentierte Ausnahme nur für den Build mit öffentlichen Normtexten; die Laufzeit mit Nutzereingaben bleibt in der EU auf Bedrock.“
