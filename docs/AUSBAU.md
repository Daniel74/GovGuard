# GovGuard – Ausbau in elf Szenarien (Post-MVP)

Das GovGuard-MVP operiert bewusst mit definierten Limits: ein Prüfumfang aus Serverless-Diensten, RDS/Aurora und Fargate, ein Eingabelimit von 100.000 Zeichen und ein Katalog aus 3 Golden Archetypes. Dieses Dokument beschreibt elf Ausbaustufen und definiert, was an den aktuellen Architekturgrenzen bricht und wie das System in Produktion darauf skaliert.

Drei fundamentale Prinzipien bleiben in jedem Ausbauszenario konstant:

- Jede Prüfregel bekommt zwingend einen Befund; es werden keine Regeln per Vektorsuche weggelassen.

- Jeder Beleg ist ein wörtliches Zitat, dessen Existenz vom Code verifiziert wird.

- Das LLM urteilt ausschließlich, während der Code die Vorbereitung (Filtern, Clustern) und die Endkontrolle übernimmt.

## Szenario 1: Skalierung der Regelbasis (z. B. auf 80 Regeln oder BSI C5)

_Seit ADR 0011 im MVP: Quellen-Adapter, Cache, Pruning per Ressourceninventar und parallele Pakete. Offen bleibt der Umbau auf Asynchronität (unten)._

- **Auslöser:** Die Wissensbasis überschreitet ca. 50 Regeln oder die API-Antwortzeit nähert sich dem 29-Sekunden-Timeout des API Gateways.

- **Was bricht:** Das Modell muss zu viel auf einmal bewerten. Die Inferenzzeit steigt massiv an, und die Qualität der Antworten sinkt durch das "Lost in the Middle"-Syndrom.

**Architektur-Anpassungen (Lösungen):**

| Phase | Anpassung | Ausführende Schicht |
|---|---|---|
| **Build** | **Quellen-Adapter:** Neue Kataloge (wie BSI C5) erhalten standardisierte Schnittstellen zum Auslesen und Vorfiltern. | Code |
| **Build** | **Inkrementeller Build:** Bereits klassifizierte Anforderungen werden gecacht. Das LLM bewertet nur noch Delta-Änderungen (geänderte/neue Regeln). | Code & LLM |
| **Laufzeit** | **Deterministisches Pruning:** Fehlt eine Ressource im IaC-Template (z.B. kein S3-Bucket), setzt der Code alle S3-Prüfregeln sofort auf `N/A`, ohne diese an das LLM zu senden. Im MVP für CloudFormation-JSON umgesetzt (ADR 0007); Terraform: Szenario 9. | Code |
| **Laufzeit** | **Map-Reduce-Evaluierung:** Der Katalog wird in thematische Pakete à 20 Regeln zerlegt. Eigene LLM-Aufrufe evaluieren diese Pakete parallel; der Code führt die Befunde final zusammen. | Code & LLM |

## Szenario 2: Verarbeitung massiver Dokumente (> 100.000 Zeichen)

- **Auslöser:** Upload von 300-seitigen Architekturkonzepten oder 3.000 Zeilen großen Terraform-Projekten.

- **Was bricht:** Der HTTP-Request überschreitet das Payload-Limit (Lambda akzeptiert maximal 6 MB). Das LLM übersieht in riesigen Textmengen kritische DSGVO-Verstöße.

**Architektur-Anpassungen (Lösungen):**

| Eingabeformat | Anpassung | Ausführende Schicht |
|---|---|---|
| **Generell** | **S3-Upload-Pattern:** Der Client lädt die Datei direkt in einen S3-Bucket und übergibt der API lediglich die Object-URI zur Verarbeitung. | Code |
| **IaC / OpenAPI** | **AST-Kürzung:** Ein Parser extrahiert nur sicherheitsrelevante Ressourcen, Attribute und Datenfelder. Unnötige Beschreibungen und Beispiele werden algorithmisch verworfen. | Code |
| **Minifiziertes JSON** | **Belegs-Grenze in Zeichen:** Ohne Zeilenumbrüche liefert ein Zeilenverweis `1-1` die ganze Eingabe als Beleg (ADR 0017). Der Code formatiert JSON vor dem Nummerieren oder begrenzt den Beleg zusätzlich in Zeichen. | Code |
| **Langer Freitext** | **Agentic Map-Reduce (Faktenextraktion):** 1. Code zerlegt das Dokument in Kapitel. 2. Das LLM extrahiert parallel aus jedem Kapitel Fakten (z.B. Datenhaltung, PII) inkl. Zitat. 3. Der Code baut daraus ein kompaktes Faktenblatt. 4. Das Audit läuft auf dem verdichteten Faktenblatt ab. | LLM & Code |

_Hinweis:_ Um blinde Flecken durch die Faktenextraktion transparent zu machen, visualisiert das UI das erzeugte Faktenblatt vor dem eigentlichen Audit-Report.

## Szenario 3: Komplexe Mehrfach-Architekturen

- **Auslöser:** Ein Fachverfahren erfordert eine Kombination aus Backend, Frontend und Audit-Log (mehrere Archetypen gleichzeitig).

- **Was bricht:** Die aktuelle Auswahllogik erzwingt genau _einen_ Golden Archetype. Eine dynamische Generierung zur Laufzeit bricht mit der Prämisse der vorab freigegebenen Templates (ADR 0003).

**Architektur-Anpassungen in Eskalationsstufen:**

1. **Stufe 3a (Mehrfachauswahl):** Die Tool-Choice erlaubt die Rückgabe einer Liste kompatibler Stacks (z.B. ARCH-01 + ARCH-03) inklusive einer Begründung für ihr Zusammenspiel. Das Risiko bleibt minimal, da die Bausteine vorab gehärtet wurden.

2. **Stufe 3b (Kombi-Archetypen):** Sehr häufige Kombinationen (z.B. Antragseingang + Audit-Log-Archiv; Portal + Backend erst mit Szenario 5) werden zur Build-Zeit als neuer, dedizierter Archetyp erzeugt, auditiert und freigegeben.

3. **Stufe 3c (Laufzeit-Generierung):** Das LLM kombiniert Infrastruktur-Bausteine "on the fly". **Risiko hoch:** Bricht ADR 0003. Dies erfordert den Aufbau einer eigenen Build-Container-Infrastruktur, die `cdk synth` und `cdk-nag` pro User-Request asynchron ausführt.

## Szenario 4: Skalierung der Golden Archetypes (> 10 Muster)

- **Auslöser:** Der Baukasten wächst um spezialisierte Muster wie ARCH-06 (Analytics) oder ARCH-07 (Mobile).

- **Was bricht:** Bei vielen ähnlichen Archetypen sinkt die Auswahlpräzision des LLMs; es kommt zu Fehlentscheidungen.

**Architektur-Anpassungen (Lösungen):**

| Phase | Anpassung | Ausführende Schicht |
|---|---|---|
| **Test** | **Auswahl-Presets (Ground Truth):** Für jeden Archetyp wird ein Preset mit fixiertem Soll-Ergebnis definiert, um die KI-Auswahl zu testen. | Mensch |
| **Laufzeit** | **Zweistufige Auswahl:** 1. Das LLM extrahiert binäre Merkmale aus der Spezifikation (z.B. "asynchron?", "Datei-Upload?"). 2. Der Code filtert den Katalog hart nach diesen Merkmalen. 3. Das LLM trifft die finale Auswahl aus den wenigen verbliebenen, gefilterten Mustern. | LLM & Code |

## Szenario 5: Souveräne Cloud und Bürgerportal

- **Auslöser:** Eine Behörde verlangt Betrieb unter EU-Kontrolle, oder ein Vorhaben braucht ein Portal als Teil des Archetyps.

- **Was bricht:** Ein statisches Portal braucht CloudFront. CloudFront hat keine Preisklasse nur für die EU; TLS endet an der Edge, möglicherweise in einem Drittland. Deshalb enden die Archetypen im MVP beim API Gateway (ADR 0009). Die **AWS European Sovereign Cloud** (ESC, GA seit 15.01.2026, Brandenburg) ist eine eigene Partition, getrennt vom globalen AWS. CloudFront ist dort erst für Ende 2026 angekündigt, und Bedrock bietet dort kein Claude, nur Amazon Nova und Open-Weight-Modelle.

**Architektur-Anpassungen (Lösungen):**

| Auslöser | Anpassung | Ausführende Schicht |
|---|---|---|
| **CloudFront ohne Drittlandtransfer** (z. B. in der ESC, Edge-Standorte nur in der EU) | **Portal-Archetyp:** `aws-cloudfront-s3` vor einer bestehenden Kette, z. B. ARCH-02. Bürger melden sich per Cognito an, die Ausnahme COG4 entfällt dann für diese API. Freigabe wie bisher (ADR 0003). Vorher prüfen: Wo terminiert TLS, wo liegen Logs und Cache? | Mensch & Code |
| **Umzug in die ESC** | **Region und Partition** als Konfiguration statt fest `eu-central-1`; ARNs über `Aws.PARTITION`. Alle Gates laufen in der ESC neu. | Code |
| **Kein Claude in der ESC** | **Modellwechsel** (ADR 0001 ersetzen): Nova Pro oder ein Open-Weight-Modell. Das Preset-Gate misst Qualität, Laufzeit (< 29 s) und Kosten neu, bevor gewechselt wird. | Code & LLM |

## Szenario 6: Relationale Datenbank (Aurora Serverless v2)

- **Auslöser:** Ein Fachverfahren braucht SQL, etwa für Berichte oder Fremdschlüssel. Auditiert wird Aurora schon im MVP (Prüfumfang), gebaut wird noch kein Archetyp.
- **Was bricht:** Aurora läuft immer in einer VPC. Die Archetypen kennen bisher keine VPC.

| Hürde | Anpassung | Ausführende Schicht |
|---|---|---|
| **Aufwachen aus der Pause** (0 ACU: bis 15 s, nach über 24 h Pause 30 s oder mehr, laut AWS-Doku) | Der erste Aufruf kann das 29-s-Timeout reißen. Mindestkapazität > 0 kostet Leerlaufkosten, sonst Wiederholung im Client. | Mensch |
| **VPC ist Pflicht** | VPC ohne NAT-Gateway; Lambda greift über die RDS Data API zu, nicht aus der VPC. | Code |
| **FSBP `Lambda.3`** (Lambda in VPC) | Ausnahme mit Begründung „Data API, keine Lambda in der VPC“ (ADR 0011). | Mensch |

## Szenario 7: Leerlaufkosten fremder Architekturen prüfen

- **Auslöser:** Behörden wollen wissen, ob eine Architektur ohne Last Geld kostet (provisioniertes RDS, NAT-Gateway, WAF).
- **Was bricht:** Jede Prüfregel braucht einen Primäranker. Keine Quelle im MVP hat Kostenregeln; ein Hinweis ohne Normanker wäre eine GovGuard-Meinung, kein Befund.
- **Anpassung:** Eine neue Quelle, z. B. die *Cost Optimization*-Säule des AWS Well-Architected Framework (nicht recherchiert), über das Rezept für neue Quellen (ARCHITECTURE, *Code-Struktur*).

## Szenario 8: Container-Archetyp (Fargate)

- **Auslöser:** Ein Fachverfahren liegt schon als Container vor oder braucht lange Laufzeiten über 15 Minuten. Auditiert wird Fargate schon im MVP (Prüfumfang), gebaut wird kein Archetyp.
- **Was bricht:** Ein Fargate-Dienst läuft dauerhaft und hat damit Leerlaufkosten. Er braucht eine VPC und meist einen Application Load Balancer, der selbst Leerlaufkosten hat.
- **Anpassung:** Ein Container-Archetyp nur mit bewusst akzeptierten Leerlaufkosten, dokumentiert als Ausnahme von der FinOps-Leitplanke (neuer ADR). Vorher prüfen: Reicht ein ereignisgesteuerter Fargate-Task (z. B. Step Functions oder EventBridge startet ihn), der ohne Last nicht läuft?

## Szenario 9: Terraform als Format mit Code-Inventar

- **Auslöser:** Behörden liefern ihre Architektur als Terraform, und N/A soll der Code setzen statt des LLM (ADR 0015).
- **Was bricht:** Prüfregeln, Prüfumfang und Eigenschaften sprechen CloudFormation (`AWS::S3::Bucket`), Terraform heißt `aws_s3_bucket`. Die Zuordnung ist nicht 1:1: Ein CloudFormation-Typ verteilt sich in Terraform auf mehrere Blöcke (z. B. Verschlüsselung als eigener Block). Im MVP gilt Terraform als Freitext, und kein Preset testet es.

| Weg | Anpassung | Ausführende Schicht |
|---|---|---|
| **Plan-JSON + Zuordnungstabelle** | `terraform show -json` liefert ein maschinenlesbares Inventar; eine gepflegte Tabelle `aws_*` → `AWS::*` übersetzt die Typen. Zuerst ein Terraform-Preset, dann die Tabelle, beides getestet. | Code & Mensch |
| **CloudFormation IaC Generator nach dem Deploy** | Der Generator scannt bereits angelegte Ressourcen einer Region im Konto und erzeugt daraus ein CloudFormation-Template (laut AWS-Doku nur Typen, die die Cloud Control API unterstützt; ein Template fasst bis zu 500 Ressourcen). Geprüft wird also der Ist-Zustand nach dem Deploy, nicht die Eingabe vor dem Deploy. Vorher klären: Kontozugriff und IAM-Rechte, Region, und ob der Beleg aus dem generierten Template noch „Eingabe“ ist. _(Stand der AWS-Doku am 2026-10-14, vor dem Bau erneut prüfen.)_ | Code |
| **LLM übersetzt nach CloudFormation** | **Ausdrücklich verworfen (ADR 0015):** Der Beleg stünde nicht mehr in der Eingabe, der Existenz-Check wäre wertlos. | – |

## Szenario 10: KI-Verordnung als Quelle im Spec-Audit (#52)

_Schlanke Variante in Umsetzung (#52, FAHRPLAN 12n): ca. 8 Artikel, ohne Vorstufe für die Hochrisiko-Einstufung. Offen bleiben die Vorstufe und der volle Umfang._

- **Auslöser:** Behörden setzen KI-Systeme ein und haben dann eigene Pflichten nach der KI-Verordnung (Verordnung (EU) 2024/1689), z. B. als Betreiber (Art. 26) und als öffentliche Stelle mit Grundrechte-Folgenabschätzung (Art. 27). GovGuard ist selbst ein KI-System; das Selbst-Audit (`spec-govguard`) würde dann auch gegen die KI-Verordnung prüfen.
- **Was bricht:** Die meisten Pflichten gelten nur für Hochrisiko-Systeme (Art. 6, Anhang III). Ob eine Spezifikation darunter fällt, muss vor allen anderen Regeln feststehen; sonst vergibt das Modell N/A je Regel einzeln, und das schwankt (SPEC P1). Der Katalog ist eingefroren (SPEC G13).
- **Anpassung:** Neue Quelle über das Rezept (ARCHITECTURE, *Neue Quelle hinzufügen*). Der Text liegt wie die DSGVO im Formex-XML bei EUR-Lex; der DSGVO-Adapter ist vermutlich weitgehend wiederverwendbar. Dazu ein Musterfall mit KI-Einsatz und Soll, und für `spec-govguard` ein neues Soll. Vorher klären: Wer entscheidet die Hochrisiko-Einstufung (Code-Vorstufe oder Mensch), und welche Fristen gelten aktuell? _(Rechtsstand vor dem Bau prüfen.)_

## Szenario 11: Prompt-Fassung und Betrieb beobachtbar machen

- **Auslöser:** Prompts werden weiterentwickelt und sollen schrittweise eingeführt werden: eine neue Fassung erst für einen Teil der Audits, dann messbar mit der alten verglichen.
- **Was bricht:** Der Audit-Report nennt `model_id` und `catalog_sha256`, aber keine Prompt-Fassung. `kb_commit` steht im Demo-Stand auf `local`. Ein Betriebsprotokoll gibt es nicht: `AuditEvent` existiert nur als Modell (ADR 0006). Prompts liegen als Python-Texte im Code; ihre Änderungen zeigt nur der Git-Verlauf (SPEC, Abschnitt 12).

| Anpassung | Ausführende Schicht |
|---|---|
| **Prompt-Prüfsumme in der Rückverfolgung:** `Trace.prompt_sha256` über System-Prompt, Regel der offenen Welt, Prompt der Zweitprüfung und Tool-Schemas, nach dem Vorbild von `prompt_version` im Bau. Zwei Reports sind dann nur vergleichbar, wenn Modell, Katalog und Prompts gleich sind. | Code |
| **Prompt-Fassung beim Formulieren:** dieselbe Prüfsumme im Bauprotokoll von `rules`, damit eine Prüfregel ihrer Prompt-Fassung zugeordnet werden kann. | Code |
| **Versionsstand setzen:** `KB_COMMIT` in den Secrets von Streamlit bzw. im Deploy setzen. | Betrieb |
| **Betriebsprotokoll:** `AuditEvent` je Audit schreiben (Recruiter-Stand: CloudWatch Logs, ADR 0006), ergänzt um Laufzeit, Tokens und Prompt-Prüfsumme. Daraus lassen sich Abbruchquote, Laufzeit und Kosten je Prompt-Fassung auswerten. | Code & Betrieb |
| **Prompts als Dateien (optional):** erst, wenn Fachleute ohne Programmierkenntnis Prompts pflegen sollen. Der Lader gehört in den Einstieg, die Prüflogik bleibt ohne Datei-Zugriff. | Code |

## Weitere Typen im Prüfumfang (EFS, SSM-Klartext-Parameter)

- **Auslöser:** Prüfregeln nennen `AWS::EFS::FileSystem` (Verschlüsselung, Backup) und `AWS::SSM::Parameter` (Klartext statt SecureString). Beide liegen außerhalb des Prüfumfangs (ADR 0013), die Regeln fallen deshalb aus dem Katalog.
- **Anpassung:** Typ in `scope.json`, Snapshot neu ziehen (README), Stufe ② voll neu laufen lassen. Bei SSM-Parametern zuerst klären, wie ein Klartext-Parameter am Template erkennbar ist (`Type: String` gegen `SecureString`).

## Systemweite Auswirkungen: Der Weg zu Asynchronität

Sobald Map-Reduce für große Regelkataloge (Szenario 1) oder lange Dokumente (Szenario 2) greift, ändert sich die Systemarchitektur fundamental:

- **REST API:** Antwortet nicht mehr mit dem finalen Report, sondern asynchron mit einer Job-ID (HTTP 202 Accepted).

- **Orchestrierung:** **AWS Step Functions** steuern die parallelen Lambda-Aufrufe (Scatter-Gather-Pattern), wobei Kosten nur pro Ausführung anfallen.

- **Persistenz & DSGVO:** Aufträge und Reports müssen persistent gespeichert (S3/DynamoDB) und abgefragt werden. Dies erzwingt die Implementierung strenger Löschfristen nach Art. 5 Abs. 1 lit. e DSGVO.

**Der Leitgedanke für das Systemdesign:**

> „Wir skalieren durch Aufteilen, nicht durch Weglassen. Vollständigkeit und Zitatpflicht gelten in jeder Ausbaustufe.“
