# 0003 – Golden Archetypes als CDK mit Solutions Constructs

_Ergänzt durch [ADR 0007](0007-relevanz-und-ausnahmen.md) und [ADR 0009](0009-end-to-end-archetypen.md)._

## Kontext

Ursprünglich waren Terraform-Entwürfe geplant. Frei generiertes IaC ist fehleranfällig. CDK-Code mit Solutions Constructs ist kurz, verbirgt aber die Sicherheits-Defaults – ein Audit des CDK-Codes allein würde überall Prüfbedarf melden.

## Entscheidung

- Drei Golden Archetypes: 01 Sync REST, 02 Antragseingang (bis ADR 0009: Async Document Ingest), 03 Audit-Log-Archiv – als Python-CDK mit AWS Solutions Constructs, zur Build-Zeit vom LLM erzeugt.
- Freigabe-Schleife: `cdk synth` → Architektur-Audit auf das CloudFormation-Template **und** cdk-nag (Regelpaket AwsSolutions) als unabhängige deterministische Prüfung; erlaubt sind nur Ausnahmen aus der Allowlist (ADR 0007). Das LLM korrigiert höchstens 3 Runden, sonst bricht der Build ab.
- Freigegeben ist nur, was weder FAIL noch WARN hat (N/A erlaubt).
- Zur Laufzeit wählt das LLM nur aus – „kein passender Archetyp“ ist eine erlaubte Antwort.

## Konsequenzen

- Das Architektur-Audit akzeptiert auch CloudFormation; der Nutzer erhält CDK-Code und Template.
- CLAUDE.md: „Terraform-Entwurf“ wird zu „CDK-Entwurf“.
- Node.js und CDK CLI werden nur in der Build-Umgebung benötigt.

## Fachgespräch-Satz

„Zur Laufzeit generieren wir nichts: Jeder Archetyp hat vorher unser eigenes Audit und eine unabhängige deterministische Prüfung bestanden – Vier-Augen-Prinzip für Infrastructure as Code.“
