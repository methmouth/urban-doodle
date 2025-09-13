#!/usr/bin/env bash
set -e
echo "=== Instalando dependencias base ==="
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip build-essential ffmpeg git wget curl libsm6 libxrender1 libxext6
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt