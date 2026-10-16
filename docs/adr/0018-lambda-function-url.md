# 0018 – Lambda Function URL statt API Gateway

_Im Recruiter-Stand asynchron als Audit-Job mit Timeout 300 s: [ADR 0023](0023-demo-und-recruiter-stand.md)._

_Setzt den Plan B aus [ADR 0011](0011-vollstaendiger-katalog.md) um. Ändert [ADR 0004](0004-streamlit-community-cloud.md) (Rechte, Throttling) und [ADR 0006](0006-cloudwatch-audit-protokoll.md) (`dataTrace`). Umsetzung: #9._

## Kontext

- API Gateway REST bricht eine Integration nach 29 s ab. Die Messung vom 14.10.2026 (#26, `spec-wohngeld-openapi`): Bedrock 43,8 s gesamt, langsamster Einzelaufruf 33,4 s, ein Retry verdoppelt das. Groq läuft gedrosselt mindestens 2 Minuten (ADR 0016). Architektur-Audits sind noch nicht gemessen.
- Ein Quota-Antrag hebt das Timeout regionaler REST-APIs an, kann aber das Throttling-Kontingent des Kontos senken. Ob er bis zur Präsentation (26.10.) durchgeht, ist offen.
- Das Lambda-Konto-Limit liegt bei 10 gleichzeitigen Ausführungen. Reserved Concurrency geht damit nicht, denn AWS verlangt 100 freie.

## Entscheidung

- Die Audit-Lambda bekommt eine **Function URL mit `AuthType: AWS_IAM`** (SigV4, Dienst `lambda`). API Gateway entfällt im GovGuard-Stack.
- Der Handler routet `POST /audit/spec` und `POST /audit/architecture` selbst, sonst 404.
- **Lambda-Timeout 180 s**, die UI wartet 190 s mit `st.spinner`. Bestätigt durch den Durchlauf am 14.10.2026 (#26): `spec-wohngeld-openapi` mit Bedrock 47,4 s, mit Groq 73,5 s, `arch-antragseingang-fehlerhaft` mit Bedrock 31,6 s, jeweils mit Retries.
- Der Streamlit-User erhält über seine Gruppe nur `lambda:InvokeFunctionUrl` und `lambda:InvokeFunction` mit der Bedingung `lambda:InvokedViaFunctionUrl`, beides auf genau diese Funktion. Seit Oktober 2025 verlangt AWS beide Rechte.
- Missbrauchsschutz: IAM-Auth, Budget-Alarm bei 5 € und das Konto-Limit von 10. Ein eigenes Throttling gibt es nicht.

## Konsequenzen

- Kein Stage-Throttling und keine WAF-Option. Ein gestohlener Access Key kann bis zum Budget-Alarm Kosten erzeugen (ca. 1 $ je großem Audit mit Bedrock).
- Für `AWS::Lambda::Url` hat der Katalog keine Prüfregel: Das Selbst-Audit prüft den Eingang des eigenen Stacks nicht, nur cdk-nag und der CDK-Assertions-Test (`AuthType: AWS_IAM`). Die Ausnahmen `APIGateway.3` und `.4` braucht der Stack nicht mehr.
- Keine Zugriffslogs am Eingang. Das `AuditEvent` des Handlers (ADR 0006) bleibt der einzige Nachweis je Aufruf.
- Streaming der Antwort gibt es nur mit Node.js oder eigener Runtime, für Python also nicht. Für Produktion ist ein asynchroner Ablauf mit Job-ID der saubere Weg ([AUSBAU](../AUSBAU.md), Weg zu Asynchronität).

## Fachgespräch-Satz

„Ein Audit mit vollem Katalog dauert länger als die 29 s von API Gateway. Darum ruft die UI die Lambda direkt über eine Function URL mit IAM-Auth auf: gleiche Signatur, gleiches Least Privilege, ohne einen Quota-Antrag, auf den ich warten müsste.“
