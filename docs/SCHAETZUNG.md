# GovGuard – Schätzung: Umfang und LLM-Aufwand

Stand 09.10.2026, grob, vor der ersten Codezeile. Grundlage: [ARCHITECTURE.md](ARCHITECTURE.md) → *Code-Struktur* und [FAHRPLAN.md](FAHRPLAN.md).
**Methode:** Ein Modul hat höchstens ca. 200 Zeilen (CLAUDE.md), Tests stehen etwa 1:1 zum Code. Nicht gezählt sind der generierte CDK-Code der Archetypen und die JSON-Daten.

## 1. Umfang und Komplexität

| Modul | Aufgabe | LOC Code | LOC Tests | Komplexität | Grund |
|---|---|---|---|---|---|
| `govguard/models.py` | Pydantic-Modelle (`Rule`, Report, `AuditEvent`) | 120 | 60 | niedrig | nur Deklaration |
| `govguard/text.py` | `normalize`, `contains_quote`, Ressourcentypen | 60 | 80 | niedrig | reine Funktionen |
| `govguard/audit_engine.py` | Validierungskette, N/A, Gesamtstatus, Archetyp-Auswahl | 200 | 250 | **hoch** | Halluzinationsschutz liegt hier |
| `govguard/aws_services.py` | boto3, Bedrock-Modell | 100 | 80 | mittel | Stubber-Tests, Tool-Choice |
| `govguard/handler.py`, `cli.py` | Einstieg Lambda und lokal | 160 | 130 | mittel | 3 Endpunkte, HTTP 422/502 |
| **Summe `govguard/`** | | **640** | **600** | | |
| `kb_build/source_fetch.py`, `cdk_runner.py` | Adapter für HTTP und subprocess | 130 | 100 | niedrig | dünne Hüllen |
| `kb_build/sources/` (BSI, CIS, DSGVO, SDM) | Extraktion und Vorfilter | 460 | 400 | **hoch** | 4 Formate, SDM aus PDF |
| `kb_build/ranking.py` | reihum, Gleichstand, gesetzte Plätze | 120 | 150 | mittel | deterministisch, gut testbar |
| `kb_build/curation.py` | LLM: prüfbar ja/nein, Relevanzfilter | 150 | 120 | **hoch** | LLM-Urteil plus Code-Kontrolle |
| `kb_build/gates.py` | Schema, Anker, Zitat, Preset-Gate | 200 | 200 | mittel | viele Fehlerfälle |
| `kb_build/archetypes.py` | CDK-Schleife (max. 3 Runden), Allowlist | 180 | 180 | **hoch** | LLM-Schleife plus cdk-nag |
| `kb_build/__main__.py` | Build verdrahten | 60 | 30 | niedrig | nur Klebe-Code |
| **Summe `kb_build/`** | | **1.300** | **1.180** | | |
| `infra/` | CDK-Stack: Lambda, API, KMS, IAM, Logs | 170 | 120 | **hoch** | Security-kritisch |
| `ui/` | Streamlit-Demo | 150 | 30 | niedrig | nur HTTP zur API |
| `.github/workflows/` | `build-kb.yml`, `deploy.yml` | 120 (YAML) | – | mittel | OIDC, keine Logik |
| **Gesamt** | | **ca. 2.400** | **ca. 1.950** | | **ca. 4.350 LOC** |

## 2. LLM-Aufwand im Claude-Pro-Abo

Gemessen in **„% Weekly“**, also in der Einheit der Usage-Anzeige. Anthropic veröffentlicht keine festen Token-Zahlen, deshalb sind die Werte Annahmen, die nach #1 kalibriert werden.

| Fenster (Reset ca. montags) | Arbeitstage | Verfügbar |
|---|---|---|
| A: 09.–12.10. | 2 | 85 % (am 09.10. bereits 15 % verbraucht) |
| B: 13.–19.10. | 5 | 100 % |
| C: 20.–21.10. | 2 | 100 % (Puffer, Präsentation) |

| Wer baut | Tickets | % Weekly je Ticket | Summe |
|---|---|---|---|
| 🤖 Claude, groß (Opus, heikel) | #1, #7, #9 | 13 | 39 |
| 🤖 Claude, mittel/klein | #2 (8), #3 (5) | 5–8 | 13 |
| 🛠 Junie baut, Claude prüft | #4, #6, #10, #12 | 3 | 12 |
| 🛠 Junie baut, Claude prüft + Wizard/großes Review | #5, #8 | 4 | 8 |
| 🛠 Junie (UI), 🤖 Claude (`deploy.yml`) | #11 | 5 | 5 |
| Puffer Debugging | +30 % | | 23 |
| **Bedarf** | | | **ca. 100 %** |

**Ergebnis:** Der Bedarf von ca. 100 % liegt deutlich unter den 185 % in A+B, und C bleibt als Reserve. Ohne Junie wären es ca. 140 %. Engpass ist eher das 5h-Session-Limit pro Tag als das Weekly-Budget.
**Junie** (PyCharm, GPT-5.2) verbraucht Credits aus dem JetBrains-Abo, nicht aus Claude Pro. Prüfe den Credit-Stand nach #4.

**Kalibrierung:** Notiere den Weekly-Wert vor und nach #1. Kostet #1 mehr als 13 %, multiplizierst du alle Werte mit *Ist ÷ 13*. Liegt der Bedarf dann über 185 %, kürzt du zuerst den Umfang (SDM in #5, UI in #11), bevor die Qualität leidet.
**Sparen:** Sonnet baut, Opus urteilt; nach jedem Schritt `/clear`; große Dokumente nur abschnittsweise lesen lassen.
