---
name: folien-verlinken
description: Interne Links im Deep-Dive-Deck (Google Slides) setzen oder nach einem neuen Export neu setzen – Landkarte, Kapiteldeckblätter, Kapitelzeilen. Nutzt den Google-Slides-Connector.
---

Jede Folie trägt oben in der Kapitelzeile einen Code wie „K6.06 · KAPITEL 6 · SPEC-AUDIT“; das Deckblatt eines Kapitels endet auf `.00`, die Landkarte ist K0.01. Ziele findet das Skript immer über diesen Code, nie über die Seitenzahl. Es setzt nur das Linkformat: kein Text ändert sich, nichts wird verschoben. Jeder neue Export aus dem Slides-Artefakt verliert alle Links, danach läuft dieser Skill erneut.

## Regeln

| Regel | Wo | Verlinkter Text | Ziel |
|---|---|---|---|
| R1 | Landkarte K0.01 | „K6 · ab Folie 59“ (ganze Zeile der Karte) | Deckblatt K6.00 |
| R2 | jedes Deckblatt | jeder Code in „Folien in diesem Kapitel“, nur der Code | Folie mit diesem Code |
| R3 | jede andere Folie | „KAPITEL 6 · SPEC-AUDIT“ (ab „KAPITEL“ bis Zeilenende) | Deckblatt K6.00 |
| R4 | jedes Deckblatt | „KAPITEL 6“ | Landkarte K0.01 |

## Ablauf

`<skill>` ist dieser Ordner, `<s>` der Scratchpad. Die Präsentations-ID steht im Link, den der Nutzer gibt (`/presentation/d/<ID>/`).

1. **Deck lesen** mit `read_presentation` und genau dieser Feldmaske:

   ```
   revisionId,slides(objectId,pageElements(objectId,shape(text.textElements(startIndex,endIndex,textRun(content,style(link,foregroundColor,underline)))),elementGroup.children(objectId,shape(text.textElements(startIndex,endIndex,textRun(content,style(link,foregroundColor,underline)))))))
   ```

   Das Ergebnis (rund 1 MB) speichert das Werkzeug als Datei; kopiere sie nach `<s>/before.json`.

2. **Planen:** `python3 -I <skill>/links.py plan <s>/before.json <s>/plan`. Die Ausgabe nennt die Revision, die Zahl der Anfragen je Regel und alles, was nicht setzbar ist. Erwartet sind 15 × R1, je ein R4 pro Deckblatt außer K0.00, je ein R3 pro übriger Folie und je ein R2 pro übriger Folie außerhalb von Kapitel 0 (Stand 23.10.: 15 · 142 · 145 · 14).

3. **Schreiben**, Paket für Paket (`b1.json`, `b2.json`, …): Paket mit `cat` ausgeben und unverändert als `requests` an `update_presentation` geben, mit `writeControl.requiredRevisionId`. Paket 1 nimmt die Revision aus Schritt 2; vor jedem weiteren Paket die aktuelle Revision holen mit `read_slide_page` (beliebige Folie, Feldmaske `["revisionId"]`). Fertig, wenn jedes Paket nur leere Antworten `{}` zurückgibt.

4. **Prüfen:** Deck wie in Schritt 1 neu lesen nach `<s>/after.json`, dann `python3 -I <skill>/links.py verify <s>/before.json <s>/after.json`. Fertig, wenn: Reihenfolge gleich `True`, Text- und Farbänderungen `0`, interne Links = Zahl der Anfragen aus Schritt 2 (plus vorher schon vorhandene), falsche Ziele „keine“.

5. **Ansehen:** Vorschau eines Deckblatts mit `read_slide_page_thumbnail` holen, per `curl` nach `<s>/thumbs/` laden und mit Read öffnen. Fertig, wenn Codes und Kapitelzeile aussehen wie vorher: keine Unterstreichung, kein Link-Blau.

6. **Melden:** Links je Regel, acht Stichproben „Code „Text“ → Zielcode“ und die Liste „nicht setzbar“ aus Schritt 2 mit Grund.

## Fallstricke

- **Link-Farbe:** Setzt die API nur `link`, färbt sie den Text in die Link-Farbe des Themes und unterstreicht ihn. Deshalb schickt jede Anfrage die bisherige Farbe und Unterstreichung des Textstücks mit (`fields: link,foregroundColor,underline`).
- **Zeilenende:** Endet der Link am Zeilenende, bekommt das unsichtbare `\n` die Farbe des Textes davor. Das ist nicht sichtbar; `verify` ignoriert Zeilenenden.
- **Pakete:** 80 Anfragen pro Paket halten jeden Aufruf überschaubar. Ein Paket ist atomar: Schlägt es fehl, ist nichts davon gesetzt. Dann Revision neu holen und dasselbe Paket erneut senden.
- **Bekannte Lücken** im Stand vom 23.10.2026: K0.00 hat keine „Kapitel 0“-Zeile und keine Folienliste; die Kapitelzeile von K14.11 lautet „ZUM MITNEHMEN“ ohne „Kapitel 14“. Diese drei Links fehlen, bis der Text im Slides-Artefakt ergänzt ist.
