#lettvekt Python-base
FROM python:3.11-slim

# Vi må ha med noen ekstra Linux-biblioteker for at OpenCV skal fungere i containeren
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

#arbeidsmappe i containeren
WORKDIR /app

#Flask som er nødvendig for scriptet og AI-motorene
RUN pip install --no-cache-dir \
    flask \
    numpy \
    opencv-python-headless \
    ultralytics \
    easyocr

# "Pre-loading": Vi laster ned AI-modellene under bygging så Pi-en er klar til kamp
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
RUN python -c "import easyocr; easyocr.Reader(['en'])"

#Kopierer selve scriptet inn i containeren
COPY mottakerAvData.py .

# Lager mappen for bildene dine inne i containeren (for bind mount til SSD)
RUN mkdir -p /bilder

#Forteller Docker at vi bruker port 5000
EXPOSE 5000

#Vi starter scriptet
CMD ["python", "mottakerAvData.py"]