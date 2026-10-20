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
- Die **KI-Verordnung (KI-VO)** ist das EU-Gesetz für KI-Systeme. Ein KI-System ist Software, die
  aus Eingaben selbst Ergebnisse wie Empfehlungen ableitet. Die KI-VO stuft solche Systeme nach
  ihrem Risiko ein.
- Der **IT-Grundschutz** des Bundesamts für Sicherheit in der Informationstechnik (BSI) beschreibt
  Sicherheitsanforderungen an IT-Systeme.

GovGuard ist ein digitaler Prüfassistent für diese Vorprüfung. Er prüft eine Spezifikation gegen
DSGVO, KI-VO und SDM und eine Architektur gegen BSI IT-Grundschutz, BSI C5, CIS AWS und AWS FSBP.

Ein solcher Prüflauf heißt Audit. Sein Ergebnis ist ein Audit-Report: je Prüfregel ein Befund mit
Status, wörtlichem Beleg und Empfehlung.

GovGuard ersetzt die Fachleute nicht. Er zeigt ihnen in Minuten, wo sie genauer hinsehen müssen.

## 2 Geltungsbereich und Abgrenzung

Diese Beschreibung gilt für den Demo-Stand, der zur Präsentation am 26.10.2026 läuft.

Der Demo-Stand ist eine Web-Anwendung auf Streamlit Community Cloud. Das ist ein kostenloser Dienst
zum Betrieb von Python-Anwendungen.

Die Prüfregeln wendet ein Sprachmodell beim Dienstleister Groq an. Ein Sprachmodell ist eine KI, die Text
liest und Text oder strukturierte Daten zurückgibt.

Nicht zum Umfang gehören:

- **echte personenbezogene Daten:** Der Demo-Stand verarbeitet nur fiktive Beispiele.
- **Rechtsberatung:** Ein Befund ist ein Hinweis für die Fachleute, kein Rechtsgutachten.
- **Betrieb auf AWS** mit Programmierschnittstelle für automatische Abläufe: Er ist als Ausbau
  beschrieben ([AUSBAU.md](AUSBAU.md)), aber aus Budgetgründen nicht gebaut.

## 3 Prüfgrundlagen

GovGuard prüft nicht gegen ganze Regelwerke, sondern gegen ausgewählte Teile davon. Ein PASS heißt
deshalb nie „konform mit der DSGVO“. Es heißt nur: Diese eine Prüfregel ist belegt eingehalten.

### Wie die Teile ausgewählt werden

Bei DSGVO und KI-VO wird jeder Artikel zuerst zerlegt. Ein Artikel enthält oft mehrere Pflichten,
etwa Art. 5 DSGVO sechs Grundsätze. Ein Sprachmodell teilt ihn deshalb in Einzelpflichten mit
eigener Fundstelle, z. B. „DSGVO Art. 5 Abs. 1 lit. a“.

Dabei sagt das Sprachmodell nur, ob Absätze alle gelten, ob einer genügt oder ob sie gar keine
Pflicht enthalten. Wortlaut und Fundstelle übernimmt das Programm aus dem Normtext.

Jede Anforderung eines Regelwerks durchläuft danach bis zu drei Filter:

1. **Vorfilter (Programm):** behält nur festgelegte Kapitel, Artikel, Bausteine oder Bereiche, mit
   festem Begründungssatz für alles andere. Verworfen wird auch, was laut Zerlegung keine Pflicht ist.
2. **Prüfbarkeit (Sprachmodell):** Lässt sich die Anforderung an einer Spezifikation bzw. Architektur
   überhaupt prüfen (G10)?
3. **Relevanz (Programm, nur Architektur):** Betrifft sie einen Dienst im Prüfumfang? Der Prüfumfang
   ist eine feste Liste von AWS-Diensten: vor allem Serverless-Dienste, dazu RDS/Aurora und Fargate.

Jede Entscheidung steht mit Begründung im Auswahlprotokoll. Die Zahlen unten stammen daraus.

### Für Spezifikationen

| Regelwerk | Fassung | Verwendeter Teil | Anforderungen | nach Vorfilter | Prüfregeln |
|---|---|---|---|---|---|
| DSGVO | Verordnung (EU) 2016/679, Text von EUR-Lex | Kapitel II–V (Art. 5–49); je Einzelpflicht eine Anforderung; ohne Art. 20, 27, 41 und 47 | 350 | 247 | 169 |
| KI-VO | Verordnung (EU) 2024/1689, konsolidierte Fassung vom 27.07.2026, Text von EUR-Lex | Art. 4, 5, 6, 13, 14, 26, 27 und 50; je Einzelpflicht eine Anforderung | 197 | 74 | 65 |
| SDM | Bausteine der Datenschutzkonferenz, V1.0 bzw. V1.0a | Löschen und Vernichten (M60), Trennen (M50), Zugriffe regeln (M51); alle Maßnahmen | 147 | 147 | 116 |

Der Vorfilter Behörde verwirft vier Artikel, die für eine deutsche Behörde nie gelten: Art. 20
(Datenübertragbarkeit, Abs. 3), Art. 27 (Vertreter nur für Verantwortliche außerhalb der EU),
Art. 41 (Überwachung von Verhaltensregeln, Abs. 6) und Art. 47 (BCR nur für Unternehmensgruppen).
Jeder Artikel steht mit festem Begründungssatz im Auswahlprotokoll (ADR 0028).

Nicht verwendet werden bei der DSGVO Kapitel I, VI bis VIII, X und XI. Sie regeln Begriffe,
Aufsicht, Rechtsbehelfe, Sanktionen und Schlussbestimmungen, also nichts, was eine Spezifikation
erfüllen kann.

Auch Kapitel IX fehlt. Es regelt besondere Fälle wie Beschäftigtendaten oder Forschung und wäre für
manche Spezifikation einschlägig. Das ist eine bewusste Lücke.

Von der KI-VO werden acht Artikel verwendet: KI-Kompetenz (Art. 4), verbotene Praktiken (Art. 5),
Einstufung als Hochrisiko-System (Art. 6), dessen Pflichten (Art. 13, 14, 26, 27) und Transparenz
(Art. 50). Ein Hochrisiko-System ist ein KI-System, das die KI-VO wegen seines Einsatzbereichs,
etwa bei Sozialleistungen, strengen Pflichten unterwirft.

Alle übrigen Artikel der KI-VO fehlen, etwa das Risikomanagement der Anbieter (Art. 9).

Die drei SDM-Bausteine setzen je einen Grundsatz aus Art. 5 DSGVO um, den die DSGVO-Prüfregel
allein nicht prüfbar macht: Löschen die Speicherbegrenzung, Trennen die Zweckbindung, Zugriffe
regeln die Vertraulichkeit. An diesen drei Punkten scheitern Cloud-Verfahren von Behörden häufig.

Vom SDM fehlen alle übrigen Bausteine.

### Für Architekturen

| Regelwerk | Fassung | Verwendeter Teil | Anforderungen | nach Vorfilter | Prüfregeln |
|---|---|---|---|---|---|
| BSI IT-Grundschutz++ | Katalog des BSI auf GitHub, fester Stand | MUSS und SOLLTE bei normalem Schutzbedarf; sechs technische Praktiken (DLS, BER, DET, KONF, BES, ARCH) | 1.000 | 380 | 39 |
| BSI C5:2025 | über Prowler 5.44.0 | Bereiche OPS, IAM, CRY, COS, PSS | 610 | 300 | 11 |
| CIS AWS Foundations Benchmark | v7.0.0, über Prowler | Kapitel 2 (IAM), 3 (Speicher), 4 (Protokollierung), 6 (Netzwerk) | 70 | 54 | 20 |
| AWS FSBP | über Prowler 5.44.0 | Controls zu Diensten im Prüfumfang | 286 | 150 | 105 |

Prowler ist ein quelloffenes Prüfwerkzeug für AWS. Seine Dateien enthalten die Anforderungen dieser
Regelwerke maschinenlesbar. Für CIS sichert eine Stichprobe gegen das Original die Texttreue ab.

Die meisten BSI- und C5-Anforderungen fallen als nicht prüfbar heraus. Sie betreffen Organisation,
Personen oder das ganze Konto, nicht ein einzelnes Template (B5).

## 4 Rollen

| Rolle                                    | Aufgabe                                                                                                                                                     |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Besucher (z. B. Personalverantwortliche) | sieht in der Galerie gespeicherte Audits an, ohne Anmeldung                                                                                                 |
| Prüfende Person                          | startet mit dem Demo-Passwort ein eigenes Audit und lädt den Audit-Report herunter                                                                          |
| Projektbetreiber                         | baut die Wissensbasis, pflegt die Musterfälle, verwaltet Passwort und Zugangsschlüssel                                                                      |
| Groq                                     | Dienstleister für das Sprachmodell (Inferenz)                                                                                                               |
| Streamlit Community Cloud                | Dienstleister für den Betrieb der Web-Anwendung                                                                                                             |
| GitHub                                   | Dienstleister für die Versionsverwaltung: Programmcode, Wissensbasis, Musterfälle und Galerie liegen dort öffentlich; Streamlit lädt die Anwendung von dort |

## 5 Fachliche Anforderungen

### F1 Audit einer Spezifikation

Die prüfende Person gibt eine Spezifikation als Text, Markdown oder
OpenAPI ein. GovGuard bewertet sie gegen alle 350 Prüfregeln aus DSGVO, KI-VO und SDM.

### F2 Audit einer Architektur

Die prüfende Person gibt eine Architektur als Freitext oder als
CloudFormation-Vorlage ein. GovGuard bewertet sie gegen die Prüfregeln aus BSI, CIS und FSBP.
Eine CloudFormation-Vorlage ist eine Datei, die AWS-Ressourcen als Bauplan beschreibt.

### F3 Galerie

Die Galerie zeigt gespeicherte Audit-Reports zu Musterfällen, je neben dem geprüften
Dokument. Ein Musterfall ist eine erfundene Eingabe mit festgelegtem Soll-Ergebnis.
Weicht der Audit-Report vom Soll ab, zeigt die Galerie die Abweichung.

### F4 Audit-Report

Der Audit-Report nennt den Gesamtstatus und je Prüfregel genau einen Befund mit
Normanker, Status, Begründung, Beleg und Empfehlung. Die prüfende Person kann ihn als JSON-Datei
herunterladen. Ein Normanker ist die Fundstelle im Regelwerk, etwa „DSGVO Art. 9“.

### F5 Wissensbasis bauen

Der Projektbetreiber erzeugt die Prüfregeln aus den öffentlichen
Normtexten. Die Wissensbasis ist die Gesamtheit dieser Prüfregeln, je Audit-Art ein Prüfkatalog.

Der Bau läuft in vier Schritten (G10–G13):

1. Normtexte vom Herausgeber laden, nur mit der hinterlegten Prüfsumme (G9). DSGVO und KI-VO in
   Einzelpflichten zerlegen (Abschnitt 3).
2. Je Anforderung urteilt ein Sprachmodell, ob sie an einer Spezifikation oder Architektur prüfbar ist.
3. Das Programm wählt aus, und ein Sprachmodell formuliert aus jeder Anforderung eine Prüfregel.
4. Programme prüfen das Ergebnis, der Projektbetreiber gibt es frei.

Wie das technisch abläuft, beschreibt [ARCHITECTURE.md](ARCHITECTURE.md) Abschnitt 1.

### F6 Wissensbasis erweitern

Der Projektbetreiber kann ein weiteres Regelwerk als Quelle
aufnehmen, etwa das Bundesdatenschutzgesetz. Er stößt die Erweiterung an und gibt sie frei (G12).

Eine neue Quelle braucht drei Dinge: einen Herausgeber mit festem Dokument und Prüfsumme (G9),
mindestens einen Musterfall mit Soll und eine schriftliche Entscheidung mit Begründung.
Das technische Vorgehen beschreibt [ARCHITECTURE.md](ARCHITECTURE.md) unter „Neue Quelle hinzufügen“.

## 6 Geschäftsregeln

### G1 Fester Prüfkatalog

Jedes Audit bewertet alle Prüfregeln seiner Art, keine wird ausgelassen. Der Prüfkatalog ist diese
feste, beim Bau der Wissensbasis bestimmte Menge.

### G2 Status

Jeder Befund hat genau einen von vier Status. Der Audit-Report nutzt die international üblichen
Kürzel, die Oberfläche zeigt deutsche Bezeichnungen.

| Kürzel | Oberfläche        | Bedeutung                                                                                                                            |
| ------ | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| PASS   | Einhaltung belegt | Die Eingabe belegt, dass die Prüfregel eingehalten ist.                                                                              |
| WARN   | Prüfbedarf        | Aus der Eingabe ist es nicht entscheidbar, es besteht Prüfbedarf.                                                                    |
| FAIL   | Verstoß belegt    | Die Eingabe belegt einen Verstoß.                                                                                                    |
| N/A    | Nicht anwendbar   | Die Prüfregel ist auf die Eingabe nicht anwendbar. Bei einer Architektur entscheidet das Programm das über die vorkommenden Dienste. |

Ein Befund mit WARN ohne Belegzeilen heißt in der Oberfläche „Lücke“: Die Eingabe beschreibt die
Prüfregel nicht.

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

### G10 Das Sprachmodell urteilt, das Programm wählt aus

Beim Bau der Wissensbasis sagt das Sprachmodell je Anforderung nur „prüfbar ja oder nein“, mit
Begründung. Ob eine Anforderung in den Prüfkatalog kommt, entscheidet das Programm.

Jede Entscheidung steht mit Begründung im Auswahlprotokoll. Das Auswahlprotokoll ist eine Liste
aller Anforderungen mit ihrem Ergebnis, aufgenommen oder verworfen.

### G11 Prüfungen beim Bau

Jede Prüfregel muss ihre Quelle wörtlich zitieren, und ihre Fundstelle muss im Regelwerk existieren.
Ein zweiter Aufruf des Sprachmodells prüft, dass jedes Verstoßkriterium eine Festlegung beschreibt
und kein bloßes Fehlen (G4).

Jeder Pflichtanker muss im Prüfkatalog stehen. Ein Pflichtanker ist eine Fundstelle, deren Befund
ein Musterfall in seinem Soll festlegt.

Fällt eine dieser Prüfungen durch, bricht der Bau ab. Die bisherige Wissensbasis bleibt dann gültig.

### G12 Freigabe durch einen Menschen

Der Bau startet nur von Hand. Der Projektbetreiber liest das Auswahlprotokoll, bevor er die neue
Wissensbasis freigibt.

Gültig wird die neue Wissensbasis erst, wenn er sie in der Versionsverwaltung speichert. Dort ist
jede Änderung mit Zeitpunkt und Autor nachvollziehbar.

### G13 Bestehende Prüfregeln bleiben unverändert

Seit dem 18.10.2026 bleiben die bestehenden Prüfregeln und die Prüflogik unverändert. So bleiben die
Audit-Reports der Galerie untereinander vergleichbar.

Eine neue Quelle darf nur Prüfregeln hinzufügen. Ändert eine Erweiterung bestehende Prüfregeln,
müssen alle Audit-Reports der Galerie neu entstehen und alle Soll-Ergebnisse erneut geprüft werden.

Diese Ausnahme gilt bewusst für die Zerlegung von DSGVO und KI-VO in Einzelpflichten (#53,
[ADR 0026](adr/0026-rechtsartikel-zerlegen.md)): Die Spec-Galerie ist danach neu entstanden.

## 7 Daten und Datenschutz

### Datenflüsse

| Daten                                         | Herkunft                   | Wohin                                   | Wie lange                                                        |
| --------------------------------------------- | -------------------------- | --------------------------------------- | ---------------------------------------------------------------- |
| Eingabe (Spezifikation oder Architektur)      | prüfende Person            | Streamlit Community Cloud, Groq         | GovGuard speichert sie nicht; sie lebt nur in der Sitzung        |
| Audit-Report mit Belegen                      | GovGuard                   | Browser der prüfenden Person            | bis zum Ende der Sitzung oder als heruntergeladene Datei bei ihr |
| Angaben zur Rückverfolgung                    | GovGuard                   | im Audit-Report                         | wie der Audit-Report                                             |
| Audit-Reports der Galerie                     | Projektbetreiber           | öffentliche Versionsverwaltung (GitHub) | bis zur Löschung durch den Projektbetreiber                      |
| Zugriffsdaten der Besucher (z. B. IP-Adresse) | Browser                    | Streamlit Community Cloud               | nach den Bedingungen von Streamlit                               |
| Öffentliche Normtexte                         | Herausgeber der Regelwerke | Groq, nur beim Bau der Wissensbasis     | als Zitate in den Prüfregeln auf GitHub                          |

Eine Sitzung ist die Verbindung eines Browsers mit der Web-Anwendung. Schließt man das Fenster,
endet sie.

Zur Rückverfolgung stehen im Audit-Report nur Prüfsummen, das verwendete Sprachmodell und eine
zufällige Kennung des Audits (G9). Daten über die prüfende Person enthält er nicht.

### Verarbeitung außerhalb der EU

Streamlit, Groq und GitHub verarbeiten Daten auch außerhalb der EU. Ein Staat außerhalb der EU heißt
in der DSGVO Drittland.

Für diese Übermittlung in ein Drittland legt der Demo-Stand keine eigenen Garantien nach Art. 46
DSGVO fest. Deshalb gilt die Regel: nur fiktive Daten.

### Speicherung und Löschung

Was Groq und Streamlit selbst speichern und wann sie es löschen, regeln deren Nutzungsbedingungen.
GovGuard legt dafür keine eigene Löschfrist fest. Ein eigenes Audit-Protokoll führt der Demo-Stand
nicht.

## 8 Einstufung nach KI-Verordnung

GovGuard ist ein KI-System nach Art. 3 Nr. 1 KI-VO, denn ein Sprachmodell leitet die Befunde aus
der Eingabe ab.

GovGuard ist kein Hochrisiko-System nach Art. 6 KI-VO. Es prüft Dokumente, bewertet keine Menschen
und entscheidet nicht über Leistungen oder Rechte; das tun die Fachleute. Damit fällt es unter
keinen Einsatzbereich von Anhang III. Verbotene Praktiken nach Art. 5 kommen nicht vor.

Für GovGuard gelten deshalb nur die allgemeinen Pflichten der KI-VO:

| Pflicht                                     | Umsetzung                                                                                                                                        |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| KI-Kompetenz der Nutzer (Art. 4)            | Die Seite „Start & Hilfe“ erklärt jeder prüfenden Person, wie ein Befund entsteht, wie der Code ihn nachprüft und wie Korrekturen zu lesen sind. |
| Hinweis auf das KI-System (Art. 50 Abs. 1)  | Die Seite „Start & Hilfe“ nennt das Sprachmodell als Quelle der Befunde.                                                                         |
| Kennzeichnung der Ausgaben (Art. 50 Abs. 2) | Jeder Audit-Report nennt im Feld `model_id` maschinenlesbar das Sprachmodell, das ihn erzeugt hat.                                               |

## 9 Nicht-funktionale Anforderungen

| Merkmal             | Anforderung                                                                                                                                                                           |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Leistung            | Eine Eingabe hat höchstens 100.000 Zeichen; das prüft das Programm vor jedem Aufruf des Sprachmodells. Ein Audit dauert mit Groq ca. 20 bis 55 Sekunden (Messung 16.10.2026).         |
| Kosten              | Ein Audit kostet mit Groq 2 bis 3 Cent. Das Passwort verhindert, dass Fremde Kosten auslösen.                                                                                         |
| Leerlaufkosten      | 0 €. Leerlaufkosten sind Kosten, die ohne Nutzung allein durch Zeit entstehen.                                                                                                        |
| Sicherheit          | Passwort und Zugangsschlüssel für das Sprachmodell liegen nur in den geschützten Einstellungen von Streamlit, nicht im Programmcode. Ohne eingerichtetes Passwort startet kein Audit. |
| Nachvollziehbarkeit | Jedes Audit und jeder Bau der Wissensbasis hinterlässt prüfbare Spuren (Abschnitt 10).                                                                                                |
| Prüfbarkeit         | Alle automatischen Tests laufen ohne AWS und ohne Groq.                                                                                                                               |

## 10 Beobachtbarkeit

Beobachtbarkeit heißt: Man kann im Nachhinein erkennen, was das System getan hat und warum.
GovGuard hält das auf drei Ebenen fest, ohne Eingabetexte zu speichern.

| Ebene                   | Was festgehalten wird                                                                                                                                                                                  | Wo                                                | Wer liest es                          |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------- | ------------------------------------- |
| Je Audit                | Prüfsummen von Eingabe und Prüfkatalog, Sprachmodell und Kennung des Audits (G9); je Befund der ursprüngliche Status und jede Korrektur (G5, G6); Zahl der Wiederholungen und Urteile der Zweitprüfung | im Audit-Report                                   | prüfende Person, Besucher der Galerie |
| Je Bau der Wissensbasis | Auswahlprotokoll mit Begründung je Anforderung (G10); Bauprotokoll mit jeder Wiederholung samt Grund, Zahl der Anfragen und Tokens; Qualitätsbericht je Quelle                                         | Versionsverwaltung, zusammen mit der Wissensbasis | Projektbetreiber                      |
| Je Messlauf             | Laufzeit, Tokens, Kosten, Gründe für Wiederholungen und Abweichungen vom Soll                                                                                                                          | im zugehörigen Ticket                             | Projektbetreiber                      |

Messläufe startet der Projektbetreiber von Hand, etwa vor und nach einer Änderung an der
Wissensbasis. Was der Demo-Stand nicht festhält, steht in Abschnitt 12.

## 11 Qualität und Restrisiken

Ein Audit-Report ist ein Hinweis für Fachleute, kein Nachweis. Ein Sprachmodell kann irren, und
GovGuard macht sichtbar, wo.

**Qualitätsziel:** Jeder Musterfall erreicht sein Soll im Gesamtstatus und in seinen Pflichtbefunden.

Die Zahlen in P1 bis P6 sind Messwerte aus Messläufen im Oktober 2026 und aus der Galerie. Sie
zeigen den Ist-Stand, keine Anforderung.

### So wird die Qualität gesichert

- **Musterfälle mit Soll:** Das Soll steht vor dem ersten Lauf fest. Abweichungen zeigt die Galerie (G8).
- **Programm prüft jede Antwort:** genau ein Befund je Prüfregel, gültige Belegzeilen, festes Format.
  Sonst folgt eine Wiederholung oder der sichere Abbruch (G5, G7).
- **Eingriffe sichtbar:** Jede Herabstufung und jedes Urteil der Zweitprüfung steht als Korrektur
  am Befund (G6).

### P1 Schwankung zwischen Läufen

Dieselbe Eingabe kann im nächsten Lauf andere Status erhalten. Bei Spezifikationen änderten zwischen
zwei Läufen mit Groq 42 von 151 Prüfregeln ihren Status, mit AWS Bedrock 19. Gemessen wurde mit dem
Katalog von 151 Prüfregeln, vor KI-VO und Zerlegung.

- **Gegenmaßnahme:** Das Modell läuft ohne Zufallsanteil (Temperatur 0). Falsche FAILs fängt die
  Zweitprüfung ab.
- **Was bleibt:** PASS und WARN schwanken weiter. Jeder Audit-Report nennt deshalb sein Modell.

### P2 Falsches FAIL bei bloßem Fehlen

Das Modell wertet „nicht beschrieben“ gern als Verstoß, obwohl G4 das verbietet.

- **Gegenmaßnahme:** Die Zweitprüfung. Beim Musterfall Wohngeld stufte sie 9 von 14 FAILs auf WARN herab.
- **Was bleibt:** Die Zweitprüfung ist selbst ein Sprachmodell. Beim Musterfall Wohngeld blieben fünf
  FAILs stehen, der Gesamtstatus weicht vom Soll WARN ab.

### P3 Falsches PASS

Das Modell nennt Belegzeilen, die keine Einhaltung zeigen. Das Programm prüft nur, ob die Zeilen
existieren und lang genug sind, bis zu einem Abschnitt von 200 Zeilen.

- **Gegenmaßnahme:** Ohne gültige Zeilen wird PASS zu WARN (G5). Musterfälle legen PASS-Befunde fest.
- **Was bleibt:** Für PASS gibt es keine Zweitprüfung. Das ist das größte Restrisiko. Beispiel:
  Am 16.10.2026 ergab eine Messung beim Musterfall Antragseingang BSI BER.4.1 als PASS statt FAIL.

### P4 Viele Lücken

In der offenen Welt sind die meisten Befunde WARN, bei den Musterfällen 101 bis 120 von 151
(Katalog von 151 Prüfregeln).
Meist beschreibt die Eingabe die Anforderung einfach nicht.

- **Gegenmaßnahme:** Die Oberfläche trennt Lücken (nicht beschrieben) vom Prüfbedarf (Beleg unklar).
- **Was bleibt:** Der Audit-Report ist lang. Die Aussagekraft liegt in FAIL und Prüfbedarf.

### P5 Schwächen im Prüfkatalog

Ob eine Anforderung prüfbar ist und wie ihre Prüfregel lautet, hat beim Bau ein Sprachmodell
formuliert. Einzelne Fehlurteile sind möglich. Zwölf Prüfregeln enthalten Platzhalter, vier werten
eine Einstellung falsch herum.

- **Gegenmaßnahme:** Programme prüfen Zitate, Fundstellen und Pflichtanker. Musterfälle decken
  Fehler auf.
- **Was bleibt:** Ein Fehler im Katalog wirkt in jedem Audit gleich. Beispiel: Im Musterfall
  Protokollarchiv steht BSI DET.3.1 wegen eines Platzhalters auf WARN statt PASS.

### P6 Übersehene Dienste in Freitext-Architekturen

Bei einer Architektur als Freitext erkennt das Sprachmodell die verwendeten Dienste.

- **Gegenmaßnahme:** Es muss jeden erkannten Dienst mit Zeilen belegen.
- **Was bleibt:** Die Prüfregeln eines übersehenen Dienstes stehen auf N/A, mit dem Hinweis
  „Dienst in der Eingabe nicht erkannt“. Bewertet werden sie nicht.

## 12 Bekannte Grenzen

### B1 Keine echten Daten

Der Demo-Stand ist für echte Daten nicht geeignet (Abschnitt 7). Vorgesehen
ist dafür das Sprachmodell über AWS Bedrock in der EU (Region Frankfurt), mit einem Protokoll ohne
Eingabetext. Dieser Weg besteht nur über die Kommandozeile. Betrieb auf AWS und Protokoll sind
entworfen, aber nicht gebaut.

### B2 Prompt-Fassung nicht im Audit-Report

Ein Prompt ist die Arbeitsanweisung an das
Sprachmodell. Der Audit-Report nennt Sprachmodell und Prüfkatalog, aber nicht die Fassung der Prompts.

Ändert sich ein Prompt, sehen zwei Audit-Reports gleich aus, obwohl sie unterschiedlich entstanden
sind. Eine neue Fassung lässt sich deshalb nicht schrittweise einführen und messbar mit der alten
vergleichen; das geht nur über Zeitpunkt und Versionsverwaltung. Nur beim Einstufen der
Anforderungen ist die Prompt-Fassung Teil des Zwischenspeichers, sonst nirgends.

### B3 Kein Betriebsprotokoll

Wie viele Audits liefen, wie viele abbrachen und wie lange sie dauerten,
erfasst der Demo-Stand nicht. Ein Protokolleintrag je Audit ohne Eingabetext ist entworfen, aber
erst für den Betrieb auf AWS vorgesehen.

### B4 Versionsstand der Wissensbasis

Im Audit-Report steht dafür im Demo-Stand nur „local“. Welche
Wissensbasis geprüft hat, zeigt allein die Prüfsumme des Prüfkatalogs.

### B5 Umfang

Protokollierung prüft GovGuard nicht an der Spezifikation (SDM M43), sondern an der Architektur
(BSI DET, CIS Kapitel 4).

Kontoweite AWS-Pflichten wie die Mehr-Faktor-Anmeldung des Hauptkontos fehlen bewusst. Terraform und
CloudFormation-Vorlagen in YAML prüft GovGuard nur als Freitext.

### B6 Bedingungen: die Vorstufe liest nur, sie stuft nicht ein

Vor den Prüfpaketen stellt ein Aufruf des Sprachmodells fest, was die Spezifikation zu sieben
Bedingungen sagt: KI-System, Hochrisiko-KI, Drittlandübermittlung, Auftragsverarbeiter, Einwilligung,
Mandantenfähigkeit und automatisierte Entscheidung. Nur eine ausdrückliche Verneinung für das ganze
Vorhaben macht die Prüfregeln der Bedingung zu „Nicht anwendbar“, mit der Verneinungszeile als Beleg.

Schweigt die Spezifikation, steht die Bedingung auf „nicht festgelegt“ und ihre Prüfregeln bleiben
im Audit. Die Vorstufe stuft also nicht selbst ein: Ein Hochrisiko-System erkennt GovGuard nur, wenn
die Spezifikation es ausdrücklich beschreibt oder ausschließt. Eine verschwiegene Einstufung fällt
deshalb weiter nicht auf; die Prüfregeln zu Art. 4, 5, 6 und 50 KI-VO (KI-System) sowie zu Art. 13,
14, 26 und 27 (Hochrisiko-KI) bewertet dann das Sprachmodell. Kein KI-System heißt auch kein
Hochrisiko-System.

Fällt die Vorstufe aus, bleiben alle Bedingungen „nicht festgelegt“ und jede Prüfregel geht ans
Modell. Das Audit schlägt deshalb nie wegen der Vorstufe fehl (ADR 0028).
