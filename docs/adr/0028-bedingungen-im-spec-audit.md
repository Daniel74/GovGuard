# 0028 – Bedingungen im Spec-Audit

_Ergänzt [ADR 0026](0026-rechtsartikel-zerlegen.md) (Zerlegung) und [ADR 0025](0025-ki-vo-als-neue-quelle-bei-eingefrorenem-katalog.md) (eingefrorener Katalog); bricht SPEC G13 für DSGVO bewusst (#59, #60)._

## Kontext

- Der Spec-Katalog prüft jede Spezifikation gegen alle Regeln, auch gegen Pflichten, die für eine deutsche Behörde nie gelten. Das kostete 24 Lücken je Audit und beim Wohngeld ein falsches FAIL (Art. 27 Abs. 2).
- Vier DSGVO-Artikel sind für Behörden ausgeschlossen: Art. 20 Abs. 3 (öffentliche Aufgabe), Art. 27 (Vertreter nur außerhalb der EU), Art. 41 Abs. 6 (Behörden ausgenommen), Art. 47 (BCR nur für Unternehmensgruppen).

## Entscheidung

- **Vorfilter Behörde:** Der DSGVO-Vorfilter (`kb_build/extract/dsgvo.py`) verwirft Art. 20, 27, 41 und 47 mit festem Begründungssatz im Auswahlprotokoll. Die Liste ist bewusst fest, wie bei der KI-VO (ADR 0025); ein weiterer Artikel kommt nur mit Test dazu.
- **Rebuild ohne LLM-Aufruf:** `extract`, `decompose`, `select --only-missing` und `rules --only-missing` laufen allein aus Cache und eingefrorenem Teil. Die vier Artikel stehen als `prefiltered` im Auswahlprotokoll und fehlen in Auswahl und Katalog.
- **Bedingungs-Vorlauf (#60):** _Wird mit #60 ergänzt._

## Konsequenzen

- Der Spec-Katalog hat 350 statt 374 Prüfregeln (DSGVO 169 statt 193); genau die 24 Regeln der vier Artikel fehlen, alle übrigen sind byte-gleich.
- Die Galerie-Reports stehen noch auf 374 Regeln und entstehen mit #61 neu.
- Ein Verantwortlicher außerhalb der EU oder eine Unternehmensgruppe wird von GovGuard nicht mehr geprüft. Das ist eine bekannte Grenze: Das Werkzeug ist für Behörden gebaut.

## Fachgespräch-Satz

„Was für eine Behörde nie gilt, prüft GovGuard gar nicht erst: Der Vorfilter verwirft es mit Begründung im Protokoll, statt dass das Audit-LLM eine Lücke erfindet.“
