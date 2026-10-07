# **Übersetzung normativer Datenschutzvorgaben in deklarative Cloud-Infrastrukturen: Eine Analyse anhand von DSGVO, SDM V3.1a und AWS Serverless-Spezifikationen**

Die Überführung abstrakter juristischer Normen in deterministische, maschinenlesbare Infrastruktur-Architekturen stellt eine der zentralen Herausforderungen der modernen Cloud-Entwicklung dar. Die europäische Datenschutz-Grundverordnung (DSGVO) verlangt den Schutz der Grundrechte und Grundfreiheiten natürlicher Personen bei der Verarbeitung personenbezogener Daten1. Um diese abstrakten Schutzziele handhabbar zu machen, haben die deutschen Datenschutzaufsichtsbehörden das Standard-Datenschutzmodell (SDM) in der Version V3.1a entwickelt2. Das SDM operationalisiert die Rechtsnormen der DSGVO durch sieben Gewährleistungsziele: Datenminimierung, Verfügbarkeit, Integrität, Vertraulichkeit, Nichtverkettung, Transparenz und Intervenierbarkeit2.  
In einer hochdynamischen, deklarativ gesteuerten Amazon Web Services (AWS) Serverless-Umgebung – insbesondere im Kontext von GovCloud-Infrastrukturen – können diese Gewährleistungsziele nicht länger durch nachgelagerte, manuelle Audits oder rein organisatorische Richtlinien sichergestellt werden. Vielmehr müssen sie als „Privacy by Design“ (Datenschutz durch Technikgestaltung) direkt in der Infrastructure as Code (IaC), primär über Terraform, sowie in den Software-Spezifikationen wie OpenAPI verankert werden1. Dieser Bericht liefert eine erschöpfende Analyse darüber, wie die juristischen Vorgaben der DSGVO und die methodischen Anforderungen des SDM auf der Ebene von APIs, Datenbanken und globalen Cloud-Richtlinien in AWS exakt übersetzt werden. Ferner wird eine formale Ableitung für eine Compliance-Audit-Engine dargelegt, die in der Lage ist, Infrastrukturspezifikationen auf Code-Ebene zu evaluieren und abgelehnte Architekturen präventiv zu blockieren.

## **1\. SDM-Gewährleistungsziele im Code: Architektur und Entwicklerperspektive**

Für Cloud-Entwickler und Infrastruktur-Architekten stellen die Gewährleistungsziele des SDM fundamentale Systemanforderungen dar, die das Design von der ersten API-Ressource bis hin zur physischen Datenspeicherung determinieren. Das SDM beschreibt einen iterativen Prozess aus Planung, Implementierung, Kontrolle und Verbesserung (Plan-Do-Check-Act-Zyklus), innerhalb dessen die Gewährleistungsziele als konkrete Leitplanken für das Systemdesign fungieren2. Insbesondere die Ziele „Datenminimierung“, „Nichtverkettung“ und „Intervenierbarkeit“ erzwingen bei der Nutzung von Serverless-Technologien wie AWS Lambda, Amazon API Gateway und Amazon DynamoDB spezifische architektonische Muster, die sich drastisch von traditionellen monolithischen Systemen unterscheiden.

| SDM-Gewährleistungsziel | Juristischer Ursprung (DSGVO) | Cloud-Natives Implementierungsparadigma in AWS Serverless |
| :---- | :---- | :---- |
| Datenminimierung | Art. 5 Abs. 1 lit. c, Art. 25 | Strikte API-Schema-Validierung (OpenAPI), kurzlebige Compute-Instanzen (Lambda), automatische Löschung durch DynamoDB TTL. |
| Nichtverkettung | Art. 5 Abs. 1 lit. b | Bounded Contexts via Microservices, dedizierte DynamoDB-Tabellen pro Service, getrennte AWS-Accounts via AWS Organizations. |
| Intervenierbarkeit | Art. 12-22 | Event-Driven Deletion via Amazon EventBridge, Crypto-Shredding, automatisierte Datenexport-APIs via AWS Step Functions. |

### **1.1 Datenminimierung (Data Minimization) aus Entwicklersicht**

Das Gewährleistungsziel der Datenminimierung konkretisiert und operationalisiert den Grundsatz der Erforderlichkeit, der verlangt, dass die Verarbeitung personenbezogener Daten auf das für den Zweck angemessene, erhebliche und absolut notwendige Maß beschränkt bleibt1. Für einen Cloud-Entwickler bedeutet dies die Abkehr vom klassischen Paradigma des unbegrenzten Datensammelns hin zu einem hochgradig defensiven Datenmodell. Das Minimierungsgebot erstreckt sich auf die Menge der erhobenen Daten, den Umfang der Verarbeitung, die Zugänglichkeit und die Speicherfrist2.  
In einer AWS Serverless-Architektur manifestiert sich die Datenminimierung zunächst an der Peripherie des Systems, konkret am API-Gateway. Entwickler nutzen die OpenAPI 3.0-Spezifikation (OAS), um den Kontrakt zwischen dem Client und dem Cloud-Backend zu definieren3. Die OAS 3.0 erlaubt standardmäßig die Übermittlung nicht deklarierter Felder, da das Attribut additionalProperties implizit auf true gesetzt ist4. Aus der Perspektive der Datenminimierung ist dies ein kritisches Risiko, da übermäßig sendende Clients unstrukturierte personenbezogene Daten in das System injizieren könnten, die das Backend ohne weitere Prüfung in NoSQL-Datenbanken wie DynamoDB persistieren würde. Die technische Umsetzung des Minimierungsgebots erfordert daher die zwingende Definition von additionalProperties: false in sämtlichen Request-Body-Schemata5. Ergänzt wird diese Konfiguration durch den AWS API Gateway Request Validator, der so konfiguriert wird, dass Anfragen, die vom Schema abweichen, bereits an der Netzwerkkante mit einem HTTP 400 Statuscode abgewiesen werden, ohne jemals AWS Lambda-Rechenzeit zu konsumieren oder Daten in der Cloud zu hinterlassen6.  
Darüber hinaus erfordert die Datenminimierung eine strikte Speicherbegrenzung1. Personenbezogene Daten dürfen nur so lange in identifizierbarer Form gespeichert werden, wie es für den Zweck erforderlich ist1. In Amazon DynamoDB wird dies nicht durch kostenintensive, manuelle Batch-Prozesse erreicht, sondern durch das native Time-To-Live (TTL)-Feature. Entwickler fügen den Datensätzen ein Ablaufdatum als Epochen-Zeitstempel hinzu. Sobald dieser Zeitstempel überschritten ist, markiert DynamoDB das Element als abgelaufen und entfernt es innerhalb von 48 Stunden automatisch aus der Tabelle7. Dieser asynchrone, von AWS verwaltete Prozess garantiert die Einhaltung von Löschfristen ohne den Aufbau eigener, fehleranfälliger Löschroutinen und entspricht exakt der Forderung des SDM, die Dauer der Datenspeicherung durch automatisierte Prozesse auf das notwendige Maß zu beschränken2.

### **1.2 Nichtverkettung (Unlinkability) aus Entwicklersicht**

Das Gewährleistungsziel der Nichtverkettung fordert, dass personenbezogene Daten, die für unterschiedliche Zwecke erhoben wurden, nicht unzulässig zusammengeführt oder verknüpft werden dürfen1. Das SDM betont im Baustein 50 ("Trennen"), dass unterschiedliche Zwecke von Verarbeitungstätigkeiten unterschiedliche Befugnisse erzeugen, die zwingend Trennungsmaßnahmen erfordern9. Aus der Sicht eines Cloud-Architekten entspricht dieses Konzept der Isolation von Domänen im Sinne des Domain-Driven Design (DDD).  
Die Architektur-Patterns zur Erreichung der Nichtverkettung basieren auf strenger Kapselung. Anstelle eines monolithischen Datenbankschemas, in dem Authentifizierungsdaten, Transaktionshistorien und Kundensupportdaten in relationalen Tabellen verknüpft sind, bedient sich die Serverless-Architektur des Konzepts der "Polyglot Persistence". Jeder Microservice verwaltet seine eigene, dedizierte DynamoDB-Tabelle9. Die Nichtverkettung wird auf der Ebene des AWS Identity and Access Management (IAM) durch das Prinzip der geringsten Rechte (Least Privilege) erzwungen: Die IAM-Rolle, die der Lambda-Funktion des Rechnungsservices zugewiesen ist, erhält ausschließlich Lese- und Schreibrechte für die DynamoDB-Tabelle des Rechnungsservices und hat technisch keine Möglichkeit, auf die Tabelle des Marketingservices zuzugreifen.  
Sollten übergreifende Analysen notwendig sein, fordert das SDM, dass eine solche Zusammenführung nur unter definierten, gesicherten und dokumentierten Bedingungen stattfindet9. Hierfür wird AWS Key Management Service (KMS) eingesetzt. Durch die Vergabe von service-spezifischen Customer Managed Keys (CMKs) wird eine kryptographische Trennung erreicht10. Selbst wenn Datenexporte in einem gemeinsamen Amazon S3 Data Lake abgelegt werden, bleiben die Daten der unterschiedlichen Services verschlüsselt isoliert. Eine Verknüpfung der Datenbestände ist erst möglich, wenn einer IAM-Rolle durch die KMS Key Policy explizit das Recht zur Entschlüsselung beider Datenquellen eingeräumt wird (kms:Decrypt auf beide Schlüssel)10. Diese strikte Trennung von Schlüsseln und Daten verhindert proaktiv eine anwendungsübergreifende Verkettung durch Datenbankadministratoren oder unautorisierte Prozesse.

### **1.3 Intervenierbarkeit (Intervenability) aus Entwicklersicht**

Intervenierbarkeit beschreibt die technische Disposition eines Systems, die Rechte der betroffenen Personen aus Kapitel III der DSGVO (wie das Recht auf Auskunft, Berichtigung, Löschung und Datenübertragbarkeit) jederzeit, unverzüglich und wirksam umzusetzen1. Das SDM verlangt, dass die verarbeitende Stelle jederzeit in die Datenverarbeitung eingreifen kann, vom Erheben bis zum Löschen der Daten2. Für den Entwickler bedeutet dies, dass Interventionsprozesse als First-Class-Citizens der Architektur entworfen werden müssen.  
Das klassische Pattern hierfür ist die Bereitstellung spezifischer Privacy-Endpoints in der OpenAPI-Definition des API-Gateways. Anstatt dass ein Administrator manuelle SQL-Löschbefehle auf Zuruf ausführt, interagieren autorisierte Systeme oder die betroffenen Personen selbst mit standardisierten REST-Ressourcen. Ein Löschauftrag (gemäß Art. 17 DSGVO) über einen Endpoint wie DELETE /api/v1/users/{userId} löst dabei idealerweise ein verteiltes Ereignis (Event) in Amazon EventBridge aus. Da die Architektur aus Microservices besteht, die dem Gebot der Nichtverkettung folgen, ist es unmöglich, die Löschung zentral in einer Datenbank vorzunehmen. Stattdessen wird ein UserDeleted-Event über den zentralen EventBus publiziert. Jeder angebundene Microservice (beispielsweise das Billing-Modul, das Analytics-Modul und das Support-Modul) konsumiert dieses Event asynchron und triggert isoliert die eigenen Lösch- oder Anonymisierungsroutinen8.  
Eine erhebliche Herausforderung der Intervenierbarkeit stellt die Löschung aus asynchronen Backups und immutablen Event-Logs dar. Das SDM weist darauf hin, dass eine Löschung erst vollzogen ist, wenn keine Kopie oder Replikation mehr bei dem Verantwortlichen gespeichert ist, mit der eine natürliche Person identifiziert werden kann8. Da es technisch kaum praktikabel ist, einzelne Datensätze aus fortlaufenden S3-Archiven oder Glacier-Backups herauszuschneiden, wird das kryptographische Pattern des "Crypto-Shredding" (Krypto-Vernichtung) angewandt. Dabei werden die personenbezogenen Daten (PII) eines jeden Nutzers mit einem eindeutigen, benutzerspezifischen Datenteilschlüssel verschlüsselt8. Soll der Nutzer gelöscht werden, wird nicht das Datum in den zahllosen Backups gesucht, sondern lediglich der KMS-Masterschlüssel oder der entsprechende Schlüsselverweis im Key Store vernichtet8. Durch die Vernichtung des Schlüssels werden alle vorhandenen Backups der PII dieses Nutzers im selben Moment mathematisch unlesbar und gelten im Sinne der DSGVO als gelöscht, wodurch die Intervenierbarkeit selbst bei komplexen Speicherszenarien gewahrt bleibt.

## **2\. DSGVO Cloud-Mapping (Art. 5, 25, 32, 44\)**

Die DSGVO ist technologieneutral verfasst. Der Erfolg von Cloud-Compliance hängt daher maßgeblich von der Fähigkeit ab, die normativen Anforderungen in präzise technische Spezifikationen und Cloud-Dienst-Konfigurationen zu übersetzen. Im Folgenden wird die Synthese der rechtlichen Artikel in AWS-Architektur-Paradigmen detailliert analysiert.

### **2.1 Umsetzung von Art. 25 (Privacy by Design / Privacy by Default)**

Artikel 25 DSGVO ordnet an, dass der Verantwortliche bereits bei der Konzeption von Systemen und bei deren Betrieb geeignete technische und organisatorische Maßnahmen treffen muss, um den Datenschutz wirksam umzusetzen1. Die Maßnahmen müssen so ausgelegt sein, dass durch Voreinstellung nur personenbezogene Daten verarbeitet werden, die für den spezifischen Zweck erforderlich sind1.  
In modernen Cloud-Datenbanken wie DynamoDB bedeutet Privacy by Design die Abkehr von reiner Festplattenverschlüsselung (Storage-level Encryption) hin zur Verschlüsselung auf Applikationsebene. AWS bietet hierfür das AWS Database Encryption SDK an, welches eine attributbasierte (feldgenaue) Verschlüsselung ermöglicht12. Wenn Daten in der AWS-Infrastruktur persistiert werden, ist es datenschutzrechtlich kritisch, dass nicht einmal der Cloud-Provider oder ein Datenbankadministrator Zugriff auf die Klartexte sensibler Felder hat13.  
Das SDK verschlüsselt in der Anwendungsschicht gezielt nur jene Attribute (z.B. medizinische Diagnosen, Sozialversicherungsnummern), die als ENCRYPT\_AND\_SIGN markiert wurden, während Primärschlüssel zur Indexierung als SIGN\_ONLY im Klartext verbleiben12. Das SDK erzeugt für jedes Item einen einzigartigen symmetrischen Datenschlüssel, verschlüsselt die definierten Attribute und verschlüsselt anschließend den Datenschlüssel selbst mit einem Wrapping-Key (Envelope Encryption), der über den AWS KMS bezogen wird12. Die Kapselung der Entschlüsselungslogik innerhalb der Applikation garantiert, dass das Gebot der datenschutzfreundlichen Voreinstellungen erfüllt wird, da die Datenbank durch ihre reine Struktur keine PII im Klartext offenlegt. Zur Sicherung der Integrität (SDM-Gewährleistungsziel) fügt das SDK ein Signatur-Feld (aws\_dbe\_foot) hinzu, das kryptographisch über alle Attribute berechnet wird (mittels ECDSA oder HMAC)14. Jede Manipulation des Datensatzes auf Ebene der Cloud-Datenbank führt unweigerlich zu einem Signaturfehler beim Auslesen, womit unautorisierte Modifikationen nach dem Stand der Technik ausgeschlossen werden14.

### **2.2 Umsetzung von Art. 32 (Sicherheit der Verarbeitung)**

Artikel 32 DSGVO zwingt den Verantwortlichen, die Sicherheit der Verarbeitung zu gewährleisten. Dies umfasst explizit die Pseudonymisierung und Verschlüsselung, die Gewährleistung von Vertraulichkeit, Integrität, Verfügbarkeit und Belastbarkeit der Systeme sowie ein Verfahren zur regelmäßigen Überprüfung der Wirksamkeit dieser Maßnahmen1.

| DSGVO Art. 32 Anforderung | AWS-Sicherheitsmechanismus (Terraform-Repräsentation) | Funktionsweise |
| :---- | :---- | :---- |
| **Vertraulichkeit** & Verschlüsselung | AWS KMS Customer Managed Keys (aws\_kms\_key) | Die alleinige Nutzung der von AWS verwalteten Schlüssel genügt hohen Compliance-Anforderungen nicht. Es müssen CMKs erstellt werden, bei denen die Schlüsselrotation (enable\_key\_rotation \= true) aktiviert ist und die Zugriffspolitik (aws\_kms\_key\_policy) extrem restriktiv gehandhabt wird10. |
| **Sicherheit der Übertragung** (Integrität) | TLS 1.3 via API Gateway Security Policies | Daten in Transit müssen gegen Abfangen und Modifikation gesichert sein. In Terraform wird für Custom Domain Names des API Gateways die security\_policy zwingend auf die neuesten Standards, optimalerweise TLS 1.3, konfiguriert (SecurityPolicy\_TLS13\_1\_3\_...)17. TLS 1.2 mit Perfect Forward Secrecy bildet das absolute Minimum19. |
| **Belastbarkeit** & Verfügbarkeit | API Gateway Throttling Limits (throttling\_rate\_limit) | Belastbarkeit (Resilience) bedeutet Widerstandsfähigkeit gegen externe Angriffe. Durch die Definition von Rate Limits (maximale Anfragen pro Sekunde) und Burst Limits in der API Gateway Konfiguration20 wird der Backend-Ressourcenverbrauch kontrolliert. Ein Token-Bucket-Algorithmus schützt die Lambda-Funktionen vor Erschöpfung durch DDoS-Attacken. |
| **Evaluierbarkeit** & Kontrolle | Verschlüsselte und fristgebundene CloudWatch Logs | Die Wirksamkeit der Maßnahmen muss kontrolliert werden1. Das SDM verlangt im Baustein "Protokollieren" dedizierte System-Logs21. Die Log-Gruppen (aws\_cloudwatch\_log\_group) müssen mit einem CMK (kms\_key\_id) verschlüsselt sein und eine definierte Löschfrist (retention\_in\_days) besitzen, um ausufernde Datenhalden zu vermeiden22. |

Die Umsetzung von Art. 32 erstreckt sich auch auf das Netzwerkdesign. Im Kontext von GovCloud oder hochsensiblen Finanz-Applikationen wird das Risiko der Datenübertragung über das öffentliche Internet vollständig eliminiert, indem AWS PrivateLink (VPC Endpoints) verwendet wird. Die Kommunikation zwischen den Serverless-Komponenten (API Gateway zu Lambda, Lambda zu DynamoDB) erfolgt dann ausschließlich innerhalb des isolierten AWS-Backbone-Netzwerks, was die Angriffsfläche für Data-in-Transit-Abfänge drastisch minimiert.

### **2.3 Analyse von Art. 44 (Drittlandtransfer) im AWS-Kontext**

Das Kapitel V der DSGVO (Art. 44 ff.) regelt die Übermittlung personenbezogener Daten an Drittländer oder internationale Organisationen1. Eine Übermittlung ist nur zulässig, wenn der Verantwortliche die Vorgaben der Verordnung einhält und ein angemessenes Schutzniveau gewährleistet bleibt1. Im Kontext eines US-amerikanischen Hyperscalers wie AWS ist diese Thematik aufgrund des "Schrems II"-Urteils des Europäischen Gerichtshofs und extraterritorialer Gesetze wie dem US CLOUD Act (Clarifying Lawful Overseas Use of Data Act) hochbrisant23. Der CLOUD Act ermöglicht es US-Behörden theoretisch, den Zugriff auf Daten zu erzwingen, die von US-Unternehmen auch auf Servern innerhalb der Europäischen Union gespeichert werden23.  
Um die Risiken des Drittlandtransfers zu steuern, müssen zunächst technische Schutzwälle auf der Kontroll- und Verwaltungsebene (Control Plane) der Cloud etabliert werden. Die alleinige Dienstanweisung, Ressourcen nur in der Region Frankfurt (eu-central-1) bereitzustellen, ist fehleranfällig. Moderne Architektur nutzt AWS Organizations in Kombination mit Service Control Policies (SCPs), um ein hartes Geofencing auf Organisationsebene zu implementieren24. SCPs sind IAM-Richtlinien, die den absoluten Maximalradius an Berechtigungen definieren; sie überschreiben sämtliche administrativen Rechte25. Eine Region-Deny-SCP blockiert systematisch jede API-Operation (wie das Erstellen eines S3-Buckets oder den Start einer EC2-Instanz), deren Kontext (aws:RequestedRegion) nicht auf die autorisierte EU-Region (z.B. eu-central-1) lautet24. Ausgenommen von diesem Blockade-Regelwerk werden lediglich die zwingend global operierenden AWS-Dienste wie AWS Identity and Access Management (IAM), AWS Organizations oder Amazon CloudFront, da deren Metadaten global in us-east-1 verarbeitet werden müssen24.  
**Technisch-organisatorische Abwehr des CLOUD Act:** Das Sperren physischer Regionen adressiert jedoch nicht das juristische Zugriffsrisiko des US-Mutterkonzerns. Um den Zugriff von US-Behörden wirksam auszuschließen und damit den Vorgaben des Europäischen Datenschutzausschusses (EDSA) zu genügen, bedarf es einer kryptographischen Isolation. AWS adressiert dieses tiefgreifende Souveränitätsbedürfnis langfristig durch die angekündigte AWS European Sovereign Cloud, welche infrastrukturell und operativ vollständig durch in der EU ansässiges Personal getrennt vom globalen AWS-Netz betrieben wird. Bis zur vollständigen Migration in souveräne Cloud-Architekturen verlangt der Stand der Technik die Nutzung von External Key Stores (XKS) in Verbindung mit Client-Side Encryption12. Die Kryptoschlüssel zur Entschlüsselung der in AWS gespeicherten Daten (z.B. via AWS KMS External Key Store) liegen dabei auf einem physischen Hardware Security Module (HSM) außerhalb der AWS-Infrastruktur, idealerweise betrieben von einer europäischen Entität (z. B. T-Systems). Selbst wenn US-Behörden durch einen Beschluss unter dem CLOUD Act die Herausgabe der Cloud-Speicherdaten erzwingen, erhält AWS lediglich stark verschlüsselte Chiffretexte. Da AWS physisch nicht in der Lage ist, den Entschlüsselungsprozess ohne kontinuierliche Anfragen an das externe, europäische HSM durchzuführen – welches unter Kontrolle des Verantwortlichen steht und Anfragen aus Drittstaaten ablehnen kann –, wird ein Zugriff effektiv verhindert und Art. 44 DSGVO konform umgesetzt.

## **3\. Ableitung für die Compliance-Audit-Engine (Unified Audit Rules)**

Um die Einhaltung der juristischen (DSGVO) und architektonischen (SDM) Vorgaben in skalierenden Cloud-Infrastrukturen zu garantieren, dürfen Compliance-Prüfungen nicht post-mortem erfolgen. Eine präventive Automatisierung innerhalb der CI/CD-Pipeline ist zwingend erforderlich. Tools wie HashiCorp Sentinel, Checkov oder Open Policy Agent (OPA) können den Terraform- (HCL) und OpenAPI-Code statisch analysieren, bevor eine einzige Ressource in der Cloud entsteht.  
Die nachfolgenden Unified Audit Rules (UAR) definieren die exakten mappings zwischen Rechtstext, SDM-Gewährleistungsziel und Code-Muster. Wenn ein "Violation Pattern" identifiziert wird, unterbricht die Engine den Deployment-Prozess mit einem harten FAIL-Status.

### **Regel 1: SDM Datenminimierung – Strict Payload Enforcement (OpenAPI/Terraform)**

**Rechtliche & Methodische Basis:** Art. 25 DSGVO (Privacy by Default)1 und SDM-Ziel "Datenminimierung"2. Die Architektur darf keine PII aufnehmen, die nicht zweckgebunden im Schema deklariert sind. Da die OpenAPI 3.0-Spezifikation zusätzliche JSON-Felder standardmäßig zulässt (additionalProperties ist implizit true4), entsteht eine massive Sicherheitslücke für PII-Injektionen.  
**Prüflogik:** Die Audit-Engine muss das Zusammenspiel von Infrastruktur-Routing und API-Definition validieren. Erstens muss in der Terraform-Deklaration des AWS API Gateway Request Validators die Prüfung des Request-Bodys (validate\_request\_body) zwingend aktiviert sein6. Zweitens muss die referenzierte OpenAPI-YAML/JSON-Datei geparst werden: Jedes deklarierte Objekt-Schema muss das Attribut additionalProperties: false enthalten5.  
**Violation Pattern (FAIL):** Die API-Infrastruktur verzichtet auf eine harte Validierung oder die OpenAPI-Spezifikation verlässt sich auf die unsicheren Default-Werte4. *Terraform (Anti-Pattern):*

Terraform  
resource "aws\_api\_gateway\_request\_validator" "violation\_validator" {  
  name                        \= "loose-validator"  
  rest\_api\_id                 \= aws\_api\_gateway\_rest\_api.api.id  
  validate\_request\_body       \= false \# FAIL: Das API Gateway prüft den Body nicht.  
  validate\_request\_parameters \= false  
}

*OpenAPI (Anti-Pattern):*

YAML  
UserPayload:  
  type: object  
  \# FAIL: additionalProperties ist nicht definiert, somit greift der Default 'true'.  
  \# Das Backend würde nicht deklarierte Felder (z.B. Gesundheitsdaten) blind akzeptieren.  
  properties:  
    id:  
      type: string

**Compliant Pattern (PASS):** Der Request-Validator in Terraform verlangt eine Prüfung und die OAS 3.0 Definition weist unbekannte Attribute kryptographisch strikt ab5. *Terraform (Compliant):*

Terraform  
resource "aws\_api\_gateway\_request\_validator" "compliant\_validator" {  
  name                        \= "strict-validator"  
  rest\_api\_id                 \= aws\_api\_gateway\_rest\_api.api.id  
  validate\_request\_body       \= true \# PASS: Das Gateway erzwingt die Schema-Prüfung.  
  validate\_request\_parameters \= true  
}

*OpenAPI (Compliant):*

YAML  
UserPayload:  
  type: object  
  additionalProperties: false \# PASS: API blockiert injizierte PII sofort.  
  properties:  
    id:  
      type: string

### **Regel 2: DSGVO Art. 32 – Belastbarkeit der Infrastruktur (API Gateway Throttling)**

**Rechtliche & Methodische Basis:** Art. 32 Abs. 1 lit. b DSGVO verlangt die Fähigkeit, die Verfügbarkeit und Belastbarkeit der Systeme auf Dauer sicherzustellen1. Serverless-Architekturen ohne Throttle-Limits können durch fehlerhafte Clients oder böswillige Überlastungsangriffe die Backend-Ressourcen (Lambda-Concurrency, DynamoDB RCU/WCU) erschöpfen, was den Dienstsausfall (Verfügbarkeitsverlust) für legitime Anfragen bedingt.  
**Prüflogik:** Die Audit-Engine durchläuft den Abstrakten Syntaxbaum (AST) des Terraform-Codes und sucht nach Blöcken des Typs aws\_api\_gateway\_method\_settings oder aws\_apigatewayv2\_stage. Sie prüft, ob die Parameter throttling\_rate\_limit und throttling\_burst\_limit deklariert sind und Werte größer als 0 aufweisen20.  
**Violation Pattern (FAIL):** Das API-Gateway wird ohne konfigurierte Schutzmechanismen (Rate Limiting) in die Produktion überführt.

Terraform  
resource "aws\_api\_gateway\_method\_settings" "violation\_settings" {  
  rest\_api\_id \= aws\_api\_gateway\_rest\_api.api.id  
  stage\_name  \= aws\_api\_gateway\_stage.prod.stage\_name  
  method\_path \= "\*/\*"

  settings {  
    metrics\_enabled \= true  
    \# FAIL: throttling\_rate\_limit und throttling\_burst\_limit fehlen.  
    \# Die API ist völlig ungeschützt gegen Request Flooding.  
  }  
}

**Compliant Pattern (PASS):** Es existiert eine explizite Definition der Belastbarkeitsgrenzen, die den Token-Bucket-Algorithmus von AWS aktivieren20.

Terraform  
resource "aws\_api\_gateway\_method\_settings" "compliant\_settings" {  
  rest\_api\_id \= aws\_api\_gateway\_rest\_api.api.id  
  stage\_name  \= aws\_api\_gateway\_stage.prod.stage\_name  
  method\_path \= "\*/\*"

  settings {  
    metrics\_enabled        \= true  
    throttling\_rate\_limit  \= 1000  \# PASS: Maximale Requests pro Sekunde definiert.  
    throttling\_burst\_limit \= 500   \# PASS: Maximale Burst-Rate definiert.  
  }  
}

### **Regel 3: SDM Protokollieren & Art. 32 – Verschlüsselte und fristgebundene Logs**

**Rechtliche & Methodische Basis:** Nach Art. 5 Abs. 2 DSGVO muss der Verantwortliche die Einhaltung der Verordnung nachweisen können (Rechenschaftspflicht)1. Hierzu bedarf es Systemprotokollen (Logs). Das SDM konkretisiert dies im Baustein 43 "Protokollieren" und verlangt, dass Logs geschützt (Vertraulichkeit/Integrität) und zeitlich begrenzt (Datenminimierung) werden21. Die zeitlich unbegrenzte Speicherung von CloudWatch-Logs im Klartext stellt einen massiven Verstoß gegen die Speicherbegrenzung dar1.  
**Prüflogik:** Die Audit-Engine iteriert über alle aws\_cloudwatch\_log\_group Ressourcen. Sie verifiziert, dass:

> 1. Das Argument kms\_key\_id vorhanden ist, welches auf einen Customer Managed Key verweist, um die Vertraulichkeit abzusichern22.  
> 2. Das Argument retention\_in\_days gesetzt ist. Der Wert darf nicht 0 sein (was endlose Speicherung bedeutet) und muss einem genehmigten Zeitraum (z. B. 30, 90 oder 365 Tage) entsprechen22.

**Violation Pattern (FAIL):** Die Log-Gruppe verlässt sich auf die AWS-Standardwerte (kein CMK, unendliche Speicherung).

Terraform  
resource "aws\_cloudwatch\_log\_group" "violation\_logs" {  
  name \= "/aws/lambda/user-service"  
  \# FAIL: retention\_in\_days fehlt (Default: Speicherung für immer)  
  \# FAIL: kms\_key\_id fehlt (Verletzung der Verschlüsselungskontrolle)  
}

**Compliant Pattern (PASS):** Lebensdauer und Verschlüsselung sind durch Terraform hart kodiert22.

Terraform  
resource "aws\_cloudwatch\_log\_group" "compliant\_logs" {  
  name              \= "/aws/lambda/user-service"  
  retention\_in\_days \= 30 \# PASS: Automatische Löschung nach 30 Tagen zur Datenminimierung  
  kms\_key\_id        \= aws\_kms\_key.cloudwatch\_kms\_key.arn \# PASS: Strenge Vertraulichkeit  
}

### **Regel 4: DSGVO Art. 44 – Geofencing auf Control-Plane-Ebene (Drittlandtransfer)**

**Rechtliche & Methodische Basis:** Zur Unterbindung von illegalen Drittlandtransfers gemäß Art. 44 DSGVO genügt es nicht, Entwicklern Richtlinien an die Hand zu geben1. Es bedarf einer Service Control Policy (SCP) auf der Ebene von AWS Organizations. SCPs fungieren als absolut überschreibendes Regulativ, das auch den mächtigsten Cloud-Administratoren untersagt, Operationen außerhalb zugelassener EU-Regionen auszuführen25.  
**Prüflogik:** Die Audit-Engine sucht nach aws\_organizations\_policy Ressourcen vom type \= "SERVICE\_CONTROL\_POLICY"25. Sie untersucht das in content injizierte JSON auf ein Statement, welches den Effect \= "Deny" trägt und in der Condition die AWS-Variable aws:RequestedRegion so filtert, dass sie alle Regionen außer der genehmigten (z.B. eu-central-1) betrifft25.  
**Violation Pattern (FAIL):** Es fehlen explizite Region-Deny-SCPs im IaC-Repository der Organisation, oder die SCP ist fehlerhaft konfiguriert (z.B. indem sie auf Allow statt Deny basiert, da SCPs im Whitelist-Modell schwer administrierbar sind und durch das Fehlen eines Deny ein Schlupfloch lassen)25. *(Das Fehlen des nachfolgenden Compliant-Patterns im Control-Tower-Code führt zum Audit-Fail).*  
**Compliant Pattern (PASS):** Die SCP erzwingt den Betrieb in Frankfurt (eu-central-1) und schließt nur globale Identitäts- und Routing-Services aus25.

Terraform  
resource "aws\_organizations\_policy" "eu\_central\_only" {  
  name        \= "restrict-regions-to-frankfurt"  
  description \= "Blockt alle Operationen ausserhalb von eu-central-1 gemaess Art. 44 DSGVO"  
  type        \= "SERVICE\_CONTROL\_POLICY"

  content \= jsonencode({  
    Version \= "2012-10-17"  
    Statement \= \[  
      {  
        Sid    \= "DenyNonEuRegions"  
        Effect \= "Deny"  
        \# Notwendige Ausnahme für globale AWS-Dienste  
        NotAction \= \[  
          "iam:\*",  
          "organizations:\*",  
          "route53:\*",  
          "cloudfront:\*"  
        \]  
        Resource \= "\*"  
        Condition \= {  
          StringNotEquals \= {  
            "aws:RequestedRegion" \= \[  
              "eu-central-1" \# PASS: Hard-Limit auf die EU-Region  
            \]  
          }  
        }  
      }  
    \]  
  })  
}

Die Synthese aus juristischer Vorgabe (DSGVO), methodischem Handlungsleitfaden (SDM V3.1a) und präziser Code-Validierung (Terraform/OpenAPI) garantiert, dass Datenschutz nicht länger ein theoretisches Audit-Konstrukt ist, sondern als kompilierbarer Infrastrukturzustand etabliert wird. Compliance-Audit-Engines transformieren die Verordnung in einen deterministischen Gatekeeper, der Rechtsbrüche durch Fehlkonfigurationen in AWS Serverless-Umgebungen proaktiv und zuverlässig verhindert.

#### **Works cited**

> 1. dsgvo.pdf  
> 2. SDM-Methode-V31a.pdf  
> 3. Describing Request Body | Swagger Docs, [https\://swagger.io/docs/specification/v3\_0/describing-request-body/describing-request-body/](https://swagger.io/docs/specification/v3_0/describing-request-body/describing-request-body/)  
> 4. explicit guidance on additionalProperties in request body schemas, [https\://github.com/camaraproject/Commonalities/issues/632](https://github.com/camaraproject/Commonalities/issues/632)  
> 5. OpenAPI Errors Cheat Sheet \- ApiNotes, [https\://apinotes.io/cheatsheet/openapi-errors](https://apinotes.io/cheatsheet/openapi-errors)  
> 6. aws\_api\_gateway\_request\_valid, [https\://registry.terraform.io/providers/hashicorp/awS/latest/docs/resources/api\_gateway\_request\_validator](https://registry.terraform.io/providers/hashicorp/awS/latest/docs/resources/api_gateway_request_validator)  
> 7. aws\_dynamodb\_table | Resources | hashicorp/aws | Terraform, [https\://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb\_table](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table)  
> 8. SDM-V2.0\_Löschen\_und\_Vernichten\_V1.0a.pdf  
> 9. SDM-V2.0\_Trennen\_V1.0.pdf  
> 10. aws\_kms\_key | Resources | hashicorp/aws \- Terraform Registry, [https\://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms\_key](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key)  
> 11. aws\_kms\_key\_policy | Resources | hashicorp/aws \- Terraform Registry, [https\://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms\_key\_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key_policy)  
> 12. AWS Database Encryption SDK concepts, [https\://docs.aws.amazon.com/database-encryption-sdk/latest/devguide/concepts.html](https://docs.aws.amazon.com/database-encryption-sdk/latest/devguide/concepts.html)  
> 13. AWS Database Encryption SDK for DynamoDB, [https\://docs.aws.amazon.com/database-encryption-sdk/latest/devguide/dynamodb-encryption-client.html](https://docs.aws.amazon.com/database-encryption-sdk/latest/devguide/dynamodb-encryption-client.html)  
> 14. How the AWS Database Encryption SDK works, [https\://docs.aws.amazon.com/database-encryption-sdk/latest/devguide/how-it-works.html](https://docs.aws.amazon.com/database-encryption-sdk/latest/devguide/how-it-works.html)  
> 15. Which fields are encrypted and signed? \- AWS Documentation, [https\://docs.aws.amazon.com/database-encryption-sdk/latest/devguide/DDB-encrypted-and-signed.html](https://docs.aws.amazon.com/database-encryption-sdk/latest/devguide/DDB-encrypted-and-signed.html)  
> 16. AWS KMS Terraform module \- GitHub, [https\://github.com/terraform-aws-modules/terraform-aws-kms](https://github.com/terraform-aws-modules/terraform-aws-kms)  
> 17. aws\_api\_gateway\_rest\_api | Resources | hashicorp/aws | Terraform, [https\://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api\_gateway\_rest\_api](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/api_gateway_rest_api)  
> 18. aws\_apigatewayv2\_domain\_na, [https\://github.com/hashicorp/terraform-provider-aws/issues/46611](https://github.com/hashicorp/terraform-provider-aws/issues/46611)  
> 19. Infrastructure security in Amazon API Gateway \- AWS Documentation, [https\://docs.aws.amazon.com/apigateway/latest/developerguide/infrastructure-security.html](https://docs.aws.amazon.com/apigateway/latest/developerguide/infrastructure-security.html)  
> 20. aws\_apigatewayv2\_stage | Resources | hashicorp/aws | Terraform, [https\://registry.terraform.io/providers/hashicorp/awS/latest/docs/resources/apigatewayv2\_stage](https://registry.terraform.io/providers/hashicorp/awS/latest/docs/resources/apigatewayv2_stage)  
> 21. SDM-V3.1\_Protokollieren\_V2.0.pdf  
> 22. aws\_cloudwatch\_log\_group | Resources | hashicorp/aws | Terraform, [https\://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch\_log\_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group)  
> 23. What the CLOUD Act Really Means for EU Data Sovereignty \- Wire, [https\://wire.com/en/blog/cloud-act-eu-data-sovereignty](https://wire.com/en/blog/cloud-act-eu-data-sovereignty)  
> 24. Deny access to AWS based on the requested AWS Region, [https\://docs.aws.amazon.com/controltower/latest/controlreference/primary-region-deny-policy.html](https://docs.aws.amazon.com/controltower/latest/controlreference/primary-region-deny-policy.html)  
> 25. How to Create SCPs (Service Control Policies) in Terraform, [https\://oneuptime.com/blog/post/2026-02-23-how-to-create-scps-service-control-policies-in-terraform/view](https://oneuptime.com/blog/post/2026-02-23-how-to-create-scps-service-control-policies-in-terraform/view)  
> 26. Modify SCP to enable AWS Config in restricted AWS regions, [https\://repost.aws/questions/QUdFhqKssUSDysi2vSUL5e\_g/modify-scp-to-enable-aws-config-in-restricted-aws-regions](https://repost.aws/questions/QUdFhqKssUSDysi2vSUL5e_g/modify-scp-to-enable-aws-config-in-restricted-aws-regions)  
> 27. Restrict Access to AWS Based on the Requested Region (Disable, [https\://asecure.cloud/a/scp\_whitelist\_region/](https://asecure.cloud/a/scp_whitelist_region/)  
> 28. aws\_cloudwatch\_log\_group | Data Sources | hashicorp/aws, [https\://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/cloudwatch\_log\_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/cloudwatch_log_group)  
> 29. Understanding AWS CloudWatch Log Group Retention Periods, [https\://medium.com/pareture/aws-cloudwatch-log-group-retention-periods-bb8a2fb9c358](https://medium.com/pareture/aws-cloudwatch-log-group-retention-periods-bb8a2fb9c358)  
> 30. Using Terraform With AWS Service Control Policies (SCPs) \- Firefly AI, [https\://www\.firefly.ai/academy/using-terraform-with-aws-service-control-policies-for-cloud-governance](https://www.firefly.ai/academy/using-terraform-with-aws-service-control-policies-for-cloud-governance)  
> 31. aws\_organizations\_policy | Resources | hashicorp/aws | Terraform, [https\://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations\_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/organizations_policy)