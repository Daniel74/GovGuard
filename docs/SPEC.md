# Fachkonzept (Kurzfassung): GovGuard im Demo-Stand

_Stand 19.10.2026. Diese Systembeschreibung ist zugleich ein Musterfall: GovGuard prüft sie selbst,
das Ergebnis steht in der Galerie._

_Begriffe: [CONTEXT.md](../CONTEXT.md) · Entscheidungen: [adr/](adr/) · Technik: [ARCHITECTURE.md](ARCHITECTURE.md)_

## 1 Ausgangslage und Zweck

Bevor eine Behörde ein IT-Verfahren in die Cloud bringt, prüfen Fachleute zwei Dokumente von Hand:

- Die **Spezifikation** beschreibt fachlich, was das Verfahren tut und welche Daten es verarbeitet.
- Die **Architektur** beschreibt technisch, aus welchen Cloud-Diensten es besteht.

Diese Prüfung dauert Tage und hängt von der Erfahrung der prüfenden Person ab.

Geprüft wird gegen Regelwerke:

- Die **DSGVO** ist das EU-Gesetz zum Schutz personenbezogener Daten.
- Das **Standard-Datenschutzmodell (SDM)** der Datenschutzkonferenz übersetzt die DSGVO in Maßnahmen.
- Der **IT-Grundschutz** des Bundesamts für Sicherheit in der Informationstechnik (BSI) beschreibt
  Sicherheitsanforderungen an IT-Systeme.

GovGuard ist ein digitaler Prüfassistent für diese Vorprüfung. Er prüft eine Spezifikation gegen
DSGVO und SDM und eine Architektur gegen BSI IT-Grundschutz, BSI C5, CIS AWS und AWS FSBP.

Ein solcher Prüflauf heißt Audit. Sein Ergebnis ist ein Audit-Report: je Prüfregel ein Befund mit
Status, wörtlichem Beleg und Empfehlung.

GovGuard ersetzt die Fachleute nicht. Er zeigt ihnen in Minuten, wo sie genauer hinsehen müssen.

## 2 Geltungsbereich und Abgrenzung

Diese Beschreibung gilt für den Demo-Stand, der zur Präsentation am 26.10.2026 läuft.

Der Demo-Stand ist eine Web-Anwendung auf Streamlit Community Cloud. Das ist ein kostenloser Dienst
zum Betrieb von Python-Anwendungen.

Die Prüfregeln wendet ein Sprachmodell beim Anbieter Groq an. Ein Sprachmodell ist eine KI, die Text
liest und Text oder strukturierte Daten zurückgibt.

Nicht zum Umfang gehören:

- **echte personenbezogene Daten:** Der Demo-Stand verarbeitet nur fiktive Beispiele.
- **Rechtsberatung:** Ein Befund ist ein Hinweis für die Fachleute, kein Rechtsgutachten.
- **Betrieb auf AWS** mit Programmierschnittstelle für automatische Abläufe: Er ist als Ausbau
  beschrieben ([AUSBAU.md](AUSBAU.md)), aber aus Budgetgründen nicht gebaut.

## 3 Rollen

| Rolle | Aufgabe |
|---|---|
| Besucher (z. B. Personalverantwortliche) | sieht in der Galerie gespeicherte Audits an, ohne Anmeldung |
| Prüfende Person | startet mit dem Demo-Passwort ein eigenes Audit und lädt den Audit-Report herunter |
| Projektbetreiber | baut die Wissensbasis, pflegt die Musterfälle, verwaltet Passwort und Zugangsschlüssel |
| Groq | Dienstleister für das Sprachmodell (Inferenz) |
| Streamlit Community Cloud | Dienstleister für den Betrieb der Web-Anwendung |

Inferenz bedeutet: Das Sprachmodell berechnet eine Antwort auf eine Anfrage.

## 4 Fachliche Anforderungen

**F1 Audit einer Spezifikation.** Die prüfende Person gibt eine Spezifikation als Text, Markdown oder
OpenAPI ein. GovGuard bewertet sie gegen alle 151 Prüfregeln aus DSGVO und SDM.

**F2 Audit einer Architektur.** Die prüfende Person gibt eine Architektur als Freitext oder als
CloudFormation-Vorlage ein. GovGuard bewertet sie gegen die Prüfregeln aus BSI, CIS und FSBP.
Eine CloudFormation-Vorlage ist eine Datei, die AWS-Ressourcen als Bauplan beschreibt.

**F3 Galerie.** Die Galerie zeigt gespeicherte Audit-Reports zu Musterfällen, je neben dem geprüften
Dokument. Ein Musterfall ist eine erfundene Eingabe mit festgelegtem Soll-Ergebnis.
Weicht der Audit-Report vom Soll ab, zeigt die Galerie die Abweichung.

**F4 Audit-Report.** Der Audit-Report nennt den Gesamtstatus und je Prüfregel genau einen Befund mit
Normanker, Status, Begründung, Beleg und Empfehlung. Die prüfende Person kann ihn als JSON-Datei
herunterladen. Ein Normanker ist die Fundstelle im Regelwerk, etwa „DSGVO Art. 9“.

**F5 Wissensbasis.** Der Projektbetreiber erzeugt die Prüfregeln von Hand angestoßen aus den
öffentlichen Normtexten. Jede Prüfregel zitiert ihre Quelle wörtlich, und ein Programm prüft das.
Normtexte lädt GovGuard nur vom Herausgeber und nur mit der hinterlegten Prüfsumme (G9).

## 5 Geschäftsregeln

### G1 Fester Prüfkatalog

Jedes Audit bewertet alle Prüfregeln seiner Art, keine wird ausgelassen. Der Prüfkatalog ist diese
feste, beim Bau der Wissensbasis bestimmte Menge.

### G2 Status

Jeder Befund hat genau einen von vier Status. Der Audit-Report nutzt die international üblichen Kürzel.

| Status | Bedeutung |
|---|---|
| PASS | Die Eingabe belegt, dass die Prüfregel eingehalten ist. |
| WARN | Aus der Eingabe ist es nicht entscheidbar, es besteht Prüfbedarf. |
| FAIL | Die Eingabe belegt einen Verstoß. |
| N/A | Die Prüfregel betrifft keinen Dienst, der in der Architektur vorkommt. |

### G3 Gesamtstatus

Der Gesamtstatus ist der schlechteste Status aller Befunde: FAIL vor WARN vor PASS.

### G4 FAIL nur bei festgelegtem Verstoß

Eine Spezifikation ist eine offene Welt. Das bedeutet: Was sie nicht erwähnt, kann anderswo
geregelt sein. Fehlt eine Angabe, ist der Befund daher WARN.

FAIL gibt es nur, wenn der Text etwas festlegt, das der Prüfregel widerspricht. Dazu zählt auch ein
erklärter Verzicht.

Eine CloudFormation-Vorlage ist dagegen eine geschlossene Welt: Was fehlt, gilt als Standardwert
und kann FAIL sein.

### G5 Wörtlicher Beleg

Das Sprachmodell nennt zu PASS und FAIL nur die Zeilen der Eingabe. Den Beleg schneidet das
Programm selbst aus der Eingabe aus.

Fehlen gültige Zeilen, stuft das Programm den Befund auf WARN herab. Der ursprüngliche Status
bleibt sichtbar.

### G6 Zweitprüfung jedes FAIL

In der offenen Welt prüft ein zweiter Aufruf des Sprachmodells jedes FAIL. Er sieht nur das
Verstoßkriterium und die Belegzeilen.

Bestätigt er das FAIL nicht, wird es WARN. Fällt er aus, bleibt das FAIL ungeprüft stehen, denn
der strengere Status ist der sichere.

### G7 Sicherer Abbruch

Im Zweifel liefert GovGuard kein Ergebnis statt eines falschen.

Ist die Antwort des Sprachmodells auch nach einer Wiederholung ungültig, bricht das Audit ab. Es
zeigt dann eine Fehlermeldung, nie einen halben Audit-Report.

### G8 Soll-Abweichung

Weicht ein gespeicherter Audit-Report vom Soll seines Musterfalls ab, wird das angezeigt. Das Audit
wird nicht so lange wiederholt, bis das Ergebnis passt.

### G9 Rückverfolgung über Prüfsummen

Eine Prüfsumme ist ein Fingerabdruck aus 64 Zeichen, den GovGuard mit dem Verfahren SHA-256 aus
einem Text berechnet. Schon ein geändertes Zeichen ergibt eine andere Prüfsumme. Aus ihr lässt sich
der Text nicht zurückrechnen.

Jeder Audit-Report trägt die Prüfsumme seiner Eingabe und die des Prüfkatalogs. Die Eingabe selbst
speichert er nicht. Damit ist belegbar, welchen Text ein Audit-Report mit welchen Prüfregeln bewertet hat.

Ein Audit-Report der Galerie gilt nur für das Dokument mit genau seiner Prüfsumme. Ändert sich das
Dokument, muss der Audit-Report neu entstehen. Ein automatischer Test prüft das für jeden Musterfall.

## 6 Daten und Datenschutz

### Datenflüsse

| Daten | Herkunft | Wohin | Wie lange |
|---|---|---|---|
| Eingabe (Spezifikation oder Architektur) | prüfende Person | Streamlit Community Cloud (USA), Groq (USA) | GovGuard speichert sie nicht; sie lebt nur in der Sitzung |
| Audit-Report mit Belegen | GovGuard | Browser der prüfenden Person | bis zum Ende der Sitzung oder als heruntergeladene Datei bei ihr |
| Angaben zur Rückverfolgung | GovGuard | im Audit-Report | wie der Audit-Report |
| Audit-Reports der Galerie | Projektbetreiber | öffentliche Versionsverwaltung (GitHub) | bis zur Löschung durch den Projektbetreiber |
| Zugriffsdaten der Besucher (z. B. IP-Adresse) | Browser | Streamlit Community Cloud (USA) | nach den Bedingungen von Streamlit |

Eine Sitzung ist die Verbindung eines Browsers mit der Web-Anwendung. Schließt man das Fenster,
endet sie.

Zur Rückverfolgung stehen im Audit-Report nur Prüfsummen, das verwendete Sprachmodell und eine
zufällige Kennung des Audits (G9). Daten über die prüfende Person enthält er nicht.

### Übermittlung in die USA

Betrieb und Sprachmodell laufen in den USA. Die USA sind aus Sicht der DSGVO ein Drittland, also ein
Staat außerhalb der EU.

Für diese Übermittlung legt der Demo-Stand keine eigenen Garantien nach Art. 46 DSGVO fest.
Deshalb gilt die Regel: nur fiktive Daten. Die Oberfläche weist vor jedem Audit auf den Datenfluss
in die USA hin.

### Speicherung und Löschung

Was Groq und Streamlit selbst speichern und wann sie es löschen, regeln deren Nutzungsbedingungen.
GovGuard legt dafür keine eigene Löschfrist fest. Ein eigenes Audit-Protokoll führt der Demo-Stand
nicht.

### Weg für echte Daten

Für echte Daten ist ein anderer Weg festgelegt: das Sprachmodell über AWS Bedrock in der EU
(Region Frankfurt), mit einem Protokoll ohne Eingabetext.

## 7 Nicht-funktionale Anforderungen

| Merkmal | Anforderung |
|---|---|
| Leistung | Eine Eingabe hat höchstens 100.000 Zeichen; das prüft das Programm vor jedem Aufruf des Sprachmodells. Ein Audit dauert mit Groq ca. 20 bis 55 Sekunden (Messung 16.10.2026). |
| Kosten | Ein Audit kostet mit Groq 2 bis 3 Cent. Das Passwort verhindert, dass Fremde Kosten auslösen. |
| Leerlaufkosten | 0 €. Leerlaufkosten sind Kosten, die ohne Nutzung allein durch Zeit entstehen. |
| Sicherheit | Passwort und Zugangsschlüssel für das Sprachmodell liegen nur in den geschützten Einstellungen von Streamlit, nicht im Programmcode. Ohne eingerichtetes Passwort startet kein Audit. |
| Nachvollziehbarkeit | Jeder Audit-Report nennt Sprachmodell und Prüfsummen (G9). Jeder Eingriff des Programms in eine Antwort des Sprachmodells steht als Korrektur am Befund. |
| Prüfbarkeit | Alle automatischen Tests laufen ohne AWS und ohne Groq. |

## 8 Bekannte Grenzen

**Schwankung.** Ein Sprachmodell antwortet nicht immer gleich. Bei Spezifikationen änderten zwischen
zwei Läufen mit Groq 42 von 151 Prüfregeln ihren Status. Die Zweitprüfung fängt falsche FAILs ab,
PASS und WARN schwanken weiter.

**Wissensbasis per KI.** Ob eine Anforderung prüfbar ist, hat beim Bau ein Sprachmodell beurteilt.
Einzelne Fehlurteile sind möglich. Programme sichern nur Zitate, Fundstellen und Pflichtanker ab.

**Umfang.** Protokollieren (SDM M43) und kontoweite AWS-Pflichten wie die Mehr-Faktor-Anmeldung des
Hauptkontos fehlen bewusst. Terraform und CloudFormation-Vorlagen in YAML prüft GovGuard nur als Freitext.
