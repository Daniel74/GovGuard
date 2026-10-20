"""German UI texts shared by several pages (#11)."""

from govguard_ui.style import LOOKS, STATUS_FILTERS

DATA_RULE = "Keine echten oder personenbezogenen Daten eingeben."  # ADR 0004, 0016, 0023

OPEN_WORLD_ONLY = "Nur bei offener Welt: Spezifikation, Architektur als Freitext."  # ADR 0020
HELP = {  # help on the report head; status help lives in style.LOOKS
    "judge": "Ein zweiter Modellaufruf sieht je Verstoß nur das Verstoßkriterium und die "
             f"Belegzeilen. Bestätigt er nicht, stuft der Code auf {LOOKS['WARN'].label} herab. "
             "„Nicht verfügbar“: Der Verstoß bleibt ungeprüft stehen. " + OPEN_WORLD_ONLY,
    "expected": "Jeder Musterfall hat ein festgelegtes Soll: Gesamtstatus und Pflichtbefunde. "
                "Weicht ein Report ab, zeigt GovGuard das offen, statt neu zu würfeln. Ein Klick "
                "auf einen Pflichtbefund springt zu ihm.",
    "conditions": "Manche Prüfregeln gelten nur unter einer Bedingung, z. B. die KI-VO nur für ein "
                  "KI-System. Vor dem Audit prüft die KI, was die Eingabe zu jeder Bedingung "
                  "sagt. Nur ein **nein** mit Beleg macht Prüfregeln nicht anwendbar. Der Pfeil "
                  "an jeder Bedingung zeigt Erklärung und Beleg.",
    "gaps": "Eine Lücke ist eine Prüfregel, zu der die Eingabe nichts sagt. Das ist kein Verstoß, "
            "sondern eine offene Frage: vor der Umsetzung klären oder bewusst ausschließen. Im "
            f"JSON-Report: {LOOKS['GAP'].code}. Die Lücken stehen nicht in der Befundtabelle oben.",
    "overall": "Der strengste Status aller Befunde: "
               + " vor ".join(LOOKS[name].label for name in STATUS_FILTERS) + ".",
}

VALUE_WORDS = {"yes": "ja", "no": "nein", "unstated": "nicht genannt"}  # result of a condition

TYPE_LABELS = {"spec": "Spezifikation (DSGVO, KI-VO, SDM)",
               "architecture": "Architektur (BSI IT-Grundschutz, BSI C5, CIS, AWS FSBP)"}
TYPE_CHOICES = {  # radio options on "Audit erstellen": norms and input formats (#41)
    "spec": "**Spezifikation** · DSGVO, KI-VO, SDM · Markdown oder OpenAPI",
    "architecture": "**Architektur** · BSI IT-Grundschutz, BSI C5, CIS, AWS FSBP · "
                    "CloudFormation-JSON, Terraform oder Freitext",
}
