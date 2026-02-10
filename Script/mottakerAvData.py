from flask import Flask, request # Flask må ha stor F for å virke
import base64 #dekoder bilder i tekst
import os
import time

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

@app.route('/upload-bilde', methods=['POST'])
def upload():
    try:
        #hente ut tekstrengen til base64
        base64_data = request.data.decode('utf-8')

        #dekode tekst til bilde-bytes
        image_bytes = base64.b64decode(base64_data)

        #Lagre på serveren (raspberry pi 5)
        filename = f"bil_{int(time.time())}.jpg"
        filepath = os.path.join(SAVE_PATH, filename)

        with open(filepath, 'wb') as f:
            f.write(image_bytes)

        print(f"Suksess, bildet er lagret i {SAVE_PATH}/{filename}")
        return "OK", 200

    except Exception as e:
        print(f"FEIL: {e}")
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)