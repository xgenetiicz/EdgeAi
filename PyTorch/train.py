import torch
from ultralytics import YOLO
import os
import cv2
import glob

def main():
    # Sett stien til din bachelor-mappe
    path_to_my_storage = os.getenv("path_to_my_storage")
    if path_to_my_storage is None:
        print("Feil: 'path_to_my_storage' er ikke satt i .env-filen!")
        return #vil at den skal stoppe hvis path ikke er satt.
    base_path = path_to_my_storage
    os.chdir(base_path) 
    
    # GRAYSCALE KONVERTERING
    # Vi endrer bildene i images-mappene. Labels-mappene inneholder bare tekst,
    # så de lar vi være i fred, men vi vasker bort cachen deres etterpå.
    print("Konverterer bilder til grayscale for monokrom-kamera!")
    for folder in ['train/images', 'valid/images', 'test/images']:
        files = glob.glob(os.path.join(base_path, folder, "*.jpg")) + glob.glob(os.path.join(base_path, folder, "*.png"))
        for f in files:
            img = cv2.imread(f)
            if img is not None:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                cv2.imwrite(f, cv2.merge([gray, gray, gray])) # Beholder 3 kanaler for kompatibilitet
    # Dette sletter train.cache og val.cache uansett om de ligger i labels eller images
    print("Sletter alle gamle .cache-filer i hele prosjektet!")
    for cache_path in glob.glob(os.path.join(base_path, "**/*.cache"), recursive=True):
        os.remove(cache_path)
        print(f"Fjernet: {cache_path}")

    # I WSL2 er Windows-disker montert under /mnt/
    #os.chdir('/mnt/e/bacheloroppgave') Prøvde å med WSL -  men windows er dessverre bare problematisk.

    #Løsningen er selvfølgelig Linux med dual boot/Ubuntu.Da funket treningen med AMD GPU.
    
    # Sjekker om ROCm/GPU er klar
    if torch.cuda.is_available():
        device = 'cuda'
        print(f"Starter lokal trening på AMD GPU: {torch.cuda.get_device_name(0)}")
    else: 
        print("Finner ikke GPU-enhet (ROCm). Sjekk installasjonen eller bruk 'cpu'.")
        return

    model = YOLO("yolov8m.pt") 

    model.train(
        data="data.yaml",
        epochs=60, #trener litt og litt ved resume trening
        imgsz=1024,
        device=device,
        batch=4,
        project="bachelor_ai",
        name="final_1024px",
        amp=False,   
        workers=0,
        exist_ok=True,
        plots=True,
        
        # --- AUGMENTERINGER ---
        # Dette er albumentations som har blitt brukt under trening - 
        augment=True,
        mosaic=0.5,
        mixup=0.0,
        hsv_v=0.4,
        degrees=5.0,
        perspective=0.0001,
        shear=0.0, #ønsker ikke å deformere skiltbokstaver lenger.
        scale=0.6, 
        hsv_s=0.0, #monochromatic photos - so we get grayscale 100%. (saturation)
        fliplr=0.5, #speilvending
        translate=0.1 #flytter på bilene -  spesielt de som er halveis med i bildet.
    )

if __name__ == '__main__':
    main()
