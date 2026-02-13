from flask import Flask, request # Flask må ha stor F for å virke
import base64 #dekoder bilder i tekst
import os
import time
import cv2 # for tegning og bildebehandling slik at vi viser visuelt hva som blir identifisert!
import numpy as np #Dette er for bildematriser
from ultralytics import YOLO # AI - motoren som gjør Object identifisering
import easyocr #Skiltleseren, der mqtt skal identifisere denne strengen og trekke det ut av bildet.

app = Flask(__name__)

#Vi bruker denne pathen slik at den når riktig volum som er:
# - /media/genetiicz/storage/bil/bilder:/bilder #Dette er data(bilder) av skilt og bil!
#Bildene blir lagret på ssd

#Scriptet er for å tilrettelegget behandling av mottakelse av Base64 data,
#samt dekoder bildet tilbake til bilde-bytes, slik at bildene kommer frem.

#RIKTIG_PATH
SAVE_PATH = "/bilder"

#Sikrer at mappen eksisterer på SSD før vi lagrer til serveren.
if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)

#AI - modell oppstart på RAM ved oppstart på Pironman 5 16GB RAM - Raspberry pi 5
print("Initialiserer 'hjernen' (YOLO + OCR)")
model = YOLO("yolov8n.pt")
reader = easyocr.Reader(['en'], gpu=False)
print("Systemet er nå klart for objekt identifikasjon!")

#Liste over objekter som skal trigge på lagring, dette er for test - hvor listen vil være mindre senere
TARGET_OBJECTS = ["person","remote","cell phone","car", "truck", "laptop", "mouse"]

@app.route('/upload-bilde', methods=['POST'])
def upload():
    try:
        #hente ut tekstrengen til base64
        base64_data = request.data.decode('utf-8')

        #dekode tekst til bilde-bytes
        image_bytes = base64.b64decode(base64_data)

        # Konverterer bytes til bildeformat som AI kan lese
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # AI IDENTIFISERING (Automatisk)
        results = model(img, verbose=False)
        
        # Sjekk om vi fant noen 'TARGET_OBJECTS'
        found_interesting = False
        for r in results:
            for box in r.boxes:
                label = model.names[int(box.cls[0])]
                if label in TARGET_OBJECTS:
                    found_interesting = True
                    break
        
        # Når vi finner noe bruker vi AI-ens innebygde tegnefunksjon
        if found_interesting:
            # .plot() tegner bokser og navn på bildet helt AUTOMATISK -- dette gjør den ved ta hensyn til koordinater
            # som x1, y1.
            annotated_frame = results[0].plot() 
            
            # --- EKSTRA FOR BILSKILT ---
            # Hvis det er en bil, kjører vi OCR i tillegg 
            if any(model.names[int(b.cls[0])] in ["car", "truck"] for b in results[0].boxes):
                ocr_result = reader.readtext(img)
                for (_, text, prob) in ocr_result:
                    if len(text) >= 5 and prob > 0.5: #Skal registrere skilt der den er mer enn 50% sikker.
                        # Skriver skiltet nederst i hjørnet på det ferdige bildet
                        cv2.putText(annotated_frame, f"SKILT: {text.upper()}", (20, 40), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)

            #Lagre på serveren (raspberry pi 5)
            filename = f"deteksjon_{int(time.time())}.jpg"
            filepath = os.path.join(SAVE_PATH, filename)
            
            # Vi lagrer det ferdige bildet (med automatiske bokser)
            cv2.imwrite(filepath, annotated_frame)

            print(f"Suksess, AI har merket bildet og lagret det i {SAVE_PATH}/{filename}")
            return "OK - Funnet og merket", 200
        
        else:
            print("Ingen relevante objekter funnet. Forkaster bildet.")
            return "OK - Ingen treff", 200

    except Exception as e:
        print(f"FEIL: {e}")
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)