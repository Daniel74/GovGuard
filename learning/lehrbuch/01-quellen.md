# 01 – Quellen: gepinnt, geprüft, nicht im Repo

## Zweck

Der Build lädt jedes Regelwerk selbst vom Herausgeber. Er muss bei jedem Lauf dieselbe Datei bekommen (Reproduzierbarkeit) und darf keine Texte weitergeben, die die Lizenz nicht erlaubt (ADR 0008).

## Ablauf

`data/input/sources.json` → `SourceSpec` je Eintrag → `fetch_to_cache()` → SHA-256 prüfen → lokaler Cache `data/intermediate/sources/` → `read_cached()` (JSON als dict, XML und PDF als bytes). Alles in `kb_build/source_fetch.py`.

## Eigenschaften und Garantien

- **Pinning:** Jede URL ist auf einen Commit-SHA, Tag oder eine Fassung fixiert. Die Datei dahinter ändert sich nicht still.
- **Hash-Gate:** `_verify()` vergleicht die SHA-256 mit dem Eintrag in `sources.json` und wirft `SourceHashMismatchError`. Das gilt **auch für den Cache**: Eine manipulierte lokale Datei fällt auf (Test `test_fetch_to_cache_rejects_tampered_cache_file`).
- **Einziger HTTP-Ort:** Nur `source_fetch.py` darf HTTP (`urllib.request`); ein Architekturtest erzwingt das (`tests/test_architecture.py`).
- **Injizierbarer Fetcher:** `fetch_to_cache(..., fetcher=...)` nimmt eine Funktion entgegen, Tests reichen einen Fake hinein, ohne Netz.
- **Neuer Hash ist Absicht:** Ändert ein Herausgeber die Datei, bricht der Build ab. Ein neuer Hash ist dann eine bewusste Aktualisierung per Pull Request.

## Die Quellen (ADR 0008)

| Quelle (`SourceName`) | Format | Geladen von | Gepinnt auf | Extrakt im Repo |
|---|---|---|---|---|
| BSI Grundschutz++ (`BSI`) | OSCAL-JSON | GitHub `BSI-Bund/Stand-der-Technik-Bibliothek` | Commit `c96d9f57…` | ja (CC BY-SA 4.0) |
| CIS AWS v7.0.0 (`CIS`) | Prowler-JSON | GitHub `prowler-cloud/prowler` | Tag `5.44.0`, Commit `499fd637` | nein (Lizenz) |
| AWS FSBP (`FSBP`) | Prowler-JSON | Prowler, gleicher Tag | `5.44.0` | nein |
| BSI C5:2025 (`C5`) | Prowler-JSON | Prowler, gleicher Tag | `5.44.0` | nein |
| DSGVO (`DSGVO`) | Formex-XML | CELLAR (EU-Veröffentlichungsamt) | Fassung `000.003` | ja (EU-Recht) |
| SDM (`SDM`) | 3 PDFs | datenschutz-mv.de | SHA-256, Versionen V1.0a / V1.0 / V1.0 | ja (dl-de/by-2-0) |

`sources.json` hat acht Einträge, weil das SDM aus drei Bausteinen besteht (M60 Löschen, M50 Trennen, M51 Zugriffe regeln).

## Warum so

- **Maschinenlesbar statt PDF:** Der Existenz-Check vergleicht Zitate wörtlich. PDF-Text ist dafür fehleranfällig; ein Regex über das CIS-Inhaltsverzeichnis übersah 3.2.2 und 6.4 wegen eines Seitenumbruchs. Deshalb: OSCAL, Formex, Prowler-JSON. Nur das SDM gibt es nur als PDF.
- **Prowler als abgeleitete Quelle:** Für CIS AWS v7 gibt es offiziell nur das PDF. Prowler pflegt ein JSON mit 70 Empfehlungen wie im PDF. Eine Stichprobe gegen ein lokales PDF sichert die Texttreue ab. Dasselbe Schema nutzen FSBP und C5, deshalb teilen sie einen Parser (`extract/prowler.py`).
- **Lizenz:** Die Nutzungsbedingungen des CIS-PDF erlauben keine Weitergabe; das PDF wurde aus der Git-Historie entfernt. CIS-, FSBP- und C5-Volltexte stehen in `.gitignore` (`data/intermediate/extracted/cis.json`, `fsbp.json`, `c5.json`). Eingecheckt werden nur Prüfregeln mit kurzem `source_quote`. Quellenvermerke stehen in `NOTICE`.

## Beispiel: ein Eintrag in `sources.json`

```json
"fsbp_aws_prowler": {
  "url": "https://raw.githubusercontent.com/prowler-cloud/prowler/499fd637/prowler/compliance/aws/aws_foundational_security_best_practices_aws.json",
  "version": "5.44.0",
  "sha256": "8462b45bf7e2b1c9781ce6b83e5a1ab0369aae34364790cda978f55a7619a900",
  "license": "Apache-2.0 (Prowler JSON). Texts by AWS, license unclear: treated like CIS (ADR 0008).",
  "filename": "fsbp_aws_prowler.json"
}
```

## Fachbegriffe

- **SHA-256:** Prüfsumme; ändert sich ein Zeichen der Datei, ändert sich die Summe.
- **Pinning:** Eine Abhängigkeit auf eine exakte Version festlegen, nicht auf „neueste“.
- **OSCAL:** maschinenlesbares Format des NIST für Kataloge von Sicherheitsanforderungen; das BSI veröffentlicht Grundschutz++ so.
- **Formex:** XML-Format der EU für Rechtstexte.
- **Abgeleitete Quelle:** ein Text, den nicht der Urheber, sondern ein Dritter (Prowler) weitergibt.

## Grenzen

- Prowler ist zweite Hand: Abweichungen vom CIS-Original fängt nur die Stichprobe ab (ADR 0008).
- Die lizenzierten Volltexte gehen bei jedem Lauf an Groq (US). Das nimmt ADR 0014 für einen Prototyp ohne Weitergabe in Kauf.

## Fragen für das Fachgespräch

1. Wie stellen Sie sicher, dass der Build bei jedem Lauf dieselbe Quelle liest?
2. Warum liegen CIS-Volltexte nicht im öffentlichen Repo, und was liegt stattdessen dort?
3. Was passiert, wenn der Herausgeber die Datei hinter der URL ändert?
