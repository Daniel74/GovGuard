# 0002 – Bounded Catalog statt Retrieval

## Kontext

Top-K-Retrieval kann relevante Anforderungen übersehen – für ein Audit ist das eine Vollständigkeitslücke. Eine Vektor-Datenbank kostet zudem im Leerlauf Geld. Die Quellen sind groß (BSI Grundschutz++ allein ca. 1.000 Anforderungen).

## Entscheidung

- Je Audit-Art gibt es eine fest begrenzte Menge Prüfregeln: Architektur-Audit 12 BSI + 12 CIS, Spec-Audit 20 aus DSGVO und SDM.
- Der Katalog geht in jedem Audit vollständig in den Prompt; der Code prüft, dass jede Prüfregel genau einen Befund hat.
- Die Auswahl entsteht zur Build-Zeit für alle Quellen gleich: deterministischer Vorfilter → LLM klassifiziert „prüfbar ja/nein“ mit Begründung → deterministisches Ranking (BSI: Summe der Schutzziel-Werte; CIS: Level 1 vor Level 2) → Obergrenze.
- Der BSI-Katalog wird auf einen Commit-SHA fixiert (das Repo hat keine Releases).

## Konsequenzen

- Keine Suche, keine Embeddings, keine Vektor-DB.
- Die Abdeckung ist bewusst begrenzt; die Auswahlliste liegt versioniert im Repo.
- SDM ohne Protokollieren (M43): eigenes ID-Schema in V2.0, Aufwand zu hoch; Protokollierung deckt das Architektur-Audit ab.
- Ausbau später per Map-Reduce: mehrere Teilkataloge parallel auswerten.

## Fachgespräch-Satz

„Bei uns kann keine Regel durchs Retrieval fallen: Jede Prüfregel des Katalogs bekommt in jedem Audit einen Befund – das prüft der Code, nicht das Modell.“
