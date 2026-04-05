# Bachelor: Edge AI Kjøretøyidentifikasjon

> **Prosjektformål:** Utvikle et skalerbart og personvernfokusert system for sanntidsidentifisering av kjøretøy og bilskilt ved bruk av Edge AI og offentlige API-er.

---

## Teknisk Arkitektur
Dette systemet er bygget rundt en **Raspberry Pi 5 (16GB RAM)** med et avansert NVMe-lagringsoppsett, designet for robust og lynrask Edge-prosessering.

* **Hardware:** Raspberry Pi 5 m/ doble NVMe-disker (500GB OS / 2TB Data).
* **Plattform:** Docker & Portainer for portabel og isolert containerstyring.
* **Kamerasystem (Edge):** Videostrøm hentes via RTSP fra en Raspberry Pi 4 over et sikkert **Tailscale**-nettverk (VPN). Bildeanalysen utføres sentralt på Pi 5 for å ivareta personvern lokalt.
* **Nettverk:** Cloudflare-domene og Cloudflare tunnel for sikker, lokasjonsuavhengig tilgang og HTTPS.

### Programvare-stakken (The Stack)
Systemet består av flere hovedkomponenter som kjøres sømløst sammen i Docker:
1. **AI / Image Processor:** Egenutviklet Python-container (YOLOv8 + EasyOCR) som leser RTSP-strøm, vasker bilder og trekker ut skiltnummer.
2. **MQTT (Mosquitto):** Broker for rask meldingsutveksling og IoT-kommunikasjon.
3. **InfluxDB:** Tidsseriedatabase optimalisert for NVMe, brukt for varig lagring av passeringer.
4. **Node-RED:** Systemets hjerne som orkestrerer dataflyten og utfører API-oppslag mot Statens Vegvesen.
5. **Redis:** Lynrask caching/mellomlagring som indekserer oppslag mot databasen og gir umiddelbar responstid.
6. **Caddy (Gateway):** Fungerer som en Reverse Proxy som håndterer HTTPS-sertifikater automatisk og ruter trafikk via subdomener.

---

## Sikkerhet & Konfigurasjon
Dette repositoriet er klargjort for offentlig publisering. 

### Miljøvariabler
Passord, API-nøkler og sensitive filstier (volumes) håndteres dynamisk via en `.env`-fil som er ekskludert fra versjonskontroll (`.gitignore`). Dette er av sikkerhetmessige grunner.
---

## API-integrasjon
Systemet er integrert mot **Statens Vegvesen sitt Autosys-API**. 
Dette er et API som er offentliggjort ved bestilling som privatperson. API-et gir tilgang til kjøretøyopplysninger og teknisk data. Når AI-modellen detekterer et skiltnummer, utføres et teknisk enkeltoppslag for å berike dataene i dashbordet med:
* Kjøretøyets merke og modell.
* Status for EU-kontroll.
---

## Prosjektdokumentasjon

Her finner dere detaljert dokumentasjon for de ulike fasene og komponentene i prosjektet:

* **[01 - Systemarkitektur og Infrastruktur](./Docs/01-Systemarkitektur.md):** Beskrivelse av maskinvare (Pi 5, NVMe), Docker-oppsett og sikkerhet.
* **[02 - Dataflyt og Backend](./Docs/02-Dataflyt-og-Backend.md):** Dokumentasjon av dataoverføring, Flask-mottaker og lagringslogikk.
* **[03 - Edge-enhet](./Docs/03-Edge-enhet.md):** Teknisk oppsett av kamera og lokal maskinvare.
* **[04 - Edge & Server](./Docs/04-Edge-og-Server.md):** Detaljer rundt Node-RED, API-oppslag mot Statens Vegvesen og logikk.
* **[05 - Sikker og Lokasjonsuavhengig IoT-Arkitektur](./Docs/05-Lokal-til-https.md):** Implementering av Cloudflare Tunnel og Caddy HTTPS.
* **[06 - Object Identification & AI Inference](./Docs/06-Object-Identification.md):** Gjennomgang av AI-modellering, EasyOCR og bilde-annotering.
* **[07 - Roboflow, AI-trening og AMD Optimalisering](./Docs/07-Roboflow-AI-Training.md):** Dokumentasjon av tidlig prototyping på Linux/ROCm og første trening – resultatet var en YOLOv8m-modell på eget datasett.
* **[08 - Skalering og Cloud-Trening: Fra Prototype til Produksjon](./Docs/08-Videre-Dyp-Trening.md):** Detaljer rundt hvordan datasettet ble oppskalert til 22 000 bilder med Gemini 2.0 Flash, og den endelige sky-treningen (`best.pt`) på en RTX 4090 via RunPod.
* **[09 - RTSP Strøm: Fra stillbilder til konstant videostrøm](./Docs/09-RTSP-Strøm.md):** Detaljer rundt hvordan konverteringen gikk fra ESP32 med et kamera til 640x440p gikk fra til å bli til en konstant video - strøm med en arducam 120fps monokromt kamera.
* **[10 - Stack for Raspberry Pi 4](/Docs/10-stack-rtsp.md):** Detaljer rundt om stacken som kjøres på Portainer for der videostrømmen går, og valgene som har blitt tatt for optimalisering på det ytterste nivået i form av driftssikkerhet. Driftsikkerhet er automatisk oppstart og driftsstabilitet på enheten kamernoden kjører på!
* **[11 - Script endringer: Fra en `Flask server` til `RTSP-Stream`](/Docs/11-script-changes-and-tailscale.md):** Detaljer om nettverksprotokollene som ble endret og etter kritisk tenkning samt analyse, gikk valget over til Tailscale.
Dokumentasjon også om `mottakerAvData.py` - der logikk strukturen ble endret.
* **[12 - Systemtest, produksjonstest & Optimalisering](/Docs/12-testing-build.md):** Detaljer om den kritiske testfasen, fra første live - test med Global Shutter - kamera og RTSP - strøm, til diagnose og løsning av Out of Memory-krasj på Pi 4 -> (60fps -> 30fps, 8 -> 4 Mbps).

