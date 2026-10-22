# 0015 – CloudFormation ist das einzige Format mit Code-Inventar, Terraform ungetestet

_Ergänzt [ADR 0007](0007-relevanz-und-ausnahmen.md) (N/A bei CloudFormation) und [ADR 0011](0011-vollstaendiger-katalog.md) (Ressourceninventar). Ausbau: `AUSBAU.md`, Szenario 9 (bis 22.10.2026, Git-Verlauf)._

## Kontext

- Prüfregeln, `scope.json` und `cfn_properties.json` sprechen CloudFormation (`AWS::S3::Bucket`). Nur dort kann der Code das Ressourceninventar aus der Eingabe lesen (`template_resource_types()`, JSON).
- Die Eingabe-Docs nannten Terraform bisher gleichberechtigt. Kein Preset ist aber in Terraform geschrieben, die Zusage wäre also nie getestet worden.
- Terraform-Typen heißen anders (`aws_s3_bucket`), und ein Terraform-Block entspricht nicht immer genau einer CloudFormation-Ressource (z. B. `aws_s3_bucket_server_side_encryption_configuration` gehört in CloudFormation zu `AWS::S3::Bucket`).

## Entscheidung

- **Nur CloudFormation-JSON** hat ein Ressourceninventar per Code und damit N/A durch den Code. YAML und Terraform nimmt GovGuard als Freitext an: Ein LLM-Vorlauf nennt die Typen mit Beleg (ADR 0011).
- **Einschränkung „Terraform als Freitext, nicht getestet“:** Kein Preset und kein Gate prüft Terraform. GovGuard nimmt die Eingabe an und liefert Befunde mit wörtlichen Belegen, sichert aber weder Vollständigkeit noch Qualität des Inventars zu.
- **Verworfen: Zuordnungstabelle `aws_*` → `AWS::*`.** Die Zuordnung ist nicht 1:1 (siehe Kontext), die Tabelle müsste für jeden Typ gepflegt und getestet werden, und kein Preset würde sie abdecken. Aufwand ohne Nachweis.
- **Verworfen: LLM übersetzt Terraform nach CloudFormation.** Der Beleg müsste wörtlich in der Eingabe stehen. Im übersetzten Text steht er nicht mehr, und der Existenz-Check des Codes würde ihn ablehnen oder gegen Text prüfen, den das LLM selbst erzeugt hat.

## Konsequenzen

- Es entsteht kein Code und kein neues Preset. `CONTEXT.md`, `SPEC.md` und `ARCHITECTURE.md` nennen dieselbe Einschränkung.
- Ein übersehener Dienst in Terraform steht als „nicht erkannt“ im Befund, nicht als stilles N/A (ADR 0011).
- Wer Terraform fest unterstützen will, folgt `AUSBAU.md`, Szenario 9 (bis 22.10.2026, Git-Verlauf), und legt zuerst ein Terraform-Preset an.

## Fachgespräch-Satz

„Das Ressourceninventar liest der Code nur dort, wo wir es testen – bei CloudFormation; Terraform nehmen wir als Freitext an und sagen offen, dass es ungetestet ist, statt es per LLM zu übersetzen und damit den wörtlichen Beleg zu verlieren.“
