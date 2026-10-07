# **Technischer Forschungsbericht: Automatisierte Shift-Left-Compliance-Engine für AWS Serverless-Architekturen**

## **Einleitung und sicherheitsarchitektonischer Kontext**

Die fortwährende Evolution des Cloud-Computings hin zu nativen Serverless-Architekturen wie AWS Lambda, Amazon API Gateway, Amazon DynamoDB und Amazon Aurora Serverless hat die traditionellen Sicherheits- und Compliance-Paradigmen tiefgreifend transformiert. In einer vollständig abstrahierten Infrastruktur, in der Cloud-Service-Kunden (Cloud Service Customers, CSCs) keinen administrativen Zugriff mehr auf das zugrunde liegende Betriebssystem (OS) oder die physische Netzwerkschicht haben, verschiebt sich der Fokus der Sicherheitsverantwortung im Rahmen des Shared Security Responsibility Models (SSRM) dramatisch1. Die klassische, perimeterbasierte Netzwerksicherheit weicht einer streng identitätsbasierten Sicherheitsarchitektur, in der Identity & Access Management (IAM) als neuer Perimeter fungiert. In diesem Kontext stellen Fehlkonfigurationen in IAM-Richtlinien, fehlerhafte Datenspeicherungs-Parameter und unzureichende Audit-Protokollierungen die primären Angriffsvektoren dar4.  
Um dieser veränderten Bedrohungslandschaft proaktiv zu begegnen, ist die Implementierung des sogenannten "Shift-Left"-Paradigmas unerlässlich. Dieser Ansatz integriert Sicherheits- und Compliance-Prüfungen so früh wie möglich in den Software Development Life Cycle (SDLC)6. Anstatt Cloud-Infrastruktur erst nach der Bereitstellung reaktiv durch Cloud Security Posture Management (CSPM) zu scannen, werden Infrastructure-as-Code (IaC)-Definitionen wie Terraform, AWS CloudFormation oder AWS CDK bereits in der CI/CD-Pipeline analysiert9. Eine automatisierte Compliance-Engine, die auf deterministischen Regeln basiert, verhindert durch einen sogenannten "Hard Fail" die Bereitstellung von nicht-konformen Ressourcen und reduziert somit das Risiko von Datenlecks, Privilege Escalation oder unbefugten Zugriffen auf ein absolutes Minimum4.  
Dieser Forschungsbericht analysiert die architektonische Integration des "CIS AWS Foundations Benchmark" und der "CSA Cloud Controls Matrix (CCM v4)" zur Entwicklung einer solchen automatisierten Audit-Engine. Das primäre Ziel besteht darin, hochgradig technische Konfigurationsvorgaben in abstrakte Compliance-Anforderungen zu übersetzen und übergeordnete rechtliche Frameworks wie die ISO/IEC 27001:2022 oder den BSI C5-Katalog nahtlos an deterministische IaC-Parameter zu binden. Die resultierende Engine befähigt Organisationen, Sicherheit nicht als reaktives Nachbessern, sondern als unverrückbares, programmatisches Fundament in das Engineering zu integrieren.

## **Paradigmenwechsel der statischen Code-Analyse im Shift-Left-Ansatz**

Die technische Grundlage einer Shift-Left-Compliance-Engine bildet die statische Code-Analyse (Static Application Security Testing, SAST) von Infrastructure-as-Code (IaC). Werkzeuge wie Checkov, tfsec (nun integriert in Trivy), Terrascan und der Open Policy Agent (OPA) mit seiner Abfragesprache Rego ermöglichen es, textbasierte Infrastrukturdefinitionen in maschinenlesbare Abstract Syntax Trees (AST) oder komplexe Graphenmodelle zu transformieren, bevor auch nur eine einzige Cloud-Ressource instanziiert wird9.  
Checkov, entwickelt von Bridgecrew, zeichnet sich durch seine graphenbasierte Analyse aus, die nicht nur isolierte Ressourcenblöcke bewertet, sondern die kontextuellen Beziehungen zwischen AWS-Komponenten versteht9. Dies ist in Serverless-Umgebungen entscheidend, um beispielsweise zu verifizieren, ob eine AWS Lambda-Funktion über eine zugehörige IAM-Rolle verfügt, die wiederum an eine restriktive Richtlinie gebunden ist. Tfsec und Trivy bieten hingegen eine extrem schnelle Analyse, die tief in die HashiCorp Configuration Language (HCL) integriert ist und sofortiges Feedback in der Pipeline liefert10. Für hochgradig angepasste und komplexe Compliance-Anforderungen etabliert sich der Open Policy Agent (OPA) mit Rego, welcher es ermöglicht, Richtlinien als Code (Policy-as-Code) zu definieren und IaC-JSON-Artefakte gegen diese Richtlinien zu evaluieren12.  
Ein zentrales Problem bei der Implementierung dieser Scanner in CI/CD-Pipelines ist das Aufkommen von False Positives (Fehlalarmen). Eine Engine, die Entwickler mit Tausenden von irrelevanten Warnungen überflutet, führt unweigerlich zu Alarmmüdigkeit und zur Deaktivierung der Sicherheitsprüfungen6. Daher ist der Übergang von einem weichen Warnsystem ("Soft Fail") zu einem rigorosen Blockierungsmechanismus ("Hard Fail") nur bei hochgradig deterministischen, ausnahmslos zutreffenden Sicherheitsregeln ratsam7. Die in diesem Bericht entwickelte Engine nutzt daher exakt definierte, binäre Parameter (z. B. das zwingende Vorhandensein eines Blockierungs-Flags für öffentliche S3-Buckets), um fehlerfreie und auditierbare Hard-Fails zu garantieren.

## **Filterung und Serverless-Fokus des CIS AWS Foundations Benchmark**

Der CIS AWS Foundations Benchmark bietet eine detaillierte, präskriptive Anleitung zur sicheren Konfiguration von AWS-Diensten und wird durch den Konsens von Cybersicherheitsexperten weltweit gepflegt19. Da dieser Benchmark jedoch historisch aus der Absicherung traditioneller Rechenzentren und virtueller Maschinen gewachsen ist, enthält er zahlreiche Kontrollen, die für moderne, ereignisgesteuerte Serverless-Architekturen technisch irrelevant sind. Um eine effiziente Audit-Engine zu entwerfen, muss der Benchmark rigoros gefiltert werden.

### **Exklusionskriterien für EC2 und klassische Netzwerke**

Für die Entwicklung der serverless-spezifischen Shift-Left-Compliance-Engine werden alle CIS-Regeln, die sich auf klassische Elastic Compute Cloud (EC2)-Instanzen, temporäre Compute-Ressourcen, Host-basierte Firewalls oder netzwerkbasierte Betriebssystemzugänge beziehen, ignoriert. In einer Architektur, die ausschließlich auf verwalteten Diensten wie Lambda, API Gateway und S3 basiert, entfällt die Notwendigkeit zur Absicherung von Betriebssystemebenen.  
Dies betrifft insbesondere die gesamte CIS Sektion 6 (Networking). Kontrollen wie die Regel 6.1.2 zur Restriktion von CIFS-Zugriffen, die Regeln 6.2 und 6.3 zur Unterbindung von SSH (Port 22\) und RDP (Port 3389\) Ingress-Regeln aus dem öffentlichen Internet (0.0.0.0/0), die Regel 6.4 zur IPv6-Remote-Administration und die Regel 6.7 zur zwingenden Nutzung von IMDSv2 auf EC2-Instanzen sind für Serverless-Komponenten nicht applizierbar19. Da Serverless-Dienste überdies nativ über IAM-Autorisierung und AWS-Backbone-Routing (wie VPC Endpoints) interagieren, werden auch OS-Level-Routingtabellen (CIS 6.6) in diesem spezifischen Fokus nicht priorisiert19.

### **Extraktion und deterministische Transformation der Kernregeln**

Nach der methodischen Filterung verbleiben die kritischen Kernbereiche des CIS Benchmarks, die für den sicheren Betrieb von Serverless-Workloads unabdingbar sind. Diese umfassen Identity & Access Management (Sektion 2), Storage (Sektion 3.1), verwaltete Datenbanken (Sektion 3.2) und Logging/Monitoring (Sektion 4\)19. Diese normativen Vorgaben müssen präzise in deterministische Cloud-Infrastruktur-Parameter übersetzt werden, um von IaC-Scannern verarbeitet werden zu können.  
Die folgende Analyse transformiert die wichtigsten CIS-Regeln in evaluierbare Terraform-Strukturen, die als Grundlage für die "Hard Fail"-Auslöser in der CI/CD-Pipeline dienen.

| CIS ID | AWS Service & Domäne | CIS Kontroll-Spezifikation (Auszug) | Serverless Relevanz & Risiko | Terraform IaC Determinismus (Hard Fail Trigger) |
| :---- | :---- | :---- | :---- | :---- |
| **2.14** | IAM (Identity & Access) | Ensure IAM policies that allow full "*:*" administrative privileges are not attached | Verhindert, dass kompromittierte Lambda-Funktionen durch übermäßige Privilegien (Blast Radius) die gesamte Cloud-Umgebung übernehmen können15. | aws\_iam\_policy / aws\_iam\_role\_policy: Das JSON statement darf nicht Effect="Allow", Action="\*" und Resource="\*" kombinieren. |
| **2.21** | IAM (Resource Policies) | Ensure AWS resource policies do not allow unrestricted access using "Principal": "\*" | Blockiert den unauthentifizierten, anonymen Zugriff auf API Gateways, SQS-Queues oder EventBridge-Busse, was Denial-of-Wallet-Angriffe verhindert21. | Ressourcenrichtlinien dürfen das Feld Principal: "\*" nicht ohne restriktive Condition (z. B. aws:SourceArn) enthalten. |
| **3.1.4** | S3 (Storage) | Ensure that S3 is configured with 'Block Public Access' enabled | Schließt die häufigste Ursache für massive Datenexfiltrationen aus Cloud-Speichern aus21. | Jede aws\_s3\_bucket Ressource muss zwingend mit aws\_s3\_bucket\_public\_access\_block verknüpft sein, wobei alle vier Block-Parameter auf true stehen23. |
| **3.1.1** | S3 (Storage) | Ensure S3 Bucket Policy is set to deny HTTP requests | Erzwingt TLS-Verschlüsselung bei der Übertragung, um Man-in-the-Middle-Angriffe auf den Datentransfer zu unterbinden21. | Die Bucket-Policy muss ein Deny-Statement für alle Aktionen enthalten, falls die Bedingung aws:SecureTransport \== "false" zutrifft. |
| **3.2.1** | RDS / Aurora (Database) | Ensure that encryption-at-rest is enabled for RDS instances | Schützt persistente Geschäftsdaten vor unbefugtem Zugriff auf die zugrunde liegenden Speichermedien oder Backups (Snapshots)15. | Die Parameter storage\_encrypted in aws\_rds\_cluster oder aws\_db\_instance müssen zwingend auf true gesetzt sein. |
| **3.2.3** | RDS / Aurora (Database) | Ensure that RDS instances are not publicly accessible | Verhindert direkte Netzwerkangriffe auf Datenbank-Endpunkte aus dem öffentlichen Internet15. | Der Parameter publicly\_accessible muss explizit auf false gesetzt sein. |
| **4.1** | CloudTrail (Logging) | Ensure CloudTrail is enabled in all regions | Die API-Ebene ist die einzige Quelle der Wahrheit für Auditing und Forensik in Serverless-Umgebungen; ohne sie ist keine forensische Analyse möglich21. | Eine aws\_cloudtrail Ressource muss definiert sein, und der Parameter is\_multi\_region\_trail muss auf true gesetzt sein. |
| **4.5** | CloudTrail (Logging) | Ensure CloudTrail logs are encrypted at rest using KMS CMKs | Verhindert die nachträgliche Manipulation von Audit-Logs durch interne oder externe Angreifer21. | Der Parameter kms\_key\_id muss in der aws\_cloudtrail Ressource mit einem gültigen Customer Managed Key (CMK) belegt sein. |

Die Extraktion dieser Parameter bildet das technische Fundament. Um diese Parameter jedoch in einen regulatorischen Kontext zu setzen, bedarf es einer Vermittlungsschicht, die maschinenlesbaren Code in juristische und prozessuale Normen übersetzt.

## **Die CSA Cloud Controls Matrix als Taxonomie und Join-Schlüssel**

Während der CIS AWS Foundations Benchmark tief technischer Natur ist und exakte API-Einstellungen vorgibt, fordern Auditoren, Risikomanager und Regulierungsbehörden meist den Nachweis der Einhaltung generischer, rechtlicher und risikobasierter Standards. Hierzu zählen beispielsweise die internationale Norm ISO/IEC 27001:2022, der BSI Cloud Computing Compliance Criteria Catalogue (C5) in Deutschland oder branchenspezifische Frameworks wie TISAX oder DORA2. Die direkte, unkommentierte Übersetzung eines Terraform-Parameters (wie storage\_encrypted \= true) in ein juristisches Risiko ist ohne ein methodisches Bindeglied fehleranfällig und für Auditoren kaum nachvollziehbar.  
Hier fungiert die CSA Cloud Controls Matrix (CCM v4) als abstrakter "Join-Schlüssel" (Anchor Key). Die CCM v4 ist ein branchenübergreifender De-facto-Sicherheitsstandard, der aus 197 detaillierten Kontrollzielen besteht, die strukturiert in 17 Domänen unterteilt sind (darunter Data Security & Privacy, Cryptography, Identity & Access Management und Logging)21.

### **Mechanik der abstrakten Verknüpfung**

Die Architektur der Compliance-Engine verknüpft die granularen technischen Prüfungen mit den hochrangigen rechtlichen Frameworks durch eine relationale und bidirektionale Taxonomie. Der Workflow in der Shift-Left-Engine entfaltet sich in einer präzisen Kausalkette:  
Zunächst analysiert die IaC-Scanner-Ebene den Code. Ein Scanner wie Checkov oder eine strukturierte OPA-Rego-Regel evaluiert einen Terraform-Plan und erkennt, dass ein S3-Bucket ohne den verpflichtenden Block aws\_s3\_bucket\_public\_access\_block bereitgestellt werden soll10. In der zweiten Phase, der Benchmark-Ebene, ordnet der Scanner diese fehlende Konfiguration einem spezifischen technischen Verstoß zu und meldet eine Verletzung gegen die CIS Benchmark Regel 3.1.421.  
An diesem Punkt greift die abstrakte Ebene der CSA CCM v4. Die Engine nutzt ein integriertes Mapping-Modul, welches CIS 3.1.4 auf die CCM-Kontrolle DSP-17 (Data Security & Privacy Lifecycle Management) abbildet. DSP-17 fordert abstrakt, dass Daten durch technische Maßnahmen geschützt werden müssen, um unbefugte Offenlegungen zu verhindern27. In der vierten und letzten Phase, der Framework-Ebene, referenziert das CCM-Mapping, dass DSP-17 direkt auf die Anforderungen der ISO/IEC 27001:2022, spezifisch auf die Annex A Kontrollen A.8.24 (Use of Cryptography) und A.5.18, sowie auf entsprechende BSI C5 Kriterien mappt29.  
Durch diese relationale Join-Logik generiert die CI/CD-Pipeline nicht nur eine für Entwickler leicht verständliche, rein technische Fehlermeldung zur Behebung des Problems, sondern liefert den Compliance- und GRC-Verantwortlichen (Governance, Risk, and Compliance) gleichzeitig den exakten, metrischen Beweis, dass das Unternehmen kontinuierlich gegen die Anforderungen der ISO 27001 arbeitet. Die CCM fungiert somit als das linguistische und regulatorische Scharnier zwischen Code-Commit und Compliance-Audit.

### **Domänenanalyse: Data Security and Privacy (DSP)**

Die DSP-Domäne der CCM v4 umfasst den gesamten Lebenszyklus von Daten, beginnend bei der Erstellung über die Speicherung und Übertragung bis hin zur sicheren und nachvollziehbaren Löschung27. Die Vorgaben dieser Domäne sind stark an globalen Datenschutzgesetzen orientiert und dienen als Basis für den Schutz sensibler Informationen in der Cloud.  
Die Kontrolle **DSP-17 (Data Protection)** spezifiziert, dass Cloud-Service-Kunden (CSCs) und Cloud-Service-Provider (CSPs) gemeinsam technische und organisatorische Maßnahmen ergreifen müssen, um Daten vor unbefugtem Zugriff zu schützen27. Wie zuvor erläutert, wird diese abstrakte Vorgabe in der AWS-Serverless-Welt direkt durch die **CIS 3.1.4** Regel für S3 Block Public Access operationalisiert21. Ein Verstoß auf der IaC-Ebene bedeutet eine unmittelbare Nichtkonformität mit DSP-17 und konsekutiv mit **ISO/IEC 27001:2022 A.8.24** und **NIST SP 800-53 SC-28**28.  
Ein weiteres Beispiel ist die Kontrolle **DSP-05 (Data Retention & Disposal)**, die die Implementierung von Richtlinien und technischen Maßnahmen zur sicheren Datenaufbewahrung und Datenlöschung fordert28. Innerhalb der AWS-Infrastruktur spiegelt sich dies in der **CIS 3.1.3** Regel wider, welche verlangt, dass alle Daten in Amazon S3 klassifiziert und gesichert werden21. Über die Taxonomie der CCM mappt DSP-05 direkt auf **ISO/IEC 27001:2022 A.8.10** (Information Deletion), wodurch sichergestellt wird, dass technische Lifecycle-Policies in S3-Buckets rechtlich als konforme Datenlöschkonzepte anerkannt werden29.

### **Domänenanalyse: Cryptography, Encryption and Key Management (CEK)**

Die CEK-Domäne adressiert den unabdingbaren Einsatz von Kryptografie, die Stärke der verwendeten Algorithmen sowie die sichere Verwaltung von kryptografischen Schlüsseln im gesamten Cloud-Ökosystem28. In Serverless-Architekturen, bei denen Daten ständig zwischen flüchtigen Compute-Instanzen und persistenten Speichern fließen, ist diese Domäne von höchster Kritikalität.  
Die Kontrolle **CEK-03 (Data Encryption)** schreibt vor, dass Mechanismen zur Datenverschlüsselung im Ruhezustand (Encryption at Rest) und während der Übertragung (Encryption in Transit) implementiert werden müssen, um Datenlecks bei kompromittierten Speichermedien oder abgefangenem Netzwerkverkehr zu verhindern28. In der technischen Umsetzung der Shift-Left-Engine wird CEK-03 durch die **CIS 3.2.1** Regel (RDS / Aurora Encryption at Rest) sowie die **CIS 4.5** Regel (CloudTrail Logs encrypted with KMS CMKs) durchgesetzt21. Über die CCM als Anchor Key beweist die Einhaltung dieser Terraform-Parameter automatisch die Konformität mit **ISO/IEC 27001:2022 Annex A.8.24** (Use of Cryptography) und den korrespondierenden Kriterien des BSI IT-Grundschutz-Kompendiums29.  
Zusätzlich fordert die Kontrolle **CEK-08 (Key Management)**, dass Verschlüsselungsschlüssel sicher generiert, verwaltet und in definierten Intervallen rotiert werden28. Dies wird in der Audit-Engine durch die Überprüfung der **CIS 4.6** Regel (Ensure rotation for customer-created symmetric CMKs is enabled) sichergestellt21. Fehlt in einem Terraform-Artefakt für die Ressource aws\_kms\_key der Parameter enable\_key\_rotation \= true, schlägt die Engine fehl. Dieser deterministische Auslöser garantiert die fortwährende Einhaltung der Schlüssellebenszyklus-Vorgaben nach internationalen Standards.  
Die nachfolgende Tabelle visualisiert die durchgehende Verknüpfung von der maschinenlesbaren Terraform-Ressource bis zur internationalen Norm, moderiert durch die CSA CCM v4.

| Terraform IaC Ressource & Parameter | CIS AWS Foundation Benchmark | CSA CCM v4 (Anchor Key) | ISO/IEC 27001:2022 / BSI Mapping |
| :---- | :---- | :---- | :---- |
| aws\_iam\_policy / Action \!= "\*" | CIS 2.14 (IAM Least Privilege) | **IAM-07** (Privilege Management) | A.5.18 (Access rights), BSI ORP.4 |
| aws\_s3\_bucket\_public\_access\_block | CIS 3.1.4 (S3 Public Access) | **DSP-17** (Data Protection) | A.8.24 (Data protection), BSI CON.2 |
| aws\_rds\_cluster / storage\_encrypted=true | CIS 3.2.1 (RDS Encryption) | **CEK-03** (Data Encryption) | A.8.24 (Cryptography), BSI SYS.1.1 |
| aws\_kms\_key / enable\_key\_rotation=true | CIS 4.6 (KMS Key Rotation) | **CEK-08** (Key Management) | A.8.24 (Key Lifecycle), BSI CON.1 |

## **Synthese und Architektur der Audit-Engine**

Um die theoretische Architektur in eine operative Lösung zu überführen, müssen die CIS-Prüfungen, die CCM-Taxonomie und die Determinismus-Auslöser strukturiert und maschinenlesbar abgebildet werden. Diese Abstraktion erfolgt in der Regel durch Konfigurationsdateien, die von Policy-Engines wie OPA (mit Rego) oder Scannern wie Checkov in der CI/CD-Pipeline geladen werden10.  
Die folgenden drei detaillierten Daten-Chunks im JSON-Format definieren das Herzstück der Engine. Sie verknüpfen die Identifikatoren der CCM und des CIS Benchmarks (als technical\_ground\_truth) mit den exakten, deterministischen IaC-Bedingungen (deterministic\_triggers), die zu einem sofortigen Abbruch der Bereitstellung ("Hard Fail") führen.

### **JSON-Datenblock: Identity and Access Management**

Dieser Block evaluiert die Einhaltung des Least-Privilege-Prinzips, indem er administrative Wildcards rigoros blockiert. Dies ist bei der Zuweisung von Execution Roles für AWS Lambda elementar, um das Risiko einer Privilege Escalation zu minimieren15.

JSON  
{  
  "chunk\_id": "eng\_rule\_iam\_001\_no\_admin\_wildcard",  
  "ccm\_id": "IAM-07",  
  "domain": "Identity and Access Management",  
  "description": "Prueft, ob IAM-Policies das Zuweisen von uneingeschraenkten Administrator-Rechten erlauben, um Privilege Escalation in Serverless-Funktionen zu verhindern.",  
  "technical\_ground\_truth": {  
    "cis\_aws\_benchmark\_parameter": "CIS 2.14",  
    "cis\_title": "Ensure IAM policies that allow full '\*:\*' administrative privileges are not attached",  
    "compliant\_criteria": "Die IAM Policy enthaelt keine Statements, bei denen Effect='Allow' und gleichzeitig Action='\*' und Resource='\*' gesetzt sind.",  
    "violation\_criteria": "Die IAM Policy enthaelt ein explizites Statement mit Effect='Allow', bei dem Action='\*' und Resource='\*' definiert sind. Dies ermoeglicht einen maximalen Blast Radius bei Kompromittierung."  
  },  
  "deterministic\_triggers": \[  
    {  
      "trigger\_type": "terraform\_resource\_parameter",  
      "target\_resource": "aws\_iam\_policy",  
      "forbidden\_parameter\_combination": {  
        "statement.effect": "Allow",  
        "statement.action": \["\*"\],  
        "statement.resource": \["\*"\]  
      },  
      "action": "HARD\_FAIL"  
    },  
    {  
      "trigger\_type": "terraform\_resource\_parameter",  
      "target\_resource": "aws\_iam\_role\_policy",  
      "forbidden\_parameter\_combination": {  
        "statement.effect": "Allow",  
        "statement.action": \["\*"\],  
        "statement.resource": \["\*"\]  
      },  
      "action": "HARD\_FAIL"  
    }  
  \]  
}

### **JSON-Datenblock: Storage Security**

Dieser Block sichert Serverless-Speichersysteme gegen unbefugte externe Zugriffe ab und verknüpft diese fundamentale AWS-Sicherheitsanforderung direkt mit der CCM-Vorgabe für den Datenschutz und die Vermeidung von Datenlecks21.

JSON  
{  
  "chunk\_id": "eng\_rule\_s3\_002\_block\_public\_access",  
  "ccm\_id": "DSP-17",  
  "domain": "Data Security & Privacy Lifecycle Management",  
  "description": "Stellt sicher, dass Amazon S3 Buckets auf globaler Kontoebene vor oeffentlichem Zugriff geschuetzt sind, um die unbeabsichtigte Exfiltration von Daten zu unterbinden.",  
  "technical\_ground\_truth": {  
    "cis\_aws\_benchmark\_parameter": "CIS 3.1.4",  
    "cis\_title": "Ensure that S3 is configured with 'Block Public Access' enabled",  
    "compliant\_criteria": "Jeder deklarierte aws\_s3\_bucket weist zwingend eine syntaktisch verknuepfte aws\_s3\_bucket\_public\_access\_block Ressource auf, in der alle vier Block-Parameter auf 'true' gesetzt sind.",  
    "violation\_criteria": "Es existiert ein S3 Bucket ohne anhaengende Block Public Access Konfiguration in der IaC-Definition, oder mindestens einer der vier Restriktions-Parameter ist auf 'false' konfiguriert."  
  },  
  "deterministic\_triggers": \[  
    {  
      "trigger\_type": "terraform\_dependency\_check",  
      "target\_resource": "aws\_s3\_bucket",  
      "required\_associated\_resource": "aws\_s3\_bucket\_public\_access\_block",  
      "action": "HARD\_FAIL"  
    },  
    {  
      "trigger\_type": "terraform\_resource\_parameter",  
      "target\_resource": "aws\_s3\_bucket\_public\_access\_block",  
      "required\_parameters\_must\_be\_true": \[  
        "block\_public\_acls",  
        "block\_public\_policy",  
        "ignore\_public\_acls",  
        "restrict\_public\_buckets"  
      \],  
      "action": "HARD\_FAIL"  
    }  
  \]  
}

### **JSON-Datenblock: Database Cryptography**

Dieser Block gewährleistet die Verschlüsselung im Ruhezustand (Encryption at Rest) für serverlose Datenbanken und verknüpft diese technische Notwendigkeit mit den kryptografischen Rahmenbedingungen der CSA15.

JSON  
{  
  "chunk\_id": "eng\_rule\_rds\_003\_storage\_encryption",  
  "ccm\_id": "CEK-03",  
  "domain": "Cryptography, Encryption and Key Management",  
  "description": "Ueberprueft, ob relationale und serverlose Datenbanken im Ruhezustand verschluesselt sind, um den Schutz vor physischen oder block-level Datenzugriffen durch Dritte zu gewaehrleisten.",  
  "technical\_ground\_truth": {  
    "cis\_aws\_benchmark\_parameter": "CIS 3.2.1",  
    "cis\_title": "Ensure that encryption-at-rest is enabled for RDS instances",  
    "compliant\_criteria": "Die Parameter storage\_encrypted in aws\_rds\_cluster (z. B. fuer Aurora Serverless) oder aws\_db\_instance sind explizit auf 'true' gesetzt.",  
    "violation\_criteria": "Die Storage-Verschluesselung ist in der Infrastrukturdefinition entweder implizit (durch Fehlen des Parameters) oder explizit (durch den Wert 'false') deaktiviert."  
  },  
  "deterministic\_triggers": \[  
    {  
      "trigger\_type": "terraform\_resource\_parameter",  
      "target\_resource": "aws\_rds\_cluster",  
      "required\_parameters\_must\_be\_true": \[  
        "storage\_encrypted"  
      \],  
      "action": "HARD\_FAIL"  
    },  
    {  
      "trigger\_type": "terraform\_resource\_parameter",  
      "target\_resource": "aws\_db\_instance",  
      "required\_parameters\_must\_be\_true": \[  
        "storage\_encrypted"  
      \],  
      "action": "HARD\_FAIL"  
    }  
  \]  
}

## **Strategische Implikationen und Fazit**

Die Implementierung einer Shift-Left-Compliance-Engine für AWS Serverless-Architekturen erfordert einen grundlegenden Paradigmenwechsel in der Konzeption und Beurteilung von Cloud-Sicherheit. Wie die tiefgehende Analyse des CIS AWS Foundations Benchmarks gezeigt hat, müssen überholte Netzwerk- und Instanz-Checks, die für herkömmliche IaaS-Umgebungen (wie Amazon EC2) entworfen wurden, systematisch ausgeklammert werden. Nur so lässt sich der Fokus auf die tatsächlichen, kritischen Angriffsvektoren moderner Clouds richten: das Identity & Access Management (IAM), hochskalierbare Storage-Konfigurationen (S3), serverlose Datenbanken (Aurora) und lückenloses API-Auditing (CloudTrail).  
Die technologische Kernherausforderung für moderne Entwicklungs- und Sicherheitsteams besteht jedoch nicht allein im bloßen Identifizieren fehlerhafter Infrastrukturcodes. Vielmehr liegt die Schwierigkeit in der konsistenten, rechtssicheren und nachvollziehbaren Dokumentation dieser Prüfungen für interne und externe Audits. Die in diesem Forschungsbericht detailliert aufgeschlüsselte CSA Cloud Controls Matrix (CCM v4) erweist sich in diesem Spannungsfeld als der entscheidende technologische und organisatorische "Join-Schlüssel". Durch das methodische Mapping der präzisen, maschinenlesbaren technischen IaC-Parameter – evaluiert durch fortschrittliche AST-Analysen via Checkov oder OPA/Rego – über den CIS Benchmark hin zu abstrakten CCM-Kontrollen entsteht eine ununterbrochene Nachweiskette. Diese Chain of Custody belegt, dass eine Zeile Code in Terraform direkte Auswirkungen auf die Einhaltung internationaler Standards wie der ISO/IEC 27001:2022 (z. B. Annex A.8.24) oder des BSI C5-Katalogs hat.  
Durch den Einsatz der im JSON-Format spezifizierten deterministischen Triggermechanismen wird die CI/CD-Pipeline befähigt, Deployment-Fehler in Echtzeit durch einen "Hard Fail" zu stoppen. Dieser konsequente Ansatz eliminiert die für Entwickler frustrierenden False Positives, die bei heuristischen Scans häufig auftreten, und garantiert, dass Sicherheits- und Compliance-Vorgaben nicht als reaktives, teures Nachbessern, sondern als unverrückbares Architektur-Fundament in das Engineering integriert werden. Die resultierende Cloud-Infrastruktur ist damit nicht nur sicher durch Design (Security-by-Design), sondern nachweislich konform durch Code (Compliance-as-Code), was die Agilität von Software-Deployments erhöht und gleichzeitig die regulatorischen Risiken in Serverless-Umgebungen auf ein absolutes Minimum reduziert.

#### **Works cited**

> 1. CCM v4.1 Implementation Guidelines v2.1 20260120.pdf  
> 2. Introductory Guidance to CCM 20261006.pdf  
> 3. CCM v4.0 Implementation Guidelines v2.0 20240528 | PDF \- Scribd, [https\://www\.scribd.com/document/744617433/CCM-v4-0-Implementation-Guidelines-v2-0-20240528](https://www.scribd.com/document/744617433/CCM-v4-0-Implementation-Guidelines-v2-0-20240528)  
> 4. 100+ DevSecOps interview Questions and Answers (2026) \- WeCP, [https\://www\.wecreateproblems.com/interview-questions/devsecops-interview-questions](https://www.wecreateproblems.com/interview-questions/devsecops-interview-questions)  
> 5. Serverless AI Security: Attack Surface Analysis and Runtime ... \- arXiv, [https\://arxiv.org/pdf/2601.11664](https://arxiv.org/pdf/2601.11664)  
> 6. What Is Shift-Left Testing? A Complete Guide For Cloud Security, [https\://www\.wiz.io/academy/application-security/shift-left-testing](https://www.wiz.io/academy/application-security/shift-left-testing)  
> 7. Shift-Left Security: Reduce Vulnerability Costs, [https\://accuknox.com/blog/shift-left-security-costs](https://accuknox.com/blog/shift-left-security-costs)  
> 8. DevOps Engineer Resume: Structure, Skills, Examples | Wiz, [https\://www\.wiz.io/academy/cloud-careers/devops-engineer-resume](https://www.wiz.io/academy/cloud-careers/devops-engineer-resume)  
> 9. IaC scanning tools, sorted by what they actually do \- Stategraph, [https\://stategraph.com/blog/iac-scanning](https://stategraph.com/blog/iac-scanning)  
> 10. Securing Terraform DevSecOps Workflows \- Thought Parameters LLC, [https\://blog.thoughtparameters.com/post/securing\_terraform\_devsecops\_workflows/](https://blog.thoughtparameters.com/post/securing_terraform_devsecops_workflows/)  
> 11. Terraform security scanning tools | DevSecOpsAtlas, [https\://devsecopsatlas.com/guides/terraform-security-scanning-tools](https://devsecopsatlas.com/guides/terraform-security-scanning-tools)  
> 12. A practical guide to writing secure Dockerfiles | by Madhu Akula, [https\://medium.com/miro-engineering/a-practical-guide-to-writing-secure-dockerfiles-bf561224dd80](https://medium.com/miro-engineering/a-practical-guide-to-writing-secure-dockerfiles-bf561224dd80)  
> 13. GitHub \- open-policy-agent/awesome-opa: A curated list of OPA, [https\://github.com/open-policy-agent/awesome-opa](https://github.com/open-policy-agent/awesome-opa)  
> 14. Complete guide for picking the right tool for Terraform Security Code, [https\://www\.revolgy.com/insights/blog/complete-guide-for-picking-the-right-tool-for-terraform-security-code-analysis](https://www.revolgy.com/insights/blog/complete-guide-for-picking-the-right-tool-for-terraform-security-code-analysis)  
> 15. 10 Infrastructure as Code (IaC) Scanning Tools Compared \- Spacelift, [https\://spacelift.io/blog/iac-scanning-tools](https://spacelift.io/blog/iac-scanning-tools)  
> 16. OPA Blog \- Open Policy Agent, [https\://www\.openpolicyagent.org/blog](https://www.openpolicyagent.org/blog)  
> 17. A Review on Vibe Coding: Fundamentals, State-of-the-art, [https\://www\.techrxiv.org/doi/pdf/10.36227/techrxiv.174681482.27435614/v1?download=true](https://www.techrxiv.org/doi/pdf/10.36227/techrxiv.174681482.27435614/v1?download=true)  
> 18. Best IaC Security Scanning Tools: 2026 Buyer's Guide \- Safeguard, [https\://safeguard.sh/resources/blog/best-infrastructure-as-code-iac-security-scanning-tools](https://safeguard.sh/resources/blog/best-infrastructure-as-code-iac-security-scanning-tools)  
> 19. CIS\_Amazon\_Web\_Services\_Foundations\_Benchmark\_v7.0.0.pdf  
> 20. AWS CIS Benchmark: Automated Compliance | CloudQuery Blog, [https\://www\.cloudquery.io/blog/how-to-aws-cis-compliance](https://www.cloudquery.io/blog/how-to-aws-cis-compliance)  
> 21.   
> 22. Secure CI/CD for Serverless Applications \-- An OpenFaaS Case Study, [https\://arxiv.org/pdf/2509.04328](https://arxiv.org/pdf/2509.04328)  
> 23. Building near real-time automatic remediation for disabled S3 Block, [https\://builder.aws.com/content/2ZZnk0NQzBSZwL7vKTx8TVQKhjW/building-near-real-time-automatic-remediation-for-disabled-s3-block-public-access-with-serverless-tools](https://builder.aws.com/content/2ZZnk0NQzBSZwL7vKTx8TVQKhjW/building-near-real-time-automatic-remediation-for-disabled-s3-block-public-access-with-serverless-tools)  
> 24. Startup Showcase Registry: Innovating Cloud and AI Security, [https\://cloudsecurityalliance.org/csa-startup-showcase/registry](https://cloudsecurityalliance.org/csa-startup-showcase/registry)  
> 25. Dette er en tittel 36/40 pkt går over to linjer \- Anskaffelser.no, [https\://markedsplassen.anskaffelser.no/sites/default/files/2026-05/20260511\_dfo\_mps\_cloud\_reference\_architecture\_v1.3.pdf](https://markedsplassen.anskaffelser.no/sites/default/files/2026-05/20260511_dfo_mps_cloud_reference_architecture_v1.3.pdf)  
> 26. Cloud Computing Compliance Controls Catalogue (C5) \- Scribd, [https\://www\.scribd.com/document/530556675/ComplianceControlsCatalogue-Cloud-Computing-C5](https://www.scribd.com/document/530556675/ComplianceControlsCatalogue-Cloud-Computing-C5)  
> 27. Data Classification | Plerion, [https\://www\.plerion.com/cloud-knowledge-base/data-classification](https://www.plerion.com/cloud-knowledge-base/data-classification)  
> 28. CSA CCM v4 — Control Mappings | Open Security Architecture, [https\://www\.opensecurityarchitecture.org/frameworks/csa-ccm-v4/controls/](https://www.opensecurityarchitecture.org/frameworks/csa-ccm-v4/controls/)  
> 29. Security Framework Crosswalk \- AccountMade, [https\://accountmade.com/tools/framework-crosswalk](https://accountmade.com/tools/framework-crosswalk)  
> 30. Security \- Insignia, [https\://www\.insignia.tech/capabilities/security](https://www.insignia.tech/capabilities/security)  
> 31. ciso-assistant-community/README.md at main \- GitHub, [https\://github.com/intuitem/ciso-assistant-community/blob/main/README.md](https://github.com/intuitem/ciso-assistant-community/blob/main/README.md)  
> 32. Cloud Controls Matrix CCM Explained \- ForgePath, [https\://forgepath.com/ccm/](https://forgepath.com/ccm/)  
> 33. 7 Cloud Security Frameworks to Protect Your Digital Assets \- TuxCare, [https\://tuxcare.com/blog/cloud-security-frameworks/](https://tuxcare.com/blog/cloud-security-frameworks/)  
> 34. Introductory Guidance to Cloud Controls Matrix (CCM) | CSA, [https\://cloudsecurityalliance.org/artifacts/introductory-guidance-to-ccm](https://cloudsecurityalliance.org/artifacts/introductory-guidance-to-ccm)  
> 35. MRIS for ISO/IEC 27001 (Annex A) – Assessed Against Frontier AI, [https\://mris.info/iso27001-en.html](https://mris.info/iso27001-en.html)  
> 36. We mapped all 261 CAIQ v4 questions by domain | Wolfia, [https\://wolfia.com/blog/we-mapped-all-261-caiq-v4-questions-by-domain](https://wolfia.com/blog/we-mapped-all-261-caiq-v4-questions-by-domain)