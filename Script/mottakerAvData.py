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
TRAIN_PATH = os.path.join(BASE_PATH, "edge_impulse") # Rå-bilder for læring
DETECTION_PATH = os.path.join(BASE_PATH, "deteksjoner") # Ferdige bilder
CAR_PATH = os.path.join(BASE_PATH, "bil") # Spesifikk for bil-test
LOG_FILE = os.path.join(BASE_PATH, "error_log.txt") # Her lagres 500-feilmeldingen

# Sikrer at mappen eksisterer på SSD før vi lagrer til serveren.
for path in [TRAIN_PATH, DETECTION_PATH, CAR_PATH]:
    if not os.path.exists(path):
        os.makedirs(path)

# AI - modell oppstart på RAM ved oppstart på Raspberry pi 5
print("Initialiserer 'hjernen' (YOLO + OCR)", flush=True)
model = YOLO("yolov8m.pt") # Laster ned M-modellen for best accuracy og fart
reader = easyocr.Reader(['en'], gpu=False)
print("Systemet er nå klart for objekt identifikasjon!", flush=True)

# Liste over objekter som skal trigge på lagring
TARGET_OBJECTS = ["person", "cell phone", "car", "truck", "laptop"]
# Henter ID-er slik at plot() bare tegner det vi vil se
TARGET_IDS = [id for id, name in model.names.items() if name in TARGET_OBJECTS]

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
        
        # 1. LAGRE RÅ-BILDE (Dette lagres uansett for Edge Impulse)
        cv2.imwrite(os.path.join(TRAIN_PATH, f"raw_{timestamp}.jpg"), img)

        # 2. AI IDENTIFISERING (Bruker konfidens på 0.2 som forespurt)
        print(f"Kjører YOLOv8m-analyse (conf=0.2)...", flush=True)
        results = model(img, verbose=False, conf=0.2) 
        
        # Sjekker hvilke objekter vi fant
        found_names = [model.names[int(b.cls[0])] for r in results for b in r.boxes]
        is_vehicle = any(name in ["car", "truck"] for name in found_names)
        
        # Sjekk om vi fant noen 'TARGET_OBJECTS'
        if any(name in TARGET_OBJECTS for name in found_names):
            print(f"Treff funnet: {found_names}. Starter bildebehandling.", flush=True)
            
            # .plot() tegner bokser og navn KUN for dine objekter
            annotated_frame = results[0].plot(classes=TARGET_IDS) 
            
            # --- EKSTRA FOR BILSKILT ---
            if is_vehicle:
                print("Starter EasyOCR skiltlesing...", flush=True)
                ocr_result = reader.readtext(img)
                for (_, text, prob) in ocr_result:
                    if len(text) >= 5 and prob > 0.85:
                        cv2.putText(annotated_frame, f"SKILT: {text.upper()}", (20, 40), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                save_path = os.path.join(CAR_PATH, f"bil_{timestamp}.jpg")
            else:
                save_path = os.path.join(DETECTION_PATH, f"deteksjon_{timestamp}.jpg")

            # Lagre det ferdige bildet (med automatiske bokser)
            cv2.imwrite(save_path, annotated_frame)
            print(f"Lagret deteksjon i: {save_path}", flush=True)
        
        else:
            print("Ingen relevante objekter over terskelen på 0.5 funnet.", flush=True)

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