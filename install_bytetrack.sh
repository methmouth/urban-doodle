#!/usr/bin/env bash
set -e

echo "=== Instalando ByteTrack ==="

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "⚠ Virtualenv no encontrado, ejecuta primero ./install.sh"
  exit 1
fi

source "$VENV_DIR/bin/activate"

# Instalar dependencias necesarias para ByteTrack
pip install cython cython_bbox lap
pip install -U onemetric
pip install -U yolox

# Clonar repositorio oficial si no existe
if [ ! -d "$PROJECT_DIR/bytetrack" ]; then
  git clone https://github.com/ifzhang/ByteTrack.git "$PROJECT_DIR/bytetrack"
fi

cd "$PROJECT_DIR/bytetrack"
pip install -r requirements.txt

echo "=== ByteTrack instalado correctamente ==="