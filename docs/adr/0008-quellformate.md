# 0008 – Quellformate und Quellen außerhalb des Repos

## Kontext

- Der Existenz-Check vergleicht Zitate wörtlich mit der Quelle. PDF-Text ist dafür fehleranfällig: Ein Regex über das CIS-Inhaltsverzeichnis übersieht 3.2.2 und 6.4, weil dort ein Seitenumbruch liegt.
- Recherche `docs/research/Maschinenlesbare Formate für Compliance-Quellen.md`, nachgeprüft am 2026-10-09: Die DSGVO gibt es als Formex-XML über CELLAR. Für CIS AWS v7 gibt es offiziell nur das PDF, Prowler pflegt aber `cis_7.0_aws.json` (Apache-2.0, 70 Empfehlungen wie im PDF, mit Level, Automated/Manual und Langtexten). Das SDM gibt es nur als PDF. CSA CCM mappt nicht auf unsere Quellen.
- Die Terms of Use des CIS-PDF erlauben keine Weitergabe. Das PDF lag trotzdem im öffentlichen Repo.

## Entscheidung

| Quelle | Der Build lädt von | Gepinnt auf | Extrakt im Repo |
|---|---|---|---|
| BSI Grundschutz++ | GitHub `BSI-Bund/Stand-der-Technik-Bibliothek`, OSCAL | Commit-SHA | ja, CC BY-SA 4.0 |
| CIS AWS v7.0.0 | GitHub `prowler-cloud/prowler`, `cis_7.0_aws.json` | Commit `e2b2e568a6` + SHA-256 | nein |
| DSGVO | CELLAR, Formex, CELEX `02016R0679-20160504` | Fassung 000.003 + SHA-256 | ja, EU-Rechtstext |
| SDM | datenschutz-mv.de, PDFs Löschen, Trennen, Zugriffe regeln | SHA-256 | ja, dl-de/by-2-0 |

- **Keine Quelldatei im Repo.** `data/sources.json` nennt je Quelle URL, Version, SHA-256 und Lizenz. Der Build lädt jede Datei, prüft den Hash und bricht bei einer Abweichung ab. `data/sources/` ist nur ein lokaler Cache und steht in `.gitignore`.
- **Extrakte nur bei offener Lizenz.** Die Quellenvermerke stehen in `NOTICE`, beim SDM mit Veränderungshinweis. CIS-Volltexte kommen nie ins Repo: `cis.json` erzeugt der Build, eingecheckt werden nur Prüfregeln mit kurzem `source_quote`.
- **CIS-Anker** prüft der Existenz-Check gegen den Prowler-Text, und zwar nach `normalize()` ohne Markdown-Zeichen. DSGVO-Anker prüft er gegen `ARTICLE IDENTIFIER` im XML.

## Konsequenzen

- Für CIS und DSGVO entfällt der PDF-Parser. PDF-Extraktion braucht nur noch das SDM.
- Prowler ist eine abgeleitete Quelle. Abweichungen vom CIS-Original prüft eine Stichprobe gegen ein lokales PDF. Restrisiko: Prowler gibt CIS-Texte weiter, und die Prüfregeln zitieren daraus kurz.
- Ändert ein Herausgeber die Datei hinter einer URL, bricht der Build ab. Ein neuer Hash ist dann eine bewusste Aktualisierung per Pull Request.
- Das CIS-PDF wird aus der Git-Historie entfernt. `ARCHITECTURE.md` und die FAHRPLAN-Schritte 4 und 5 werden angepasst.

## Fachgespräch-Satz

„Jede Quelle ist auf Version und Prüfsumme gepinnt und wird vom Ursprung geladen – das macht den Build reproduzierbar, und wir verbreiten nichts, was die Lizenz nicht erlaubt.“
