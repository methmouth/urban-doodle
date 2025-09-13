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

