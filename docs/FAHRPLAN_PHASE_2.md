# GovGuard – Fahrplan Phase 2

Phase 2 beginnt nach der Präsentation am 26.10.2026: erst ein UI-Ticket, dann die Roadmap recherchieren, schätzen, entscheiden und bauen.
**Maßgeblich für die Roadmap** sind allein die Backup-Folien „Produktstrategie“ bis „Einbindung in Behördenwerkzeuge“ der [Abschlusspräsentation](https://claude.ai/artifact/9afnq6xg11xyqzPzGcjT7w), Kern ist „Roadmap: GovGuard im Behördenablauf“ (Phasen 1, 2a, 2b, 3, 4). [AUSBAU.md](AUSBAU.md) ist veraltet und keine Quelle.
Ein Eintrag je Schritt, in Bearbeitungsreihenfolge; jeder Eintrag steht für sich. Hier stehen nur Aufgaben und Befehle, Ergebnisse stehen in Issues, ADRs und `docs/research/`. Hake die Kästchen im Editor ab.

**Legende:** 👤 du · 🤖 Claude · 🆕 neue Session (`/clear`) · 🔀 Halt: du entscheidest · `/…` Befehl zum Eintippen.

**Rhythmus jedes Eintrags:** _Budget ablesen → Starten → Bauen oder Entscheiden → Prüfen → Verstehen → Budget ablesen → Abschließen._

**So steuerst du:**

- **Vorlage statt Technik.** Claude beginnt jeden Schritt mit Nutzen, Aufwand und Risiko und deinen Entscheidungen (CLAUDE.md → _Arbeitsweise_). Du antwortest mit Go, Korrektur oder Stopp.
- **Budget in % Weekly.** Lies `/usage` vor und nach jedem Schritt ab und schreib „Budget: geschätzt X %, Ist Y %“ als Kommentar ins Issue. Das Ist von #81 (P1) ist die Messlatte für alle weiteren Schätzungen, Methode wie [SCHAETZUNG.md](SCHAETZUNG.md) → _Kalibrierung_. Das Wochenlimit setzt montags zurück; wird es knapp, schneide den Umfang, nicht die Qualität.
- **Modell und Session** wie in [FAHRPLAN.md](FAHRPLAN.md): Sonnet baut, Opus urteilt, jeder Schritt startet frisch mit „Lies docs/FAHRPLAN_PHASE_2.md Schritt N“.

**Demo-Stand schützen:** Die IHK-Präsentation ist Mitte November. Der Stand vom 26.10. bekommt einen Tag (P0). Streamlit Community Cloud rollt bei jedem Push neu aus, darum pushst du erst nach der Abnahme.

**Reihenfolge:**

| Schritt | Was                         | Skill                     | Hängt ab von                   | Schätzung (Annahme) |
| ------- | --------------------------- | ------------------------- | ------------------------------ | ------------------- |
| P0      | Stand sichern               | –                         | –                              | < 1 %               |
| P1      | #81 Befunde nach Fundstelle | `/prototype`, `/tdd`      | P0                             | 10–15 %, Messlatte  |
| P2      | Recherche Testdaten         | `/research`               | P0, läuft im Hintergrund       | 5–10 %              |
| P3      | Roadmap-Karte und Schätzung | `/wayfinder`              | P1 (Messlatte), parallel zu P2 | 8–12 %              |
| P4      | Prüfregeln festlegen        | `/grill-with-docs`        | P2 und P3                      | 3–5 %               |
| P5      | Karte in baubare Tickets    | `/to-spec`, `/to-tickets` | P3 und P4                      | 3–5 %               |
| P6 ff.  | Umsetzung je Ticket         | `/tdd`, `/code-review`    | P5                             | entsteht in P5      |

---

### Schritt P0 – Stand sichern

**Ziel:** CLAUDE.md und dieser Fahrplan liegen auf GitHub; der Demo-Stand der Präsentation ist markiert.

- [ ] 👤 committet und pusht CLAUDE.md, `docs/AUSBAU.md` und `docs/FAHRPLAN_PHASE_2.md`
- [ ] 👤 `git tag demo-26-10 && git push origin demo-26-10`

**Fertig, wenn:** `git status` sauber ist und der Tag auf GitHub liegt. Zurück zum Demo-Stand: `git checkout demo-26-10`.

---

### Schritt P1 – #81 Befunde nach Fundstelle gruppieren

**Ziel:** Der Report zeigt Befunde wahlweise nach Fundstelle: Wer das Fachkonzept korrigiert, behebt eine Stelle einmal, statt sieben Befunde einzeln zu lesen. Weil sich die UI sichtbar ändert, entscheidet ein Prototyp die Darstellung vor dem Bau.
**Voraussetzung:** P0. Kein LLM-Aufruf, keine Groq-Kosten.

- [x] **Budget** 👤 `/usage` ablesen
- [ ] **Prototyp** 🆕 _Opus_ · 👤 `/prototype Issue #81: 2–3 Varianten der Ansicht „nach Fundstelle“ auf der echten Galerie, umschaltbar per ?variant=, Branch prototype/81-fundstelle` → 🤖 startet ihn mit `/run`
- [x] **🔀 Halt: Variante wählen** 👤 alle Varianten mit `arch-antragseingang-fehlerhaft` und `spec-govguard` ansehen; Variante wählen und die offene Frage beantworten (überlappende Bereiche gruppieren?) → 🤖 schreibt den Prototyp-Kommentar in #81: gewählte Variante, was wiederverwendbar ist, was nicht übernommen wird
- [ ] **Starten** 🆕 _Sonnet_ · 👤 `/tdd Issue #81 umsetzen, nach dem Prototyp-Kommentar neu schreiben statt kopieren` → Vorlage → Go
- [ ] **Design** 🤖 ergänzt das Design-Artefakt um die neue Ansicht · 👤 `/design-screenshots`
- [ ] **🔀 Halt: Bilder freigeben** 👤 Vergleichsbilder in `tests/visual/output/` ansehen, dann `uv run pytest -m visual --update-snapshots`
- [ ] **Prüfen** 🆕 _Opus_ · 👤 `/code-review gegen Issue #81` → Befunde beheben
- [ ] **Budget** 👤 `/usage` ablesen → Kommentar in #81 „Budget: geschätzt 10–15 %, Ist Y %“
- [ ] **Verstehen** 👤 `/verstehen 81 Gruppierung als reine Funktion`
- [ ] **Abschließen** 👤 committet und pusht, schließt #81

**Fertig, wenn:** #81 geschlossen ist, `pytest`, `pytest -m visual` und ruff grün sind und der Budget-Kommentar in #81 steht.
**Fürs Fachgespräch:** Die Ansicht sortiert nur um: dieselben Befunde, kein neuer Status, kein Modell beteiligt. Darum reicht eine reine Funktion mit Unit-Tests.

---

### Schritt P2 – Recherche: Testdaten für das Spec-Audit

**Ziel:** Eine belegte Übersicht, welche Testdaten mit Soll es für das Prüfen von Fachkonzepten gegen DSGVO, SDM und KI-VO gibt. Sie ist Grundlage für die Prüfregeln (P4) und für Roadmap-Phase 1 „Prüfen besser machen: messen“ (Folie „Qualität messen und lernen“).
**Voraussetzung:** P0. Läuft als Hintergrund-Agent, du kannst parallel an P1 oder P3 arbeiten.

- [ ] **Budget** 👤 `/usage` ablesen
- [ ] **Starten** 🆕 _Opus_ · 👤 `/research Testdaten für das Spec-Audit, Fragen aus docs/FAHRPLAN_PHASE_2.md Schritt P2, Ablage docs/research/Testdaten für das Spec-Audit.md`
      Fragen: 1. Welche Datensätze mit Soll von Fachleuten gibt es für die Prüfung von Texten gegen DSGVO oder KI-VO? Je Datensatz Zugang, Lizenz, Sprache, Umfang; mindestens Amaral, Briand u. a. 2023 und AIReg-Bench 2025. 2. Wie erzeugt die Forschung synthetische Testdokumente, und wie stellt sie sicher, dass das Soll von Menschen kommt und nicht vom Modell? 3. Welche Messgrößen und Protokolle nutzen die Studien: Trefferquote, Fehlalarme, falsche Einhaltung, Übereinstimmung zwischen Fachleuten? 4. Gibt es öffentliche deutschsprachige Fachkonzepte, Lastenhefte oder DSFA aus Behörden, die als Testfall taugen? 5. Welche Normteile decken die gefundenen Testsets ab (DSGVO-Artikel, SDM-Bausteine, KI-VO-Pflichten)? Antwort als Tabelle, sie ist die Eingabe für P4.
- [ ] **Lesen** 👤 Zusammenfassung lesen. Braucht es Antworten von Forschenden oder einer Fachperson, z. B. Zugang zum Datensatz von Amaral u. a.? → `/to-questionnaire`
- [ ] **Budget** 👤 `/usage` ablesen
- [ ] **Abschließen** 👤 committet die Recherche

**Fertig, wenn:** Die Datei in `docs/research/` liegt, jede Aussage eine Quelle hat und Frage 5 als Tabelle beantwortet ist.

---

### Schritt P3 – Roadmap-Karte und Schätzung

**Ziel:** Die Roadmap liegt als Karte aus Entscheidungs-Tickets auf GitHub, und jedes Arbeitspaket hat eine Schätzung in % Weekly. Quelle sind allein die Backup-Folien „Produktstrategie“ bis „Einbindung in Behördenwerkzeuge“ im Deck.
**Voraussetzung:** P1 abgeschlossen (Messlatte). Läuft parallel zu P2; Entscheidungen, die Testdaten brauchen, stehen auf der Karte mit `Blocked by` auf die Recherche.

- [ ] **Budget** 👤 `/usage` ablesen
- [ ] **Starten** 🆕 _Opus_ · 👤 `/wayfinder Roadmap Phase 2 allein aus den Backup-Folien „Produktstrategie“ bis „Einbindung in Behördenwerkzeuge“ im Deck https://claude.ai/artifact/9afnq6xg11xyqzPzGcjT7w, Kern „Roadmap: GovGuard im Behördenablauf“; docs/AUSBAU.md ist veraltet; die Recherche aus P2 ist ein Recherche-Ticket der Karte, „Prüfregeln festlegen“ (P4) ein Entscheidungs-Ticket`
- [ ] **🔀 Entscheidungen** 👤 beantwortet die Entscheidungs-Tickets, die nicht blockiert sind, eins nach dem anderen; je Ticket eine frische Session
- [ ] **Schätzen** 🤖 schätzt jedes Arbeitspaket in S, M oder L, rechnet über die Messlatte aus #81 in % Weekly um und legt eine Wochenplanung vor, als neuer Abschnitt _Phase 2_ in [SCHAETZUNG.md](SCHAETZUNG.md)
- [ ] **🔀 Halt: Plan freigeben** 👤 Wochenplanung lesen → „passt“ oder Umfang schneiden
- [ ] **Budget** 👤 `/usage` ablesen
- [ ] **Abschließen** 👤 committet SCHAETZUNG.md

**Fertig, wenn:** Jeder Punkt der Roadmap an einem Ticket der Karte hängt, das Ticket „Prüfregeln festlegen“ existiert und SCHAETZUNG.md den Abschnitt _Phase 2_ hat.

---

### Schritt P4 – Prüfregeln festlegen

**Ziel:** Entschieden und als ADR festgehalten ist, gegen welche Prüfregeln das Spec-Audit in Phase 2 läuft: welche Quellen, welcher Umfang, eingefroren oder neu gebaut. Die Entscheidung passt zu den Fähigkeiten, die zuerst kommen (P3), und zu den Testdaten, mit denen man sie messen kann (P2).
**Voraussetzung:** P2 und die dafür nötigen Entscheidungen aus P3. Ist das Entscheidungs-Ticket auf der Karte.

- [ ] **Budget** 👤 `/usage` ablesen
- [ ] **Starten** 🆕 _Opus_ · 👤 `/grill-with-docs Prüfregeln für Phase 2, Entscheidungs-Ticket „Prüfregeln festlegen“; Grundlagen: docs/research/Testdaten für das Spec-Audit.md, docs/ENTWICKLUNG.md, ADR 0011 und 0025`
- [ ] **🔀 Entscheidung** 👤 entscheidet im Grilling → 🤖 schreibt ADR und `CONTEXT.md`, kommentiert und schließt das Ticket auf der Karte. Prüfregeln ändert nur der Build, nie die Hand (CLAUDE.md).
- [ ] **Budget** 👤 `/usage` ablesen
- [ ] **Abschließen** 👤 committet

**Fertig, wenn:** Die ADR vorliegt und das Ticket geschlossen ist.
**Fürs Fachgespräch:** Ein Prüfkatalog ist nur so gut, wie man ihn messen kann: Für eine Regel ohne Testfall kann niemand sagen, ob ihr Urteil stimmt.

---

### Schritt P5 – Karte in baubare Tickets

**Ziel:** Aus den Entscheidungen der Karte werden eine Spec und baubare Tickets, mit `Blocked by`, Schätzung und Reihenfolge. Dieser Fahrplan bekommt je Ticket einen Schritt P6, P7 und so weiter.
**Voraussetzung:** Alle Entscheidungs-Tickets der Karte sind geschlossen, P4 eingeschlossen.

- [ ] **Budget** 👤 `/usage` ablesen
- [ ] **Starten** 🆕 _Opus_ · 👤 `/to-spec aus der Wayfinder-Karte Roadmap Phase 2` → `/to-tickets` in derselben Session
- [ ] **Eintragen** 🤖 legt je Ticket einen Schritt in diesem Fahrplan an, im Format von P1, und ergänzt die Tabelle _Reihenfolge_
- [ ] **🔀 Halt: Schnitt freigeben** 👤 Tickets und Reihenfolge lesen → Go oder Korrektur
- [ ] **Budget** 👤 `/usage` ablesen
- [ ] **Abschließen** 👤 committet

**Fertig, wenn:** Jedes Ticket eine Schätzung und hier einen Schritt hat.

---

### Ab Schritt P6 – Umsetzung

Entsteht in P5.
