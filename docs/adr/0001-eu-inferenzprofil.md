# 0001 – EU-Inferenzprofil statt „nur Frankfurt“

## Kontext

Die Leitplanke lautete „nur eu-central-1“. Stand 2026-10-08 ist kein aktuelles Claude-Modell in Frankfurt direkt (in-region) aufrufbar, sondern nur über Cross-Region-Inferenzprofile. Das Profil `eu.` verarbeitet in eu-central-1, eu-north-1, eu-south-1, eu-south-2, eu-west-1 und eu-west-3; das Profil `global.` weltweit.

## Entscheidung

- Bedrock wird aus eu-central-1 über das Profil `eu.` aufgerufen (Claude Haiku 4.5, unterstützt erzwungene Tool-Nutzung).
- Persistente Daten liegen ausschließlich in eu-central-1.
- `global.`-Profile werden per IAM-Policy gesperrt.

## Konsequenzen

- Die Leitplanke lautet neu: „Daten in eu-central-1, Inferenz nur in der EU“.
- Bedrock speichert Ein- und Ausgaben standardmäßig nicht; CloudTrail protokolliert die tatsächliche Verarbeitungsregion (`inferenceRegion`).
- Geo-Profile kosten ca. 10 % mehr als `global.` – bei Audits im einstelligen Cent-Bereich vernachlässigbar.

## Fachgespräch-Satz

„Die Daten liegen in Frankfurt, die Inferenz verlässt die EU nie – damit liegt kein Drittlandtransfer nach Art. 44 DSGVO vor, und ich kann die Region pro Aufruf per CloudTrail nachweisen.“
