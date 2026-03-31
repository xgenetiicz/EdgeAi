import torch
from ultralytics import YOLO
import os

def main():
    #sti til mappen
    path_to_my_storage = os.getenv("path_to_my_storage")
    if path_to_my_storage is None:
        print("Feil: 'path_to_my_storage' er ikke satt i .env-filen!")
        return #vil at den skal stoppe hvis path ikke er satt.

    base_path = path_to_my_storage
    os.chdir(base_path) 

    #Sjekk GPU
    if torch.cuda.is_available():
        print(f"Gjenopptar trening på: {torch.cuda.get_device_name(0)}")
    else:
        print("GPU ikke funnet!")
        return

    # Stien til trente modell av den siste modellen (last.pt)
    # Dette er eksempel på hvordan vi brukte filstier slik at vi kunne fortsette
    # treningen etter at den ble stoppet - ettersom dette tok flere timer og nesten dager.
    # ALT ble kjørt lokalt på starten på en AMD 6700 XT GPU med ROCm

    #Peker på riktig path for treningen - basert på train.py
    model_path = 'runs/detect/bachelor_ai/test_1024px/weights/last.pt'
    model = YOLO(model_path)

    #Denne vil lese fra args.yaml filen som ble laget når treningen ble stoppet i den mappen.
    #Hvis du vil endre batch,pixel størrelse, epoker så må du endre args.yaml filen til 
    #Der treningen ligger!!!

    # Som er i dette tilfellet: runs/detect/bachelor_ai/test_1024px/args.yaml.

    model.train(resume=True)

if __name__ == '__main__':
    main()
