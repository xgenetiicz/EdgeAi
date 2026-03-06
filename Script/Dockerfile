# Lettvekt Python-base
FROM python:3.11-slim

# Vi kjører alt linje for linje for å unngå tegnfeil (spesialtegn)
RUN apt-get update
RUN apt-get install -y libgl1
RUN apt-get install -y libglib2.0-0
RUN rm -rf /var/lib/apt/lists/*

# Arbeidsmappe i containeren
WORKDIR /app

# Installerer Python-biblioteker en etter en for å unngå spesialtegn problem
RUN pip install --no-cache-dir flask
RUN pip install --no-cache-dir numpy
RUN pip install --no-cache-dir opencv-python-headless
RUN pip install --no-cache-dir ultralytics
RUN pip install --no-cache-dir easyocr

# Last ned AI-modeller under bygging
RUN python -c "import easyocr; easyocr.Reader(['en'])"

# Kopierer scriptet
COPY mottakerAvData.py .

# Lager bilde-mappen for SSD-en
RUN mkdir -p /bilder

#For å sikre at AI-modellen som lastes ned
RUN mkdir -p /app/modeller 


# Eksponerer port 5000
EXPOSE 5000

# Starter appen
CMD ["python", "mottakerAvData.py"]