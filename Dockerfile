FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential cmake git python3-dev libopenblas-dev liblapack-dev libboost-all-dev pkg-config ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt \
    && pip install cython \
    && pip install git+https://github.com/iflytek/ByteTrack.git

COPY . .

ENV TRACKER=bytetrack
CMD ["python", "app.py"]