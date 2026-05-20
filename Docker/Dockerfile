FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Samme kommando som i PyTorch.md
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.0

RUN pip3 install --no-cache-dir ultralytics
RUN pip3 install --no-cache-dir easyocr
RUN pip3 install --no-cache-dir opencv-python-headless
RUN python3 -c "import easyocr; easyocr.Reader(['en'])"

WORKDIR /app
COPY RTSP/mottakerAvData.py .
RUN mkdir -p /bilder /app/modeller

EXPOSE 5000
CMD ["python3", "mottakerAvData.py"]