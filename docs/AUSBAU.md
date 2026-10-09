# GovGuard – Ausbau in fünf Szenarien (Post-MVP)

Das GovGuard-MVP operiert bewusst mit definierten Limits: maximal 24 bzw. 20 Prüfregeln, ein Eingabelimit von 100.000 Zeichen und ein Katalog aus 3 Golden Archetypes. Dieses Dokument beschreibt fünf Ausbaustufen und definiert, was an den aktuellen Architekturgrenzen bricht und wie das System in Produktion darauf skaliert.

Drei fundamentale Prinzipien bleiben in jedem Ausbauszenario konstant:

- Jede Prüfregel bekommt zwingend einen Befund; es werden keine Regeln per Vektorsuche weggelassen.

- Jeder Beleg ist ein wörtliches Zitat, dessen Existenz vom Code verifiziert wird.

- Das LLM urteilt ausschließlich, während der Code die Vorbereitung (Filtern, Clustern) und die Endkontrolle übernimmt.

## Szenario 1: Skalierung der Regelbasis (z. B. auf 80 Regeln oder BSI C5)

- **Auslöser:** Die Wissensbasis überschreitet ca. 50 Regeln oder die API-Antwortzeit nähert sich dem 29-Sekunden-Timeout des API Gateways.

- **Was bricht:** Das Modell muss zu viel auf einmal bewerten. Die Inferenzzeit steigt massiv an, und die Qualität der Antworten sinkt durch das "Lost in the Middle"-Syndrom.

**Architektur-Anpassungen (Lösungen):**

| Phase | Anpassung | Ausführende Schicht |
|---|---|---|
| **Build** | **Quellen-Adapter:** Neue Kataloge (wie BSI C5) erhalten standardisierte Schnittstellen zum Auslesen, Vorfiltern und Ranken. | Code |
| **Build** | **Inkrementeller Build:** Bereits klassifizierte Anforderungen werden gecacht. Das LLM bewertet nur noch Delta-Änderungen (geänderte/neue Regeln). | Code & LLM |
| **Laufzeit** | **Deterministisches Pruning:** Fehlt eine Ressource im IaC-Template (z.B. kein S3-Bucket), setzt der Code alle S3-Prüfregeln sofort auf `N/A`, ohne diese an das LLM zu senden. Im MVP für CloudFormation-JSON umgesetzt (ADR 0007); Ausbau: Terraform und YAML. | Code |
| **Laufzeit** | **Map-Reduce-Evaluierung:** Der Katalog wird in thematische Pakete à 20 Regeln zerlegt. Eigene LLM-Aufrufe evaluieren diese Pakete parallel; der Code führt die Befunde final zusammen. | Code & LLM |

## Szenario 2: Verarbeitung massiver Dokumente (> 100.000 Zeichen)

- **Auslöser:** Upload von 300-seitigen Architekturkonzepten oder 3.000 Zeilen großen Terraform-Projekten.

- **Was bricht:** Der HTTP-Request überschreitet das Payload-Limit (Lambda akzeptiert maximal 6 MB). Das LLM übersieht in riesigen Textmengen kritische DSGVO-Verstöße.

**Architektur-Anpassungen (Lösungen):**

| Eingabeformat | Anpassung | Ausführende Schicht |
|---|---|---|
| **Generell** | **S3-Upload-Pattern:** Der Client lädt die Datei direkt in einen S3-Bucket und übergibt der API lediglich die Object-URI zur Verarbeitung. | Code |
| **IaC / OpenAPI** | **AST-Kürzung:** Ein Parser extrahiert nur sicherheitsrelevante Ressourcen, Attribute und Datenfelder. Unnötige Beschreibungen und Beispiele werden algorithmisch verworfen. | Code |
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

## Systemweite Auswirkungen: Der Weg zu Asynchronität

Sobald Map-Reduce für große Regelkataloge (Szenario 1) oder lange Dokumente (Szenario 2) greift, ändert sich die Systemarchitektur fundamental:

- **REST API:** Antwortet nicht mehr mit dem finalen Report, sondern asynchron mit einer Job-ID (HTTP 202 Accepted).

- **Orchestrierung:** **AWS Step Functions** steuern die parallelen Lambda-Aufrufe (Scatter-Gather-Pattern), wobei Kosten nur pro Ausführung anfallen.

- **Persistenz & DSGVO:** Aufträge und Reports müssen persistent gespeichert (S3/DynamoDB) und abgefragt werden. Dies erzwingt die Implementierung strenger Löschfristen nach Art. 5 Abs. 1 lit. e DSGVO.

**Der Leitgedanke für das Systemdesign:**

> „Wir skalieren durch Aufteilen, nicht durch Weglassen. Vollständigkeit und Zitatpflicht gelten in jeder Ausbaustufe.“
