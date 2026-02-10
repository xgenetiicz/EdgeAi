# Dokumentasjon: Dataflyt & Backend

Denne økten fokuserte på å gjøre systemet operativt ved å koble skiltgjenkjenningen mot **Statens Vegvesen sine offentlige API-er**. Utviklingen ble primært gjennomført i **Node-RED**, med særlig vekt på kompleks databehandling, rekursiv logikk og visualisering.

### 1. Integrasjon mot Statens Vegvesen (Kjøretøyopplysninger)
Systemet benytter tjenesten "Enkeltoppslag" for å hente tekniske kjøretøydata basert på kjennemerke. Dette har blitt bestilt som privatperson på Genti Rudi slik at vi har tilgang til API - uten visning av eierskap på bil, men bare kjøretøyopplysninger.
<ul>
  <li>**Teknisk implementering:** Utvikling av GET-forespørsler mot endepunktet spesifisert i Swagger-dokumentasjonen: `https://akfell-datautlevering.atlas.vegvesen.no/swagger-ui/index.html?configUrl=/v3/api-docs/swagger-config#/enkelt-oppslag-resource/hentKjoretoydata`.</li>
  <li>**Sikker autentisering:** Oppsett av HTTP-headere (`SVV-Authorization`) der API-nøkkelen hentes dynamisk fra miljøvariabler (`SVV_API_KEY`) for å sikre legitimasjon og unngå hardkoding i kildekoden.</li>
  <li>**Pre-prosessering av inndata:** Implementering av logikk som automatisk renser inkommende skiltnummer ved å fjerne mellomrom og tvinge store bokstaver før forespørselen sendes til API-et.</li>
</ul>

### 2. "DeepFind"-algoritmen (Avansert databehandling)
Som følge av at API-responsen returnerer komplekse og dypt nøstede JSON-strukturer, ble det utviklet skreddersydd JavaScript-logikk for robust databehandling:
<ul>
  <li>**Rekursivt søk:** Implementering av funksjonen `deepFind(obj, key)` som traverserer hele JSON-treet rekursivt for å lokalisere spesifikke datafelt (som `fabrikantnavn` eller `kontrollfrist`) uavhengig av deres plassering i objektet.</li>
  <li>**Robust datauthenting:** Bruk av hjelpefunksjonen `pick()` for å håndtere inkonsekvenser i API-et, der datafelt kan returneres som enten enkeltobjekter eller lister (arrays).</li>
  <li>**Logikk for EU-kontroll:** Programmering av logikk som aggregerer alle tilgjengelige dato-felt for periodisk kjøretøykontroll og selekterer den mest relevante fristen for visning.</li>
</ul>

### 3. Visualisering og brukergrensesnitt (Dashboard)
Målet var å presentere komplekse data på en umiddelbar og forståelig måte for sluttbrukeren.
<ul>
  <li>**Responsivt design:** Konfigurering av Node-RED Dashboard med et layout som automatisk tilpasser seg ulike skjermstørrelser.</li>
  <li>**Dynamisk statusindikator:** Implementering av betinget styling (Vue.js-syntaks) som endrer bakgrunnsfarge og visuelt uttrykk basert på kjøretøyets EU-status (f.eks. rød farge ved utgått frist og grønn ved godkjent status).</li>
  <li>**Feilhåndtering:** Integrasjon av brukervennlige feilmeldinger i grensesnittet for situasjoner der API-et er utilgjengelig eller skiltnummeret ikke finnes i registeret.</li>
</ul>

### 4. Tekniske kilder og dokumentasjon
Utviklingen av integrasjonen er basert på offisielle spesifikasjoner fra Statens Vegvesen:
<ul>
  <li>**Swagger UI (Teknisk spesifikasjon):** `https://akfell-datautlevering.atlas.vegvesen.no/swagger-ui/index.html?configUrl=/v3/api-docs/swagger-config#/enkelt-oppslag-resource/hentKjoretoydata` – Benyttet for definisjon av datamodeller og endepunkter.</li>
  <li>**API-oversikt og bestilling:** `https://autosys-kjoretoy-api.atlas.vegvesen.no/api-ui/index-api.html?apiId=enkeltoppslag` – Benyttet for forståelse av tilgangsstyring og tjenesteinnhold.</li>
</ul>