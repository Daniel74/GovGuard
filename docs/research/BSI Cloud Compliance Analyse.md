# **Maschinelle Verwertbarkeit des BSI IT-Grundschutz-Kompendiums: Systematik, OSCAL-Transformation und automatisierte Cloud-Compliance**

Die NIS2-Umsetzungsverordnung und die stetig wachsende Komplexität moderner Cloud-Umgebungen zwingen regulierte Organisationen zu einem Paradigmenwechsel in der IT-Governance. Mit dem Start der Parallelphase des „Grundschutz++“ im Januar 2026 vollzieht das Bundesamt für Sicherheit in der Informationstechnik (BSI) den zwingenden Schritt von statischen, dokumentenzentrierten PDF-Katalogen hin zu strukturierten, maschinenlesbaren Datenmodellen1. Die Einführung maschinenlesbarer Formate revolutioniert die Art und Weise, wie Compliance-Prüfungen in Continuous Integration und Continuous Deployment (CI/CD) Pipelines integriert werden. Dieser Bericht liefert eine tiefgehende, architektonische und algorithmische Analyse, wie das BSI IT-Grundschutz-Kompendium über das OSCAL-Format systematisch für automatisierte Security-Audits in ereignisgesteuerten AWS-Serverless-Architekturen adaptiert werden kann.

## **1\. Systematik & Anatomie des BSI IT-Grundschutz-Kompendiums**

Die Architektur des IT-Grundschutzes bildet das sicherheitstechnische Rückgrat für Behörden, Betreiber Kritischer Infrastrukturen (KRITIS) und stark regulierte Unternehmen. Um dieses Framework für automatisierte Cloud-Compliance-Prüfungen im Sinne von Compliance-as-Code nutzbar zu machen, ist ein präzises Verständnis seiner mehrdimensionalen Systematik unerlässlich.

### **Hierarchischer Aufbau der Schichten**

Das Kompendium ist methodisch in zehn fachliche Schichten unterteilt. Diese Architektur spiegelt den gesamten Lebenszyklus und die operationale Realität moderner IT-Landschaften wider. Jede Schicht adressiert spezifische Angriffsvektoren, Verantwortlichkeiten und technologische Domänen. Die Systematik ermöglicht es Sicherheitsarchitekten, Kontrollen exakt auf die betroffenen Assets abzubilden.  
Die Schicht ISMS (Information Security Management System) bildet die organisatorische Klammer der gesamten Sicherheitsarchitektur. Sie definiert die strategische Ausrichtung, die Governance-Strukturen, Richtlinien und die kontinuierlichen Verbesserungsprozesse der Informationssicherheit. Flankiert wird dies durch die Schicht ORP (Organisation und Personal), welche personelle Aspekte, das Onboarding, Sensibilisierungsschulungen sowie das abstrakte Identitäts- und Berechtigungsmanagement behandelt2.  
Auf einer übergreifenden, konzeptionellen Ebene operiert die Schicht CON (Konzeption und Vorgehensweise). Sie umfasst fundamentale Sicherheitskonzepte wie die angewandte Kryptographie, Vorgaben zum Datenschutz (CON.2), Löschkonzepte und das übergeordnete Notfallmanagement. Die Schicht OPS (Betrieb) regelt den sicheren täglichen Betrieb von IT-Systemen, was das Patch-Management, die Protokollierung (OPS.1.1.5) und insbesondere die sichere Cloud-Nutzung (OPS.1.1.2) einschließt3.  
Die proaktive und reaktive Überwachung wird durch die Schicht DER (Detektion und Reaktion) abgedeckt. Diese Schicht konzentriert sich auf Security Incident and Event Management (SIEM), zentrale Logging-Infrastrukturen, Auditierung und Incident Response Mechanismen. Die Schicht APP (Anwendungen) spezifiziert detaillierte Sicherheitsanforderungen für die Softwareentwicklung, den Betrieb von Webanwendungen (APP.3.1), die Absicherung relationaler Datenbanken (APP.4.3) sowie den Einsatz von Container-Technologien (APP.4.4).  
Für die Infrastrukturebene existieren vier weitere Schichten. Die Schicht SYS (IT-Systeme) fokussiert sich auf Endgeräte, Server-Betriebssysteme und mobile Endgeräte (SYS.3.2.2). Die Schicht IND (Industrielle IT) adressiert Operational Technology (OT), SCADA-Systeme und das Internet of Things (IoT) im industriellen und physischen Kontext4. Die Netzwerksicherheit wird in der Schicht NET (Netze und Kommunikation) definiert, welche Vorgaben für Netzarchitekturen (NET.1.1), Netzsegmentierung (NET.1.2), Firewalls und den Schutz der Datenübertragung auf OSI-Layer 3 bis 7 enthält. Abgeschlossen wird das Framework durch die Schicht INF (Infrastruktur), die physische Sicherheitsaspekte wie den Schutz von Gebäuden (INF.1), Rechenzentren (INF.2), Klimatisierung und unterbrechungsfreie Stromversorgungen (USV) reguliert.

### **Interne Struktur eines Bausteins (Praktik)**

Mit dem Übergang zum Grundschutz++ wurde der klassische Begriff des „Bausteins“ durch den agileren Begriff der „Praktik“ abgelöst2. Die interne Anatomie wurde dabei grundlegend für die maschinelle Auswertbarkeit und präzisere Auditierbarkeit geschärft. Eine Praktik ist strukturell in drei voneinander abhängige Kernbereiche gegliedert.  
Die Zielsetzung definiert das angestrebte Schutzspektrum prägnant. Sie dient in Audits als Interpretationshilfe für die teleologische Auslegung, falls spezifische technische Implementierungen nicht eindeutig durch die Kernanforderungen abgedeckt sind. Darauf folgt die Definition der Gefährdungslage. Hier werden die elementaren Gefährdungen und spezifischen Bedrohungen (wie unbefugte Rechteausweitung, Denial-of-Service-Angriffe oder Datenabfluss) detailliert, die auf das jeweilige Zielobjekt einwirken können.  
Den normativen Kern bilden die Sicherheitsanforderungen. Jede Anforderung ist streng atomisiert und mit einem Universally Unique Identifier (UUID) versehen5. Diese Strukturierung erlaubt eine lückenlose digitale Rückverfolgbarkeit (Traceability) über Systemgrenzen hinweg. Wenn ein Cloud-Scanner eine Fehlkonfiguration feststellt, kann diese über die UUID deterministisch auf die rechtliche Anforderung zurückgeführt werden6. Zudem sind die Anforderungen parametrisiert, sodass spezifische Vorgaben, wie Schlüssellängen oder Löschfristen, als Variablen in maschinenlesbaren Formaten instanziiert werden können5.

### **Verbindlichkeit der Anforderungsstufen**

Die funktionale Granularität des Grundschutzes wird durch ein dreistufiges Modell der Verbindlichkeit gesteuert. Diese Stufen korrelieren direkt mit den Ergebnissen der Schutzbedarfsfeststellung (Normal, Hoch, Sehr Hoch) eines Informationsverbundes und determinieren das Verhalten von automatisierten Prüfungswerkzeugen.

| Verbindlichkeitsstufe | Beschreibung und Audit-Relevanz | Automatisierungs-Verhalten (CI/CD) |
| :---- | :---- | :---- |
| **Basis-Anforderungen \[B\]** | Fundamentale, zwingende Maßnahmen zur Erreichung eines minimalen Sicherheitsniveaus. Keine Ausnahmen zulässig. | Verletzungen führen zu einem sofortigen Abbruch des Deployments (Hard Block). |
| **Standard-Anforderungen \[S\]** | Definieren den regulären Stand der Technik für Systeme mit normalem Schutzbedarf. Kernbestandteil von Zertifizierungsaudits. | Führen zu Warnungen (Soft Block) oder Abbruch, je nach Risikoakzeptanzverfahren des Managements. |
| **Erhöhter Schutzbedarf \[H\]** | Zusatzmaßnahmen für Systeme, die besonders sensible Daten verarbeiten (z. B. VS-NfD). Greifen bei Schutzbedarf „Hoch“ oder „Sehr Hoch“. | Aktiviert dedizierte, strenge Prüfrichtlinien (z. B. physische Hardware-Token, mTLS-Zwang). |

### **Bedeutung der Nomenklatur**

Die Kürzel der Anforderungen folgen einer streng hierarchischen Syntax, die maschinelles Parsen ermöglicht. Die Kennung OPS.1.1.2.A3 lässt sich exakt dekonstruieren. Das Präfix OPS verweist auf die fachliche Schicht (Betrieb). Der numerische Pfad 1.1.2 klassifiziert die spezifische Unterkategorie, in diesem Fall den Baustein „Cloud-Nutzung“3. Das Suffix A3 definiert die fortlaufende Anforderungs-ID innerhalb dieses Bausteins. Da diese IDs über verschiedene Katalogversionen hinweg stabil bleiben, können Mappings für Automated Security Testing (AST) und Governance-Werkzeuge verlässlich gepflegt werden, ohne bei jedem Update des BSI-Katalogs Refactoring betreiben zu müssen.

## **2\. OSCAL & Die GitHub-Bereitstellung (Stand-der-Technik-Bibliothek)**

Der signifikanteste Engpass der klassischen IT-Governance bestand in der Medieninkonsistenz. Textbasierte PDF-Dokumente konnten von den Continuous Integration/Continuous Deployment (CI/CD)-Pipelines und statischen Code-Analysatoren moderner Cloud-Umgebungen nicht konsumiert werden. Im September 2025 schloss das BSI diese Lücke durch die Publikation der „Stand-der-Technik-Bibliothek“ auf GitHub, wodurch IT-Sicherheitskonzepte erstmals nativ toolgestützt und automatisiert erstellt und validiert werden können8.

### **Das OSCAL-Format und der Rationale des BSI**

OSCAL (Open Security Controls Assessment Language) ist ein von der US-amerikanischen Standardisierungsbehörde NIST (National Institute of Standards and Technology) entwickeltes Framework6. Es liefert standardisierte JSON-, XML- und YAML-Strukturen, um Sicherheitskontrollen, System-Sicherheitspläne (SSPs) und kontinuierliche Audit-Ergebnisse (Assessment Results) maschinenlesbar darzustellen5.  
Das BSI wählte OSCAL für den Grundschutz++ aus drei strategischen Kernüberlegungen: Erstens schafft OSCAL Interoperabilität. Es fungiert als universeller Übersetzer (Rosetta Stone) für die Informationssicherheit, der es Werkzeugen wie AWS Security Hub, Open Policy Agent (OPA) und Compliance-Dashboards ermöglicht, native BSI-Anforderungen ohne manuelle Mapping-Schichten zu verarbeiten2. Zweitens garantiert das Format deterministische Rückverfolgbarkeit. Durch die konsequente Nutzung globaler und lokaler UUIDs (Universally Unique Identifiers) in Katalogen, Gruppen und Kontrollen kann eine festgestellte Schwachstelle algorithmisch exakt auf einen BSI-Paragrafen zurückgeführt werden5. Drittens ermöglicht die modulare Trennung von Kontrollkatalogen (catalog) und Prüfergebnissen (assessment-results) die Implementierung von Continuous Authorization to Operate (cATO), bei der Systeme kontinuierlich ihren eigenen Compliance-Status beweisen7.

### **Architektur des offiziellen BSI-Repositories**

Das offizielle Repository github.com/BSI-Bund/Stand-der-Technik-Bibliothek ist modular aufgebaut und steht unter der offenen Lizenz CC-BY-SA-4.08. Die primären Artefakte werden sukzessive im Verzeichnis sources/ bereitgestellt8. Die Architektur unterscheidet strikt zwischen verschiedenen semantischen Ebenen.  
Der Control Layer enthält die aufgelösten, nativen JSON- und XML-Kataloge der Grundschutz-Praktiken, welche die reine normative Anforderungsebene repräsentieren8. Der Implementation Layer ist für wiederverwendbare Beschreibungen konkreter Implementierungen durch Produkte oder Cloud-Dienste vorgesehen8. Dies ermöglicht es Cloud-Providern, fertige OSCAL-Komponenten bereitzustellen, die belegen, wie ein spezifischer Service (z. B. AWS KMS) eine BSI-Anforderung erfüllt. Der Assessment Layer ist für zukünftige Artefakte zur Planung, Ausführung und Nachbereitung von maschinengestützten Prüfungen reserviert8.

### **Das JSON-Schema eines BSI-Bausteins in OSCAL**

Die Entscheidung des BSI, JSON als primäres Format für den Grundschutz++ zu verwenden, trägt der Realität moderner Cloud-Entwicklung Rechnung, da JSON in REST-APIs und Serverless-Ökosystemen den De-facto-Standard bildet5. Das JSON-Metaschema von OSCAL, definiert unter http\://csrc.nist.gov/ns/oscal, ist tief verschachtelt und streng typisiert12.  
Das Wurzelobjekt bildet der catalog. Er enthält globale Metadaten, einschließlich des Titels, der Version und einer globalen UUID, und kapselt sämtliche Bausteine12. Innerhalb des Katalogs strukturieren groups die Inhalte logisch, üblicherweise genutzt, um die zehn BSI-Schichten (ORP, OPS, APP etc.) physisch in der Datei voneinander zu trennen12. Die eigentlichen atomaren Sicherheitsanforderungen residieren in den controls. Ein Control-Objekt besitzt eine eigene ID (z. B. OPS.1.1.2.A3), einen Titel und eine essenzielle Liste von Eigenschaften, die als props (Properties) deklariert sind2. Der eigentliche normative Text ist in den parts untergebracht. Ein Part vom Typ statement (prose) enthält den verbindlichen Regeltext. Ein Part vom Typ assessment-objective beschreibt hingegen die konkreten Prüfziele, nach denen ein Auditor oder ein automatisiertes Skript suchen muss, um die Erfüllung der Anforderung zu verifizieren12.  
Die Zuordnung, ob eine Regel als Basis \[B\], Standard \[S\] oder für hohen Schutzbedarf \[H\] klassifiziert ist, wird nicht im Fließtext versteckt. Stattdessen wird sie deterministisch in den Metadaten kodiert. Das BSI nutzt dafür das Array props innerhalb eines controls, wo Schlüssel-Wert-Paare wie {"name": "requirement-level", "value": "standard"} hinterlegt werden, um Automatisierungs-Pipelines eine bedingte Logikausführung zu ermöglichen2.  
**OSCAL JSON-Beispiel-Snippet:**  
Das folgende JSON-Snippet demonstriert die exakte Verschachtelung für eine Cloud-Speicher-Anforderung:

JSON  
{  
  "catalog": {  
    "uuid": "a1b2c3d4-e5f6-7890-1234-56789abcdef0",  
    "metadata": {  
      "title": "BSI IT-Grundschutz-Kompendium / Grundschutz++",  
      "last-modified": "2026-03-15T00:00:00Z",  
      "version": "2026.1"  
    },  
    "groups": \[  
      {  
        "id": "group-ops",  
        "title": "Betrieb (OPS)",  
        "controls": \[  
          {  
            "id": "OPS.1.1.2.A3",  
            "title": "Verschlüsselung von Cloud-Speichern",  
            "props": \[  
              {  
                "name": "requirement-level",  
                "value": "standard"  
              },  
              {  
                "name": "layer",  
                "value": "OPS"  
              }  
            \],  
            "parts": \[  
              {  
                "id": "OPS.1.1.2.A3\_stmt",  
                "name": "statement",  
                "prose": "Daten in Cloud-Speichern MÜSSEN im Ruhezustand (At-Rest) mittels kundenverwalteter Schlüssel verschlüsselt werden."  
              },  
              {  
                "id": "OPS.1.1.2.A3\_obj",  
                "name": "assessment-objective",  
                "prose": "Verifizierung, dass kein Cloud-Speicher unverschlüsselt oder mit Standard-Anbieterschlüsseln betrieben wird."  
              }  
            \]  
          }  
        \]  
      }  
    \]  
  }  
}

### **Automatisierte Verarbeitung und Normalisierung mittels Python**

Da die OSCAL-JSON-Struktur deterministisch und vorhersehbar ist, lässt sich der gesamte BSI-Katalog mittels Python programmatisch einlesen, filtern und in kontextspezifische, schlankere Regelwerke transformieren. Eine automatisierte Prüfengine muss nicht hunderte Seiten Text durchsuchen. Stattdessen iteriert das Skript durch den JSON-Baum, sucht nach relevanten Control-IDs auf Basis der props und extrahiert den Parameter prose aus dem assessment-objective. Diese extrahierten Rohdaten können anschließend als statische OPA-Regeln (Open Policy Agent) in CI/CD-Pipelines integriert oder für LLM-gestützte Analysen genutzt werden17.  
Diese Automatisierung reduziert den administrativen Overhead drastisch, da Änderungen im offiziellen BSI-Repository (via Git Pull) durch erneutes Ausführen des Parsers sofort in aktualisierte Prüfregeln für die Infrastruktur umgewandelt werden, was die Grundlage für echtes Continuous Compliance bildet.

## **3\. Kriterien für die Auswahl vs. Verwerfung von Bausteinen (Cloud Shift-Left)**

Der naive Ansatz, das gesamte BSI-Kompendium mit all seinen über 100 Bausteinen unreflektiert in ein automatisiertes Cloud-Sicherheitstool oder eine Infrastructure-as-Code (IaC) Prüfpipeline zu laden, ist ein weithin dokumentiertes architektonisches Anti-Pattern. Eine derartige 1:1-Übernahme scheitert in der operativen Praxis aus mehreren Gründen. Erstens provoziert sie bei asynchronen Serverless-Architekturen eine unkontrollierbare Menge an False-Positives, da Regeln für nicht-existente Infrastruktur (wie virtuelle Maschinen oder physische Switches) angewendet werden. Zweitens zwingt sie automatisierte Code-Scanner dazu, organisatorische Management-Pflichten evaluieren zu wollen, die in maschinenlesbarem Code (wie Terraform-State-Files oder OpenAPI-Spezifikationen) systematisch nicht abbildbar sind18.  
Die belastbare Lösung besteht in einer radikalen "Shift-Left"-Reduktion. Hierbei wird das Katalogvolumen algorithmisch auf 25 bis 35 technische Kernregeln komprimiert, die direkt in den Code-Repositories der Entwickler (Shift-Left) evaluiert werden. Diese Verdichtung basiert auf vier harten architektonischen Filtern.

### **Kriterium 1: Das AWS Shared Responsibility Model (Cloud vs. On-Premises)**

In der Public Cloud verschieben sich die Grenzen der IT-Sicherheitsverantwortung fundamental. Managed Services und Serverless-Architekturen bei Amazon Web Services (AWS) operieren auf einem extrem hohen Abstraktionsniveau, bei dem der Endkunde keinerlei Berührungspunkte mehr mit physischer Hardware, Hypervisoren oder der Gebäudesicherheit hat.  
Dementsprechend greift der erste Filter radikal ein und verwirft sämtliche Bausteine der Schicht INF (Infrastruktur). Regelungen wie INF.1 (Allgemeines Gebäude) oder INF.2 (Rechenzentrum, Notstromaggregate, Klimatisierung) entfallen vollständig aus dem Code-Audit. Der rechtsverbindliche Nachweis dieser Compliance obliegt ausschließlich dem Cloud-Provider. In Deutschland wird dieser Nachweis über das BSI C5-Testat (Cloud Computing Compliance Criteria Catalogue) in der Version C5:2020 Typ 2 erbracht20. AWS verfügt über vollumfängliche C5-Testate sowie SOC 2 Type II Berichte für die Region eu-central-1 (Frankfurt)23.  
Für den Audit-Kunden und die AST-Engine bedeutet dies: Die Konfiguration, ob die korrekte, testierte Region (Frankfurt) für das Deployment gewählt wird, ist im Terraform-Code prüfbar. Die physische Absicherung der Rechenzentren in Frankfurt ist es jedoch nicht24. Ausgewählt werden in diesem Filterschritt folglich ausschließlich Bausteine der Schichten APP, NET, OPS und CON, bei denen die Konfigurationshoheit und damit das Risiko – etwa beim Identity and Access Management (IAM), der Verschlüsselung von Daten At-Rest oder dem Netzwerk-Routing – vollständig in der Verantwortung des Cloud-Kunden liegt ("Security *in* the Cloud").

### **Kriterium 2: Compliance-as-Code & AST-Prüfbarkeit**

Der zweite Filter eliminiert Bausteine, die ausschließlich organisatorische Dokumentationspflichten oder manuelle Unternehmensprozesse beschreiben. Schichten wie ISMS (Informationssicherheits-Managementsysteme) und ORP (Organisation und Personal, z. B. Mitarbeiter-Schulungen, Ernennung eines CISO, Ausarbeiten von Notfallhandbüchern) lassen sich nicht durch die Analyse einer Terraform-Datei (.tf) oder eines YAML-Manifests verifizieren18.  
Ein modernes Application Security Testing (AST)-Tool, das auf Abstract Syntax Trees (AST) basiert, parst den deterministischen Quellcode in eine mathematische Baumstruktur, um Infrastrukturkonfigurationen algorithmisch zu prüfen19. Ein AST-Parser kann absolut zweifelsfrei evaluieren, ob ein S3-Bucket in Terraform die Eigenschaft BlockPublicAccess \= true aufweist oder ob ein API Gateway in seiner OpenAPI-Spezifikation TLS 1.3 In-Transit erzwingt. Er kann jedoch niemals prüfen, ob ein Mitarbeiter eine Phishing-Schulung absolviert hat. Die Extraktion für das automatisierte RAG-System (Retrieval-Augmented Generation) fokussiert sich daher zu 100 % auf maschinenlesbaren, technischen Vollzug.

### **Kriterium 3: Das "Bounded Catalog"-Prinzip (FinOps & Token Constraints)**

Das "Bounded Catalog"-Prinzip (abgegrenzter Katalog) adressiert die massiven probabilistischen Schwächen, die Large Language Models (LLMs) in streng normativen Compliance-Szenarien aufweisen. Klassische RAG-Systeme zerteilen hunderte Seiten von Richtlinien in Text-Chunks (Vektoren) und speichern sie in kostenintensiven Vektordatenbanken. Bei einer Prüfung ruft das System über eine semantische Ähnlichkeitssuche (Top-K-Retrieval) die vermeintlich passenden Textblöcke ab, um sie dem KI-Modell zur Auswertung vorzulegen. Dies führt bei Audits regelmäßig zu fatalen Fehlern – sogenannten Halluzinationen oder Lücken –, da semantisch ähnliche, aber rechtlich falsche Bausteine abgerufen werden können oder kritische Querbezüge durch das Raster des Top-K-Limits fallen.  
Die architektonische Lösung ist die radikale Kontext-Restriktion durch den Bounded Catalog. Indem das BSI-Universum durch die Filter 1 und 2 auf 25 bis 35 exakt definierte, Cloud-relevante BSI-Regeln eingedampft wird, entsteht ein hochkomprimierter, atomarer In-Memory-JSON-Index. Diese \~30 Regeln umfassen in ihrer Gesamtheit lediglich etwa 3.500 bis 4.500 Tokens3.  
Anstatt eine fehleranfällige und langsame Vektorsuche durchzuführen, wird dieser kompakte Regelkatalog bei jeder Validierung im RAM vorgehalten und vollständig in das Context-Window von leistungsfähigen Foundation Models (wie AWS Bedrock Claude 3.5) geladen. Das LLM evaluiert den Terraform-AST deterministisch gegen den *gesamten* relevanten BSI-Katalog in einem einzigen Inferenz-Durchstich. Dies schließt den Verlust von Kontext gänzlich aus, eliminiert das Risiko fehlender Referenzen, senkt die FinOps-Kosten drastisch und liefert mathematisch stabile Audit-Ergebnisse ohne Vektordatenbank-Latenzen.

## **4\. Technisches Mapping auf Referenz-Architekturen (GovCloud Archetypes)**

Die auf 25 bis 35 Kontrollen reduzierte Auswahl an OSCAL-Bausteinen muss präzise auf die Zielarchitekturen (Archetypen) des AWS-Ökosystems gemappt werden. Abstrakte normative BSI-Anforderungen werden hierbei in konkrete, binär prüfbare AWS-Infrastruktur-Pattern übersetzt. Die Analyse der folgenden Kernbausteine verdeutlicht die Mechanismen von Compliant Patterns gegenüber verletzenden (Violation) Patterns.

### **ARCH-GOV-01 (Sync Citizen REST)**

**Ziel:** Sichere Bereitstellung synchroner REST-APIs für Bürgerdienste mit hohem Durchsatz.**Ressourcen:** Amazon API Gateway, AWS Lambda, Amazon Aurora PostgreSQL, AWS KMS.

* **NET.1.1 (Netzarchitektur):** Das Design der Netzarchitektur verlangt eine strikte Trennung von Datenhaltungs- und Präsentationsschichten.  
  * *Compliant Pattern:* Die Aurora-Datenbank wird in isolierten, privaten Subnetzen der Amazon VPC (Virtual Private Cloud) provisioniert, die über keinerlei Internet Gateway (IGW) oder NAT-Gateway verfügen. Die Lambda-Funktionen werden VPC-attached konfiguriert und greifen über Security Groups im strikten Least-Privilege-Modus auf die Datenbank zu.  
  * *Violation Pattern:* Die Aurora-Instanz erhält das Flag publicly\_accessible \= true, oder die Lambda-Funktion läuft ohne VPC-Integration (Default), wodurch der Datenverkehr potenziell über das öffentliche AWS-Routing und nicht über isolierte ENIs (Elastic Network Interfaces) geleitet wird.  
* **APP.4.3 (Relationale Datenbanken):**  
  * *Compliant Pattern:* AWS Secrets Manager rotiert die administrativen DB-Credentials automatisch. Für Applikationszugriffe wird die IAM-Authentifizierung für PostgreSQL erzwungen, sodass keine statischen Passwörter in Konfigurationsdateien existieren.  
* **OPS.1.1.2 (Cloud-Nutzung):**  
  * *Compliant Pattern:* Daten in der Aurora-Datenbank müssen At-Rest verschlüsselt sein. Hierfür wird zwingend ein kundenverwalteter Schlüssel (AWS KMS CMK \- Customer Managed Key) aus der Region eu-central-1 verwendet, wodurch die kryptographische Hoheit und Nachvollziehbarkeit (via CloudTrail) beim Kunden bleibt24.

### **ARCH-GOV-02 (Async Document Ingest)**

**Ziel:** Asynchrone, hochskalierbare und entkoppelte Verarbeitung von eingereichten Dokumenten.**Ressourcen:** Amazon S3, Amazon SQS (mit Dead Letter Queue), AWS Lambda, AWS KMS.

* **OPS.1.1.2 (Cloud/Speicher):**  
  * *Compliant Pattern:* Alle S3-Buckets erzwingen serverseitige Verschlüsselung (s3:x-amz-server-side-encryption) auf Basis eines KMS CMK. Zusätzlich ist das Feature BlockPublicAccess sowohl auf Account- als auch auf Bucket-Ebene zwingend auf true gesetzt, um versehentliche Datenlecks durch fehlerhafte ACLs zu unterbinden28.  
  * *Violation Pattern:* Verwendung von AWS Managed Keys (SSE-S3), was den Schlüsselzugriff durch AWS-Administratoren theoretisch erlaubt und den BSI-Schutzbedarf für sensible Bürgerdaten unterminiert.  
* **CON.2 (Datenschutz) & APP.4.4 (Container):**  
  * *Compliant Pattern:* SQS-Queues puffern eingehende Payloads und entkoppeln die Systeme. Lambda-Funktionen oder ECS Fargate Container (APP.4.4) verarbeiten die Daten asynchron. SQS-Nachrichten sind ebenfalls via KMS verschlüsselt. Eine zwingend konfigurierte Dead Letter Queue (DLQ) fängt toxische Payloads (Poison Pills) zur forensischen Analyse ab, ohne den sauberen Datenbestand zu gefährden oder Denial-of-Service-Schleifen (APP.4.4) zu erzeugen.

### **ARCH-GOV-03 (Audit & Log Archiving)**

**Ziel:** Revisionssichere Archivierung systemweiter Log-Daten gemäß gesetzlichen Aufbewahrungsfristen.**Ressourcen:** AWS CloudTrail, Amazon S3 (Object Lock), AWS KMS.

* **DER.1 (Detektion/Logging) & OPS.1.1.5 (Protokollierung):**  
  * *Compliant Pattern:* AWS CloudTrail protokolliert API-Aufrufe mandantenübergreifend und leitet diese in einen zentralen, netzwerktechnisch abgeschotteten Audit-Account weiter28. Der Ziel-S3-Bucket nutzt S3 Object Lock im strikten Compliance Mode (WORM \- Write Once Read Many) für eine gesetzlich fixierte Retention-Periode (z. B. 10 Jahre). Dies schützt die Audit-Trails kryptographisch vor Modifikation.  
  * *Violation Pattern:* Audit-Trails können durch kompromittierte, privilegierte IAM-Rollen manipuliert oder gelöscht werden (z. B. fehlendes S3 Object Lock, unverschlüsselte CloudTrail Logs).

### **ARCH-GOV-04 (Citizen Web Portal)**

**Ziel:** Schnelle Frontend-Auslieferung mit maximalem Schutz vor Web- und DDoS-Angriffen.**Ressourcen:** Amazon CloudFront, AWS WAFv2, Amazon S3, AWS Certificate Manager (ACM).

* **APP.3.1 (Webanwendungen):**  
  * *Compliant Pattern:* Edge-TLS-Terminierung erfolgt ausschließlich mit TLS 1.3 (konfiguriert über ACM-Richtlinien). Eine AWS WAFv2 ist mit den AWS Managed Rules (OWASP Top 10\) sowie applikationsspezifischen Rate-Limiting-Regeln an die CloudFront-Distribution gekoppelt.  
* **NET.1.2 (Netzsegmentierung):**  
  * *Compliant Pattern:* Der S3-Origin-Bucket, der die statischen Frontend-Assets hält, erzwingt den Zugriff via Origin Access Control (OAC). Dadurch kann der Bucket ausschließlich vom zugewiesenen CloudFront-Service gelesen werden; direkte HTTP-Zugriffe über das Internet auf den Bucket werden blockiert.

### **ARCH-GOV-05 (Register Synchronizer)**

**Ziel:** Sichere Backend-Kopplung an behördliche Bestandsregister ohne Nutzung öffentlicher Netze.**Ressourcen:** Amazon API Gateway, AWS PrivateLink, AWS Lambda.

* **NET.1.1 & NET.3.2 (Datenübertragung):**  
  * *Compliant Pattern:* Nutzung von AWS PrivateLink (VPC Endpoints), sodass der API-Traffic zwischen dem Behörden-VPC und den angeforderten AWS-Diensten das hochsichere Backbone-Netz von AWS niemals verlässt. Im API Gateway wird beidseitige TLS-Authentifizierung (mTLS) für die sichere Identifikation der koppelnden Behörden-Clients erzwungen.  
  * *Violation Pattern:* Die Datensynchronisation erfolgt über das öffentliche Internet mit lediglich softwarebasierter IP-Whitelisting, was eklatante Man-in-the-Middle-Angriffsflächen (Verletzung NET.3.2) belässt.

### **ARCH-GOV-06 (Analytics Aggregator)**

**Ziel:** Hochskalierbare Datenaggregation unter strikter Wahrung der Mandantentrennung und der DSGVO.**Ressourcen:** Amazon S3, AWS Glue, Amazon Athena, AWS KMS.

* **APP.4.6 (Data Warehouse) & CON.2:**  
  * *Compliant Pattern:* Die logische Mandantentrennung im Data Lake wird durch strikte KMS-Key-Richtlinien in Verbindung mit Attribute-Based Access Control (ABAC) und AWS Lake Formation durchgesetzt. Lake Formation Policies auf Zeilen- und Spaltenebene (Row/Column-level Security) verhindern algorithmisch die unbefugte Verknüpfung von Rohdaten (Verletzung des Zweckbindungsprinzips der DSGVO). Rohdaten (Raw) und pseudonymisierte, aggregierte Daten (Curated) liegen zwingend in physisch separierten S3-Buckets.

### **ARCH-GOV-07 (Citizen Mobile Backend)**

**Ziel:** Bereitstellung eines hochsicheren Backends für mobile Bürger-Applikationen.**Ressourcen:** Amazon API Gateway, Amazon Cognito, Amazon SNS (Push), AWS KMS.

* **SYS.3.2.2 (Mobile Endgeräte) & ORP.4 (Identitäten):**  
  * *Compliant Pattern:* Die API-Authentifizierung erfolgt über Amazon Cognito unter strikter Nutzung von PKCE (Proof Key for Code Exchange) für die OAuth2-Flows, um Token-Interception-Angriffe auf mobilen Geräten zu verhindern.  
  * *Zero-PII Push-Trigger:* Push-Benachrichtigungen, die über Amazon SNS an Apple APNs oder Google FCM versendet werden, enthalten systemseitig keinerlei personenbezogene Daten (PII \- Personally Identifiable Information). Die Notification agiert lediglich als kryptographisch signierter asynchroner "Wake-up Call", der die Applikation zwingt, neue, verschlüsselte Payload-Daten über die mit mTLS gesicherte API aktiv abzurufen (Pull-Modell). Dadurch wird ein Datenabfluss über die Infrastruktur der Smartphone-Betriebssystemhersteller (Apple/Google) architektonisch ausgeschlossen.

| Archetyp | AWS Kern-Services | Primäre BSI-Bausteine | Grund für die Auswahl & Compliance-Muster |
| :---- | :---- | :---- | :---- |
| **ARCH-GOV-01** | API Gateway, Lambda, Aurora PG, KMS | NET.1.1, OPS.1.1.2, APP.4.3 | Netztrennung für DB (VPC ohne IGW), CMK-Verschlüsselung At-Rest. |
| **ARCH-GOV-02** | S3, SQS (+ DLQ), Lambda, KMS | OPS.1.1.2, CON.2, APP.4.4 | Bucket-Härtung (BlockPublicAccess), asynchrone Entkopplung toxischer Payloads. |
| **ARCH-GOV-03** | CloudTrail, S3 Object Lock, KMS | DER.1, OPS.1.1.5 | Revisionssicherheit via WORM (Object Lock), Manipulationsschutz von Trails. |
| **ARCH-GOV-04** | CloudFront, WAFv2, S3, ACM | APP.3.1, NET.1.2 | OWASP WAF-Schutz, OAC (Origin Access Control), strikte Edge-TLS-Terminierung. |
| **ARCH-GOV-05** | API Gateway, PrivateLink, Lambda | NET.1.1, NET.3.2 | Behördennetzkopplung ohne Internet via AWS Backbone, mTLS Zwang. |
| **ARCH-GOV-06** | S3, Glue, Athena, KMS | APP.4.6, CON.2 | Mandantentrennung via ABAC, Verhindern von Rohdatenverknüpfung (Row-Level-Security). |
| **ARCH-GOV-07** | API Gateway, Cognito, SNS, KMS | SYS.3.2.2, ORP.4 | App-Attestation, PKCE für OAuth2, Zero-PII Push Architektur. |

## **5\. Synthese: Das ideale Datenmodell für eine Serverless-Audit-Engine**

Um Compliance-Vorgaben in der DevOps-Praxis maschinell durchzusetzen, reicht die native BSI-OSCAL-Darstellung allein nicht aus. Eine moderne Audit-Engine muss Anforderungen aus verschiedenen Frameworks – wie dem BSI IT-Grundschutz, den Artikeln 25 und 32 der EU-DSGVO, den CIS AWS Foundations Benchmarks und dem CSA Cloud Controls Matrix (CCM) – deduplizieren und semantisch fusionieren29. Das Resultat dieser Aggregation ist die "Unified Audit Rule".  
Dieses fusionierte Datenmodell wandelt abstrakte Rechtsprosa in deterministische, boole'sche Prüfbedingungen um, die von IaC-Scannern und Policy-Engines wie dem Open Policy Agent (OPA) über Rego direkt konsumiert und ausgeführt werden können7. Das Schema kombiniert normative Metadaten (für die rechtliche Audit-Dokumentation) mit lexikalischen Prüf-Triggern (für die technische Evaluation des AST) und den formalen Vorgaben für die Ausstellung von OSCAL Assessment Results (oscal-ar), um kontinuierliches Reporting zu gewährleisten7.

### **Architektur des fusionierten JSON-Schemas ("Unified Audit Rule")**

Das Datenmodell der Unified Audit Rule ist streng in drei funktionale Sektionen gegliedert, um rechtliche und technische Domänen sauber zu trennen:

> 1. **Metadata & Normative References:** Diese Sektion verknüpft die isolierte technische Regel konsistent mit den übergeordneten Rechtsquellen und Normen (BSI OSCAL ID, DSGVO-Artikel, CIS-Identifikatoren). Dies vermeidet Redundanzen, da ein einziger fehlerfreier Infrastruktur-Check gleichzeitig den Nachweis für vier verschiedene Compliance-Frameworks erbringt29.  
> 2. **Evaluation Triggers (Deterministisch):** Definiert algorithmisch, bei welchen Cloud-Ressourcen (z. B. aws\_s3\_bucket) in welchem Parser-Kontext (z. B. terraform\_hcl) die Regel überhaupt getriggert wird. Dies minimiert Latenzen und False Positives beim Scannen.  
> 3. **Conditions (Must-Haves & Anti-Patterns):** Die konkrete technische Prüflogik für die AST-Validierung oder die OPA-Regel. Was muss auf Attributsebene zwingend vorhanden sein (Must-Haves), und welche Konfigurationswerte führen zum sofortigen Blockieren der Pipeline (Anti-Patterns)?  
> 4. **OSCAL Mapping:** Vorgaben, wie das Evaluierungsergebnis in einen validen OSCAL Assessment Results (AR) Report zu übersetzen ist, der dann an Aggregationswerkzeuge wie AWS Security Hub oder ServiceNow übergeben wird13.

**Konkretes JSON-Schema einer Unified Audit Rule:**  
Das folgende JSON-Dokument demonstriert das Schema für die Überprüfung der Speichersicherheit:

JSON  
{  
  "rule\_id": "UAR-AWS-S3-001",  
  "rule\_name": "Sichere Konfiguration und Verschlüsselung von Objektspeichern",  
  "severity": "CRITICAL",  
  "normative\_references": {  
    "bsi\_grundschutz": {  
      "control\_id": "OPS.1.1.2.A3",  
      "requirement\_level": "standard",  
      "url": "https\://github.com/BSI-Bund/Stand-der-Technik-Bibliothek"  
    },  
    "dsgvo": \[  
      "Art. 32 (1) a (Pseudonymisierung und Verschlüsselung)",  
      "Art. 25 (Data Protection by Default)"  
    \],  
    "cis\_aws\_benchmark": "3.1.4 Ensure S3 bucket server-side encryption is enabled",  
    "csa\_ccm": "DSP-17 (Data Security & Privacy: Encryption)"  
  },  
  "evaluation\_triggers": {  
    "target\_resources": \[  
      "aws\_s3\_bucket",  
      "aws\_s3\_bucket\_server\_side\_encryption\_configuration",  
      "aws\_s3\_bucket\_public\_access\_block"  
    \],  
    "ast\_scope": "terraform\_hcl"  
  },  
  "conditions": {  
    "must\_haves": \[  
      {  
        "attribute": "rule.apply\_server\_side\_encryption\_by\_default.sse\_algorithm",  
        "expected\_value": "aws:kms",  
        "rationale": "Erzwingt kundenverwaltetes Key-Material (CMK), schließt unsicheres SSE-S3 systemseitig aus."  
      },  
      {  
        "attribute": "block\_public\_acls",  
        "expected\_value": true,  
        "rationale": "Verhindert algorithmisch die Anlage öffentlicher Access Control Lists auf Infrastruktur-Ebene."  
      },  
      {  
        "attribute": "block\_public\_policy",  
        "expected\_value": true,  
        "rationale": "Verhindert das unbedachte Anwenden öffentlicher Bucket Policies durch Administratoren."  
      }  
    \],  
    "anti\_patterns": \[  
      {  
        "attribute": "acl",  
        "prohibited\_value": "public-read",  
        "remediation\_message": "S3 ACLs dürfen keinesfalls auf public-read gesetzt sein. Ändern Sie auf private oder nutzen Sie granulare IAM-Policies."  
      },  
      {  
        "attribute": "website",  
        "prohibited\_value": "\*",  
        "remediation\_message": "S3 Static Website Hosting ist für schützenswerte Buckets (GovCloud Archetypes) strikt untersagt. Nutzen Sie stattdessen CloudFront kombiniert mit OAC."  
      }  
    \]  
  },  
  "oscal\_assessment\_result": {  
    "component\_id": "s3-storage-subsystem",  
    "status\_on\_pass": "satisfied",  
    "status\_on\_fail": "not-satisfied",  
    "evidence\_mapping": "cloudtrail\_arn\_reference"  
  }  
}

Durch diesen holistischen Modellierungsansatz wird eine hochgradig effiziente Brücke zwischen der primär juristisch geprägten Compliance-Dokumentation des BSI und der harten, deterministischen Code-Realität einer AWS DevOps-Pipeline geschlagen. Der aus OSCAL abgeleitete Bounded Catalog, nahtlos eingespeist in LLM-basierte Auswertungssysteme und validiert durch präzise Unified Audit Rules, führt zu einer extremen Reduzierung von False Positives. Er minimiert den manuellen Audit-Aufwand drastisch33 und integriert sich organisch in Evidence-Sammler wie AWS Security Hub oder spezialisierte OSCAL-Compliance-Kits7. Die Maschinelesbarkeit des BSI Grundschutz++ über OSCAL, gepaart mit einer rigorosen Shift-Left-Filterarchitektur, bildet somit das technologische Fundament für Continuous Authorization to Operate (cATO) im streng regulierten Cloud-Umfeld der Zukunft.

#### **Works cited**

> 1. Grundschutz++ \- Wikipedia, [https\://de.wikipedia.org/wiki/Grundschutz++](https://de.wikipedia.org/wiki/Grundschutz++)  
> 2. BSI Grundschutz++ 2026/2030: was sich für KMU ändert (OSCAL, [https\://www\.fraghugo.de/bsi-grundschutz-plus-plus-2027-kmu-vorbereitung/](https://www.fraghugo.de/bsi-grundschutz-plus-plus-2027-kmu-vorbereitung/)  
> 3. BSI-Mapping \- Johannes Kresse, [https\://johanneskresse.com/bsi-mapping/](https://johanneskresse.com/bsi-mapping/)  
> 4. BSI IT-Grundschutz 2026: Grundschutz++ & Certification \- Orbiq, [https\://www\.orbiqhq.com/eu-regulations/bsi-it-grundschutz](https://www.orbiqhq.com/eu-regulations/bsi-it-grundschutz)  
> 5. Grundschutz++: Mehr Resilienz in der Informationssicherheit?, [https\://research.hisolutions.com/2026/03/grundschutz-mehr-resilienz-in-der-informationssicherheit/](https://research.hisolutions.com/2026/03/grundschutz-mehr-resilienz-in-der-informationssicherheit/)  
> 6. OSCAL Workshop Slides \- NIST Pages, [https\://pages.nist.gov/OSCAL/learn/presentations/OSCAL-workshop-20191105.pdf](https://pages.nist.gov/OSCAL/learn/presentations/OSCAL-workshop-20191105.pdf)  
> 7. Study Guide \- GRC Engineering Club, [https\://grcengclub.com/academy/CGE-P\_Study\_Guide.pdf](https://grcengclub.com/academy/CGE-P_Study_Guide.pdf)  
> 8. BSI-Bund/Stand-der-Technik-Bibliothek \- GitHub, [https\://github.com/BSI-Bund/Stand-der-Technik-Bibliothek](https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek)  
> 9. BSI veröffentlicht Stand-der-Technik-Bibliothek auf GitHub, [https\://www\.bsi.bund.de/DE/Service-Navi/Presse/Alle-Meldungen-News/Meldungen/Stand-der-Technik-Bibliothek\_250930.html](https://www.bsi.bund.de/DE/Service-Navi/Presse/Alle-Meldungen-News/Meldungen/Stand-der-Technik-Bibliothek_250930.html)  
> 10. BSI-Grundschutz++: Kompendium-Preview \- ComConsult, [https\://www\.comconsult.com/bsi-grundschutz-kompendium-preview-in-stand-der-technik-bibliothek-auf-github-veroeffentlicht/](https://www.comconsult.com/bsi-grundschutz-kompendium-preview-in-stand-der-technik-bibliothek-auf-github-veroeffentlicht/)  
> 11. Public Health Cybersecurity Education Gaps: Pandemics Are Both, [https\://search.proquest.com/openview/1c974d78638d2fa59bb62e38b67041ec/1?pq-origsite=gscholar\&cbl=18750\&diss=y](https://search.proquest.com/openview/1c974d78638d2fa59bb62e38b67041ec/1?pq-origsite=gscholar&cbl=18750&diss=y)  
> 12. OSCAL Catalog Model v1.1.2 JSON Format Metaschema Reference, [https\://pages.nist.gov/OSCAL-Reference/models/v1.1.2/catalog/json-definitions/](https://pages.nist.gov/OSCAL-Reference/models/v1.1.2/catalog/json-definitions/)  
> 13. New features and products in Australia \- ServiceNow, [https\://www\.servicenow.com/docs/r/australia/release-notes/rn-summary-new-features.html](https://www.servicenow.com/docs/r/australia/release-notes/rn-summary-new-features.html)  
> 14. DevSecOps Roadmap 2026 \- GitHub, [https\://github.com/siddhantbhattarai/DevSecOps-Roadmap](https://github.com/siddhantbhattarai/DevSecOps-Roadmap)  
> 15. OSCAL Contributing \- Big Bang Docs, [https\://docs-bigbang.dso.mil/3.22.1/docs/community/development/oscal-contributing/](https://docs-bigbang.dso.mil/3.22.1/docs/community/development/oscal-contributing/)  
> 16. Grundschutz++ Navigator, [https\://grundschutz-navigator.de/](https://grundschutz-navigator.de/)  
> 17. [unknown\_url](http://docs.google.com/unknown_url)  
> 18. Blog \- sota.io, [https\://www\.sota.io/blog](https://www.sota.io/blog)  
> 19. security | Noise | Page 3, [https\://noise.getoto.net/tag/security/page/3/](https://noise.getoto.net/tag/security/page/3/)  
> 20. Masterthesis \- Hochschule Heilbronn, [https\://cdn.hs-heilbronn.de/e796ec2c9b6ac2be/ed83603c66f4/Masterthesis\_cbaas\_197504.pdf](https://cdn.hs-heilbronn.de/e796ec2c9b6ac2be/ed83603c66f4/Masterthesis_cbaas_197504.pdf)  
> 21. Kompendium für organisationsinterne Telekommunikationssysteme, [https\://www\.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Cyber-Sicherheit/Themen/KomTK-Teil1.pdf?\_\_blob=publicationFile\&v=2](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Cyber-Sicherheit/Themen/KomTK-Teil1.pdf?__blob=publicationFile&v=2)  
> 22. (PDF) Adoption Frameworks for Digital Health Solutions in Hospital, [https\://www\.researchgate.net/publication/401924562\_Adoption\_Frameworks\_for\_Digital\_Health\_Solutions\_in\_Hospital\_Settings](https://www.researchgate.net/publication/401924562_Adoption_Frameworks_for_Digital_Health_Solutions_in_Hospital_Settings)  
> 23. Trustcenter: Jede Aussage mit Beleg \- AI MyDocuments, [https\://ai-mydocuments.de/trustcenter](https://ai-mydocuments.de/trustcenter)  
> 24. AWS Bedrock AVV und DSGVO in Deutschland \- Compound Law, [https\://compound.law/de-DE/tools/aws-bedrock/](https://compound.law/de-DE/tools/aws-bedrock/)  
> 25. ReadyStack \- Open VSX Registry, [https\://open-vsx.org/namespace/readystack](https://open-vsx.org/namespace/readystack)  
> 26. Visualization — list of Rust libraries/crates // Lib.rs, [https\://lib.rs/visualization](https://lib.rs/visualization)  
> 27. Blog | Rohan Bhagat | IT Security Engineer, [https\://www\.rohanbhagat.com/blog/](https://www.rohanbhagat.com/blog/)  
> 28. Security, Identity & Compliance | Noise | Page 2, [https\://noise.getoto.net/tag/security-identity-compliance/page/2/](https://noise.getoto.net/tag/security-identity-compliance/page/2/)  
> 29. GantmanBiz — AI-First Software Company · Products That Ship, [https\://gantman.biz/](https://gantman.biz/)  
> 30. Gemara mapping \- Evidentia, [https\://docs.evidentiagrc.com/5-compliance/gemara-mapping/](https://docs.evidentiagrc.com/5-compliance/gemara-mapping/)  
> 31. v0.13 — IaC / OCSF / OSCAL ingest \+ emit · Issue \#12 · darpanzope, [https\://github.com/darpanzope/compliancekit/issues/12](https://github.com/darpanzope/compliancekit/issues/12)  
> 32. Run evidence collectors \- Evidentia, [https\://docs.evidentiagrc.com/2-guides/run-collectors/](https://docs.evidentiagrc.com/2-guides/run-collectors/)  
> 33. Security Blog | Noise | Page 2, [https\://noise.getoto.net/tag/security-blog/page/2/](https://noise.getoto.net/tag/security-blog/page/2/)  
> 34. CLI (6.16.1.0 and older) \- RegScale Documentation, [https\://regscale.readme.io/changelog/changelog-cli](https://regscale.readme.io/changelog/changelog-cli)