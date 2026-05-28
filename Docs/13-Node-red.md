
# 13 - Node-RED: Dashboard, Logikkflyt og Portstyring
 
## Oversikt
 
Node-RED fungerer som systemets sentrale logikkmotor. Det er her AI-resultatene kobles sammen med kjøretøydata fra Statens Vegvesen, reservasjonslogikk og fysisk portstyring via ESP32.
 
Flyten er lineær og HTTP-basert. MQTT ble vurdert men forkastet — filbasert flyt ga bedre kontroll og enklere feilsøking uten å legge til unødvendig kompleksitet -  istedenfor leser den direkte fra filstien.
 
---
 
## Hovedflyt
 
Systemet leser filnavnet på siste bilde lagret i `/bilder/bil/`. Filnavnet følger formatet `{SKILT}_{timestamp}.jpg`. Skiltnummeret normaliseres, slås opp mot Statens Vegvesen sitt Autosys-API, og sammenlignes mot reservasjonslisten. Resultatet oppdaterer dashboardet og setter bomstatus.
 
En rekursiv `deepFind`-funksjon traverserer API-responsen uavhengig av JSON-struktur - dette var nødvendig fordi Autosys returnerer data i varierende nøstede strukturer avhengig av kjøretøytype.
 
---
 
## Dashboard
 
Dashbord har tre sider:
 
- **Kjøretøydata** — viser skannet skilt, merke, modell, første registrering, neste EU-kontroll og adgangsstatus (Godkjent / Avslått)

![Kjøretøydata](/Docs/NodeRedBilder/Kjøretøydata.png) && ![test](/Docs/NodeRedBilder/test.png)
Dette viser illustrasjoner til hvordan dette fungerer visuelt messig, der det også foreligger testbilder med miniatyrbiler.


- **Reserver bil** — operatøren legger inn skiltnummer som skal ha adgang
![reserver](/Docs/NodeRedBilder/reserver.png)
Dette viser hvordan reservasjonen fungerer og ser ut.

- **Bilhistorikk** — kronologisk logg over alle passeringer med tidspunkt og adgangsstatus
![historikk](/Docs/NodeRedBilder/historikk.png)
Slik ser bilhistorikken ut etter følgende tester.

Nettsiden er ikke tilgjengelig basert på at dette er en stack som kjøres, og ettersom dette ikke er til daglig bruk som blir stacken satt på pause. Linken til siden er: `https://bachelor.gtztech.net/dashboard/` - men dette er satt opp med Cloudflare Zero Trust med OTP verifisering slik at sikkerheten er på plass.

---
 
## ESP32-endepunkt
 
```
GET /esp/status
```
 
ESP32 poller dette endepunktet hvert 2. sekund og mottar enten `aapne` eller `lukke`. Dette er lagt til ved en URL i Arduino hvor denne puller på status hentet fra angitt URL i koden.
