# Architekturbeschreibung: Revisionssicheres Protokollarchiv für Fachverfahren

_Fiktives Beispiel der Stadt Musterhausen._

## Zweck

Mehrere Fachverfahren der Stadt (Wohngeld, Elterngeld, Gewerbeamt) sollen ihre Protokollereignisse an
einer zentralen Stelle unveränderbar ablegen. Das Archiv dient der Revision und dem Nachweis gegenüber
der Aufsicht; es wird nur gelesen, wenn ein Vorfall untersucht wird.

## Komponenten und Ablauf

Alle Komponenten liegen in einem eigenen AWS-Konto in der Region eu-central-1.

1. **API Gateway (REST, regional):** Die Fachverfahren senden Protokollereignisse mit `POST /ereignisse`.
   Die Methode verlangt IAM-Authentifizierung (AWS Signature Version 4); nur die Rollen der
   angebundenen Fachverfahren dürfen sie aufrufen.
2. **Lambda-Funktion „Ereignisannahme“:** Sie prüft das Schema eines Ereignisses (Zeitpunkt, Quelle,
   Zielobjekt, Ereignisart, Ergebnis), ergänzt den Empfangszeitpunkt und gibt es an Firehose weiter.
3. **Amazon Data Firehose:** Der Lieferstrom bündelt die Ereignisse für bis zu 5 Minuten oder 5 MB und
   schreibt sie als komprimierte JSON-Dateien in den Archiv-Bucket.
4. **S3-Archiv-Bucket:** Der Bucket ist mit S3 Object Lock im Modus Compliance angelegt; die
   Standard-Aufbewahrung beträgt 10 Jahre. Innerhalb dieser Zeit kann niemand ein Objekt löschen oder
   überschreiben, auch kein Administrator. Versionierung ist aktiv.

## Sicherheitsmaßnahmen

- Am Archiv-Bucket sind alle vier Einstellungen von S3 Block Public Access aktiv: BlockPublicAcls,
  IgnorePublicAcls, BlockPublicPolicy und RestrictPublicBuckets. Zusätzlich ist Block Public Access
  auf Kontoebene aktiv.
- Der Bucket und der Lieferstrom sind mit einem kundenverwalteten KMS-Schlüssel verschlüsselt.
- Die Bucket-Policy lehnt alle Anfragen ohne TLS ab (Bedingung `aws:SecureTransport = false` → Deny).
- Die Lambda-Funktion und Firehose haben je eine eigene IAM-Rolle mit den Rechten, die sie für ihre
  Aufgabe brauchen.

## Protokollierung der Plattform selbst

Das Archiv protokolliert seine eigenen sicherheitsrelevanten Ereignisse in CloudWatch Logs:

- API Gateway schreibt Zugriffsprotokolle für jeden Aufruf mit Zeitpunkt, aufrufender IAM-Rolle,
  Quell-IP, Methode, Pfad und HTTP-Status, also auch für abgelehnte Aufrufe mit 403.
- Die Lambda-Funktion protokolliert jedes abgewiesene Ereignis mit Zeitpunkt, Quelle, Zielobjekt und
  Fehlergrund, ohne den Inhalt des Ereignisses.
- Firehose protokolliert Zustellfehler in eine eigene Log-Gruppe.

Die Log-Gruppen bewahren die Einträge 1 Jahr auf.

## Betrieb

Die Fachverfahren senden zusammen etwa 40.000 Ereignisse pro Tag, in Spitzen 50 pro Sekunde. Im
Leerlauf fallen nur Kosten für den Speicher und den KMS-Schlüssel an.
