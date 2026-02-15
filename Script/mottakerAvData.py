from flask import Flask, request # Flask må ha stor F for å virke
import base64 # dekoder bilder i tekst
import os
import time
import cv2 # for tegning og bildebehandling
import numpy as np # Dette er for bildematriser
from ultralytics import YOLO # AI - motoren
import easyocr # Skiltleseren
import traceback # Henter ut nøyaktig feilmelding ved krasj

app = Flask(__name__)

# --- RIKTIG_PATH FOR SSD ---
BASE_PATH = "/bilder"
TRAIN_PATH = os.path.join(BASE_PATH, "edge_impulse") 
DETECTION_PATH = os.path.join(BASE_PATH, "deteksjoner") 
CAR_PATH = os.path.join(BASE_PATH, "bil") 
LOG_FILE = os.path.join(BASE_PATH, "error_log.txt") 

for path in [TRAIN_PATH, DETECTION_PATH, CAR_PATH]:
    if not os.path.exists(path):
        os.makedirs(path)

# AI - modell oppstart
print("Initialiserer 'hjernen' (YOLO + OCR)", flush=True)
model = YOLO("yolov8m.pt") 
reader = easyocr.Reader(['en'], gpu=False)
print("Systemet er nå klart!", flush=True)

# Dine Target Objects
TARGET_OBJECTS = ["person", "remote", "cell phone", "car", "truck", "laptop"]

@app.route('/upload-bilde', methods=['POST'])
def upload():
    start_time = time.time()
    print(f"\n--- [{time.strftime('%H:%M:%S')}] Forespørsel mottatt ---", flush=True)
    
    try:
        base64_data = request.data.decode('utf-8')
        image_bytes = base64.b64decode(base64_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Bilde-dekoding feilet.")

        timestamp = int(time.time())
        cv2.imwrite(os.path.join(TRAIN_PATH, f"raw_{timestamp}.jpg"), img)

        # Kjører analyse på 0.2 som vi ble enige om
        valgt_conf = 0.2
        results = model(img, verbose=False, conf=valgt_conf) 
        
        # Loggføring av alt den ser
        detections = []
        for r in results:
            for box in r.boxes:
                name = model.names[int(box.cls[0])]
                conf = float(box.conf[0])
                detections.append(f"{name} ({conf:.2f})")
        
        if detections:
            print(f"AI-en ser: {', '.join(detections)}", flush=True)
        else:
            print("AI-en ser ingenting.", flush=True)

        # Sjekk mot target-lista di
        found_targets = [d.split(' ')[0] for d in detections if d.split(' ')[0] in TARGET_OBJECTS]
        
        if found_targets:
            print(f"TREFF: Fant {found_targets}. Lagrer deteksjon.", flush=True)
            
            # FIKS: Fjernet 'classes' argumentet som forårsaket krasj
            annotated_frame = results[0].plot() 
            
            is_vehicle = any(v in found_targets for v in ["car", "truck"])
            if is_vehicle:
                print("Starter EasyOCR...", flush=True)
                ocr_result = reader.readtext(img)
                for (_, text, prob) in ocr_result:
                    if len(text) >= 5 and prob > 0.85:
                        cv2.putText(annotated_frame, f"SKILT: {text.upper()}", (20, 40), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                save_path = os.path.join(CAR_PATH, f"bil_{timestamp}.jpg")
            else:
                save_path = os.path.join(DETECTION_PATH, f"deteksjon_{timestamp}.jpg")

            cv2.imwrite(save_path, annotated_frame)
            print(f"Lagret i: {save_path}", flush=True)
        else:
            print(f"Ingen targets funnet (Slo ut på: {detections})", flush=True)

        return "OK", 200

    except Exception as e:
        error_msg = traceback.format_exc()
        print(f"!!! KRASJ !!!\n{error_msg}", flush=True)
        with open(LOG_FILE, "a") as f:
            f.write(f"\n--- [{time.strftime('%Y-%m-%d %H:%M:%S')}] ---\n{error_msg}\n")
        return "Internal Server Error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)