# 06 - Object Identification & AI Inference

Denne modulen beskriver "hjernen" i systemet, som er ansvarlig for å transformere rå bilde-bytes fra ESP32-CAM til meningsfylt informasjon og visuelle bevis.

## Arkitektur og Flyt

Systemet benytter en **Edge AI**-tilnærming der all tung prosessering skjer lokalt på en Raspberry Pi 5 (16GB RAM). Dette eliminerer behovet for sky-tjenester, reduserer latenstid og sikrer personvern ved at data ikke forlater det lokale nettverket.



### Prosesseringspipelinen
1.  **Mottak:** Flask-API-et mottar Base64-kodet data fra ESP32-CAM.
2.  **Dekoding:** Data konverteres til en NumPy-matrise ved bruk av `cv2.imdecode`. Dette sikrer at vi jobber med et ekte bildeformat i minnet og fungerer som en barriere mot korrupte data.
3.  **Inferens (YOLOv8):** Bildet sendes gjennom YOLOv8-modellen for å identifisere objekter definert i `TARGET_OBJECTS`. *Dette skal endres senere – men akkurat nå er vi i en testfase hvor vi ønsker at den skal identifisere flere objekter (som person, mobil, etc.) enn bare bil for å verifisere modellens nøyaktighet.*
4.  **Annotering:** Ved funn brukes `.plot()`-funksjonen til å tegne "Bounding Boxes" og labels helt automatisk på bildet. Dette gir et umiddelbart visuelt bevis på at identifikasjonen fungerer korrekt.
5.  **OCR (EasyOCR):** Hvis et kjøretøy detekteres ("car" eller "truck"), kjøres EasyOCR for å identifisere registreringsnummeret med en satt sikkerhetsterskel (Confidence > 0.5).
6.  **Lagring:** Det ferdige bildet lagres direkte på systemets **2TB NVMe SSD**. Dette gjøres via en **Docker Bind Mount**, slik at dataene skrives fysisk til SSD-en og ikke blir liggende i containerens flyktige lagringsplass.

## Teknisk Implementering

### Automatisk Visualisering
Tidligere krevde tegning av rammer manuell beregning av koordinater ($x_1, y_1, x_2, y_2$). Ved å implementere `results[0].plot()`, har vi automatisert denne prosessen:

## Refleksjonsnotat: Modelloptimalisering

Gjennom utviklingen ble systemet testet med tre iterasjoner av YOLOv8 for å finne balansen mellom ytelse og nøyaktighet med tanke på ytelsen til kameraet (esp32):

* **YOLOv8-Nano:** Forkastet grunnet lav konfidens mellom 25 % og 55 %. 
* **YOLOv8-Nano (Feil):** Modellen produserte hyppige feilklassifiseringer som "umbrella" eller "suitcase".
* **YOLOv8-Medium:** Viste forbedring med treffsikkerhet opptil 90 % på enkelte objekter. 
* **YOLOv8-Medium (Instabilitet):** Slet med stabilitet og forveksling mellom objekter som "remote" og "keyboard" under krevende forhold.
* **YOLOv8-XL:** Implementert som endelig løsning ved utnyttelse av Raspberry Pi 5 med 16 GB RAM. 
* **YOLOv8-XL (Ytelse):** Leverer stabil presisjon over 90 % for kritiske objekter og 93 % for personidentifikasjon.

**Konklusjon:** Kombinasjonen av XL-modell og en konfidensterskel på 0.7 eliminerer usikker gjetting og sikrer pålitelige visuelle bevis - men i bunn og grunn så er det ikke AI modellen som er avviket, men kameraet (esp32). Det er for dårlig oppløsning, og med en slik oppløsning så kan dette resultere i feil for hovedfunksjonen til å faktisk identifisere bil og skiltnummer. Kort og presist så er flaskehalsen oppløsning og sensorstøy.
```python
# Automatisk tegning av bokser og navn basert på AI-ens funn
# Dette fjerner behovet for manuell piksel-manipulasjon.
annotated_frame = results[0].plot()