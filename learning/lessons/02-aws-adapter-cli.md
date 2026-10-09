# #2 aws_services: Bedrock-Modell + CLI-Audit

## Was es tut
`bedrock_model()` baut das Pydantic-AI-Modell für Claude Haiku 4.5 über das EU-Profil in Frankfurt. Die CLI liest Datei und Katalog, bildet den `Trace` (nur Hashes) und ruft `run_audit()` mit diesem Modell auf. Bei ungültiger LLM-Antwort gibt sie nichts aus und endet mit Exit 2.
`Datei + Katalog → Trace (SHA-256) → bedrock_model() → run_audit() → AuditReport als JSON`

## Wo im Code
- [aws_services.py](../../src/govguard/aws_services.py): einziger Ort mit boto3 und Bedrock-Modell; keine Prüflogik.
- [cli.py](../../src/govguard/cli.py): Einstieg, der Datei, Modell und `run_audit()` nur verbindet.
- [test_aws_services.py](../../tests/test_aws_services.py): Stubber-Test belegt, dass der Request `toolChoice` enthält.

## Entscheidung und Warum
- **EU-Profil `eu.` statt `global.`:** Daten liegen in eu-central-1, die Inferenz verlässt die EU nie. Damit gibt es keinen Drittlandtransfer (DSGVO Art. 44, ADR 0001).
- **Tool-Choice per Test festnageln:** Ob Pydantic AI `any` oder `auto` sendet, hängt am Modellprofil (`bedrock_supports_tool_choice`). Ändert ein Update oder eine neue Modell-ID das Profil, fällt es still auf `auto` zurück. Der Stubber-Test prüft deshalb den Wert `{"any": {}}`, sonst käme unbemerkt Freitext statt strukturierter Befunde.

## Prüfungsbegriffe
- **Adapter**: Die dünne Schicht, in der alle I/O liegt (boto3); die Prüflogik bleibt rein und ohne AWS testbar.
- **Tool-Choice (`toolChoice: any`)**: Das Modell muss das Formular-Tool aufrufen und kann nur schema-konformes JSON liefern.
- **Cross-Region-Inferenzprofil**: Ein Profil-Präfix (`eu.`) wählt aus, in welchen Regionen Bedrock rechnen darf.

## Merksatz
„Die Daten liegen in Frankfurt, die Inferenz bleibt in der EU, und ein Test beweist, dass das Modell strukturiert antworten muss und nicht frei reden darf.“

## Abruffragen
1. Warum steht boto3 nur in `aws_services.py`, und was gewinnt man dadurch?
2. Was bedeutet das Präfix `eu.` in der Modell-ID, und welchen DSGVO-Punkt sichert es?
3. Wogegen schützt der Stubber-Test mit `toolChoice`, und was würde sonst passieren?
