# Bachelor: Edge AI Kjøretøyidentifikasjon

> **Prosjektformål:** Utvikle et skalerbart og personvernfokusert system for sanntidsidentifisering av kjøretøy ved bruk av Edge AI og offentlige API-er.

---

## Teknisk Arkitektur
Dette systemet er bygget på en **Raspberry Pi 5 (16GB RAM)** med et avansert NVMe-lagringsoppsett.

* **Hardware:** Raspberry Pi 5 m/ doble NVMe-disker (500GB OS / 2TB Data).
* **Plattform:** Docker & Portainer for containerstyring.
* **Edge AI:** ESP32-CAM som utfører lokal bildeanalyse for å minimere datatrafikk og ivareta personvern.
* **Cloudflare** Vi vil også eventuell bruke en cloudflare domene (vurderbart) slik at vi kan bruke dette på nettet - uavhengig av hvor vi er.


### Programvare-stakken (The Stack)
Systemet består av tre hovedkomponenter som kjøres i isolerte containere:
1. **MQTT (Mosquitto):** Broker for mottak av skiltdata fra Edge-enheter.
2. **InfluxDB:** Tidsseriedatabase optimalisert for NVMe for lagring av passeringer.
3. **Node-RED:** Systemets hjerne som utfører API-oppslag mot Statens Vegvesen.
4. **Redis** Vurderbart, inneholder caching som indexerer svært rask opp mot databasen og gir bedre responstid.
5. **Caddy** (Gateway): Fungerer som en Reverse Proxy som håndterer HTTPS-sertifikater og ruter trafikk til riktig tjeneste via subdomener.

---

## Sikkerhet & Konfigurasjon
Dette repositoriet er klargjort for offentlig publisering. 

### Miljøvariabler
Passord og sensitive data håndteres via en `.env`-fil som er ekskludert fra versjonskontroll via `.gitignore`. 
Dette er for å ivareta sikkerheten til IoT - applikasjonen vår og databasen.

---------------------------------------------------------------------------------------
## API-integrasjon
Systemet er integrert mot **Statens Vegvesen sitt Autosys-API**. 
Dette er API som er offentlig gjort ved bestilling som privat person, der dette gir kjøretøyopplysninger
samt teknisk data for mottak av et skiltnummer, der det utføres et teknisk enkeltoppslag for å berike dataene med:
* Kjøretøyets merke og modell.
* Registrert farge.
* *EU - kontroll*

---------------------------------------------------------------------------------------
## Prosjektdokumentasjon

Her finner dere detaljert dokumentasjon for de ulike fasene og komponentene i **prosjektet**:

* **[01 - Systemarkitektur og Infrastruktur](./Docs/01-Systemarkitektur.md):** Beskrivelse av maskinvare (Pi 5, NVMe), Docker-oppsett og sikkerhet.
* **[02 - Dataflyt og Backend](./Docs/02-Dataflyt-og-Backend.md):** Dokumentasjon av Base64-overføring, Flask-mottaker og lagringslogikk.
* **[03 - Edge-enhet](./Docs/03-Edge-enhet.md):** Teknisk oppsett av ESP32-CAM, kamerasensor og lokal lagring.
* **[05 - Sikker og Lokasjonsuavhengig IoT-Arkitektur](./Docs/05-Lokal-til-https.md):** Implementering av Cloudflare Tunnel og HTTPS.
* **[06 - Object Identification & AI Inference](./Docs/06-Object-Identification.md):** Gjennomgang av YOLOv8-modellvalg (XL), EasyOCR og bilde-annotering.
* **[07 - Roboflow, AI-trening og AMD Optimalisering](./Docs/07-Roboflow-AI-Training.md):** Dokumentasjon av trening på Linux/ROCm, auto-labeling med Gemini og treningsresultater - resultat er YOlOv8m modell - med eget trent datasett.