# Integration in Behörden-Werkzeuge

Research für Backup-Folien zur Produktstrategie. Ergänzt [Werkzeuge der Behörden je Prozessschritt](Werkzeuge%20der%20Beh%C3%B6rden%20je%20Prozessschritt.md) (Q1–Q39) und [Markt und Forschung](Markt%20und%20Forschung%20%E2%80%93%20Audits%20und%20Remediation.md) (P, K, L); was dort steht, wird nicht wiederholt. Stand: 2026-10-25.

## Kernaussage

Alle fünf Werkzeuge haben dokumentierte Import- oder API-Wege (CSV, XML, REST), aber keines nimmt nachweislich einen externen Prüfbericht oder OSCAL-Befunde an. Der leichteste Weg ist heute ein Export als CSV oder Excel, den sich ein Mensch im Werkzeug einliest. Eine Schnittstelle zu Befunden („Assessment Results“) ist in keinem Herstellerdokument belegt.

## Quellenregel

Wie im Schwesterdokument: Jede Aussage hat eine Quelle `[In]` mit URL; Abruf am 2026-10-25. Was ein Hersteller über sich selbst sagt, steht als „Herstellerangabe“. Eine Aussage ohne Primärquelle steht als „*Einschätzung:*“. Nicht Gefundenes steht als „nicht gefunden“. Primärquellen sind Hersteller-Doku, BSI und ITZBund. Ausnahme: I11 (Pressedienst) und I12 (Konferenzfolie eines Dritten) tragen nur Hinweise.

## Tabelle: Schnittstellen je Werkzeug

| Werkzeug | Format / Schnittstelle | Externe Befunde importierbar? | Quelle |
|---|---|---|---|
| verinice (veo, neue Generation) | CSV-Import in alle Felder aller Objekttypen; ohne Verknüpfungen, ohne Aktualisierung bereits importierter Objekte. Für wiederkehrenden Import verweist die Doku auf die REST API. | Teilweise: Als CSV-Zeilen ja (Pflichtfelder „Abkürzung“ und „Name“), als verknüpfte Befunde nein. Ein Befundtyp oder Prüfbericht-Import ist nicht gefunden. | [I1] |
| verinice (veo), API | HTTP-Endpunkte (GET, POST, PUT, DELETE) je Elementtyp, OpenAPI-Doku, JSON, Anmeldung per OpenID Connect (Keycloak) mit Passwort und Einmalcode. Updates mit ETag (`If-Match`). | Ja, technisch: Elemente lassen sich per POST anlegen, z. B. Szenarien oder Maßnahmen in einer Domäne. Ob ein Befund-Modell für GovGuard-Befunde existiert, ist nicht gefunden. | [I2] |
| verinice (veo), VNA-Importer | Importer für das VNA-Archivformat, das alle verinice-Versionen exportieren. Zweck ist die Migration aus classic verinice, nicht der Fremdimport. | Nein (nur eigenes Format). | [I3] |
| HiScout (GRC Suite) | „DataExchange“: XML-Import und -Export, beliebiges XML über XSLT, Export auch als CSV; Datenstruktur per Drag-and-drop konfiguriert; Steuerung (Überschreiben, Abbruch bei Fehler) per Weboberfläche oder Befehle im XML; automatisierbar per Workflow. Herstellerangabe. | Ja, plausibel für Datensätze: Fremd-XML wird per XSLT in die HiScout-Struktur umgewandelt. Ein fertiges Schema für externe Prüfbefunde ist nicht gefunden. Excel-Import, REST-API und OSCAL-Import sind in keiner Herstellerquelle gefunden. | [I4] |
| caralegal | Export: Verarbeitungsverzeichnis als PDF oder Excel; Import bestehender Dokumentation aus Excel, Word oder Confluence; Enterprise-Tarif nennt SSO, REST-API und Integrationen (z. B. LeanIX). Alles Herstellerangabe. | Unklar: Es gibt eine REST-API, aber keine öffentliche API-Doku mit Endpunkten. Ein Befund- oder DSFA-Import von außen ist nicht gefunden. Der Import ist ein Migrationsdienst (Excel, Word), kein Fremdbefund-Kanal. | [I5], [I6] |
| OneTrust (Privacy, DPIA) | Öffentliche REST-API-Doku (OAuth 2.0 Client Credentials, Scopes `ASSESSMENT` und `ASSESSMENT_READ`). Assessment-Endpunkte: Launch (auch in Bulk, ein Assessment je Inventory-ID), Submit Responses, Submit Child Question Responses, Manage Assessment Question Attachments, Approve, Complete. | Ja, technisch am besten belegt: Ein Fremdsystem kann Assessments anlegen, Antworten schreiben und Anhänge ablegen. Das Format eines Prüfberichts ist nicht vorgesehen; die Befunde müssten in Fragen/Antworten übersetzt werden. Ob ein Behördenkunde die API-Scopes freigeschaltet bekommt, ist nicht gefunden. | [I7] |
| V-Modell XT Bund | Projektassistent erzeugt aus der Auswahl (Tailoring) die Prozessdoku und Produktvorlagen; in Release 2.3 sind die Vorlagen **ODT** (nach Projekttyp „Vergabe“ und „Eigenentwicklung“), der Assistent ein Java-Programm (1.5.8). ITZBund nennt „praxisnahe Dokumentenvorlagen“, Open-Source-Projektassistent und Editor. | Nicht zutreffend: Das V-Modell ist ein Vorgehensmodell, keine Datenbank. Befunde gehören als Anhang oder Prüfvermerk zum Dokument, nicht in ein Importformat. Ob in Release 2.4 Vorlagen oder Assistent anders geliefert werden, ist **nicht verifiziert** (eine Suchzusammenfassung nennt einen Web-Assistenten, die BMI-Seite war nicht abrufbar). | [I8], [I9] |
| BSI Grundschutz++ (OSCAL) | OSCAL-Kataloge auf GitHub. Die Doku beschreibt die Modelle Catalog, Profile, Component Definition und **Assessment Results** („Enthalten die dokumentierten Resultate der Prüfungen“), außerdem SSP, Assessment Plan, POA&M. Sie nennt kein Werkzeug, das ein bestimmtes Modell importiert, und sagt nur, Hersteller von Grundschutz-Tools arbeiteten an der Einbindung. | Das Format für Befunde existiert (OSCAL Assessment Results). Ob verinice oder HiScout es lesen, ist nicht gefunden. | [I10] |

## Zusätzliche Befunde

- **Fachkonzept-Format:** Die Produktvorlagen des V-Modells XT Bund 2.3 sind laut Release Notes ODT [I9]; ob darunter die Lastenheft-Vorlage ist, wurde nicht einzeln geprüft. Wie behördeneigene Fachkonzepte ausgeliefert werden (Word, PDF, ODT), steht in keiner gefundenen Primärquelle; *Einschätzung:* Word oder ODT, aus Vorlagen erzeugt, danach oft als PDF verteilt.
- **OSCAL bei ISMS-Herstellern:** HiScout und verinice nennen in den gefundenen Herstellerseiten keinen OSCAL-Import. Ein HiScout-Vortrag auf der it-sa 2026 ist angekündigt („Excel versus OSCAL“, 28.10.2026, nur Ankündigung) [I11]. Das ist kein Funktionsbeleg.
- **Wer heute OSCAL-Befunde erzeugt:** Auf dem NIST OSCAL Adopters Workshop #46 (19.08.2026) zeigt NTT DATA offene Browser-Werkzeuge, die Assessment Plan, Assessment Results und POA&M als OSCAL erzeugen; das ist ein Drittprojekt auf GitHub, kein ISMS-Hersteller [I12].
- **Warnung des Vortrags:** OSCAL transportiere den Katalog, aber „noch nicht die ganze Bedeutung“; Werkzeuge ignorierten Eigenschaften, die sie nicht prüfen können [I12].

## Folgerungen für GovGuard

1. **Leichtester Weg heute: CSV oder Excel.** verinice (CSV-Import, Pflichtfelder „Abkürzung“ und „Name“) [I1], HiScout (CSV/XML) [I4] und caralegal (Excel) [I5] nehmen Tabellen entgegen. Ein Befund-Export als CSV mit Kennung, Titel, Schwere, Normbezug, Beleg braucht keine Zustimmung des Herstellers (*Einschätzung:* geringer Aufwand).
2. **Zweitleichtester Weg: Anbindung per API, wo sie öffentlich dokumentiert ist.** OneTrust [I7] und verinice veo [I2] haben dokumentierte Endpunkte; GovGuard könnte Befunde als Elemente oder Assessment-Antworten schreiben. Der Aufwand liegt in der Abbildung (Befund → Frage/Element) und in der Behördenfreigabe der Zugänge, nicht im Protokoll.
3. **OSCAL Assessment Results ist der saubere Zielstandard, aber noch ohne Abnehmer.** Das Format ist von BSI und NIST beschrieben [I10], doch kein ISMS-Hersteller belegt einen Import. GovGuard sollte das Befundmodell so schneiden, dass ein OSCAL-Export später aus denselben Feldern entsteht (siehe `Maschinenlesbare Formate für Compliance-Quellen.md`), aber heute nicht davon abhängen.
4. **V-Modell XT Bund ist kein Import-Ziel, sondern ein Anlass.** Der Einstieg ist das Lastenheft-Dokument (ODT/Word/PDF); GovGuard liest es ein und liefert einen Bericht als Anhang. Eine Integration in den Projektassistenten ist nicht angezeigt.
5. **Datenschutz-Werkzeuge: Kopplung über Dokument, nicht über Schnittstelle.** Für caralegal ist keine öffentliche API-Doku gefunden [I6]. Eine Behörde würde den Bericht als Anhang an die DSFA hängen. Das genügt für die Vorprüfung.

## Offene Lücken

- **Nicht gefunden:** öffentliche API-Doku von caralegal; HiScout-REST-API oder Excel-Import; OSCAL-Import bei verinice oder HiScout; Schnittstellen von ZeDIS; ein Fachkonzept-Standardformat der Behörden; Gültigkeit von V-Modell XT Bund 2.4 samt Vorlagenformat.
- **Nur Herstellerangabe:** alle Funktionen von HiScout DataExchange und caralegal; die Wirksamkeit der Importe in der Praxis ist nicht geprüft.

## Quellenverzeichnis

Alle Quellen abgerufen am 2026-10-25.

| Nr. | Quelle | URL |
|---|---|---|
| I1 | verinice-Handbuch (veo): CSV-Import | https://docs.eu.verinice.cloud/de/manual/CSV-Import.html |
| I2 | verinice-Entwicklerdoku: Getting started with the verinice API | https://docs.eu.verinice.cloud/de/developers/getting-started-with-the-verinice-api.html |
| I3 | verinice: easy migration to the new generation of verinice (VNA-Importer) | https://verinice.com/en/news/detail/easy-migration-to-the-new-generation-of-verinice |
| I4 | HiScout: DataExchange | https://www.hiscout.com/en/dataexchange/ |
| I5 | caralegal: Enterprise (REST-API, SSO, Import) | https://caralegal.eu/en/solutions/enterprise/ |
| I6 | caralegal: Verarbeitungsverzeichnis-Software (Export PDF/Excel) | https://caralegal.eu/en/data-protection-software/record-of-processing-activities/ |
| I7 | OneTrust Developer Portal: Launch Assessments in Bulk (mit Liste der Assessment-Endpunkte) | https://developer.onetrust.com/onetrust/reference/createbulkassessmentusingpost |
| I8 | ITZBund: V-Modell XT | https://www.itzbund.de/DE/Produkte/V-Modell-XT/v-modell-xt_node.html |
| I9 | ITZBund: V-Modell XT Bund 2.3 Release Notes (Produktvorlagen im ODT-Format, Projektassistent 1.5.8) | https://www.itzbund.de/static/download/Produkte/VMXT/V-Modell-XT-Bund-2.3-Release-Notes.pdf |
| I10 | BSI: Stand-der-Technik-Bibliothek, `documentation/OSCAL.md` | https://github.com/BSI-Bund/Stand-der-Technik-Bibliothek/blob/main/documentation/OSCAL.md |
| I11 | HiScout: Pressemitteilung „Grundschutz und OSCAL“ (Titel aus Suchergebnis; Seite nicht abrufbar, 403) | https://www.pressebox.de/pressemitteilung/hiscout-gmbh/Grundschutz-und-OSCAL/boxid/1308911 |
| I12 | NIST OSCAL Adopters Workshop #46, „BSI goes OSCAL“ (NTT DATA, 19.08.2026) | https://csrc.nist.gov/csrc/media/Projects/open-security-controls-assessment-language/images-media/2026/oscal-monthly-workshop-46-NTTData/BSI-goes-OSCAL_NIST-Workshop-46.pptx.pdf |

Hinweis zu I11 und I12: I11 ist ein Herstellertext auf einem Pressedienst (nur Titel und Suchauszug gesehen, nicht der Volltext); I12 ist eine Konferenzfolie eines Dritten (NTT DATA), keine Herstellerdoku. Beide tragen nur Hinweise, keine Funktionsbelege.
