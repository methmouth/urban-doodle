#!/usr/bin/env bash
set -e

echo "=== Instalador CCTV_Inteligente (Debian 11+) ==="

apt-get update -y
apt-get install -y python3 python3-venv python3-pip ffmpeg git wget curl build-essential cmake \
    libsm6 libxext6 libxrender-dev libgl1-mesa-glx libboost-all-dev libsqlite3-dev

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

# Crear usuario de servicio
if ! id -u cctv >/dev/null 2>&1; then
  useradd -m -s /bin/bash cctv
fi

# Crear venv
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip wheel setuptools

# Instalar dependencias
pip install -r "$PROJECT_DIR/requirements.txt"

echo "=== Instalación completada ==="
echo "Ejecuta: source $VENV_DIR/bin/activate"
echo "Inicializa la BD: python db_init.py"
echo "Ejecuta la app: python app.py"