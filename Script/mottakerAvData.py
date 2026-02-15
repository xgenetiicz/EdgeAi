from flask import Flask, request # Flask må ha stor F for å virke
import base64 #dekoder bilder i tekst
import os
import time
import cv2 # for tegning og bildebehandling slik at vi viser visuelt hva som blir identifisert!
import numpy as np #Dette er for bildematriser
from ultralytics import YOLO # AI - motoren som gjør Object identifisering
import easyocr #Skiltleseren, der mqtt skal identifisere denne strengen og trekke det ut av bildet.

app = Flask(__name__)

# --- MAPPESTRUKTUR FOR SSD ---
BASE_PATH = "/bilder"
# Mappe for RÅ-bilder uten bokser (Viktig for Edge Impulse læring)
TRAIN_PATH = os.path.join(BASE_PATH, "edge_impulse")
# Mappe for ferdige deteksjoner med bokser
DETECTION_PATH = os.path.join(BASE_PATH, "deteksjoner")
# Spesifikk undermappe for bil-testene
CAR_PATH = os.path.join(DETECTION_PATH, "bil")

# Sikrer at alle mapper eksisterer på SSD før vi starter
for path in [TRAIN_PATH, DETECTION_PATH, CAR_PATH]:
    if not os.path.exists(path):
        os.makedirs(path)

# AI - modell oppstart på RAM ved oppstart på Pironman 5 16GB RAM - Raspberry pi 5
print("Initialiserer 'hjernen' (YOLO + OCR)")
model = YOLO("yolov8m.pt") # Laster ned M-modellen for best accuracy og fart på Pi 5 CPU
reader = easyocr.Reader(['en'], gpu=False)
print("Systemet er nå klart for objekt identifikasjon!")

# Liste over objekter som skal trigge på lagring. 
# KUN disse vil bli tegnet på bildet og lagret i deteksjons-mappene.
TARGET_OBJECTS = ["person", "cell phone", "car", "truck", "laptop"]

# Henter ID-ene til objektene automatisk for å filtrere bort irrelevante funn (som bananer/toalett)
TARGET_IDS = [id for id, name in model.names.items() if name in TARGET_OBJECTS]

@app.route('/upload-bilde', methods=['POST'])
def upload():
    try:
        # hente ut tekstrengen til base64
        base64_data = request.data.decode('utf-8')

        # dekode tekst til bilde-bytes
        image_bytes = base64.b64decode(base64_data)

        # Konverterer bytes til bildeformat som AI kan lese
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        timestamp = int(time.time())

        # LAGRE RÅ-BILDE UANSETT (Edge Impulse Data)
        # Vi lagrer originalen her slik at vi kan lære opp AI-en på Edge Impulse senere, så trenger en undermappe for bilder uten
        # uten tegninger
        cv2.imwrite(os.path.join(TRAIN_PATH, f"raw_{timestamp}.jpg"), img)

        # AI IDENTIFISERING (Automatisk)
        # Bruker konfidens på 0.7 for å sikre nøyaktige treff i produksjon
        results = model(img, verbose=False, conf=0.7) 
        
        # Sjekk om vi faktisk fant noe fra TARGET_OBJECTS
        found_names = [model.names[int(b.cls[0])] for r in results for b in r.boxes]
        is_vehicle = any(name in ["car", "truck"] for name in found_names)
        found_interesting = any(name in TARGET_OBJECTS for name in found_names)
        
        # LAGRE DETEKSJON (Kun hvis objektet er i listen vår)
        if found_interesting: 
            # .plot(classes=TARGET_IDS) tegner KUN bokser på objektene i listen din!
            annotated_frame = results[0].plot(classes=TARGET_IDS) 
            
            # --- EKSTRA FOR BILSKILT ---
            if is_vehicle:
                ocr_result = reader.readtext(img)
                for (_, text, prob) in ocr_result:
                    if len(text) >= 5 and prob > 0.85: # Skal registrere skilt der den er mer enn 85% sikker.
                        cv2.putText(annotated_frame, f"SKILT: {text.upper()}", (20, 40), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                
                # Lagre i bil-mappen
                save_path = os.path.join(CAR_PATH, f"bil_{timestamp}.jpg")
            else:
                # Lagre i generell deteksjons-mappe hvis det ikke er en bil.
                save_path = os.path.join(DETECTION_PATH, f"deteksjon_{timestamp}.jpg")

            # Lagre det ferdige bildet med bokser
            cv2.imwrite(save_path, annotated_frame)
            print(f"Suksess! Interessant objekt funnet og lagret i {save_path}")
            return "OK - Deteksjon lagret", 200
        
        else:
            # Hvis ingen target objects ble funnet, har vi allerede lagret råbildet over.
            return "OK - Kun råbilde lagret (ingen target treff)", 200

    except Exception as e:
        print(f"FEIL: {e}")
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)