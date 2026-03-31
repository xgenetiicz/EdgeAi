# Endring av Flask Server til RTSP-stream server & Tailscale

## Script & Nettverks endringer
* **Flask Server:** Til nå så har det vært et flask server som hadde et port åpent der den kunne ta i mot stillbilder med esp32. Der dette ble tatt i mot gjennom en tunnel ved bruk av cloudflare som nådde til Raspberry pi 5.
* **Tailscale:** Tailscale ble den nye løsningen når det gjelder kommunikasjon mellom enhetene - og denne løsningen gjorde ting enkelt.
* **RTSP Stream:** Scriptet -> [mottakerAvData.py](/RTSP/mottakerAvData.py) ble endret og konfigurert til å fungere som en RTSP-strøm, der logikken måtte også endres siden nå så måtte bildene bli tatt fra en videostrøm så dette er da enkeltbilder fra sanntidsstrømmen - der dette ikke er stillbilder lenger.
