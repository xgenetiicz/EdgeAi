# Systemarkitektur og Infrastruktur

### 1. Hardware og Operativsystem (Fundamentet)
<ul>
  <li>Valg av **Raspberry Pi 5 (16GB RAM)** som sentral prosesseringsenhet for å sikre tilstrekkelig ytelse til parallelle AI-tjenester og databehandling.</li>
  <li>Konfigurering av lagringsløsning med doble **NVMe-disker**: 500GB partisjonert til operativsystemet og en dedikert 2TB M.2 NVMe SSD for lagring av data og bilder, noe som sikrer maksimal lese- og skrivehastighet.</li>
  <li>Installasjon av **Raspberry Pi OS (64-bit)** med optimalisering av filsystemet for håndtering av tunge Docker-volumer.</li>
  <li>Montering og oppsett av **Pironman 5 Max**-kabinett for effektiv aktiv kjøling og integrert støtte for M.2-lagring på Raspberry Pi 5.</li>
</ul>

### 2. Docker og Utviklingsmiljø
<ul>
  <li>Etablering av **Docker og Docker Compose** for å kjøre systemet som en isolert og skalerbar mikrotjeneste-arkitektur.</li>
  <li>Implementering av **Portainer** som grafisk grensesnitt for visuell overvåking og effektiv administrasjon av container-stacks.</li>
  <li>Automatisering av distribusjon ved å koble Portainer direkte til prosjektets **GitHub-repositorium**, noe som muliggjør kontinuerlig oppdatering («pull»), bygging og re-deployering av stacks fra `main`-branchen.</li>
</ul>

### 3. Den Initielle Programvare-stacken
<ul>
  <li>**MQTT (Mosquitto):** Broker konfigurert for å håndtere meldinger og dataoverføring fra ESP32-CAM.</li>
  <li>**InfluxDB 2.x:** Tidsseriedatabase klargjort for strukturert lagring av kjøretøydata og historiske passeringer.</li>
  <li>**Node-RED:** Implementert som systemets sentrale logikkmotor for databehandling og integrasjon mot Statens Vegvesen API.</li>
  <li>**Persistent lagring:** Konfigurering av faste volumer mot SSD (f.eks. `${STORAGE_BASE}/`) for å sikre data-integritet og hindre datatap ved container-oppdateringer.</li>
</ul>

### 4. Sikkerhet og Konfigurasjonsstyring
<ul>
  <li>Bruk av **.env-filer** for sikker håndtering av sensitive miljøvariabler, som passord og API-nøkler, adskilt fra kildekoden.</li>
  <li>Oppsett av en omfattende **.gitignore** for å ekskludere sensitive data, logger og store databasefiler fra versjonskontroll på GitHub.</li>
  <li>Etablering av juridisk rammeverk via **LICENSE**-fil for å beskytte bachelorgruppens opphavsrett til egenutviklet kildekode.</li>
  <li>Implementering av **Caddy Reverse Proxy** for å skjule interne porter og sikre trafikken, samt oppsett av autentisering med **CaddyHash** for tilgang til Node-RED Dashboard via domenet.</li>
</ul>