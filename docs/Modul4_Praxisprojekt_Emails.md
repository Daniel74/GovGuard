# Modul 4 Praxisprojekt – E-Mail-Verlauf

Gesammelte Inhalte aller E-Mails zum Thema "Modul 4 Praxisprojekt" (Postfach d.tshisuaka@gmail.com), chronologisch sortiert. Jeder Abschnitt ist mit Betreff sowie Datum/Uhrzeit der jeweiligen E-Mail gekennzeichnet.

---

## 1. Betreff: "Modul 4 Praxisprojekt"
**Datum/Uhrzeit:** 2026-09-18 17:17:01 (UTC)

Das ist ein herausragendes Projekt mit exakt dem richtigen Profil für die IHK-Qualifizierung und Bewerbungen im öffentlichen Dienst: Es löst ein reales Business-Problem (*Compliance-as-Code & Audit-Readiness*), adressiert BSI IT-Grundschutz/DSGVO und beweist architektonische Reife.

Damit das Ganze in deinen *6 Wochen (3 Wochen Konzeption + 3 Wochen Bau)* realistisch bleibt und *unter 0–2 €/Monat* kostet, müssen wir die Architektur radikal auf *Serverless Free-Tier-Primitives* zuschneiden und teure AWS-Dienste (wie OpenSearch Serverless oder dauerhafte RDS/Aurora-Cluster) elegant umgehen.

### 1. Das Fachkonzept: „GovCloud Compliance Copilot“

- *Ziel:* Cloud-Architekten und IT-Sicherheitsbeauftragte laden eine System-Spezifikation (z. B. Markdown, Text oder PDF) in einen *Workspace* (z. B. *„Bürgerportal-Backend“* oder *„Justiz-Register-DB“*) hoch.
- *Funktion:*
  1. Das System prüft die Spezifikation gegen eine hinterlegte *Regulatorik-Knowledge-Base* (z. B. BSI IT-Grundschutz-Bausteine *APP.4.4 Kubernetes*, *OPS.1.1.2 Cloud-Nutzung*, *NET.1.1 Netzarchitektur* sowie DSGVO Art. 25/32).
  2. Es liefert einen *Compliance-Gap-Report* mit Ampel-Status (Grün/Gelb/Rot) und konkreten Behebungsempfehlungen.
  3. Über einen Chat können Architekten Nachfragen stellen (*„Warum verletzt die Verwendung eines NAT-Gateways ohne Egress-Filtering Baustein NET.3.2?“*).

### 2. Zero-Cost / Free-Tier Architektur (FinOps by Design)

Um im Free Tier zu bleiben, nutzen wir *AWS Bedrock On-Demand* (nur Bruchteile von Cent pro Query) und vermeiden alle dauerhaften Cluster-Kosten:

```
AWS REGION: eu-central-1 (Frankfurt)

[ Web-Frontend: S3 Static Website + CloudFront (HTTPS / WAF Basic) ]
                │
                ▼
[ Amazon API Gateway (HTTP API - Free Tier: 1 Mio. Calls/Monat) ]
                │
    ┌───────────┴───────────┐
    ▼                       ▼
[ Lambda Ingestion ]  [ Lambda Evaluation/Chat ]
- Prüft PII/Maskierung - Lädt Spec + Workspace-Filter
- Extrahiert Text     - Hybrid Vektor-/BM25-Suche
- Chunking & Metadaten - Baut Structured Compliance-Prompt für Bedrock
        │                       │
        ▼                       ▼
[ S3 Storage Bucket ]     [ Amazon Bedrock ]
- /workspaces/{id}/specs/ - Inferenz in Frankfurt
- /knowledge-base/bsi-grundschutz/ - Titan / Claude / Llama
- /indices/{workspace_id}.json - Pay-per-Token (~0,001 €/Query)
        │
        ▼
[ Compliance Report ]
```

Die entscheidenden Free-Tier-Designentscheidungen:

1. *Kein OpenSearch Serverless (Spart ~170 €/Monat!):* OpenSearch Serverless berechnet ein Minimum von 2 bis 4 OCUs pro Stunde. Für Demos und Evaluierungen reicht:
   - *Option A (Simpel & 0 €):* Ein vorberechneter Vektor-Index (z. B. FAISS/NumPy oder SQLite mit sqlite-vss), der als Datei im S3-Bucket liegt und von der Lambda-Funktion bei Bedarf in den RAM geladen wird.
   - *Option B (Serverless DB):* *Amazon DynamoDB* (25 GB + 25 RCU/WCU dauerhaft kostenlos) speichert Dokument-Chunks und Metadaten; Vektor-Embeddings oder Keyword-Lookups laufen direkt darüber oder über einen kostenlosen Cloud-Vektor-Service (z. B. Pinecone/Qdrant Free Tier).
2. *Compute:* *AWS Lambda* (1 Million Aufrufe/Monat dauerhaft im Free Tier).
3. *Storage:* *Amazon S3* (5 GB Standard-Speicher im Free Tier) mit SSE-KMS verschlüsselt.
4. *LLM & Embeddings:* *Amazon Bedrock* (nur Tokens zahlen; typische Tests kosten über Wochen hinweg weniger als 1–2 Euro).

### 3. Der 6-Wochen-Fahrplan

- *Phase 1: Fachkonzept, Compliance-Mapping & Architektur (Woche 1, Halbtags, 18 Std.)* – Definition des Anwendungsfalls, BSI/DSGVO-Compliance-Matrix, Auswahl von 3–4 Grundschutz-Bausteinen, High-Level-Architektur.
- *Phase 2: Detaillierte System Spec & ADRs (Woche 2, Halbtags, 18 Std.)* – ADRs (Vektor-Storage-Wahl, Bedrock-Region, Datenresidenz, Mandantentrennung), API-Spezifikation (OpenAPI/Swagger), Prompt-Schema für Audit-Reports.
- *Phase 3: IHK-Dokumentation & Präsentations-Entwurf (Woche 3, Halbtags, 18 Std.)* – Schriftliches Konzept, Foliensatz (Business Value, FinOps, Sicherheitskonzept, Architekturdiagramme). Meilenstein: Konzeptabnahme.
- *Phase 4: IaC-Fundament & Storage/Ingestion (Woche 4, Vollzeit, 38 Std.)* – AWS-Konto mit Budget-Alarmen (5 €), Terraform-Module für S3/IAM/SQS/Lambda, Parsing- und Chunking-Pipeline.
- *Phase 5: RAG-Logik, Bedrock & Workspace-Evaluation (Woche 5, Vollzeit, 38 Std.)* – Integration Amazon Bedrock, Workspace-Konzept, Prompt-Engine für Compliance-Gap-Report.
- *Phase 6: UI, End-to-End Test, Video-Demo & Polishing (Woche 6, Vollzeit, 38 Std.)* – Web-Frontend, End-to-End-Testing, 3-Minuten-Videodemo, Feinschliff.

### 4. Was die IHK-Prüfer & Behörden-Recruiter sehen wollen

1. *Wirtschaftlichkeit (FinOps):* Vergleichstabelle Klassischer Ansatz (~250 €/Monat) vs. Serverless (< 2 €/Monat).
2. *Sicherheitskonzept:* Schichtenmodell (Netzwerk/Transport: TLS 1.3, API Gateway Throttling; Daten: CMK-KMS mit Rotation, S3 Block Public Access; Identität: getrennte IAM-Rollen; KI-Governance: keine Trainingsnutzung durch Bedrock, Anti-Halluzinations-Prompts).
3. *Workspace-Trennung:* Multi-Tenancy über logische Pfade und IAM Session Tags.

---

## 2. Betreff: "Modul 4 Praxisprojekt: knowledge base automatisch generieren"
**Datum/Uhrzeit:** 2026-09-18 17:44:05 (UTC)

Die gesamte BSI-Knowledge-Base von Hand zu tippen oder mühsam aus PDFs zu kopieren, wäre ineffizient und fehleranfällig. Für automatisierte Compliance-Pipelines gibt es zwei hocheffektive Wege: *Offizielle maschinenlesbare Quellen des BSI (OSCAL/JSON)* oder eine *automatisierte LLM-Synthese-Pipeline* mit AWS Bedrock.

### Strategie 1: Offizielle BSI-Quelldaten nutzen (Der eleganteste Weg)

Das BSI stellt den modernisierten IT-Grundschutz (Grundschutz++) über die offizielle *Stand-der-Technik-Bibliothek* auf GitHub direkt als maschinenlesbare *OSCAL-JSON- bzw. XML-Struktur* bereit:

- *Repository:* github.com/BSI-Bund/Stand-der-Technik-Bibliothek
- *Format:* *OSCAL* (Open Security Controls Assessment Language – der weltweite NIST/BSI-Standard für maschinenlesbare Sicherheitskontrollen).

Mit einem kurzen Python-Skript holst du dir alle Bausteine, filterst nach relevanten Schlagworten (Cloud, Netzwerk, Speicher, Kryptografie) und speicherst sie sofort als mundgerechte JSON-Chunks in S3:

```python
import requests
import json

# Offizielle OSCAL/JSON-Quelle des BSI
OSCAL_URL = "https://raw.githubusercontent.com/BSI-Bund/Stand-der-Technik-Bibliothek/main/.../grundschutz.json"

def fetch_and_filter_bsi():
    data = requests.get(OSCAL_URL).json()
    knowledge_base = []

    for control in data.get("catalog", {}).get("controls", []):
        cid = control.get("id")
        title = control.get("title")
        description = control.get("prose", "")

        if any(prefix in cid for prefix in ["OPS.1.1.2", "NET.1.1", "APP.4", "CON.2", "SYS.1"]):
            knowledge_base.append({
                "bsi_id": cid,
                "titel": title,
                "vorgabe": description,
                "keywords": [w for w in ["encryption", "subnet", "tls", "backup"] if w in description.lower()]
            })

    with open("bsi_knowledge_base.json", "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

fetch_and_filter_bsi()
```

### Strategie 2: LLM-gestützte Synthese-Pipeline (Data Augmentation)

Rohe Gesetzestexte enthalten oft keine konkreten AWS-Implementierungshinweise. Um die Rohdaten anzureichern, lässt du *Amazon Bedrock (Claude 3.5 Sonnet/Haiku)* einmalig über die BSI-Bausteine laufen und für jede Anforderung automatisch konkrete AWS-Must-Haves und No-Gos generieren:

```
[ BSI Roh-Anforderung (OSCAL/JSON) ]
                 │
                 ▼
     [ AWS Bedrock Inferenz ]
  "Mappe diesen BSI-Baustein auf konkrete AWS-Architekturmerkmale (Compliant vs Non-Compliant)"
                 │
                 ▼
[ Strukturierter Chunk inkl. AWS-Mapping & Embeddings ]
                 │
                 ▼
      [ S3: /knowledge-base/*.json ]
```

Automatisches Generierungsskript (build_kb.py):

```python
import boto3
import json

bedrock = boto3.client("bedrock-runtime", region_name="eu-central-1")

PROMPT_TEMPLATE = """
Du bist Chef-Architekt für BSI IT-Grundschutz und AWS.
Formatiere folgende BSI-Anforderung in einen strukturierten JSON-Datensatz für eine RAG-Knowledge-Base.

BSI-Anforderung:
{raw_requirement}

Gib AUSSCHLIESSLICH valides JSON in folgendem Format zurück:
{{
  "bsi_ref": "ID",
  "topic": "Themenbereich",
  "bsi_summary": "1-2 prägnante Sätze zur Soll-Vorgabe",
  "aws_compliant_patterns": ["Konkreter AWS Dienst + Konfiguration"],
  "aws_violations": ["Anti-Pattern, das gegen diese Regel verstößt"],
  "detection_keywords": ["suchbegriff1", "suchbegriff2"]
}}
"""

def augment_with_bedrock(raw_text):
    response = bedrock.converse(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        messages=[{"role": "user", "content": [{"text": PROMPT_TEMPLATE.format(raw_requirement=raw_text)}]}]
    )
    content = response["output"]["message"]["content"][0]["text"]
    return json.loads(content)
```

### Strategie 3: Vector Embeddings in einem Durchgang generieren

```python
def generate_embedding(text: str):
    body = json.dumps({"inputText": text})
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        contentType="application/json",
        accept="application/json",
        body=body
    )
    return json.loads(response["body"].read())["embedding"]

embeddings_index = []
for item in knowledge_base:
    vector = generate_embedding(f"{item['titel']}: {item['bsi_summary']}")
    embeddings_index.append({"bsi_ref": item["bsi_ref"], "vector": vector, "payload": item})

with open("kb_index.json", "w") as f:
    json.dump(embeddings_index, f)
```

### Was du damit für IHK und Behörden-Bewerbungen erreichst

1. *Revisionssichere Herkunft (Data Provenance):* Nachweis im IHK-Bericht: „Die Daten stammen direkt aus den maschinenlesbaren OSCAL-Katalogen des BSI-GitHub-Repositorys, nicht aus willkürlichen Internetquellen.“
2. *Vollautomatischer Build-Prozess:* Das gesamte Knowledge-Base-Deployment lässt sich als Terraform- oder Python-Schritt in CI/CD abbilden (`make build-kb`).
3. *Null laufende Kosten:* Die fertige `kb_index.json` ist für 50–100 Kernbausteine nur wenige Megabyte groß, liegt für Bruchteile von Cent in S3 und wird von der Lambda-Funktion blitzschnell im Speicher durchsucht.

---

## 3. Betreff: "Modul 4 Praxisprojekt - Spezifikation und Design"
**Datum/Uhrzeit:** 2026-09-18 18:10:41 (UTC)

# System-Spezifikation & Architektur-Design: GovCloud Compliance & Architecture Copilot

### 1. Fachliche Spezifikation

**Zielsetzung & Problemstellung:** Im behördlichen Sektor verzögern manuelle Sicherheitsüberprüfungen und unklare Vorgaben Cloud-Projekte erheblich. Der *GovCloud Compliance Copilot* fungiert als automatisierte Shift-Left-Prüfinstanz: Er evaluiert Architektur-Spezifikationen bereits in der Entwurfsphase gegen BSI IT-Grundschutz und DSGVO, deckt Konfigurationsfehler vor der Bereitstellung auf und liefert strukturierte Behebungsempfehlungen mit Fundstellen.

**Kern-Anwendungsfälle (Use Cases):**

- *UC-1 (Multi-Workspace Management):* Mandantenfähige Trennung von Projekten (z. B. Bürgerportal-Core, Justiz-Register-DB), inklusive isolierter Ablage von Entwürfen und Prüfberichten.
- *UC-2 (Automatisierte Spezifikations-Evaluation):* Analyse unstrukturierter Architektur-Beschreibungen (Markdown/Text) gegen hinterlegte regulatorische Kontrollbausteine mit standardisierter Ampel-Bewertung (PASS, WARN, FAIL).
- *UC-3 (Interaktiver Compliance-Chat):* Kontextbezogene Beantwortung von Architektenfragen zur Behebung von Mängeln unter striktem Zitierzwang (Closed-Domain RAG).
- *UC-4 (Automatisierte Knowledge-Base-Kuration):* Kontinuierliches Einpflegen, Anreichern und Vektorisieren von Regelwerken via CI/CD ohne manuelle Datenbankpflege.

**Funktionale Anforderungen:**

- *Deterministische Vorprüfung:* Automatisches Erkennen und Maskieren personenbezogener Daten (PII) sowie sofortiger Abbruch bei harten Regelverletzungen (z. B. unzulässige AWS-Regionen).
- *Strikte Schema-Treue:* Audit-Ergebnisse müssen als typisiertes JSON-Objekt zur maschinellen Weiterverarbeitung vorliegen.
- *Erklärbarkeit:* Jeder Befund verweist auf die genaue BSI-Baustein-Kennung, den Schweregrad und das konkrete Gegenmittel im Cloud-Provider-Kontext.

**Nicht-funktionale Anforderungen & Leitplanken:**

- *FinOps (Zero-Cost Idle):* 100 % serverlose Architektur ohne dauerhaft laufende Cluster (keine VPC-NAT-Gateways, keine OpenSearch-Cluster); Betriebskosten im Leerlauf ≤ 0,00 €/Monat.
- *Datenresidenz & Souveränität:* Ausschließliche Datenhaltung und Inferenz in der AWS-Region Frankfurt (eu-central-1).
- *Latenz:* Audit-Evaluierung innerhalb von < 8 Sekunden; Chat-Antworten < 3 Sekunden.

### 2. Systemarchitektur & Komponenten-Design

Das System folgt einer strikt entkoppelten, zustandslosen Serverless-Architektur über vier Schichten:

```
SCHICHT 1: PRÄSENTATION & INGRESS
[ Single-Page App / Streamlit UI ] ──(HTTPS/TLS 1.3)──► [ Amazon API Gateway (HTTP) ]
                    │
                    ▼
SCHICHT 2: ORCHESTRIERUNG & BUSINESS LOGIK
┌───────────────────┴───────────────────┐
▼                                        ▼
[ Ingestion & Curation Lambda ]   [ Evaluation & Chat Lambda ]
- PII-Sanitizing                 - Workspace-Filter
- OSCAL/JSON-Parser              - In-Memory Cosine Similarity
- Titan-Embedding-Generator      - Tool-Use Schema Enforcer
        │                                │
        ▼                                ▼
SCHICHT 3: PERSISTENZ (S3)        SCHICHT 4: KOGNITIVE DIENSTE
[ Amazon S3 Compliance Bucket ]   [ Amazon Bedrock (eu-central-1) ]
├── /rules/ (Curated BSI JSONs) ◄──── - Amazon Titan Text Embeddings
├── /indices/ (Flat-File Vectors)     - Claude / Mistral via Converse
└── /workspaces/{id}/ (Audit-Logs)      (Strikte Tool-Choice)
```

**Komponenten-Rollen:**

- *Amazon API Gateway (HTTP API):* Zentraler, schlanker Einstiegspunkt. TLS-Terminierung, Throttling, Weiterleitung an Lambdas.
- *Evaluation & Chat Engine (AWS Lambda):* In-Memory-Vektorsuche, Audit-Prompt, erzwingt Ausgabe-JSON via Bedrock Converse API.
- *Unified Compliance Store (Amazon S3):* Regelwerke, vorberechnete Vektoren, Workspace-Spezifikationen.
- *Amazon Bedrock:* Semantisches Verständnis unstrukturierter Architekturbeschreibungen, Gap-Analyse via ephemere Token-Inferenz ohne Modell-Feintuning oder Datenspeicherung.

### 3. Datenarchitektur & Datenfluss

**Ingestion- und Kurations-Fluss (Asynchron):**

1. *Trigger:* Ein Versions-Release im regulatorischen Git-Repository stößt die CI/CD-Pipeline an.
2. *Normalisierung:* Relevante Bausteine (Netzwerk, Storage, Identität, Logging) werden aus dem BSI-Katalog gefiltert.
3. *LLM-Anreicherung:* Bedrock formuliert konkrete Cloud-Must-Haves und Anti-Patterns pro Baustein.
4. *Index-Erstellung:* Titan Embeddings berechnet die Vektoren; das fertige Index-Paket wird als versioniertes Artefakt in S3 abgelegt.

**Evaluierungs-Fluss (Synchron):**

1. *Ingress:* Der Nutzer übermittelt die Architektur-Spezifikation zusammen mit der workspace_id.
2. *Determinismus-Check:* Prüfung auf unzulässige Drittland-Regionen (z. B. us-east-1) und Maskierung gefundener Personendaten.
3. *Retrieval:* Vektor-Index wird aus S3 gestreamt; Cosine-Ähnlichkeit zwischen Spezifikation und BSI-Bausteinen; Top-K-Regeln als Kontext.
4. *Synthese & Tool-Zwang:* Bedrock vergleicht Spezifikation und BSI-Kontext, wird über native Tool-Choice gezwungen, das vorgegebene JSON-Schema als Argument zurückzugeben.
5. *Audit-Logging:* Strukturierter Befundbericht wird unter /workspaces/{id}/reports/ in S3 unveränderbar gespeichert.

### 4. Schnittstellen-Design (API Specification)

**1. POST /workspaces/{id}/evaluate**

- *Zweck:* Führt die vollständige BSI-/DSGVO-Prüfung für einen Workspace durch.
- *Request-Body:* target_cloud (Enum: aws, azure, gcp), target_frameworks (Array: ["bsi_grundschutz", "dsgvo"]), spec_content (String, Rohspezifikation).
- *Response-Body:* overall_status (Enum: PASS, WARN, FAIL), compliance_score (0–100), findings (Array: bsi_ref, severity, title, issue, remediation).

**2. POST /workspaces/{id}/chat**

- *Zweck:* Interaktive Rückfragen zu einem generierten Bericht.
- *Request-Body:* report_id, user_message.
- *Response-Body:* answer, citations (Array referenzierter BSI-Absätze).

### 5. Sicherheits-, Compliance- & Governance-Konzept

- *Identitäts- und Zugriffsmanagement (Least Privilege):* Lambda-Funktionen ohne weitreichende Admin-Berechtigungen; Query-Lambda darf S3-Regeldateien nur lesen (s3:GetObject) und Audit-Reports schreiben (s3:PutObject).
- *Kryptografie:* In-Transit TLS 1.3 + HSTS am API Gateway; At-Rest SSE-KMS für alle S3-Objekte.
- *Revisionssicherheit:* S3-Objektversionierung, ggf. S3 Object Lock für Audit-Pfade.
- *KI-Governance & Anti-Halluzination:* Zero Data Retention bei Bedrock, Closed-Domain Prompting (Antworten strikt auf Retrieval-Kontext beschränkt).

### 6. Architectural Decision Records (ADR-Übersicht)

- *ADR-01:* Verzicht auf verwaltete Vektordatenbanken zugunsten von In-Memory S3 Flat-Files (spart 30–170 €/Monat).
- *ADR-02:* Erzwingung strukturierter Outputs via Bedrock Tool Choice (`toolChoice = required`), 100 % valide Schema-Konformität.
- *ADR-03:* Strikte Datenresidenz in Frankfurt (eu-central-1) gemäß DSGVO Art. 44 ff. und BSI C5.

### 7. Phasenbasierter Umsetzungs- & Testplan

- *Phase A (Woche 1):* S3-Bucket, IAM-Rollen, Ingestion-Pipeline, erster Sync.
- *Phase B (Woche 2):* Evaluation-Lambda, Test der Bedrock Converse Tool-Choice-Logik.
- *Phase C (Woche 3):* API Gateway-Verdrahtung, Preset-UI, finale Dokumentationsartefakte.

---

## 4. Betreff: "Modul 4 Praxisprojekt - Datensätze"
**Datum/Uhrzeit:** 2026-09-18 18:17:51 (UTC)

Der fachliche und regulatorische Wert des Copiloten steht und fällt mit der Qualität, Aktualität und Audit-Festigkeit der zugrunde liegenden Datensätze. In einem behördlichen Prüfungskontext (IHK, BSI-Audit, Vergabe) ist ein RAG-System nur dann vertrauenswürdig, wenn die *Herkunft (Data Provenance)* lückenlos belegbar ist und die Daten vorab von rechtlichem „Rauschen“ befreit wurden.

Die Datenbasis gliedert sich in drei komplementäre Schichten:

```
1. Primär-Regelwerke (BSI & DSGVO) -> Was ist rechtlich/regulatorisch vorgeschrieben? (Soll-Zustand)
2. Technische Baselines (CIS Benchmarks & CSA CCM) -> Wie sieht die technische Umsetzung abstrakt/multi-cloud aus?
3. Provider-Spezifische Implementierungs-Regeln -> Welche konkreten AWS/Azure/GCP-Services & Parameter sind konform?
```

### Datensatz 1: BSI IT-Grundschutz (Infrastruktur & Cloud-Kernbausteine)

- *Relevante Bausteine:* OPS.1.1.2 (Ordnungsgemäße IT-Administration/Cloud-Nutzung), NET.1.1 & NET.1.2 (Netzarchitektur & Netzdesign), APP.4.4 (Kubernetes und Containerisierung), CON.2 (Datenschutz), DER.1 (Detektion von Sicherheitsvorfällen).
- *Quelle:* Offizielles GitHub-Repository github.com/BSI-Bund/Stand-der-Technik-Bibliothek, BSI-Webportal (IT-Grundschutz-Kompendium).
- *Format:* OSCAL-JSON/XML oder strukturierte XML/HTML-Exporte.
- *Kuration:* Noise Reduction (Entfernen organisatorischer Absätze), Normalisierung (atomare Anforderungen: id, level, title, prose), Semantische Anreicherung (Tags zu Cloud-Ressourcentypen).

### Datensatz 2: DSGVO/GDPR (Cloud-relevante Kernartikel)

- *Relevante Artikel:* Art. 5 (Grundsätze), Art. 25 (Data Protection by Design and by Default), Art. 32 Abs. 1 (Sicherheit der Verarbeitung), Art. 44–49 (Drittlandübermittlung).
- *Quelle:* EUR-Lex Portal (eur-lex.europa.eu, CELEX: 32016R0679).
- *Format:* XML/HTML/JSON via EU-Open-Data-API.
- *Kuration:* Juristische Extraktion IT-relevanter Absätze, Übersetzung in technische Imperative (z. B. „angemessenes Schutzniveau“ → „Verschlüsselung At-Rest mit AES-256/RSA-4096, In-Transit TLS ≥ 1.2“), Constraint-Regeln (z. B. Ausschluss von AWS-Regionen außerhalb EU/EWR).

### Datensatz 3: Cloud Security Alliance – Cloud Controls Matrix (CSA CCM v4)

- *Relevante Domänen:* DSP, IAM, IVS, EKM.
- *Quelle:* cloudsecurityalliance.org/artifacts/cloud-controls-matrix-v4/.
- *Format:* XLSX-Tabellen und strukturierte JSON/CSV-Exporte.
- *Kuration:* Extraktion der Querverweise (Mapped Frameworks → CCM-Control-ID mit BSI C5/DSGVO verknüpfen), Bereinigung.

### Datensatz 4: CIS Benchmarks (Center for Internet Security)

- *Relevante Kataloge:* CIS AWS Foundations Benchmark, CIS Microsoft Azure Foundations Benchmark, CIS GCP Foundation Benchmark.
- *Quelle:* cisecurity.org bzw. CIS GitHub Repository.
- *Format:* PDF, Word oder XCCDF/OSCAL.
- *Kuration:* Filterung nach Architektur-Relevanz, Generierung von Positiv-/Negativ-Mustern (Compliant Pattern z. B. aws_s3_bucket_server_side_encryption_configuration mit KMS Key; Violation Pattern z. B. cidr_blocks = ["0.0.0.0/0"] auf Port 22/3306).

### Das finale, kuratierte Datenformat (Unified Audit Chunk)

```json
{
  "chunk_id": "SEC-STORAGE-001",
  "domain": "Data Security & Encryption",
  "regulatory_references": {
    "bsi_grundschutz": ["OPS.1.1.2.A3", "CON.2.A1"],
    "dsgvo": ["Art. 25 Abs. 1", "Art. 32 Abs. 1 a"],
    "csa_ccm": "EKM-02",
    "cis_aws": "2.1.1"
  },
  "rule_title": "Kryptografischer Schutz ruhender Speicherobjekte mit eigener Schlüsselkontrolle",
  "normative_requirement": "Gespeicherte Daten müssen verschlüsselt sein. Der Zugriff auf Schlüssel muss unter ausschließlicher Kontrolle des Betreibers liegen (Customer Managed Keys). Standardverschlüsselungen des Cloud-Providers ohne eigene Schlüsselverwaltung genügen bei erhöhtem Schutzbedarf nicht.",
  "technical_evaluation_matrix": {
    "aws": {
      "compliant": ["SSE-KMS mit Customer Managed Key (CMK)", "KMS Key Policy mit Least Privilege"],
      "non_compliant": ["Unverschlüsselt", "Reines SSE-S3 (Default AWS Key)", "EBS unverschlüsselt"]
    },
    "azure": {
      "compliant": ["Azure Key Vault mit Customer Managed Keys (BYOK)"],
      "non_compliant": ["Platform-Managed Keys", "Public Blob Access"]
    },
    "gcp": {
      "compliant": ["Cloud KMS Customer-Managed Encryption Keys (CMEK)"],
      "non_compliant": ["Google-default KMS ohne eigene Rotation"]
    }
  },
  "deterministic_triggers": {
    "forbidden_keywords": ["unencrypted", "public-read", "us-east-1"],
    "required_keywords": ["kms", "encryption", "cmk"]
  },
  "search_context": "Verschlüsselung S3 Bucket EBS Volume At-Rest KMS CMK Key Management Datenschutz BSI OPS.1.1.2"
}
```

### Warum diese Kuration den wahren Projektwert darstellt

1. *Vermeidung des "Garbage-In, Garbage-Out"-Effekts:* Kuratiertes Schema zwingt zu harten, belegbaren Fakten.
2. *Deterministic Pre-Filtering:* Grobe Verstöße (z. B. unzulässige US-Regionen) werden sofort via Python abgefangen, bevor Bedrock-Tokens verbraucht werden.
3. *Reproduzierbarkeit & Audit-Readiness:* Nachweisbar, wie jede BSI-Zeile in das technische Regelwerk überführt wurde.

---

## 5. Betreff: "Modul 4 Praxisprojekt Risiken"
**Datum/Uhrzeit:** 2026-09-18 18:23:51 (UTC)

Bei einem 6-wöchigen Vorhaben an der Schnittstelle von generativer KI, regulatorischer Compliance und Cloud-Architektur lauern die Risiken selten im Code selbst, sondern in *Scope Creep, Datenqualität, Halluzinationen und Latenz/Kosten*.

### 1. Technische & KI-spezifische Risiken

- *Halluzinationen & falsche Paragrafen-Zuordnung:* Risiko: Modell erfindet BSI-Bausteine oder behauptet fälschlich Konformität. Mitigation: Closed-Domain RAG & Tool-Choice-Zwang; ohne Kontext → Status UNKNOWN/PRÜFBEDARF; striktes JSON-Schema via Tool-Calling.
- *Cold Starts & API-Timeouts bei Lambda:* Risiko: Einlesen des Vektor-Index, Embedding-Berechnung und Inferenz dauern > 10 Sekunden (API Gateway Timeout 29s). Mitigation: Schlanker Vektor-Index (< 1 MB), Lambda mit ≥ 1024 MB RAM.
- *Begrenzte Kontextfenster/Chunking-Verlust:* Risiko: Zusammenhänge über Chunk-Grenzen zerrissen. Mitigation: Scope auf 1–3 Seiten Markdown beschränken.

### 2. Daten- & Kurations-Risiken (Das größte Aufwandsrisiko)

- *Scope-Explosion bei den Regelwerken:* Mitigation: Strikter 80/20-Ansatz – Beschränkung auf 4 Kern-BSI-Bausteine (OPS.1.1.2, NET.1.1, SYS.1.5, CON.2) und 4 DSGVO-Artikel (5, 25, 32, 44).
- *Schlechte Datenqualität/unstrukturierte BSI-Vorlagen:* Mitigation: Fallback mit 10 handkuratierten Referenz-Regeln als lokales JSON (fallback_rules.json).

### 3. FinOps & Kostenfallen (Free-Tier-Gefahren)

- *Unbeabsichtigte AWS-Kostenblöcke:* Mitigation: Ausschließlich reine Serverless-Primitives, AWS Budget Alert bei 5,00 €.
- *Token-Runaways bei Bedrock:* Mitigation: Hartes Token-Limit (max_tokens: 1500), Rate Limiting am API Gateway (max. 10 Requests/Minute).

### 4. Zeitplan- & Prüfungs-Risiken (IHK/Vorstellungsgespräch)

- *Das Frontend-Verschleppungs-Risiko:* Mitigation: Bis Woche 5 nur gegen API/CLI testen; UI in Woche 6 mit Streamlit oder statischer HTML.
- *Überkomplizierte Multi-Cloud-Verzettelung:* Mitigation: AWS als Referenz-Implementierung (Prio 1) vollständig bauen; Azure/GCP nur konzeptionell.

### Risikomatrix & Maßnahmen-Checkliste

| Risiko | Wahrscheinlichkeit | Auswirkung | Primäre Gegenmaßnahme |
|---|---|---|---|
| Kurationsaufwand explodiert | Hoch | Kritisch | Scope auf max. 4 Bausteine kappen; LLM-Kuration nutzen |
| Frontend kostet zu viel Zeit | Hoch | Mittel | Streamlit-Preset-UI statt komplexer React-App |
| AWS-Kosten überschreiten Budget | Niedrig | Mittel | AWS Budget Alert (5 €); Verzicht auf NAT/VPC-Endpunkte |
| KI halluziniert falsche Regeln | Mittel | Kritisch | Bedrock Tool-Calling-Zwang; Pydantic-Output-Validierung |
| API Gateway Timeouts | Mittel | Hoch | In-Memory Flatfile-Suche; kein schwerer Vektor-Cluster |

---

## 6. Betreff: "Modul 4 Praxisprojekt: vollständig und akurat"
**Datum/Uhrzeit:** 2026-09-18 18:50:11 (UTC)

### Wie du echte Vollständigkeit & Akuratheit garantierst

Die größte Sorge bei RAG im regulatorischen Umfeld ist: „Das System übersieht eine kritische BSI-Regel (unvollständig) oder interpretiert eine Vorschrift falsch (unakkurat).“

Das löst du durch vier deterministische Architekturschichten:

**A. Vollständigkeit: Multi-Chunking & Full-Rule-Coverage statt reiner Vektorsuche**

- *Lösung (Hybrid Retrieval):* Kombiniere semantische Vektorsuche mit deterministischem Keyword-/Tag-Matching. Enthält die Spezifikation das Wort S3/Storage/Volume/Bucket, werden die Chunks zu OPS.1.1.2.A3 *immer* geladen – unabhängig vom Vektorsuche-Score.
- Da die kuratierte Knowledge Base nur ca. 20–30 Kernregeln umfasst, kann Bedrock bei einer Prüfung sogar *alle Kernregeln der betroffenen Domäne* auf einmal erhalten.

**B. Akuratheit: Closed-Domain Framing & Few-Shot-Beispiele**

- *Keine Halluzinationen:* „Bewerte ausschließlich auf Basis der mitgelieferten Regeln. Ist ein Aspekt nicht erwähnt, markiere ihn als UNKLAR/PRÜFBEDARF, aber erfinde keine Annahmen.“
- *Few-Shot Prompting:* Zwei vorab definierte Beispiele (Negativbeispiel: Public Subnet mit DB → Verstoß NET.1.1.A8; Positivbeispiel: Private Subnet + KMS → Konform mit OPS.1.1.2.A3).

**C. Syntaktische Akuratheit: Tool-Calling-Zwang (JSON)**

- Native Bedrock Converse Tool-Choice API zwingt das Modell in vordefinierte Typen (overall_status, bsi_ref, severity, issue, remediation). Python prüft das Objekt mit pydantic; bei Fehlern schlägt der Code fehl statt fehlerhafte Daten zu liefern.

**D. Manuelle Audit-Prüfschleife (Ground Truth Validation)**

Ein Testdatensatz aus 5 festen Test-Architekturen:

- Test 1: Absichtlich unverschlüsselter S3 Bucket → Muss FAIL auf OPS.1.1.2.A3.
- Test 2: Bereitstellung in us-east-1 → Muss FAIL auf CON.2.A1.
- Test 3: Vollständig konforme 3-Tier-Architektur in Frankfurt → Muss PASS sein.
- Test 4: Fehlendes Egress-Filtering → Muss WARN auf NET.1.1.
- Test 5: Unvollständige Spezifikation → Muss auf Informationslücken hinweisen.

Diese 5 Fälle automatisch mit pytest durchlaufen lassen; wenn alle grün, empirischer Nachweis für Akkuratheit und Vollständigkeit.

**Fazit für das Design:**

- SQS nutzen, falls Datei-Uploads asynchron verarbeitet werden sollen (Timeout-Schutz).
- Inhaltliche Qualität sichern durch: Deterministisches Regel-Tagging, strikte System-Prompts mit Few-Shot-Beispielen, automatisierte pytest-Validierung gegen 5 Referenz-Architekturen.

---

## 7. Betreff: "Modul 4 Praxisprojekt Präsentation"
**Datum/Uhrzeit:** 2026-09-18 18:58:43 (UTC)

Ein vollständiger, prüfungsfertiger Präsentationsentwurf für den *IHK Cloud Business Expert* (ca. 15 Minuten Vortrag + 15 Minuten Fachgespräch). Aufbau: Wirtschaftlicher & strategischer Business Case, Architektur- & Governance-Entscheidungen, FinOps/Qualitätssicherung/Projekterfolg.

### Folien-Übersicht & Zeitmanagement (15 Minuten)

| Folie | Thema | Fokus | Zeit |
|---|---|---|---|
| 1 | Titelblatt | Einordnung, Rollenverständnis & Leitmotiv | 1 min |
| 2 | Ausgangslage & Business Problem | Compliance-Hürden im öffentlichen Dienst | 2 min |
| 3 | Strategischer Lösungsansatz | Shift-Left Compliance, Cloud-Governance | 1.5 min |
| 4 | Facharchitektur & Datenbasis | BSI, DSGVO, CIS als strukturierte Daten | 2 min |
| 5 | Cloud-Architektur (AWS eu-central-1) | Serverless Event-Driven Design | 2.5 min |
| 6 | KI-Governance & Anti-Halluzination | Bedrock Converse API, Tool-Choice | 2 min |
| 7 | FinOps & Wirtschaftlichkeitsanalyse | Klassisch vs. Serverless, TCO | 2 min |
| 8 | Qualitätssicherung & Testergebnisse | Determinismus, Pytest Ground Truth | 1.5 min |
| 9 | Fazit & Ausblick | Business Value, Multi-Cloud-Perspektive | 0.5 min |

### Detaillierter Folien-Entwurf (Auszug)

**Folie 1: Titelblatt & Agenda** – Titel: GovCloud Compliance & Architecture Copilot. Kontext: Abschlusspräsentation IHK Cloud Business Expert.

**Folie 2: Problemstellung** – Späte Prüfungen, hohe Kosten & Verzögerungen, Expertenmangel. Kernbotschaft: „Sicherheit und Compliance müssen vom ersten Architekturentwurf an automatisiert mitgedacht werden – nicht erst im Audit.“

**Folie 3: Lösungsansatz** – Shift-Left Compliance-as-a-Service, RAG-Copilot analysiert Entwürfe während der Designphase.

**Folie 4: Fachkonzept & kuratierte Knowledge Base** – Grundsatz: Garbage-In, Garbage-Out. Quellen: BSI OSCAL, DSGVO Kernartikel, CIS/CSA CCM Muster. Automatisierte Ingestion via GitHub Actions.

**Folie 5: Zielarchitektur auf AWS** – Strikte Datenresidenz (Frankfurt), Zero-Cost Idle Pattern, vollständige Entkopplung.

**Folie 6: KI-Governance** – Syntaktischer Zwang (Tool Choice), Closed-Domain RAG, deterministische Vorfilter.

**Folie 7: FinOps & Wirtschaftlichkeitsanalyse:**

| Kostenblock | Klassischer Enterprise-Stack | Serverless-Architektur |
|---|---|---|
| Vektordatenbank | OpenSearch Serverless (~170 €/Monat) | S3 Flat-File/In-Memory (0,00 €) |
| Compute/Backend | EC2/ECS dauerhaft (~40 €/Monat) | AWS Lambda (Free Tier: 0,00 €) |
| Netzwerk/Ingress | NAT Gateway + ALB (~50 €/Monat) | HTTP API Gateway (Free Tier: 0,00 €) |
| KI-Modell | Dedizierte SageMaker-Instanz (~300 €/Monat) | Bedrock Pay-per-Token (~0,001 €/Prüfung) |
| **Gesamt/Monat** | **~560 € Fixkosten** | **≤ 1–2 € variable Tokenkosten** |

**Folie 8: Qualitätssicherung & Testergebnisse** – 3 pytest-Testfälle (Unsichere Legacy-App, Drittlandtransfer, Konforme 3-Tier App). Ergebnis: 100 % valide Schema-Einhaltung.

**Folie 9: Fazit** – „Mit diesem System transformieren wir Compliance von einem reaktiven Kontrollorgan zu einem beschleunigenden Enabler moderner Cloud-Projekte.“

### Mögliche Fragen im Fachgespräch (Prüfer-Perspektive)

1. „Warum keine dedizierte Vektordatenbank wie Pinecone/OpenSearch?“ → FinOps- und Wartbarkeitsgründe, unter 100 atomare Bausteine passen in Lambda-RAM.
2. „Wie stellen Sie sicher, dass keine sensiblen Daten über Bedrock in fremde Hände geraten?“ → eu-central-1, keine Trainingsnutzung, PII-Filter vorab.
3. „Was passiert, wenn sich ein BSI-Baustein ändert?“ → Compliance-as-Code via GitHub Actions Pipeline, automatisches Update ohne Ausfallzeit.

---

## 8. Betreff: "Modul 4 Praxisprojekt Vollständigkeit"
**Datum/Uhrzeit:** 2026-09-18 19:10:23 (UTC)

In Standard-RAG-Systemen ist das klassische *Top-K-Retrieval das größte Einfallstor für Unvollständigkeit*: Wenn eine 2-seitige Architektur eingereicht wird und das System per Vektorsuche starr nur die besten 3 Chunks abruft, werden übrige relevante Kontrollen ignoriert. Für ein Audit ist das fatal.

Vollständigkeit wird über ein *vierstufiges, deterministisches Sicherheitsnetz* garantiert:

### 1. Das „Bounded Catalog“-Prinzip

Präzise abgegrenzter Zielkatalog (25–35 Kernkontrollen aus BSI OPS.1.1.2, NET.1.1, APP.4.4, SYS.1.5, CON.2). Ein BSI-Chunk umfasst ca. 100–150 Tokens; alle 30 Kernregeln zusammen ca. 3.500–4.500 Tokens (Bedrock-Kontextfenster: 200.000 Tokens). *Domain-Wide Multi-Rule Pass:* Bei Betroffenheit eines Themenbereichs werden ausnahmslos alle Kontrollen dieser Domäne übergeben.

### 2. Zwei-Phasen-Evaluation: Extraktion vor Auditierung

```
[ Architektur-Spezifikation ]
               │
               ▼
PHASE 1: Komponenteninventur (Entity & Service Extraction)
- Welche AWS-Services werden genannt?
- Welche Zonen/Netzwerke sind beschrieben?
- In welcher Region liegt der Entwurf?
- Welche Komponenten FEHLEN komplett?
               │
    Gegenprüfung gegen BSI-Prüfmatrix
               ▼
PHASE 2: Checklisten-Audit (Garantierte Abdeckung)
Jede identifizierte Komponente wird gegen die gesamte zugehörige BSI-Kategorie evaluiert.
```

Beispiel: Text erwähnt „RDS PostgreSQL und S3“ → Pipeline erzwingt Prüfung gegen exakt 4 BSI-Regeln (OPS.1.1.2.A3, OPS.1.1.2.A4, NET.1.1.A8, OPS.1.1.2.A9) als Checkliste.

### 3. Explizite Erfassung von Unterlassungen („Negative Requirements“)

System-Prompt: „Für jede vorgelegte BSI-Kontrolle musst du einen von drei Zuständen deklarieren: 1. COMPLIANT, 2. VIOLATION, 3. MISSING_INFORMATION/PRÜFBEDARF. Es ist unzulässig, eine Regel unbewertet zu lassen.“ Fehlt z. B. eine Angabe zur Verschlüsselung, lautet das Ergebnis nicht „keine Fehler“, sondern [WARN] Prüfbedarf.

### 4. Deterministische Schema-Vollständigkeit via Tool-Zwang & Pydantic

```python
expected_rules = {"OPS.1.1.2.A3", "NET.1.1.A8", "CON.2.A1", "SYS.1.5.A2"}
evaluated_rules = {finding.bsi_ref for finding in report.findings}

missing = expected_rules - evaluated_rules
if missing:
    raise IncompleteAuditException(f"Folgende Kontrollen wurden nicht evaluiert: {missing}")
```

### Zusammenfassung für die IHK-Prüfung

1. Kein blindes Top-K – themenbezogene Kontrollen als vollständige Checkliste.
2. Systematische Inventur – Komponenten deterministisch auf BSI-Bausteine gemappt.
3. Auditierung von Lücken – fehlende Details als Prüfbedarf erfasst.
4. Code-Validierung – Pydantic prüft, ob jede BSI-ID im Bericht beantwortet wurde.

---

## 9. Betreff: "Modul 4 Praxisprojekt Datensätze in ingest und chat"
**Datum/Uhrzeit:** 2026-09-18 19:33:34 (UTC)

Die Zusammenführung (Datenfusion) der vier heterogenen Quellen erfolgt in zwei Betriebsmodi: *Asynchron beim Ingest (Kompilation zu einem einheitlichen Datenmodell)* und *Laufzeit-Fusion beim Chat/Evaluation (Kontext-Montage für die Inferenz)*.

### Modus 1: Die Zusammenführung beim Ingest (Build-Time Compilation)

```
1. BSI OSCAL (Rechtspflicht DE)     ──┐
2. DSGVO EUR-Lex (Recht EU)         ──┼─► [ Ingestion-Pipeline ] ──► [ Unified Audit Rule (JSON) ]
3. CSA CCM v4 (Taxonomie & Map)     ──┤    (Python + Bedrock)         ├── bsi_ref & dsgvo_ref
4. CIS Benchmarks (AWS-Messlatte)   ──┘                               ├── csa_taxonomy
                                                                       ├── aws_cis_rules (Gut/Schlecht)
                                                                       └── embedding_vector (Titan V2)
```

Der 3-Schritte-Fusionsprozess:

1. *CSA CCM als Anker (Join-Schlüssel):* CCM enthält bereits Mappings zu ISO 27001, BSI C5, DSGVO. Jede Kontroll-ID (z. B. EKM-02) bildet den primären Knotenpunkt.
2. *Attribut-Anreicherung:* Rechts-Schicht (deutscher BSI-Text + DSGVO-Artikel), Härtungs-Schicht (CIS-Benchmark-Parameter als technischer Maßstab).
3. *Kombinierte Vektorisierung (Titan Embeddings):* Kompakter, semantisch dichter Search-String aus allen vier Dimensionen (z. B. "Storage Encryption ruhende Daten BSI OPS.1.1.2.A3 DSGVO Art. 32 CSA EKM-02 CIS AWS 2.1.1 S3 Bucket KMS CMK At-Rest").

### Das fusionierte Datenartefakt (curated_rules.json)

```json
{
  "rule_id": "SEC-STORAGE-001",
  "anchors": {
    "bsi_it_grundschutz": "OPS.1.1.2.A3",
    "dsgvo": "Art. 32 Abs. 1 a",
    "csa_ccm_v4": "EKM-02",
    "cis_aws_benchmark": "2.1.1"
  },
  "normative_scope": "Ruhende Speicherobjekte müssen nach Stand der Technik kryptografisch gesichert sein. Schlüsselverwaltung muss beim Betreiber liegen.",
  "technical_ground_truth": {
    "compliant_criteria": "S3-Bucket nutzt SSE-KMS mit Customer Managed Key (CMK); KMS Key Rotation aktiv.",
    "violation_criteria": "S3 unverschlüsselt oder reines Standard-SSE-S3 (AWS-Managed Key) bei erhöhtem Schutzbedarf."
  },
  "remediation_guideline": "KMS Key erstellen, Bucket Policy anpassen: aws_s3_bucket_server_side_encryption_configuration mit kms_master_key_id.",
  "search_vector": [0.012, -0.043, 0.089, "..."]
}
```

### Modus 2: Die Zusammenführung beim Chat/Audit (Runtime Context Montage)

```
[ Architekten-Anfrage / Spezifikation ]
                  │
                  ▼
   [ Hybrid Retrieval aus S3-Index ] (Findet Regel "SEC-STORAGE-001")
                  │
                  ▼
PROMPT ASSEMBLY (Laufzeit-Fusion)
1. Normative Rolle definieren (BSI + DSGVO Pflicht)
2. Technische Messlatte injizieren (CIS Kriterien)
3. Nutzerkontext einbetten (Die Spezifikation)
4. Tool-Call Zwang für strukturiertes JSON
                  │
                  ▼
        [ Amazon Bedrock Converse Inferenz ]
                  │
                  ▼
AUDIT REPORT / CHAT ANTWORT
"Nicht konform mit BSI OPS.1.1.2.A3 / DSGVO Art. 32: Gemäß CIS AWS 2.1.1 genügt SSE-S3 nicht..."
```

Wie Bedrock die 4 Quellen im Dialog verwendet:

1. *Juristischer Anker für den Status:* BSI und DSGVO bestimmen, ob ein Verstoß vorliegt und wie schwer er ist.
2. *Technisches Urteil durch CIS:* Vergleich mit technical_ground_truth-Kriterien.
3. *Exakte Fundstellen-Synthese:* IDs werden direkt aus den Chunk-Metadaten montiert, nichts wird frei erfunden.

### Warum diese Trennung das Projekt auszeichnet

- *Performance:* Aufwendiges Verknüpfen passiert einmalig vorab beim Ingest.
- *Zero Run-Time Latency:* Lambda lädt ein fertiges JSON-Objekt statt mehrerer Datenbankabfragen.
- *100 % Audit-Festigkeit:* Jeder Befund nennt Gesetzesparagraf (Warum) und CIS-Konfigurationsbefehl (Wie).

---

## 10. Betreff: "Modul 4 Praxisprojekt Erweiterter Behördenkatalog"
**Datum/Uhrzeit:** 2026-09-18 19:50:13 (UTC)

Erweiterter Behörden-Katalog (ca. 35–45 atomare Regeln gesamt):

| Domäne | BSI-Baustein/Standard | Typische Cloud-Kontrolle |
|---|---|---|
| Web & Apps | APP.3.1 (Webanwendungen), OWASP Top 10 | WAF, TLS 1.3, DDoS-Schutz, API Gateway Auth (JWT) |
| Mobile | SYS.3.2.2 (Mobilgeräte), OWASP Mobile Top 10 | Certificate Pinning, No Plaintext Token Storage |
| Analytics & Big Data | APP.4.3 (Relationale DBs), APP.4.6 (Data Warehouse) | Data Lineage, Maskierung, Least Privilege S3 ACLs |
| AI/Machine Learning | BSI KI-Leitfaden, NIST AI RMF, EU AI Act | Model Poisoning Schutz, keine PII im Training |
| Identity & IAM (Unverzichtbar!) | ORP.4 (Identitäts- & Rechtemanagement) | MFA erzwungen, Rollen statt statischer Keys |
| CI/CD & DevOps (Unverzichtbar!) | OPS.1.1.6 (Softwareentwicklung & Tests) | Image Vulnerability Scan, Secrets nicht im Git-Repo |

---

## 11. Betreff: "Modul 4 Praxisprojekt pocock teach skill und lmnotebook"
**Datum/Uhrzeit:** 2026-09-18 20:14:24 (UTC)

Claude Code (mit dem Pocock /teach-Prinzip) und NotebookLM sollen nicht als passive Helfer, sondern als *permanentes Prüfungskomitee* eingesetzt werden, um das Fachwissen aktiv während der Entstehung des Codes zu erarbeiten.

### Die Arbeitsteilung: Claude Code vs. NotebookLM

| Werkzeug | Rolle im Projekt | Primärer Zweck |
|---|---|---|
| Claude Code (/teach) | Interaktiver Sokratischer Prüfer & Sparring-Partner im Terminal | Zwingt bei jedem Commit zur Begründung; simuliert das Fachgespräch live |
| NotebookLM | Regulatorischer Wissens-Zwilling (Ground Truth Engine) | Verschlingt Roh-PDFs/JSONs, generiert Audio-Deep-Dives, FAQ-Listen |

### Teil 1: Claude Code als Prüfer konfigurieren (CLAUDE.md)

Matt Pococks /teach-Philosophie basiert auf sokratischem Dialog. Im Root-Verzeichnis wird eine `CLAUDE.md` angelegt:

```
# GOVCLOUD COPILOT - SOCHRATE & IHK-EXAMINER PROTOCOL

Du begleitest mich als strenger, wohlwollender IHK-Prüfer und Cloud-Chefarchitekt
nach dem Pocock /teach-Prinzip durch die Phasen:
1. Konzeption & Spezifikation
2. Datenfusion & Ingestion
3. Implementation (Terraform, Lambda, Bedrock Tool-Calling)
4. Qualitätssicherung & Fachgesprächs-Vorbereitung

## VERHALTENSREGELN FÜR CLAUDE CODE:

### 1. Kein "Silent Vibe Coding"
- Wenn ich dich bitte, ein Modul, eine IAM-Policy oder eine Funktion zu schreiben,
  generiere den Code, aber blockiere den Abschluss mit 1–2 gezielten Verständnisfragen:
  * "Warum haben wir hier diese IAM-Action gewählt und keine Wildcard?"
  * "Welche Auswirkung hat diese Entscheidung auf BSI OPS.1.1.2 oder CIS 2.1?"
  * "Welchen FinOps-Trade-off gehen wir hier ein?"

### 2. Der "Explain-Back"-Zwang (Pocock Teach Loop)
- Bei komplexen Konzepten (z. B. In-Memory Cosine Similarity, Bedrock Converse Tool-Choice,
  GitHub OIDC): "Erkläre mir in 2 Sätzen mit eigenen Worten, wie X funktioniert."
- Korrigiere meine Antwort und bringe exakte Prüfungsbegriffe ein
  (z. B. Execution Context Reuse, Cold Start Mitigation, Deterministic Guardrails).

### 3. Tägliches 5-Minuten-Fachgespräch
- Bei `/ihk-check` oder `/teach-review`:
  * Nimm die Rolle des BSI-Auditors ein.
  * Stelle 3 aufeinander aufbauende Prüfungsfragen zum aktuellen Git-Stand.
  * Bewerte nach Schulnoten und gib die perfekte Musterantwort.
```

### Teil 2: Wie der Workflow durch die 4 Projektphasen steuert

- *Phase 1 (Planung & Spezifikation):* Claude Code fragt z. B. „Warum haben wir OpenSearch Serverless verworfen?“ → Nutzer formuliert FinOps- und Latenz-Begründung selbst.
- *Phase 2 (Ingestion & Datenkuration):* „Woher nimmt das Modell die Information, dass SSE-S3 nicht reicht? Zeigen Sie mir die Zeile im JSON-Schema, die CIS 2.1 mit BSI OPS.1.1.2 verknüpft.“
- *Phase 3 (Implementation):* „Warum nutzen wir toolChoice = required statt System-Prompting mit Markdown?“
- *Phase 4 (Test & Fachgespräch-Drill):* „Ihr Test für Testfall 2 schlägt fehl. Warum stuft Bedrock das US-Deployment nicht als HIGH ein? Welcher DSGVO-Artikel greift hier?“

### Teil 3: NotebookLM als Audio- & Deep-Dive-Ergänzung

1. Quellen hochladen: BSI IT-Grundschutz Kompendium (Auszug), DSGVO Volltext, CIS AWS Foundations Benchmark v3.0, eigene Projekt-Spezifikationen/ADRs.
2. Audio Overview (Deep Dive Podcast) generieren lassen für unterwegs.
3. Gezielte Prüfer-Prompts eintippen, z. B. „Erstelle eine FAQ-Liste mit den 15 fiesesten Fragen eines Auditors zur Cloud-Verschlüsselung und Datenresidenz, inklusive Fundstellen.“

### Konkreter nächster Schritt

CLAUDE.md im Repository erstellen. Bei zu schnellem Code-Fortschritt: „Stop. Erkläre mir nicht den Code, sondern nutze Pocock /teach: Stelle mir 2 Fragen, damit ich selbst darauf komme, warum wir das architektonisch so lösen müssen.“

---

## 12. Betreff: "Re: Modul 4 Praxisprojekt pocock teach skill und lmnotebook"
**Datum/Uhrzeit:** 2026-09-18 21:25:53 (UTC)
*(Antwort im selben Thread wie E-Mail 11)*

# SPRACH- & ERKLÄR-RICHTLINIEN FÜR DEN NUTZER

1. **Sprache & Tonalität:**
   - Erkläre auf Deutsch in einfacher, klarer Sprache (Niveau: Pragmatischer Senior Engineer).
   - Vermeide akademische Schachtelsätze und unnötigen Fachchinesisch-Ballast.
   - Wenn du ein Fachwort nutzt (z. B. "Execution Context"), erkläre es in einem Halbsatz.

2. **Das "Rule of 3"-Format:**
   - Erkläre niemals in Fließtext-Absätzen über mehr als 3 Zeilen.
   - Nutze maximal 3 prägnante Bulletpoints für Erklärungen.
   - Formel für Code-Erklärungen:
     - Was macht es? (1 Satz)
     - Warum so und nicht anders? (1 Satz, Bezug auf BSI/AWS)
     - Was musst du für das IHK-Gespräch wissen? (1 prägnanter Begriff)

3. **Stopp-Signal:**
   - Wenn ein Konzept neu ist, beende deine Antwort mit einer Verständnisfrage an mich, statt ungefragt 40 Zeilen theoretischen Hintergrund auszuspucken.

*(Es folgt im Anhang der zitierte Originaltext von E-Mail 11 als Zitat.)*

---

## 13. Betreff: "Modul 4 Praxisprojekt free text and syntactic spec and architecture descriptions."
**Datum/Uhrzeit:** 2026-09-19 09:22:04 (UTC)

Detailliertes Konzept für die Erweiterung des Copiloten um *Free-Text- & Syntax-Spezifikationen (OpenAPI/Swagger)* sowie *Architekturen (Text & Terraform HCL)*, unter bewusstem Verzicht auf die Testfall-Generierung.

### 1. Zusätzliche Datenquellen

| Quelle/Standard | Bezugsquelle | Rohdaten-Format | Ziel-Format in S3 |
|---|---|---|---|
| Standard-Datenschutzmodell (SDM V3.0) | DSK (datenschutzkonferenz-online.de) | PDF/HTML | sdm_controls.json (Gewährleistungsziele) |
| EDPB Guidelines 4/2019 (Data Protection by Design & Default) | edpb.europa.eu | PDF | edpb_art25.json (Default-Settings, Retention) |
| OWASP API Security Top 10 (2023) | GitHub (owasp/API-Security) | Markdown/YAML/JSON | owasp_api_rules.json (Broken Object Level Auth, Excessive Data Exposure, Mass Assignment) |

Alle Chunks werden im bestehenden S3-Bucket unter `s3://<bucket-name>/knowledge-base/` (Frankfurt) versioniert abgelegt.

### 2. Änderungen in der Kuration (Ingestion Pipeline)

Das Schema wird um den *Prüfhorizont* (target_phase) erweitert:

```json
{
  "rule_id": "SDM-MIN-001",
  "target_phase": "SPECIFICATION",
  "domain": "DATA_PRIVACY",
  "anchors": { "dsgvo": "Art. 5 Abs. 1 c", "sdm": "Gewährleistungsziel Datenminimierung" },
  "technical_ground_truth": {
    "compliant_criteria": "Payloads erfassen nur transaktionsnotwendige Felder; keine redundanten PII wie Geburtsdatum ohne Altersverifikationszwang.",
    "violation_criteria": "Erfassung sensibler Attribute (z. B. Religion, Gesundheit, Steuernummer) in Standard-Registrierungs- oder Kontakt-Payloads."
  },
  "remediation_guideline": "Entferne das Attribut aus dem OpenAPI `requestBody` oder begründe die Notwendigkeit gem. Art. 6 DSGVO."
}
```

GitHub Actions Workflow parst neben BSI/CIS nun auch SDM- und OWASP-Definitionen; Claude 3.5 Haiku taggt jede Regel mit `target_phase: "SPECIFICATION"` oder `"ARCHITECTURE"`. Die Wissensbasis wächst von ~20 auf ca. 40–50 Chunks (< 350 KB, weiterhin vollständig im Lambda-RAM cachebar).

### 3. Änderungen in der Inferenz (Zwei-Phasen Engine)

```
[ Input: OpenAPI YAML OR Free Text Spec OR Terraform OR Free Text Arch ]
                                  │
                                  ▼
ADAPTER-SCHICHT (Deterministisch oder via Haiku)
- Erkennt Format: Syntaktisch (OpenAPI/HCL) vs. Freitext
- Syntaktisch: Schnelles Python-Parsing
- Freitext: Haiku extrahiert Entitäten in dasselbe Normal-Schema
                                  │
                                  ▼
PHASE 1: TARGET-ROUTING & DOMAIN DISCOVERY
- Filtert In-Memory-Rules nach target_phase == mode
- Extrahiert aktive Risikofelder (PII-Felder ODER Cloud-Ressourcen)
                                  │
                                  ▼
PHASE 2: BEDROCK TOOL-CALLING AUDIT
- Prüft exakt die 4–6 relevanten Regeln für Spec oder Architecture
- Liefert validierten Audit-Report (Pydantic JSON) in < 4 Sekunden
```

### 4. Der End-to-End Workflow: Spec → Rework → Arch → Rework

```
Stufe 1: Spec Review ──► Stufe 2: Spec Rework ──► Stufe 3: Arch Review ──► Stufe 4: Arch Rework
  (DSGVO / SDM)          (OpenAPI Fix)              (BSI / CIS)              (Terraform Fix)
```

**Schritt 1 (Spezifikations-Review):** z. B. „Bürgerportal: Registrierung erfordert Name, E-Mail, Geburtsdatum, IBAN und Religionszugehörigkeit“ → FAIL (Religion verletzt DSGVO Art. 9), WARN (Geburtsdatum verletzt SDM-Datenminimierung).

**Schritt 2 (Spezifikations-Rework):** Unzulässige Felder entfernt, DELETE-Endpunkt für Art. 17 ergänzt → GRÜN.

**Schritt 3 (Architektur-Review):** z. B. „API Gateway → Lambda → S3 + Aurora PostgreSQL in eu-central-1“ → FAIL (publicly_accessible = true, Verstoß NET.1.1), FAIL (Standard-Verschlüsselung statt KMS-CMK).

**Schritt 4 (Architektur-Rework):** publicly_accessible = false, kms_key_arn referenziert → GRÜN.

### Bedeutung für die IHK-Präsentation

1. Frühzeitige Fehlervermeidung – Datenschutzfehler behoben vor der ersten Zeile Infrastruktur-Code.
2. Saubere Trennung fachlicher (DSGVO/SDM) und technischer (BSI/CIS) Prüfung.
3. Multi-Input-Fähigkeit für Product Owner (Text) und DevOps-Engineers (OpenAPI/Terraform).

---

## 14. Betreff: "Modul 4 Praxisprojekt Spec to architecture"
**Datum/Uhrzeit:** 2026-09-19 09:33:27 (UTC)

Logische Krönung des Shift-Left-Ansatzes: Das System schlägt nach dem Spezifikations-Review direkt einen *BSI-konformen, DSGVO-validierten Architektur-Entwurf (IaC/Terraform)* vor, unter Einbindung standardisierter, maschinenlesbarer *Architecture Pattern Catalogs*.

### 1. Beste maschinenlesbare Datenquellen für Referenzarchitekturen

**A. AWS Solutions Constructs Catalog** – github.com/awslabs/aws-solutions-constructs. TypeScript/Python Pattern-Definitionen. Ab Werk gehärtete Multi-Service-Kombinationen (z. B. aws-apigateway-lambda, aws-lambda-dynamodb) mit Access-Logging, Verschlüsselungs-Hooks, Least-Privilege-IAM.

**B. Serverless Patterns/CDKPatterns Library** – github.com/cdk-patterns/serverless oder serverlessland.com/patterns. Über 200 atomare Architekturmuster (z. B. Sync REST API with DB, Async Processing with SQS/DLQ).

**C. GovStack Building Blocks & BSI Cloud-Referenz-Muster** – specs.govstack.global / BSI C5 Implementierungshilfen. Standardisierte Bausteine für Behördenanwendungen.

### 2. Das Schema für die Pattern-Bibliothek in S3

6–8 kanonische GovCloud-Archetypen in `architecture_patterns.json`:

```json
[
  {
    "pattern_id": "ARCH-PAT-01",
    "archetype": "SYNC_REST_CRUD_WORKLOAD",
    "intent_triggers": ["crud", "rest_api", "single_entity", "citizen_service"],
    "aws_services": ["api_gateway", "lambda", "aurora_postgresql", "kms"],
    "compliance_baseline": {
      "bsi": ["NET.1.1", "SYS.1.5", "OPS.1.1.2"],
      "dsgvo": ["Art. 32", "Art. 25"]
    },
    "terraform_blueprint_skeleton": "resource \"aws_apigatewayv2_api\" \"main\" { ... }\nresource \"aws_lambda_function\" \"handler\" { ... }\nresource \"aws_db_instance\" \"db\" {\n storage_encrypted = true\n kms_key_id = aws_kms_key.cmk.arn\n publicly_accessible = false\n}"
  },
  {
    "pattern_id": "ARCH-PAT-02",
    "archetype": "ASYNC_INGEST_STORAGE_WORKLOAD",
    "intent_triggers": ["document_upload", "batch_processing", "file_storage"],
    "aws_services": ["s3", "sqs", "lambda", "kms"],
    "compliance_baseline": {
      "bsi": ["OPS.1.1.2", "CON.2"],
      "cis": ["2.1.1", "2.1.2"]
    },
    "terraform_blueprint_skeleton": "resource \"aws_s3_bucket\" \"secure_bucket\" {\n # KMS CMK + Block Public Access standardmäßig integriert\n}"
  }
]
```

### 3. Der Übergangs-Workflow: Von der Spec zum Architektur-Vorschlag

```
1. User reicht OpenAPI/Free-Text-Spezifikation ein
   │
   ▼
2. Copilot führt Spec Review durch (DSGVO/SDM) → Befund: Gültig oder nach Rework behoben
   │
   ▼
3. "Pattern Matching Phase" (Synthese)
   - Analysiert Endpunkte & Datenflüsse
   - Wählt aus architecture_patterns.json das passende Pattern
   │
   ▼
4. Output: Architekturentwurf & Terraform-Entwurf
   │
   ▼
5. User klickt auf "Run Architecture Audit" → Prüft gegen BSI/CIS → GRÜN!
```

### Bedeutung für das IHK-Projekt

1. Vom passiven Checker zum echten Copiloten – schlägt direkt die BSI-konforme Referenzarchitektur vor.
2. Klares Alleinstellungsmerkmal (USP) – Standard-Tools meckern nur, dieses System schlägt die gehärtete Lösung vor.
3. Prüfer-Antwort im Fachgespräch: „Wir generieren nicht frei im leeren Raum. Wir nutzen kuratierte Archetypen, basierend auf den AWS Solutions Constructs, injizieren die BSI/CIS-Mindestattribute deterministisch und validieren den Entwurf vor der Ausgabe noch einmal über unsere Phase-2-Engine.“

---

## 15. Betreff: "Modul 4 - Praxisprojekt v modell"
**Datum/Uhrzeit:** 2026-09-19 09:51:47 (UTC)

Das V-Modell passt perfekt zu diesem Vorhaben. Für Prüfer und Architekten ist das V-Modell der Inbegriff strukturierter Software- und Systementwicklung.

### 1. Das V-Modell als Leitplanke für dein System

```
Entwurf & Spezifikation (Links)          Verifikation & Test (Rechts)
───────────────────────────────          ────────────────────────────
[ 1. Fach-/Daten-Spezifikation ]  ──────────► [ 4. Acceptance Tests ]
   (DSGVO/SDM/OpenAPI)                          (Gherkin BDD/API-Checks)
             │                                            ▲
             ▼                                            │
[ 2. System-/Architektur-Entwurf ] ────────► [ 3. IaC & Compliance Tests ]
   (BSI/CIS/Terraform)                          (pytest/Open Policy Agent)
```

### 2. UI-Perspektive: Die 3 logischen Layout-Ansätze

**Option A (4 separate Tabs):** Nachteil – zu viele Klicks, synchroner Zusammenhang geht visuell verloren.

**Option B – "Split-Screen Workbench" (Empfehlung):** Bildschirm geteilt in Design (Links) und Verifikation (Rechts):
- *Obere Zeile/Stufe 1 (Fachspezifikation):* Links: OpenAPI/Text-Spec + [Audit Spec]-Button. Rechts: DSGVO/SDM-Audit-Ergebnis + [Generate Acceptance Tests (Gherkin)].
- *Untere Zeile/Stufe 2 (Technische Architektur):* Links: abgeleiteter Architektur-Blueprint + [Audit Architecture]-Button. Rechts: BSI/CIS-Audit-Ergebnis + [Generate IaC Tests (pytest)].

**Option C (Linearer 4-Schritte-Stepping-Wizard):** Führt den Nutzer an die Hand; gut für Live-Demos.

### 3. Muss der Output der Architekturgenerierung Free Text ODER Terraform sein?

Nein, zwingend *BEIDES gleichzeitig (Dual Output)*:

- Reiner Freitext: nicht maschinenlesbar/deploybar/testbar.
- Reines Terraform: für Nicht-Entwickler unübersichtlich.

Beispiel-Blueprint-Output:

```
### 🏛️ Architekturentwurf (Fachliche Begründung & Systemkontext)
- Gewählter Archetyp: ARCH-GOV-01 (Sync Citizen REST Service)
- Topologie: API Gateway (eu-central-1) mit TLS 1.3 terminiert an privater Lambda-Funktion.
- Datenhaltung: Amazon RDS Aurora PostgreSQL in isolierten Subnetzen ohne Internet-Gateway.
- Sicherheitsanker: Verschlüsselung aller ruhenden Daten mit KMS CMK (BSI OPS.1.1.2).

### 🛠️ Infrastruktur-Blueprint (Terraform/IaC)
resource "aws_apigatewayv2_api" "http_api" {
  name = "citizen-service-api"
  protocol_type = "HTTP"
}

resource "aws_db_instance" "database" {
  identifier = "citizen-db"
  storage_encrypted = true
  kms_key_id = var.kms_cmk_arn
  publicly_accessible = false
}
```

Aus dem Freitext-Konzept generiert das LLM fachliche Akzeptanzkriterien, aus dem Terraform-Block technische Assertions.

### 4. Was bedeuten die Tests für die beiden Stufen konkret?

| Stufe | Was wird geprüft? | Testformat |
|---|---|---|
| Obere Stufe (Spezifikation ↔ Fachliche Tests) | DSGVO/SDM-Vorgaben in Testfälle übersetzt? | Gherkin (.feature) oder Postman/Newman JSON |
| Untere Stufe (Architektur ↔ Technische Tests) | BSI/CIS-Vorgaben im Terraform-Code umgesetzt? | pytest-Assertions oder Open Policy Agent (Rego) |

### Fazit

1. Links: Fachliche Spezifikation nach DSGVO → Technische Architektur nach BSI.
2. Rechts: Automatisierte Akzeptanztests → Technische IaC-Prüfskripte.

Damit wird das Tool zu einer ganzheitlichen DevSecOps- und Compliance-Workbench nach anerkannten Software-Engineering-Standards (V-Modell).

---

## 16. Betreff: "Modul 4 Praxisprojekt Implementierungsplan"
**Datum/Uhrzeit:** 2026-09-19 10:03:58 (UTC)

15-Tage-Plan mit reduziertem, prüfungsfestem Scope: *Spec-Review (DSGVO/SDM) → Pattern-Matching (Golden Archetypes) → Architektur-Review (BSI/CIS)* mit statisch hinterlegten Verifikations-Artefakten. Jeder Tag liefert ein überprüfbares Tagesergebnis (DEVLOG.md).

### Woche 1: Fundament, Wissensbasis & Inferenz-Kern

- **Tag 1:** Projekt-Setup, Repo-Struktur, Pydantic-Schemas (UnifiedAuditRule, AuditFinding, NormalizedInput, ArchitectureArchetype). DoD: pytest validiert Dummy-Daten.
- **Tag 2:** Golden Archetypes & Normative Seeds (architecture_patterns.json mit 6 Archetypen, sdm_dsgvo_seed.json mit 10–12 Regeln, Basis-BSI-Regeln). DoD: Testskript liest alle Seeds ohne fehlende Pflichtfelder.
- **Tag 3:** AWS Bedrock Client & Phase-1-Extraktion (Scope Discovery). Boto3 Bedrock-Client (eu-central-1) mit Claude 3.5 Haiku, Phase-1-Prompt mit toolChoice = required. DoD: Beispiel-OpenAPI-Snippet wird deterministisch geparst.
- **Tag 4:** Phase-2-Audit-Engine (DSGVO/SDM & BSI-Prüfung). DoD: Testfall mit unzulässiger Religion/Steuer-ID erzeugt zuverlässig VIOLATION-Finding.
- **Tag 5:** Archetype Matcher & CLI-End-to-End-Pipeline (audit_pipeline.py). DoD: CLI-Befehl gibt vollständigen JSON-Audit-Report und passendes Terraform-Template aus.

### Woche 2: API, Caching & Streamlit Frontend

- **Tag 6:** S3 Seed-Deployment & In-Memory Cache Loader (knowledge_loader.py). DoD: Ladevorgang unter 500 ms, lokaler Fallback bei Offline-Betrieb.
- **Tag 7:** 3 IHK-Test-Presets (Unsichere Spezifikation, Behobene Spezifikation, Unsichere Architektur). DoD: alle 3 statisch hinterlegt und reproduzierbar testbar.
- **Tag 8:** Streamlit UI-Grundgerüst & Preset-Selector. DoD: Preset-Auswahl füllt Felder automatisch.
- **Tag 9:** Split-Screen Visualisierung (Ampel-Dashboard). DoD: „Audit starten“ rendert Befunde in unter 4 Sekunden.
- **Tag 10:** Archetype Blueprint & V-Modell Test-Export Tab. DoD: vollständiger Zyklus ohne UI-Neuladen durchklickbar.

### Woche 3: Härtung, Benchmarking, Demo-Video & Dokumentation

- **Tag 11:** Automatisierte Regressionstests mit pytest. DoD: läuft unter 15 Sekunden, 100 % grün.
- **Tag 12:** Performance-Tuning & FinOps-Kostenanalyse (Ziel: < 0,003 € pro Audit). DoD: Kosten-Kalkulation für Präsentation bereit.
- **Tag 13:** Edge-Case-Testing & Fehlerbehandlung (leerer Input, kaputtes JSON/YAML, us-east-1 sperren). DoD: UI stürzt niemals ab.
- **Tag 14:** Erstellung des 3-Minuten-Demovideos (OBS/Screen Studio, ElevenLabs Voiceover, CapCut/DaVinci Resolve). DoD: fertiges MP4 unter docs/demo.mp4.
- **Tag 15:** Dokumentations-Abschluss & 4 ADRs finalisieren. DoD: Projekt vollständig dokumentiert und bereit für IHK-Präsentation.

### Meilenstein-Checkliste

| Meilenstein | Tag | Liefert |
|---|---|---|
| M1: Core Engine Ready | Tag 5 | CLI-Tool führt Spec- & Architektur-Audits durch |
| M2: UI & V-Modell Ready | Tag 10 | Streamlit-App visualisiert Ampel & exportiert Test-Artefakte |
| M3: Production & Defense Ready | Tag 15 | Pytest-Suite grün, Kosten dokumentiert, Demovideo gerendert |

---

## 17. Betreff: "Modul 4 Praxisprojekt Initialisierung"
**Datum/Uhrzeit:** 2026-09-19 10:13:27 (UTC)

Erst Klarheit in Konzept und Dokumentation schaffen, bevor die erste Zeile Code geschrieben wird. Zweigeteilter Fahrplan: Vorbereitungsphase (Phase 0) mit agiler Dokumentation und gezieltem Wissensaufbau sowie Hosting für Recruiter mit minimalen Kosten.

### Teil 1: Die Initialisierungs- & Lernphase (Phase 0)

```
my-govcloud-copilot/
└── docs/
    ├── 01_PROJECT_CHARTER_LEAN.md       # Problem, Zielgruppe, Business Value
    ├── 02_SPEC_SYSTEM_REQUIREMENTS.md   # IEEE-830-light: Use Cases, Schemas
    ├── 03_ARCHITECTURE_BLUEPRINT.md     # C4-Modell (Level 1 & 2), V-Modell-Mapping
    └── adr/
        ├── ADR-001-in-memory-vs-opensearch.md
        ├── ADR-002-deterministic-archetypes.md
        ├── ADR-003-tool-calling-pydantic.md
        └── ADR-004-eu-central-1-sovereignty.md
```

**Die vier agilen Dokumente:**

1. *01_PROJECT_CHARTER_LEAN.md:* Problemstellung, Nutzen (Shift-Left spart bis zu 40 % Nacharbeitszeit), Zielgruppen.
2. *02_SPEC_SYSTEM_REQUIREMENTS.md:* Ein-/Ausgabeformate (OpenAPI, Freitext, HCL), Qualitätsanforderungen (< 5s Antwortzeit, Datenhaltung nur in Deutschland, Zero-Cost im Leerlauf).
3. *03_ARCHITECTURE_BLUEPRINT.md:* C4-Diagramme, V-Modell-Umsetzung.
4. *docs/adr/:* ADR-001 (In-Memory JSON-Cache statt OpenSearch), ADR-002 (6 kuratierte Golden Archetypes statt freier LLM-Terraform-Generierung).

### Lern- & Mentoring-Plan für Phase 0

| Thema | Lernziel | Beispiel-Prompt für Claude Code (/teach) |
|---|---|---|
| BSI IT-Grundschutz & C5 | NET.1.1 (Netztrennung), OPS.1.1.2 (Kryptokonzept) verstehen | „Erkläre mir BSI NET.1.1 anhand einer 3-Tier-Architektur in AWS.“ |
| SDM V3.1 (Datenschutz) | 7 Gewährleistungsziele kennen | „Wie unterscheidet sich Nichtverkettung von Mandantentrennung im Code?“ |
| AWS Bedrock Tool-Calling | Pydantic-Schemas als JSON-Schema an Converse API | „Erkläre den genauen Ablauf von Bedrock Converse API Tool Choice.“ |
| V-Modell im Cloud-Zeitalter | Argumentationslinie für IHK-Prüfung | „Simuliere ein 5-Minuten-IHK-Fachgespräch: Warum eignet sich das V-Modell für Serverless-Compliance?“ |

### Teil 2: Wie und wo hostest du das Web-UI für Recruiter?

**Option A (Pragmatisch & 0 €): Streamlit Community Cloud**

```
[ Recruiter ] ──► [ Streamlit Community Cloud ] ──(HTTPS)──► [ AWS Bedrock/Lambda (Frankfurt) ]
                   - Öffentliche URL
                   - Secrets via Streamlit Dashboard
```

- GitHub-Repo direkt mit share.streamlit.io verknüpft, automatisches Update bei Git-Push.
- Kosten: dauerhaft 0,00 €.
- Sicherheit: AWS Credentials niemals in Git, sondern im Streamlit-Dashboard unter Settings → Secrets; dedizierter IAM-User `streamlit-recruiter-demo` mit ausschließlich bedrock:InvokeModel (Claude 3.5 Haiku) und s3:GetObject; AWS Budget-Alert bei 5,00 €/Monat.

**Option B (100 % AWS Native): AWS App Runner in eu-central-1**

```
[ Recruiter ] ──► [ AWS App Runner (Frankfurt) ] ──(IAM Role)──► [ AWS Bedrock/S3 ]
                   - Eigener Docker-Container
                   - 100 % in eu-central-1
```

- Dockerfile für Streamlit-App, Deployment via App Runner direkt in Frankfurt.
- Vorteil: gesamtes System 100 % in Frankfurt, kein Drittanbieter; IAM-Rollen ohne API-Keys über App Runner Instance Roles.
- Kosten: ca. 3–5 €/Monat für Minimal-Instanz (0,5 GB RAM); pausierbar.

### Empfohlene Vorgehensweise

1. Woche 0: Repo anlegen, 4 Markdown-Dokumente mit Claude Code schreiben, BSI-/SDM-Konzepte verinnerlichen.
2. Projekt-Phase (3 Wochen): Logik bauen, Streamlit-App lokal testen.
3. Deployment (Tag 14/15): Repo mit Streamlit Community Cloud verbinden, AWS-Credentials im Secret Manager hinterlegen, öffentlichen Link testen.
4. Ergebnis: vorzeigbare Live-URL für LinkedIn-Profil und Lebenslauf.

---

## 18. Betreff: "Modul 4 Praxisprojekt Erster Schritt"
**Datum/Uhrzeit:** 2026-09-19 10:20:01 (UTC)

Wenn über mehrere Tage viele Zwischenschritte, Ideen und Kurskorrekturen generiert wurden (z. B. Wechsel von „Testfallgenerierung dynamisch via LLM“ zu „statisches V-Modell mit Golden Archetypes“ oder der Scope-Schnitt für 3 Wochen), entstehen typischerweise Widersprüche. Um daraus eine widerspruchsfreie „Single Source of Truth“ zu machen, wird eine Kombination aus *Gemini Pro (Synthese & Ingestion)* und *Claude Code (Datei-Strukturierung)* empfohlen.

### Schritt 1: Das Material bündeln (Raw Dump)

Inhalt aller 20 E-Mails in eine einzige Datei kopieren (z. B. `raw_project_history.md`), ohne auf Formatierung oder Dubletten zu achten.

### Schritt 2: Konsolidierung & Deduplizierung mit Gemini Pro

Gemini Pro hat ein Kontextfenster von 1–2 Millionen Tokens und kann die gesamte Korrespondenz auf einmal verarbeiten, chronologische Widersprüche erkennen und ältere Entwürfe durch neuere Entscheidungen ersetzen.

**Prompt für Gemini Pro:**

> „Im Anhang findest du den gesamten Entwurfsverlauf (ca. 20 Mails/Notizen) für mein 3-wöchiges IHK-Praxisprojekt ‚GovCloud Compliance Copilot‘.
>
> Deine Aufgabe ist eine vollständige Konsolidierung in eine einzige, in sich konsistente Systemdokumentation ohne Detailverlust.
>
> Regeln zur Auflösung von Widersprüchen (Chronologische Priorisierung):
>
> 1. Neueste Entscheidungen schlagen ältere Entwürfe: Wir generieren KEINE dynamischen Gherkin-/Pytest-Testfälle zur Laufzeit mehr per LLM. Stattdessen nutzen wir die 6 statisch kuratierten ‚Golden Archetypes‘ (architecture_patterns.json), die vorbereitete Test-Artefakte für das V-Modell enthalten.
> 2. Scope: 3 Wochen (15 Arbeitstage), 100 % serverlos auf AWS in eu-central-1 (S3 In-Memory Cache, Bedrock Converse API, Streamlit UI, Zero-Cost Idle).
> 3. Data Ingestion: Keine fragilen Live-PDF-Scraper in GitHub Actions. Gesetze (DSGVO) und Methoden (SDM V3.1) liegen als versionierte JSON-Seeds im Repo. BSI und OWASP stammen aus strukturiertem OSCAL/Git.
>
> Erstelle mir daraus ein modulares Markdown-Dossier mit 4 klaren Abschnitten:
>
> - Abschnitt 1: Fachliche Spezifikation & User Stories (inkl. DSGVO/SDM & BSI-Scope, Input-/Output-Formate).
> - Abschnitt 2: System- und Softwarearchitektur (Komponenten, V-Modell-Ablauf, C4-Container-Design).
> - Abschnitt 3: Datenarchitektur & Wissensbasis (Schema UnifiedAuditRule, In-Memory S3-Cache, die 6 Archetypen).
> - Abschnitt 4: Die 4 Architectural Decision Records (ADR-001 bis ADR-004 im Standardformat).
>
> Behalte alle technischen Details (Pydantic-Feldnamen, BSI-Kürzel, AWS-Dienste, API-Pfade) vollständig bei. Keine Platzhalter.“

### Schritt 3: Verteilen und Validieren mit Claude Code

Konsolidiertes Markdown als `CONSOLIDATED_SPEC.md` speichern. Claude Code übernimmt die Aufteilung in die Repository-Struktur:

**Prompt an Claude Code:**

> „Lies CONSOLIDATED_SPEC.md. Zerlege das Dokument modular in unsere Ziel-Dokumentationsstruktur unter docs/:
>
> 1. docs/01_PROJECT_CHARTER_LEAN.md (Problem, Zielgruppe, Business Value)
> 2. docs/02_SPEC_SYSTEM_REQUIREMENTS.md (Use Cases, API-Spezifikation, Schemas)
> 3. docs/03_ARCHITECTURE_BLUEPRINT.md (Architektur, Datenfluss, V-Modell-Integration)
> 4. docs/adr/ADR-001-in-memory-vs-opensearch.md
> 5. docs/adr/ADR-002-deterministic-archetypes.md
> 6. docs/adr/ADR-003-tool-calling-pydantic.md
> 7. docs/adr/ADR-004-eu-central-1-sovereignty.md
>
> Prüfe nach dem Anlegen der Dateien, ob es noch logische Brüche oder veraltete Referenzen (z. B. auf OpenSearch oder dynamische Testfallgenerierung) gibt, und behebe sie.“

### Warum diese Arbeitsteilung optimal ist

- *Gemini Pro:* riesiges Kontextfenster für 20 E-Mails gleichzeitig, chronologische Synthese.
- *Claude Code (Sonnet):* arbeitet direkt auf der Festplatte, baut saubere Ordner/Dateien für Recruiter und Prüfer.

---

## 19. Betreff: "Modul 4 Praxisprojekt Grosse Dokumente"
**Datum/Uhrzeit:** 2026-09-19 10:33:32 (UTC)

Wenn ein Architekt eine 40-seitige Spezifikation oder eine 3.000-Zeilen-Terraform-Konfiguration unbearbeitet an Bedrock sendet, verursacht das drei kritische Probleme:

1. *API Gateway 29s Timeout:* Verarbeitung von 50k+ Input-Tokens sprengt das synchrone Limit.
2. *Context Dilution ("Lost in the Middle"):* Große Kontextfenster verschlechtern die LLM-Aufmerksamkeit; kleine DSGVO-Verstöße werden übersehen.
3. *FinOps Bleed:* Volle Audits bei jeder Iteration verursachen unnötig hohe Kosten.

Lösung: *deterministisches Pre-Pruning und chunked map-reduce vor dem LLM.*

### 1. Die Strategie: Deterministic Filtering *vor* dem LLM

```
[ Large Upload: 3.000 Zeilen HCL / 50-seitiges OpenAPI ]
                        │
                        ▼
1. Structural Pre-Parser (python-hcl2/PyYAML)
                        │
                        ▼
2. Deterministic Scope Trimmer
   - Verwirft Beschreibungen & Docs
   - Verwirft unverwaltete Ressourcen
   - Behält nur Audit-Schlüssel
                        │ (Reduziert Kontext um 75–85%)
                        ▼
3. Phase 1: Entity Extraction ──► Bedrock Haiku (< 2k Tokens)
                        │
                        ▼
4. Phase 2: Targeted Audit ──► Bedrock Haiku (Audit nur 4–6 Regeln)
```

### 2. Umgang mit massiven strukturierten Syntax-Dateien

**A. Massive OpenAPI/Swagger-Dokumente (5.000+ Zeilen):** Nur HTTP-Methoden, Request-Body-Parameter und securitySchemes relevant.

```python
def prune_openapi_for_audit(raw_spec: dict) -> dict:
    """Strips documentation, examples, and 200/400 response bodies to minimize tokens."""
    pruned = {"paths": {}, "components": {"securitySchemes": raw_spec.get("components", {}).get("securitySchemes", {})}}

    for path, methods in raw_spec.get("paths", {}).items():
        pruned["paths"][path] = {}
        for method, details in methods.items():
            if method.lower() in ["post", "put", "patch", "delete", "get"]:
                pruned["paths"][path][method] = {
                    "parameters": [p.get("name") for p in details.get("parameters", [])],
                    "request_properties": list(
                        details.get("requestBody", {})
                        .get("content", {})
                        .get("application/json", {})
                        .get("schema", {})
                        .get("properties", {})
                        .keys()
                    )
                }
    return pruned
```

Ergebnis: Eine 5.000-Zeilen-OpenAPI-Datei schrumpft auf ein 150-Zeilen-JSON-Dictionary, Token-Verbrauch sinkt von ~35.000 auf ~800.

**B. Massive Terraform HCL-Konfigurationen (3.000+ Zeilen):** Nur Cloud-Ressourcen-Blöcke und Sicherheitsattribute relevant. python-hcl2 parst HCL in Python-Dict; Filterung auf aws_s3_bucket, aws_db_instance, aws_security_group, aws_apigatewayv2_api, aws_kms_key.

### 3. Umgang mit massivem Freitext (Chunk & Scope Pattern)

Bei 30-seitigen PDFs oder 10.000-Wort-Dokumenten: Nicht in einen Prompt dumpen, sondern *Agentic Map-Reduce Scope Discovery*:

```
[ 30-Seiten Freitext-Dokument ]
              │
              ▼ (Split nach Headings/Markdown-Sektionen in 1.000-Wort-Chunks)
MAP STEP: Fast Section Classifier (Bedrock Haiku)
"Does this chunk mention: Data/PII, Storage, Network, or Identity? Return: [YES/NO + 3-word summary]"
                           │ (Verwirft 70% irrelevanten Text)
                           ▼
REDUCE STEP: Consolidated Compliance Extract
                           │
                           ▼
       [ Normale Phase 1 & 2 Audit Pipeline ]
```

### 4. Guardrails in der Streamlit UI

```python
MAX_CHARS = 50000
user_input = st.text_area("Input Artifact:", height=300, max_chars=MAX_CHARS)
if len(user_input) >= MAX_CHARS:
    st.warning("⚠️ Input exceeds 50,000 characters. Please upload modular service definitions rather than monolithic files.")
```

Zusätzlich: File Size Gatekeeper (Ablehnung von Dateien > 1 MB vor jedem AWS-Aufruf).

### Wie im IHK-Fachgespräch präsentieren

Frage: „Was passiert, wenn ein Nutzer eine riesige 100-seitige Spezifikation hochlädt? Bricht Ihre Bedrock-Pipeline dann wegen Token-Limits oder Timeouts zusammen?“

Antwort: „Wir verlassen uns bewusst nicht darauf, unstrukturierte Riesen-Dokumente blind in das LLM-Kontextfenster zu werfen. Das würde die 29-Sekunden-Grenze des API Gateway sprengen und durch Context Dilution zu übersehenen Befunden führen. Stattdessen setzen wir auf deterministisches Pre-Pruning: Bei OpenAPI- und Terraform-Dateien parsen wir den AST lokal in Python und extrahieren ausschließlich auditrelevante Attribute. Das reduziert das Tokenvolumen um über 80 %, garantiert Latenzen unter 4 Sekunden und hält die Inferenzkosten im Sub-Cent-Bereich.“

---

## 20. Betreff: "Modul 4 Praxisprojekt Referenz Architekturen."
**Datum/Uhrzeit:** 2026-09-19 10:46:18 (UTC)

Für den Public Sector und Unternehmensarchitekturen nach ISO/IEC 25010 und dem AWS Well-Architected Framework fehlen noch *zwei zwingende NFAs*:

1. *Security & Privacy (Datensouveränität & BSI/DSGVO):* Regionale Bindung strikt an Frankfurt (eu-central-1), Verschlüsselung at-rest mit KMS CMK, Zero Trust Network Architecture.
2. *FinOps & Cost Efficiency:* 0,00 € Grundkosten im Leerlauf, automatisches Storage-Tiering, Budget-Alarme, Kostenzuordnungs-Tags.

### Die 6 Golden Archetypes: Vollständige NFA-Referenz

**Archetyp 1: Sync Citizen REST Service (Transactional CRUD)** – ARCH-GOV-01. Zielworkload: Antragsformulare, Bürgerkonto-Registrierung. Services: API Gateway, Lambda, Aurora PostgreSQL Serverless v2, KMS, Secrets Manager.

| NFA-Dimension | Technische Umsetzung |
|---|---|
| Usability | RFC 7807 Error-Payloads; /docs-Pfad OpenAPI 3.0; JWT Authorizer |
| Performance | Graviton3 (arm64); Aurora Serverless v2 Auto-Scaling (0.5–4 ACUs) |
| Reliability | Multi-AZ Cluster; Failover < 30s; Point-in-Time Recovery (30 Tage) |
| Supportability | AWS X-Ray Active Tracing; CloudWatch Logs 90 Tage Retention |
| Security & Privacy | publicly_accessible = false; KMS CMK jährliche Rotation; BSI NET.1.1 |
| FinOps | Aurora skaliert nachts auf 0.5 ACU; Lambda Pay-per-Request |

**Archetyp 2: Async Document Ingest & Processing Pipeline** – ARCH-GOV-02. Zielworkload: Upload von Antragsnachweisen, Virenprüfung, OCR. Services: S3, SQS (+ DLQ), Lambda, KMS.

| NFA-Dimension | Technische Umsetzung |
|---|---|
| Usability | Asynchroner Upload via S3 Presigned URLs |
| Performance | Entkoppelte Batch-Verarbeitung; dynamisches Lambda-Concurrency-Scaleout |
| Reliability | SQS DLQ (maxReceiveCount = 3); S3-Versionierung |
| Supportability | CloudWatch-Alarm auf ApproximateNumberOfMessagesVisible der DLQ |
| Security & Privacy | S3 Block Public Access; KMS CMK; BSI OPS.1.1.2.A2 |
| FinOps | S3 Lifecycle nach 30 Tagen in Glacier Instant Retrieval |

**Archetyp 3: Immutable Audit & Security Log Archiving** – ARCH-GOV-03. Zielworkload: Revisionssichere Protokollierung für BSI-Audits. Services: CloudTrail, S3, KMS, CloudWatch Log Group.

| NFA-Dimension | Technische Umsetzung |
|---|---|
| Usability | Athena-Partitionierung (year/month/day) |
| Performance | Getrennte Abfragepfade; CloudWatch Metric Filter |
| Reliability | S3 Object Lock im Compliance Mode (WORM) |
| Supportability | enable_log_file_validation = true |
| Security & Privacy | Dediziertes Log-Archiv-Konto; Write-Only Bucket Policy; PII-Scrubber |
| FinOps | S3 Lifecycle nach 90 Tagen in Glacier Flexible Archive |

**Archetyp 4: Public Citizen Portal (Edge & Frontend SPA)** – ARCH-GOV-04. Zielworkload: Barrierefreies Bürger-Webinterface. Services: CloudFront, WAFv2, S3, ACM.

| NFA-Dimension | Technische Umsetzung |
|---|---|
| Usability | TLS 1.3; Edge-Termination; Zero-CORS für /api/* |
| Performance | Edge-Caching via CloudFront; HTTP/3; Gzip/Brotli |
| Reliability | AWS Shield Standard; Origin-Failover auf Backup-Bucket |
| Supportability | CloudWatch RUM für clientseitige Fehler |
| Security & Privacy | AWS WAF Core Rule Set (OWASP Top 10); strikte CSP |
| FinOps | PriceClass_100 beschränkt Edge-Locations auf Europa |

**Archetyp 5: Secure Register Synchronizer (Cross-Agency API Bridge)** – ARCH-GOV-05. Zielworkload: Anbindung an Bundes-/Landesregister, XÖV-Standards. Services: API Gateway, VPC Endpoint, PrivateLink, Lambda.

| NFA-Dimension | Technische Umsetzung |
|---|---|
| Usability | Klare OpenAPI-Definitionen für XÖV/XML/JSON |
| Performance | Direkte Übertragung über AWS-Backbone; einstellige ms-Latenz |
| Reliability | Redundante PrivateLink Endpoints in 3 AZs; Exponential Backoff |
| Supportability | VPC Flow Logs |
| Security & Privacy | Mutual TLS mit Bundes-PKI-Zertifikaten; Verkehr bleibt im Privatnetz |
| FinOps | VPC Endpoint Interfaces geteilt; Abrechnung nach Transfervolumen |

**Archetyp 6: Anonymized Analytics & Open Data Aggregator** – ARCH-GOV-06. Zielworkload: Statistische Auswertungen, Dashboards, Open Data. Services: S3, Glue Job, Athena Workgroup, KMS.

| NFA-Dimension | Technische Umsetzung |
|---|---|
| Usability | Standardisierte CSV/Parquet über Athena-Views |
| Performance | Parquet + Snappy-Kompression; bis zu 90 % schnellere Abfragen |
| Reliability | Ephemere Glue Jobs; idempotente ETL-Pipelines |
| Supportability | Glue DataBrew/Data Quality Rules |
| Security & Privacy | Trennung Rohdaten-/Clean-Room-Bucket; k-Anonymitäts-Filter |
| FinOps | Athena Workgroup mit Ausgabenlimit (max. 1 GB/Query) |

---

## 21. Betreff: "Modul 4 Praxisprojekt mobile apps"
**Datum/Uhrzeit:** 2026-09-19 10:50:45 (UTC)

Mobile Apps im Public Sector (z. B. BundID-App, AusweisApp2, Wohngeld-Apps, kommunale Bürger-Apps) unterscheiden sich fundamental von Web-Portalen oder Server-zu-Server-Schnittstellen:

1. *Unkontrollierte Client-Umgebung:* Geräte können kompromittiert, gerootet oder gejailbreakt sein.
2. *Besondere Authentifizierungsstandards:* Smart-eID (Online-Ausweisfunktion via NFC), biometrische Freigabe (FaceID/TouchID), OIDC/PKCE-Flows.
3. *Strenge DSGVO-Vorgaben für Mobile:* Keine US-Tracking-SDKs (Firebase Analytics, Facebook SDK, Crashlytics) ohne Rechtsgrundlage und EU-Hosting.
4. *Push-Mitteilungen & Barrierefreiheit:* Sichere Push-Nachrichten ohne Weitergabe personenbezogener Inhalte an APNs/FCM; BITV 2.0.

Die Archetypen-Sammlung wird um genau *einen dedizierten Mobile-Archetypen (ARCH-GOV-07)* ergänzt.

### Der 7. Golden Archetype: ARCH-GOV-07 – Secure Citizen Mobile Backend

- *Name:* Secure Citizen Mobile Backend & Identity Relay
- *Zielworkload:* Native Bürger-Apps (iOS/Android), Antrags-Tracking, Push-Zustellung, eID/BundID-Anbindung.
- *AWS Services:* API Gateway, Cognito User Pool, Lambda, SNS (Mobile Push), WAFv2, KMS.

| NFA-Dimension | Technische Umsetzung |
|---|---|
| Usability (Mobile DX) | OAuth 2.1 mit PKCE via Cognito/API Gateway; RFC 7807; Offline-First Delta-Sync |
| Performance | Payload-Kompression (Gzip/Brotli); Edge-Optimierung via CloudFront |
| Reliability | Idempotente Endpunkte via Idempotency-Key-Header |
| Supportability | EU-konformes Error-Logging ohne PII; kein Firebase-Tracking |
| Security & Privacy | App-Attestation (Apple DeviceCheck/App Attest, Google Play Integrity API); TLS-Pinning; Zero-PII-Push (stumme SNS-Trigger) |
| FinOps | Cognito MAU Free Tier (bis 50.000 Nutzer); SNS Pay-per-Push |

### Änderungen im Spec Review & Architektur Review für Mobile Apps

**Im Spec Review (DSGVO/SDM/OWASP MASVS):**

- *Datenschutzrechtliches Nadelöhr:* Regel SDM-NIC-004 (Unzulässige Datenweitergabe an US-Dienstleister via Device-IDs gem. EuGH Schrems II) bei SDKs wie Firebase Crashlytics/Google Analytics. Remediation: eigenes Telemetrie-Gateway in Frankfurt oder Tracking-Verzicht.
- *Authentifizierungs-Check:* Regel OWASP-MASVS-AUTH/BSI TR-03107-1 bei veralteten OAuth-Flows (Resource Owner Password Grant/Implicit Flow). Remediation: Authorization Code Flow mit PKCE erzwingen.

**Im Architektur Review & Blueprint (BSI/CIS):**

- *WAF & Bot-Control:* WAF vor mobilen APIs gegen Credential Stuffing/Scraper.
- *Stille Benachrichtigungen (Privacy-Preserving Push):* Keine Klartext-Meldungen über Apple-/Google-Server; Pattern Wake-Up Push → Authenticated Fetch.

### Einbindung in die 3 Wochen

1. *Preset-Ergänzung:* OpenAPI-Spezifikation für mobile Bürger-App (mobile_citizen_api.yaml mit Push-Notification-Endpunkt, Device-Token-Registrierung).
2. *Archetyp ARCH-GOV-07:* als fertiges JSON in architecture_patterns.json.
3. *Präsentations-Mehrwert:* Bei Fragen zu BundID/kommunalen Apps auf ARCH-GOV-07 verweisen (App Attestation, PKCE, Zero-PII-Push).

---

*Ende der gesammelten E-Mail-Inhalte (21 Nachrichten, 18.–19.09.2026).*
