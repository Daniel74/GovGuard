# 0028 – Bedingungen im Spec-Audit

_Ergänzt [ADR 0026](0026-rechtsartikel-zerlegen.md) (Zerlegung) und [ADR 0025](0025-ki-vo-als-neue-quelle-bei-eingefrorenem-katalog.md) (eingefrorener Katalog); bricht SPEC G13 für DSGVO bewusst (#59, #60)._

## Kontext

- Der Spec-Katalog prüft jede Spezifikation gegen alle Regeln, auch gegen Pflichten, die für eine deutsche Behörde nie gelten. Das kostete 24 Lücken je Audit und beim Wohngeld ein falsches FAIL (Art. 27 Abs. 2).
- Vier DSGVO-Artikel sind für Behörden ausgeschlossen: Art. 20 Abs. 3 (öffentliche Aufgabe), Art. 27 (Vertreter nur außerhalb der EU), Art. 41 Abs. 6 (Behörden ausgenommen), Art. 47 (BCR nur für Unternehmensgruppen).

## Entscheidung

- **Vorfilter Behörde:** Der DSGVO-Vorfilter (`kb_build/extract/dsgvo.py`) verwirft Art. 20, 27, 41 und 47 mit festem Begründungssatz im Auswahlprotokoll. Die Liste ist bewusst fest, wie bei der KI-VO (ADR 0025); ein weiterer Artikel kommt nur mit Test dazu.
- **Rebuild ohne LLM-Aufruf:** `extract`, `decompose`, `select --only-missing` und `rules --only-missing` laufen allein aus Cache und eingefrorenem Teil. Die vier Artikel stehen als `prefiltered` im Auswahlprotokoll und fehlen in Auswahl und Katalog.
- **Bedingungs-Vorlauf (#60):** Im Spec-Audit stellt ein LLM-Aufruf vor den Paketen fest, was die Spezifikation zu sieben Bedingungen sagt (`data/input/conditions.json`, Prompt in `calls/conditions.py`). Es nennt je Bedingung Zeilen, die sie belegen, und Zeilen, die sie für das ganze Vorhaben verneinen; der Code setzt `yes`, `no` oder `unstated`. Beide Arten: `yes` mit Korrektur „Widerspruch“ (der strengere Wert). Kein KI-System: auch kein Hochrisiko-System; deren Prüfregeln sind dann N/A mit der Begründung „KI-System“ und der Zeile, die es ausschließt.
- **N/A nur mit Beleg:** Bei `no` setzt der Code die Prüfregeln der Bedingung auf N/A (Beleg: Verneinungszeile, fester Satz „Die Spezifikation verneint: …“); sie gehen nicht ans Modell. Schweigen ist `unstated`, die Regeln bleiben. Die Zuordnung steht in der Datei: Artikel-Anker mit exakter Artikelgrenze, für SDM-Baustein Trennen (M50) eine Liste von 16 Prüfregeln für `multi_tenant`. Jede Prüfregel gehört höchstens zu einer Bedingung.
- **Ausfall:** Bleibt die Antwort nach einem Retry ungültig oder fällt der Dienst aus, sind alle Bedingungen `unstated` mit Hinweis in den Korrekturen. Das Audit läuft weiter, kein fail closed: Der Vorlauf kann nur Regeln wegnehmen, nie ein FAIL erzeugen.

## Konsequenzen

- Der Spec-Katalog hat 350 statt 374 Prüfregeln (DSGVO 169 statt 193); genau die 24 Regeln der vier Artikel fehlen, alle übrigen sind byte-gleich.
- Die Galerie-Reports stehen noch auf 374 Regeln und entstehen mit #61 neu. `AuditReport.conditions` hat Default leer, alte Reports laden weiter.
- Ein Audit kostet einen LLM-Aufruf mehr; eine falsch verneinte Bedingung versteckt Prüfregeln. Deshalb zählt nur eine Verneinung für das ganze Vorhaben, `temperature` ist 0.
- **Messung** (Groq, je 1 Lauf, #60): 18 von 21 Bedingungen treffen ihr Soll. Meldeportal `consent` ist `no`: Abschnitt 4 nennt für Anmeldung und Untersuchung das Gesetz, Z. 47 schließt die Einwilligung für die Auswertung aus; das Soll ist darauf korrigiert. Zweimal `unstated` statt eines Werts (Wohngeld `processor`, GovGuard `automated_decision`), das kostet nur eine Lücke. Die Lücken ohne Bedingung sinken um 31 % und 24 %, bei `spec-govguard` nur um 15 %, weil dort fast alle Bedingungen `yes` sind. KI-VO Art. 50 Abs. 2 kippte dort PASS → WARN; die Regel geht normal ans Modell, das ist Schwankung.
- Ein Verantwortlicher außerhalb der EU oder eine Unternehmensgruppe wird von GovGuard nicht mehr geprüft. Das ist eine bekannte Grenze: Das Werkzeug ist für Behörden gebaut.

## Fachgespräch-Satz

„Was für eine Behörde nie gilt, prüft GovGuard gar nicht erst: Der Vorfilter verwirft es mit Begründung im Protokoll, statt dass das Audit-LLM eine Lücke erfindet; und eine Prüfregel fällt nur weg, wenn die Spezifikation ihre Bedingung ausdrücklich verneint, Schweigen bleibt eine offene Frage.“
