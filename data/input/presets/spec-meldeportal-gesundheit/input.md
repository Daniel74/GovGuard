# Fachkonzept: Online-Anmeldung zur Schuleingangsuntersuchung

_Fiktives Beispiel. Behörde, Personen und Dienstleister sind erfunden._

## 1 Ziel

Das Gesundheitsamt des Landkreises Musterland untersucht jedes Jahr rund 2.300 Kinder vor der
Einschulung. Bisher füllen Eltern einen Papierbogen aus und bringen ihn zur Untersuchung mit. Künftig
melden sie ihr Kind online an und beantworten den Anamnesebogen vorab im Bürgerportal des Landkreises.
So kann die Schulärztin oder der Schularzt die Untersuchung besser vorbereiten, und die Wartezeit im
Amt sinkt.

## 2 Ablauf

1. Die Eltern erhalten mit dem Einladungsschreiben einen Zugangscode und melden sich damit im
   Bürgerportal an.
2. Sie wählen einen Untersuchungstermin und füllen den Anamnesebogen aus.
3. Das Bürgerportal übermittelt Anmeldung und Anamnesebogen an die Schnittstelle des Gesundheitsamts.
   Die Schnittstelle bestätigt den Eingang sofort und übernimmt die Daten danach asynchron über eine
   Warteschlange in die Fachanwendung des Kinder- und Jugendärztlichen Dienstes.
4. Die Eltern können Unterlagen hochladen, etwa das gelbe Kinderuntersuchungsheft oder den Impfpass.
   Die Unterlagen werden im Dokumentenspeicher des Gesundheitsamts in der AWS-Region eu-central-1
   abgelegt.
5. Nach der Untersuchung erhalten die Eltern das Ergebnis per Post.

## 3 Erhobene Daten

| Datengruppe | Felder |
|---|---|
| Kind | Name, Vorname, Geburtsdatum, Geschlecht, Anschrift, vorgesehene Grundschule |
| Sorgeberechtigte | Name, Anschrift, Telefon, E-Mail |
| Anamnese | Vorerkrankungen, chronische Erkrankungen, Allergien, Medikamente, Krankenhausaufenthalte, Frühgeburt, Entwicklungsauffälligkeiten (Sprache, Motorik, Verhalten), laufende Therapien (Logopädie, Ergotherapie, Psychotherapie) |
| Impfstatus | Impfungen laut Impfpass, insbesondere Masern |
| Familie | Erkrankungen der Eltern und Geschwister, Muttersprache, Anzahl der Geschwister |
| Unterlagen | Scans des Kinderuntersuchungshefts und des Impfpasses |

## 4 Rechtsgrundlagen

Die Schuleingangsuntersuchung selbst beruht auf dem Schulgesetz des Landes und dem Gesetz über den
Öffentlichen Gesundheitsdienst. Für die Anmeldung, den Termin und die Untersuchungsdaten ist das die
Rechtsgrundlage.

Zusätzlich wertet das Gesundheitsamt die Angaben des Anamnesebogens aus, um das Angebot des Portals zu
verbessern und Kampagnen zu planen: Welche Erkrankungen und Therapien kommen in welchen Stadtteilen
gehäuft vor, und welche Eltern brechen den Bogen an welcher Stelle ab? Dafür werden die
Anamnesedaten einschließlich der Angaben zu Erkrankungen und Therapien des Kindes mit Name und
Anschrift ausgewertet. Eine Einwilligung der Eltern wird für diese Auswertung nicht eingeholt; die
Verarbeitung der Gesundheitsangaben für die Auswertung stützt das Gesundheitsamt auf berechtigte
Interessen nach Art. 6 Abs. 1 lit. f DSGVO.

## 5 Analyse der Nutzung

Für die Auswertung nach Abschnitt 4 bindet das Bürgerportal das Analysewerkzeug „Musteranalyse“ der
fiktiven Musteranalyse Inc. mit Sitz in Austin, Texas (USA) ein. Das Portal überträgt jede Eingabe im
Anamnesebogen zusammen mit Name und Anschrift des Kindes an die Server von Musteranalyse in den USA.
Musteranalyse Inc. ist nicht nach dem EU-US Data Privacy Framework zertifiziert. Standardvertragsklauseln
oder andere geeignete Garantien nach Art. 46 DSGVO wurden nicht vereinbart, weil der Anbieter nur
seine eigenen Nutzungsbedingungen akzeptiert. Die Eltern werden über die Übermittlung in die USA nicht
informiert.

## 6 Speicherung und Löschung

Anmeldung, Anamnesebogen und Unterlagen werden in der Fachanwendung gespeichert. Eine Löschfrist ist
noch nicht festgelegt; das Gesundheitsamt möchte die Daten zunächst für spätere Vergleiche aufbewahren.

## 7 Sicherheit

- Die Schnittstelle ist nur über HTTPS erreichbar und nimmt nur Aufrufe des Bürgerportals an.
- Der Dokumentenspeicher ist verschlüsselt.
- Zugriff auf die Fachanwendung haben die Beschäftigten des Kinder- und Jugendärztlichen Dienstes.
