# GovGuard – Entwicklung

Dieses Dokument sagt, wie man GovGuard einrichtet, die Wissensbasis baut, ein Audit per Kommandozeile startet, die Oberfläche testet und eine neue Quelle ergänzt. Den Aufbau und das *Warum* zeigt [ARCHITECTURE.md](ARCHITECTURE.md), Begriffe in [CONTEXT.md](../CONTEXT.md). Alle Befehle laufen im Repo-Root.

| Abschnitt | Aufgabe |
|---|---|
| 1 Einrichten | Installieren, Tests, Linter, Oberfläche starten |
| 2 Wissensbasis bauen | Prüfregeln aus den Normtexten erzeugen |
| 3 Audit per Kommandozeile | Eine Datei prüfen, Exit-Codes |
| 4 Screenshot-Regression | Oberfläche im Browser gegen Referenzbilder prüfen |
| 5 Neue Quelle hinzufügen | Eine weitere Norm in den Katalog aufnehmen |
| 6 Bekannte Grenzen | Was im Betrieb nicht (voll) funktioniert |

## 1 Einrichten

[uv](https://docs.astral.sh/uv/) ist der Paketmanager des Projekts; er holt Python 3.13 und alle Pakete aus `uv.lock`.

| Aufgabe (Befehl) | Was passiert |
|---|---|
| Installieren (`uv sync`) | Installiert die Pakete (Gruppen `build`, `dev`, `ui` sind Standard, `pyproject.toml`). |
| Testen (`uv run pytest -q`) | Alle Tests ohne Browser; die Browser-Tests (Marker `visual`) bleiben aus. Sie brauchen weder AWS noch Groq. |
| Code prüfen (`uv run ruff check .`) | Der Linter ruff liest den Code, ohne ihn auszuführen, und meldet Regelverstöße. Er prüft auch die Grenzen für kleine Einheiten (Komplexität, Argumente, Anweisungen je Funktion). |
| Oberfläche starten (`uv run streamlit run streamlit_app.py`) | Startet die Demo-Oberfläche; die Galerie läuft ohne Schlüssel (auch `./start_streamlit.sh`). |

**Audit erstellen in der lokalen Oberfläche:** Die Seite verlangt ein Passwort und, für das Modell, den Groq-Schlüssel. Beides kommt aus Umgebungsvariablen oder aus `.streamlit/secrets.toml`: `APP_PASSWORD=… GROQ_API_KEY=… uv run streamlit run streamlit_app.py`. Fehlt das Passwort (`APP_PASSWORD`), startet kein Audit (fail closed). Auf Streamlit Community Cloud stehen beide Werte in den Secrets der App ([ARCHITECTURE](ARCHITECTURE.md#43-ausrollen-betrieb-und-kosten) 4.3).

## 2 Wissensbasis bauen

Der Build ist ein Werkzeug, das lokal läuft: `uv run python -m kb_build <befehl>`. Die Befehle laufen in dieser Reihenfolge; jeder liest das Ergebnis des vorigen. Ein Gate ist eine Prüfung im Code, die eine Prüfregel nur durchlässt, wenn sie eine feste Regel erfüllt. Ein Retry ist die erneute Frage ans Modell, nachdem der Code die Antwort mit Grund abgelehnt hat. Hintergrund und Gates: [ARCHITECTURE](ARCHITECTURE.md#32-paket-kb_build-der-build) 3.2.

| Schritt (Befehl) | Was passiert | Ergebnis |
|---|---|---|
| Zerlegen (`extract`, Standard) | Lädt die Quellen, prüft die SHA-256 und zerlegt sie in Anforderungen. Kein Modell, braucht Netz. | `data/intermediate/extracted/*.json` |
| Gruppieren (`decompose`) | Das Modell gruppiert die Abschnitte von DSGVO und KI-VO; der Code setzt Anker und Wortlaut ([ADR 0026](adr/0026-rechtsartikel-zerlegen.md)). | `data/intermediate/decomposed/*.json`, `decompositions_spec.json` |
| Auswählen (`select`) | Das Modell urteilt „prüfbar ja/nein“, der Code wählt aus (Relevanz, Pflichtanker). | `selection_<arch\|spec>.json`, `verdicts_*.json` (Urteil je Anforderung, [ADR 0011](adr/0011-vollstaendiger-katalog.md)) |
| Formulieren (`rules`) | Das Modell formuliert je ausgewählter Anforderung eine Prüfregel; ein Gate prüft Schema, Anker, Zitat und Eigenschaften. | `data/knowledge_base/rules_<arch\|spec>.json` |
| Eigenschaften lesen (`cfn-properties`) | Liest Schemas aus einem Ordner und schreibt die echten Eigenschaften je Ressourcentyp. Kein Modell. | `data/input/cfn_properties.json` |

**Optionen:**

- **Modell (`--provider`):** Standard ist Groq ([ADR 0014](adr/0014-groq-standard-im-build.md)): `export GROQ_API_KEY=…`, das Modell wechselt `GROQ_MODEL`. Fehlt der Schlüssel, bricht der Lauf ab, ohne auf Bedrock auszuweichen. Bedrock gibt es nur ausdrücklich: `--provider bedrock` (`eu-central-1`, Profil `eu.`, gültiger Login über `AWS_PROFILE=…`) oder `--provider bedrock-global` ([ADR 0012](adr/0012-globales-profil-im-build.md)). Der Build schickt nur öffentliche Normtexte hinaus.
- **Eine Audit-Art (`--audit-type spec|architecture`):** `select` und `rules` rechnen nur diese Liste neu. Nach dem Vorfilter stuft `select` rund 470 Spec- bzw. 880 Architektur-Anforderungen ein (`verdicts_*.json`).
- **Nur Fehlendes (`--only-missing`):** Die eingefrorenen Regeln bleiben, das Modell bewertet nur neue Anforderungen. Gebaut nur für das Spec-Audit, also immer mit `--audit-type spec` (Abschnitt 5, [ADR 0025](adr/0025-ki-vo-als-neue-quelle-bei-eingefrorenem-katalog.md)).

**Protokoll und Abbruch:**

- **Protokoll:** Jeder Lauf schreibt eine Zeile je Anforderung mit Uhrzeit auf das Terminal und in `data/intermediate/logs/<befehl>.log` (Retries, Tokens, Verstoß-Prüfer). Die Logs werden mit dem Ergebnis eingecheckt.
- **Abbruch:** Ein Pflichtanker ist eine Norm-Stelle, deren Befund ein Musterfall festlegt; sie muss in den Katalog. Fehlt ein Pflichtanker (`pinned`), bricht der Lauf in den ersten Sekunden ab. Scheitert eine Regel an einem Gate, bricht der Lauf ab und der alte Stand bleibt.
- **Wiederholen:** Ein Cache ist ein Zwischenspeicher für schon bezahlte Urteile; er gilt für `decompose` (`decomposition_cache.json`) und `select` (`judgement_cache.json`). Ein Checkpoint ist eine Zwischendatei mit den fertigen Regeln; ihn schreibt nur `rules --only-missing` (`rules_<art>.checkpoint.json`). Ein normales `rules` formuliert nach einem Abbruch alles neu. Kosten je Befehl: siehe unten.

**Kosten je Befehl** (Groq `gpt-oss-120b`, aus den Build-Logs in `data/intermediate/logs/`): `select` Architektur ca. 0,31 $ (897 Anfragen, ca. 29 min), `rules` Architektur ca. 0,17 $ (267 Anfragen, ca. 9 min), `rules` Spec mit 151 Regeln ca. 0,18 $ (619 Anfragen, ca. 16 min), `decompose` ca. 0,04 $ (56 Anfragen, ca. 3 min); `extract` und `cfn-properties` kosten 0 $. Ein Neubau aller Stufen kostet hochgerechnet ca. 1,1 $ und dauert ca. 1,5 h; mit `--only-missing` und Cache sinken die Kosten auf Cent-Beträge. Bedrock käme mit gleichen Tokens auf das 8- bis 9-Fache (Rechenbeispiel).

**Echte Ressourcentypen und Eigenschaften:** Das Modell darf nur Typen und Eigenschaften nennen, die es wirklich gibt; sonst gibt es einen Retry. Der Qualitätsbericht zählt unbekannte Eigenschaften (`unknown_properties`). Beide Dateien zieht man neu aus AWS (Login nötig):

- **Typen:** `data/input/cfn_resource_types.json` (1926 Typen) kommt aus `aws cloudformation list-types --visibility PUBLIC --type RESOURCE --filters Category=AWS_TYPES --query 'TypeSummaries[].TypeName'`.
- **Eigenschaften:** `data/input/cfn_properties.json` hält je Typ des Prüfumfangs alle Eigenschaftspfade (z. B. `RedirectConfig.Protocol`). Neu ziehen: `mkdir schemas`, dann `for t in $(jq -r '.[][]' data/input/scope.json); do aws cloudformation describe-type --type RESOURCE --type-name $t --query Schema --output text > schemas/${t//::/-}.json; done`, danach `uv run python -m kb_build cfn-properties` (anderer Ordner per `--schema-dir`). Nennt eine Prüfregel einen Typ außerhalb von `scope.json`, gibt es ebenfalls einen Retry.

## 3 Audit per Kommandozeile

Das Kommando prüft eine Datei und gibt den Audit-Report als JSON auf stdout aus: `uv run python -m govguard.cli spec <datei>` für eine Spezifikation, `arch <datei>` für ein CloudFormation-Template oder Freitext. Beispiel mit einem Musterfall: `uv run python -m govguard.cli arch data/input/presets/arch-fristenwecker/template.json`.

| Exit-Code | Bedeutung |
|---|---|
| 0 | Report auf stdout |
| 1 | Eingabe über 100.000 Zeichen; abgelehnt vor dem ersten Modellaufruf, es kostet nichts |
| 2 | fail closed: die Modellantwort war auch nach dem Retry ungültig; Grund auf stderr ([ADR 0017](adr/0017-beleg-per-zeilenverweis.md)) |
| 3 | Groq-Schlüssel (`GROQ_API_KEY`) fehlt; `export GROQ_API_KEY=…`, das Kommando liest keine `.env` |

- **Modell (`--provider`):** Standard ist Groq, nur mit fiktiven Daten, denn die Eingabe geht in die USA. Für echte Daten gibt es nur `--provider bedrock` (Profil `eu.`, [ADR 0001](adr/0001-eu-inferenzprofil.md)).
- **Katalog (`--catalog`):** Standard ist `data/knowledge_base/rules_spec.json` bzw. `rules_arch.json`; ein kleinerer Katalog macht Probeläufe billig.
- **Messen:** Kosten, Dauer und Retry-Gründe misst der Skill `/audit-messen` (`.claude/skills/audit-messen/SKILL.md`); `uv run python .claude/skills/audit-messen/evaluate.py data/measurements` wertet die Läufe in `data/measurements/` aus.

## 4 Screenshot-Regression

Die Regression fotografiert die Oberfläche in einem echten Browser und vergleicht die Bilder mit Referenzbildern. So fällt auf, wenn eine Änderung das Aussehen verschiebt ([ADR 0024](adr/0024-teststrategie-demo-ui.md)). Ein Marker ist ein Etikett an einem Test, mit dem pytest Tests gezielt ein- oder ausschließt; die Browser-Tests tragen den Marker `visual`.

- **Einmalig:** `uv run playwright install chromium`. Normales `uv run pytest` braucht den Browser nicht und überspringt den Marker `visual`.
- **Prüfen:** `uv run pytest -m visual` startet `streamlit_app.py` lokal (ohne Schlüssel, `AUDIT_BACKEND=local`) und fotografiert 4 Ansichten bei 1440 px (`start`, `gallery-spec`, `gallery-arch`, `create`). Erlaubt sind höchstens 100 geänderte Pixel. In `tests/visual/output/` (nicht eingecheckt) landen das Foto, bei Abweichung `<ansicht>-diff.png` (Änderungen rot) und `<ansicht>-design.png` (links Design aus `tests/visual/design/`, rechts Streamlit).
- **Freigeben:** War die Änderung gewollt, schreibt `uv run pytest -m visual --update-snapshots` die Referenzbilder `tests/visual/<ansicht>.png` neu; danach ansehen und committen. Die Referenzbilder stammen von macOS, auf einem anderen System rendern die Schriften anders. Das Bild `gallery-spec.png` zeigt auch das [README](../README.md).

## 5 Neue Quelle hinzufügen

Eine Quelle ist ein Regelwerk wie BSI oder CIS, aus dem Prüfregeln entstehen ([CONTEXT.md](../CONTEXT.md)). Der Ablauf hat sechs Schritte:

1. `data/input/sources.json`: URL, Version (Commit oder Tag), SHA-256, Lizenz ([ADR 0008](adr/0008-quellformate.md)).
2. Ein Adapter ist ein Modul, das genau ein Quellformat liest. Er liegt in `src/kb_build/extract/<quelle>.py` und hat eine Lesefunktion (`extract()`) und einen Vorfilter (`prefilter()`). Der Vorfilter gibt `None` zurück oder für jede verworfene Anforderung einen festen Begründungssatz (Auswahlprotokoll). Prowler-Quellen (CIS, FSBP, C5) beschreiben nur ihr Format (`ProwlerFormat`: Anker, Titel, Text, Attribute, Vorfilter); gelesen wird im gemeinsamen Parser `prowler.py`.
3. Anmelden: die Liste der Adapter (`ADAPTERS` in `src/kb_build/extract/run.py`) und die Liste der Quellnamen (`SourceName` in `src/govguard/models.py`). In der Zuordnung zur Audit-Art (`SELECTIONS` in `src/kb_build/build_inputs.py`) kommt die Quelle zu Spec oder Architektur.
4. Lizenz: offen → Extrakt einchecken, Vermerk in `NOTICE`; sonst Extrakt in `.gitignore` (CIS, FSBP, C5).
5. Test mit kleinem Fixture: Anzahl, Stichprobe, Vorfilter mit Begründung.
6. Ist der Katalog eingefroren ([SPEC](SPEC.md) G13), baut der Schalter „nur fehlende Regeln formulieren“: `select --audit-type spec --only-missing` und `rules --audit-type spec --only-missing`. Vorhandene Urteile und Regeln bleiben erhalten, das Modell bewertet nur die neuen Anforderungen ([ADR 0025](adr/0025-ki-vo-als-neue-quelle-bei-eingefrorenem-katalog.md), nur Spec-Audit). Byte für Byte gilt das nur für Quellen ohne Zerlegung; zerlegte Regeln bekommen ihr Zitat vom Code ([ADR 0026](adr/0026-rechtsartikel-zerlegen.md)).

**Fallstrick:** Die Prompts der Einstufung gelten je Audit-Art, nicht je Quelle. Ihre Version steckt im Cache-Schlüssel (`prompt_version`). Ändert sich der Prompt, verliert die ganze Audit-Art den Cache, und ein normales `select` würfelt die alte Auswahl neu. Deshalb verlässt sich `--only-missing` auf die eingecheckte Auswahl, nicht auf den Cache: Der Spec-Katalog stammt von einer älteren Prompt-Version als der Code.

## 6 Bekannte Grenzen

Die Grenzen des Betriebs stehen hier, die Risiken des Entwurfs in [ARCHITECTURE](ARCHITECTURE.md#64-wo-die-schale-endet) 6.4.

| Grenze | Was es heißt | Maßnahme |
|---|---|---|
| Groq schwankt | Je Musterfall behalten 70 bis 99 % der Prüfregeln in allen Läufen ihren Status (#54); früher wechselten im Spec-Audit 42 von 151 Prüfregeln, bei Bedrock 19 (#29). Der FAIL-Prüfer fängt FAILs ohne festgelegten Verstoß ab (#31), PASS und WARN schwanken weiter. Jeder Report nennt sein Modell (`model_id`). | Zeigen, nicht nachwürfeln ([ADR 0023](adr/0023-demo-und-recruiter-stand.md)); Bedrock ist für die Demo nicht verfügbar. |
| fail closed | Von 10 Spec-Läufen brach einer ab (#54). | Erneut starten. |
| YAML | CloudFormation-YAML gilt als Freitext und damit als offene Welt; ein fehlender Baustein wird dort nur WARN, kein FAIL (#48). | Template als JSON einreichen ([ADR 0015](adr/0015-cloudformation-einziges-inventarformat.md)). |
| Build mit Groq | Der Build (`kb_build`) bricht oft an einer einzelnen Regel ab (#49). | Wiederholen; der Cache spart `decompose` und `select`, ein normales `rules` beginnt von vorn (Abschnitt 2). |
| Prüfregeln | S3.5, DLS.2.2, IAM-09.01AC und BER.5.9 werten Deny bei `false` als Verstoß; 12 Regeln enthalten Platzhalter, nur `<Mindestfrist>` in DET.3.1 verfälscht das Ergebnis (WARN statt PASS, #50). | Offen, im Review beobachten. |
| Bildvergleich | Die Referenzbilder stammen von macOS (Abschnitt 4). | Auf anderem System mit `--update-snapshots` neu anlegen und ansehen. |

Weitere Symptome: Bei HTTP 429 (Groq-Limit von 250.000 Tokens je Minute) hilft Warten und nacheinander starten: Ein Spec-Audit braucht ca. 120.000 Tokens je Minute, `GROQ_MAX_PARALLEL` und `checks/token_budget.py` halten nur ein einzelnes Audit unter dem Limit, eine Warteschlange gibt es nicht. Ein fehlendes oder falsches `APP_PASSWORD` verhindert den Start (fail closed). Stimmt die SHA-256 einer Quelle nicht, bricht der Build ab: den neuen Hash bewusst eintragen und den Diff prüfen (Abschnitt 5).
