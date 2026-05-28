# 14 - Cloudflare Zero Trust og Sikkerhet

## Oversikt

Ekstern tilgang til dashboardet og portstyring er sikret gjennom Cloudflare Tunnel og Zero Trust Access. Dette gjør at systemet ikke har åpne porter i det lokale nettverket — all trafikk går gjennom Cloudflare sin infrastruktur.

---

## Cloudflare Tunnel

Cloudflared kjører som en systemd-service på Raspberry Pi 5 og etablerer en utgående tunnel til Cloudflare. Caddy fungerer som revers-proxy bak tunnelen og ruter trafikk til riktig tjeneste.

```
Bruker → Cloudflare → Tunnel → Caddy → Node-RED
```

Ingen porter er eksponert direkte mot internett.

---

## Zero Trust Access — Dashboard

Dashboardet på `bachelor.gtztech.net` er beskyttet med en tilgangspolicy som krever autentisering via OTP-kode sendt til godkjent e-postadresser. E-postkontoene er i tillegg sikret med tofaktorautentisering.

Sesjonsvarighet er satt til 24 timer.

---

## Zero Trust Access — ESP32 Bypass

ESP32-enheten poller `/esp/status` automatisk hvert 2. sekund og kan ikke gjennomføre en OTP-innlogging. Dette endepunktet er derfor konfigurert med en egen Bypass-policy som tillater alle. Dette er forsvarlig fordi endepunktet kun returnerer `aapne` eller `lukke` som ren tekst - ingen sensitiv informasjon eksponeres, og derfor kunne man ha en bypass på Policy på den angitte URL slik at informasjonen kan hentes og gi videre input til bom.

---

## Tailscale

Kommunikasjonen mellom kameranoden (Pi 4) og prosesseringsnoden (Pi 5) skjer over Tailscale VPN. Dette gir en kryptert peer-to-peer-tunnel basert på WireGuard-protokollen, uten behov for portviderekobling eller åpne brannmurregler.

Tailscale er installert på alle enheter i systemet inkludert Pixel 10 Pro som ble brukt under USNExpo som kamerakilde under demonstrasjonen. Forklaringen av problemet som ble støtt på er dokumentert i ![15-Hardware-løsning.md](/Docs/15-Hardware-løsning.md)

---

## Privacy-by-design

All bildeanalyse skjer lokalt på Raspberry Pi 5. Rå bildedata forlater aldri enheten — kun avledet informasjon som skiltnummer og adgangsstatus sendes videre i systemet. Dette er et bevisst arkitekturvalg for å minimere personvernrisiko.