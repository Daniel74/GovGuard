"""German UI texts shared by several pages (#11)."""

DATA_WARNING = ("Keine echten oder personenbezogenen Daten eingeben. "
                "Eingaben gehen zur Inferenz an Groq in die USA.")  # ADR 0004, 0016, 0023

HELP = {  # help on the report head; status help lives in style.LOOKS
    "judge": "Ein zweiter Modellaufruf sieht je FAIL nur das Verstoßkriterium und die "
             "Belegzeilen. Bestätigt er nicht, stuft der Code auf WARN herab. „Nicht "
             "verfügbar“: Das FAIL bleibt ungeprüft stehen. Nur bei Spezifikationen.",
    "expected": "Jedes Preset hat ein festgelegtes Soll: Gesamtstatus und Pflichtbefunde. Weicht "
                "ein Report ab, zeigt GovGuard das offen, statt neu zu würfeln. Ein Klick auf "
                "einen Pflichtbefund springt zu ihm.",
    "overall": "Der strengste Status aller Befunde: FAIL vor WARN vor PASS vor N/A.",
}

TYPE_LABELS = {"spec": "Spezifikation (DSGVO, SDM)",
               "architecture": "Architektur (BSI IT-Grundschutz, BSI C5, CIS, AWS FSBP)"}
