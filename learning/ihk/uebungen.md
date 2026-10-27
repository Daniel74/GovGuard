# IHK Cloud Business Expert – Übung 1

## Szenario

**Wasen Digital GmbH (fiktiv)**: ein IT-Dienstleister aus Stuttgart, der für Kommunen, Landesbehörden in Baden-Württemberg und regulierte Mittelständler Fachanwendungen baut und betreibt. Er will seine Kundenprojekte von eigenen Servern in die Cloud bringen, kommt aber bei den Prüfungen zu Datenschutz und IT-Sicherheit nicht hinterher.

| Merkmal             | Ausprägung (Annahme für die Übung)                                                                                      |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Standort, Größe     | Stuttgart, ca. 250 Beschäftigte                                                                                         |
| Kunden              | Kommunen, Landesbehörden, Mittelstand mit Datenschutzpflichten                                                          |
| Cloud-Stand         | „Cloud too“: ca. 30 % der Anwendungen bei europäischen Cloud-Anbietern, der Rest im eigenen Rechenzentrum               |
| Projekte            | ca. 25 Cloud-Projekte pro Jahr: ca. 15 Migrationen bestehender Anwendungen, ca. 10 Neuentwicklungen direkt in der Cloud |
| Prüfteam            | 4 Fachleute für Datenschutz und Informationssicherheit                                                                  |
| Vorgaben der Kunden | DSGVO, BSI IT-Grundschutz, Daten nur in der EU                                                                          |

„Cloud too“ heißt: Cloud ist eine Option neben dem eigenen Rechenzentrum, aber nicht die erste Wahl.

**Wo GovGuard ansetzt.** In beiden Projektarten müssen Fachkonzept, Datenschutz und IT-Sicherheit vor dem Start geprüft werden. Bei einer Neuentwicklung entsteht das Fachkonzept neu; bei einer Migration muss es überarbeitet werden, weil der Cloud-Anbieter als neuer Auftragsverarbeiter dazukommt. GovGuard prüft diese Fachkonzepte. Die Architektur, also die Konfiguration in der Ziel-Cloud, prüfen etablierte Open-Source-Werkzeuge (Punkt 8).

## Pitch (ca. 4 Minuten)

**Ausgangslage (25 s).** 86 % der Unternehmen in Deutschland nutzen die Cloud, aber im Schnitt laufen erst 47 % ihrer Anwendungen dort. Was bremst, ist selten die Technik, sondern die Frage nach Sicherheit und Datenschutz: 95 % nennen Vertrauen in IT-Sicherheit, Datenschutz und Compliance als Muss-Kriterium.

**Unser Fall (40 s).** Die Wasen Digital GmbH aus Stuttgart will jedes Jahr rund 25 Kundenprojekte in die Cloud bringen, gut die Hälfte davon Migrationen bestehender Anwendungen, der Rest Neuentwicklungen. Jedes Projekt muss vorher DSGVO und BSI IT-Grundschutz nachweisen. Dafür gibt es vier Fachleute, die jedes Projekt-Dokument von Hand prüfen: Fachkonzept, DSFA, Löschregeln, Grundschutz-Check und Cloud-Vorlage. Bei einer Migration kommen das Migrationskonzept und der Abgleich der alten gegen die neue Fassung dazu. Ein Projekt wartet darauf im Schnitt vier Wochen, und Fehler fallen oft erst bei der Abnahme auf. Angenommen sind das 6 Personentage bei einer Neuentwicklung und 10 bei einer Migration; bei 700 € Tagessatz kosten die Prüfungen rund 147.000 € im Jahr.

**Die Lösung (25 s).** GovGuard prüft ein Fachkonzept in Minuten auf Datenschutz und IT-Sicherheit, bei Neuentwicklungen ebenso wie beim Umzug bestehender Anwendungen. Die Architektur in der Ziel-Cloud prüfen bewährte Open-Source-Werkzeuge; dafür baut Wasen nichts Eigenes. In Stufe zwei bietet Wasen es als SaaS an: Behörden als Auftraggeber prüfen damit selbst die Fachkonzepte ihrer Dienstleister. So sinkt die größte Hürde zur Cloud kostengünstiger und zuverlässiger.

**Fehler und Folgekosten (25 s).** Auch gute Fachleute übersehen Fehler: Reviews finden laut Forschung im Median nur 60 %. Ein Fehler, der erst nach der Auslieferung auffällt, kostet bei großen Systemen oft das Hundertfache, bei kleinen etwa das Fünffache. Ein Datenleck kostet in Deutschland im Schnitt 3,87 Millionen Euro. Menschen und Werkzeuge finden unterschiedliche Fehler. Deshalb ergänzt GovGuard die Fachleute, statt sie zu ersetzen.

**CapEx, OpEx und TCO (45 s).**

- Einmalig investiert Wasen rund 38.000 € in Arbeitszeit, ganz ohne gekaufte Server: für den Piloten mit Anbindung an ein europäisches Modell, die Anbindung an Prozesse und Systeme und die Architekturprüfung mit Open-Source-Werkzeugen. Das ist CapEx. Die Entwicklung davor trage ich selbst.
- Laufend kostet GovGuard rund 5.800 € im Jahr: unter 200 € für Betrieb und Modell, der Rest für die Pflege der Prüfregeln und der Schnittstellen. Das ist OpEx.
- Rund zwei Drittel der Prüfarbeit prüfen GovGuard und die Open-Source-Werkzeuge vor. Dort bewerten die Fachleute nur noch Warnungen und Verstöße. Wir nehmen an, dass sich dieser Teil halbiert: rund 47.000 € weniger im Jahr. Den Abgleich alter gegen neue Fassung und den Grundschutz-Check machen weiter die Fachleute.
- Die TCO, also alle Kosten über drei Jahre: ohne GovGuard 441.000 €, mit GovGuard rund 354.000 €. Das sind rund 87.000 € weniger, die Investition ist nach rund 11 Monaten bezahlt, und die Wartezeit sinkt von vier auf ein bis zwei Wochen.

**Betrieb nur in der EU (45 s).**

- Heute läuft der Prototyp bei US-Anbietern: Oberfläche bei Streamlit, Modell bei Groq.
- Das Modell GPT-OSS 120B ist offen. Europäische Anbieter ohne US-Mutterkonzern wie STACKIT, IONOS oder Scaleway betreiben es in der EU und rechnen pro Nutzung ab. Ein Audit kostet dort Cent-Beträge und dauert etwa dreimal so lange wie bei Groq, also Sekunden bis wenige Minuten.
- Bevor ich Piloten suche, schließe ich eine Entwicklungsphase ab: Befunde werden nach Fundstelle gebündelt, die Prüfregeln auf die Dokumente für Neuentwicklung und Migration abgestimmt und mit öffentlichen, wissenschaftlichen oder synthetischen Musterfällen getestet.
- Im Piloten läuft GovGuard als Docker-Container auf einem Server bei Wasen, ohne Zusatzkosten, und wird an den europäischen Modellanbieter angebunden, den Wasen wählt. Später kann GovGuard serverlos laufen, etwa bei Scaleway: Dann kostet der Betrieb nur, wenn jemand prüft.
- Ist der Pilot erfolgreich, folgen Datenhaltung und die Anbindung an Prozesse und Systeme.

**Abschluss (10 s).** GovGuard ersetzt keine Freigabe. Aber es sorgt dafür, dass mehr Projekte schneller und sicher in die Cloud kommen.

## Zahlen, Fakten und Schlussfolgerungen

Die Belege hinter dem Pitch, als roter Faden in fünf Fragen: Wo steht der Markt (A)? Was kostet die Prüfarbeit bei Wasen heute (B)? Wie sieht die Lösung aus, und wo läuft sie (C)? Wie kommt sie zu Wasen (D)? Lohnt es sich (E)? Jeder Unterpunkt beginnt mit „Kurz gesagt“ und endet mit einer Schlussfolgerung. Annahmen für die Übung sind als solche markiert.

**Übersicht**

| Nr. | Frage | Antwort in einem Satz |
| --- | --- | --- |
| 1 | Wie verbreitet ist Cloud, und was bremst? | 86 % nutzen Cloud, aber erst 47 % der Anwendungen laufen dort; Vertrauen in Sicherheit und Compliance ist Muss-Kriterium Nr. 1. |
| 2 | Migration oder Neuentwicklung: Wo hilft GovGuard? | Reines Rehosting ist die Minderheit; GovGuard hilft bei Neuentwicklungen am meisten, bei Migrationen als ein Baustein. |
| 3 | Welche Dokumente kommen durch die Cloud dazu? | Auf drei Ebenen: einmal je Behörde, einmal je Cloud-Anbieter oder -Dienst, und je Projekt; ein Migrationskonzept nur bei Migration. |
| 4 | Wie viel Arbeit machen die Dokumente je Projekt? | Annahme: 31 bzw. 33 Personentage, davon Prüfen 6 bei Neuentwicklung und 10 bei Migration; 147.000 € im Jahr, zwei Drittel davon vorprüfbar. |
| 5 | Wie viele Fehler übersehen Menschen, was kostet das? | Reviews finden im Median 60 % der Fehler; spät gefundene Fehler kosten das 5- bis 100-Fache. |
| 6 | Wie bleiben die Daten in der EU? | GPT-OSS 120B bei europäischen Anbietern ohne US-Mutterkonzern; ein Audit kostet Cent und dauert etwa 3-mal so lange wie bei Groq. |
| 7 | Serverlos oder Container? | Serverlos geht nur bei Scaleway; der Pilot läuft als Container auf einem Server bei Wasen. |
| 8 | Architektur-Audits selbst entwickeln? | Nein: Open-Source-Werkzeuge nutzen und eigene Regeln für europäische Clouds ergänzen. |
| 9 | Wie sieht der Pilot aus? | Erst schließe ich die Entwicklungsphase ab, dann sucht GovGuard Piloten; bei Wasen kostet der Pilot rund 24 PT, für die Anbindung an den EU-Modellanbieter und vor allem für alte Dokumente mit Soll. |
| 10 | Wäre GovGuard als SaaS für Wasen interessant? | Eher nicht; Selbstbetrieb mit Wartungsvertrag passt besser. |
| 11 | Lohnt sich GovGuard? | Für Wasen ab rund 20 % Ersparnis an den vorgeprüften Projekt-Dokumenten; bei angenommenen 50 % amortisiert es sich in rund 11 Monaten. |

### A. Markt und Bedarf

Wie verbreitet Cloud ist, was bremst und welche Projektarten es gibt.

#### 1. Cloud-Nutzung und Hürden in Deutschland

**Kurz gesagt:** Fast alle Unternehmen nutzen Cloud, aber nur für etwa die Hälfte ihrer Anwendungen. Das wichtigste Kriterium bei der Wahl eines Anbieters ist Vertrauen in Sicherheit, Datenschutz und Compliance.

**Nutzung** (Bitkom Cloud Report 2026, 603 Unternehmen ab 20 Beschäftigten)

| Befund                                                  | Wert                                                    |
| ------------------------------------------------------- | ------------------------------------------------------- |
| Unternehmen, die Cloud nutzen                           | 86 % (Vorjahr 90 %)                                     |
| Unternehmen, die Cloud planen oder diskutieren          | 14 %                                                    |
| Anteil der Anwendungen in der Cloud, 2025 → in 5 Jahren | 47 % → 58 %                                             |
| Strategie unter Nutzern                                 | „Cloud first“ 33 %, „Cloud too“ 28 %, „Cloud only“ 17 % |
| Bieten eigene Produkte als Cloud-Dienst an / planen es  | 22 % / 23 %                                             |

**Hürden** (Bitkom Cloud Report 2026)

| Befund                                                                                      | Wert           |
| ------------------------------------------------------------------------------------------- | -------------- |
| Muss-Kriterium bei der Anbieterwahl: Vertrauen in IT-Sicherheit, Datenschutz und Compliance | 95 % (Platz 1) |
| Muss-Kriterium: Verschlüsselung der Daten                                                   | 89 %           |
| Muss-Kriterium: Schutz vor Zugriff durch den Cloud-Anbieter selbst                          | 87 %           |
| Rechtliche Vorgaben für souveräne Cloud sind unklar oder widersprüchlich                    | 53 %           |
| Behörden sollen stärker auf europäische oder souveräne Cloud setzen                         | 90 %           |

Für Bundesbehörden gilt zusätzlich: Externe Cloud-Dienste brauchen ein C5-Testat. Ein C5-Testat ist der Bericht eines Wirtschaftsprüfers, dass ein Cloud-Anbieter den Kriterienkatalog C5 des BSI erfüllt.

Vorsicht bei der Formulierung: Bitkom fragt nicht nach der „größten Hürde“, sondern nach Muss-Kriterien. Verteidigbar ist: „Vertrauen in Sicherheit, Datenschutz und Compliance ist das wichtigste Muss-Kriterium.“

**Schlussfolgerung:** Die Frage ist nicht mehr, *ob* Unternehmen in die Cloud gehen, sondern *wie viel und wie sicher*. Wer den Nachweis von Datenschutz und IT-Sicherheit schneller und gleichmäßiger macht, setzt genau am wichtigsten Kriterium an. Für die öffentlichen Kunden von Wasen wiegt das noch schwerer, weil dort zusätzlich C5 und souveräne Anbieter gefordert sind.

#### 2. Migration oder Neuentwicklung: Wo hilft GovGuard?

**Kurz gesagt:** Nur ein Viertel der Unternehmen zieht Anwendungen unverändert um; die meisten passen sie beim Umzug an, und neue Anwendungen entstehen fast immer direkt in der Cloud. Datenschutz und Compliance sind die häufigste Herausforderung bei Migrationen.

Rehosting (auch Lift-and-Shift) heißt: Eine bestehende Anwendung zieht fast unverändert in die Cloud. Neuentwicklung direkt in der Cloud (cloud-nativ) heißt: Die Anwendung wird von Anfang an für die Dienste eines Cloud-Anbieters gebaut. Dazwischen liegen Replatforming und Refactoring, bei denen die Anwendung beim Umzug teilweise angepasst wird.

**Was die Daten sagen**

| Befund                                     | Wert                                                                                                      | Quelle                                                               |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Migrationsansatz deutscher Unternehmen     | Lift-and-Shift 24 %, Lift-and-Extend 49 %, Lift-and-Reshape (Replatforming) 35 %; Mehrfachnennung         | CIO/COMPUTERWOCHE „Cloud-Migration 2025“, 346 Befragte, Oktober 2024 |
| Größte Herausforderungen bei der Migration | Datenschutz und Compliance 37 %, Datensicherheit 32 %                                                     | CIO/COMPUTERWOCHE „Cloud-Migration 2025“                             |
| Unternehmen mit Migrationsplänen           | 91 % wollen bis 2028 mindestens 40 % ihrer Anwendungen migrieren                                          | Lünendonk, zitiert im Digitalbusiness Magazin                        |
| Kosten und Zeit von Migrationen            | im Schnitt 14 % mehr Migrationskosten als geplant; 38 % der Unternehmen mit mehr als einem Quartal Verzug | McKinsey 2021                                                        |
| Neue Anwendungen                           | Prognose: über 95 % neuer digitaler Workloads auf cloud-nativen Plattformen bis 2025 (2021: 30 %)         | Gartner 2021, Prognose, nicht überprüft                              |

**Was das für GovGuard heißt**

| Projektart                           | Fachkonzept                      | Datenschutz und IT-Sicherheit                                                                                                                                                                  | Rolle von GovGuard                                                                                                                          |
| ------------------------------------ | -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Migration (Rehosting, Replatforming) | existiert, ist aber oft veraltet | Der Cloud-Anbieter kommt als Auftragsverarbeiter dazu; Verträge, technische und organisatorische Maßnahmen und die Modellierung nach IT-Grundschutz (Baustein OPS.2.2 Cloud-Nutzung) ändern sich | Prüft das überarbeitete Fachkonzept; den Abgleich mit der alten Fassung machen vorerst die Fachleute; das größte Risiko liegt aber in der Konfiguration der Ziel-Cloud, und die prüfen Open-Source-Werkzeuge |
| Neuentwicklung cloud-nativ           | entsteht neu                     | Datenschutz durch Technikgestaltung (Art. 25 DSGVO) muss von Anfang an im Konzept stehen                                                                                                       | Größter Hebel: Prüfung schon am ersten Entwurf, bevor Code entsteht                                                                         |

**Schlussfolgerung:** GovGuard nützt bei Neuentwicklungen am meisten, weil Fehler im Fachkonzept dort am billigsten zu beheben sind (Punkt 5). Bei Migrationen bleibt GovGuard nützlich, ist aber nur ein Baustein neben der Konfigurationsprüfung. Da Migrationen oft teurer und später fertig werden als geplant, zählt jede Woche, die eine schnellere Vorprüfung spart.

### B. Die Prüfarbeit bei Wasen heute

Welche Dokumente die Cloud mit sich bringt, wie viel Arbeit sie machen und was beim Prüfen von Hand durchrutscht.

#### 3. Welche Dokumente kommen durch die Cloud dazu?

**Kurz gesagt:** Wer eine Anwendung in die Cloud bringt, braucht mehr als Fachkonzept, DSFA, Löschkonzept, Schutzbedarf und Grundschutz-Check, die die Prozesskette der Abschlusspräsentation (Backup-Folie 18) nennt. Dazu kommen Datenschutz-Dokumente mit Bezug auf den Cloud-Anbieter und cloud-spezifische Sicherheitsdokumente nach BSI-Baustein OPS.2.2 „Cloud-Nutzung“. Eine Migration braucht zusätzlich ein Migrationskonzept und muss die bestehenden Dokumente nachziehen. Nicht jedes Dokument entsteht je Projekt: Manche gelten einmal für die ganze Behörde, manche einmal je Cloud-Anbieter oder Cloud-Dienst.

**Was die Abschlusspräsentation schon sagt.** Die Prozesskette auf Backup-Folie 18 beschreibt eine Neuentwicklung: Sie beginnt mit dem Schreiben des Fachkonzepts. Bei einer Migration gibt es Fachkonzept, DSFA, Löschkonzept und Grundschutz-Check schon, aber für den alten Betrieb im eigenen Rechenzentrum. Die Präsentation trennt die beiden Fälle nicht und nennt keine Dokumente, die erst durch die Cloud entstehen.

**Wie oft ein Dokument entsteht: drei Ebenen**

| Ebene | Wann es entsteht | Rolle im Projekt |
| --- | --- | --- |
| Je Behörde | einmal für alle Projekte | Rahmen, an dem jedes Projekt gemessen wird |
| Je Cloud-Anbieter oder Cloud-Dienst | einmal, beim ersten Projekt auf diesem Anbieter oder Dienst; danach nur aktualisieren | wird von jedem weiteren Projekt mitgenutzt; je Projekt nur prüfen, ob es das Projekt abdeckt |
| Je Projekt | für jedes Projekt neu | eigentlicher Prüfgegenstand |

Ein Cloud-Dienst ist ein einzelnes Angebot eines Anbieters, etwa ein Kubernetes-Cluster oder ein Sprachmodell-Dienst. Im Szenario ist „die Behörde“ der Auftraggeber von Wasen; Wasen hält die Verträge mit dem Cloud-Anbieter als Unterauftragsverarbeiter, die Behörde muss ihn genehmigen.

**Je Behörde: einmal für alle Projekte**

| Dokument | Grundlage | Neuentwicklung | Migration | GovGuard |
| --- | --- | --- | --- | --- |
| Strategie für die Cloud-Nutzung mit Machbarkeitsstudie | OPS.2.2.A1 | einmal vorhanden | ebenso | Maßstab für den Abgleich, kein Prüfgegenstand je Projekt |
| Sicherheitsrichtlinie für die Cloud-Nutzung | OPS.2.2.A2 | einmal vorhanden | ebenso | Maßstab für den Abgleich |
| Verzeichnis von Verarbeitungstätigkeiten als Ganzes | DSGVO Art. 30 | einmal vorhanden; je Projekt ein Eintrag (unten) | ebenso | – |

**Je Cloud-Anbieter oder Cloud-Dienst: einmal, beim ersten Projekt darauf**

| Dokument | Grundlage | Neuentwicklung | Migration | GovGuard |
| --- | --- | --- | --- | --- |
| Vertrag zur Auftragsverarbeitung, Liste der Unterauftragsverarbeiter | DSGVO Art. 28 | neu beim ersten Projekt | ebenso; bisher eigener Betrieb ohne Anbieter | Regeln im Katalog; je Projekt Abgleich mit dem Fachkonzept (Orte, Datenarten) |
| Prüfung von Übermittlungen in Drittländer | DSGVO Art. 44–49 | nur wenn Daten oder Zugriffe die EU verlassen | ebenso | Regeln im Katalog |
| Anforderungsprofil, Leistungsbeschreibung, Vertrag (Standort, Löschung, Kündigung, Subunternehmen) | OPS.2.2.A8, A9 | neu beim ersten Projekt | ebenso | je Projekt Abgleich mit Fachkonzept und DSFA |
| Nachweis des Anbieters, z. B. C5-Testat | OPS.2.2.A13 | einmal einholen, regelmäßig erneuern | ebenso | kein Prüfgegenstand; je Projekt prüfen Fachleute, ob der Geltungsbereich die genutzten Dienste erfasst |
| Service-Definition und Abgrenzung der Verantwortung | OPS.2.2.A3, A4 | je Cloud-Dienst | ebenso | neue Regelquelle nötig |
| Planung der Einbindung: Schnittstellen, Netz, Administration, Datenmanagement | OPS.2.2.A6 | je Cloud-Dienst | ebenso; ersetzt die bisherige Einbindung | neue Regelquelle nötig |
| Sicherheitskonzept für die Cloud-Nutzung | OPS.2.2.A7 | je Cloud-Dienst | ebenso; ergänzt das bisherige Sicherheitskonzept | neue Regelquelle nötig |
| Notfallkonzept für den Cloud-Dienst | OPS.2.2.A11 | je Cloud-Dienst | ebenso; ersetzt das bisherige Notfallkonzept | neue Regelquelle nötig |
| Ausstieg: geordnete Beendigung, Portabilität | OPS.2.2.A14, A15 | je Anbieter | ebenso | neue Regelquelle nötig |

**Je Projekt: für jedes Projekt neu**

| Dokument | Grundlage | Neuentwicklung | Migration | GovGuard |
| --- | --- | --- | --- | --- |
| Fachkonzept | Folie 18, Schritt ① | schreiben | überarbeiten: Betrieb, Datenflüsse, Anbieter | Prüfen heute; Abgleich alt gegen neu als Option (Punkt 11) |
| DSFA | DSGVO Art. 35 | neu, wenn hohes Risiko; ähnliche Verarbeitungen dürfen eine gemeinsame DSFA haben (Abs. 1 Satz 2) | überprüfen, weil sich das Risiko ändert (Abs. 11) | Regeln im Katalog; Abgleich alt gegen neu |
| Eintrag im Verzeichnis von Verarbeitungstätigkeiten | DSGVO Art. 30 | neuer Eintrag | Eintrag ändern: Empfänger, Übermittlungen, technische und organisatorische Maßnahmen | Regeln im Katalog |
| Löschregeln des Verfahrens | DSGVO Art. 5, 17 | neu | zusätzlich Altdaten im eigenen Rechenzentrum löschen | Prüfen heute |
| Schutzbedarf und Grundschutz-Check | Folie 18, Schritt ④ | neu | neu modellieren, weil OPS.2.2 dazukommt | Abgleich mit ① und ③ (Roadmap) |
| Migrationskonzept mit Testlauf | OPS.2.2.A5, A10 | entfällt | neu | neue Regelquelle nötig |
| Cloud-Vorlage (Infrastructure as Code) | Folie 18, Schritt ⑥ | neu | neu, bisher keine | Open-Source-Werkzeuge (Punkt 8) |

OPS.2.2.A1–A4 sind Basis-Anforderungen (MUSS), A5–A14 Standard-Anforderungen (SOLLTE), A15 gilt bei erhöhtem Schutzbedarf. „Regeln im Katalog“ heißt: GovGuard hat dafür heute schon Prüfregeln, 13 Regeln zu Art. 28, 14 zu Art. 30, 8 zu Art. 35 und 11 zu Art. 44–49; sie prüfen bisher aber nur das Fachkonzept, nicht das jeweilige Dokument selbst.

**Was das für die Prozesskette heißt**

| Schritt auf Folie 18 | Neuentwicklung | Migration |
| --- | --- | --- |
| ① Fachkonzept | schreiben, GovGuard prüft | bestehendes Fachkonzept überarbeiten; GovGuard prüft die neue Fassung, der Abgleich mit der alten ist eine Option |
| ③ Datenschutz | DSFA, Verzeichnis, Auftragsverarbeitung neu | dieselben Dokumente nachziehen; das Risiko einer veralteten DSFA ist hier am größten |
| ④ IT-Sicherheit | Schutzbedarf, Grundschutz-Check, dazu OPS.2.2-Dokumente | zusätzlich Migrationskonzept; Modellierung ändert sich, weil OPS.2.2 dazukommt |
| ⑥ Umsetzung | Cloud-Vorlage neu | Cloud-Vorlage neu, Testlauf der Migration |

**Schlussfolgerung:** Die Unterscheidung verändert vor allem, *was* GovGuard tun muss. Bei einer Neuentwicklung ist es das Prüfen neuer Dokumente entlang der Kette. Bei einer Migration ist es das Abgleichen: Hat jedes bestehende Dokument die Änderung durch die Cloud mitgemacht? Das stärkt die Alleinstellung „Abgleichen“ aus der Präsentation.

Die Ebenen bestimmen, *wann* geprüft wird. Je Projekt prüft GovGuard die Projekt-Dokumente. Dokumente je Behörde, Anbieter oder Dienst prüft man einmal gründlich; danach sind sie der Maßstab, gegen den jedes Projekt abgeglichen wird. Für Wasen heißt das: Das erste Projekt auf einem neuen Cloud-Dienst trägt den Aufwand für dessen Dokumente; jedes weitere Projekt ist billiger. Für die cloud-spezifischen Dokumente nach OPS.2.2 hat GovGuard heute keine Prüfregeln; dafür wäre OPS.2.2 eine neue Regelquelle im Build.

#### 4. Dokumentenfluss und Prüfaufwand je Projekt

**Kurz gesagt:** Laut Annahme arbeitet Wasen an den Dokumenten einer Neuentwicklung 31 Personentage, an denen einer Migration 33. Ein Viertel davon ist internes Prüfen: 6 bzw. 10 Personentage je Projekt, zusammen rund 210 Personentage oder 147.000 € im Jahr. Rund zwei Drittel davon können GovGuard und Open-Source-Werkzeuge heute vorprüfen.

**Dokumentenfluss je Projekt (Hypothese)**

Wie Dokumente zwischen Wasen und der Behörde und zwischen den Abteilungen laufen, ist nicht erhoben. Die Tabelle ist eine Annahme, die eine Erhebung prüfen müsste; sie zeigt alle Schritte, damit sichtbar wird, wo die Zeit hängt. Zeiten in Personentagen je Projekt, für alle Projekt-Dokumente zusammen.

| Schritt | Wer | Neuentwicklung | Migration | GovGuard heute | GovGuard laut Roadmap |
| --- | --- | --- | --- | --- | --- |
| 1 Erstellen bzw. überarbeiten | Projektteam von Wasen; der Fachbereich der Behörde liefert zu | 20 | 16 (überarbeiten 12, Migrationskonzept 4) | Selbstprüfung durch die Autorin oder den Autor vor der Abgabe | – |
| 2 Review intern | Prüfteam von Wasen | 4 | 7 (davon Abgleich alt gegen neu 2,5) | Vorprüfung (Spec-Audit) | Abgleich zwischen Dokumenten |
| 3 Nachbesserung | Projektteam | 3 | 4 | Empfehlung als Text (Remediation Stufe 0) | Textvorschlag, den der Code nachprüft (Stufe 2) |
| 4 Re-Review und Freigabe intern | Prüfteam | 2 | 3 | erneute Vorprüfung | Abgleich der Fassungen vor und nach der Nachbesserung |
| 5 Review durch die Behörde | Datenschutz- und IT-Sicherheitsbeauftragte der Behörde | 3 | 4 | – | Stufe zwei: Die Behörde prüft selbst mit GovGuard |
| 6 Nachbesserung nach Rückmeldung | Projektteam und Prüfteam von Wasen | 2 | 3 | erneute Vorprüfung | Textvorschlag, Abgleich |
| 7 Freigabe durch die Behörde | Behörde | – | – | – | Freigabe im Audit-Protokoll |

Remediation heißt: Behebung eines Befunds. Die Stufen stammen aus der Abschlusspräsentation (Folie 14): Stufe 0 gibt nur einen Hinweis, Stufe 1 einen Textvorschlag, in Stufe 2 prüft der Code den Vorschlag gegen dieselbe Prüfregel nach.

**Was das im Jahr kostet** (10 Neuentwicklungen, 15 Migrationen, 700 € je Personentag)

| Block | Neuentwicklung | Migration | Jahr | Kosten |
| --- | --- | --- | --- | --- |
| Erstellen (Schritt 1) | 20 PT | 16 PT | 440 PT | 308.000 € |
| Prüfen intern (Schritte 2 und 4) | 6 PT | 10 PT | 210 PT | 147.000 € |
| Nachbessern (Schritte 3 und 6) | 5 PT | 7 PT | 155 PT | 108.500 € |
| **Summe bei Wasen** | **31 PT** | **33 PT** | **805 PT** | **563.500 €** |
| Review durch die Behörde (Schritt 5) | 3 PT | 4 PT | 90 PT | trägt die Behörde |

Was das zeigt:

- **Prüfen ist ein Viertel:** Die Wirtschaftlichkeit (Punkt 11) betrachtet nur das interne Prüfen, also 26 % der Dokumentenarbeit bei Wasen.
- **Nachbessern ist der nächste Hebel:** Es kostet rund drei Viertel so viel wie das Prüfen, und jede Schleife über die Behörde (Schritte 5 und 6) kostet zusätzlich Wartezeit und Vertrauen beim Kunden. Halbierte Remediation die Nachbesserung, wären das rund 78 PT oder 54.000 € im Jahr; das ist eine Annahme auf einer Annahme und steht deshalb nicht in der Rechnung.
- **Erstellen bleibt beim Menschen:** Es ist der größte Block, aber GovGuard schreibt keine Dokumente, weil die Fakten vom Menschen kommen (Folie 16).

**Prüfaufwand je Projekt** (Annahme, in Personentagen, nur Dokumente je Projekt aus Punkt 3)

| Dokument | Neuentwicklung: prüfen | Migration: prüfen | Migration: abgleichen alt gegen neu | Vorprüfung durch |
| --- | --- | --- | --- | --- |
| Fachkonzept | 2 | 2 | 1 | GovGuard; Abgleich von Hand |
| DSFA (Durchschnitt, nicht jedes Projekt braucht eine) | 1 | 1 | 0,5 | GovGuard; Abgleich von Hand |
| Verzeichnis-Eintrag und Löschregeln | 0,5 | 0,5 | 0,5 | GovGuard; Abgleich von Hand |
| Migrationskonzept mit Testlauf | – | 1,5 | – | GovGuard, mit OPS.2.2 aus der Entwicklungsphase (Punkt 9) |
| Schutzbedarf und Grundschutz-Check | 1,5 | 1,5 | 0,5 | keine, erst laut Roadmap, auch kein Abgleich |
| Cloud-Vorlage (Infrastructure as Code) | 1 | 1 | – | Open-Source-Werkzeuge (Punkt 8) |
| **Summe je Projekt** | **6** | **7,5** | **2,5** | Migration zusammen **10** |
| davon vorgeprüft | 4,5 | 6 | 0 | Migration zusammen 6 |

Abgleichen heißt: prüfen, ob ein bestehendes Dokument die Änderung durch die Cloud mitgemacht hat. GovGuard prüft heute nur die neue Fassung; den Abgleich mit der alten machen in dieser Rechnung die Fachleute, als Funktion von GovGuard ist er eine Option (Punkt 11). Ohne Vorprüfung bleiben damit Abgleich und Grundschutz-Check. Dokumente je Behörde und je Cloud-Anbieter oder -Dienst bleiben zur Vereinfachung außen vor.

Im Jahr sind das 10 × 6 + 15 × 10 = 210 Personentage Prüfung, davon 10 × 4,5 + 15 × 6 = 135 vorprüfbar (64 %). Das ist rund ein Viertel der Arbeitszeit der vier Fachleute; den Rest binden Beratung, Dokumente je Behörde und Anbieter, Kundenaudits und Vorfälle.

**Schlussfolgerung:** Die Prüfarbeit hängt an der Projektart: Eine Migration kostet 10 statt 6 Personentage, ein Viertel davon ist Abgleich. Für die Wirtschaftlichkeit (Punkt 11) zählt der heute vorprüfbare Teil, 135 von 210 Personentagen. Alle Zeiten sind Annahmen; wie Dokumente wirklich zwischen Wasen, Prüfteam und Behörde laufen, müsste eine Erhebung zeigen.

#### 5. Fehler bei manuellen Prüfungen und ihre Kosten

**Kurz gesagt:** Reviews durch Fachleute finden im Median etwa 60 % der Fehler. Je später ein Fehler auffällt, desto teurer wird er, je nach Systemgröße 5- bis 100-mal.

Belastbare Zahlen zu manuellen Compliance-Audits gibt es kaum. Die Forschung misst vor allem Reviews in der Softwareentwicklung, also das systematische Durchlesen von Anforderungen, Entwürfen oder Code durch Fachleute. Das ist dem Prüfen von Fachkonzepten und Architekturen am nächsten. Eigene Messwerte von GovGuard nutze ich bewusst nicht: GovGuard hat keinen soliden Messplan, die wenigen Musterfälle sind keine Statistik.

**Wie viele Fehler finden Menschen?**

| Befund                                                                                         | Wert                                       | Quelle                                                              |
| ---------------------------------------------------------------------------------------------- | ------------------------------------------ | ------------------------------------------------------------------- |
| Anteil der Fehler, die Reviews finden                                                          | 31–93 %, Median ca. 60 %                   | Boehm & Basili 2001, IEEE Computer (Auswertung zahlreicher Studien) |
| Design- und Code-Inspektionen zusammen                                                         | entfernen meist mindestens 70 % der Fehler | Capers Jones 1996, IEEE Computer                                    |
| Gezielte Reviews mit festen Blickwinkeln (z. B. Nutzer, Tester) gegenüber Reviews ohne Vorgabe | finden 35 % mehr Fehler                    | Boehm & Basili 2001                                                 |
| Reviews, Analysewerkzeuge und Tests                                                            | finden unterschiedliche Arten von Fehlern  | Boehm & Basili 2001                                                 |
| Fehler, die erst spät im Entwicklungsprozess gefunden werden                                   | über die Hälfte                            | NIST 2002                                                           |

**Was kosten übersehene Fehler?**

| Befund                                                                       | Wert                                                                       | Quelle                         |
| ---------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------ |
| Fehler nach der Auslieferung beheben, statt in Anforderung oder Design       | oft 100-mal teurer; bei kleinen, unkritischen Systemen eher 5-mal          | Boehm & Basili 2001            |
| Aufwand für vermeidbare Nacharbeit in Softwareprojekten                      | 40–50 % des Gesamtaufwands                                                 | Boehm & Basili 2001            |
| Kosten unzureichender Tests für die US-Wirtschaft                            | 22,2–59,5 Mrd. $ pro Jahr                                                  | NIST 2002                      |
| Durchschnittliche Kosten eines Datenlecks in Deutschland                     | 3,87 Mio. € (Vorjahr 4,9 Mio. €)                                           | IBM Cost of a Data Breach 2025 |
| Ersparnis durch breiten Einsatz von KI und Automatisierung in der Sicherheit | 1,9 Mio. $ weniger pro Datenleck, 80 Tage schneller erkannt und eingedämmt | IBM Cost of a Data Breach 2025 |

**Wie gut prüfen Maschinen?**

| Befund                                                                                | Wert                              | Quelle                                                                                          |
| ------------------------------------------------------------------------------------- | --------------------------------- | ----------------------------------------------------------------------------------------------- |
| Automatische Prüfung von 30 echten Verträgen zur Auftragsverarbeitung gegen die DSGVO | Präzision 89 %, Trefferquote 82 % | Amaral, Azeem, Abualhaija, Briand, IEEE Transactions on Software Engineering (arXiv 2209.09722) |

Präzision heißt: Wie viele der gemeldeten Verstöße sind echte Verstöße. Trefferquote (Recall) heißt: Wie viele der echten Verstöße hat das Werkzeug gefunden. Die Studie nutzt Sprachverarbeitung mit festen Regeln, kein großes Sprachmodell wie GovGuard; sie zeigt aber, dass eine automatische DSGVO-Prüfung in der Größenordnung menschlicher Reviews liegen kann.

Vorsicht im Fachgespräch: Die Kurve von Boehm (Faktor 100) ist umstritten, weil die alten Studien dahinter dünn sind. Verteidigbar ist „deutlich teurer, je nach Systemgröße 5- bis 100-mal“, nicht eine feste Zahl.

**Schlussfolgerung:**

1. **Früher statt später:** GovGuard prüft das Fachkonzept, also die billigste Phase. Jeder Fehler, der dort statt nach der Auslieferung auffällt, spart das 5- bis 100-Fache.
2. **Ergänzen statt ersetzen:** Menschen finden im Median 60 %, Werkzeuge andere Fehlerarten. Zwei unabhängige Filter übersehen zusammen weniger als jeder allein.
3. **Ehrliche Grenze:** Keine Studie misst, wie viel Prüfzeit eine KI-Vorprüfung von Compliance-Dokumenten spart. Die 50 % Ersparnis in Punkt 11 bleiben eine Annahme, bis GovGuard einen Messplan hat.

### C. Lösung und Betrieb

GovGuard prüft die Dokumente, Open-Source-Werkzeuge die Cloud-Vorlagen; alles läuft in der EU.

#### 6. Daten nur in der EU: Modell und Anbieter

**Kurz gesagt:** GovGuard nutzt das offene Modell GPT-OSS 120B. Vier europäische Anbieter ohne US-Mutterkonzern betreiben es, alle mit Abrechnung pro Token. Ein Audit kostet dort Cent-Beträge und dauert etwa 3-mal so lange wie heute bei Groq.

Heute nutzt der Prototyp drei US-Dienste: Streamlit Community Cloud für die Oberfläche, Groq für das Modell und GitHub für Code und Musterfälle. Für echte Daten müssen Oberfläche und Modell in die EU, und zwar zu Anbietern ohne US-Mutterkonzern.

Der US CLOUD Act ist ein US-Gesetz, nach dem US-Behörden von US-Unternehmen Daten verlangen können, auch wenn diese in der EU liegen. Entscheidend ist also nicht der Standort des Rechenzentrums, sondern wem der Anbieter gehört. Deshalb scheiden US-Anbieter aus, auch mit Rechenzentren in der EU.

**Europäische Anbieter für GPT-OSS 120B**

| Anbieter                    | Sitz, Rechenzentrum                      | Tool-Aufrufe                                             | Preis pro 1 Mio. Tokens (Eingabe / Ausgabe)                      |
| --------------------------- | ---------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------- |
| STACKIT AI Model Serving    | Neckarsulm (Schwarz Gruppe), Deutschland | ja, laut Release Notes                                   | ca. 0,49–0,53 $ / 0,71–0,76 $                                    |
| IONOS AI Model Hub          | Montabaur (United Internet), Deutschland | nicht geprüft                                            | ca. 0,15 € / 0,65 €                                              |
| Scaleway Generative APIs    | Paris (Iliad), Frankreich                | ja, Anbieter empfiehlt dafür die Responses-Schnittstelle | ca. 0,15 € / 0,60 €                                              |
| OVHcloud AI Endpoints       | Roubaix, Frankreich                      | widersprüchliche Angaben                                 | ca. 0,08–0,09 $ / 0,40–0,47 $                                    |
| Selbst betreiben mit vLLM   | eigenes Rechenzentrum Stuttgart          | ja                                                       | keine Token-Kosten, aber GPU-Server als CapEx und Leerlaufkosten |
| Zum Vergleich: Groq (heute) | USA                                      | ja                                                       | 0,15 $ / 0,60 $                                                  |

Die Preise stammen von Vergleichsseiten Dritter und sind vor einer Entscheidung beim Anbieter zu prüfen. Alle rechnen pro Token ab: Das Modell ist damit bei allen schon serverlos, im Leerlauf kostet es nichts.

**Warum das offene Modell ein Vorteil ist**

- **Gleiches Modell, anderer Anbieter:** GPT-OSS 120B steht unter der Apache-2.0-Lizenz und wird von mehreren europäischen Anbietern betrieben. Prompts und Prüfregeln aus der Entwicklung bleiben unverändert.
- **Kein Lock-in:** Alle Anbieter haben eine Schnittstelle wie OpenAI. Ein Wechsel ist eine Änderung der Adresse und des Schlüssels, kein Umbau.
- **Selbst betreiben möglich:** Das Modell passt auf eine einzige GPU mit 80 GB (z. B. NVIDIA H100). Wer gar keinen externen Anbieter will, betreibt es mit vLLM im eigenen Rechenzentrum.

Lock-in heißt: Ein Wechsel des Anbieters wird so teuer, dass man faktisch an ihn gebunden ist.

**Warum nicht Claude?** Claude Haiku kostet pro großem Audit rund 0,90 $, ein Vielfaches von GPT-OSS 120B. Außerdem gibt es Claude nur bei US-Anbietern. Die Verarbeitung lässt sich dort zwar auf EU-Regionen beschränken, gegen einen Zugriff nach dem CLOUD Act schützt das aber nicht.

**Wie lange dauert ein Audit bei europäischen Anbietern?**

Groq rechnet auf eigenen Chips (LPU), die für Sprachmodelle gebaut sind. Die europäischen Anbieter nutzen Grafikkarten (GPU). Die Ausgabegeschwindigkeit für GPT-OSS 120B laut Artificial Analysis (Messung mit 10.000 Eingabe-Tokens, Median über 72 Stunden):

| Anbieter                     | Ausgabe in Tokens pro Sekunde | Faktor gegenüber Groq |
| ---------------------------- | ----------------------------- | --------------------- |
| Cerebras (USA, eigene Chips) | 1.694                         | 3,6-mal schneller     |
| Groq (USA, LPU)              | 472                           | 1                     |
| Nebius (Amsterdam, GPU)      | 358                           | 1,3-mal langsamer     |
| Scaleway (Paris, GPU)        | 156                           | 3-mal langsamer       |
| IONOS, STACKIT, OVHcloud     | nicht gemessen                | im Piloten messen     |

Ein Faktor 10 ist also nicht zu erwarten, eher Faktor 3. Ein Fachkonzept-Audit erzeugt viel Ausgabe (60.000–85.000 Tokens), deshalb wächst die Dauer etwa mit diesem Faktor: von 140–215 s auf ca. 7–11 min. Die Messungen bei Groq waren teils durch Drosselung gebremst; der echte Abstand kann daher kleiner sein.

**Dauer und Kosten pro Audit**

| Größe | Wert | Herkunft |
| --- | --- | --- |
| Dauer eines Fachkonzept-Audits bei Groq | 140–215 s | Messläufe Prototyp |
| Dauer bei europäischen GPU-Anbietern | etwa 3-mal so lang: ca. 7–11 min | Schätzung, siehe oben |
| Modellkosten pro Fachkonzept-Audit bei Groq | 7–10 Cent | Messläufe Prototyp; IONOS und Scaleway haben ähnliche Preise |
| Modellkosten pro Fachkonzept-Audit bei STACKIT | bis ca. 25 Cent | Schätzung: Eingabe überwiegt, Eingabepreis ca. 3,5-mal so hoch wie bei Groq |
| Modellkosten im Jahr bei Wasen | ca. 460 Audits × 7–25 Cent = ca. 30–115 €/Jahr | Annahme: 4 Dokumente je Neuentwicklung, 5 je Migration, je 4 Läufe; ein Dokument kostet etwa so viel wie ein Fachkonzept |

**Schlussfolgerung:** Datenresidenz in der EU ist mit dem offenen Modell ohne Mehrkosten und ohne Umbau der Prüflogik erreichbar. Die längere Dauer ist unkritisch: Zehn Minuten Vorprüfung ersetzen heute vier Wochen Wartezeit. Ich empfehle STACKIT als ersten Anbieter, weil er in Baden-Württemberg sitzt und Tool-Aufrufe für dieses Modell dokumentiert; IONOS oder Scaleway sind die Ausweichlösung. Entschieden wird nach einem Test mit den Musterfällen, nicht nach dem Preis.

#### 7. Betrieb: serverlos oder als Container?

**Kurz gesagt:** Das Modell ist bei allen Anbietern schon serverlos; offen ist nur, wo die Anwendung mit der Oberfläche läuft. Serverlose Container bietet von den drei Anbietern nur Scaleway; bei STACKIT und IONOS läuft GovGuard als dauerhafter Container.

Serverlos heißt: Der Anbieter startet die Anwendung erst bei einer Anfrage und fährt sie im Leerlauf auf null herunter; man zahlt nur die Laufzeit. Container-basiert heißt hier: Die Anwendung läuft dauerhaft in einem Container auf einem Server oder einer VM, auch wenn niemand sie nutzt.

**Was die Anbieter für die Anwendung bieten**

| Anbieter                    | Serverlos                                                                                                                                                         | Container dauerhaft                             | Eignung für GovGuard                                                                                   |
| --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Scaleway                    | **ja:** Serverless Containers, fahren nach 15 min ohne Anfrage auf null; Anfragen dürfen bis 60 min dauern                                                        | Instances (VMs), Kubernetes                     | Einziger der drei mit serverlosen Containern; WebSockets laut FAQ möglich, für Streamlit vorher testen |
| STACKIT                     | **eingeschränkt:** STACKIT Functions, nur einzelne Funktionen, keine Container; Verfügbarkeit, Laufzeitgrenze und Herunterfahren auf null sind nicht dokumentiert | VMs (Compute Engine), Kubernetes, Cloud Foundry | Streamlit läuft nicht als Funktion; dauerhafter Container auf einer VM ist der Weg                     |
| IONOS                       | **nein:** kein serverloses Angebot für Anwendungen gefunden                                                                                                       | VMs (Compute Engine, Cubes), Kubernetes         | Nur dauerhafter Container                                                                              |
| Eigenes Rechenzentrum Wasen | nein                                                                                                                                                              | vorhandene Server                               | Pilot ohne Zusatzkosten, Daten bleiben im Haus                                                         |

**Gegenüberstellung für GovGuard**

| Kriterium                                                   | Container dauerhaft                                                | Serverlos (Scaleway Serverless Containers)                                                                             |
| ----------------------------------------------------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| Kosten im Leerlauf                                          | VM ca. 13 €/Monat (STACKIT), auf eigenem Server ca. 0 € zusätzlich | ca. 0 €                                                                                                                |
| Kosten bei Nutzung                                          | gleich, unabhängig von der Nutzung                                 | 0,00001 € pro vCPU-Sekunde und 0,000002 € pro GB-Sekunde, monatlich 200.000 vCPU-Sekunden und 400.000 GB-Sekunden frei |
| Erste Anfrage nach Pause                                    | sofort                                                             | Wartezeit, bis der Container gestartet ist (Kaltstart)                                                                 |
| Streamlit-Oberfläche                                        | läuft unverändert                                                  | läuft als Container, solange WebSockets funktionieren; eine Instanz, sonst verliert die Sitzung ihren Zustand          |
| Lange Audits (Fachkonzept bis ca. 11 min bei GPU-Anbietern) | keine Grenze                                                       | innerhalb der 60 min pro Anfrage                                                                                       |
| Daten zwischen Sitzungen                                    | auf der Platte möglich                                             | nichts bleibt im Container; Speicherung braucht einen Objektspeicher                                                   |
| Pflege                                                      | Betriebssystem der VM patchen (entfällt beim eigenen Server nicht) | Anbieter patcht die Plattform                                                                                          |
| Anbieterwahl                                                | STACKIT, IONOS, Scaleway oder intern                               | nur Scaleway                                                                                                           |
| Umbau                                                       | keiner (Pilot-Container genügt)                                    | gering für den Start; für SaaS der Audit-Job (siehe unten)                                                             |

Rechenbeispiel Scaleway: Ein Container mit 1 vCPU und 2 GB, der 40 Stunden im Monat läuft, verbraucht 144.000 vCPU-Sekunden und 288.000 GB-Sekunden. Beides liegt im Freikontingent, kostet also 0 €. Bei 100 Stunden wären es rund 2,25 € im Monat.

Kaltstart heißt: Nach einer Pause muss der Anbieter den Container erst laden und starten, bevor er antwortet. WebSockets sind eine dauerhafte Verbindung zwischen Browser und Server, über die Streamlit die Oberfläche aktualisiert.

**Audit-Job für den späteren SaaS-Betrieb.** Für viele Nutzer reicht eine Oberfläche, die den Audit selbst ausführt, nicht mehr. Dann läuft die Prüfung als eigener Job im Hintergrund, etwa als Scaleway Serverless Job, und schreibt ihren Fortschritt in einen Objektspeicher. Die Oberfläche fragt alle paar Sekunden nach. `run_audit` meldet den Fortschritt dafür schon heute über einen Callback (`on_progress`).

**Schlussfolgerung:**

1. **Pilot:** Container auf einem vorhandenen Server bei Wasen, Modell bei STACKIT. Keine Zusatzkosten, kein Umbau, die Testdokumente verlassen das Haus nur für den Modellaufruf.
2. **SaaS mit deutschem Anbieter:** Container dauerhaft auf einer STACKIT-VM, ca. 160 € im Jahr. Das ist nicht null, aber gegen die Ersparnis vernachlässigbar.
3. **SaaS ganz serverlos:** Scaleway Serverless Containers plus Scaleway Generative APIs, also Anwendung und Modell bei einem französischen Anbieter, im Leerlauf 0 €.

Die Wahl zwischen 2 und 3 ist eine Entscheidung zwischen deutschem Anbieter und echten 0 € im Leerlauf; finanziell ist der Unterschied mit rund 160 € im Jahr unerheblich.

#### 8. Architektur-Audits mit Open-Source-Werkzeugen

**Kurz gesagt:** Für die großen US-Clouds ist der Markt gesättigt, für europäische Clouds nicht. Die Lücke schließt man aber billiger mit eigenen Regeln in vorhandenen Open-Source-Werkzeugen als mit einer eigenen Entwicklung.

Infrastructure as Code (IaC) heißt: Die Infrastruktur einer Anwendung steht als Text in Vorlagen, etwa mit Terraform oder OpenTofu. Werkzeuge können diese Vorlagen vor dem Aufbau auf Fehlkonfigurationen prüfen.

| Werkzeug                          | Was es prüft                                                                            | Bezug zu deutschen Vorgaben                           |
| --------------------------------- | --------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| Checkov (Open Source, Apache 2.0) | IaC-Vorlagen, u. a. Terraform und Kubernetes; eigene Regeln in Python oder YAML möglich | keine BSI-Zuordnung eingebaut                         |
| Trivy (Open Source, Apache 2.0)   | IaC-Vorlagen, Container-Images; eigene Regeln in Rego möglich                           | keine BSI-Zuordnung eingebaut                         |
| Prowler (Open Source, Apache 2.0) | laufende Cloud-Konten                                                                   | Rahmenwerk BSI C5 enthalten, für die großen US-Clouds |

**Eingebaute Terraform-Regeln in Checkov je Cloud-Anbieter** (eigene Zählung im Policy Index, Stand 27.10.2026)

| Anbieter                           | Regeln |
| ---------------------------------- | ------ |
| AWS                                | 456    |
| Azure                              | 302    |
| Google Cloud                       | 162    |
| OpenStack                          | 5      |
| STACKIT, IONOS, Scaleway, OVHcloud | 0      |

Für eine Migration nach STACKIT, IONOS oder Scaleway muss Wasen die Regeln also selbst schreiben, zum Beispiel „Speicher ist verschlüsselt“ oder „Datenbank nicht aus dem Internet erreichbar“. Eine Zuordnung zum IT-Grundschutz bietet keines der Werkzeuge; die stellt das Prüfteam einmalig in der Regelbeschreibung her. GovGuards eigene Architekturprüfung hilft hier nicht: Sie liest nur ein Vorlagenformat (CloudFormation), das bei europäischen Anbietern nicht vorkommt.

**Schlussfolgerung:** Architektur-Audits sind kein Feld für eine Eigenentwicklung. Wasen bindet ein Open-Source-Werkzeug in die Bereitstellungs-Pipeline ein und ergänzt eigene Regeln für die europäischen Ziel-Clouds; dafür sind 7 Personentage CapEx und ein Teil der jährlichen Wartung eingeplant (Punkt 11). Das bestätigt den Fokus von GovGuard auf Fachkonzepte, Datenschutz und IT-Sicherheit, wo es kein vergleichbares Werkzeug gibt.

### D. Umsetzung

In welchen Schritten GovGuard zu Wasen kommt und in welcher Form.

#### 9. Pilot und nächste Schritte

**Kurz gesagt:** Bevor überhaupt Piloten gesucht werden, schließe ich als Entwickler eine Entwicklungsphase von rund 21 Personentagen auf eigene Kosten ab: Befunde nach Fundstelle, abgestimmte Prüfregeln für Neuentwicklung und Migration, Musterfälle aus öffentlichen, wissenschaftlichen oder synthetischen Quellen, Docker-Image. Der Pilot bei Wasen bindet den europäischen Modellanbieter an, den der Kunde wählt, und ist aufwendiger als die Technik vermuten lässt: Alte Dokumente und ihr Soll müssen aufbereitet und getestet werden, angenommen rund 24 Personentage.

**Ablauf in drei Phasen**

| Phase | Wer trägt die Kosten | Inhalt | Aufwand (Annahme) | Ergebnis |
| --- | --- | --- | --- | --- |
| 1 Entwicklungsphase | ich als Entwickler, vor der Suche nach Piloten | Fundstelle, Prüfregeln je Dokument- und Projektart, OPS.2.2, Musterfälle, Docker-Image | 21 PT | ein pilotreifes GovGuard |
| 2 Pilot | Wasen | EU-Modellanbieter anbinden, alte Dokumente und Soll aufbereiten, testen, Prüfzeit messen | 24 PT | gemessene Ersparnis an Prüfzeit |
| 3 Integration | Wasen | Datenhaltung, Transaktionen, Anbindung an Prozesse und Systeme, Architektur-Werkzeug | 30 PT | GovGuard im Projektablauf |

**Phase 1: Entwicklungsphase vor der Suche nach Piloten**

| Arbeitspaket | Warum vorher fertig | Aufwand (Annahme) |
| --- | --- | --- |
| Befunde nach Fundstelle gruppieren (Issue #81) | Viele Befunde zeigen auf dieselben Zeilen; in der Galerie teilen 36–89 % der Befunde mit Zeilen einen Bereich. Fachleute beheben eine Stelle einmal, statt Befunde einzeln zu lesen. Ohne das misst der Pilot Lesezeit statt Prüfzeit. | 4 PT; Prototyp liegt auf einem Branch vor |
| Prüfregeln je Dokument- und Projektart zuordnen | Heute prüfen alle 350 Regeln jedes Dokument als Fachkonzept. Für DSFA, Verzeichnis, Auftragsverarbeitung und Löschregeln (Punkt 3) braucht es die passenden Regeln je Dokument, getrennt für Neuentwicklung und Migration, und ohne Doppelungen zwischen DSGVO und SDM. | 6 PT |
| BSI OPS.2.2 als neue Regelquelle | Ohne sie prüft GovGuard die Cloud-Dokumente (Migrationskonzept, Sicherheits- und Notfallkonzept) gar nicht. Neue Regeln entstehen nur über den Build mit Freigabe im Git-Diff. | 5 PT |
| Musterfälle mit Soll für die neuen Dokumentarten | Ohne Soll lässt sich nicht unterscheiden, ob GovGuard oder die Regel falsch liegt. Quellen: öffentlich verfügbare Dokumente (z. B. veröffentlichte Verfahrensbeschreibungen von Behörden), von der Forschung geteilte Testsets oder synthetische Fälle wie bei AIReg-Bench. Das Soll kommt aus der Quelle oder von mir, nie aus einem Lauf. | 5 PT |
| Docker-Image | Ein Pilot soll ohne Umbau installiert werden können. Im Image ist `browser.gatherUsageStats = false` gesetzt; Streamlit sendet sonst Nutzungsstatistiken. | 1 PT |

Harmonisieren heißt hier: ein abgestimmter Satz von Prüfregeln, in dem jede Regel weiß, für welches Dokument und welche Projektart sie gilt, und keine Pflicht doppelt oder widersprüchlich geprüft wird.

**Phase 2: Pilot bei Wasen**

Ein IT-Dienstleister wird schon für interne Testfälle verlangen, dass die Daten in der EU bleiben. Ein Docker-Container im eigenen Rechenzentrum plus ein europäischer Modellanbieter erfüllt das ohne Umbau. Docker ist ein Werkzeug, das eine Anwendung mit allem, was sie braucht, in ein Paket (Container) schnürt, das auf jedem Server gleich läuft.

| Arbeitspaket bei Wasen | Inhalt | Aufwand (Annahme) |
| --- | --- | --- |
| Installation und Vertrag | Container auf einem internen Server, nur im Firmennetz erreichbar; Vertrag zur Auftragsverarbeitung mit dem Modellanbieter | 2 PT |
| Anbindung an den EU-Modellanbieter | Den Anbieter wählt der Pilotkunde, etwa STACKIT oder IONOS. Dazu gehören ein Adapter für eine Schnittstelle wie bei OpenAI und ein Test aller Musterfälle gegen diesen Anbieter: Anbieter betreiben GPT-OSS unterschiedlich gut, besonders bei Tool-Aufrufen, und GovGuard braucht erzwungene Tool-Nutzung (ADR 0005). | 4 PT |
| Alte Dokumente aufbereiten | aus 10–20 abgeschlossenen Projekten Fachkonzept, DSFA, Verzeichnis-Eintrag, Löschregeln und bei Migrationen das Migrationskonzept heraussuchen, Formate vereinheitlichen, Kundendaten wo nötig schwärzen | 5 PT |
| Soll festlegen | Das Prüfteam legt je Dokument fest, welche Befunde richtig wären; das ist zugleich die Prüfung von Hand für den Vergleich | 8 PT |
| Testen und auswerten | GovGuard-Läufe, Vergleich mit dem Soll, Prüfzeit, gefundene Mängel, Fehlalarme und Dauer je Audit messen | 5 PT |

Aufbau: Der Container baut nur eine Verbindung nach außen auf, zum Modellanbieter in der EU. Testdokumente und Berichte bleiben in der Sitzung oder als Download; es gibt noch keine Datenbank. Architekturen prüft ein Open-Source-Werkzeug (Punkt 8). Für STACKIT und IONOS gibt es keine unabhängigen Geschwindigkeitsmessungen; der Pilot misst die Dauer selbst.

**Nach einem erfolgreichen Piloten: Daten, Transaktionen, Integration**

| Thema                   | Offene Fragen für Phase 3                                                                                                                                      |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Datenmanagement         | Wo liegen Berichte und Belege? Wie lange werden sie aufbewahrt, wann gelöscht? Wie werden Kunden voneinander getrennt?                                         |
| Transaktionsmanagement  | Wird jedes Audit vollständig oder gar nicht gespeichert? Was passiert bei Abbruch? Welche Version von Prüfregeln und Modell galt für welchen Bericht?          |
| Integration in Prozesse | An welcher Stelle im Projektablauf wird geprüft, wer gibt frei? Läuft das Open-Source-Werkzeug für Architekturen automatisch in der Bereitstellungs-Pipeline? |
| Integration in Systeme  | Anmeldung über das Firmenkonto (Single Sign-on), Tickets für Verstöße, Ablage der Berichte im Dokumentenmanagement                                             |
| Betrieb                 | Container dauerhaft oder serverlos (Punkt 7)? Wer überwacht, wer reagiert auf Ausfälle?                                                                        |

Transaktionsmanagement heißt: Ein Vorgang wird entweder ganz oder gar nicht ausgeführt und gespeichert, damit nie halbe Ergebnisse entstehen. Für Audits ist das wichtig, weil ein Bericht später als Nachweis dienen soll.

**Schlussfolgerung:** Die Risiken sind sauber getrennt. Ich trage die Entwicklungsphase (rund 21 Personentage) und gehe erst mit einem pilotreifen GovGuard auf Piloten zu. Wasen trägt bis zur Entscheidung nur den Pilot, rund 24 Personentage oder 16.800 €; der größte Teil davon ist Aufbereiten und Soll-Festlegen, nicht Technik. Die Anbindung an den Modellanbieter gehört in den Pilot, weil erst der Kunde den Anbieter wählt. Dafür beantwortet der Pilot die eine Frage, an der die Wirtschaftlichkeit hängt: Wie viel Prüfzeit spart GovGuard wirklich? Liegt die gemessene Ersparnis deutlich über 20 % (Punkt 11), lohnt sich Phase 3 mit Datenhaltung und Integration; liegt sie darunter, endet das Vorhaben nach dem Piloten. Die aufbereiteten Dokumente mit Soll behält Wasen als Testset für jede spätere Version.

#### 10. Wäre GovGuard als SaaS für Wasen interessant?

**Kurz gesagt:** Eher nicht. Für Wasen passt eine selbst betriebene Installation mit Wartungsvertrag besser als ein SaaS-Abo bei einem fremden Anbieter.

| Argument                                   | Warum es gegen SaaS spricht                                                                                                                                                |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Wasen ist selbst Auftragsverarbeiter       | Die Fachkonzepte gehören den Behörden. Ein SaaS-Anbieter wäre ein weiterer Unterauftragsverarbeiter, und den muss jeder Kunde vorher genehmigen (Art. 28 Abs. 2 DSGVO). |
| Eigenes Rechenzentrum und Betriebspersonal | Einen Docker-Container zu betreiben ist für einen IT-Dienstleister Routine.                                                                                                |
| Integration                                | Single Sign-on, Ticketsystem und Dokumentenmanagement lassen sich intern einfacher anbinden.                                                                               |
| Geringe Menge                              | Rund 460 Audits im Jahr machen ein Abo pro Audit für beide Seiten uninteressant.                                                                                           |

**Wann ein fremder Anbieter doch Sinn hätte:** Der eigentliche Wert eines Anbieters ist die Pflege der Prüfregeln, wenn sich DSGVO-Auslegung, SDM oder IT-Grundschutz ändern. Das lässt sich auch ohne SaaS kaufen: als Software zum Selbstbetrieb mit Wartungsvertrag, der Regel-Updates liefert.

**Schlussfolgerung:** Für Wasen als Nutzer ist Selbstbetrieb mit Wartungsvertrag das passende Modell. Davon zu unterscheiden ist Stufe zwei im Pitch: Dort bietet Wasen selbst GovGuard als SaaS für seine Behördenkunden an. Für die Behörden ist Wasen ein bekannter deutscher Dienstleister, der ohnehin schon ihre Daten verarbeitet; für Wasen wird GovGuard so vom Kostenblock zum Produkt.

### E. Wirtschaftlichkeit

Was Pilot, Integration und Betrieb kosten und ab wann sich das rechnet.

#### 11. Lohnt sich GovGuard? CapEx, OpEx und TCO

**Kurz gesagt:** Betrieb und Modell kosten unter 200 € im Jahr; teuer ist die Arbeitszeit. Gerechnet wird nur mit dem Prüfen der Dokumente je Projekt (Punkt 4): rund 147.000 € im Jahr. Bei angenommenen 50 % Ersparnis an den vorgeprüften Dokumenten sind die 37.800 € für Pilot und Integration nach rund 11 Monaten bezahlt, lohnend ist es ab rund 20 %. Gerechnet ist nur, was GovGuard heute kann; Abgleich und Remediation sind Optionen. Die Entwicklungsphase davor trage ich als Entwickler.

Die Rechnung beruht auf Annahmen für die Übung. Dauer und Modellkosten stammen aus Messläufen des Prototyps mit GPT-OSS 120B bei Groq (`data/measurements/`), Preise der Anbieter aus ihren Preislisten oder von Vergleichsseiten.

**Grundlagen der Rechnung**

| Größe | Wert | Herkunft |
| --- | --- | --- |
| Prüfaufwand heute | 210 Personentage/Jahr | Punkt 4 |
| Kosten der Prüfung ohne GovGuard | 210 × 700 € = 147.000 €/Jahr | Annahme: interner Tagessatz 700 € |
| Vorgeprüfter Anteil | 135 Personentage/Jahr (64 %) | Punkt 4: GovGuard für Projekt-Dokumente, Open-Source-Werkzeuge für die Cloud-Vorlage |
| Ersparnis durch Vorprüfung | 50 % von 135 → 67,5 Personentage/Jahr | Annahme: Fachleute bewerten bei vorgeprüften Dokumenten nur Warnungen und Verstöße |
| Wert der Ersparnis | 67,5 × 700 € = 47.250 €/Jahr | Annahme: interner Tagessatz 700 € |
| Wartezeit pro Projekt | 4 Wochen → 1–2 Wochen | Annahme |
| Betrieb und Modell | unter 200 €/Jahr | Modell ca. 30–115 € (Punkt 6), Container auf vorhandenem Server ca. 0 € (Punkt 7) |
| Architektur-Audits mit Open-Source-Werkzeugen | 0 € Lizenz | Punkt 8 |

**CapEx und OpEx**

CapEx (Capital Expenditure) sind einmalige Investitionen, die über Jahre genutzt werden, etwa Server oder selbst entwickelte Software. OpEx (Operational Expenditure) sind laufende Betriebskosten wie Cloud-Rechnung, Lizenzen oder Wartung. Cloud verschiebt Kosten von CapEx zu OpEx: Statt Server zu kaufen, zahlt man nach Nutzung.

| Posten                                                                                                                  | Art            | Betrag                      | Herkunft                              |
| ----------------------------------------------------------------------------------------------------------------------- | -------------- | --------------------------- | ------------------------------------- |
| Pilot: Installation, Vertrag mit dem Modellanbieter (Punkt 9)                                                           | CapEx          | 2 PT × 700 € = 1.400 €      | Annahme                               |
| Pilot: Anbindung an den EU-Modellanbieter, Test aller Musterfälle gegen diesen Anbieter                                 | CapEx          | 4 PT × 700 € = 2.800 €      | Annahme                               |
| Pilot: alte Dokumente aus 10–20 Projekten aufbereiten                                                                   | CapEx          | 5 PT × 700 € = 3.500 €      | Annahme                               |
| Pilot: Soll je Dokument durch das Prüfteam festlegen                                                                    | CapEx          | 8 PT × 700 € = 5.600 €      | Annahme                               |
| Pilot: testen und auswerten nach Messplan                                                                               | CapEx          | 5 PT × 700 € = 3.500 €      | Annahme                               |
| Integration: Datenhaltung und Transaktionsmanagement (Berichte speichern, Löschfristen, Versionen von Regeln und Modell) | CapEx          | 8 PT × 700 € = 5.600 €      | Annahme                               |
| Integration: Anmeldung über das Firmenkonto (Single Sign-on)                                                            | CapEx          | 3 PT × 700 € = 2.100 €      | Annahme                               |
| Integration: Verstöße als Tickets im Ticketsystem                                                                       | CapEx          | 4 PT × 700 € = 2.800 €      | Annahme                               |
| Integration: Ablage der Berichte im Dokumentenmanagement                                                                | CapEx          | 3 PT × 700 € = 2.100 €      | Annahme                               |
| Integration in Prozesse: Prüfschritt und Freigabe im Projektablauf, Schulung des Prüfteams                              | CapEx          | 5 PT × 700 € = 3.500 €      | Annahme                               |
| Architektur-Audit: Open-Source-Werkzeug in der Pipeline, eigene Regeln für europäische Clouds (Punkt 8)                 | CapEx          | 7 PT × 700 € = 4.900 €      | Annahme                               |
| Server-Hardware                                                                                                         | CapEx          | 0 €                         | entfällt durch Cloud                  |
| **Summe einmalig**                                                                                                      | **CapEx**      | **54 PT = 37.800 €**        | davon 24 PT Pilot                     |
| Nicht bei Wasen: Entwicklungsphase vor der Suche nach Piloten (Punkt 9)                                                 | Vorleistung des Entwicklers | ca. 21 PT      | nicht in der TCO von Wasen            |
| Optional, nur für ein SaaS-Angebot an Behörden: Umbau für serverlosen Betrieb (Audit-Job)                               | CapEx          | 15 PT × 700 € = 10.500 €    | Annahme; nicht in der TCO             |
| Betrieb und Modell                                                                                                      | OpEx           | unter 200 €/Jahr            | siehe Tabelle oben                    |
| Pflege der Prüfregeln bei neuen Normständen                                                                             | OpEx           | 5 PT × 700 € = 3.500 €/Jahr | Annahme                               |
| Wartung der Schnittstellen und der Regeln für das Architektur-Werkzeug                                                  | OpEx           | 3 PT × 700 € = 2.100 €/Jahr | Annahme                               |
| **Summe laufend**                                                                                                       | **OpEx**       | **ca. 5.800 €/Jahr**        |                                       |
| Ersparnis Prüfaufwand                                                                                                   | OpEx (weniger) | 47.250 €/Jahr               | siehe Tabelle oben                    |
| **Netto-Ersparnis**                                                                                                     |                | **ca. 41.450 €/Jahr**       | 47.250 € − 5.800 €                    |
| **Amortisation**                                                                                                        |                | **rund 11 Monate**          | 37.800 € ÷ 41.450 €/Jahr = 0,91 Jahre |

Amortisation heißt: die Zeit, bis die Ersparnis die einmalige Investition wieder eingespielt hat. Selbst entwickelte Software darf nach § 248 Abs. 2 HGB aktiviert werden, muss aber nicht; ob der Umbau in der Bilanz als CapEx erscheint, entscheidet also die Buchhaltung.

**TCO über drei Jahre**

TCO (Total Cost of Ownership) sind alle Kosten einer Lösung über ihre Nutzungsdauer, also CapEx plus OpEx aller Jahre. Verglichen wird hier der ganze Prüfprozess, nicht nur GovGuard, weil die Prüfung von Hand der größte Kostenblock bleibt.

| Posten                                                      | Ohne GovGuard            | Mit GovGuard             |
| ----------------------------------------------------------- | ------------------------ | ------------------------ |
| CapEx: Pilot und Integration (einmalig)                     | 0 €                      | 37.800 €                 |
| OpEx: Prüfung von Hand                                      | 3 × 147.000 € = 441.000 € | 3 × 99.750 € = 299.250 € |
| OpEx: Betrieb, Modell, Pflege von Regeln und Schnittstellen | 0 €                      | 3 × 5.800 € = 17.400 €   |
| **TCO 3 Jahre**                                             | **441.000 €**            | **354.450 €**            |

Unterschied: rund 86.550 € weniger in drei Jahren, das sind 20 %. Gut ein Drittel der Prüfarbeit, Abgleich alt gegen neu und Grundschutz-Check, bleibt ohne Vorprüfung. Die Entwicklungsphase trage ich als Entwickler; sie steht deshalb nicht in der TCO von Wasen. Drei Jahre sind eine übliche Nutzungsdauer für IT-Investitionen. Nicht eingerechnet sind die kürzere Wartezeit und die früher gefundenen Fehler (Punkt 5), deren Wert sich schwer beziffern lässt.

**Wie stark hängt das Ergebnis an der Annahme von 50 %?**

| Ersparnis an vorgeprüften Dokumenten | TCO 3 Jahre mit GovGuard | Vorteil gegenüber 441.000 € | Amortisation      |
| ------------------------------------ | ------------------------ | --------------------------- | ----------------- |
| 25 %                                 | 425.325 €                | 15.675 €                    | ca. 25 Monate     |
| 50 % (Annahme)                       | 354.450 €                | 86.550 €                    | rund 11 Monate    |
| 75 %                                 | 283.575 €                | 157.425 €                   | ca. 7 Monate      |

Gerechnet mit 37.800 € CapEx, 5.800 € OpEx pro Jahr und 135 vorgeprüften Personentagen im Jahr. Die Gewinnschwelle über drei Jahre liegt bei rund 20 % Ersparnis: (37.800 € + 3 × 5.800 €) ÷ (3 × 135 × 700 €) = 19,5 %.

**Was die Rechnung weiter verbessern kann**

| Hebel | Wirkung bei 50 % Ersparnis | Wer trägt es |
| --- | --- | --- |
| Abgleich alt gegen neu in GovGuard, wenn der Pilot den Bedarf zeigt | weitere 15 × 2 PT × 50 % = 15 PT = rund 10.500 €/Jahr; Amortisation rund 9 Monate, Gewinnschwelle rund 16 % | ich: ca. 6 PT Entwicklung; Wasen: ca. 2 PT mehr im Pilot für das Soll der Abgleiche |
| Remediation: Textvorschlag für die Nachbesserung, den der Code nachprüft | bis rund 54.000 €/Jahr, wenn sie die Nachbesserung halbiert (Punkt 4); Annahme auf Annahme | ich, wenn der Bedarf belegt ist |
| Grundschutz-Check vorprüfen und abgleichen, laut Roadmap | weitere (25 × 1,5 PT + 15 × 0,5 PT) × 50 % = 22,5 PT = rund 15.750 €/Jahr | ich, nach dem Piloten; Aufwand noch nicht geschätzt |
| Integration schlank starten: Single Sign-on, Tickets und Dokumentenmanagement erst später | CapEx 10 PT weniger, also 30.800 €; Amortisation rund 9 Monate | Wasen |
| Vermiedene Nacharbeit und kürzere Wartezeit (Punkt 5) | nicht eingerechnet, weil schwer zu beziffern; spricht zusätzlich für GovGuard | – |

**Schlussfolgerung:** Die Cloud-Rechnung ist für die Entscheidung unerheblich; es geht um Arbeitszeit. Wie viel GovGuard spart, hängt daran, wie viele Projekt-Dokumente es vorprüft: Gerechnet ist nur, was GovGuard heute kann; damit sind rund zwei Drittel der Prüfarbeit vorgeprüft. Abgleich und Remediation würden die Rechnung verbessern, kommen aber erst in die Roadmap, wenn der Pilot oder eine Erhebung zeigt, dass Wasen sie braucht. Unter rund 20 % Ersparnis rechnet es sich über drei Jahre nicht; genau das muss der Pilot messen (Punkt 9).

## Quellen

**Markt und Bedarf (A)**

- [Bitkom Cloud Report 2026](https://www.bitkom.org/sites/main/files/2026-09/bitkom-study-report-cloud-report-2026-en.pdf) (603 Unternehmen ab 20 Beschäftigten)
- [Bitkom-Presseinformation zum Cloud Report 2025](https://www.bitkom.org/Presse/Presseinformation/Wirtschaft-ruft-nach-einer-deutschen-Cloud) (Vorjahreswerte)
- [BSI-Vortrag: Sichere Cloudnutzung mit C5](https://isaca.de/images/Publikationen/Prasentationen/ISACA%20Fokus%20Event%20-%20BSI-Vortrag%20-%20Sichere%20Cloudnutzung%20mit%20C5%20-%20221103.pdf) (C5-Pflicht für Bundesbehörden)
- [CIO/COMPUTERWOCHE: Cloud-Migration mit angezogener Handbremse](https://www.computerwoche.de/article/3817430/cloud-migration-mit-angezogener-handbremse.html) (Studie „Cloud-Migration 2025“, 346 Befragte)
- [Lünendonk-Studie im Digitalbusiness Magazin](https://www.digitalbusiness-magazin.de/cloud-migration-wie-der-lift-and-shift-ansatz-ki-ausbremst-a-48a09da52e5abaf7ff68ab3b0373ff59/)
- [McKinsey: Cloud-migration opportunity: Business value grows, but missteps abound](https://www.mckinsey.com/capabilities/tech-and-ai/our-insights/cloud-migration-opportunity-business-value-grows-but-missteps-abound), 2021
- [Gartner-Prognose zu cloud-nativen Workloads (TechRepublic)](https://www.techrepublic.com/article/85-of-organizations-will-be-cloud-first-by-2025-says-gartner/) und [The Edge Malaysia](https://theedgemalaysia.com/article/cloud-will-be-centerpiece-new-digital-experiences-says-gartner)

**Prüfarbeit und Fehler (B)**

- [BSI IT-Grundschutz-Kompendium, Baustein OPS.2.2 Cloud-Nutzung, Edition 2023](https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Grundschutz/IT-GS-Kompendium_Einzel_PDFs_2023/04_OPS_Betrieb/OPS_2_2_Cloud-Nutzung_Edition_2023.pdf?__blob=publicationFile&v=3)
- [DSGVO (EUR-Lex)](https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32016R0679), Art. 28, 30, 35, 44–49
- [Abschlusspräsentation GovGuard](https://claude.ai/artifact/9afnq6xg11xyqzPzGcjT7w), Backup-Folien 16–21; `data/knowledge_base/rules_spec.json` (Regeln zu Art. 28, 30, 35, 44–49)
- [Boehm & Basili: Software Defect Reduction Top 10 List](https://condor.depaul.edu/dmumaugh/readings/handouts/SE425/J81.pdf), IEEE Computer 34(1), 2001, S. 135–137
- [Capers Jones: Software Defect Removal Efficiency](https://www.ifsq.org/work-jones-1996.html), IEEE Computer 29(4), 1996 (Zusammenfassung bei IfSQ)
- [NIST Planning Report 02-3: The Economic Impacts of Inadequate Infrastructure for Software Testing](https://www.nist.gov/document/report02-3pdf), 2002
- [IBM Cost of a Data Breach 2025](https://www.ibm.com/reports/data-breach) und [IBM-Pressemitteilung Deutschland](https://de.newsroom.ibm.com/2025-07-30-IBM-Studie-Kosten-von-Datenlecks-sinken-in-Deutschland-erstmals-seit-funf-Jahren?asPDF=1)
- [Amaral et al.: NLP-based Automated Compliance Checking of Data Processing Agreements against GDPR](https://arxiv.org/abs/2209.09722), IEEE TSE
- [Bossavit-Kritik an der Kostenkurve (TechWell)](https://www.techwell.com/techwell-insights/2013/10/what-does-it-really-cost-fix-software-defect)

**Lösung und Betrieb (C)**

- [gpt-oss-120b Model Card bei Hugging Face](https://huggingface.co/openai/gpt-oss-120b) (Lizenz, eine GPU mit 80 GB, vLLM, Tool-Aufrufe)
- [Artificial Analysis: gpt-oss-120b nach Anbietern](https://artificialanalysis.ai/models/gpt-oss-120b/providers) (Ausgabegeschwindigkeit, Latenz)
- [STACKIT AI Model Serving](https://docs.stackit.cloud/products/data-and-ai/ai-model-serving/), [Release Notes](https://docs.stackit.cloud/products/data-and-ai/ai-model-serving/release-notes/), [Preise bei Mastra](https://mastra.ai/models/providers/stackit) und [Modellübersicht bei innFactory](https://innfactory.de/de/cloud/stackit/produkte/ai-model-serving/)
- [STACKIT: Serverless Computing / STACKIT Functions](https://stackit.com/en/learn/knowledge/serverless-computing) und [STACKIT-Preisblatt 2024](https://www.stackit.de/wp-content/uploads/2024/05/20240425-STACKIT_Whitepaper_Pricing_en_v1.1.0.pdf) (Compute Engine, Cloud Foundry)
- [IONOS Cloud: Produktübersicht](https://cloud.ionos.co.uk/cloud-offer) und [devops.ionos.com](https://devops.ionos.com)
- [Preisvergleich gpt-oss-120b bei infrabase.ai](https://infrabase.ai/models/gpt-oss-120b) (IONOS, Scaleway, Groq)
- [Scaleway: OpenAI-Kompatibilität](https://www.scaleway.com/en/docs/generative-apis/reference-content/openai-compatibility/) und [Scaleway bei Hugging Face](https://huggingface.co/blog/inference-providers-scaleway)
- [Scaleway: Serverless-Preise](https://www.scaleway.com/en/pricing/serverless/), [Serverless Containers FAQ](https://www.scaleway.com/en/docs/serverless-containers/faq/), [Konzepte](https://www.scaleway.com/en/docs/serverless-containers/concepts/) und [Grenzen](https://www.scaleway.com/en/docs/serverless-containers/reference-content/containers-limitations/)
- [OVHcloud gpt-oss-120b bei computeprices.com](https://computeprices.com/providers/ovhcloud/models/gpt-oss-120b)
- [Checkov: Terraform Policy Index](https://www.checkov.io/5.Policy%20Index/terraform.html) (eigene Zählung der Regeln je Anbieter)
- [Trivy: Terraform-Prüfung](https://trivy.dev/latest/docs/coverage/iac/terraform/) und [Prowler: Compliance-Rahmenwerke](https://docs.prowler.com/user-guide/cli/tutorials/compliance)

**Umsetzung und Wirtschaftlichkeit (D, E)**

- [OpenRouter: Provider Variance](https://openrouter.ai/blog/provider-variance-introducing-exacto), [Simon Willison zu ungleicher Leistung der Anbieter](https://feeds.simonwillison.net/2025/Aug/15/inconsistent-performance/), [OpenAI: Verifying gpt-oss implementations](https://developers.openai.com/cookbook/articles/gpt-oss/verifying-implementations)
- [Streamlit: config.toml](https://docs.streamlit.io/develop/api-reference/configuration/config.toml) (`browser.gatherUsageStats`, Standard `true`)
- GovGuard-Repo: `data/measurements/` (Messläufe mit GPT-OSS 120B bei Groq), ADR 0005 (erzwungene Tool-Nutzung), ADR 0023 (Kosten Claude Haiku), `src/govguard/adapters/groq_services.py` (Modell GPT-OSS 120B)
