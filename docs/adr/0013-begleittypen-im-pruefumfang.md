# 0013 – Begleittypen im Prüfumfang, Typen außerhalb streicht der Code

_Ergänzt [ADR 0011](0011-vollstaendiger-katalog.md) (Prüfumfang)._

## Kontext

- Nach #17 prüft ein Gate jede Eigenschaft einer Prüfregel gegen `cfn_properties.json`. Die Datei kennt nur Typen aus `scope.json`. 16 Regeln nannten andere Typen (CloudTrail, CloudFront, Classic ELB, WAF Classic, EFS, Backup, Auto Scaling) und blieben ungeprüft (`unjudged_properties`).
- Zwei Anforderungen gehören zu Diensten im Prüfumfang, brauchen aber Typen daneben: FSBP DynamoDB.4 und RDS.26 (AWS Backup), Auto Scaling bei DynamoDB.

## Entscheidung

- **Begleittypen:** AWS Backup (`BackupVault`, `BackupPlan`, `BackupSelection`) und Application Auto Scaling (`ScalableTarget`, `ScalingPolicy`) kommen in den Prüfumfang. EFS, EBS-Volume und SSM-Parameter bleiben draußen (`AUSBAU.md`).
- **Der Code streicht:** Stufe ② entfernt Typen außerhalb des Prüfumfangs aus der Antwort, ohne Retry. Relevant bleibt „erster Typ im Prüfumfang“; bleibt keiner übrig, ist die Anforderung nicht relevant.
- **`formulate_rule` und Gate:** Kriterien mit Typen außerhalb des Prüfumfangs gehen per `ModelRetry` zurück; `check_rules` bricht ab, wenn eine Prüfregel solche Typen nennt.
- Jede Änderung an `scope.json` heißt: Snapshot neu ziehen und Stufe ② voll neu laufen lassen (kein Nachfiltern des Caches).

## Konsequenzen

- Das Gate aus #17 prüft jede Eigenschaft; `unjudged_properties` ist 0.
- Regeln, die nur auf Typen außerhalb des Prüfumfangs zeigen (z. B. CloudTrail-Bucket), fallen aus dem Katalog. Das Auswahlprotokoll nennt sie als „nicht relevant“.
- Der Prompt von Stufe ② ändert sich, der Judgement-Cache ist damit ungültig.

## Fachgespräch-Satz

„Ein Gate prüft nur so weit, wie seine Referenz reicht; deshalb begrenzt der Code die Prüfregeln auf den Prüfumfang, statt ungeprüfte Typen durchzulassen.“
