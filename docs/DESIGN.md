# GovGuard – Design (Schnittstellenverträge)

Dieses Dokument legt die **Verträge** zwischen den Tickets fest: Datenformate und Funktionssignaturen. Das Innenleben eines Moduls (Prompts, Bibliotheken, Algorithmen) entsteht im jeweiligen Ticket. Big Picture: [ARCHITECTURE.md](ARCHITECTURE.md), Begriffe: [CONTEXT.md](../CONTEXT.md).

## Vertragskarte

| Vertrag | Liefert | Nutzt |
|---|---|---|
| `Requirement`, `ExtractedSource` (1.1) | #4, #5 | #6 |
| `Selection` (1.2) | #6 | #12 |
| `Rule` (1.2) | #1 (Modell), #12 (Daten) | #2, #7, #9 |
| `Archetype` (1.3) | #7 | #10, #11 |
| `NagException` (1.3) | Mensch, `data/nag_allowlist.json` | #7, #9, #11 |
| `Preset`, `Expected` (1.4) | #3 | #6, #8, #11 |
| `Finding`, `AuditReport` (2.1) | #1 | #2, #7, #8, #9, #11 |
| `run_audit()` (2.2) | #1 | #2, #7, #8, #9 |
| `select_archetype()`, `ArchetypeChoice` (2.2) | #10 | #11 |
| API-JSON (2.3) | #9, #10 | #11 |
| `Trace`, `AuditEvent` (2.4) | #1 | #9, #10 |
| `normalize()`, `contains_quote()`, `template_resource_types()` (3) | #1 | #4, #5, #12 |

## 1. Build-Verträge

### 1.1 Requirement – extrahierte Anforderung

Ein Quellen-Adapter (`src/kb_build/sources/*.py`) schreibt je Quelle eine Datei `data/extracted/<source>.json`. Sie enthält **alle** Anforderungen der Quelle, nicht nur die gefilterten, denn das Gate prüft auch Querverweise auf Anforderungen außerhalb der Auswahl.

```python
class Requirement(BaseModel):
    id: str                  # ID wie in der Quelle: "3.1.4", "DET.3.1", "Art. 32", "M60.D01"
    title: str
    text: str                # Volltext, mit normalize() bereinigt (siehe 3)
    primary_anchor: str      # Format nach ARCHITECTURE 1.3, z. B. "CIS AWS v7.0.0 3.1.4"
    attributes: dict[str, str | int | bool]  # Fakten der Quelle für Vorfilter und Ranking
    prefilter_passed: bool

class ExtractedSource(BaseModel):
    source: Literal["BSI", "CIS", "DSGVO", "SDM"]
    version: str             # "v7.0.0", BSI-Commit-SHA, PDF-Version
    origin: str              # Pfad in data/sources/ oder URL
    requirements: list[Requirement]
```

Beispiel (gekürzt):

```json
{
  "source": "CIS",
  "version": "v7.0.0",
  "origin": "data/sources/CIS_Amazon_Web_Services_Foundations_Benchmark_v7.0.0.pdf",
  "requirements": [{
    "id": "3.1.4",
    "title": "Ensure that S3 is configured with 'Block Public Access' enabled",
    "text": "Amazon S3 provides Block public access (bucket settings) and …",
    "primary_anchor": "CIS AWS v7.0.0 3.1.4",
    "attributes": { "chapter": 3, "level": 1, "automated": true },
    "prefilter_passed": true
  }]
}
```

Die `attributes` liefert der Adapter als reine Fakten. Gefiltert und gerankt wird erst danach, in `prefilter()` und `ranking.py`.

| Quelle | `attributes` |
|---|---|
| BSI | `practice` („DET“), `modal_verb`, `sec_level`, `cia_sum` (0–6) |
| CIS | `chapter`, `level` (1/2), `automated` |
| DSGVO | `chapter`, `fine_tier` (4, 2 oder 0 % nach Art. 83) |
| SDM | `module` („M60“), `layer` („D“, „S“, „P“) |

Funktionen je Adapter:

```python
def extract(origin: str, raw: dict, version: str) -> ExtractedSource  # rein: parsen + normalisieren
def prefilter(req: Requirement) -> bool              # rein, Kriterien aus ARCHITECTURE 1.1
```

Datei lesen und `version` aus `data/sources.json` holen übernimmt `python -m kb_build`; so bleiben die Adapter ohne I/O testbar.

Das Gate (#12) prüft `source_quote` gegen den `text` **genau der Anforderung**, auf die der Primäranker zeigt, nicht gegen die ganze Quelle.

### 1.2 Rule – Prüfregel

Stufe ② und das Ranking (#6) schreiben je Audit-Art eine **Auswahlliste** `data/knowledge_base/selection_<spec|arch>.json`. Sie ist der Kontrollpunkt, bevor Prüfregeln formuliert werden (ADR 0007).

```python
class Classification(BaseModel):         # vom LLM, Schema für Tool classify_requirement
    testable: bool
    rationale: str
    cfn_resource_types: list[str] = []   # nur Architektur; bei Spec immer leer

class SelectedRequirement(BaseModel):
    requirement_id: str                  # Requirement.id
    source: Literal["BSI", "CIS", "DSGVO", "SDM"]
    rationale: str                       # Classification.rationale
    cfn_resource_types: list[str]        # Classification.cfn_resource_types
    pinned: bool                         # gesetzter Platz aus einem Preset
    rank: int                            # 1 = zuerst innerhalb der Quelle

class Selection(BaseModel):              # Datei selection_spec.json bzw. selection_arch.json
    audit_type: Literal["spec", "architecture"]
    model_id: str
    selected: list[SelectedRequirement]
```

Die Felder der Prüfregel stehen in ARCHITECTURE 1.2. Das Modell ist zweigeteilt: Was das LLM schreibt, liegt in `RuleDraft`. Aus diesem Modell entsteht auch das Schema des Tools `formulate_rule`. Was der Code weiß, ergänzt `Rule`.

```python
class CrossReference(BaseModel):
    anchor: str                          # Primäranker-Format einer anderen Quelle
    origin: Literal["ai_suggested"]

class RuleDraft(BaseModel):              # vom LLM, Schema für Tool formulate_rule
    source_quote: str
    title: str
    compliant_if: str
    violation_if: str
    recommendation: str
    cross_references: list[CrossReference] = []

class Rule(RuleDraft):                   # vom Code ergänzt
    id: str                              # "<SPEC|ARCH>-<SOURCE>-<Requirement.id ohne Leerzeichen>"
    audit_type: Literal["spec", "architecture"]
    source: Literal["BSI", "CIS", "DSGVO", "SDM"]
    primary_anchor: str                  # aus Requirement übernommen
    selection_rationale: str             # aus der Auswahlliste (Stufe ②)
    cfn_resource_types: list[str] = []   # aus der Auswahlliste; nur Architektur
    rank: int                            # aus der Auswahlliste
    pinned: bool = False                 # gesetzter Platz (ADR 0007)

class RuleCatalog(BaseModel):            # Datei rules_spec.json bzw. rules_arch.json
    audit_type: Literal["spec", "architecture"]
    source_versions: dict[str, str]      # {"CIS": "v7.0.0", "BSI": "<SHA>"}
    model_id: str                        # welches Modell formuliert hat
    rules: list[Rule] = Field(min_length=1)  # leerer Katalog hätte keinen Gesamtstatus
```

Beispiele für IDs: `ARCH-CIS-3.1.4`, `ARCH-BSI-DET.3.1`, `SPEC-DSGVO-Art.32`, `SPEC-SDM-M60.D01`. Der Katalog enthält bewusst keinen Zeitstempel, damit ein unveränderter Build keinen Git-Diff erzeugt.

### 1.3 Archetype – Golden Archetype

Der **Steckbrief** ist die feste Vorgabe eines Menschen (ARCHITECTURE 1.4) und liegt in `data/archetype_profiles.json`. Der Build ergänzt Code, Template und Freigabe-Nachweis.

```python
class ArchetypeProfile(BaseModel):       # Datei data/archetype_profiles.json, von Hand gepflegt
    id: Literal["ARCH-01", "ARCH-02", "ARCH-03"]
    name: str                            # "Sync REST"
    purpose: str                         # Zweck, deutsch; nutzt auch select_archetype
    constructs: list[str]                # ["aws-apigateway-lambda", "aws-lambda-dynamodb"]
    required_resource_types: list[str]   # Struktur-Soll
    resource_types: list[str]            # Relevanzfilter: Pflicht-Typen + IAM::Role, KMS::Key, Logs::LogGroup

class Approval(BaseModel):
    audit_report: AuditReport            # Architektur-Audit des Templates: nur PASS / N/A
    cdk_nag_errors: list[str]            # nach Abzug der Ausnahmen; muss leer sein
    nag_exceptions: list[str]            # angewendete Ausnahmen: "<rule_id> <path>"
    rounds: int                          # 1–3 Korrekturrunden

class Archetype(ArchetypeProfile):
    cdk_code: str                        # Python-CDK, eine Datei
    template: dict                       # CloudFormation-JSON aus cdk synth
    approval: Approval

class ArchetypeCatalog(BaseModel):       # Datei archetypes.json
    rules_arch_sha256: str               # Hash von rules_arch.json, gegen den freigegeben wurde
    archetypes: list[Archetype]
```

`rules_arch_sha256` beweist, dass die Archetypen gegen den **aktuellen** Architektur-Katalog freigegeben wurden. Passt der Hash nicht zur Datei `rules_arch.json` daneben, schlägt das Preset-Gate (#8) fehl.

Die **Ausnahmen** pflegt ein Mensch in `data/nag_allowlist.json` (ADR 0007). Sie gelten für Archetypen und den GovGuard-Stack. Angewendet werden sie vom Code (Build bzw. `infra/`), nie vom LLM-Code.

```python
class NagException(BaseModel):           # ein Eintrag in data/nag_allowlist.json
    rule_id: str                         # "AwsSolutions-IAM4"
    path_pattern: str                    # Glob auf den Construct-Pfad, z. B. "*/BucketNotificationsHandler*/Role/Resource"
    reason: str                          # Begründung, deutsch
```

### 1.4 Preset und Expected

Jedes Preset ist ein Ordner `data/presets/<id>/` mit einer Eingabedatei und einer `preset.json`. Das Soll legt ein Mensch fest.

```python
class RequiredFinding(BaseModel):
    anchor: str                          # Primäranker, z. B. "DSGVO Art. 9" – stabil über Builds
    status: Literal["PASS", "FAIL"]        # nie WARN: Ermessen würde das Gate flackern lassen

class Expected(BaseModel):
    overall_status: Status
    required_findings: list[RequiredFinding]
    archetype: Literal["ARCH-01", "ARCH-02", "ARCH-03", "NONE"] | None = None  # nur Spec ohne FAIL

class Preset(BaseModel):                 # Datei preset.json
    title: str                           # Anzeige in der UI, deutsch
    audit_type: Literal["spec", "architecture"]
    input_file: str                      # "input.md", "openapi.yaml" oder "template.json", max. 100.000 Zeichen
    expected: Expected
```

Das Preset-Gate gilt als bestanden, wenn drei Bedingungen erfüllt sind:
- Der Gesamtstatus stimmt.
- Zu jedem `RequiredFinding` gibt es eine Prüfregel mit diesem Primäranker und genau diesem Status.
- Der Archetyp stimmt, falls einer angegeben ist.

Weitere Befunde sind frei. Ein Anker wird nur Pflicht-Befund, wenn der Bauplan der Eingabe und eine blinde Zweitprüfung mit einem anderen Modell übereinstimmen (FAHRPLAN Schritt 2). Pflicht-Befunde verweisen auf den Primäranker statt auf die Regel-ID, weil ein Mensch ihn direkt aus der Norm kennt. Die Anker aller `required_findings` einer Audit-Art sind zugleich ihre gesetzten Plätze (#6), höchstens 4.

## 2. Laufzeit-Verträge

### 2.1 Finding und AuditReport

Wie bei `Rule` schreibt das LLM nur einen Entwurf. Die Daten aus dem Katalog ergänzt der Code.

```python
Status = Literal["PASS", "WARN", "FAIL", "N/A"]

class FindingDraft(BaseModel):           # vom LLM, ein Element im Tool submit_audit
    rule_id: str
    status: Status
    evidence: str | None                 # wörtliches Zitat aus der Eingabe; Pflicht bei PASS und FAIL
    rationale: str
    recommendation: str | None           # Pflicht bei WARN und FAIL

class AuditResponse(BaseModel):          # Schema des Tools submit_audit
    findings: list[FindingDraft]

class Finding(FindingDraft):             # vom Code aus dem Katalog ergänzt
    title: str
    primary_anchor: str
    cross_references: list[CrossReference]

class AuditReport(BaseModel):
    audit_type: Literal["spec", "architecture"]
    overall_status: Status
    findings: list[Finding]              # genau einer je Prüfregel, Reihenfolge wie im Katalog
    model_id: str
    trace: Trace                         # Rückverfolgung, siehe 2.4
```

- **Beleg-Pflicht folgt aus dem Glossar:** PASS heißt „Einhaltung belegt“, FAIL heißt „Verstoß belegt“, beide brauchen also ein Zitat. Fehlt etwas in der Eingabe, ist das WARN, nicht FAIL.
- **Gesamtstatus:** Rangfolge FAIL > WARN > PASS > N/A, der schlechteste Status gewinnt. Sind alle Befunde N/A, ist der Gesamtstatus N/A.

### 2.2 run_audit() und select_archetype()

Die Prüflogik kennt Bedrock nicht. Sie bekommt ein Pydantic-AI-Modell übergeben (Dependency Injection, ADR 0005). `aws_services.bedrock_model()` baut es mit dem Profil `eu.`, Tests übergeben `TestModel` oder `FunctionModel` von Pydantic AI mit festen Antworten.

```python
# src/govguard/audit_engine.py – rein, ohne boto3
def run_audit(catalog: RuleCatalog, input_text: str, model: Model,
              trace: Trace) -> AuditReport
def select_archetype(spec_text: str, report: AuditReport,
                     catalog: ArchetypeCatalog, model: Model) -> ArchetypeChoice

class AuditDeps(BaseModel):              # deps_type des Audit-Agenten
    catalog: RuleCatalog
    input_text: str
    is_template: bool                    # CloudFormation im Architektur-Audit

class ArchetypeChoice(BaseModel):        # Schema des Tools select_archetype
    archetype: Literal["ARCH-01", "ARCH-02", "ARCH-03", "NONE"]
    rationale: str
```

Vor dem LLM-Aufruf prüft `run_audit()` im Architektur-Audit mit `template_resource_types()` (3), ob die Eingabe ein CloudFormation-Template ist. Falls ja, erhält jede Prüfregel ohne passenden Ressourcentyp im Template vom Code den Befund N/A mit der Begründung „Ressourcentyp nicht im Template“ und geht nicht ans Modell (ADR 0007). Im Spec-Audit geht auch ein Template vollständig ans Modell, denn ein stilles N/A würde eine falsch eingereichte Eingabe verdecken.

`run_audit()` validiert die LLM-Antwort in dieser Reihenfolge:
1. Pydantic-Schema (`AuditResponse`), durch Pydantic AI.
2. Jede an das Modell gesendete `rule_id` kommt genau einmal vor, und es gibt keine unbekannten IDs. Bei CloudFormation ist N/A vom Modell verboten, denn der Ressourcentyp kommt vor; der Prompt sagt das dem Modell vorab.
3. Beleg vorhanden, wo er Pflicht ist (PASS, FAIL), und jeder gesetzte Beleg mit `contains_quote()` wörtlich in der Eingabe gefunden (siehe 3). Empfehlung vorhanden bei WARN und FAIL.

Die Schritte 2 und 3 laufen im `@agent.output_validator` und lösen bei Fehlern `ModelRetry` aus. Pydantic AI schickt die Fehlermeldung dann **einmal** zurück ans Modell (`retries=1`). Scheitert auch der zweite Versuch, wirft die Funktion `AuditValidationError`, und der Handler antwortet mit HTTP 502. `select_archetype()` wirft `ValueError`, wenn der Report ein FAIL enthält.

### 2.3 API-JSON

| Endpunkt | Request | Response 200 |
|---|---|---|
| `POST /audit/spec` | `{"input": "<Text, max. 100.000 Zeichen>"}` | `AuditReport` |
| `POST /audit/architecture` | `{"input": "<Freitext, Terraform oder CloudFormation>"}` | `AuditReport` |
| `POST /archetype/select` | `{"spec": "<Text>", "report": AuditReport}` | `{"archetype", "rationale", "cdk_code", "template"}`; bei `NONE` sind Code und Template `null` |

| Status | Wann | Body |
|---|---|---|
| 400 | Eingabe fehlt oder ist länger als 100.000 Zeichen | `{"error": "invalid_input", "message": "…"}` |
| 403 | SigV4-Signatur fehlt oder ist falsch (API Gateway) | von AWS |
| 422 | `/archetype/select` mit FAIL im Report | `{"error": "report_has_fail", "message": "…"}` |
| 429 | Throttling greift (API Gateway) | von AWS |
| 502 | LLM-Antwort auch nach dem zweiten Versuch ungültig | `{"error": "llm_invalid", "message": "…"}` |
| 504 | Länger als 29 Sekunden (API Gateway) | von AWS |

Die Texte in `message` sind deutsch. Eine CI-Pipeline wertet nur `overall_status` aus (User Story 4).

### 2.4 Trace und AuditEvent – Audit-Protokoll (ADR 0006)

Handler bzw. CLI bauen den `Trace` vor dem Audit; `run_audit()` legt ihn unverändert in den Report. Nach jedem Aufruf, auch bei 422 und 502, loggt der Handler genau ein `AuditEvent` als JSON-Zeile.

```python
class Trace(BaseModel):
    audit_id: str                        # Lambda-Request-ID, in der CLI eine UUID
    input_sha256: str                    # Hash der Eingabe, nie der Text selbst
    catalog_sha256: str                  # Hash der geladenen Datei: rules_*.json bzw. archetypes.json
    kb_commit: str                       # Git-Commit des Deploys, Umgebungsvariable aus deploy.yml

class AuditEvent(BaseModel):             # eine JSON-Zeile in CloudWatch Logs
    event: Literal["audit_event"] = "audit_event"   # Filter für Logs Insights
    timestamp: datetime                  # UTC
    endpoint: Literal["/audit/spec", "/audit/architecture", "/archetype/select"]
    outcome: Literal["ok", "rejected", "validation_failed"]   # 200, 422, 502
    trace: Trace
    model_id: str
    overall_status: Status | None        # None bei /archetype/select und bei Fehlern
    statuses: dict[str, Status]          # rule_id → Status; ohne Belege und Begründungen
    archetype: str | None                # nur /archetype/select
```

- **Keine Zitate im Ereignis:** Belege sind wörtliche Auszüge der Eingabe; im Ereignis stehen nur IDs, Hashes und Status (Datenminimierung, Art. 5 Abs. 1 lit. c DSGVO).
- **Kette zum Regelwerk:** `catalog_sha256` → Katalogdatei im Commit `kb_commit` → `source_versions` (z. B. CIS v7.0.0, BSI-Commit-SHA).

## 3. Gemeinsame Funktionen

Build (Zitat-Check) und Laufzeit (Beleg-Check) normalisieren mit **derselben** Funktion. Sonst würde ein Zitat im Build bestehen und zur Laufzeit scheitern oder umgekehrt.

```python
# src/govguard/text.py – rein
MIN_QUOTE_LENGTH = 15                        # kürzere Zitate wie "S3" beweisen nichts

def normalize(text: str) -> str
def contains_quote(text: str, quote: str) -> bool  # len >= MIN_QUOTE_LENGTH und normalize(quote) in normalize(text)
def template_resource_types(text: str) -> set[str] | None  # Typen aus "Resources" eines CloudFormation-JSON, sonst None
```

`normalize()` führt fünf Schritte aus, in dieser Reihenfolge:
1. Unicode-Normalform NFKC herstellen.
2. EUR-Lex-Marker wie „►C2“ und „◄“ entfernen.
3. Weiche Trennstriche entfernen.
4. Typografische Anführungszeichen und Gedankenstriche durch ASCII-Zeichen ersetzen, damit „…“ und "…" gleich sind.
5. Alle Leerzeichen und Zeilenumbrüche zu einem Leerzeichen zusammenfassen.

Groß- und Kleinschreibung bleibt erhalten, denn „wörtlich“ heißt wörtlich. Eine bekannte Grenze: Silbentrennung am Zeilenende („Verarbei- tung“) wird nicht repariert, weil sich echte Bindestriche („Cloud-Dienst“) nicht sicher davon unterscheiden lassen.

`template_resource_types()` erkennt nur JSON. YAML mit Kurzformen wie `!Ref` und Terraform gelten als Freitext; dort entscheidet das LLM über N/A.
