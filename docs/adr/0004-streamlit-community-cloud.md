# 0004 – Streamlit Community Cloud für die Demo-UI

## Kontext

Für Präsentation und Bewerbungen ist ein öffentlicher Live-Link gewünscht. Ein Frontend-Hosting in Frankfurt kostet Zeit und laufend Geld. Streamlit Community Cloud ist kostenlos, hostet aber in den USA.

## Entscheidung

- Die Demo-UI läuft auf Streamlit Community Cloud.
- Sie ruft die API in eu-central-1 per SigV4 über einen eigenen IAM-User auf, der nur `execute-api:Invoke` auf genau diese API darf. Das Recht erhält er nur über eine IAM-Gruppe (CIS 2.13).
- Schutz vor Missbrauch: Throttling am API-Stage und AWS-Budget-Alarm bei 5 €.

## Konsequenzen

- Eingaben verlassen über die UI die EU – es werden nur fiktive Daten verarbeitet; die UI weist darauf hin („Keine echten oder personenbezogenen Daten eingeben“). Technisch erzwingen lässt sich das nicht.
- Ein langlebiger Access Key liegt in den Streamlit-Secrets (Restrisiko, minimal berechtigt). Er wird spätestens alle 90 Tage rotiert (CIS 2.12).
- In Produktion zieht das Frontend nach Frankfurt; der Hosting-Dienst ist dann neu zu entscheiden.

## Fachgespräch-Satz

„Für die Demo akzeptiere ich US-Hosting der Oberfläche bewusst, weil nur fiktive Daten fließen – Backend, Daten und Inferenz bleiben in der EU, in Produktion zieht das Frontend nach Frankfurt.“
