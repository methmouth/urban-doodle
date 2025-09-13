import os, cv2, sys, sqlite3, json, time, subprocess
import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
import pyttsx3

DB_PATH = "people.db"
CAM_CONFIG = "cameras.json"
TRACKER = os.getenv("TRACKER", "bytetrack").lower()

# === Inicialización ===
model = YOLO("yolov8n.pt")  # ligero para edge
engine = pyttsx3.init()

try:
    from yolox.tracker.byte_tracker import BYTETracker
    USE_BYTETRACK = True if TRACKER == "bytetrack" else False
except ImportError:
    print("⚠ ByteTrack no disponible, usando DeepSORT.")
    USE_BYTETRACK = False

if USE_BYTETRACK:
    tracker = BYTETracker(track_thresh=0.5, match_thresh=0.8)
else:
    tracker = DeepSort(max_age=30)

# === Utilidades ===
def speak(text):
    engine.say(text)
    engine.runAndWait()

def db_log_event(camera, person):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO events(timestamp, camera, person) VALUES(datetime('now'), ?, ?)", (camera, person))
    conn.commit()
    conn.close()

def load_cameras():
    with open(CAM_CONFIG, "r") as f:
        return json.load(f)

# === PyQt5 GUI ===
class CCTVApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CCTV Inteligente")
        self.resize(1200, 800)

        # Widget principal
        self.tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab: Cámaras
        self.video_label = QtWidgets.QLabel("Video aquí")
        self.tabs.addTab(self.video_label, "Monitoreo")

        # Tab: Personas (CRUD tipo Excel)
        self.table_persons = QtWidgets.QTableWidget()
        self.tabs.addTab(self.table_persons, "Personas")

        # Tab: Eventos
        self.table_events = QtWidgets.QTableWidget()
        self.tabs.addTab(self.table_events, "Eventos")

        # Timer para refrescar DB
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh_tables)
        self.timer.start(5000)

        # Cargar cámaras
        self.cameras = load_cameras()
        self.cap = cv2.VideoCapture(int(self.cameras["1"]))  # default primera

        # Loop de video
        self.timer_video = QtCore.QTimer()
        self.timer_video.timeout.connect(self.update_frame)
        self.timer_video.start(30)

    def refresh_tables(self):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Persons
        c.execute("SELECT * FROM persons")
        rows = c.fetchall()
        self.table_persons.setRowCount(len(rows))
        self.table_persons.setColumnCount(3)
        for i, r in enumerate(rows):
            for j, v in enumerate(r):
                self.table_persons.setItem(i, j, QtWidgets.QTableWidgetItem(str(v)))

        # Events
        c.execute("SELECT * FROM events ORDER BY id DESC LIMIT 50")
        rows = c.fetchall()
        self.table_events.setRowCount(len(rows))
        self.table_events.setColumnCount(4)
        for i, r in enumerate(rows):
            for j, v in enumerate(r):
                self.table_events.setItem(i, j, QtWidgets.QTableWidgetItem(str(v)))

        conn.close()

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret: return

        results = model(frame)
        detections = []
        for r in results:
            for box, conf, cls in zip(r.boxes.xyxy, r.boxes.conf, r.boxes.cls):
                if int(cls) == 0 and conf > 0.5:  # solo personas
                    x1,y1,x2,y2 = map(int, box[:4])
                    detections.append([x1,y1,x2,y2,float(conf), int(cls)])

        if USE_BYTETRACK:
            tracks = tracker.update(np.array(detections), [frame.shape[0], frame.shape[1]], [frame.shape[0], frame.shape[1]])
            for t in tracks:
                x1,y1,x2,y2,tid = map(int, t.tlbr) + [t.track_id]
                cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)
                cv2.putText(frame,f"ID:{tid}",(x1,y1-5),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)
                db_log_event("1", f"TrackID {tid}")
        else:
            tracks = tracker.update_tracks(detections, frame=frame)
            for t in tracks:
                if not t.is_confirmed(): continue
                x1,y1,x2,y2 = map(int, t.to_ltrb())
                tid = t.track_id
                cv2.rectangle(frame,(x1,y1),(x2,y2),(255,0,0),2)
                cv2.putText(frame,f"ID:{tid}",(x1,y1-5),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,0,0),2)
                db_log_event("1", f"TrackID {tid}")

        # Mostrar frame
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h,w,ch = rgb.shape
        qimg = QtGui.QImage(rgb.data,w,h,ch*w,QtGui.QImage.Format_RGB888)
        self.video_label.setPixmap(QtGui.QPixmap.fromImage(qimg))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = CCTVApp()
    win.show()
    sys.exit(app.exec_())