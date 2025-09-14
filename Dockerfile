FROM python:3.10-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg git wget curl build-essential cmake \
    libsm6 libxext6 libxrender-dev libgl1-mesa-glx libboost-all-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . .

# Crear carpetas necesarias
RUN mkdir -p recordings evidencias reports config_history faces

EXPOSE 5000

CMD ["python", "app.py"]