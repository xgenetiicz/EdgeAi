# 09 - Oppgradering av Kamerasystem: Fra ESP32 til RTSP og Global Shutter

For at objektidentifikasjonen og spesielt OCR-lesingen skulle fungere optimalt i et reelt miljø, ble det tidlig klart at maskinvaren for bildeinnhenting måtte oppgraderes. Dette kapittelet dokumenterer overgangen fra enkle stillbilder til en kontinuerlig, høyoppløselig videostrøm.

## 1. Begrensningene med ESP32-CAM
I den tidlige fasen av prosjektet benyttet jeg et ESP32-CAM. Dette var utmerket for rask prototyping, men det hadde flere kritiske svakheter for dette spesifikke bruksområdet:
* **Oppløsning:** Begrenset til lav oppløsning (primært 640x480), noe som ga EasyOCR for få piksler å jobbe med når bilene var på avstand.
* **Rolling Shutter:** ESP32-kameraet leser pikslene linje for linje. Når en bil kjører forbi i hastighet, skaper dette en "jello-effekt" (bevegelsesuskarphet og forvrengning) som gjør bokstavene på bilskiltet uleselige for AI-en.
* **Prosessering:** Modulen slet med å levere bilder raskt nok, noe som førte til at biler ofte rakk å kjøre ut av bildet før systemet reagerte.
* **Støy samt mørke kontraster:** ESP32 - slet utrolig mye med mørke omgivelser som er forståelig, men samtidig var dette så mye støy i bildene at det var vanskelig å gjennkjenne hva objektet var.

## 2. Løsningen: 1280x720px Global Shutter
For å løse problemet med bevegelsesuskarphet, gikk jeg til anskaffelse av et **Global Shutter**-kamera etter samtale med veileder. I motsetning til rolling shutter, eksponerer en global shutter-sensor alle pikslene nøyaktig samtidig. Resultatet er krystallklare bilder av objekter i høy hastighet – et absolutt krav for vellykket skiltgjenkjenning.
Samtidig ble oppløsningen doblet til 1280x720 piksler, noe som ga AI-modellen et mye rikere detaljnivå å analysere.

## 3. Infrastruktur: Repurposing av Raspberry Pi 4
Siden prosjektets hovedmaskin (Raspberry Pi 5) allerede var tungt belastet med å kjøre AI-modellen (`best.pt`), Node-RED, InfluxDB og Docker-infrastrukturen, valgte jeg en distribuert arkitektur. 

Jeg tok i bruk en Raspberry Pi 4 jeg hadde liggende hjemme, og dedikerte den utelukkende til rollen som en "Kamera-node". Målet var at Pi 4-en skulle håndtere maskinvaren og strømme videoen over nettverket til Pi 5-en for analyse.

## 4. Etablering av RTSP-strøm med MediaMTX
Å gå fra enkle HTTP-stillbilder på ESP32 til en stabil RTSP-videostrøm (Real-Time Streaming Protocol) viste seg å kreve betydelig innsats. Jeg valgte å bruke **MediaMTX** (tidligere rtsp-simple-server) som strømmeserver på Raspberry Pi 4.

**Linux-komplikasjoner under oppsett:**
Å få strømmen i gang var en vanskelig oppgave. Det oppsto flere komplikasjoner knyttet til Linux-miljøet og drivere:
* **Video4Linux2 (v4l2):** Å få MediaMTX til å snakke riktig med kameraets hardware-grensesnitt krevde presis konfigurasjon av enhetsfilene (`/dev/video0`).
* **Rettigheter og Grupper:** Det oppsto utfordringer med brukerrettigheter, hvor tjenesten måtte gis spesifikk tilgang til `video`-gruppen i Linux for å få lov til å lese data fra kamerasensoren. Dette er $USERS permissions og måtte gi meg selv chown mod permissions.
* **Hardware Encoding:** For å unngå at CPU-en på Pi 4-en knelte, måtte systemet konfigureres til å utnytte maskinvareakselerert koding (h264_v4l2m2m) slik at strømmen kunne sendes effektivt.
**FPS strøm:*** 120 fps strøm var alftor mye - dette fikk Raspberry Pi 4 med 4GB RAM til å kræsje - så måtte konfigurere denne på 60 fps. Da funket ./mediamtx og serveren var oppe og gikk med riktig portnummer.

## Oppsummering
Etter utstrakt feilsøking på Linux-nivå, resulterte arbeidet i en bunnsolid RTSP-strøm. Kamerasystemet sender nå en kontinuerlig monokront 720p Global Shutter-strøm fra Raspberry Pi 4.