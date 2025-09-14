#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py - CCTV Inteligente (versión final)
- YOLOv8 (ultralytics)
- Tracker: ByteTrack (por defecto), DeepSORT (fallback), o ambos en modo diagnóstico
- Face recognition (face_recognition)
- GUI PyQt5: árbol Edificio>Habitación>Cámara, panóptico, vista individual, consola logs
- Enroll GUI + register_face helper
- Reporter thread + Flask API
- TTS (pyttsx3) + Telegram + upload hooks (rclone / s3)
"""
import os, sys, json, time, sqlite3, threading, subprocess, traceback, math
from pathlib import Path
from collections import deque, defaultdict

import cv2
import numpy as np
from ultralytics import YOLO
import face_recognition
import pyttsx3
import pandas as pd
import requests

from PyQt5 import QtWidgets, QtGui, QtCore
from flask import Flask, jsonify

# ----------------------- Paths & constants -----------------------
BASE = Path(__file__).parent
DB_PATH = BASE / "people.db"
CAM_CONF = BASE / "cameras.json"
FACES_DIR = BASE / "faces"
EVID_DIR = BASE / "evidencias"
RECORD_DIR = BASE / "recordings"
REPORTS_DIR = BASE / "reports"
CONFIG_HISTORY = BASE / "config_history"

for p in (FACES_DIR, EVID_DIR, RECORD_DIR, REPORTS_DIR, CONFIG_HISTORY):
    p.mkdir(parents=True, exist_ok=True)

# Configurable via env:
TRACKER_DEFAULT = os.getenv("TRACKER", "bytetrack").lower()
MODEL_WEIGHTS = os.getenv("YOLO_WEIGHTS", "yolov8n.pt")
ALERT_COOLDOWN = float(os.getenv("ALERT_COOLDOWN", "8"))
BUFFER_SECONDS = int(os.getenv("BUFFER_SECONDS", "30"))
PROCESS_EVERY_N_FRAMES = int(os.getenv("PROCESS_EVERY_N_FRAMES", "3"))
UPLOAD_METHOD = os.getenv("UPLOAD_METHOD","")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN","")
TELEGRAM_CHAT  = os.getenv("TELEGRAM_CHAT","")
COMPARE_TRACKERS = os.getenv("COMPARE_TRACKERS","false").lower() in ("1","true","yes")

# ----------------------- Load model -----------------------
print("Cargando YOLO:", MODEL_WEIGHTS)
model = YOLO(MODEL_WEIGHTS)

# ----------------------- Tracker imports -----------------------
use_bytetrack = False
use_deepsort = False
try:
    from yolox.tracker.byte_tracker import BYTETracker
    use_bytetrack = True
except Exception:
    pass

try:
    from deep_sort_realtime.deepsort_tracker import DeepSort
    use_deepsort = True
except Exception:
    pass

# ----------------------- Tracker wrapper -----------------------
class TrackerWrapper:
    def __init__(self, mode_hint=None):
        self.mode = None
        self.inst = None
        hint = (mode_hint or TRACKER_DEFAULT).lower()
        if hint == "bytetrack" and use_bytetrack:
            self.inst = BYTETracker(track_thresh=0.5, track_buffer=30, match_thresh=0.8)
            self.mode = "bytetrack"
        elif hint == "deepsort" and use_deepsort:
            self.inst = DeepSort(max_age=30)
            self.mode = "deepsort"
        elif use_bytetrack:
            self.inst = BYTETracker(track_thresh=0.5, track_buffer=30, match_thresh=0.8)
            self.mode = "bytetrack"
        elif use_deepsort:
            self.inst = DeepSort(max_age=30)
            self.mode = "deepsort"
        else:
            raise RuntimeError("Ningún tracker disponible")

    def update(self, detections, frame=None):
        if self.mode == "deepsort":
            return self.inst.update_tracks(detections, frame=frame)
        else:
            online_targets = self.inst.update(detections, (frame.shape[0], frame.shape[1]), (frame.shape[0], frame.shape[1]))
            outs = []
            for t in online_targets:
                class Obj: pass
                o = Obj()
                o.track_id = t.track_id
                tlwh = t.tlwh
                o.to_ltrb = lambda tlwh=tlwh: (int(tlwh[0]), int(tlwh[1]), int(tlwh[0]+tlwh[2]), int(tlwh[1]+tlwh[3]))
                o.is_confirmed = lambda : True
                outs.append(o)
            return outs
# ----------------------- Parte 2 de app.py -----------------------
# Face DB (encodings cache)
known_encodings = []
known_meta = []  # list of dicts {name, role, path}

def reload_known_faces():
    global known_encodings, known_meta
    known_encodings = []
    known_meta = []
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT name, role, face_path FROM persons WHERE face_path IS NOT NULL").fetchall()
        conn.close()
        for r in rows:
            p = r[2]
            try:
                if p and Path(p).exists():
                    img = face_recognition.load_image_file(p)
                    encs = face_recognition.face_encodings(img)
                    if encs:
                        known_encodings.append(encs[0])
                        known_meta.append({"name": r[0], "role": r[1], "path": p})
            except Exception as e:
                print("Error loading face:", p, e)
    except Exception as e:
        print("reload_known_faces error", e)

reload_known_faces()

# Buffer & summarizer
event_buffer = deque()

def add_to_buffer(evt):
    event_buffer.append((time.time(), evt))
    cutoff = time.time() - BUFFER_SECONDS
    while event_buffer and event_buffer[0][0] < cutoff:
        event_buffer.popleft()

def summarize_buffer():
    items = [e for ts,e in event_buffer]
    if not items:
        return "Sin eventos recientes."
    by_cam = defaultdict(int)
    unknown = 0
    for e in items:
        by_cam[e.get("camera")] += 1
        if e.get("person_name") in (None, "Desconocido"):
            unknown += 1
    parts = [f"{c}:{n}" for c,n in by_cam.items()]
    return f"{'; '.join(parts)}; Desconocidos: {unknown}"

# Compare trackers CSV header
COMPARE_CSV = REPORTS_DIR / "compare_trackers.csv"
if COMPARE_TRACKERS:
    if not COMPARE_CSV.exists():
        COMPARE_CSV.write_text("ts,camera,frame_idx,bytetrack_count,deepsort_count,bytetrack_ids,deepsort_ids\n", encoding="utf-8")

# helper upload (stub)
def safe_upload(path):
    try:
        return upload_file(path, None)
    except Exception as e:
        print("upload error", e)
        return False

# CameraWorker with optional compare mode
class CameraWorker(QtCore.QThread):
    frame_signal = QtCore.pyqtSignal(object, str)
    alert_signal = QtCore.pyqtSignal(dict)

    def __init__(self, cam_id, source, tracker_mode=None, process_every=PROCESS_EVERY_N_FRAMES):
        super().__init__()
        self.cam_id = str(cam_id)
        self.source = source
        self.process_every = process_every
        self.running = True
        self.cap = None
        self.tracker_mode = tracker_mode
        self.process_idx = 0
        self.last_alert = {}
        # trackers: primary and secondary for compare
        try:
            # primary tracker per-camera/hint
            self.primary_tracker = TrackerWrapper(mode_hint=tracker_mode)
        except Exception as e:
            print(f"[{self.cam_id}] Primary tracker init failed:", e); self.primary_tracker = None
        self.secondary_tracker = None
        if COMPARE_TRACKERS and use_bytetrack and use_deepsort:
            # create both if available (for diagnosis only)
            try:
                self.bytet = TrackerWrapper(mode_hint="bytetrack")
                self.deept = TrackerWrapper(mode_hint="deepsort")
                self.secondary_tracker = (self.bytet, self.deept)
                print(f"[{self.cam_id}] Compare mode: both trackers active")
            except Exception as e:
                print(f"[{self.cam_id}] Compare init failed:", e)
                self.secondary_tracker = None

    def run(self):
        self.cap = cv2.VideoCapture(self.source)
        while self.running:
            if not self.cap.isOpened():
                time.sleep(0.5)
                self.cap = cv2.VideoCapture(self.source)
                continue
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.02)
                continue
            self.process_idx += 1
            if self.process_idx % self.process_every == 0:
                try:
                    preds = model(frame, verbose=False)
                    dets = []
                    for r in preds:
                        boxes = getattr(r, "boxes").xyxy.cpu().numpy()
                        confs = getattr(r, "boxes").conf.cpu().numpy()
                        clss = getattr(r, "boxes").cls.cpu().numpy()
                        for (x1,y1,x2,y2),conf,cls in zip(boxes, confs, clss):
                            if int(cls)==0 and conf>0.35:
                                dets.append([int(x1),int(y1),int(x2),int(y2),float(conf),int(cls)])
                    # primary tracker update
                    if self.primary_tracker:
                        tracks = self.primary_tracker.update(dets, frame=frame)
                    else:
                        tracks = []

                    # If compare mode, update both trackers separately and log counts/ids
                    if self.secondary_tracker:
                        bt, ds = self.secondary_tracker
                        bt_out = bt.update(dets, frame=frame)
                        ds_out = ds.update(dets, frame=frame)
                        # collect ids
                        bt_ids = [str(getattr(o,"track_id",None)) for o in bt_out]
                        ds_ids = [str(getattr(o,"track_id",None)) for o in ds_out]
                        # append compare log
                        try:
                            line = f"{time.strftime('%Y-%m-%d %H:%M:%S')},{self.cam_id},{self.process_idx},{len(bt_out)},{len(ds_out)},\"{';'.join(bt_ids)}\",\"{';'.join(ds_ids)}\"\n"
                            COMPARE_CSV.write_text(line, mode="a", encoding="utf-8")
                        except Exception as e:
                            # fallback append
                            with open(REPORTS_DIR/"compare_trackers.tmp","a",encoding="utf-8") as f:
                                f.write(line)
                    # handle primary tracks for alerts / recognition
                    for t in tracks:
                        confirmed = getattr(t,"is_confirmed", lambda: True)()
                        if not confirmed: continue
                        tid = getattr(t,"track_id", None)
                        ltrb = getattr(t,"to_ltrb", lambda: (0,0,0,0))()
                        x1,y1,x2,y2 = map(int, ltrb)
                        # crop head region
                        h = max(1, y2-y1); head = max(1, h//3)
                        y0, y1h = max(0,y1), min(y2, y1+head)
                        crop = frame[y0:y1h, x1:x2] if (x2>x1 and y1h>y0) else None
                        name = "Desconocido"
                        if crop is not None and crop.size>0 and known_encodings:
                            try:
                                rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                                encs = face_recognition.face_encodings(rgb)
                                if encs:
                                    dists = face_recognition.face_distance(known_encodings, encs[0])
                                    idxm = int(np.argmin(dists))
                                    if dists[idxm] < 0.45:
                                        name = known_meta[idxm]["name"]
                            except Exception as e:
                                print("face err", e)
                        role = "Empleado" if name!="Desconocido" else "Desconocido"
                        evpath = ""
                        if name=="Desconocido":
                            fn = f"{self.cam_id}_{tid}_{int(time.time())}.jpg"
                            evpath = str(EVID_DIR / fn)
                            cv2.imwrite(evpath, frame)
                            # upload in bg
                            if UPLOAD_METHOD:
                                threading.Thread(target=safe_upload, args=(evpath,), daemon=True).start()
                        log_event(self.cam_id, tid, name, role, 0.0, [x1,y1,x2,y2], evpath)
                        evt = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "camera": self.cam_id, "track_id": tid, "person_name": name, "role": role, "bbox":[x1,y1,x2,y2], "evidence": evpath}
                        add_to_buffer(evt)
                        self.alert_signal.emit(evt)
                        last = self.last_alert.get(tid, 0)
                        if time.time() - last > ALERT_COOLDOWN and name=="Desconocido":
                            self.last_alert[tid] = time.time()
                            speak(f"Alerta: persona desconocida en cámara {self.cam_id}")
                            if TELEGRAM_TOKEN and TELEGRAM_CHAT:
                                threading.Thread(target=send_telegram, args=(f"Alerta desconocido en {self.cam_id}", evpath), daemon=True).start()
                except Exception as e:
                    print("Worker processing error:", e); traceback.print_exc()
            # emit frame for GUI (unprocessed)
            self.frame_signal.emit(frame, self.cam_id)
        if self.cap:
            self.cap.release()

    def stop(self):
        self.running = False

# ----------------------- Flask API -----------------------
api = Flask("cctv_api")

@api.route("/api/events")
def api_events():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM events ORDER BY id DESC LIMIT 500", conn)
    conn.close()
    return df.to_json(orient="records", force_ascii=False)

@api.route("/api/cameras")
def api_cameras():
    if CAM_CONF.exists():
        return CAM_CONF.read_text(encoding="utf-8")
    return jsonify({"buildings":[]})

def run_api():
    api.run(host="0.0.0.0", port=5000, threaded=True)

# ----------------------- GUI MainWindow -----------------------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CCTV Inteligente - FINAL")
        self.resize(1400, 900)
        # layout
        central = QtWidgets.QWidget(); vmain = QtWidgets.QVBoxLayout(central)
        top = QtWidgets.QHBoxLayout(); vmain.addLayout(top, 9)
        bottom = QtWidgets.QHBoxLayout(); vmain.addLayout(bottom, 2)
        # left: tree
        left = QtWidgets.QWidget(); left_l = QtWidgets.QVBoxLayout(left)
        left_l.addWidget(QtWidgets.QLabel("<b>Inventario de Cámaras</b>"))
        self.tree = QtWidgets.QTreeWidget(); self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self.on_tree_item)
        left_l.addWidget(self.tree)
        btn_add = QtWidgets.QPushButton("Agregar cámara"); btn_add.clicked.connect(self.add_camera_dialog)
        left_l.addWidget(btn_add)
        top.addWidget(left, 2)
        # center: stack (panopticon / single)
        self.stack = QtWidgets.QStackedWidget()
        self.panoptic = QtWidgets.QWidget(); self.grid = QtWidgets.QGridLayout(self.panoptic)
        self.stack.addWidget(self.panoptic)
        self.single = QtWidgets.QLabel("Seleccione una cámara"); self.single.setAlignment(QtCore.Qt.AlignCenter)
        self.stack.addWidget(self.single)
        top.addWidget(self.stack, 6)
        # right: controls & logs
        right = QtWidgets.QWidget(); r_l = QtWidgets.QVBoxLayout(right)
        self.btn_reload = QtWidgets.QPushButton("Recargar cámaras"); self.btn_reload.clicked.connect(self.load_cameras)
        r_l.addWidget(self.btn_reload)
        self.btn_summary = QtWidgets.QPushButton("Resumen 30s"); self.btn_summary.clicked.connect(self.show_summary)
        r_l.addWidget(self.btn_summary)
        self.btn_export = QtWidgets.QPushButton("Exportar events CSV"); self.btn_export.clicked.connect(self.export_events)
        r_l.addWidget(self.btn_export)
        r_l.addStretch()
        r_l.addWidget(QtWidgets.QLabel("<b>Consola</b>"))
        self.console = QtWidgets.QTextEdit(); self.console.setReadOnly(True)
        r_l.addWidget(self.console)
        top.addWidget(right, 2)
        self.setCentralWidget(central)
        # state
        self.workers = {}
        self.labels = {}
        # load cameras
        self.load_cameras()
        # start API and reporter
        threading.Thread(target=run_api, daemon=True).start()
        threading.Thread(target=self.reporter_loop, daemon=True).start()

    def reporter_loop(self):
        while True:
            try:
                subprocess.run([sys.executable, str(BASE/"reporter.py"), "once"], check=False)
            except Exception as e:
                print("Reporter loop error", e)
            time.sleep(8*3600)

    def load_cameras(self):
        # stop workers
        for w in list(self.workers.values()):
            try: w.stop()
            except: pass
        self.workers.clear(); self.labels.clear()
        # clear grid and tree
        self.tree.clear()
        while self.grid.count():
            it = self.grid.takeAt(0); wd = it.widget()
            if wd: wd.deleteLater()
        # read config
        if not CAM_CONF.exists():
            CAM_CONF.write_text(json.dumps({"buildings":[]}, indent=2), encoding="utf-8")
        cfg = json.loads(CAM_CONF.read_text(encoding="utf-8"))
        # populate
        for b in cfg.get("buildings", []):
            bnode = QtWidgets.QTreeWidgetItem([b.get("name","Building")])
            self.tree.addTopLevelItem(bnode)
            for room in b.get("rooms", []):
                rnode = QtWidgets.QTreeWidgetItem([room.get("name","Room")])
                bnode.addChild(rnode)
                for cam in room.get("cameras", []):
                    cam_node_label = f"{cam.get('name')} ({cam.get('source')})"
                    cnode = QtWidgets.QTreeWidgetItem([cam_node_label])
                    cnode.setData(0, QtCore.Qt.UserRole, cam)
                    rnode.addChild(cnode)
                    # grid widget
                    lbl = QtWidgets.QLabel(cam.get("name")); lbl.setStyleSheet("background:black;color:white"); lbl.setAlignment(QtCore.Qt.AlignCenter)
                    idx = self.grid.count(); r_idx = idx//2; c_idx = idx%2
                    self.grid.addWidget(lbl, r_idx, c_idx)
                    self.labels[cam.get("name")] = lbl
                    # start worker
                    src = cam.get("source")
                    src = int(src) if isinstance(src, str) and src.isdigit() else src
                    tmode = cam.get("tracker") or None
                    w = CameraWorker(cam.get("name"), src, tracker_mode=tmode)
                    w.frame_signal.connect(lambda f, l=lbl, name=cam.get("name"): self.on_frame(f,l,name))
                    w.alert_signal.connect(self.on_alert)
                    w.start()
                    self.workers[cam.get("name")] = w
        self.tree.expandAll()
        self.log("Cámaras cargadas.")

    def on_tree_item(self, item, col):
        cam = item.data(0, QtCore.Qt.UserRole)
        if cam:
            name = cam.get("name")
            lbl = self.labels.get(name)
            if lbl and lbl.pixmap():
                self.single.setPixmap(lbl.pixmap().scaled(self.single.width(), self.single.height(), QtCore.Qt.KeepAspectRatio))
                self.stack.setCurrentWidget(self.single)

    def on_frame(self, frame, label_widget, cam_name):
        if frame is None: return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h,w,ch = rgb.shape
        qimg = QtGui.QImage(rgb.data, w, h, ch*w, QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(qimg).scaled(480,320, QtCore.Qt.KeepAspectRatio)
        label_widget.setPixmap(pix)

    def on_alert(self, alert):
        line = f"[{alert.get('ts')}] {alert.get('camera')} - {alert.get('person_name')} ({alert.get('role')})"
        self.log(line)

    def log(self, text):
        self.console.append(text)
        print(text)

    def add_camera_dialog(self):
        bname, ok = QtWidgets.QInputDialog.getText(self, "Agregar edificio", "Nombre edificio")
        if not ok or not bname: return
        rname, ok = QtWidgets.QInputDialog.getText(self, "Agregar habitación", "Nombre habitación")
        if not ok or not rname: return
        cname, ok = QtWidgets.QInputDialog.getText(self, "Agregar cámara", "Nombre cámara")
        if not ok or not cname: return
        source, ok = QtWidgets.QInputDialog.getText(self, "Fuente", "0 para webcam o rtsp://...")
        if not ok or not source: return
        tracker_opt, ok = QtWidgets.QInputDialog.getItem(self, "Tracker", "Selecciona tracker para cámara", ["auto","bytetrack","deepsort"], 0, False)
        if not ok: tracker_opt = "auto"
        # load config and modify
        cfg = json.loads(CAM_CONF.read_text()) if CAM_CONF.exists() else {"buildings":[]}
        b = next((x for x in cfg["buildings"] if x["name"]==bname), None)
        if not b:
            b = {"name": bname, "rooms": []}; cfg["buildings"].append(b)
        r = next((x for x in b["rooms"] if x["name"]==rname), None)
        if not r:
            r = {"name": rname, "cameras": []}; b["rooms"].append(r)
        cam_obj = {"name": cname, "source": int(source) if source.isdigit() else source, "tracker": None if tracker_opt=="auto" else tracker_opt}
        r["cameras"].append(cam_obj)
        # version
        ts = time.strftime("%Y%m%d_%H%M%S")
        if CAM_CONF.exists():
            (CONFIG_HISTORY / f"cameras_{ts}.json").write_text(CAM_CONF.read_text(), encoding="utf-8")
        CAM_CONF.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        self.log(f"Cámara añadida: {cname} {source}")
        self.load_cameras()

    def show_summary(self):
        s = summarize_buffer()
        QtWidgets.QMessageBox.information(self, "Resumen 30s", s)

    def export_events(self):
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM events ORDER BY id DESC LIMIT 10000", conn)
        conn.close()
        out = REPORTS_DIR / f"events_export_{int(time.time())}.csv"
        df.to_csv(out, index=False)
        QtWidgets.QMessageBox.information(self, "Exportado", f"Events exportados a {out}")

    def closeEvent(self, event):
        for w in list(self.workers.values()):
            try: w.stop()
            except: pass
        super().closeEvent(event)

# ----------------------- Entrypoint -----------------------
def main():
    reload_known_faces()
    ensure_db()
    app = QtWidgets.QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    # start API thread
    threading.Thread(target=run_api, daemon=True).start()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()