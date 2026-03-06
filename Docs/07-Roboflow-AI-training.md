# 07 - Roboflow, AI-trening og AMD Optimalisering

Denne modulen dokumenterer progresjonen fra innledende datainnsamling til et ferdig trent AI-system optimalisert fra AMD-maskinvare.

## 1. Utviklingsreisen: Fra Edge Impulse til Roboflow
Prosjektet har flyttet seg gjennom flere stadier for å finne den mest effektive metoden for datasettbehandling:
* **Fase 1: Edge Impulse**: Brukt innledningsvis for rask prototyping, men ble funnet for begrenset for komplekse YOLO-arkitekturer og spesialisert trening.
* **Fase 2: Gemini API (Auto-labeling)**: For å effektivisere arbeidet ble Gemini API benyttet til å tegne "Bounding Boxes" på bildene vi tok med ESP32-kameraet. Dette automatiserte en ellers tidkrevende manuell prosess og sikret et godt grunnlag for treningen.
* **Fase 3: Roboflow**: Valgt som endelig plattform på grunn av overlegen håndtering av versjoner og automatisering. Datasettet på 163 bilder er splittet i en 70/20/10-fordeling for trening, validering og testing.

## 2. Tekniske Utfordringer: Windows vs. Linux Compute
Den største tekniske utfordringen i prosjektet var operativsystemets begrensninger for AI-computing på AMD-kort (RX 6700 XT).
* **Windows-problematikken**: Forsøk på å kjøre trening under Windows feilet fordi operativsystemets bakgrunnsprosesser og strenge regelsett hindret direkte kommunikasjon med AMD ROCm. Dette gjorde det umulig for PyTorch å benytte skjermkortets regnekraft til Python-skriptene våre.
* **Løsningen (Linux/ROCm)**: Ved å etablere en Dual-Boot-løsning med Ubuntu, kunne vi fjerne operativsystem-sperrene. Linux tillot direkte kontakt med GPU-en via `/dev/kfd`, noe som låste opp støtte for ROCm og PyTorch. Dette var det kritiske steget som gjorde at vi kunne flytte treningen fra CPU til GPU.

## 3. Treningsresultater og GPU-ytelse
Ved å bruke 6700 XT-kortet på Linux-siden, ble treningen ekstremt effektiv:
* **Hastighet**: 100 epoker ble fullført på kun **2,28 minutter** (0.038 timer) - der CPU Ryzen 7 7800x3D brukte nesten opp mot 40 minutter.
* **Nøyaktighet (mAP50)**:
    * **License Plate**: Oppnådde **0.777**, som er et svært sterkt resultat for identifikasjon av skilt.
    * **Car**: Oppnådde **0.527**, som er tilstrekkelig for å detektere kjøretøy under varierte forhold.
* **Inferens**: Systemet har en responstid på **1.0ms per bilde**, som er mer enn raskt nok for sanntidsbruk.

## 4. Refleksjonsnotat: Miljøfaktorer og Augmentering
Treningen må ses i sammenheng med utstyrets begrensninger:
* **Sensorstøy i mørket**: ESP32-CAM (OV2640) har betydelig støy i mørke arealer, noe som kan skape forvirring for AI-modellen og føre til feilklassifiseringer.
* **Albumentations**: For å motvirke dette har vi brukt augmentering (Albumentations) i Roboflow for å simulere dårlige lysforhold og støy under treningen. Dette gjør modellen mer robust mot det faktiske støynivået fra kameraet.
* **Konfidensterskel**: For å unngå at sensorstøy tolkes som objekter, har vi landet på en sikkerhetsmargin (Confidence) på **0.7** for å sikre pålitelige visuelle bevis.

## 5. Veien Videre: Validering og Implementering
Neste kritiske fase fokuserer på å validere den egenutviklede modellen i et reelt miljø:
* **Test av egenlaget modell**: Det skal gjennomføres omfattende tester for å dokumentere hva den ferdig trente modellen presterer i praksis.
* **Dagslys-verifisering**: Testingen vil primært foregå i dagslys for å evaluere modellens evne til å detektere kjøretøy og gjennomføre korrekt skiltregistrering.
* **Systemintegrasjon**: Når deteksjonen er verifisert, ferdigstilles applikasjonen i Node-RED. Siden logikken for API-oppslag mot Statens Vegvesen allerede er på plass, vil fokuset ligge på å knytte AI-resultatene sammen med dashboardet for en komplett brukeropplevelse.