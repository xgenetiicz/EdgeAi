import os
import time
import cv2 # for tegning og bildebehandling slik at vi viser visuelt hva som blir identifisert!
import numpy as np # Dette er for bildematriser
from ultralytics import YOLO # AI - motoren som gjør Object identifisering
#   import easyocr # Skiltleseren
import pytesseract  #prøver ut ny motor for skiltlesing.
import traceback # Henter ut nøyaktig feilmelding ved krasj
import re # NYTT: Importerer regex for å fiske ut norske skilt fra tekststøyen

RTSP_PORT = os.getenv("RTSP_PORT") # Porten for RTSP-strømmen, legger frem her for forståelse av at dette ligger i .env
RTSP_STREAM_BASE = os.getenv("RTSP_STREAM_URL") 
RTSP_STREAM_URL = f"{RTSP_STREAM_BASE}:{RTSP_PORT}/bil" # RTSP URL for streaming med porten fra .env.

#Har satt opp Tailscale der rasperry pi 4 og pi 5 snakker sammen og bruker Tailscale IP-adresser for å kommunisere. Dette gjør at vi kan sende bilder fra pi 4 til pi 5
# uten å bekymre oss for nettverkskonfigurasjon, 
# og det gir en stabil og sikker forbindelse mellom enhetene, dette er for å unngå ulike subnett og slikt.

# --- RIKTIG_PATH FOR SSD ---
# /media/genetiicz/storage/bil/bilder:/bilder 
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
print("Initialiserer 'hjernen' (YOLOv8 + Tesseract)",flush=True)

# Vi bruker 'modeller/best.pt' for å matche volum-mappingen i docker-compose
model = YOLO("modeller/best.pt") # Bruker den trenede modellen som ligger i samme mappe. Sørg for at "best.pt" er der før oppstart. skal ligge på /media/genetiicz/pathtossd/modeller/best.pt
print("Systemet er nå klart for å identifisere skilt.", flush=True)

# Liste over objekter som skal trigge på lagring
TARGET_OBJECTS = ["car", "license plate"] # "license plate" er nøkkelen for oppgaven - den skal trigger ocr lesingen (ikke bilen).

#vi setter variabler for oppførsel slik at kameraet ikke analyserer 60 bilder i sekundet -  bare når klassene dukker opp.
frame_counter = 0 
ocr_count = 0

#Vi lager en Videocapture objekt for å hente RTSP-strømmen fra pi 4, 
#og vi bruker OpenCV for å håndtere videostrømmen.
cap = cv2.VideoCapture(RTSP_STREAM_URL)

#Hvis den ikke funker
if not cap.isOpened():
    print(f"Feil: Klarte ikke å hente ut RTSP-strømmen fra {RTSP_STREAM_URL}.\nSjekk loggene i stacken på portainer på pi 4 for detaljer.", flush=True)
    
    #Vi fortsetter som videre hvis det funker -> neste er logikk for å hente bilder og sende til yolov8/best.pt modellen.
else:
    print(f"RTSP-strømmen fungerer, henter video fra {RTSP_STREAM_URL}", flush=True)

#Må sette en uendelig løkke slik at scriptet holder seg i live for å gjøre bildelogikken.
try:
    while True:
        ret, frame = cap.read()

        frame_counter += 1

        if not ret:
            print("Mistet forbindelsen til rtsp - strømmen, prøver å gjennoprette streamen om 5 sekunder.", flush=True)
            time.sleep(5)
            cap = cv2.VideoCapture(RTSP_STREAM_URL)
            continue

        #Vi sjekker ai for hvert 10 bilde siden dette er 60 fps. 
        if frame_counter % 6 == 0:

            #vi identifiserer hva modellen fant
            results = model(frame, verbose=False, conf=0.7) 
            annotated_frame = results[0].plot() #Tegner bb automatisk 

            found_classes = set()
            car_box = None
            plate_box = None

            for r in results:
                for box in r.boxes:
                    name = model.names[int(box.cls[0])] 
                    found_classes.add(name)

                    #Lagre koordinator hvis klassene blir funnet:
                    if name == "car":
                        car_box = box.xyxy[0].tolist()
                    elif name == "license plate":
                        plate_box = box.xyxy[0].tolist()
            
            timestamp = int(time.time())

            # Sjekker om vi fant bil eller skilt
            if any(obj in TARGET_OBJECTS for obj in found_classes):
                
                image_to_read = None
                
                # LOGIKK: Klipp ut (crop) det vi fant før vi sender det til EasyOCR
                if plate_box:
                    # AI fant skiltet! Vi klipper ut bare skiltet.
                    x1, y1, x2, y2 = map(int, plate_box)
                    
                    # NY LOGIKK: Legg til padding (luft) rundt skiltet for at OCR skal klare å lese grensene
                    pad = 15
                    x1 = max(0, x1 - pad)
                    y1 = max(0, y1 - pad)
                    x2 = min(frame.shape[1], x2 + pad)
                    y2 = min(frame.shape[0], y2 + pad)
                    
                    image_to_read = frame[y1:y2, x1:x2]
                    print(f"[{time.strftime('%H:%M:%S')}] Skilt detektert! Skanner skiltet ->", flush=True)

                elif car_box:
                    # AI fant bare bilen. Vi klipper ut bilen og leter etter tekst på den.
                    x1, y1, x2, y2 = map(int, car_box)
                    image_to_read = frame[y1:y2, x1:x2]
                    print(f"[{time.strftime('%H:%M:%S')}] Bil detektert! Skanner bilen for skilt ->", flush=True)

                # Kjører EasyOCR BARE på det utklipte bildet - dette er for å spare
                if image_to_read is not None and image_to_read.size > 0:

                    #Testing with convertion
                    gray = cv2.cvtColor(image_to_read, cv2.COLOR_BGR2GRAY)

                    #fjerner alt som ikker er beksvart skrift. en gråskala kan inneholde 256 nyanser av grått - og NO ønske vi å gjøre det helt hvitt med bakgrunnen fordi det
                    # det skaper støy til nå.
                    _, binary_image = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

                    #Tesseract config:
                    #--oem 3: standard ai motor
                    #--oem 7: tvinger tesseract for å se på bildet med EN linje med tekst.
                    #-c tessedit_char_whitelist= -> bare tillat tegnene fra allowlist under på variabelen tesseract_result.
                    tesseract_config= r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

                    # vi forteller at resultatet skal inneholde config linjen med allowlist.
                    ocr_text =pytesseract.image_to_string(binary_image, config=tesseract_config)
                else:
                    ocr_text= ""

                skilt_lest = False
                
                # vi må endre logikk slik at tesseract forstår hvordan den skal lese skiltet
                if ocr_text:
                    # Noen ganger leser OCR skiltet i to deler (f.eks "SU" og "92254"). 
                    # Her slår vi sammen all tekst den fant i bildet til en streng.
                    samlet_tekst = ocr_text.replace(" ", "").replace("\n", "").upper()
                    
                    # Er nødt til å se hva easyOCR gjetter skiltnummeret siden den bommer hver gang.
                    print(f"LESING: Tesseract leser skiltnr som: '{samlet_tekst}' ", flush=True)
                    
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
                        time.sleep(3) # Cooldown så vi ikke tar flere bilder av samme bil
                
                # Hvis AI så bil, men OCR ikke klarte å lese teksten
                if not skilt_lest:
                    ocr_count += 1
                    print(f"Klarte ikke lese skilt godt nok. Forsøk {ocr_count}/5", flush=True)
                    
                    if ocr_count >= 5:
                        print("FEIL: Bil oppdaget 5 ganger på rad, men helt umulig å lese skiltet tydelig.", flush=True)
                        save_path = os.path.join(DETECTION_PATH, f"feilet_lesing_{timestamp}.jpg")
                        cv2.imwrite(save_path, annotated_frame)
                        ocr_count = 0 
                        time.sleep(3) # Cooldown før vi leter etter neste bil
            
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