# #15 5. Preset: fremde Serverless-Architektur

## Was es tut
Der „Fristenwecker im Bauamt“ ist ein fiktives CloudFormation-Template: Step Functions wartet bis zum Fristende und meldet per SNS an die Sachbearbeitung, ohne Lambda und ohne KMS. Es enthält keine Komponente eines Archetyps und belegt so die Behauptung aus ADR 0011, dass GovGuard auch Fremdes auditiert. Soll: Gesamtstatus FAIL, Pflicht-Befunde `AWS FSBP SNS.1` = FAIL und `StepFunctions.1` = PASS, beide von Gemini bestätigt.
`template.json → Ressourceninventar → Lambda-/S3-/API-Regeln N/A → SNS.1 FAIL, StepFunctions.1 PASS → Gesamtstatus FAIL`

## Wo im Code
- [template.json](../../data/input/presets/arch-fristenwecker/template.json): Topic ohne `KmsMasterKeyId`, StateMachine mit `LoggingConfiguration` und Rolle mit `sns:Publish` nur auf das Topic.
- [preset.json](../../data/input/presets/arch-fristenwecker/preset.json): das Soll, von Hand gesetzt.
- [test_pinned_anchors.py](../../tests/test_pinned_anchors.py): Jeder Pflichtanker steht im eingecheckten Katalog. Das prüft das Gate aus #6 ohne `kb_build`-Lauf und ohne lokale Quellen.

## Entscheidung und Warum
- **Ein PASS neben dem FAIL:** Nur FAIL-Anker würden nicht zeigen, ob der Copilot unterscheidet oder bei Unbekanntem pauschal „FAIL“ sagt. `StepFunctions.1` = PASS beweist, dass der fremde Dienst wirklich bewertet wird (Nachweis statt Behauptung, wie im BSI-Audit).
- **Wildcard nur, wo AWS sie erzwingt:** Die Log-Delivery-Aktionen von Step Functions gehen nur auf `"Resource": "*"`. Statt das zu verstecken, steht im Template der Sid `LogDeliveryRequiresWildcard`, also eine begründete Abweichung vom Prinzip der geringsten Berechtigungen (BSI BER.4.1).

## Prüfungsbegriffe
- **Anwendbar**: Eine Prüfregel läuft nur, wenn einer ihrer Ressourcentypen im Template vorkommt; sonst setzt der Code N/A, nicht das LLM.
- **Pflichtanker**: der Primäranker eines Pflicht-Befunds im Preset; er muss im Bounded Catalog stehen, sonst bricht der Build ab.
- **Mutationsprobe**: Man baut absichtlich einen Fehler ein (falscher Anker) und schaut, ob der Test rot wird; nur dann beweist ein grüner Test etwas.

## Merksatz
„Unser fünftes Preset hat keinen einzigen Baustein eines Archetyps, und trotzdem findet GovGuard das unverschlüsselte SNS-Topic und erkennt das korrekte Logging an.“

## Abruffragen
1. Warum hat das fremde Preset neben `SNS.1` = FAIL auch einen Pflicht-Befund mit PASS?
2. Wer setzt bei diesem Template die Lambda- und S3-Regeln auf N/A, und wie heißt der Begriff dafür?
3. Woran erkennst du, dass ein grüner Test wirklich etwas prüft, und wie heißt das Verfahren?
