# Design-Brief: GovGuard Demo-UI (für Claude Design)

## Produkt
GovGuard prüft fiktive Behörden-Spezifikationen (DSGVO/SDM) und AWS-Architekturen
(BSI IT-Grundschutz, CIS, AWS FSBP) und liefert einen Audit-Report mit PASS/WARN/FAIL/N/A
je Prüfregel. Nutzer: Fachleute und Recruiter, in einer 15-min-Vorführung und danach beim Selbststudium.
UI-Sprache Deutsch, sachlich, Behörden-Look (ruhig, viel Weißraum, keine Spielerei).

## Harte Grenze: Umsetzung in Streamlit
Bitte nur Layouts entwerfen, die mit Streamlit-Bordmitteln gehen:
st.navigation (Seiten), st.columns, st.tabs, st.expander, st.dataframe mit Zeilenauswahl,
st.status/st.spinner, st.radio/st.selectbox, st.text_area, st.file_uploader, st.download_button,
st.html bzw. st.markdown mit etwas CSS. Keine eigenen React-Komponenten, kein Drag & Drop,
keine Animationen.

## Seiten
1. **Start & Hilfe** – Was GovGuard tut (3 Sätze), Warnbox „Keine echten, personenbezogenen
   oder Unternehmensdaten eingeben“, Kurzanleitung „Audit erstellen“, Lesehilfe für Reports
   (Status-Legende, was „herabgestuft“ und „Korrektur“ heißen, Beleg = Zeilen der Eingabe).
2. **Audits ansehen** (Hauptseite der Demo) – Auswahl eines gespeicherten Audits
   (5 Presets, später weitere). Kopf: Titel, Audit-Typ, Gesamtstatus als große Ampel,
   Modell (z. B. „Groq gpt-oss-120b“), Zähler je Status, Zähler des FAIL-Prüfers.
   Darunter **Master-Detail**: links Befundliste (Filter nach Status, Quelle), rechts das
   geprüfte Dokument mit Zeilennummern, die Belegzeilen des gewählten Befunds hervorgehoben.
   Detail je Befund: Titel, Normanker (z. B. „DSGVO Art. 9“), Status, Begründung, Empfehlung,
   Beleg, Querverweise, Korrekturen, Hinweis „herabgestuft von FAIL“ falls vorhanden.
3. **Audit erstellen** – Typ wählen (Spezifikation / Architektur), Preset laden oder Text
   einfügen (max. 100.000 Zeichen), Modell wählen (Groq | Claude Haiku über AWS) mit Hinweis
   zu Datenfluss in die USA bei Groq, Passwortfeld (nach der Demo), Start-Button.
   Laufzeit 1–3 Minuten: Fortschrittsanzeige. Danach gleiche Ansicht wie Seite 2 + JSON-Download.

## Daten je Befund (Feldnamen aus dem Code)
rule_id, title, primary_anchor, status (PASS|WARN|FAIL|N/A), line_start, line_end, evidence,
rationale, recommendation, cross_references[], downgraded_from, corrections[].
Report: audit_type, overall_status, model_id, retries, fail_judge{checked, confirmed,
downgraded, unavailable}, unassigned_corrections[], findings[] (30–150 Stück).

## Anhänge (echte Reports, Groq)
- `beispiel-reports/report-spec-meldeportal.json` + `data/input/presets/spec-meldeportal-gesundheit/input.md`
  (Markdown, 4 KB): 151 Befunde = 16 FAIL, 7 PASS, 120 WARN, 8 N/A; FAIL-Prüfer: 23 geprüft,
  16 bestätigt, 7 herabgestuft.
- `beispiel-reports/report-arch-antragseingang.json` + `data/input/presets/arch-antragseingang-fehlerhaft/template.json`
  (CloudFormation-JSON, 12 KB, 485 Zeilen): 166 Befunde = 29 FAIL, 28 PASS, 109 N/A.
Folgerung: Die Liste ist lang und meist WARN bzw. N/A. Standardansicht „FAIL zuerst“, N/A
eingeklappt. Die Dokumentansicht muss Markdown und lange JSON-Dateien tragen (Belege bis 200 Zeilen).

## Fortschritt während des Audits
Ein Audit dauert 20–60 s (Groq) bzw. bis 3 min. Anzeige als Schrittliste, z. B.:
„Ressourcen erkannt (12 Typen) → Paket 3 von 16 geprüft → FAIL-Prüfer: 23 FAILs → Report fertig“.

## Gewünscht
Mockups der drei Seiten (Desktop, 1440 px), die Statusfarben (barrierearm, nicht nur Farbe:
auch Icon/Text), und eine Variante der Befundliste für 150 Befunde (Gruppierung? Filter?).
