# Fachkonzept (Kurzfassung): GovGuard im Demo-Stand

_Stand 19.10.2026. Diese Systembeschreibung ist zugleich das Preset `spec-govguard`: GovGuard prüft
sie mit seinem eigenen Spec-Audit, der Report steht in der Galerie. Begriffe: [CONTEXT.md](../CONTEXT.md),
Entscheidungen: [adr/](adr/), Technik: [ARCHITECTURE.md](ARCHITECTURE.md)._

## 1 Ausgangslage und Zweck

Bevor eine Behörde ein IT-Verfahren in die Cloud bringt, prüfen Fachleute zwei Dokumente von Hand.
Die Spezifikation beschreibt fachlich, was das Verfahren tut und welche Daten es verarbeitet.
Die Architektur beschreibt technisch, aus welchen Cloud-Diensten es besteht und wie sie eingestellt sind.
Geprüft wird gegen Regelwerke, vor allem die Datenschutz-Grundverordnung (DSGVO) und den IT-Grundschutz.
Die DSGVO ist das EU-Gesetz zum Schutz personenbezogener Daten.
Das Standard-Datenschutzmodell (SDM) der Datenschutzkonferenz übersetzt die DSGVO in konkrete Maßnahmen.
Der IT-Grundschutz des BSI, des Bundesamts für Sicherheit in der Informationstechnik, beschreibt
Sicherheitsanforderungen an IT-Systeme. Die Prüfung von Hand dauert Tage und hängt von der Erfahrung
der prüfenden Person ab.

GovGuard ist ein Compliance-Copilot für diese Vorprüfung. Compliance heißt: Ein System hält die für
es geltenden Regeln ein. GovGuard prüft eine Spezifikation gegen DSGVO und SDM (Spec-Audit) und eine
Architektur gegen BSI IT-Grundschutz, BSI C5, CIS AWS und AWS FSBP (Architektur-Audit). Das Ergebnis
ist ein Audit-Report: je Prüfregel ein Befund mit Status, wörtlichem Beleg und Empfehlung. GovGuard
ersetzt die Fachleute nicht, sondern zeigt ihnen in Minuten, wo sie genauer hinsehen müssen.

## 2 Geltungsbereich und Abgrenzung

Diese Beschreibung gilt für den Demo-Stand, der zur Präsentation am 26.10.2026 läuft. Der Demo-Stand
ist eine Web-Anwendung auf Streamlit Community Cloud, einem kostenlosen Hosting-Dienst für Python-Apps.
Das Sprachmodell, das die Prüfregeln auf die Eingabe anwendet, läuft beim Anbieter Groq. Ein
Sprachmodell (LLM) ist eine KI, die Text liest und Text oder strukturierte Daten zurückgibt.

Nicht zum Umfang gehören:

- echte personenbezogene Daten: Der Demo-Stand verarbeitet nur fiktive Beispiele;
- eine Rechtsberatung: Ein Befund ist ein Hinweis für die Fachleute, kein Rechtsgutachten;
- Golden Archetypes, also vorab geprüfte Referenzarchitekturen: Sie sind entworfen, aber nicht gebaut;
- ein Betrieb auf AWS mit Programmierschnittstelle für Pipelines: Er ist als Ausbau beschrieben
  ([AUSBAU.md](AUSBAU.md)), aber aus Budgetgründen nicht gebaut.

## 3 Rollen

| Rolle | Aufgabe |
|---|---|
| Besucher (z. B. Recruiter) | sieht in der Galerie gespeicherte Audits an, ohne Anmeldung |
| Prüfende Person | startet mit dem Demo-Passwort ein eigenes Audit und lädt den Report herunter |
| Projektbetreiber | baut die Wissensbasis, pflegt die Presets, verwaltet Passwort und API-Schlüssel |
| Groq | Dienstleister für das Sprachmodell (Inferenz) |
| Streamlit Community Cloud | Dienstleister für das Hosting der Web-Anwendung |

Inferenz bedeutet: Das Sprachmodell berechnet eine Antwort auf eine Anfrage.

## 4 Fachliche Anforderungen

- **F1 Spec-Audit:** Die prüfende Person gibt eine Spezifikation als Text, Markdown oder OpenAPI ein.
  GovGuard bewertet sie gegen alle 151 Prüfregeln aus DSGVO und SDM.
- **F2 Architektur-Audit:** Die prüfende Person gibt eine Architektur als Freitext oder als
  CloudFormation-Template ein. Ein CloudFormation-Template ist eine Datei, die AWS-Ressourcen als
  Bauplan beschreibt. GovGuard bewertet die Architektur gegen die Prüfregeln aus BSI, CIS und FSBP.
- **F3 Galerie:** Die Galerie zeigt gespeicherte Audit-Reports zu Presets, je neben dem geprüften
  Dokument. Ein Preset ist eine Beispiel-Eingabe mit festgelegtem Soll-Ergebnis. Weicht der Report
  vom Soll ab, zeigt die Galerie die Abweichung.
- **F4 Report:** Der Report nennt Gesamtstatus und je Prüfregel genau einen Befund mit Normanker,
  Status, Begründung, Beleg und Empfehlung. Ein Normanker ist die Fundstelle im Regelwerk, etwa
  „DSGVO Art. 9“. Die prüfende Person kann den Report als JSON herunterladen.
- **F5 Wissensbasis:** Der Projektbetreiber erzeugt die Prüfregeln von Hand angestoßen aus den
  öffentlichen Normtexten. Jede Prüfregel zitiert ihre Quelle wörtlich, und ein Programm prüft das.

## 5 Geschäftsregeln

- **G1 Bounded Catalog:** Jedes Audit bewertet alle Prüfregeln seiner Audit-Art, keine wird
  ausgelassen. Der Bounded Catalog ist diese feste, beim Bau der Wissensbasis bestimmte Menge.
- **G2 Status:** Jeder Befund hat einen von vier Status.
  PASS heißt: Die Eingabe belegt, dass die Prüfregel eingehalten ist.
  WARN heißt: Aus der Eingabe ist es nicht entscheidbar, es besteht Prüfbedarf.
  FAIL heißt: Die Eingabe belegt einen Verstoß.
  N/A heißt: Die Prüfregel betrifft keinen Dienst, der in der Architektur vorkommt.
- **G3 Gesamtstatus:** Der Gesamtstatus ist der schlechteste Status aller Befunde (FAIL vor WARN vor PASS).
- **G4 FAIL nur bei festgelegtem Verstoß:** Eine Spezifikation ist eine offene Welt. Das bedeutet:
  Was sie nicht erwähnt, kann anderswo geregelt sein. Fehlt eine Angabe, ist der Befund daher WARN.
  FAIL gibt es nur, wenn der Text etwas festlegt, das der Prüfregel widerspricht, auch einen
  erklärten Verzicht. Ein CloudFormation-Template dagegen ist eine geschlossene Welt: Was fehlt,
  gilt als Standardwert und kann FAIL sein.
- **G5 Wörtlicher Beleg:** Das Sprachmodell nennt zu PASS und FAIL nur die Zeilen der Eingabe.
  Den Beleg schneidet das Programm selbst aus der Eingabe aus. Fehlen gültige Zeilen, stuft das
  Programm den Befund auf WARN herab, und der ursprüngliche Status bleibt sichtbar.
- **G6 FAIL-Prüfer:** In der offenen Welt prüft ein zweiter Aufruf des Sprachmodells jedes FAIL nur
  anhand von Verstoßkriterium und Belegzeilen. Bestätigt er es nicht, wird es WARN. Fällt er aus,
  bleibt das FAIL ungeprüft stehen, denn der strengere Status ist der sichere.
- **G7 Fail closed:** Fail closed bedeutet: Im Zweifel liefert das System kein Ergebnis statt eines
  falschen. Ist die Antwort des Sprachmodells auch nach einer Wiederholung ungültig, bricht das Audit
  ab und zeigt eine Fehlermeldung, nie einen halben Report.
- **G8 Soll-Abweichung:** Weicht ein gespeicherter Report vom Soll seines Presets ab, wird das
  angezeigt und nicht so lange wiederholt, bis das Ergebnis passt.

## 6 Daten und Datenschutz

| Daten | Herkunft | Wohin | Wie lange |
|---|---|---|---|
| Eingabe (Spezifikation oder Architektur) | prüfende Person | Streamlit Community Cloud (USA), Groq (USA) | GovGuard speichert sie nicht; sie lebt nur in der Sitzung |
| Audit-Report mit Belegen | GovGuard | Browser der prüfenden Person | bis zum Ende der Sitzung oder als Download bei ihr |
| Rückverfolgung im Report | GovGuard | im Report | wie der Report |
| Galerie-Reports | Projektbetreiber | öffentliches Git-Repository | bis zur Löschung per Commit |
| Zugriffsdaten der Besucher (z. B. IP-Adresse) | Browser | Streamlit Community Cloud (USA) | nach den Bedingungen von Streamlit |

Eine Sitzung ist die Verbindung eines Browsers mit der Web-Anwendung; schließt man den Tab, endet sie.
Die Rückverfolgung verbindet einen Report mit seiner Eingabe, ohne sie zu speichern. Dafür steht im
Report nur ein Hash der Eingabe. Ein Hash ist ein Fingerabdruck aus Zeichen, aus dem sich der Text
nicht zurückrechnen lässt. Dazu kommen der Hash der Prüfregeln, der Git-Stand der Wissensbasis und
das verwendete Modell.

Hosting und Sprachmodell laufen in den USA. Die USA sind aus Sicht der DSGVO ein Drittland, also ein
Staat außerhalb der EU. Für diese Übermittlung legt der Demo-Stand keine eigenen Garantien nach
Art. 46 DSGVO fest. Deshalb gilt die Regel: nur fiktive Daten. Die Oberfläche weist vor jedem Audit
auf den Datenfluss in die USA hin. Was Groq und Streamlit selbst speichern und wann sie es löschen,
regeln deren Nutzungsbedingungen; GovGuard legt dafür keine eigene Löschfrist fest. Ein eigenes
Audit-Protokoll führt der Demo-Stand nicht. Für echte Daten ist ein anderer Weg festgelegt: das
Sprachmodell über AWS Bedrock in der EU (Region Frankfurt), mit Protokoll ohne Eingabetext.

## 7 Nicht-funktionale Anforderungen

- **Leistung:** Eine Eingabe hat höchstens 100.000 Zeichen; das prüft das Programm vor jedem Aufruf
  des Sprachmodells. Ein Audit dauert mit Groq ca. 20 bis 55 Sekunden (Messung 16.10.2026).
- **Kosten:** Ein Audit kostet mit Groq 2 bis 3 Cent. Die Leerlaufkosten sind 0 €. Leerlaufkosten
  sind Kosten, die ohne Nutzung allein durch Zeit entstehen. Das Passwort verhindert, dass Fremde
  Kosten auslösen.
- **Sicherheit:** Passwort und API-Schlüssel liegen nur in den Secrets von Streamlit, nicht im Code.
  Ohne eingerichtetes Passwort startet kein Audit.
- **Nachvollziehbarkeit:** Jeder Report nennt Modell, Wissensbasis und Eingabe-Hash. Jeder Eingriff
  des Programms in eine Antwort des Sprachmodells steht als Korrektur am Befund.
- **Prüfbarkeit:** Alle automatischen Tests laufen ohne AWS und ohne Groq.

## 8 Bekannte Grenzen

- **Schwankung:** Ein Sprachmodell antwortet nicht immer gleich. Im Spec-Audit änderten zwischen
  zwei Läufen mit Groq 42 von 151 Prüfregeln ihren Status. Der FAIL-Prüfer fängt falsche FAILs ab,
  PASS und WARN schwanken weiter.
- **Wissensbasis per KI:** Ob eine Anforderung prüfbar ist, hat beim Bau ein Sprachmodell beurteilt.
  Einzelne Fehlurteile sind möglich; Programme sichern nur Zitate, Fundstellen und Pflichtanker ab.
- **Umfang:** Protokollieren (SDM M43) und kontoweite AWS-Pflichten wie Root-MFA fehlen bewusst.
  Terraform und CloudFormation-YAML prüft GovGuard nur als Freitext.
