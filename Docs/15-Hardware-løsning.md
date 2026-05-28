# 15 - Hardware-krise og løsning: Fra Global Shutter til Pixel 10 Pro

## Hva skjedde

4 dager før demonstrasjon på USN Expo 2026 kortsluttet Global Shutter-kameraet koblet til Raspberry Pi 4. Kameraet var ikke lenger gjenkjent av systemet og det var ikke mulig å bestille et erstatningskamera i tide... 
Modulen ble svært varm under last - og ved en lang periode så sluttet denne å fungere til slutt etter ny stack pull, på grunn av kontinuerlig testing. Det var allerede nok problemer med Raspberry pi 4, samt holde videostrømmen oppe ettersom vi slet med stabil mbps strøm og i tillegg på hotspot. Hotspot er av den grunn at vi måtte ta hensyn til at vi skulle demonstrere en løsning som faktsk fungerer uavhengig hvor man er. 

```
ls /dev/video*
# /dev/video0 — ikke tilgjengelig
```

dmesg bekreftet at USB-enheten ikke svarte:

```
usb 1-1.4: device not accepting address, error -71
usb 1-1-port4: unable to enumerate USB device
```

---

## Løsningen

En Pixel 10 Pro med RTSP Server Pro-appen ble brukt som erstatningskamerakilde. RTSP Server Pro eksponerer en HTTP MJPEG-strøm.

Telefonen er koblet til samme Tailscale-nettverk som Pi 5, noe som gjør at strømmen er tilgjengelig over en kryptert tunnel uavhengig av lokalt nettverksoppsett. Det er derfor tailscale var så smart, fordi dette gjorde hele infrastrukturen bare så lett, der alle enhetene oppfører seg som om de er på samme subnett.

---

## Endringer i systemet

**`.env` på Pi 5:**
```
RTSP_STREAM_URL= -> riktig strøm url fra appen
RTSP_PORT = og riktig port nummer fra appen.
```

**`mottakerAvData.py`:**
Det måtte også endres basert på sti - ettersom første sti var basert på hva det var definert i mediamtx.yml -> og dette var ikke lenger i bruk siden kameranoden kortsluttet.

```python
# Tidligere (Pi 4 + MediaMTX):
RTSP_STREAM_URL = f"{RTSP_STREAM_BASE}:{RTSP_PORT}/bil"

# Nå (Pixel 10 Pro + RTSP Server Pro):
RTSP_STREAM_URL = f"{RTSP_STREAM_BASE}:{RTSP_PORT}/video"
```

---

## Resultat

Systemet ble testet to dager før demonstrasjonen og det fungerte. Det fungerte også stabilt under demonstrasjonen med Pixel 10 Pro som kamerakilde. Bilskilt ble korrekt detektert og lest, og hele kjeden fra kamera til beslutning fungerte som forventet.

Dette viser at arkitekturen er fleksibel nok til å bytte kamerakilde uten endringer i resten av systemet.