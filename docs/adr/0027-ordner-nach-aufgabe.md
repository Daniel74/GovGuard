# 0027 – Ordner nach Aufgabe, Kriterium je Paket

_Anlass: Architektur-Review vom 20.10.2026. In `govguard/` und `govguard_ui/` liegen je 17 bis 19 Dateien flach im Root._

## Kontext

- `kb_build/` ist schon nach Prozessschritt gegliedert (extract → select → decompose → rules). Die Schritte laufen dort wirklich nacheinander.
- In `govguard/` passt Prozessschritt nicht. Die Prüfung läuft als Validator *in* jedem Modellaufruf, und `evidence` und `corrections` nutzt jeder Schritt. `prepare/` hätte 2 Dateien und würde `check/` importieren.
- In der UI nutzen zwei Screens dieselbe Report-Ansicht. Die Auswahl eines Befunds (`<key>_selected`) verteilt sich auf 3 Module.

## Entscheidung

- **Regel:** Ein Ordner bündelt Dateien mit einer Aufgabe, die ein Wort benennt. Das Kriterium wählt jedes Paket selbst.
- **Root:** nur Einstiege und Verträge, die andere importieren. `python -m govguard.cli`, `python -m kb_build` und `streamlit_app.py` bleiben gleich.

| Paket | Kriterium | Ordner | Root |
|---|---|---|---|
| `govguard` | Art des Moduls | `calls/` (spricht mit dem Modell, mit `model_call`), `checks/` (rein), `adapters/` (AWS, Groq) | `audit_engine`, `models`, `open_world`, `text`, `audit_setup`, `cli` |
| `govguard_ui` | Verwendung | `screens/` (drei Seiten, `audit_runner`), `report/` (eine Report-Ansicht, Interface `render_report`) | `app`, `navigation`, `gallery`, `paths`, `style`, `texts` |
| `kb_build` | Prozessschritt | wie bisher; `gates.py` geht auf in `select/gates.py`, `rules/gates.py` und `llm_step.py` | `__main__`, `paths`, `build_log`, `source_fetch`, `llm_step`, `build_inputs` |

- `tests/test_architecture.py` erzwingt die Richtung: `checks/` importiert nie `calls/` oder `adapters/`, `report/` nie `screens/`, kein `run.py` ein anderes `run.py`.
- **Verworfen:**
  - Prozessschritt überall (siehe Kontext);
  - Arch- vs. Spec-Audit, weil nur das Inventar arch-spezifisch ist;
  - MVC, weil Streamlit keinen Controller hat;
  - `utils/`, weil der Name keine Aufgabe nennt;
  - `pages/`, weil Streamlit den Namen belegt;
  - ein gemeinsamer Modellaufruf für Laufzeit und Build. Der Build hat Cache und `llm_error`, die Laufzeit bricht fail-closed ab.

## Konsequenzen

- **Kein neues Verhalten:** Die bestehenden Tests sind der Beweis. Prompts und Cache-Keys bleiben Byte für Byte gleich, also bleibt der eingefrorene Katalog unberührt (ADR 0025).
- **Inventar:** Es behält auf Groq vorerst `ToolOutput`, eine Abweichung von ADR 0016. Die Umstellung auf `NativeOutput` bekommt ein eigenes Ticket mit Messlauf.
- **Pfade ziehen mit:** `CLAUDE.md`, `docs/ARCHITECTURE.md` → *Code-Struktur*, `docs/DESIGN.md` und `.claude/skills/audit-messen`.

## Fachgespräch-Satz

„Ein Ordner ist eine Aufgabe, und im Root steht die Schnittstelle. Darum gliedert der Build nach Prozessschritt und die Laufzeit nach ‚spricht mit dem Modell‘ oder ‚prüft rein‘, und ein Test hält die Import-Richtung fest.“
