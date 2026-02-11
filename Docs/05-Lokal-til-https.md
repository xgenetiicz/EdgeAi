# Teknisk Dokumentasjon: Sikker og Lokasjonsuavhengig IoT-Arkitektur

## 1. Systemarkitektur (Edge-to-Cloud)
Løsningen er bygget på en hybrid-arkitektur som flytter bildebehandling fra et lokalt nettverk til en globalt tilgjengelig skytjeneste. Ved å benytte en **Cloudflare Tunnel (Connector)**, oppnår systemet sikker kommunikasjon uten behov for eksponering av porter i lokale rutere (Port Forwarding).

* **Edge-enhet (ESP32-CAM)**: Fungerer som sensornode som fanger bilder og koder dem til **Base64**-tekststrenger for robust overføring.
* **Sikker Transport**: All datatrafikk er kryptert med **HTTPS (TLS 1.3)** via subdomenet `api.gtztech.net`.
* **Mottaker (Raspberry Pi 5)**: En Flask-applikasjon i en Docker-container tar imot og dekoder dataene, før de lagres på en NVMe-disk.



---

## 2. Teknisk Gjennomføring og Valg
Under utviklingen ble det gjort kritiske arkitektoniske valg for å sikre systemets integritet:

* **SSL-terminering**: Cloudflare håndterer krypteringen mot internett, mens tunnelen leverer trafikken som HTTP internt til Flask-containeren på port ****.
* **Base64-stabilitet**: Valget om å sende data som Base64-tekst i stedet for rå binærdata løste problemet med korrupte 1 KB-filer, og sikrer at hele bildefilen mottas korrekt over ustabile nettverk.
* **Sertifikathåndtering**: Implementering av `client.setInsecure()` på ESP32 muliggjør kryptert kommunikasjon uten å belaste mikrokontrollerens begrensede minne med store root-sertifikatfiler.

---

## 3. Testresultater og Driftssikkerhet (Resilience)
Systemet ble stresstestet ved bruk av et **5G-hotspot** for å simulere en installasjon i feltet, med følgende resultater:

* **Nettverksuavhengighet**: Systemet leverte bilder feilfritt fra et mobilt nettverk til serveren, noe som beviser at løsningen er uavhengig av lokal nettverksinfrastruktur.
* **Auto-reconnect (Self-healing)**: Ved simulert nettverksbrudd bekreftet testen at ESP32-enheten automatisk gjenoppretter forbindelsen til både WiFi og Cloudflare-serveren uten manuelt tilsyn.
* **Konklusjon**: Denne evnen til selvreparasjon er kritisk for IoT-enheter plassert på ubemannede lokasjoner.

---

## 4. Refleksjon: Skalerbarhet og Markedspotensial
Arkitekturen er designet for å møte fremtidige krav til en profesjonell "Smart Parking"-løsning:

* **"Plug & Play"-skalering**: Siden sensoren er programmert mot et fast subdomene, kan nye enheter installeres hos kunder over hele verden uten behov for nettverkskonfigurasjon på stedet.
* **Datasikkerhet (GDPR)**: Ved å bruke HTTPS sikres personvernet for bildedataene (bilskilt), noe som er essensielt for å møte lovkrav i en kommersiell skala.
* **Unik Enhetsidentifisering**: Systemet er klargjort for å håndtere tusenvis av enheter mot samme sentrale API, der hver enhet ruter data til sine respektive lagringsvolumer på serveren.