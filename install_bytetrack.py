#!/usr/bin/env bash
set -e
echo "=== Instalando ByteTrack ==="
sudo apt-get update -y
sudo apt-get install -y build-essential cmake git python3-dev libopenblas-dev liblapack-dev libboost-all-dev pkg-config
if [ -d "venv" ]; then source venv/bin/activate; fi
pip install --upgrade pip setuptools wheel
pip install cython
pip install git+https://github.com/iflytek/ByteTrack.git