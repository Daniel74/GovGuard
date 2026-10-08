# GovGuard – Ausbau in vier Szenarien (nicht MVP)

Das MVP ist bewusst klein: 24 bzw. 20 Prüfregeln, Eingaben bis 100.000 Zeichen, 3 Golden Archetypes. Dieses Dokument beschreibt für vier Szenarien, was beim Wachsen bricht und was sich dann ändert. Es ist ein **Ausblick, keine Entscheidung**. Gebaut wird eine Stufe erst, wenn ihr Auslöser messbar eintritt.

**Was in jedem Szenario gleich bleibt:**
- Jede Prüfregel bekommt einen Befund; es wird nichts per Ähnlichkeitssuche weggelassen.
- Jeder Beleg ist ein wörtliches Zitat, das der Code prüft.
- Das LLM urteilt, der Code bereitet vor und kontrolliert (siehe [ARCHITECTURE.md](ARCHITECTURE.md)).

---

## Szenario 1: Mehr Regeln erfassen und anwenden

**Beispiel:** Eine Behörde will statt 12 deutlich mehr BSI-Anforderungen geprüft haben (angenommen 80; die echte Zahl zeigt der erste Build-Lauf), dazu BSI C5 als neue Quelle.

**Was bricht:** Jede Prüfregel erzeugt einen Befund. Bei 80 Regeln schreibt das Modell viermal so viel. Das dauert länger als die 29 Sekunden, die API Gateway wartet, und die Qualität sinkt, weil das Modell zu viel auf einmal bewerten muss.

**Was sich ändert:**

| Schritt | Änderung | Wer |
|---|---|---|
| Erfassen (Build) | Obergrenze in der Konfiguration erhöhen; der Rest der Pipeline bleibt gleich. | Konfiguration |
| Neue Quelle (Build) | Ein **Quellen-Adapter** mit drei Funktionen: Anforderungen auslesen, vorfiltern, Rang bestimmen. Alles danach ist bestehende Pipeline. | Code |
| Schneller neu bauen (Build) | Bereits klassifizierte Anforderungen werden zwischengespeichert. Ein Neubau fragt das LLM nur zu geänderten Anforderungen. | Code |
| Unnötiges weglassen (Laufzeit) | Kommt in einem Template kein S3-Bucket vor, setzt der Code alle S3-Regeln direkt auf N/A. Diese Regeln gehen gar nicht ans LLM. | Code |
| Aufteilen (Laufzeit) | Der Katalog wird in Pakete à 20 Regeln geteilt (z. B. Identität, Speicher, Protokollierung). Jedes Paket prüft ein eigener LLM-Aufruf, alle laufen **parallel**. Danach fügt der Code die Befunde zusammen. | LLM je Paket, Code fügt zusammen |

Das Aufteilen heißt **Map-Reduce**: viele gleiche Teilaufgaben parallel (Map), dann ein Zusammenführen (Reduce).

**Auslöser:** mehr als ca. 50 Regeln oder eine Antwortzeit über 20 Sekunden.

---

## Szenario 2: Längere Dokumente auditen

**Beispiel:** Ein Fachkonzept mit 300 Seiten oder ein Terraform-Projekt mit 3.000 Zeilen.

**Was bricht:** Die Eingabe passt nicht mehr in den Request (Lambda nimmt höchstens 6 MB an). Außerdem übersieht das Modell in sehr langen Texten Details in der Mitte.

**Was sich ändert:** Je nach Art der Eingabe gibt es einen anderen Weg.

| Eingabe | Vorgehen | Wer |
|---|---|---|
| Jede große Datei | Der Client lädt die Datei direkt nach S3 hoch; die API bekommt nur noch den Speicherort. | Code |
| Terraform, CloudFormation, OpenAPI | **Kürzen:** Die Datei wird geparst, nur sicherheitsrelevante Teile bleiben (Ressourcen und ihre Einstellungen, Datenfelder, Authentifizierung). Beschreibungen und Beispiele fallen weg. | Code |
| Langer Freitext | **Erst Fakten sammeln, dann prüfen** (siehe unten). | LLM sammelt, Code prüft |

Bei langem Freitext:

1. Der Code schneidet das Dokument an Überschriften in Abschnitte.
2. Je Abschnitt sammelt das LLM nur auditrelevante Fakten, z. B. welche Daten erhoben werden, wofür, wo sie gespeichert werden und welche Dienste beteiligt sind. Jeden Fakt belegt es mit einem wörtlichen Zitat. Alle Abschnitte laufen parallel.
3. Der Code prüft jedes Zitat gegen das Original und führt die Fakten zu einem **Faktenblatt** zusammen.
4. Das Audit läuft wie im MVP, nur auf dem Faktenblatt statt auf 300 Seiten.

**Preis dafür:** Was in Schritt 2 übersehen wird, fehlt dem Audit. Deshalb zeigt die UI das Faktenblatt an, damit der Nutzer Lücken erkennt.

**Auslöser:** Eingaben über 100.000 Zeichen.

---

## Szenario 3: Größere Architekturen erzeugen

**Beispiel:** Ein Bürgerportal braucht Web-Frontend, REST-Backend, Dokumenten-Upload und Audit-Log, also mehrere Archetypen auf einmal.

**Was bricht:** Die Archetyp-Auswahl liefert genau einen Archetyp. Kombinationen gibt es nicht, und zur Laufzeit wird bewusst nichts generiert (ADR 0003).

**Was sich ändert:** Drei Stufen, jede mit mehr Nutzen und mehr Risiko.

| Stufe | Änderung | Risiko |
|---|---|---|
| 3a Mehrfachauswahl | Die Auswahl liefert eine **Liste** von Archetypen, z. B. ARCH-01 + ARCH-02 + ARCH-03. Jeder bleibt ein eigener, freigegebener Stack; eine Begründung beschreibt, wie sie zusammenspielen. | gering, weil alles weiterhin vorab freigegeben ist |
| 3b Kombi-Archetypen | Häufige Kombinationen werden als **eigener Archetyp** zur Build-Zeit erzeugt und genauso freigegeben wie die einzelnen. | gering, aber mehr Build-Aufwand |
| 3c Erzeugung zur Laufzeit | Das LLM baut aus Archetypen als Bausteinen einen neuen Entwurf. Die Freigabe-Schleife (`cdk synth`, Audit, cdk-nag) läuft dann **pro Anfrage** in einem Build-Container. | hoch: bricht ADR 0003, dauert Minuten, braucht ein neues ADR |

**Auslöser:** Nutzer fragen regelmäßig nach Kombinationen (3a, 3b). 3c nur mit neuem ADR.

---

## Szenario 4: Mehr Archetypen definieren

**Beispiel:** Ein Archetyp für mobile Bürger-Apps (ARCH-07) oder für Datenanalyse (ARCH-06) kommt dazu.

**Was bricht:** Zunächst nichts, ein neuer Archetyp ist nur ein neuer Steckbrief. Ab etwa 10 Archetypen wird die Auswahl unsicherer, weil das Modell zwischen vielen ähnlichen Optionen wählen muss.

**Was sich ändert:**

| Schritt | Änderung | Wer |
|---|---|---|
| Definieren | Neuer **Steckbrief**: Zweck, Solutions Constructs, Pflicht-Ressourcentypen. | Konfiguration |
| Erzeugen und freigeben | Die bestehende Build-Schleife: LLM schreibt CDK, `cdk synth`, Audit, cdk-nag. | wie im MVP |
| Auswahl testen | Je Archetyp ein **Auswahl-Preset**: eine Spezifikation, für die ein Mensch festlegt, welcher Archetyp herauskommen muss. | Mensch legt Soll fest |
| Auswahl in zwei Schritten | Ab ca. 10 Archetypen: Zuerst bestimmt das LLM wenige Merkmale der Spezifikation (z. B. synchron oder asynchron? Datei-Upload? Mobile App?). Dann filtert der Code die Archetypen nach diesen Merkmalen, und das LLM wählt nur noch unter den passenden. | LLM, Code, LLM |

**Auslöser:** mehr als ca. 10 Archetypen oder ein Auswahl-Preset schlägt fehl.

---

## Übersicht: Was sich am System insgesamt ändert

Sobald ein Audit mehrere LLM-Aufrufe braucht (Szenario 1 Aufteilen, Szenario 2 Freitext), reicht die synchrone Antwort nicht mehr:

| Heute (MVP) | Später |
|---|---|
| Die API antwortet direkt mit dem Report. | Die API antwortet sofort mit einer Auftragsnummer; der Report wird später abgeholt. |
| Eine Lambda-Funktion. | **Step Functions** steuert die parallelen Aufrufe; Kosten nur pro Ausführung. |
| Nichts wird gespeichert. | Aufträge und Reports werden gespeichert und brauchen dann Löschfristen (DSGVO Art. 5 Abs. 1 lit. e). |

**Satz für die Verteidigung:** „Wir skalieren durch Aufteilen, nicht durch Weglassen. Vollständigkeit und Zitatpflicht gelten in jeder Ausbaustufe.“
