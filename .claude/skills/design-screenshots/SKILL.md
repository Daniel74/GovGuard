---
name: design-screenshots
description: Soll-Bilder aus dem Design-Artefakt von #11 neu fotografieren (tests/visual/design/), nachdem sich das Design geändert hat. Steuert ein Chrome, in das der Nutzer eingeloggt ist.
---

Die Soll-Bilder zeigen die Artboards im Play-Modus bei 1440 px. Sie sind Vorlage für die Vergleichsbilder „Design | Streamlit“ (#40), kein Pixel-Orakel.

1. **Chrome starten** (Bash mit `run_in_background`, Profil im Scratchpad):

   ```bash
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9333 \
     --user-data-dir=<scratchpad>/chrome-profile --no-first-run --no-default-browser-check \
     "https://claude.ai/artifact/7aHtX79kJsv8EX8PjzLn2q"
   ```

2. **Login abwarten.** Den Nutzer bitten, sich im neuen Fenster bei claude.ai einzuloggen und „drin“ zu schreiben. Bis dahin hängt kein Skript am Browser: So erkennt die Bot-Sperre von claude.ai einen normalen Browser.
3. **Fotografieren** (alle Artboards oder nur genannte, z. B. `start create`):

   ```bash
   uv run --no-project --with playwright==1.64.0 --with pillow \
     python .claude/skills/design-screenshots/shoot.py tests/visual/design [board ...]
   ```

4. **Ansehen.** Jedes Bild mit Read öffnen. Fertig, wenn jedes das ganze Artboard zeigt: Seitenleiste links, Titel oben, keine claude.ai-Leiste, kein Hinweis-Popup, unten nichts abgeschnitten.
5. **Aufräumen.** Den Chrome-Task mit TaskStop beenden und `<scratchpad>/chrome-profile` löschen: Es enthält die Login-Sitzung.

## Fallstricke

- Playwrights eigenes Chromium ist als ferngesteuert markiert; dort scheitert der Login per E-Mail und per Google. Deshalb immer das echte Chrome mit eigenem Profil.
- Die Play-IDs in `BOARDS` (`shoot.py`) gelten, solange die Artboards bestehen. Zeigt ein Bild das falsche Artboard, im Canvas oben rechts ▷ → „Prototypes“ das Artboard wählen und die neue ID aus der URL (`#play-…`) übernehmen.
- `TOP = 80` schneidet die claude.ai-Leiste und die Play-Leiste ab. Ändert claude.ai seine Oberfläche, zeigt Schritt 4 das als Rand oben oder abgeschnittenen Titel.
- Fehlt Chromium für Playwright: `uv run --no-project --with playwright==1.64.0 python -m playwright install chromium`.
