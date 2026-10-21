# Rechercheauftrag (Gemini Deep Research)

Kontext: Python-Streamlit-App (Demo, fiktive Daten) ruft ein LLM über Groq
(openai/gpt-oss-120b) auf. Ein Audit braucht bis ca. 460.000 Tokens und 1–3 Minuten.
Ziel: 0 € Fixkosten, Kosten je Audit minimal. Bitte nur Primärquellen
(Hersteller-Doku, Preisseiten) und je Aussage Link + Datum.

1. **Groq**: aktuelle Rate Limits (RPM, TPM, TPD) für openai/gpt-oss-120b im Free- und im
   Developer-Tier; Preis je 1 Mio. Input-/Output-Tokens; gibt es ein hartes Ausgabenlimit
   (Spend Limit) in der Konsole?
2. **Streamlit Community Cloud**: RAM/CPU-Grenzen, Schlafverhalten, maximale Laufzeit einer
   Script-Ausführung bzw. WebSocket-Timeouts bei 3 Minuten Rechenzeit, Umgang mit Secrets,
   Serverstandort; private Apps (Anzahl, Zugang per Passwort?).
3. **Alternativen mit EU-Standort und 0 € Leerlauf** für eine Streamlit-App (z. B. Hugging
   Face Spaces, Google Cloud Run, Fly.io, Render): Free-Tier-Grenzen, Kaltstart, Region.
4. **AWS Free Plan für neue Konten (seit Juli 2025)**: Höhe und Laufzeit der Credits, ob
   Amazon Bedrock (Claude Haiku 4.5, Profil eu.) damit bezahlt werden darf, was nach Ablauf
   passiert (Konto geschlossen oder kostenpflichtig?).
