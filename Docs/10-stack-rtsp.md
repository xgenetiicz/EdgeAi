## 5. Automasjon driftsikkerhet med Docker (Docker Stack)
For å gjøre Raspberry Pi 4-en til en fullstendig autonom "Kamera-node", var det kritisk at videostrømmen startet automatisk ved strømbrudd eller system-omstart. Å måtte logge inn via SSH for å starte MediaMTX-serveren manuelt ved hver eneste test var verken skalerbart eller holdbart for et reelt Edge-miljø.

**Løsningen: Containerisering med Docker**
For å løse dette problemet, var valget å pakke RTSP-serveren inn i en egen **Docker Stack** ved hjelp av en `docker-compose.yml`-fil lokalt på Raspberry Pi 4-en. 
stacken er synlig i:

![Stack For PI 4](/Docker/docker-composepi4.yml)

* **Restart Policies:** Ved å konfigurere containeren med parameteren `restart: always`, instrueres Docker-motoren på operativsystemnivå til å kontinuerlig overvåke tjenesten.
* **Autonom Drift:** Dersom maskinen mister strømmen og booter opp på nytt, eller hvis selve server-prosessen krasjer, vil Docker automatisk spinne opp MediaMTX-containeren. Den kobler seg da direkte til kameragrensesnittet (`/dev/video0`) i bakgrunnen.

Dette grepet forvandlet Pi 4-en fra et midlertidig testoppsett til en robust plug and plat enhet, som kontinuerlig pumper videostrømmen over til hovedserveren (Pi 5) uansett hvor mange ganger man trekker ut strømkabelen under felttesting.