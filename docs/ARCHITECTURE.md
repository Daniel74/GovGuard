# GovGuard – Big Picture

GovGuard hat zwei Betriebsarten: **Build-Zeit** (Wissensbasis erzeugen) und **Laufzeit** (Audits beantworten). Beide nutzen dieselbe **Audit-Engine**. Begriffe: [CONTEXT.md](../CONTEXT.md), Anforderungen: [SPEC.md](SPEC.md).

## Arbeitsteilung LLM ↔ Code

Testfrage für jede Aufgabe: **Gibt es genau eine richtige Antwort, die sich ohne Sprachverständnis ermitteln lässt?** Ja → Code. Nein → LLM, und danach prüft der Code das Ergebnis.

| Code (deterministisch) | LLM (probabilistisch) |
|---|---|
| zählen, sortieren, nachschlagen, vergleichen | verstehen, bewerten, formulieren |
| Vorfilter, Relevanz, Abdeckung, N/A über das Ressourceninventar | „Ist diese Anforderung prüfbar, und welche Ressourcentypen betrifft sie?“ |
| Primäranker, Querverweis-IDs prüfen | Prüfregel-Kriterien und Empfehlungen formulieren |
| Zitat steht wörtlich in Quelle/Eingabe? Jede Prüfregel genau ein Befund? | „Verstößt diese Spezifikation gegen Art. 9?“ |
| Gesamtstatus = schlechtester Einzelstatus; N/A, wenn der Ressourcentyp im Template fehlt | Ressourceninventar aus Freitext nennen, mit Beleg (ADR 0015) |

Das LLM sitzt immer **zwischen zwei Code-Schichten**: Der Code bereitet vor (filtern, auswählen), das LLM urteilt, und der Code kontrolliert (Schema, Vollständigkeit, Zitate). Was der Code schon weiß, erzeugt das LLM nicht. Das hält den Anteil klein, der halluzinieren kann.

## 1. Build-Zeit – Wissensbasis erzeugen (manueller Workflow `build-kb.yml`)

```mermaid
flowchart TD
  subgraph Q[Quellen]
    BSI["BSI Grundschutz++<br/>OSCAL-JSON (GitHub)"]
    CIS["CIS AWS v7, AWS FSBP, BSI C5<br/>Prowler-JSON (GitHub)"]
    DS["DSGVO Formex-XML (CELLAR)<br/>+ SDM-PDFs (DSK)"]
  end
  BSI & CIS & DS -->|"gepinnt + SHA-256"| E["1 Extrahieren"]
  E --> F["2 Vorfiltern (deterministisch)"]
  F --> K["3 LLM: prüfbar ja/nein<br/>+ Ressourcentypen"]
  K --> R["4 Relevanz (Prüfumfang)<br/>+ Abdeckungs-Gate (deterministisch)"]
  R --> P["5 LLM formuliert Prüfregeln + Querverweise"]
  P --> G1{"Gate: Schema, Anker, Zitat"}
  G1 -->|ok| PR{"6 Preset-Gate"}
  PR -->|grün| KB["Pull Request<br/>rules_spec.json<br/>rules_arch.json"]
  G1 -->|Fehler| X["Build-Abbruch"]
  PR -->|rot| X
```

Die Rauten sind **Gates**: automatische Prüfpunkte, an denen Code das Ergebnis des LLM kontrolliert. Fällt etwas durch, bricht der Build ab, und die alte Wissensbasis bleibt aktiv.

Das Build-Skript lädt jede Quelle vom Herausgeber, wie in `data/input/sources.json` festgelegt, und bricht ab, wenn die SHA-256-Prüfsumme nicht stimmt. Quelldateien liegen nie im Repo (ADR 0008). Dann siebt es die Quellen in zwei Stufen: Ein deterministischer Vorfilter wirft offensichtlich Irrelevantes weg, dann entscheidet das LLM je Anforderung, ob sie an einer Spezifikation oder an einem CloudFormation-Template prüfbar ist, und nennt bei Architektur die betroffenen Ressourcentypen. Der Code behält alles, was prüfbar ist und einen Dienst im Prüfumfang betrifft, ohne Obergrenze; jede Entscheidung steht mit Begründung im Auswahlprotokoll (ADR 0011). Erst danach formuliert das LLM daraus Prüfregeln.

Das erste Gate prüft jede Prüfregel in drei Punkten:

| Prüfung | Frage | Schützt vor |
|---|---|---|
| Schema | Passt das JSON zum Pydantic-Modell `Rule` (Pflichtfelder, Typen, erlaubte Werte)? | unvollständigen oder kaputten Regeln |
| Anker | Gibt es Primäranker und Querverweise wirklich in der Quelle (1.3)? | erfundenen Fundstellen, z. B. „DET.3.99“ |
| Zitat | Steht `source_quote` wörtlich im Text der verankerten Anforderung (1.3)? | erfundenem oder umformuliertem Normtext |

Den Primäranker setzt zwar der Code, der Check sichert aber die Extraktion ab. Querverweise schlägt dagegen das LLM vor; hier fängt der Check erfundene IDs ab.

Zum Schluss müssen die 5 Presets ihr festgelegtes Soll-Ergebnis liefern. Nur wenn alle Gates grün sind, öffnet der Workflow einen Pull Request mit der neuen Wissensbasis. Nach S3 gelangt sie erst nach dem Merge, über den normalen Deploy (Abschnitt 3). Jeder Fehler bricht den Build ab, und die alte Version bleibt aktiv.

Der Workflow startet nur manuell: Er kostet viele LLM-Aufrufe, liefert bei jedem Lauf leicht andere Texte, und die Quellen ändern sich selten. Golden Archetypes baut der Build nicht (ADR 0019).

### 1.1 Sieben: Vorfilter, LLM, Relevanz

Jede Quelle durchläuft dieselben Stufen; nur die Parameter unterscheiden sich. Leitsatz: **Das LLM urteilt, der Code wählt aus.** Eine Obergrenze gibt es nicht (ADR 0011).

| Quelle | Einheit (Anforderung) | ① Vorfilter (Code) | ② LLM-Frage (ja/nein + Begründung) |
|---|---|---|---|
| BSI Grundschutz++ | Control im OSCAL-Katalog, z. B. `DET.3.1` | `modal_verb` ∈ MUSS, SOLLTE, `sec_level` = normal-SdT, Praktik ∈ DLS, BER, DET, KONF, BES, ARCH | „An einer Architektur aus Diensten des Prüfumfangs prüfbar? Welche Ressourcentypen?“ |
| BSI C5:2025 | Kriterium, z. B. `CRY-03.01B` | Bereiche OPS, IAM, CRY, COS, PSS | wie BSI Grundschutz++ |
| CIS AWS v7 | Empfehlung, z. B. `3.1.4` | Kapitel 2 IAM, 3 Storage, 4 Logging, 6 Networking (Security Groups für Aurora) | wie BSI Grundschutz++ |
| AWS FSBP | Control, z. B. `SNS.1` | Dienst (`Service`) gehört zum Prüfumfang, z. B. Lambda, ECS, ECR, ELB, RDS; EC2 wegen der VPC-Controls, Instanzen und Classic LB sortiert die Relevanz aus | wie BSI Grundschutz++ |
| DSGVO | Artikel | Kapitel II–V (Art. 5–49) | „An einer Spezifikation prüfbar?“ |
| SDM | Maßnahme, z. B. `M60.D01` | Bausteine Löschen (M60), Trennen (M50), Zugriffe regeln (M51); alle Ebenen (Daten, Systeme, Prozesse), denn Löschfristen stehen auf Ebene P | „An einer Spezifikation prüfbar?“ |

- **① Vorfilter:** reiner Code auf Metadaten (OSCAL-Props, Kapitel, Bereiche, Dienste, Maßnahmen-IDs). Er ist billig, reproduzierbar und wirft Organisatorisches früh weg. Für jede verworfene Anforderung schreibt er einen festen Begründungssatz ins Auswahlprotokoll.
- **② LLM:** bekommt **eine** Anforderung und den Prüfumfang und antwortet nur ja/nein mit Begründung, bei Architektur zusätzlich mit `cfn_resource_types` (per Tool-Choice, siehe 2.1). Es zählt nicht und wählt nicht aus. Das Urteil wird gecacht (Text-Hash, Prompt-Version, `model_id`); ein neuer Lauf fragt nur neue oder geänderte Anforderungen.
- **Relevanz (Code, nur Architektur):** Es bleiben nur Anforderungen, deren erster (wichtigster) `cfn_resource_type` im Prüfumfang liegt (`data/input/scope.json`): Serverless-Dienste, dazu RDS/Aurora und Fargate (ECS) mit dem, was beide brauchen: VPC-Typen, ECR und ELBv2. Kontoweite Pflichten wie Root-MFA oder CloudTrail fallen damit heraus, denn sie sind an keinem Template entscheidbar.
- **Aufnahme:** Jede prüfbare und relevante Anforderung kommt in den Bounded Catalog. Das Auswahlprotokoll (`verdicts_*.json`) hält für jede Anforderung Ergebnis und Begründung fest (SPEC). Die Liste der aufgenommenen (`selection_spec.json`, `selection_arch.json`) liegt versioniert im Repo; Änderungen zwischen zwei Builds zeigt der Git-Diff.
- **Gates:** Die Pflichtanker der Presets müssen aufgenommen sein, und jede Komponente der Archetypen (Pflicht-Ressourcentypen, 1.4) braucht mindestens eine Prüfregel. Sonst bricht der Build ab.

### 1.2 Prüfregel-Schema

Aus jeder ausgewählten Anforderung formuliert das LLM genau eine Prüfregel (Pydantic-Modell `Rule`). Feldnamen sind englisch, Inhalte deutsch. Beispiel:

```json
{
  "id": "ARCH-CIS-3.1.4",
  "audit_type": "architecture",
  "source": "CIS",
  "primary_anchor": "CIS AWS v7.0.0 3.1.4",
  "source_quote": "Ensure that S3 is configured with 'Block Public Access' enabled",
  "title": "S3 Block Public Access aktiv",
  "compliant_if": "Jeder S3-Bucket hat alle vier Block-Public-Access-Einstellungen aktiv.",
  "violation_if": "Ein Bucket deaktiviert mindestens eine Einstellung.",
  "recommendation": "Am Bucket BlockPublicAccess.BLOCK_ALL setzen.",
  "cfn_resource_types": ["AWS::S3::Bucket"],
  "selection_rationale": "Direkt an der Bucket-Konfiguration im Template prüfbar.",
  "cross_references": [{ "anchor": "BSI GS++ …", "origin": "ai_suggested" }]
}
```

| Feld | Herkunft | Zweck |
|---|---|---|
| `id`, `audit_type`, `source`, `primary_anchor` | Code | Identität und Herkunft – das LLM erfindet hier nichts |
| `source_quote` | LLM, vom Code geprüft | Wörtlicher Auszug aus der Quelle (siehe 1.3) |
| `title`, `compliant_if`, `violation_if`, `recommendation` | LLM | Prüfbare Kriterien für PASS/FAIL und die Abhilfe |
| `cfn_resource_types` | LLM aus Stufe ②, nur Architektur | Für welche CloudFormation-Typen die Regel gilt: Relevanz und N/A durch den Code (siehe 1.1, 2) |
| `selection_rationale` | LLM aus Stufe ② | Warum die Anforderung prüfbar ist |
| `cross_references` | LLM, vom Code geprüft | Bezug auf eine andere Quelle; nur `ai_suggested` (KI-vorgeschlagen), ohne Einfluss auf den Status |

### 1.3 Primäranker

Der Primäranker ist die **eine** Anforderung, aus der eine Prüfregel stammt. Ihn setzt der Code, nicht das LLM, denn er kennt die ID aus Stufe ①. Das Gate prüft zwei Dinge:

| Quelle | Format | Existenz-Check |
|---|---|---|
| BSI | `BSI GS++ DET.3.1` + Commit-SHA des Katalogs | ID existiert im Katalog-JSON |
| CIS | `CIS AWS v7.0.0 3.1.4` | `Id` existiert im Prowler-JSON (fester Commit) |
| DSGVO | `DSGVO Art. 32` (optional Abs./lit.) | `ARTICLE IDENTIFIER="032"` existiert im Formex-XML |
| SDM | `SDM Löschen M60.D01` | Maßnahmen-ID steht im Baustein-Text |
| C5 | `BSI C5 CRY-03.01B` | `Id` existiert im Prowler-JSON (fester Commit) |
| FSBP | `AWS FSBP SNS.1` | `Id` existiert im Prowler-JSON (fester Commit) |

Zusätzlich muss das `source_quote` **wörtlich** im Text genau der verankerten Anforderung stehen. Verglichen wird nach Entfernen von EUR-Lex-Markern wie „►C2“ und **ohne Leerzeichen**, denn pypdf zerteilt Wörter (SDM `M60.S06`: „Protokollie rung“). Der Beleg zur Laufzeit nutzt bewusst dieselbe Funktion (DESIGN 3): Zitat statt Behauptung. Dass ein Treffer dabei über Wortgrenzen gehen kann, nehmen wir in Kauf, denn die Zeichenfolge muss trotzdem lückenlos stimmen. Ist der ganze Text kürzer als 15 Zeichen (SDM `M60.P03`: „Löschkonzept“), muss das Zitat den ganzen Text umfassen. Querverweise müssen existieren und zu einer **anderen** Quelle gehören.

Dieselben Prüfungen laufen schon beim Formulieren als Validator: Das LLM bekommt den Fehler zurück und hat bis zu sechs Wiederholungen. Bei Architektur-Regeln prüft er zusätzlich, ob die Kriterien einen Ressourcentyp der Regel nennen und keine vagen Wörter wie „erforderlich“ enthalten. Bei Spec-Regeln fragt er einen LLM-Prüfer, ob `violation_if` eine Festlegung beschreibt und kein Fehlen (offene Welt, ADR 0020). Bleibt ein Entwurf ungültig, bricht der Build ab.

### 1.4 Steckbriefe der Archetypen (nur fürs Abdeckungs-Gate)

Golden Archetypes werden nicht gebaut (ADR 0019). Ihre Steckbriefe in `data/input/archetype_profiles.json` bleiben, denn sie nennen die Komponenten, die das Abdeckungs-Gate braucht (1.1): Jeder Pflicht-Ressourcentyp braucht mindestens eine Prüfregel. Jeder Archetyp ist als End-to-End-Kette ab API Gateway mit IAM-Auth entworfen (ADR 0009).

| Archetyp | Solutions Constructs | Pflicht-Ressourcentypen |
|---|---|---|
| ARCH-01 Sync REST | `aws-apigateway-lambda`, `aws-lambda-dynamodb` | `AWS::ApiGateway::RestApi`, `AWS::Lambda::Function`, `AWS::DynamoDB::Table` |
| ARCH-02 Antragseingang | `aws-apigateway-lambda`, `aws-lambda-sqs`, `aws-sqs-lambda`, `aws-lambda-s3` | `AWS::ApiGateway::RestApi`, `AWS::Lambda::Function`, `AWS::SQS::Queue`, `AWS::S3::Bucket` |
| ARCH-03 Audit-Log-Archiv | `aws-apigateway-lambda`, `aws-lambda-kinesisfirehose`, `aws-kinesisfirehose-s3` | `AWS::ApiGateway::RestApi`, `AWS::Lambda::Function`, `AWS::KinesisFirehose::DeliveryStream`, `AWS::S3::Bucket` mit `ObjectLockEnabled` |

Die Steckbriefe stammen aus [Behörden Cloud-Referenzarchitekturen Analyse](research/Behörden%20Cloud-Referenzarchitekturen%20Analyse.md). Wie Bau und Freigabe aussähen (CDK vom LLM, `cdk synth`, Audit-Engine und cdk-nag, höchstens drei Korrekturrunden), beschreiben ADR 0003 und 0009 als Ausbau.

## 2. Laufzeit – ein Audit

```mermaid
sequenceDiagram
  actor U as Streamlit-UI / CI
  participant L as Lambda (Audit-Engine)<br/>Function URL, IAM-Auth
  participant S3 as S3
  participant B as Bedrock (eu.)
  participant CW as CloudWatch Logs
  Note over L,S3: Kaltstart: Wissensbasis in den Speicher laden
  U->>L: POST /audit/spec (SigV4, Timeout 180 s)
  L->>B: Converse, Tool submit_audit (je Paket parallel: anwendbare Prüfregeln + Eingabe)
  B-->>L: Befunde (JSON)
  L->>L: Pydantic + Code-Checks (1 Befund je Regel, Belege wörtlich)
  L->>CW: Audit-Ereignis (Hashes + Status, ohne Eingabe)
  L-->>U: Audit-Report
```

Die UI ruft die Lambda direkt über ihre Function URL auf, ohne API Gateway: Ein Audit mit vollem Katalog dauert länger als dessen 29 s (ADR 0018).

Beim Kaltstart lädt die Lambda-Funktion die Wissensbasis einmal aus S3 in den Speicher, weitere Aufrufe nutzen sie direkt. Zuerst bestimmt sie das Ressourceninventar der Eingabe: bei CloudFormation-JSON der Code, bei Freitext, YAML und Terraform ein LLM-Vorlauf mit Beleg je Dienst (ADR 0015). Jede Prüfregel ohne passenden Ressourcentyp setzt der Code auf N/A; IAM, KMS und Logs streicht er nie. Die anwendbaren Prüfregeln gehen in Paketen à ca. 10 parallel mit der Eingabe an Bedrock (ADR 0011). Das Modell muss über das erzwungene Tool `submit_audit` antworten (Tool-Choice), es kann also nur strukturiertes JSON liefern, keinen Freitext.

Danach prüft der Code, nicht das Modell, das Ergebnis. Pydantic validiert das Schema, und zusätzlich muss jede Prüfregel genau einen Befund haben und jeder Beleg wörtlich in der Eingabe stehen. Im Spec-Audit gehen danach alle FAILs gebündelt an den FAIL-Prüfer (Tool `submit_fail_verdicts`): Bestätigt er ein FAIL nicht, wird es WARN; fällt er aus, bleibt es ungeprüft FAIL, ohne HTTP 502 (ADR 0020). Erst dann wird der Gesamtstatus berechnet.

Das Architektur-Audit (`POST /audit/architecture`) läuft genauso wie das Spec-Audit ab, nur mit den Prüfregeln aus BSI Grundschutz++, BSI C5, CIS und FSBP.

### 2.1 Tool-Choice – wie das Modell zur Struktur gezwungen wird

Die Bedrock Converse API erlaubt, dem Modell „Tools“ anzubieten. Jedes Tool hat einen Namen und ein JSON-Schema für seine Eingabe. Mit `toolChoice` erzwingen wir ein Tool. Das Modell darf dann nicht frei antworten, sondern muss dieses Tool mit schema-konformen Argumenten „aufrufen“. Wir führen dabei nichts aus. **Das Tool ist ein Formular**, und seine Argumente sind unser Ergebnis.

Den Aufruf baut Pydantic AI (ADR 0005): Aus dem Draft-Modell entsteht das Tool-Schema, und weil es nur dieses eine Ausgabe-Tool gibt, sendet das Framework `toolChoice: any`, also „ein Tool ist Pflicht“.

```python
# aws_services.py – einziger Ort mit boto3
model = BedrockConverseModel("eu.anthropic.claude-haiku-4-5-20251001-v1:0")   # EU-Profil, ADR 0001

# audit_packages.py – rein, bekommt das Modell übergeben
audit_agent = Agent(
    output_type=ToolOutput(AuditResponse, name="submit_audit",       # Groq: NativeOutput (ADR 0016)
                           description="Gib genau einen Befund je Prüfregel ab.",
                           strict=True),   # statisches Schema, alle Felder Pflicht (ADR 0017)
    instructions=SYSTEM_PROMPT,     # Rolle + Regeln für PASS/WARN/FAIL/N/A
    deps_type=AuditDeps,            # Katalog + Eingabe für die Code-Checks
    retries=1,                      # genau ein Retry, Lambda-Timeout 180 s (ADR 0018)
)
result = audit_agent.run_sync(catalog_and_input, model=model, deps=deps)
```

| Tool | Schema (vereinfacht) | Wo |
|---|---|---|
| `classify_requirement` | `testable: bool`, `rationale: str`, `cfn_resource_types: [str]` (nur Architektur) | Build, Stufe ② |
| `formulate_rule` | LLM-Felder der Prüfregel (siehe 1.2) | Build, Stufe 5 |
| `judge_violation` | `describes_absence: bool`, `reason: str` | Build, Stufe 5, nur Spec |
| `submit_audit` | `findings: [{rule_id, status: PASS\|WARN\|FAIL\|N/A, line_start, line_end, rationale, recommendation}]` | Laufzeit, beide Audits |
| `submit_fail_verdicts` | `verdicts: [{rule_id, confirmed: bool, reason}]` | Laufzeit, nur Spec, nur bei FAIL (ADR 0020) |

- **Enums schließen die Antwortmenge:** Das Modell kann keinen Status „OK“ erfinden.
- **Tool-Choice ist kein Beweis:** Das Modell kann trotzdem falsche Werte liefern. Deshalb validiert danach Pydantic, und der Code prüft Vollständigkeit und Belege (`@agent.output_validator`). Bei Fehlern schickt Pydantic AI die Fehlermeldung einmal zurück ans Modell, danach HTTP 502.
- **Was der Code weiß, fragt man das Modell nicht:** Primäranker, Querverweise und Gesamtstatus ergänzt der Code aus der Wissensbasis. Das Modell liefert nur Status, Zeilenbereich und Begründung; den Beleg schneidet der Code aus der Eingabe (ADR 0017).
- **Modellwahl:** Haiku 4.5 unterstützt erzwungene Tools; Opus 5.5, Sonnet 5.5 und Fable 5.1 lehnen `toolChoice` = `any` bzw. `tool` laut Anthropic-Doku mit HTTP 400 ab. Achtung: Kann ein Modell kein Erzwingen, fällt Pydantic AI still auf `auto` zurück – darum bleibt Haiku 4.5 gesetzt.

## 3. Deployment – GovGuard prüft sich selbst

```mermaid
flowchart LR
  Push["Push auf main<br/>(auch Merge des KB-PR)"] --> GA["GitHub Actions<br/>deploy.yml"]
  GA -->|"OIDC-Rolle, keine Keys"| Synth["cdk synth GovGuard-Stack"]
  Synth --> Nag["cdk-nag"]
  Nag --> Self["Audit-Engine: Architektur-Audit<br/>des eigenen Templates"]
  Self -->|"kein FAIL / WARN"| Deploy["cdk deploy eu-central-1<br/>+ Wissensbasis nach S3"]
  Self -->|Beanstandung| Stop["Deploy blockiert"]
```

GovGuard wird selbst mit CDK beschrieben und über GitHub Actions ausgerollt. Die Pipeline meldet sich per OIDC bei AWS an und erhält kurzlebige Rechte, es liegen also keine dauerhaften Zugangsschlüssel in GitHub.

Vor jedem Deploy durchläuft der eigene Stack zwei Prüfungen. Erst prüft cdk-nag deterministisch, mit den Ausnahmen aus der Allowlist, dann prüft die Audit-Engine das Template gegen die Architektur-Prüfregeln. Ein FAIL oder WARN blockiert das Deployment, außer bei einer Ausnahme aus der Allowlist (ADR 0011).

So beweist GovGuard an sich selbst, dass seine Regeln erfüllbar sind (Dogfooding).

Es gibt nur **einen Weg in die Produktion**: `deploy.yml`. Er lädt auch die Wissensbasis aus dem Repo nach S3. Darum liegen die Regeln schon vor dem ersten Deploy bereit, und das Selbst-Audit nutzt immer dieselbe Version, die danach live geht.

## Komponenten

| Komponente | Aufgabe | Technik |
|---|---|---|
| Build-Skript | Wissensbasis erzeugen | Python-Paket `kb_build` |
| Audit-Engine | Prompt bauen, Bedrock aufrufen, Befunde validieren | Python-Modul, Pydantic, Pydantic AI |
| API | 2 Endpunkte, IAM-Auth | Lambda mit Function URL (ADR 0018) |
| Wissensbasis | Prüfregeln | JSON in `data/knowledge_base/` (versioniert), per Deploy nach S3 |
| UI | Eingabe, Ampel, Download | Streamlit Community Cloud (ADR 0004) |
| Audit-Protokoll | ein Ereignis je Aufruf, für Auditoren | CloudWatch Logs, KMS, 365 Tage (ADR 0006) |
| Build-Workflow | manuell: Build-Skript ausführen, PR öffnen | GitHub Actions `build-kb.yml` |
| Deploy-Workflow | bei Push: Selbst-Audit, Deploy, Wissensbasis nach S3 | GitHub Actions `deploy.yml`, CDK |

## Code-Struktur

Ein- und Ausgabe (AWS, externe Programme) und Prüflogik liegen in getrennten Dateien. So bleibt der Kern ohne AWS und ohne CDK testbar. Pfeil = „importiert bzw. ruft auf“.

```mermaid
flowchart TB
  subgraph E["Einstieg – verbindet nur"]
    H["govguard/handler.py<br/>Lambda"]
    C["govguard/cli.py<br/>lokal + Selbst-Audit"]
    U["govguard_ui/<br/>Streamlit-Demo, ohne AWS"]
    S["govguard/audit_setup.py<br/>Kataloge, Rückverfolgung,<br/>Fehlertext für CLI + UI"]
    M["kb_build/__main__.py<br/>Build"]
    R["kb_build/*/run.py<br/>Dateien lesen + schreiben,<br/>Pfade aus paths.py"]
  end
  subgraph L["Logik – rein, ohne I/O"]
    AE["govguard/audit_engine.py<br/>+ audit_packages.py, audit_gates.py, corrections.py,<br/>evidence.py, fail_judge.py, inventory.py, models.py,<br/>repairs.py, text.py"]
    KB["kb_build/extract, select, rules,<br/>reference (ohne run.py), gates.py, build_log.py"]
    RV["govguard_ui/review.py<br/>Report lesen: Lücke, Soll-Abgleich"]
  end
  subgraph A["Adapter – einziger Ort für AWS, Groq, HTTP"]
    AWS["govguard/aws_services.py<br/>boto3, Bedrock-Modell"]
    GQ["govguard/groq_services.py<br/>Groq-Modell, Laufzeit + Build"]
    FE["kb_build/source_fetch.py<br/>HTTP + SHA-256"]
  end
  subgraph X["Extern"]
    B[("Bedrock eu.")]
    G[("Groq")]
    S3[("S3")]
    HG["Herausgeber<br/>GitHub, CELLAR, DSK"]
  end
  H & C & U --> AE
  H & C --> AWS
  H & C & U --> GQ
  C & U --> S
  U --> RV
  M --> R --> KB
  M --> AWS & GQ & FE
  KB --> AE
  AWS --> B & S3
  GQ --> G
  FE --> HG
```

Von der Logik führt **kein Pfeil** zu den Adaptern, und von der Demo-UI keiner zu AWS (ADR 0023). Der Einstieg reicht die Adapter hinein, etwa das Bedrock-Modell (Dependency Injection); Tests reichen Fakes bzw. `TestModel` hinein.

Jeder Ordner auf oberster Ebene ist eine eigene Deployment-Einheit oder eine Datenart. `src/kb_build/` hat je Build-Kommando einen Unterordner, `data/` ist nach Herkunft getrennt:

```
src/govguard/         Laufzeit-Kern, wird zum Lambda-Paket
src/kb_build/         Build-Werkzeug: python -m kb_build (importiert govguard, nie umgekehrt)
  __main__.py         Einstieg; gates.py, build_log.py (Retries im Build-Log), paths.py (alle Datenpfade), source_fetch.py
  extract/            Adapter je Quelle (bsi, cis, c5, dsgvo, fsbp, sdm, prowler), models.py, run.py
  select/             classify, curation, judgement_cache, models.py, run.py
  rules/              catalog, formulate, prompts, criteria, violation_judge, quality, run.py
  reference/          scope, cfn_types, cfn_properties, archetype_profiles, run.py (cfn-properties)
infra/                CDK-App des GovGuard-Stacks
src/govguard_ui/      Streamlit-Demo (ADR 0023): ruft run_audit im eigenen Prozess mit Groq auf;
                      Start über streamlit_app.py im Root
data/input/           von Hand gepflegt: sources.json (URL, Version, SHA-256, Lizenz; ADR 0008),
                      scope.json (Prüfumfang, ADR 0011), archetype_profiles.json,
                      cfn_resource_types.json, cfn_properties.json, presets/ (5 Presets mit Soll-Ergebnis)
data/intermediate/    Zwischenergebnisse, eingecheckt fürs Review: extracted/ (cis, fsbp, c5 nur lokal),
                      judgement_cache.json, selection_*.json, verdicts_*.json; sources/ = Download-Cache, in .gitignore
                      logs/<kommando>[_spec|_arch].log: Build-Log je Lauf (Retries mit Grund, Tokens), mit dem Ergebnis committen
data/knowledge_base/  nur das Endergebnis: rules_spec.json, rules_arch.json; geht nach S3
data/gallery/        Galerie: je Preset ein gespeicherter Report, wächst nur per Commit
tests/                pytest, flach
.github/workflows/    build-kb.yml, deploy.yml
```

- **Adapter für I/O:** Nur `aws_services.py` importiert boto3 und baut das Bedrock-Modell für Pydantic AI, nur `groq_services.py` baut das Groq-Modell für Laufzeit und Build (ADR 0014, 0023), nur `source_fetch.py` lädt Quellen aus dem Netz. Kein Modul startet Prozesse (ADR 0019). Die Demo-UI lädt weder `cli.py` noch `aws_services.py`, auch nicht über Umwege. Tests prüfen das.
- **Keine Logik in Klebe-Code:** Einstiegsdateien und Workflow-YAML verbinden nur. Was CLI und UI teilen, liegt in `audit_setup.py`; kein Einstieg importiert einen anderen. Ein Workflow meldet sich an, ruft `python -m …` auf und öffnet den PR. Derselbe Befehl läuft lokal.
- **src-Layout:** Der CDK-Stack packt mit `Code.from_asset("src/govguard")` genau den Laufzeit-Kern, ohne Build-Code, UI oder Daten.

### Neue Quelle hinzufügen

1. `data/input/sources.json`: URL, Version (Commit oder Tag), SHA-256, Lizenz (ADR 0008).
2. Adapter `src/kb_build/extract/<quelle>.py` mit `extract()` und `prefilter()`. Der Vorfilter gibt `None` zurück oder für jede verworfene Anforderung einen festen Begründungssatz (Auswahlprotokoll). Prowler-Quellen (CIS, FSBP, C5) beschreiben nur ihr `ProwlerFormat` (Anker, Titel, Text, Attribute, Vorfilter); gelesen wird im gemeinsamen Parser `prowler.py`.
3. Je ein Eintrag in `ADAPTERS` (`extract/run.py`) und `SourceName` (`models.py`). In `SELECTIONS` (`select/run.py`) kommt die Quelle zu ihrer Audit-Art.
4. Lizenz: offen → Extrakt einchecken, Vermerk in `NOTICE`; sonst Extrakt in `.gitignore` (CIS, FSBP, C5).
5. Test mit kleinem Fixture: Anzahl, Stichprobe, Vorfilter mit Begründung.

## Endpunkte

| Endpunkt | Eingabe → Ausgabe |
|---|---|
| `POST /audit/spec` | Spezifikation → Audit-Report |
| `POST /audit/architecture` | Architektur → Audit-Report |

- Beide Pfade liegen an derselben Function URL mit IAM-Auth; der Handler routet, sonst 404 (ADR 0018). Einen Endpunkt für Golden Archetypes gibt es nicht (ADR 0019).
- Ein Audit wertet die anwendbaren Prüfregeln in parallelen Paketen aus (ADR 0011). Das Lambda-Timeout liegt vorläufig bei 180 s; die Messung in Schritt 10a bestätigt es.
- Scheitert die Validierung, schickt Pydantic AI die Fehlermeldung einmal zurück ans Modell (`retries=1`), danach HTTP 502.

## Kosten

Der eigene Stack verschlüsselt mit einem kundenverwalteten KMS-Schlüssel (CMK), ca. 1 $/Monat; derselbe Schlüssel schützt auch das Audit-Protokoll. Ein Audit-Ereignis (ca. 2 KB) kostet Bruchteile eines Cents. Regel: **0 € Leerlaufkosten** (CONTEXT.md): Im Leerlauf zahlen wir nur für gehaltene Daten und für Sicherheit. Satz für die Verteidigung: „Sicherheit hat einen Preis, und ich kann ihn auf den Cent beziffern.“

## Bekannte Grenzen

- **SDM ohne Protokollieren (M43):** Der Baustein V2.0 hat ein eigenes ID-Schema (`M43.21.04`) ohne Ebenen D/S und führt ungültige Maßnahmen nur durchgestrichen weiter. Er bräuchte einen eigenen Parser und fehlt bewusst; Protokollierung prüft das Architektur-Audit (BSI DET, CIS Kapitel 4).
- **CIS aus zweiter Hand:** Offiziell maschinenlesbar gibt es den Benchmark nur für CIS-Mitglieder. Wir nutzen deshalb das Prowler-JSON, und eine Stichprobe gegen das lokale PDF sichert die Texttreue ab (ADR 0008).
- **DSGVO-Einheit „Artikel“:** Art. 5 ergibt nur eine Prüfregel, obwohl er sechs Grundsätze enthält. Die Grundsätze kommen über das SDM in den Katalog; die SDM-Methode ist genau ihre Operationalisierung (Teil C, „Systematisierung der Anforderungen der DS-GVO durch die Gewährleistungsziele“).
- **Audit-Protokoll nicht revisionssicher:** CloudWatch Logs sind für Admins löschbar, und gespeichert werden nur Hashes und Status, keine Eingaben und vollständigen Reports (ADR 0006). Ein unlöschbarer Speicher für Inhalte widerspräche dem Recht auf Löschung (Art. 17 DSGVO). Die Build-Historie in Git schützt eine Branch Protection auf `main` gegen Force-Push und Löschen; der GitHub Free Plan bietet sie für öffentliche Repos an.
- **Keine kontoweiten Pflichten:** Root-MFA, Passwort-Policy oder ein kontoweiter CloudTrail sind an keinem Template entscheidbar und fehlen bewusst (ADR 0007). Dafür gibt es Werkzeuge wie Prowler oder AWS Security Hub.
- **Stufe ② urteilt per LLM:** Einzelne Fehlurteile sind möglich, z. B. gilt C5 CRY-07.01B (Schlüsselrotation) als „nicht prüfbar“. Die Gates sichern nur Pflichtanker und Abdeckung; die Rotation prüfen weiter CIS 4.6 und FSBP KMS.4. Konto- und Personenpflichten landen teils als „nicht prüfbar“ statt mit festem Satz der Ebene; draußen sind sie in beiden Fällen (#18). *Lösungsansatz:* Gegenprobe gegen die Prowler-Checks der Quelle als Hinweis im Qualitätsbericht, nicht als Gate, denn viele Checks sind kontoweit (C5 OPS-16.01B: MFA für Konsolen-Nutzer, CloudTrail-Bucket).
- **Ressourceninventar:** Nur CloudFormation-JSON liest der Code (ADR 0015). YAML-Templates mit Kurzformen wie `!Ref` und Terraform behandelt GovGuard wie Freitext, Terraform ist ungetestet; dort nennt ein LLM-Vorlauf die Dienste mit Beleg, und ein übersehener Dienst steht als „nicht erkannt“ im Befund.
- **Kein X-Ray:** `xray:Put*` erlaubt keine Ressourcen-ARNs und bräuchte eine weitere Ausnahme. In Produktion: X-Ray mit begründeter Ausnahme.
- **Umfang:** Prüfumfang aus Serverless-Diensten plus RDS/Aurora und Fargate; EC2-Instanzen, EKS, CloudTrail, CloudFront und der Classic Load Balancer fehlen bewusst (ADR 0011). Eingaben bis 100.000 Zeichen. Wie GovGuard darüber hinaus wächst, beschreibt [AUSBAU.md](AUSBAU.md).
