# 0025 – KI-Verordnung als neue Quelle bei eingefrorenem Katalog

_Ergänzt [ADR 0008](0008-quellformate.md) (Quellformate) und [ADR 0011](0011-vollstaendiger-katalog.md) (Bounded Catalog); setzt SPEC G13 um (#52). Für DSGVO und KI-VO teilweise ersetzt durch [ADR 0026](0026-rechtsartikel-zerlegen.md), siehe Nachtrag._

## Kontext

- GovGuard ist selbst ein KI-System. Das Selbst-Audit `spec-govguard` soll deshalb die eigene Einstufung nach der KI-Verordnung (Verordnung (EU) 2024/1689) prüfen.
- Seit Schritt 12l ist der Spec-Katalog eingefroren: 151 Prüfregeln aus DSGVO und SDM, auf denen alle Galerie-Reports stehen. Ein Neubau würde jede Regel neu formulieren und die Galerie unvergleichbar machen.
- Fund vom 19.10.2026: Die eingecheckte Spec-Auswahl stammt von Prompt-Version `8cb1a979f2c2`, der Code steht seit dem 13.10. auf `7c67212e69aa`. Ein normales `select` würde 19 der 151 Anforderungen verwerfen und 8 andere aufnehmen, obwohl der Cache greift.
- CELLAR bietet die konsolidierte Fassung `02024R1689-20260727` als Formex-ZIP an, mit eingefügten Artikeln (Art. 4a) und den verschobenen Hochrisiko-Fristen (Art. 113).

## Entscheidung

- **Neue Quelle `KI-VO`** aus der konsolidierten Fassung 27.07.2026 (Stand 29.09.2026), gepinnt mit SHA-256. Den Formex-Leser teilen sich DSGVO und KI-VO (`extract/formex.py`). Der Vorfilter behält Art. 4, 5, 6, 13, 14, 26, 27 und 50.
- **Auswahl und Regeln bleiben eingefroren.** `select --only-missing` behält Auswahl und Auswahlprotokoll und stuft nur Anforderungen ohne Urteil ein. `rules --only-missing` übernimmt jede vorhandene Regel unverändert und formuliert nur die neuen. Ein Test pinnt den Hash der 151 Regeln.
- **Nur fürs Spec-Audit.** Das Architektur-Audit braucht für sein Abdeckungs-Gate die ganze Auswahl und baut weiter vollständig.
- **Der Spec-Prompt nennt Beispiele für KI-Systeme** (Einstufung, verbotene Praktiken, KI-Kompetenz). Ohne sie verwarf das Modell Art. 4, 5 und 6 als nicht prüfbar (Lauf vom 19.10.2026). Das weicht bewusst von #52 ab. Für die alten Regeln ist das harmlos, denn `--only-missing` liest die eingecheckte Auswahl und nicht den Cache.

## Konsequenzen

- Die übrigen Galerie-Reports bleiben auf ihrem Katalogstand mit 151 Prüfregeln und werden nicht neu erzeugt.
- Die Hochrisiko-Einstufung entscheidet das Audit-LLM anhand von Art. 6, ohne eigene Vorstufe im Code. Das ist eine bekannte Grenze.
- Eine Prüfregel je Artikel greift bei langen Artikeln nur einen Aspekt heraus: Art. 5 nur ein Verbot, Art. 6 nur Abs. 1 (Anhang I), nicht Anhang III.
- Ein künftiger Neubau ohne `--only-missing` würfelt mit der neuen Prompt-Version auch DSGVO und SDM neu.
- Der Vorfilter ist bewusst eine feste Liste von 8 Artikeln und kein Kapitelfilter wie bei der DSGVO. Ein weiterer Artikel kommt nur über eine Änderung dieser Liste dazu, mit Test.

## Fachgespräch-Satz

„Eine neue Rechtsquelle kommt dazu, ohne dass sich eine einzige alte Prüfregel ändert: Das macht der Hash-Test beweisbar, nicht nur behauptet.“

## Nachtrag 19.10.2026: Zerlegung bricht das Einfrieren für DSGVO und KI-VO (#53)

- ADR 0026 zerlegt DSGVO- und KI-VO-Artikel in Einzelpflichten. Deren Regeln entstehen neu, mit Absatz-Ankern wie `KI-VO Art. 50 Abs. 2`. Der Spec-Katalog hat jetzt 374 Prüfregeln, die beiden Spec-Galerie-Reports sind neu erzeugt.
- Eingefroren bleiben nur die 116 SDM-Regeln; der Hash-Test pinnt nur noch sie. Alte Regeln bekommen ihr `source_quote` vom Code (`quoted_by_code`), Kriterien und Empfehlung bleiben.
- `--only-missing` bleibt der Weg für neue Quellen, beide Befehle nur fürs Spec-Audit. Der Fachgespräch-Satz gilt seither für SDM.
