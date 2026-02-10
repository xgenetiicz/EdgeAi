#lettvekt Python-base
FROM python:3.11-slim

#arbeidsmappe i containeren
WORKDIR /app

#Flask som er nødvendig for scriptet
RUN pip install --no-cache-dir flask

#Kopierer selve scriptet inn i containeren - sånn at det funker 24/7
COPY mottakerAvData.py .

#Forteller Docker at vi bruker port 5000 slik at den mottar
EXPOSE 5000

#Vi starter scriptet
CMD ["python", "mottakerAvData.py"]