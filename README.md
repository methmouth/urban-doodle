# 📹 CCTV Inteligente — Dashboard con AI + CRUD + TTS + Reportes

Sistema de videovigilancia inteligente para escritorio y servidor.  
Usa **YOLOv8 + ByteTrack/DeepSORT** para detección y tracking de personas.  
Incluye dashboard en **PyQt5**, **API Flask**, CRUD tipo Excel, alertas TTS y reporter automático (PDF/HTML/CSV).

---

## 🚀 Características principales

- **Detección AI**
  - Detector YOLOv8 (ultralytics).
  - Trackers: **ByteTrack** (principal) o **DeepSORT** (fallback).
  - Modo diagnóstico: corre ambos en paralelo y guarda comparativas en `reports/compare_trackers.csv`.
  - Reconocimiento facial básico con `face_recognition`.

- **Dashboard PyQt5**
  - Vista panóptica (todas las cámaras) o individual (Zoom).
  - Árbol lateral: **Edificio > Habitación > Cámara**.
  - Barra de herramientas:
    - `Agregar cámara` → añadir cámaras (locales o RTSP).
    - `Recargar cámaras`.
    - `Resumen 30s` → describe últimos eventos.
    - `Exportar CSV` → exporta eventos a `reports/`.
    - Consola en vivo abajo estilo depuración.

- **Base de datos (SQLite)**
  - `persons`: empleados, clientes, proveedores, invitados.
  - `events`: log de detecciones (con bbox, cámara, timestamp, evidencia).
  - Editor tipo Excel embebido en el dashboard.

- **Alertas**
  - TTS en tiempo real: *“Alerta: persona desconocida en cámara X”*.
  - Notificaciones a Telegram (opcional).
  - Evidencias (frames) en carpeta `evidencias/`.
  - Subida opcional a nube con rclone/S3.

- **Reportes automáticos**
  - Genera **PDF y HTML** cada 8h con resumen + tabla.
  - Gráficas básicas de distribución de roles.
  - Export manual CSV desde dashboard.

- **Servicios y despliegue**
  - Ejecutable en Linux con systemd (`cctv.service`, `cctv_admin.service`).
  - Soporte Docker + docker-compose.
  - Instaladores `install.sh` y `install_bytetrack.sh`.

---

## 📂 Estructura del proyecto

CCTV_Inteligente/ │── app.py              # Dashboard principal + API Flask │── db_init.py          # Inicializador de BD (persons + events) │── reporter.py         # Generador de reportes (PDF/HTML/CSV) │── register_face.py    # Enrolamiento facial (CLI) │── cameras.json        # Configuración jerárquica de cámaras │── requirements.txt    # Dependencias Python │── install.sh          # Instalador base │── install_bytetrack.sh# Instalador ByteTrack │── Dockerfile │── docker-compose.yml │── Makefile │── .dockerignore │── systemd/ │   ├── cctv.service │   └── cctv_admin.service │── people.db           # SQLite (se genera con db_init.py) │── recordings/         # Grabaciones │── evidencias/         # Evidencias de alertas │── reports/            # Reportes y comparativas │── config_history/     # Versionado de cameras.json │── faces/              # Carpeta de rostros registrados

---

## ⚙️ Instalación en Debian 11+

```bash
git clone <REPO_URL> CCTV_Inteligente
cd CCTV_Inteligente
sudo bash install.sh

Instalar ByteTrack (opcional):

sudo bash install_bytetrack.sh

Inicializar base de datos:

python3 db_init.py

Ejecutar app:

python3 app.py


---

🐳 Uso con Docker

Construir imagen:

docker build -t cctv_inteligente .

Levantar servicio:

docker-compose up -d


---

🛠️ Uso

Al abrir app.py se lanza el dashboard.

Lateral izquierdo: árbol jerárquico de cámaras.

Centro: panóptico o vista de una sola cámara.

Derecha: herramientas y consola.


En la barra:

Agregar cámara: añade a cameras.json y versiona en config_history/.

Resumen 30s: describe últimos eventos.

Exportar CSV: exporta a reports/.



---

🔔 Ejemplo cameras.json

{
  "buildings": [
    {
      "name": "Edificio A",
      "rooms": [
        {
          "name": "Recepción",
          "cameras": [
            { "name": "Webcam Local", "source": 0, "tracker": "auto" }
          ]
        },
        {
          "name": "Oficina",
          "cameras": [
            { "name": "Camara IP", "source": "rtsp://admin:12345@192.168.1.50:554/Streaming/Channels/101", "tracker": "bytetrack" }
          ]
        }
      ]
    }
  ]
}


---

🛡️ Seguridad

cctv.service: corre como usuario limitado cctv.

cctv_admin.service: corre como root (solo administración).

Rotación de grabaciones y reportes (borrar viejos cada X días).

Opcional: cifrado de BD o almacenamiento con LUKS/encFS.



---

📊 Roadmap Futuro

Reconocimiento facial avanzado con embeddings + verificación.

Dashboard web (Flask + React) para acceso remoto.

Integración de almacenamiento en nube (Nextcloud, S3).

Reportes automáticos más ricos (PDF/HTML con estadísticas).

Analítica avanzada: comportamiento, mapas de calor.



---

👷 Autores

Equipo de Seguridad + TI
Implementación asistida con IA (OpenAI GPT-5)


---

---
# 📹 CCTV Inteligente — Dashboard con AI + CRUD + TTS + Reportes

Sistema de videovigilancia inteligente para escritorio y servidor.  
Usa **YOLOv8 + ByteTrack/DeepSORT** para detección y tracking de personas.  
Incluye dashboard en **PyQt5**, **API Flask**, CRUD tipo Excel, alertas TTS y reporter automático (PDF/HTML/CSV).

---

## 🚀 Características principales

- **Detección AI**
  - Detector YOLOv8 (ultralytics).
  - Trackers: **ByteTrack** (principal) o **DeepSORT** (fallback).
  - Modo diagnóstico: corre ambos en paralelo y guarda comparativas en `reports/compare_trackers.csv`.
  - Reconocimiento facial básico con `face_recognition`.

- **Dashboard PyQt5**
  - Vista panóptica (todas las cámaras) o individual (Zoom).
  - Árbol lateral: **Edificio > Habitación > Cámara**.
  - Barra de herramientas:
    - `Agregar cámara` → añadir cámaras (locales o RTSP).
    - `Recargar cámaras`.
    - `Resumen 30s` → describe últimos eventos.
    - `Exportar CSV` → exporta eventos a `reports/`.
    - Consola en vivo abajo estilo depuración.

- **Base de datos (SQLite)**
  - `persons`: empleados, clientes, proveedores, invitados.
  - `events`: log de detecciones (con bbox, cámara, timestamp, evidencia).
  - Editor tipo Excel embebido en el dashboard.

- **Alertas**
  - TTS en tiempo real: *“Alerta: persona desconocida en cámara X”*.
  - Notificaciones a Telegram (opcional).
  - Evidencias (frames) en carpeta `evidencias/`.
  - Subida opcional a nube con rclone/S3.

- **Reportes automáticos**
  - Genera **PDF y HTML** cada 8h con resumen + tabla.
  - Gráficas básicas de distribución de roles.
  - Export manual CSV desde dashboard.

- **Servicios y despliegue**
  - Ejecutable en Linux con systemd (`cctv.service`, `cctv_admin.service`).
  - Soporte Docker + docker-compose.
  - Instaladores `install.sh` y `install_bytetrack.sh`.

---

## 📂 Estructura del proyecto

URBAN DOODLE
# CCTV Inteligente — Dashboard con AI + CRUD + TTS

Sistema de videovigilancia inteligente para escritorio.  
Usa **YOLOv8 + ByteTrack/DeepSORT** para detección y tracking de personas en tiempo real.  
Incluye dashboard con PyQt5 y base de datos SQLite para gestionar personal, clientes, proveedores e invitados.

## 🚀 Características
- Detección AI (YOLOv8n, optimizado para edge)
- Tracking estable (ByteTrack/DeepSORT)
- Dashboard PyQt5 con CRUD estilo Excel
- Logs en DB + exportación a CSV/PDF
- Alertas por TTS en tiempo real
- Soporte Docker + systemd

## 📂 Estructura
- `app.py` — dashboard + AI
- `db_init.py` — inicialización de base de datos
- `reporter.py` — reportes en PDF
- `register_face.py` — enrolamiento de rostros
- `cameras.json` — configuración de cámaras
- `systemd/` — servicios para Linux
- `Dockerfile`, `docker-compose.yml`, `Makefile`

## 🛡️ Seguridad
- DB SQLite con versionado
- Grabaciones rotativas en `recordings/`
- Servicios dedicados para admin y usuario cctv 
Detector de Personas para PC con OpenCV y YOLOv3 💻

Este es un script de visión por computadora en Python que utiliza la cámara web de una PC para detectar personas en tiempo real. El proyecto se basa en **OpenCV** para el procesamiento de video y el modelo **YOLOv3** (You Only Look Once) pre-entrenado en el dataset COCO para la detección de objetos.

##  Características

- **Detección en Tiempo Real:** Captura video desde la cámara web (índice 0).
- **Modelo Robusto:** Utiliza YOLOv3, un modelo potente y conocido para la detección de objetos.
- **Ligero en Dependencias:** Solo requiere OpenCV y NumPy para funcionar.
- **Fácil de Ejecutar:** Un solo script de Python para iniciar la detección.



## 🛠️ Prerrequisitos

- Python 3.8+
- Pip (manejador de paquetes de Python)
- Una cámara web conectada.

## Instalación y Uso

1.  **Clona el repositorio:**
    ```bash
    git clone [https://github.com/TU_USUARIO/persona-detector-pc.git](https://github.com/TU_USUARIO/persona-detector-pc.git)
    cd persona-detector-pc
    ```

2.  **Instala las dependencias de Python:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Descarga los archivos del modelo YOLOv3:**
    Para que el script funcione, necesitas los siguientes tres archivos. Búscalos en internet y descárgalos:
    - `yolov3.weights` (El archivo de pesos, es grande ~236 MB)
    - `yolov3.cfg` (El archivo de configuración de la red)
    - `coco.names` (El archivo con los nombres de las 80 clases que detecta)
    
    **¡Importante! Coloca estos tres archivos en la misma carpeta que `detector_pc.py`.**

4.  **Ejecuta el detector:**
    ```bash
    python detector_pc.py
    ```
    Se abrirá una ventana mostrando el video de tu cámara con recuadros verdes alrededor de las personas detectadas. Presiona la tecla **'q'** para cerrar.

