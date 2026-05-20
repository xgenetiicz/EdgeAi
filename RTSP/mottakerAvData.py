import os
import torch #for cuda.
import time
import cv2 # for tegning og bildebehandling slik at vi viser visuelt hva som blir identifisert!
import numpy as np # Dette er for bildematriser
from ultralytics import YOLO # AI - motoren som gjør Object identifisering
import easyocr # Skiltleseren
import traceback # Henter ut nøyaktig feilmelding ved krasj
import re # NYTT: Importerer regex for å fiske ut norske skilt fra tekststøyen

RTSP_PORT = os.getenv("RTSP_PORT") # Porten for RTSP-strømmen, legger frem her for forståelse av at dette ligger i .env
RTSP_STREAM_BASE = os.getenv("RTSP_STREAM_URL") 

###STORE ENDRINGER, FOR Å FÅ DETTE TIL Å FUNKE PÅ DEMONSTRASJONEN SÅ BLIR DET BRUKT EN PIXEL 10 FREMOVER.
### VIDEO STREAMINGEN PÅ PI 4 KORTSLUTTET, SELVE KAMERAENHETEN OG BESTILLNG AV NYTT KAMERA NÅR IKKE FREM TIL DAGEN
### VI SKAL DEMONSTRERE DETTE PÅ EN PIXEL 10, SLIK AT VI FORTSATT KAN VISE FUNKSJONALITETEN AV SYSTEMET.

#RTSP_STREAM_URL = f"{RTSP_STREAM_BASE}:{RTSP_PORT}/bil"  --> dette var den originale RTSP URL-en for streaming fra Rasppberry Pi 4.

RTSP_STREAM_URL = f"{RTSP_STREAM_BASE}:{RTSP_PORT}/video" # RTSP URL for streaming med porten fra .env. 

#Har satt opp Tailscale der rasperry pi 4 og pi 5 snakker sammen og bruker Tailscale IP-adresser for å kommunisere. Dette gjør at vi kan sende bilder fra pi 4 til pi 5
# uten å bekymre oss for nettverkskonfigurasjon, 
# og det gir en stabil og sikker forbindelse mellom enhetene, dette er for å unngå ulike subnett og slikt.

BASE_PATH = "/bilder"
TRAIN_PATH = os.path.join(BASE_PATH, "roboflow") # Rå-bilder for læring
DETECTION_PATH = os.path.join(BASE_PATH, "deteksjoner") # Ferdige bilder
CAR_PATH = os.path.join(BASE_PATH, "bil") # Spesifikk for bil-test
LOG_FILE = os.path.join(BASE_PATH, "error_log.txt") # Her lagres 500-feilmeldingen

# Sikrer at mappen eksisterer på SSD før vi lagrer til serveren.
for path in [TRAIN_PATH, DETECTION_PATH, CAR_PATH]:
    if not os.path.exists(path):
        os.makedirs(path)

# AI - modell oppstart på RAM ved oppstart på Raspberry pi 5
print("Initialiserer 'hjernen' (YOLOv8 + OCR)", flush=True)

# Vi bruker 'modeller/best.pt' for å matche volum-mappingen i docker-compose
model = YOLO("modeller/best.pt") # Bruker den trenede modellen som ligger i samme mappe. Sørg for at "best.pt" er der før oppstart. skal ligge på /media/genetiicz/pathtossd/modeller/best.pt
model.to('cuda') # Flytter modellen til GPU for raskere inferens.

reader = easyocr.Reader(['en'], gpu=True) #Gjør en endring her - setter den til True slik at den bruker GPU.
if torch.cuda.is_available(): # Sjekker om EasyOCR faktisk bruker GPU, og gir tilbakemelding i loggen.
    print("EasyOCR er initialisert med GPU-støtte for raskere skiltlesing.", flush=True)
else: 
    print("Advarsel: EasyOCR kunne ikke initialiseres med GPU-støtte. EasyOCR går på CPU og Torch funker ikke", flush=True)
    
# Liste over objekter som skal trigge på lagring
TARGET_OBJECTS = ["car", "license plate"] # "license plate" er nøkkelen for oppgaven - den skal trigger ocr lesingen (ikke bilen).

#vi setter variabler for oppførsel slik at kameraet ikke analyserer 60 bilder i sekundet -  bare når klassene dukker opp.
frame_counter = 0 
ocr_count = 0

#Vi lager en Videocapture objekt for å hente RTSP-strømmen fra pi 4, 
#og vi bruker OpenCV for å håndtere videostrømmen.
cap = cv2.VideoCapture(RTSP_STREAM_URL)

# Reduserer bufferstørrelsen for å minimere forsinkelse og sikre at vi alltid analyserer det nyeste bildet fra kameraet.
# Etter gjentatte tester, ser man at bufferen bygger seg opp og tar opp minne - og den analyserer ikke det ferskeste bildet.
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) 

#Hvis den ikke funker
if not cap.isOpened():
    print(f"Feil: Klarte ikke å hente ut RTSP-strømmen fra {RTSP_STREAM_URL}.\nSjekk loggene i stacken på portainer på pi 4 for detaljer.", flush=True)
    
    #Vi fortsetter som videre hvis det funker -> neste er logikk for å hente bilder og sende til yolov8/best.pt modellen.
else:
    print(f"RTSP-strømmen fungerer, henter video fra {RTSP_STREAM_URL}", flush=True)

#Må sette en uendelig løkke slik at scriptet holder seg i live for å gjøre bildelogikken.
cooldown_until = 0 
try:
    while True:
        # Tving OpenCV til å hoppe over alle bildene som ligger i køen
        # slik at vi alltid analyserer det nyeste bildet fra kameraet
        ret, frame = cap.read() # Hent det ferskeste bildet

        if not ret:
            print("Mistet forbindelsen til rtsp - strømmen, prøver å gjennoprette stream.", flush=True)
            for sekund in range(5,0, -1):
                print(f"Streamen gjenopprettes om {sekund} sekunder")
                time.sleep(1)

            print(f"Streamen tilkobles på nytt nå!", flush=True)
            cap = cv2.VideoCapture(RTSP_STREAM_URL)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Reduser bufferstørrelsen igjen etter gjenoppretting
            continue
        
        #Sjekker for bildetap siden dette viste seg i loggen på portainer
        if frame is None or frame.size == 0: #sjekker om bildet er er lik 0 eller faktisk null.
            print("Mottok en korrupt datapakke eller korrupt databilde fra strømmen, hopper over bildet.", flush=True) 
            continue

        frame_counter += 1

        if time.time() < cooldown_until: # Hvis vi er i cooldown, hopper vi over resten av logikken og fortsetter til neste bilde
            continue        

        #Vi analyserer hvert 3. bilde for å redusere belastningen på CPU.
        if frame_counter % 3 == 0:

            #vi identifiserer hva modellen fant
            results = model(frame, verbose=False, conf=0.7, device=0) #conf er konfidensgrensen. Slik at modellen må være 70% sikker på at det den ser er en bil eller et skilt før den tegner bb og sender det til ocr. 
            annotated_frame = results[0].plot() #Tegner bb automatisk 

            found_classes = set() # for å holde styr på hvilke klasser vi har funnet i bildet, set () er for unike verdier slik det ikke oppstår duplikater.
            car_box = None # Vi starter med None fordi vi ikke har funnet noen enda
            plate_box = None # Når vi finner bil eller skilt - så vil objektet lagres i disse variablene til deres respektive klasse som er fra TARGET_OBJECTS listen.

            for r in results: # Det kan være flere resultater i samme bilde, så vi må iterere gjennom alle resultatene for å se hva vi har funnet.
                for box in r.boxes: # for hver boks som modellen har tegnet rundt det den fant, så sjekker vi hva det er.
                    name = model.names[int(box.cls[0])]  #henter navnet ved å legge det inn i en ny variabel som er "name" for å vise resultatet neste linje.
                    found_classes.add(name) # resultatet vises her og det er lettere å lese dette som "name" variabel.

                    #Lagre koordinator hvis klassene blir funnet: - dette er selvforklarende etter løkken vi implementerte for å sjekke hva modellen fant av bilder/resultater
                    if name == "car":
                        car_box = box.xyxy[0].tolist() #tegn xyxy koordinater
                    elif name == "license plate": 
                        plate_box = box.xyxy[0].tolist() #tegn xyxy koordinater
            
            timestamp = int(time.time()) #bruker timestamp for å lagre bilder med unike navn, dette er viktig for å unngå overskriving av bilder og for å kunne spore når bildene ble tatt.

            # Sjekker om vi fant bil eller skilt
            if any(obj in TARGET_OBJECTS for obj in found_classes): # vi sjekker for hvilke klasser vi fant i bildet, og hvis noen av det er i TARGET_OBJECTS arrayet
            # så kjører vi en løkke i target objects for hver objekt og itererer gjennom arrayet for å se hva vi fant av bilder i found_classes som er resultatet av boksene den har tegnet.
                
                image_to_read = None # setter denne som null og tar dette i bruk senere ved å klippe ut selve bildet vi fant.
                
                # LOGIKK: Klipp ut (crop) det vi fant før vi sender det til EasyOCR - vi sjekker først for license plate alltid ettersom dette er 
                # det kritiske funksjonelle kravet for prosjektet -  uten skilt får vi ingen lagring eller videre logikk.

                #Pad må bli definert før statements går gjennom.
                 
                pad = 15 # for nå er det bra, men ved flere tester og skalering må dette justeres.    
                if plate_box:
                    # Vi mapper koordinatene til listen plate_box (DETTE ER KOORDINATER FRA if name == "license plate") og gjør dem alle desimaltall til heltall ved å sette dem til int.
                    # fordi det er fire uavhengige literaler for hver iterasjon av løkken, der hver x og y akse representer variabelen ulikt fordi bilen er i fart - og da endrer matten seg over 
                    # tid på grunn av hastighet og bevegelse. 
                    x1, y1, x2, y2 = map(int, plate_box)

                    #Vil også se hvilke koordinater best.pt fant og hva den tegner i bildet. Fint å ha hvis det ikke finner skiltet, og da kan vi se om
                    # den tegner feil.
                    print(f"best.pt fant skiltet og tegnet en boks med koordinater: {x1}, {y1}, {x2}, {y2}", flush=True)
                    
                    # Vi har satt til padding rundt skiltet og bokstavene for å hjelpe EasyOCR me d å lese skiltet bedre, og se tydeligere forskjell mellom bokstavene og tallene.
                    x1 = max(0, x1 - pad) # vi forteller at x1 og y1 er minimum 0 slik at vi ikke klipper utenfor - fordi det gir feil.
                    y1 = max(0, y1 - pad) # på grunn av x1 er venstre side av bildet og y1 er toppen av bildet, så må vi sørge for at vi ikke går under 0 når vi legger til padding.
                    x2 = min(frame.shape[1], x2 + pad)
                    y2 = min(frame.shape[0], y2 + pad)
                    
                    image_to_read = frame[y1:y2, x1:x2] # image_to_read inneholder koordinatene nå til det utklipte bildet av skiltet gjennom koordinater.
                    print(f"[{time.strftime('%H:%M:%S')}] Skilt detektert! Skanner skiltet ->", flush=True) # vi printer ut at vi har funnet skiltet og sender videre til EasyOCR.

                elif car_box: # Hvis den finner bilen først så er det fortsatt verdt å prøve å lese skiltet, så vi klipper ut bilen og sender det til EasyOCR for å se om den klarer å finne skiltet der.
                    # Vi mapper koordinatene til listen car_box (DETTE ER KOORDINATER FRA if name == "car") og gjør dem alle desimaltall til heltall ved å sette dem til int.
                    # fordi det er fire uavhengige literaler for hver iterasjon av løkken, der hver x og y akse representer variabelen ulikt fordi bilen er i fart - og da endrer matten seg over 
                    # tid på grunn av hastighet og bevegelse. (hentet fra plate_box logikken).
                    x1, y1, x2, y2 = map(int, car_box)

                    x1 = max(0, x1 - pad) # vi forteller at x1 og y1 er minimum 0 slik at vi ikke klipper utenfor - fordi det gir feil.
                    y1 = max(0, y1 - pad) # på grunn av x1 er venstre side av bildet og y1 er toppen av bildet, så må vi sørge for at vi ikke går under 0 når vi legger til padding.
                    x2 = min(frame.shape[1], x2 + pad)
                    y2 = min(frame.shape[0], y2 + pad)

                    #initialiserer variabelen image_to_read siden vi har et utklipt bilde nå basert på hvilket objekt den fant først -> men sluttresultate vil alltid være license_plate
                    # Ellers vil denne kaste en feilmelding senere når vi sender den til EasyOCR - da vil den si at den ikke kan lese tekten av det utklipte bildet.
                    image_to_read = frame[y1:y2, x1:x2] #Her klipper det bildet vi har fått koordinater på og paddet ferdig.
                    print(f"[{time.strftime('%H:%M:%S')}] Bil detektert! Skanner bilen for skilt ->", flush=True)

                # Kjører EasyOCR BARE på det utklipte bildet - dette er gjort for å forbedre lesingen samt optimalisere den.
                if image_to_read is not None and image_to_read.size > 0: # må være større enn 0 for da vet vi at det ligger et bilde med tall som kan leses - og som ikke er None eller null.

                    #-- VI TAR MED BILDEVASKINGEN FRA TESSERACT BRANCHEN SLIK AT VI TESTER DET MED EASYOCR---

                    #vi tester med å forstørre bildet som fungerer bra ved test med tesseract
                    image_to_read = cv2.resize(image_to_read, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
                    gray= cv2.cvtColor(image_to_read, cv2.COLOR_BGR2GRAY)

                    _, binary_image = cv2.threshold(gray, 130, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

                    #prøver dilation fra tesseract branchen igjen... "fylle hullene med bleksvart"
                    inverted= cv2.bitwise_not(binary_image)
                    kernel=np.ones((3,3), np.uint8)
                    dilated = cv2.dilate(inverted, kernel, iterations=1)
                    final_image = cv2.bitwise_not(dilated)
                    
                    # allowlist tvinger EasyOCR til å bare gjette på STUB og TALL, ikke flagg og småbokstaver
                    ocr_result = reader.readtext(final_image, allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', detail=0, paragraph=False)
                else:
                    ocr_result = []

                skilt_lest = False
                
                # vi må endre logikk slik at easyocr forstår hvordan den skal lese skiltet
                if ocr_result:
                    # Noen ganger leser OCR skiltet i to deler (f.eks "SU" og "92254"). 
                    # Her slår vi sammen all tekst den fant i bildet til en streng.
                    samlet_tekst = "".join(ocr_result).replace(" ", "").upper()
                    
                    # Er nødt til å se hva easyOCR gjetter skiltnummeret siden den bommer av og til.
                    print(f"---DEBUGGING: EASYOCR GJETTET SKILTNR SOM: '{samlet_tekst}' ", flush=True)
                    
                    # Regex leter etter nøyaktig 2 bokstaver og 5 tall i den samlede teksten.
                    match = re.search(r'[A-Z]{2}[0-9]{5}', samlet_tekst) # denne er superviktig.
                    
                    if match:
                        plate_text = match.group(0) # Dette blir det rene, norske skiltnummeret
                        cv2.putText(annotated_frame, f"SKILT: {plate_text}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                        
                        #plate_text lagrer filen med riktig skiltnummer til bilen slik at vi har riktig bilde med riktig skiltnummer
                        save_path = os.path.join(CAR_PATH, f"{plate_text}_{timestamp}.jpg")
                        cv2.imwrite(save_path, annotated_frame)
                        print(f"SUKSESS! Leste skilt: {plate_text}.", flush=True)
                        
                        skilt_lest = True
                        ocr_count = 0 
                        cooldown_until = time.time() + 3 # Cooldown så vi ikke tar flere bilder av samme bil
                
                # Hvis AI så bil, men OCR ikke klarte å lese teksten
                if not skilt_lest:
                    ocr_count += 1
                    print(f"Klarte ikke lese skilt godt nok. Forsøk {ocr_count}/5", flush=True)
                    
                    if ocr_count >= 5:
                        print("FEIL: Bil oppdaget 5 ganger på rad, men helt umulig å lese skiltet tydelig.", flush=True)
                        save_path = os.path.join(DETECTION_PATH, f"feilet_lesing_{timestamp}.jpg")
                        cv2.imwrite(save_path, annotated_frame)
                        ocr_count = 0 
                        cooldown_until = time.time() + 3 # Cooldown før vi leter etter neste bil
            
            # Rydder opp telleren hvis bilen forsvinner
            else:
                ocr_count = 0

except KeyboardInterrupt:
    print("Scriptet ble stoppet manuelt.")
except Exception as e:
    error_msg = traceback.format_exc()
    print(f"SCRIPTET HAR KRÆSJET HELT, SJEKK EXCEPTION!!\n{error_msg}", flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"\n--- [{time.strftime('%Y-%m-%d %H:%M:%S')}] ---\n{error_msg}\n")
finally:
    # Rydder opp strømmen ordentlig når scriptet krasjer/lukkes
    cap.release()
    cv2.destroyAllWindows()