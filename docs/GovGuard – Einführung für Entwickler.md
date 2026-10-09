# GovGuard – Einführung für Entwickler

Oct 9, 2026 · @Daniel

## 1. Worum es geht

GovGuard ist ein automatischer Prüfer für Behörden-IT. Er prüft fachliche **Spezifikationen** gegen Datenschutzrecht (DSGVO und Standard-Datenschutzmodell SDM) und **Cloud-Architekturen** gegen IT-Sicherheitsstandards (BSI Grundschutz++ und CIS AWS Benchmark v7).

Das Ergebnis ist ein **Audit-Report**. Er enthält zu jeder Prüfregel genau einen Befund: einen Status, ein wörtliches Zitat aus der Eingabe als Beleg und eine Empfehlung. Hat eine Spezifikation keinen Verstoß, schlägt GovGuard zusätzlich eine passende, vorab geprüfte Architekturvorlage vor (einen **Golden Archetype**).

Ein Bild zur Orientierung: GovGuard arbeitet wie eine TÜV-Prüfung mit fester Checkliste. Jeder Punkt der Liste wird bei jeder Prüfung abgehakt, und für jedes Urteil muss der Prüfer zeigen, wo er es gesehen hat.

| Wer | gibt hinein | bekommt heraus |
| --- | --- | --- |
| Architekt | eine Spezifikation (Text) | Audit-Report gegen DSGVO und SDM |
| Architekt | eine Architektur (Freitext, Terraform oder CloudFormation) | Audit-Report gegen BSI und CIS |
| Architekt | Spezifikation + Audit-Report ohne FAIL | Golden Archetype (CDK-Code + Template) oder „kein passender Archetyp“ |
| CI-Pipeline | einen API-Aufruf | den Gesamtstatus zum maschinellen Auswerten |
| Projektbetreiber | den Start des Builds | einen Pull Request mit neuer Wissensbasis |
| Auditor | – | ein Protokoll-Ereignis je Aufruf in CloudWatch Logs |

## 2. Das Grundprinzip: Das LLM entwirft, der Code entscheidet

Wenn du nur einen Gedanken aus diesem Dokument mitnimmst, dann diesen: **Das Sprachmodell (LLM) liefert Entwürfe. Der Code entscheidet, ob daraus Fakten werden.**

Ein LLM ist gut im Verstehen, Bewerten und Formulieren. Es arbeitet aber probabilistisch: Dieselbe Frage kann verschiedene Antworten ergeben, und eine plausible Antwort kann erfunden sein (Halluzination). In einem Compliance-Werkzeug ist ein erfundener Normverweis schlimmer als gar keiner.

Deshalb behandelt GovGuard jede LLM-Ausgabe wie eine **unvertrauenswürdige Eingabe**, etwa ein Formular aus dem Internet. Sie wird validiert, bevor irgendetwas damit passiert.

### Die Testfrage: Code oder LLM?

Für jede Aufgabe gilt eine einfache Frage: *Gibt es genau eine richtige Antwort, die sich ohne Sprachverständnis ermitteln lässt?* Ja → Code. Nein → LLM, und danach prüft der Code das Ergebnis.

| Code (deterministisch) | LLM (probabilistisch) |
| --- | --- |
| zählen, sortieren, filtern, nachschlagen | verstehen, bewerten, formulieren |
| Vorfilter, Ranking, Obergrenze des Katalogs | „Ist diese Anforderung an einem Template prüfbar?“ |
| Steht das Zitat wörtlich in der Quelle? | Prüfkriterien und Empfehlungen formulieren |
| Hat jede Prüfregel genau einen Befund? | „Verstößt diese Spezifikation gegen Art. 9 DSGVO?“ |
| Gesamtstatus = schlechtester Einzelstatus | Archetyp aus einer geschlossenen Liste wählen |

### Das Sandwich

Das LLM sitzt immer zwischen zwei Code-Schichten: Der Code **bereitet vor** (filtert, wählt aus), das LLM **urteilt**, der Code **kontrolliert** (Schema, Vollständigkeit, Zitate). Dazu kommt eine Leitregel: *Was der Code schon weiß, erzeugt das LLM nicht.* Jedes Feld, das das LLM nicht ausfüllen muss, kann es auch nicht falsch ausfüllen.

### Das Draft-Pattern

Daraus folgt ein Muster, das du überall im Datenmodell wiederfindest. Fast jedes Kernobjekt gibt es zweimal:

- Ein **Draft** (Entwurf) enthält nur die Felder, die Sprachverständnis brauchen. Aus dieser Pydantic-Klasse entsteht das Formular, das das LLM ausfüllen muss.
- Die fertige **Entity** erbt vom Draft und ergänzt, was der Code sicher weiß: IDs, Fundstellen, Rang, Herkunft.

| LLM liefert | Code macht daraus | Wo |
| --- | --- | --- |
| `Classification` | `Selection` (Auswahlliste) | Build |
| `RuleDraft` | `Rule` (Prüfregel) | Build |
| `FindingDraft` | `Finding` (Befund) | Laufzeit |

### Das Tool ist ein Formular

Technisch zwingt GovGuard das LLM über **Tool-Choice** in eine feste Struktur. Die Bedrock Converse API bietet dem Modell ein „Tool“ mit JSON-Schema an und erzwingt dessen Nutzung. Das Modell kann dann nicht frei antworten, sondern nur das Formular ausfüllen. Ausgeführt wird dabei nichts: Die Argumente des Tools *sind* das Ergebnis. Die Bibliothek Pydantic AI erzeugt das Schema aus dem Draft-Modell und übernimmt den Retry bei Fehlern (ADR 0005).

Enums im Schema schließen die Antwortmenge: Das Modell kann keinen Status „OK“ und keinen Archetyp „ARCH-09“ erfinden. Tool-Choice ist aber kein Beweis für richtige Werte. Darum prüft danach immer der Code.

## 3. Die wichtigsten Begriffe

Diese Begriffe tauchen in jedem Kapitel auf. Die Datenmodell-Namen in Klammern findest du so im Code (`DESIGN.md`).

| Begriff | Bedeutung | Beispiel |
| --- | --- | --- |
| Quelle | Ein Regelwerk, aus dem Prüfregeln entstehen | BSI Grundschutz++, CIS AWS v7, DSGVO, SDM |
| Anforderung (`Requirement`) | Eine einzelne Vorgabe aus einer Quelle, unverändert extrahiert | CIS 3.1.4, BSI DET.3.1, DSGVO Art. 32 |
| Primäranker | Die zitierfähige Fundstelle einer Anforderung, im festen Format je Quelle | `CIS AWS v7.0.0 3.1.4`, `DSGVO Art. 32` |
| Prüfregel (`Rule`) | Aus genau einer Anforderung abgeleitetes, prüfbares Kriterium | `ARCH-CIS-3.1.4` „S3 Block Public Access aktiv“ |
| Audit-Art | Spezifikation (Spec) oder Architektur | `spec`, `architecture` |
| Bounded Catalog | Feste, begrenzte Menge Prüfregeln je Audit-Art; geht in jedem Audit vollständig ans LLM | 24 Architektur-Regeln (12 BSI + 12 CIS), 20 Spec-Regeln (12 DSGVO + 8 SDM) |
| Wissensbasis | Die versionierten JSON-Dateien mit Prüfregeln und Archetypen | `rules_spec.json`, `rules_arch.json`, `archetypes.json` |
| Befund (`Finding`) | Das Urteil zu einer Prüfregel in einem Audit | Status + Beleg + Begründung + Empfehlung |
| Status | Eines von vier erlaubten Urteilen | PASS, WARN, FAIL, N/A |
| Beleg (`evidence`) | Wörtliches Zitat aus der Eingabe, das ein Urteil stützt | „BlockPublicAccess: BLOCK\_ALL“ |
| Golden Archetype | Vorab gebaute und freigegebene Architekturvorlage als CDK-Code + CloudFormation-Template | ARCH-01 Sync REST |
| Steckbrief (`ArchetypeProfile`) | Von Hand gepflegte Vorgabe für einen Archetyp: Zweck, Bausteine, Pflicht-Ressourcentypen | `data/archetype_profiles.json` |
| Gate | Automatischer Prüfpunkt im Build; fällt etwas durch, bricht der Build ab | Zitat-Gate, Preset-Gate |
| Preset | Testbeispiel mit einem von Menschen festgelegten Soll-Ergebnis | 4 Ordner unter `data/presets/` |
| Build-Zeit | Selten, manuell: Wissensbasis und Archetypen erzeugen | GitHub-Workflow `build-kb.yml` |
| Laufzeit | Je Anfrage: ein Audit beantworten | Lambda hinter API Gateway |

**Die vier Status-Werte** sind so definiert:

- **PASS:** Einhaltung ist *belegt*.
- **WARN:** Aus der Eingabe nicht entscheidbar, es besteht Prüfbedarf.
- **FAIL:** Ein Verstoß ist *belegt*.
- **N/A:** Die Prüfregel ist nicht anwendbar.

Achte auf das Wort „belegt“: Fehlt eine Information, ist das WARN, nie FAIL. So kann das LLM aus Schweigen keinen Verstoß konstruieren.

## 4. Der Weg der Daten im Überblick

GovGuard hat zwei Betriebsarten, die nur über einen Weg verbunden sind. In der **Build-Zeit** entsteht die Wissensbasis, über **Deployment** gelangt sie nach S3, und zur **Laufzeit** wird sie nur noch gelesen.

&#91;embedded content: Datenfluss · Build-Zeit, Deployment, Laufzeit\]

Lies das Bild spaltenweise von oben nach unten. Farbig markiert ist, wo ein LLM mitarbeitet: Jeder dieser Schritte ist von Code-Schritten eingerahmt, die vorbereiten oder kontrollieren.

- **Build-Zeit** läuft selten und nur auf Knopfdruck. Sie kostet viele LLM-Aufrufe, liefert bei jedem Lauf leicht andere Texte, und die Quellen ändern sich selten. Regeln und Archetypen werden immer zusammen gebaut, weil die Archetypen gegen genau diese Regeln freigegeben werden.
- **Deployment** ist der einzige Weg in die Produktion. Es prüft den eigenen Stack und kopiert die Wissensbasis nach S3.
- **Laufzeit** erzeugt nichts Neues. Sie bewertet Eingaben gegen den festen Katalog und wählt höchstens einen fertigen Archetyp aus.

Die Kapitel 5 bis 9 gehen diese Spalten Schritt für Schritt durch.

## 5. Build, Schritt 1–2: Quellen einlesen und auswählen

Aus großen Regelwerken (allein BSI Grundschutz++ hat rund 1.000 Anforderungen) macht der Build eine kleine, feste Auswahl: 24 für Architektur, 20 für Spezifikationen. Diese Auswahl ist der **Bounded Catalog**.

### Warum keine Vektorsuche?

Viele LLM-Systeme suchen zur Laufzeit per Vektorsuche die „passendsten“ Regeln heraus (Top-K-Retrieval). Für ein Audit ist das gefährlich: Eine relevante Regel kann einfach nicht gefunden werden, und niemand merkt es. GovGuard dreht das um. Die Auswahl passiert **einmal zur Build-Zeit**, liegt versioniert im Repo, und zur Laufzeit wird **jede** ausgewählte Regel in **jedem** Audit bewertet (ADR 0002). Keine Embeddings, keine Vektor-Datenbank, keine Leerlaufkosten.

### Schritt 1: Extrahieren (Code)

Je Quelle liest ein Quellen-Adapter (`src/kb_build/sources/*.py`) die Rohdaten: PDFs für CIS, DSGVO und SDM, den OSCAL-Katalog für BSI (fixiert auf einen Commit-SHA). Er schreibt eine Datei `data/extracted/<quelle>.json`.

- Die Datei enthält **alle** Anforderungen, nicht nur die gefilterten. Grund: Später wird geprüft, ob vom LLM vorgeschlagene Querverweise existieren, und die können auf beliebige Anforderungen zeigen.
- Jede Anforderung hat `id`, `title`, den mit `normalize()` bereinigten Volltext `text`, den `primary_anchor` und `attributes` (reine Fakten wie Kapitel oder Level).
- Hier ist **kein LLM** beteiligt. Diese Dateien sind das Fundament der Beweisführung: Alles, was das LLM später behauptet, wird gegen sie geprüft.

### Schritt 2: Sieben in vier Stufen

1. **Vorfilter (Code):** Wirft anhand von Metadaten Offensichtliches weg, etwa organisatorische Anforderungen. Billig und reproduzierbar. Das Ergebnis steht im Feld `prefilter_passed`.
2. **Klassifizieren (LLM):** Das LLM bekommt **eine** Anforderung und füllt das Formular `classify_requirement`: prüfbar ja/nein, eine Begründung und bei Architektur die betroffenen CloudFormation-Ressourcentypen (`cfn_resource_types`, z. B. `AWS::S3::Bucket`). Es zählt nicht und wählt nicht aus.
3. **Relevanz (Code, nur Architektur):** Es bleiben nur Anforderungen, deren Ressourcentypen sich mit den Typen der Archetyp-Steckbriefe überschneiden. Kontoweite Pflichten wie Root-MFA fallen damit heraus, denn sie sind an keinem Template entscheidbar.
4. **Gesetzte Plätze und Ranking (Code):** Zuerst kommen die Pflichtanker der Presets in den Katalog (höchstens 4 je Audit-Art). Die übrigen Plätze verteilt der Code **reihum** auf Gruppen, bis die Obergrenze erreicht ist.

&#91;embedded content: Auswahl · 6 Schritte, die Datenobjekte je Schritt\]

Links steht, was passiert, rechts, welches Datenobjekt dabei entsteht oder als Eingabe hineinfließt. Nur Schritt 3 braucht das LLM; Steckbriefe und Presets kommen von Menschen.

„Reihum“ funktioniert wie das Wählen von Mannschaften im Schulsport: Jede Gruppe (z. B. jeder Ressourcentyp) bekommt nacheinander einen Platz. Innerhalb einer Gruppe entscheidet ein fachliches Kriterium, bei Gleichstand die ID. Ohne „reihum“ hätte beim BSI das Alphabet entschieden, denn 24 von 30 Kandidaten haben dieselbe Schutzbedarfs-Summe.

| Quelle | Vorfilter | Gruppe beim Ranking | Sortierung in der Gruppe | Plätze |
| --- | --- | --- | --- | --- |
| BSI Grundschutz++ | MUSS oder SOLLTE, Schutzniveau normal-SdT, Praktiken DLS, BER, DET, KONF, BES, ARCH | Ressourcentyp | Summe Vertraulichkeit + Integrität + Verfügbarkeit (0–6), absteigend | 12 |
| CIS AWS v7 | Kapitel 2 IAM, 3 Storage, 4 Logging | Ressourcentyp | Level 1 vor Level 2, dann Automated vor Manual | 12 |
| DSGVO | Kapitel II–V (Art. 5–49) | Kapitel | Bußgeldstufe: bis 4 % vor bis 2 % (Art. 83) | 12 |
| SDM | Bausteine Löschen (M60), Trennen (M50), Zugriffe regeln (M51); Ebenen Daten und Systeme | Baustein | Ebene Daten vor Systeme | 8 |

**Ergebnis:** die Auswahlliste `data/knowledge_base/selection_arch.json` bzw. `selection_spec.json`. Jeder Eintrag nennt Anforderung, Begründung, Ressourcentypen, Rang und ob er gesetzt (`pinned`) ist. Die Liste ist ein **Kontrollpunkt**: Ein Mensch sieht im Git-Diff des Pull Requests, was sich gegenüber dem letzten Build geändert hat, bevor teure Schritte folgen.

## 6. Build, Schritt 3: Prüfregeln formulieren

Aus jeder ausgewählten Anforderung formuliert das LLM genau eine Prüfregel. Bevor sie in den Katalog darf, muss sie ein Gate mit drei Prüfungen bestehen.

&#91;embedded content: Prüfregel-Fabrik · Draft-Pattern mit Gate\]

Zwei Stränge laufen zusammen: links der Entwurf des LLM, rechts die Felder, die der Code schon kennt. Erst wenn das Gate beide zusammen akzeptiert, wird daraus eine `Rule` im Katalog.

### Was das LLM schreibt, was der Code ergänzt

Das LLM füllt das Formular `formulate_rule` (Modell `RuleDraft`). Der Code macht daraus eine `Rule`, indem er die Felder ergänzt, die er sicher kennt.

| Feld | Wer füllt es | Wozu |
| --- | --- | --- |
| `source_quote` | LLM, vom Code geprüft | Wörtlicher Satz aus der Norm: Herkunftsnachweis der Regel |
| `title` | LLM | Kurze deutsche Überschrift für den Report |
| `compliant_if` | LLM | Maßstab für PASS: Was muss in der Eingabe stehen? |
| `violation_if` | LLM | Maßstab für FAIL: Wann ist ein Verstoß belegt? |
| `recommendation` | LLM | Standard-Abhilfe, die im Audit auf die Eingabe zugeschnitten wird |
| `cross_references` | LLM, vom Code geprüft | Bezüge auf andere Quellen; immer markiert als `ai_suggested`, ohne Einfluss auf den Status |
| `id` | Code | Stabiler Schlüssel: `<SPEC oder ARCH>-<QUELLE>-<Anforderungs-ID>` |
| `audit_type`, `source` | Code | In welchen Katalog die Regel gehört, aus welchem Regelwerk sie stammt |
| `primary_anchor` | Code | Die Fundstelle, übernommen aus der Extraktion – nie vom LLM |
| `selection_rationale`, `cfn_resource_types`, `rank`, `pinned` | Code, aus der Auswahlliste | Warum die Regel ausgewählt wurde und wofür sie gilt |

Warum zwei Kriterien (`compliant_if` und `violation_if`) statt einem? Sie schaffen eine dritte Zone: Trifft keines eindeutig zu, lautet das Urteil WARN. Und weil die Kriterien einmal zur Build-Zeit festgeschrieben werden, muss das LLM die Norm nicht in jedem Audit neu auslegen.

So sieht eine fertige Prüfregel aus (gekürzt):

```json
{
  "id": "ARCH-CIS-3.1.4",
  "primary_anchor": "CIS AWS v7.0.0 3.1.4",
  "source_quote": "Ensure that S3 is configured with 'Block Public Access' enabled",
  "title": "S3 Block Public Access aktiv",
  "compliant_if": "Jeder S3-Bucket hat alle vier Block-Public-Access-Einstellungen aktiv.",
  "violation_if": "Ein Bucket deaktiviert mindestens eine Einstellung.",
  "recommendation": "Am Bucket BlockPublicAccess.BLOCK_ALL setzen.",
  "cfn_resource_types": ["AWS::S3::Bucket"],
  "rank": 3,
  "pinned": false
}
```

### Das Gate: drei Prüfungen

| Prüfung | Frage | Schützt vor |
| --- | --- | --- |
| Schema | Passt das JSON zum Pydantic-Modell `Rule`? | kaputten oder unvollständigen Regeln |
| Anker | Gibt es Primäranker und jeden Querverweis wirklich in `data/extracted/`? | erfundenen Fundstellen wie „DET.3.99“ |
| Zitat | Steht `source_quote` wörtlich im Text **genau der verankerten Anforderung**? | erfundenem oder umformuliertem Normtext |

Der dritte Punkt ist subtil: Ein Zitat aus Art. 5 darf eine Regel zu Art. 32 nicht „belegen“. Deshalb vergleicht das Gate nur mit dem Text der einen Anforderung, nicht mit der ganzen Quelle. Fällt eine Regel durch, bricht der Build ab, und die alte Wissensbasis bleibt aktiv.

### Ergebnis: der Regelkatalog

Alle Regeln einer Audit-Art landen in `rules_arch.json` bzw. `rules_spec.json` (Modell `RuleCatalog`). Dazu kommen `source_versions` (welche Normfassung, z. B. CIS v7.0.0 oder der BSI-Commit) und `model_id` (welches Modell formuliert hat). Die Datei hat **bewusst keinen Zeitstempel**: Ein unveränderter Build soll keinen Git-Diff erzeugen, damit der Reviewer nur echte Änderungen sieht.

## 7. Build, Schritt 4–5: Golden Archetypes und Preset-Gate

Zur Laufzeit generiert GovGuard keine Infrastruktur. Alle Vorlagen entstehen vorher im Build und müssen zwei unabhängige Prüfungen bestehen (ADR 0003).

### Die drei Archetypen

| Archetyp | Wofür | AWS Solutions Constructs | Pflicht-Ressourcentypen |
| --- | --- | --- | --- |
| ARCH-01 Sync REST | Synchrone Fachanwendung mit API und Datenbank | `aws-apigateway-lambda`, `aws-lambda-dynamodb` | API Gateway RestApi, Lambda, DynamoDB |
| ARCH-02 Antragseingang | Antrag per API annehmen, asynchron prüfen und ablegen | `aws-apigateway-lambda`, `aws-lambda-sqs`, `aws-sqs-lambda`, `aws-lambda-s3` | API Gateway RestApi, Lambda, SQS Queue, S3 Bucket |
| ARCH-03 Audit-Log-Archiv | Protokolle per API annehmen und unveränderbar archivieren | `aws-apigateway-lambda`, `aws-lambda-kinesisfirehose`, `aws-kinesisfirehose-s3` | API Gateway RestApi, Lambda, Kinesis Firehose, S3 Bucket mit Object Lock |

Solutions Constructs sind vorgefertigte CDK-Bausteine von AWS, die sichere Standards (Verschlüsselung, Logging) mitbringen. Das LLM baut also nicht frei, sondern aus bewährten Teilen.

### Vom Steckbrief zur Freigabe

1. Ein Mensch pflegt je Archetyp einen **Steckbrief** in `data/archetype_profiles.json`: Zweck, Constructs, Pflicht-Ressourcentypen und die für die Relevanz genutzten `resource_types` (Pflicht-Typen plus IAM-Rolle, KMS-Schlüssel, Log-Gruppe).
2. Das LLM schreibt daraus Python-CDK-Code.
3. `cdk synth` erzeugt deterministisch ein CloudFormation-Template. Geprüft wird das **Template, nicht der Code**, denn erst dort sieht man, ob ein Bucket wirklich verschlüsselt ist.
4. Drei Bedingungen müssen alle erfüllt sein:
   1. **Struktur-Soll:** Alle Pflicht-Ressourcentypen sind im Template. Sonst könnte das LLM eine „perfekt sichere“ Architektur liefern, die einfach die Datenbank weglässt.
   2. **Compliance-Soll:** Das Architektur-Audit von GovGuard ergibt nur PASS oder N/A. Schon ein WARN verhindert die Freigabe. N/A darf nur der Code setzen.
   3. **cdk-nag:** Das regelbasierte Werkzeug cdk-nag (Regelpaket AwsSolutions) meldet keine Errors, außer erlaubten Ausnahmen.
5. Bei einer Beanstandung korrigiert das LLM, **höchstens dreimal**. Danach bricht der Build ab. Das verhindert Endlosschleifen und unkontrollierte Kosten.

&#91;embedded content: Freigabe-Schleife · 3 Prüfungen, höchstens 3 Runden\]

Die drei Prüfungen laufen auf demselben Template. Nur eine davon nutzt ein LLM; Struktur-Check und cdk-nag sind rein deterministisch. Beanstandungen gehen als Korrekturauftrag zurück an das LLM, bis die dritte Runde erreicht ist.

Warum zwei Prüfer? Die Audit-Engine nutzt selbst ein LLM. Gäbe sie allein frei, prüfte ein LLM die Arbeit eines LLM. cdk-nag ist rein regelbasiert und damit unabhängig: ein **Vier-Augen-Prinzip** für Infrastructure as Code.

### Ausnahmen nur von Menschenhand

Mit Solutions Constructs sind null cdk-nag-Errors nicht erreichbar, weil CDK eigene Hilfsressourcen erzeugt. Erlaubte Ausnahmen stehen in der Allowlist `data/nag_allowlist.json`: je Eintrag die Regel-ID, ein Pfad-Muster und eine deutsche Begründung. Drei Regeln sichern das ab (ADR 0007):

- Nur ein **Mensch** schreibt die Liste.
- Nur der **Code** wendet sie an.
- Der LLM-Code darf kein `acknowledge(...)` enthalten. Sonst könnte das LLM die Prüfung einfach abschalten.

### Was gespeichert wird

Jeder freigegebene Archetyp landet mit Code, Template und einem **Freigabe-Nachweis** (`Approval`) in `archetypes.json`: Audit-Report, Liste der cdk-nag-Errors (muss leer sein), angewendete Ausnahmen, Anzahl Runden. Dazu kommt `rules_arch_sha256`, der Hash des Regelkatalogs, gegen den freigegeben wurde. Ändert sich der Katalog, passt der Hash nicht mehr, und die alte Freigabe ist erkennbar wertlos.

### Das Preset-Gate: der Abschlusstest

Zum Schluss muss die neue Wissensbasis vier bekannte Beispiele (Presets) richtig bewerten. Jedes Preset ist ein Ordner mit Eingabedatei und `preset.json`, das Soll legt ein **Mensch** fest:

- den erwarteten Gesamtstatus,
- Pflicht-Befunde, z. B. „DSGVO Art. 9 muss FAIL sein“ (genau dieser Status, nicht „mindestens so schlecht“),
- bei Spezifikationen ohne FAIL den erwarteten Archetyp.

Warum von Hand? Würde man das Soll aus einem früheren Lauf übernehmen, prüfte das System nur, ob es sich selbst wiederholt. Ein solcher **zirkulärer Test** wird auch grün, wenn beide Läufe falsch sind. Pflicht-Befunde sichern zusätzlich, dass der Gesamtstatus aus dem richtigen Grund entsteht. Alle übrigen Befunde bleiben frei, sonst wäre der Test bei jeder harmlosen Formulierungsänderung rot.

Nur wenn alle Gates grün sind, öffnet der Workflow einen **Pull Request** mit `rules_spec.json`, `rules_arch.json` und `archetypes.json`. Live geht die Wissensbasis erst nach dem Merge (Kapitel 8).

## 8. Deployment: GovGuard prüft sich selbst

Es gibt genau **einen Weg in die Produktion**: den GitHub-Workflow `deploy.yml`. Er startet bei jedem Push auf `main`, also auch beim Merge eines Wissensbasis-Pull-Requests.

1. GitHub Actions meldet sich per **OIDC** bei AWS an und erhält kurzlebige Rechte. Dauerhafte Zugangsschlüssel liegen nicht in GitHub.
2. `cdk synth` erzeugt das Template des eigenen GovGuard-Stacks (Ordner `infra/`).
3. cdk-nag prüft es, mit derselben Allowlist wie bei den Archetypen.
4. Die Audit-Engine prüft das eigene Template gegen den Architektur-Katalog. Ein FAIL oder WARN **blockiert** das Deployment.
5. `cdk deploy` rollt nach eu-central-1 (Frankfurt) aus und lädt die Wissensbasis aus dem Repo nach S3.

Das nennt man **Dogfooding**: GovGuard beweist an sich selbst, dass seine Regeln erfüllbar sind. Weil Selbst-Audit und Upload im selben Lauf passieren, prüft das Selbst-Audit immer genau die Wissensbasis, die danach live geht.

Für dich als Entwickler heißt das: Eine geänderte Wissensbasis wird nie direkt nach S3 kopiert. Sie geht immer den Weg Build → Pull Request → Review → Merge → `deploy.yml`.

## 9. Laufzeit: ein Audit von der Anfrage bis zum Report

Ein Audit ist genau ein Bedrock-Aufruf, eingerahmt von Code, der vorher sortiert und nachher streng prüft. Kommt nach einem Wiederholungsversuch keine gültige Antwort zustande, antwortet GovGuard ehrlich mit einem Fehler statt mit einem ungeprüften Report (**Fail closed**).

### Die Schritte

1. **Anfrage:** Ein Client (Streamlit-UI oder CI-Pipeline) ruft `POST /audit/spec` oder `POST /audit/architecture` auf, signiert per AWS SigV4. Ist die Eingabe leer oder länger als 100.000 Zeichen, antwortet die API mit 400.
2. **Wissensbasis bereitstellen:** Beim Kaltstart lädt die Lambda-Funktion die Kataloge einmal aus S3 in den Speicher. Weitere Aufrufe nutzen sie direkt.
3. **Trace bauen:** Der Handler erzeugt eine Rückverfolgungs-Kennung: `audit_id`, Hash der Eingabe, Hash des Katalogs und der Git-Commit des Deploys.
4. **Vorab-N/A (nur CloudFormation-JSON):** Der Code liest die Ressourcentypen des Templates. Jede Prüfregel, deren Typen dort nicht vorkommen, bekommt sofort N/A und geht nicht ans Modell. Beispiel: kein S3-Bucket im Template → alle S3-Regeln N/A.
5. **LLM-Aufruf:** Alle übrigen Prüfregeln gehen zusammen mit der Eingabe an Claude Haiku 4.5 über das EU-Profil von Bedrock. Das Modell muss das Formular `submit_audit` ausfüllen: je Regel `rule_id`, Status, Beleg, Begründung, Empfehlung.
6. **Validieren (Code):** Drei Prüfungen, siehe unten.
7. **Anreichern (Code):** Aus jedem `FindingDraft` wird ein `Finding`. Titel, Primäranker und Querverweise schlägt der Code über die `rule_id` im Katalog nach. Das LLM muss sie nicht wiederholen und kann sie deshalb nicht verfälschen.
8. **Gesamtstatus (Code):** Der schlechteste Einzelstatus gewinnt: FAIL vor WARN vor PASS vor N/A. Sind alle Befunde N/A, ist auch der Gesamtstatus N/A.
9. **Protokollieren:** Der Handler schreibt genau ein `AuditEvent` in CloudWatch Logs, auch bei Fehlern (Kapitel 10 und 12).
10. **Antwort:** Der `AuditReport` geht an den Client.

&#91;embedded content: Laufzeit-Audit · 8 Schritte und ihre Datenobjekte\]

Das Bild fasst die Schritte zu acht Stationen zusammen und zeigt die Datenobjekte, die dabei hinein- oder herausfließen. Die rote Schleife ist der einzige Wiederholungsversuch; danach gilt Fail closed.

### Die Validierungskette

| Prüfung | Frage | Schützt vor |
| --- | --- | --- |
| Schema | Passt die Antwort zum Pydantic-Modell `AuditResponse`? | kaputtem JSON, erfundenen Status-Werten |
| Vollständigkeit | Kommt jede gesendete `rule_id` genau einmal vor, und keine unbekannte? Bei CloudFormation: kein N/A vom Modell? | vergessenen oder erfundenen Prüfregeln; weggeredeten Regeln |
| Beleg | Ist ein Beleg da, wo er Pflicht ist, und steht er wörtlich in der Eingabe? | halluzinierten Belegen |

Schlägt eine Prüfung fehl, schickt Pydantic AI die Fehlermeldung **einmal** zurück ans Modell. Viele Fehler behebt das LLM, wenn es sieht, was falsch war. Scheitert auch der zweite Versuch, antwortet die API mit HTTP 502. Mehr Versuche würden das Zeitlimit von 29 Sekunden des API Gateway sprengen.

### Pflichtfelder je Status

| Status | Bedeutung | Beleg | Empfehlung |
| --- | --- | --- | --- |
| PASS | Einhaltung belegt | Pflicht | – |
| WARN | nicht entscheidbar, Prüfbedarf | optional | Pflicht |
| FAIL | Verstoß belegt | Pflicht | Pflicht |
| N/A | nicht anwendbar | optional | – |

Ein Beleg zählt nur, wenn `contains_quote()` ihn findet: Er muss mindestens 15 Zeichen lang sein (ein Zitat wie „S3“ beweist nichts) und nach Normalisierung wörtlich in der Eingabe stehen. Normalisiert werden Leerzeichen, Anführungszeichen und EUR-Lex-Marker; Groß- und Kleinschreibung bleibt, denn „wörtlich“ heißt wörtlich. Build und Laufzeit nutzen dieselbe Funktion, damit ein Zitat nicht im einen Teil besteht und im anderen scheitert.

### Danach: Archetyp-Auswahl

Hat das Spec-Audit kein FAIL, kann der Client `POST /archetype/select` mit Spezifikation und Report aufrufen. Enthält der Report ein FAIL, lehnt die API mit 422 ab. Sonst wählt das LLM über das Formular `select_archetype` aus einer geschlossenen Liste: ARCH-01, ARCH-02, ARCH-03 oder **NONE**. NONE ist eine erlaubte Antwort; ohne sie müsste das LLM auch bei unpassender Spezifikation irgendeinen Archetyp nehmen. Das LLM liefert nur die ID und eine Begründung, den CDK-Code und das Template lädt der Code aus `archetypes.json`.

### HTTP-Antworten im Überblick

| Code | Wann |
| --- | --- |
| 200 | Report bzw. Archetyp geliefert |
| 400 | Eingabe fehlt oder ist länger als 100.000 Zeichen |
| 403 | SigV4-Signatur fehlt oder ist falsch |
| 422 | Archetyp-Auswahl angefragt, obwohl der Report ein FAIL enthält |
| 429 | Throttling greift |
| 502 | LLM-Antwort auch nach dem zweiten Versuch ungültig |
| 504 | Länger als 29 Sekunden |

## 10. Wo welche Daten liegen

Die Wissensbasis lebt im Git-Repo und wird per Deploy nach S3 kopiert. Eingaben und Reports speichert GovGuard nicht; im Protokoll stehen nur Hashes und Status.

| Ort | Inhalt | Wer schreibt | Wer liest |
| --- | --- | --- | --- |
| `data/sources/` | Quell-PDFs von CIS, DSGVO, SDM (BSI-OSCAL lädt der Build per Commit-SHA) | Mensch | Quellen-Adapter |
| `data/extracted/<quelle>.json` | Alle Anforderungen einer Quelle, normalisiert (`ExtractedSource`) | Quellen-Adapter | Vorfilter, LLM-Klassifikation, Anker- und Zitat-Gate |
| `data/knowledge_base/selection_*.json` | Auswahlliste: welche Anforderungen in den Katalog kommen (`Selection`) | Build (Klassifikation + Ranking) | Mensch im Pull Request, Formulierung der Prüfregeln |
| `data/knowledge_base/rules_*.json` | Regelkataloge für Spec und Architektur (`RuleCatalog`) | Build, nach dem Gate | Lambda, Selbst-Audit, Preset-Gate |
| `data/knowledge_base/archetypes.json` | Freigegebene Archetypen mit Code, Template, Freigabe-Nachweis | Build | Lambda bei `/archetype/select`, Preset-Gate |
| `data/archetype_profiles.json` | Steckbriefe der drei Archetypen | Mensch | Relevanzfilter, Archetyp-Build, Archetyp-Auswahl |
| `data/nag_allowlist.json` | Erlaubte cdk-nag-Ausnahmen mit Begründung | Mensch | Archetyp-Freigabe, Deploy des GovGuard-Stacks |
| `data/presets/<id>/` | Testeingabe + `preset.json` mit Soll | Mensch | Preset-Gate, Demo in der UI |
| S3 (eu-central-1) | Kopie der Wissensbasis | `deploy.yml` | Lambda beim Kaltstart |
| Lambda-Speicher | Geladene Wissensbasis | Lambda beim Kaltstart | jedes Audit |
| CloudWatch Logs | Ein `AuditEvent` je Aufruf, KMS-verschlüsselt, 365 Tage | Lambda-Handler | Auditor über Logs Insights |
| CloudTrail | AWS-API-Aufrufe, auch die Bedrock-Verarbeitungsregion | AWS | Auditor |
| Git (`main`) | Historie aller Wissensbasis-Versionen, geschützt per Branch Protection | Pull Requests | Reviewer, Rückverfolgung |

### Der Lebensweg einer Prüfregel in einem Satz je Station

1. Eine Anforderung steht in einer Quelle, z. B. CIS 3.1.4.
2. Der Adapter extrahiert sie nach `data/extracted/cis.json`.
3. Vorfilter, LLM und Ranking setzen sie auf die Auswahlliste.
4. Das LLM formuliert eine Prüfregel, das Gate prüft sie, sie landet in `rules_arch.json`.
5. Die Archetypen werden gegen diese Regel freigegeben, das Preset-Gate wird grün, ein Pull Request entsteht.
6. Nach dem Merge kopiert `deploy.yml` den Katalog nach S3.
7. Die Lambda lädt ihn und schickt die Regel in jedem Architektur-Audit ans LLM.
8. Das Urteil erscheint als Befund im Report beim Nutzer und als Status-Eintrag im Audit-Protokoll.

## 11. Die Geschäftsregeln auf einen Blick

Diese Regeln gelten immer. Die rechte Spalte zeigt, welches Risiko die Regel abfängt.

| Bereich | Regel | Verhindert |
| --- | --- | --- |
| Katalog | Höchstens 24 Architektur-Regeln (12 BSI + 12 CIS) und 20 Spec-Regeln (12 DSGVO + 8 SDM) | Überforderung des Modells, Zeitüberschreitung |
| Katalog | Jede Architektur-Regel betrifft mindestens einen Ressourcentyp der Archetypen | Regeln, die nur Dauer-WARN oder N/A liefern |
| Katalog | Höchstens 4 gesetzte Plätze je Audit-Art, nur aus Pflicht-Befunden der Presets | einen auf die Tests zugeschnittenen Katalog |
| Katalog | Gleiche Eingabe ergibt dieselbe Auswahl und Reihenfolge | nicht reproduzierbare Builds |
| Prüfregel | Primäranker und ID setzt der Code, nie das LLM | erfundene Fundstellen |
| Prüfregel | `source_quote` steht wörtlich im Text der verankerten Anforderung | halluzinierten Normtext |
| Prüfregel | Querverweise müssen existieren und beeinflussen nie den Status | Scheinpräzision |
| Audit | Jede gesendete Prüfregel hat genau einen Befund | still verlorene oder erfundene Regeln |
| Audit | PASS und FAIL brauchen einen wörtlichen Beleg aus der Eingabe | halluzinierte Belege |
| Audit | Fehlende Information ergibt WARN, nie FAIL | Verstöße aus Schweigen |
| Audit | Bei CloudFormation-JSON setzt nur der Code N/A | weggeredete unbequeme Regeln |
| Audit | Gesamtstatus = schlechtester Einzelstatus (FAIL > WARN > PASS > N/A) | geschönte Gesamturteile |
| Audit | Genau ein Retry, danach HTTP 502 | ungeprüfte Reports, Zeitüberschreitung |
| Archetyp | Auswahl nur bei Report ohne FAIL, sonst HTTP 422 | Architekturvorschlag für eine rechtswidrige Spezifikation |
| Archetyp | Freigabe nur mit PASS oder N/A, Pflicht-Typen vorhanden, cdk-nag ohne Errors außer Allowlist | unsichere oder unvollständige Vorlagen |
| Archetyp | Höchstens 3 Korrekturrunden | Endlosschleifen und Kosten |
| Archetyp | Ausnahmen schreibt nur ein Mensch, der Code wendet sie an | dass das LLM die Prüfung abschaltet |
| Build | Nur bei grünen Gates entsteht ein Pull Request; sonst bleibt die alte Wissensbasis aktiv | kaputte Wissensbasis in Produktion |
| Build | Archetypen passen per Hash zum aktuellen Regelkatalog | veraltete Freigaben |
| Deploy | Einziger Weg in Produktion ist `deploy.yml`, mit Selbst-Audit ohne FAIL und WARN | ungeprüfte Änderungen am eigenen Stack |

## 12. Datenschutz, Nachvollziehbarkeit und bewusste Grenzen

GovGuard kann jedes Urteil bis zur Normfassung zurückverfolgen, ohne die Eingabe selbst zu speichern.

### Datenschutz

- **Region:** Alle persistenten Daten liegen in eu-central-1 (Frankfurt). Bedrock wird über das EU-Inferenzprofil `eu.` aufgerufen, die Verarbeitung bleibt also in EU-Regionen. Weltweite Profile (`global.`) sind per IAM-Policy gesperrt (ADR 0001).
- **Datenminimierung im Protokoll:** Das `AuditEvent` enthält IDs, Hashes, Modell und den Status je Prüfregel. Kein Eingabetext, keine Belege, keine Begründungen, denn die zitieren die Eingabe (ADR 0006). API Gateway loggt keine Request-Bodies.
- **Demo-UI:** Die Streamlit-Oberfläche läuft für die Demo in den USA. Deshalb dürfen dort nur fiktive Daten eingegeben werden; die UI weist darauf hin (ADR 0004).

### Rückverfolgung eines Urteils

1. Das `AuditEvent` in CloudWatch nennt `catalog_sha256` und `kb_commit`.
2. Der Commit führt im Git-Repo zu genau der Katalogdatei, die im Einsatz war; der Hash bestätigt sie.
3. Die Katalogdatei nennt in `source_versions` die Normfassungen, z. B. CIS v7.0.0 und den BSI-Commit.
4. Die Prüfregel nennt ihren Primäranker und ihr Normzitat.
5. CloudTrail belegt zusätzlich, in welcher Region Bedrock den Aufruf verarbeitet hat.

&#91;embedded content: Rückverfolgung · vom Protokoll bis zur Norm\]

Jedes Glied der Kette ist ein Feld, das der Code setzt. Die Eingabe selbst kommt in der Kette nicht vor: Sie steht nur als Hash im Trace.

### Bewusste Grenzen des MVP

- **Umfang:** höchstens 24 bzw. 20 Prüfregeln, Eingaben bis 100.000 Zeichen, drei Archetypen.
- **Keine kontoweiten Pflichten:** Root-MFA oder Passwort-Policy sind an keinem Template entscheidbar. Dafür gibt es Werkzeuge wie Prowler oder AWS Security Hub.
- **N/A durch Code nur für CloudFormation-JSON:** YAML-Templates und Terraform behandelt GovGuard wie Freitext; dort entscheidet das LLM über N/A.
- **SDM ohne Baustein Protokollieren (M43):** eigenes ID-Schema, Aufwand zu hoch. Protokollierung deckt das Architektur-Audit über BSI und CIS ab.
- **DSGVO-Einheit Artikel:** Art. 5 ergibt nur eine Prüfregel, obwohl er sechs Grundsätze enthält. Die Grundsätze kommen über das SDM in den Katalog.
- **Protokoll nicht revisionssicher:** Wer die Log-Gruppe löschen darf, kann löschen. In Produktion übernimmt das ARCH-03 mit S3 Object Lock.
- **Kein X-Ray:** würde eine weitere cdk-nag-Ausnahme brauchen.

Wie GovGuard über diese Grenzen hinauswächst, beschreibt `AUSBAU.md` (Map-Reduce über Teilkataloge, Faktenblätter für lange Dokumente, asynchrone Jobs). Der Leitgedanke bleibt: *Skalieren durch Aufteilen, nicht durch Weglassen.* Vollständigkeit und Zitatpflicht gelten in jeder Ausbaustufe.

### Wie du weiterliest

| Dokument | Lies es, wenn du … |
| --- | --- |
| `CONTEXT.md` | einen Begriff genau nachschlagen willst |
| `SPEC.md` | User Stories und Akzeptanzkriterien brauchst |
| `ARCHITECTURE.md` | Komponenten, Code-Struktur und Endpunkte im Detail suchst |
| `DESIGN.md` | Felder und Funktionssignaturen implementierst (verbindlich) |
| `DATA_MODEL_EXPLAINED.md` | zu jedem einzelnen Feld wissen willst, wer es füllt und warum |
| `adr/0001` bis `adr/0007` | verstehen willst, warum eine Entscheidung so gefallen ist |
| `AUSBAU.md` | über Skalierung nach dem MVP nachdenkst |
