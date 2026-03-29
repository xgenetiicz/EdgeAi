# Dokumentasjon: Edge & Server
Dette var økten hvor servertilkoblingen med bilder ble fullført. Vi koblet sammen Edge-enheten (ESP32) med server-infrastrukturen (Raspberry Pi 5) for å oppnå en sømløs overføring av bildedata.

### 1. Broen mellom Edge og Server (Base64)
Siden binære bildefiler kan være utfordrende å sende stabilt over enkle HTTP-forespørsler, implementerte vi en tekstbasert overføring:
<ul>
  <li>**Koding på enheten:** ESP32-en konverterer det binære bildet til en Base64-streng. Dette øker datastørrelsen med ca. 33 %, men sikrer at dataene ikke blir korrupte under overføring – noe som er kritisk for å unngå feil i skiltgjenkjenningen.</li>
  <li>**HTTP-overføring:** Bruk av `POST`-metoden for å sende tekststrengen til serverens spesifikke endepunkt på port 5000.</li>
</ul>

### 2. Python-mottaker i Docker (Flask-container)
For å håndtere de innkommende dataene utviklet vi en spesialisert mottaker-tjeneste:
<ul>
  <li>**Flask-server:** Et Python-script som lytter på port 5000 (`/upload-bilde`) inne i en isolert Docker-container.</li>
  <li>**Dekoding og lagring:** Scriptet tar imot Base64-strengen, dekoder den tilbake til binært JPEG-format, og lagrer filen med et unikt tidsstempel (Unix timestamp).</li>
  <li>**Automatisert filbehandling:** Filnavnene genereres automatisk (f.eks. `bil_1770746593.jpg`) for å unngå overskriving av data.</li>
</ul>

### 3. Persistent lagring og Volum-mapping
For å sikre at bildene er tilgjengelige for resten av systemet (Node-RED og AI-logikk), ble Docker-volumer konfigurert:
<ul>
  <li>**NVMe-lagring:** Containeren ble konfigurert til å lagre bildene direkte i mappen `${STORAGE_BASE}/bilder` på SSD-en.</li>
  <li>**Delt tilgang:** Ved å mappe `/bilder` i Python-containeren mot samme fysiske mappe som i Node-RED-containeren, oppnådde vi umiddelbar datatilgang på tvers av tjenester.</li>
</ul>

### 4. Verifisering av bildekvalitet og Begrensninger
Gjennom gjentatte tester verifiserte vi systemets ytelse, men avdekket også viktige hardware-begrensninger:
<ul>
  <li>**VGA-oppløsning:** 640x480 piksler gir tilstrekkelige detaljer for skilt- og objektidentifikasjon i dagslys.</li>
  <li>**Stabilitetstest:** Bekreftet at systemet tåler kontinuerlig overføring uten krasj i hverken ESP32-minnet eller Flask-serveren.</li>
  <li>**Utfordringer med lysforhold:** Tester viste at ESP32-kamerasensoren (OV2640) har betydelig støy og lav kontrast i mørke omgivelser. Dette identifiseres som en risikofaktor som kan påvirke sluttresultatet negativt ved kveldstid, men det er en uunngåelig begrensning gitt prosjektets tilgjengelige kamerautstyr.</li>
  <li>**Refleksjon rundt skalerbarhet:** Det konkluderes med at infrastrukturen nå oppfyller de kritiske funksjonskravene for datafangst. Selv om bildekvaliteten begrenses av IoT-enheten, er systemet modulært bygget, slik at selve kameraet enkelt kan oppgraderes til bedre utstyr senere uten å endre på server-arkitekturen.</li>
</ul>