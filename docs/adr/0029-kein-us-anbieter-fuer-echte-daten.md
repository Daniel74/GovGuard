# 0029 – Kein US-Anbieter für echte Daten (CLOUD Act)

_Ersetzt [ADR 0001](0001-eu-inferenzprofil.md) für echte Daten. Ändert [ADR 0016](0016-groq-zur-laufzeit-im-prototyp.md) und [ADR 0023](0023-demo-und-recruiter-stand.md): Bedrock `eu.` und der Recruiter-Stand auf AWS sind kein Weg zu echten Daten mehr. Der Build ([ADR 0012](0012-globales-profil-im-build.md), [ADR 0014](0014-groq-standard-im-build.md)) bleibt, denn er schickt nur öffentliche Normtexte raus._

## Kontext

- ADR 0001 schützt echte Daten über den Ort: Die Inferenz läuft bei Bedrock nur in EU-Regionen. Der US CLOUD Act ist ein US-Gesetz, nach dem US-Behörden von US-Unternehmen Daten verlangen können, auch wenn diese in der EU liegen. Entscheidend ist also, wem der Anbieter gehört, nicht wo sein Rechenzentrum steht.
- Amazon (AWS, Bedrock) und Groq sind US-Unternehmen. Eine EU-Region schützt bei ihnen nicht vor einem Zugriff nach dem CLOUD Act.
- GovGuard nutzt zur Laufzeit GPT-OSS 120B. Dieses offene Modell (Apache 2.0) betreiben auch europäische Anbieter ohne US-Mutterkonzern, alle mit Abrechnung pro Token und einer Schnittstelle wie OpenAI (Recherche in `learning/ihk/uebungen.md`, Punkt 6).

## Entscheidung

- **Echte Daten nur bei EU-Anbietern ohne US-Mutterkonzern.** Das gilt für das Modell und für das Hosting der Oberfläche. AWS ist damit für GovGuard aus dem Scope, auch in `eu-central-1`.
- **Modell bleibt GPT-OSS 120B.** Der Anbieter steht noch nicht fest. Kandidaten sind STACKIT, IONOS, Scaleway und OVHcloud; entschieden wird nach einem Test mit den Musterfällen, nicht nach dem Preis.
- **Demo-Stand unverändert:** Streamlit Community Cloud und Groq bleiben, aber nur mit erfundenen Daten (ADR 0016, 0023).

## Konsequenzen

- Bis ein EU-Anbieter angebunden ist, hat GovGuard keinen Weg für echte Daten. `--provider bedrock` in der Kommandozeile bleibt vorerst im Code, gilt aber nicht mehr als dieser Weg.
- Recruiter-Stand, Lambda, S3 und KMS aus ADR 0023 entfallen als Ausbau. Ein Ausbau entsteht neu beim gewählten EU-Anbieter.
- Ein EU-Anbieter auf Grafikkarten (GPU) braucht für ein Fachkonzept-Audit etwa dreimal so lange wie Groq auf eigenen Chips. Das ist eine Schätzung und wird im Test gemessen.
- Die Architekturprüfung liest weiter CloudFormation-Vorlagen der Behörde. Diese Entscheidung betrifft nur, wo GovGuard selbst läuft.

## Fachgespräch-Satz

„Vor dem CLOUD Act schützt nicht der Standort des Rechenzentrums, sondern nur ein Anbieter ohne US-Mutterkonzern; weil GovGuard ein offenes Modell nutzt, wechsle ich nur den Anbieter, nicht die Prüflogik.“
