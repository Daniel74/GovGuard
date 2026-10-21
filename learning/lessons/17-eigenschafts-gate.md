# #17 Gate gegen erfundene CloudFormation-Eigenschaften

## Was es tut
Ein Schnappschuss aus `aws cloudformation describe-type` hält je Typ des Prüfumfangs alle echten Eigenschaftspfade, auch verschachtelte wie `LoggingConfiguration.LogFilePrefix`. Reiner Code sucht in `compliant_if`/`violation_if` nach Namen, die wie Eigenschaften aussehen, und gleicht sie mit dem Schnappschuss ab. Nennt das LLM eine erfundene Eigenschaft (CIS 4.4: `TargetPrefix`), bekommt es per `ModelRetry` einen zweiten Versuch mit echten Alternativen. Kennen wir einen Typ nicht, zählt der Bericht die Regel als `unjudged_properties`, statt sie still als sauber zu verbuchen.
`describe-type-Schemas → cfn_properties.json → PropertyIndex → Kandidaten im Kriterium → unbekannt? ModelRetry : Regel → Qualitätsbericht`

## Wo im Code
- [cfn_properties.py](../../src/kb_build/reference/cfn_properties.py): Schnappschuss bauen, Kandidaten finden, `unknown_properties`/`unjudged_types` (rein).
- [formulate.py](../../src/kb_build/rules/formulate.py): Validator schickt erfundene Namen mit Alternativen zurück (`retries=3`, nur im Build).
- [quality.py](../../src/kb_build/rules/quality.py): zählt je Quelle `unknown_properties` und `unjudged_properties`.

## Entscheidung und Warum
- **Abgleich gegen eine Referenz statt strengerer Prompt:** Ein Prompt *bittet* das LLM um echte Namen, der Schema-Abgleich *beweist* es deterministisch. Eine Prüfregel mit erfundener Eigenschaft würde jedes Template falsch bewerten (BSI: Nachweisbarkeit, wie Zitat- und Typprüfung aus #12).
- **Lücken sichtbar statt still:** Eine Regel mit Typ außerhalb des Schnappschusses ist ungeprüft und wird gezählt (16 Regeln, Folgeticket #19). Der Schnappschuss ist ein Handbefehl ohne boto3, kostet nichts und läuft nur bei Bedarf (FinOps).

## Fachbegriffe
- **Schnappschuss** (Snapshot): eingefrorene Kopie einer externen Referenz im Repo, damit Build und Tests reproduzierbar ohne AWS laufen.
- **Deterministische Gegenprobe**: Code prüft die LLM-Ausgabe gegen eine feste Quelle; gleiche Eingabe, gleiches Urteil.
- **Fail closed** vs. **stille Lücke**: Was nicht geprüft werden kann, darf nicht als bestanden zählen, sondern muss sichtbar werden.

## Merksatz
„Ein Prompt kann Halluzinationen nur seltener machen, ein Abgleich gegen das CloudFormation-Schema schließt sie aus – und wo die Referenz endet, zählt der Bericht die Lücke statt sie zu verschweigen.“

## Abruffragen
1. Woher kommt `data/cfn_properties.json`, und warum steckt kein boto3 im Build-Code dafür?
2. Warum beweist der Schema-Abgleich mehr als eine strengere Regel im Prompt?
3. Was bedeutet `unjudged_properties`, und warum ist eine 0 bei `unknown_properties` allein nicht genug?
