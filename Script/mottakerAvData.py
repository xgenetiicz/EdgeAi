from flask import Flask, request # Flask må ha stor F for å virke
import base64 # dekoder bilder i tekst
import os
import time
import cv2 # for tegning og bildebehandling slik at vi viser visuelt hva som blir identifisert!
import numpy as np # Dette er for bildematriser
from ultralytics import YOLO # AI - motoren som gjør Object identifisering
import easyocr # Skiltleseren
import traceback # Henter ut nøyaktig feilmelding ved krasj

app = Flask(__name__)

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
print("Initialiserer 'hjernen' (YOLOv8 + OCR)", flush=True)
# Vi bruker 'modeller/best.pt' for å matche volum-mappingen i docker-compose
model = YOLO("modeller/best.pt") # Bruker den trenede modellen som ligger i samme mappe. Sørg for at "best.pt" er der før oppstart.
reader = easyocr.Reader(['en'], gpu=False)
print("Systemet er nå klart for identifisere skilt.", flush=True)

# Liste over objekter som skal trigge på lagring
TARGET_OBJECTS = ["car", "license plate"] # "license plate" er nøkkelen for oppgaven - den skal trigger ocr lesingen (ikke bilen).

@app.route('/upload-bilde', methods=['POST'])
def upload():
    # Tidspunkt for å logge prosesseringstid
    start_time = time.time()
    print(f"\n--- [{time.strftime('%H:%M:%S')}] Forespørsel mottatt ---", flush=True)
    
    try:
        # hente ut tekstrengen til base64 og dekode til bilde-bytes
        base64_data = request.data.decode('utf-8')
        image_bytes = base64.b64decode(base64_data)

        # Konverterer bytes til bildeformat som AI kan lese
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Bilde-dekoding feilet (NoneType). Sjekk om dataen er korrupt.")

        timestamp = int(time.time())
        
        # LAGRE RÅ-BILDE 
        cv2.imwrite(os.path.join(TRAIN_PATH, f"raw_{timestamp}.jpg"), img)

        # AI IDENTIFISERING 
        # Setter den på 0.5 for å få deteksjoner som kan brukes til ekperimentering, kan tas ned ved behov.
        valgt_conf = 0.5
        results = model(img, verbose=False, conf=valgt_conf) 
        
        # Henter ut informasjon for logging og sjekking
        detections_for_log = []
        found_targets = []
        
        for r in results:
            for box in r.boxes:
                name = model.names[int(box.cls[0])] # Henter hele navnet, f.eks "cell phone"
                conf = float(box.conf[0])
                detections_for_log.append(f"{name} ({conf:.2f})")
                
                # Sjekker om objektet er i listen vår (uten å splitte navnet)
                if name in TARGET_OBJECTS:
                    found_targets.append(name)
        
        if detections_for_log:
            print(f"AI-en ser: {', '.join(detections_for_log)}", flush=True)
        else:
            print("AI-en ser absolutt ingen objekter.", flush=True)

        # LAGRE DETEKSJON (Hvis vi fant et mål-objekt)
        if found_targets:
            # Vi fjerner duplikater i loggen for ryddighet
            unique_targets = list(set(found_targets))
            print(f"TREFF: Fant {unique_targets}. Starter bildebehandling.", flush=True)
            
            # .plot() tegner bokser. Vi bruker standardinstillingen for å unngå versjonsfeil.
            annotated_frame = results[0].plot() 
            
            # Sjekk om vi skal lagre i bil-mappen (Lagt til 'license plate' her for å trigge OCR)
            is_vehicle = any(v in found_targets for v in ["car","license plate"])
            
            # --- EKSTRA FOR BILSKILT ---
            if is_vehicle:
                print("Kjøretøy funnet. Starter EasyOCR...", flush=True)
                ocr_result = reader.readtext(img)
                for (_, text, prob) in ocr_result:
                    if len(text) >= 5 and prob > 0.85:
                        cv2.putText(annotated_frame, f"SKILT: {text.upper()}", (20, 40), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                save_path = os.path.join(CAR_PATH, f"bil_{timestamp}.jpg")
            else:
                save_path = os.path.join(DETECTION_PATH, f"deteksjon_{timestamp}.jpg")

            # Lagre det ferdige bildet
            cv2.imwrite(save_path, annotated_frame)
            print(f"Lagret deteksjon i: {save_path}", flush=True)
        
        else:
            print(f"Ingen av objektene ({detections_for_log}) var i TARGET_OBJECTS.", flush=True)

        proc_time = time.time() - start_time
        print(f"Total tid brukt: {proc_time:.2f} sekunder.", flush=True)
        return "OK", 200

    except Exception as e:
        # Fanger hele feilmeldingen og skriver den til SSD-en
        error_msg = traceback.format_exc()
        print(f"!!! KRASJ I SCRIPTET !!!\n{error_msg}", flush=True)
        
        with open(LOG_FILE, "a") as f:
            f.write(f"\n--- [{time.strftime('%Y-%m-%d %H:%M:%S')}] ---\n{error_msg}\n")
            
        return "Internal Server Error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)