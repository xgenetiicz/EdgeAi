# Dokumentasjon: Edge-Enhet

Dette var økten der vi gikk fra teori til fysisk maskinvare. Målet var å få **AI Thinker ESP32-CAM**-modulen til å fungere som et frittstående kamera som tar bilder og lagrer dem lokalt på et SD-kort.

### 1. Hardware-oppsett og "Reset-dansen"
For å i det hele tatt få kontakt med brikken og laste opp programvare, måtte vi gjennom en spesifikk fysisk prosedyre:
<ul>
  <li>**Board-konfigurasjon:** Valgte riktig kort-profil (**AI Thinker ESP32-CAM**) i utviklingsmiljøet for å matche den spesifikke minnearkitekturen og pin-oppsettet.</li>
  <li>**Boot-modus:** Koblet **GPIO 0 til GND** med en jumper-kabel for å tvinge brikken inn i "Flash Mode". Uten denne koblingen er det umulig å skrive ny kode til brikken.</li>
  <li>**Flashing og Reset:** Trykket på den fysiske **Reset-knappen** på baksiden av kameraet for å starte mottak av kode, og kjørte opplastingen via FTDI-adapteren.</li>
  <li>**Kjøre-modus:** Fjernet jumperen mellom GPIO 0 og GND og trykket Reset på nytt for å la brikken starte den faktiske programlogikken.</li>
</ul>

### 2. Konfigurering av kamerasensor
Vi måtte programmere sensoren manuelt for å sikre stabil drift og unngå systemkræsj som følge av minnemangel:
<ul>
  <li>**Pindefinisjoner:** Manuelt definert alle 15 pinner (D0-D7, klokke, strøm osv.) spesifikt for AI Thinker-arkitekturen for å sikre korrekt bildestrøm.</li>
  <li>**JPEG Kvalitet 12:** Satte `config.jpeg_quality = 12`. Dette er et strategisk valg: Det gir høy nok bildekvalitet til at skiltnumre er lesbare for AI-logikk, samtidig som filstørrelsen holdes nede slik at brikken ikke går tom for RAM under prosessering.</li>
  <li>**VGA Oppløsning:** Valgte **640x480 (VGA)** som en optimal balanse mellom detaljnivå for bildeanalyse og ytelse på en mikrokontroller.</li>
</ul>

### 3. Implementering av SD-kort og Lokal Lagring
Et kritisk suksesskriterium var å sikre at bilder kan lagres lokalt som en redundans:
<ul>
  <li>**Biblioteker:** Inkluderte `FS.h` og `SD_MMC.h` for å kommunisere med det innebygde SD-kortgrensesnittet på modulen.</li>
  <li>**Initialisering:** Konfigurert `SD_MMC.begin("/sdcard", true)` for å montere lagringsmediet ved systemstart.</li>
  <li>**Verifisering:** Bekreftet at kameraet vellykket lagret bildefiler til SD-kortet, og at disse kunne hentes ut og åpnes manuelt på en ekstern maskin.</li>
</ul>

### 4. Nettverkstilkobling (Forberedelse)
<ul>
  <li>**WiFi-oppkobling:** Implementert logikk for å koble brikken til det lokale nettverket ("Hjemme_nettverk") for å klargjøre enheten for fremtidig dataoverføring til server-infrastrukturen.</li>
</ul>