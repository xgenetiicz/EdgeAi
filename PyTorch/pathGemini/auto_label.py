import google.generativeai as genai
import PIL.Image
import os
import time
import re


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')


BASE_DIR = os.getenv("path_to_my_storage")
if BASE_DIR is None:
    print("Feil: 'path_to_my_storage' er ikke satt i .env-filen!")
    exit(1)
SPLITS = ['train', 'valid', 'test']
class_map = {"car": 0, "license plate": 1}

prompt = """Detect all cars and license plates. 
For each object, provide the coordinates and label in this exact format:
[ymin, xmin, ymax, xmax, label]
Use a scale of 0 to 1000. Only return the list of boxes, no other text."""

for split in SPLITS:
    img_dir = os.path.join(BASE_DIR, split, 'images')
    lbl_dir = os.path.join(BASE_DIR, split, 'labels')
    os.makedirs(lbl_dir, exist_ok=True)
    
    if not os.path.exists(img_dir):
        print(f"Fant ikke mappen: {img_dir}, hopper over...")
        continue

    bilder = [f for f in os.listdir(img_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    print(f"\n--- Sjekker {len(bilder)} bilder i '{split}' ---")

    for img_name in bilder:
        label_path = os.path.join(lbl_dir, img_name.rsplit('.', 1)[0] + ".txt")

        # Hopper over hvis filen allerede er merket korrekt
        if os.path.exists(label_path) and os.path.getsize(label_path) > 0:
            print(f"[{split}] Hopper over {img_name} (allerede merket).")
            continue

        print(f"[{split}] Sender til Gemini: {img_name}...")
        img = PIL.Image.open(os.path.join(img_dir, img_name))
        
        try:
            response = model.generate_content([img, prompt])
            # Fjerner markdown og json-tagger som Gemini av og til legger til
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            
            # Finner alle bokser i formatet [y, x, y, x, label]
            boxes = re.findall(r'\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*["\']?([\w\s]+)["\']?\s*\]', clean_text)
            
            if boxes:
                with open(label_path, "w") as f:
                    for ymin, xmin, ymax, xmax, label in boxes:
                        label = label.lower()
                        if label in class_map:
                            # YOLO-konvertering (0.0 - 1.0)
                            xc = (int(xmin) + int(xmax)) / 2000
                            yc = (int(ymin) + int(ymax)) / 2000
                            w = (int(xmax) - int(xmin)) / 1000
                            h = (int(ymax) - int(ymin)) / 1000
                            f.write(f"{class_map[label]} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
                print(f"Lagret {len(boxes)} objekter.")
            else:
                print(f"Advarsel: Ingen gyldige bokser funnet i svaret.")
            
            # Ventetid for å unngå "429 Resource exhausted"
            time.sleep(4) 
            
        except Exception as e:
            print(f"   X Feil med {img_name}: {e}")
            if "429" in str(e):
                print("Rate limit nådd.")
                time.sleep(10)

print(f"\nHELT FERDIG! kjør train.py nå for å trene modellen.")
