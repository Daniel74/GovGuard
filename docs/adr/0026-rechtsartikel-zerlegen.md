# 0026 – Rechtsartikel in Einzelpflichten zerlegen

_Ergänzt [ADR 0011](0011-vollstaendiger-katalog.md) (Bounded Catalog) und [ADR 0025](0025-ki-vo-als-neue-quelle-bei-eingefrorenem-katalog.md) (eingefrorener Katalog); bricht SPEC G13 für DSGVO und KI-VO bewusst (#53)._

## Kontext

- Bei DSGVO und KI-VO war eine Anforderung ein ganzer Artikel. Die Prüfregel griff nur einen Aspekt heraus: Art. 32 nur Verschlüsselung, Art. 9 nur Einwilligung, KI-VO Art. 6 nur Anhang I.
- Ob eine Aufzählung „alle gelten“ oder „eine genügt“ bedeutet, sagt kein Parser. Der Prototyp vom 19.10.2026 (Groq) unterschied das zuverlässig, scheiterte aber oft am wörtlichen Zitat.

## Entscheidung

- **Neue Stufe `decompose`** zwischen `extract` und `select`, nur für DSGVO und KI-VO. Der Formex-Leser liefert Abschnitte mit Marke, z. B. `Art. 32 Abs. 1 lit. b`.
- **Das LLM nennt nur Marken und die Art jeder Gruppe**: `alle_gelten`, `eine_genuegt`, `je_nach_risiko`, `keine_pflicht`. Der Code prüft, dass jede Marke genau einmal vorkommt, sonst Retry. Wortlaut und Zitat übernimmt der Code.
- **Aus Gruppen werden Anforderungen:** Eine `eine_genuegt`-Gruppe wird eine Anforderung für den Absatz (`DSGVO Art. 6 Abs. 1`), die anderen Arten eine je Abschnitt. `keine_pflicht` gilt als vom Vorfilter verworfen, auch ein Verbot mit eigener Ausnahmeliste (DSGVO Art. 9 Abs. 1): Die Ausnahmen tragen die Prüfung.
- **`rules` kennt die Art:** Bei `eine_genuegt` prüft die Regel „mindestens eine der Alternativen ist festgelegt“, bei `je_nach_risiko` „soweit das Risiko es erfordert“.
- **Protokoll und Cache wie bei der Auswahl:** `decompositions_spec.json` hält Gruppen, Begründungen und Anker fest. Scheitert das LLM, bleibt der Artikel ganz.

## Konsequenzen

- Der Spec-Katalog wächst von 159 auf 374 Regeln (DSGVO 193, KI-VO 65, SDM 116 unverändert). Galerie und Soll-Anker entstehen neu; das Wohngeld-Soll weicht ab (FAIL statt WARN), gezeigt nach ADR 0023.
- **Zwei Ausnahmen vom Einfrieren**, weil der größere Katalog sie erzwingt: `rules` baut nach einem ungültigen Ergebnis (auch Groqs HTTP 400) weiter und sichert jede Regel im Checkpoint. Zur Laufzeit bremst ein Token-Budget von 200.000 pro Minute (`token_budget.py`) die Pakete unter Groqs Limit.
- SDM-Querverweise auf ganze Artikel bleiben gültig: Das Gate bildet den Artikel-Anker auf seinen ersten Teil ab. Das reicht für die Existenzprüfung, nicht für eine Zitatprüfung.
- Die Arten bleiben als deutsche Werte im Code: Sie sind Teil des deutschen Tool-Schemas fürs LLM und stehen im Glossar.
- Jede Prompt-Änderung würfelt neu (54 von 475 Abschnitten wechselten ihre Art). Ein Test prüft die Prüfsteine (DSGVO Art. 5, 6, 9, 32, KI-VO Art. 5, 6) gegen das Protokoll.

## Fachgespräch-Satz

„Das LLM entscheidet nur, ob Abschnitte zusammen oder alternativ gelten; Wortlaut und Anker kommen vom Code, deshalb kann keine Pflicht verloren gehen oder erfunden werden.“
