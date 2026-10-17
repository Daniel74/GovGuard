# 0024 – Teststrategie der Demo-UI: drei Ebenen

_Umsetzung: #44; gilt ab #43 für jedes UI-Ticket._

## Kontext

- Die Demo-UI wächst mit #41–#43. Getestet sind Seitenaufbau und Screenshots, viele Interaktionen nicht: Status- und Quellenfilter, Auswahl eines Befunds, „Ganzes Dokument“, Texteingabe.
- AppTest (Streamlit-Test ohne Browser) ist schnell, sieht aber kein CSS, kein eigenes HTML und keinen Zustand, den nur der Browser hält, etwa eine aufgeklappte Liste.
- Playwright sieht alles, braucht aber Chromium und einen Streamlit-Server. Echte LLM-Aufrufe kosten Geld und liefern nicht immer dasselbe.

## Entscheidung

- **Jede Interaktion wird auf genau einer Ebene getestet, und zwar auf der billigsten, die sie sehen kann:** Logik mit pytest ohne Streamlit, Streamlit-Widgets mit AppTest, CSS und eigenes HTML mit Playwright (`pytest -m visual`).
- **Interaktions-Inventar im Test-Code:** Es ordnet jedes Widget mit `key`, jeden Seitenlink und den Download einem Test zu. Ein Wächter-Test wird rot, sobald ein neues Element ohne Eintrag dazukommt.
- **Kein echtes LLM in UI-Tests:** Neue Audits laufen mit `FunctionModel`, „Audits ansehen“ nutzt die gespeicherten Galerie-Reports.
- `uv run pytest` bleibt ohne Browser. `pytest -m visual` läuft vor jedem Commit, der die UI ändert.

## Konsequenzen

- Eigenes HTML mit Klick, etwa die Tabelle aus #43, lässt sich nur in Playwright prüfen und kostet mehr Testzeit. Bei gleicher UX haben native Widgets Vorrang.
- Abgedeckt heißt hier: Jede Interaktion steht im Inventar und hat ihren Test. Ein Coverage-Werkzeug ist dafür nicht nötig.

## Fachgespräch-Satz

„Testpyramide: Jede Interaktion teste ich auf der billigsten Ebene, die sie sehen kann, also Logik ohne UI, Widgets mit AppTest ohne Browser und nur CSS und eigenes HTML im echten Browser, und ein Wächter-Test sorgt dafür, dass kein neues Bedienelement ungetestet bleibt.“
