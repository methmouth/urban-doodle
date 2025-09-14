#!/usr/bin/env python3
"""
db_init.py - Inicializador de la base de datos people.db

Crea tablas:
 - persons (id, name, role, face_path, created_at)
 - events  (id, ts, camera, track_id, person_name, role, confidence, bbox, evidence)
"""
import sqlite3
import os
from pathlib import Path

DB = Path(__file__).parent / "people.db"

def create_db():
    if DB.exists():
        print("⚠ people.db ya existe. Se renombra a people.db.bak")
        DB.rename(DB.with_suffix(".db.bak"))

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS persons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        role TEXT,
        face_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT,
        camera TEXT,
        track_id TEXT,
        person_name TEXT,
        role TEXT,
        confidence REAL,
        bbox TEXT,
        evidence TEXT
    )
    """)

    # Insertar ejemplos ligeros sin face_path
    try:
        c.execute("INSERT OR IGNORE INTO persons (name, role) VALUES (?, ?)", ("Juan Perez", "Empleado"))
        c.execute("INSERT OR IGNORE INTO persons (name, role) VALUES (?, ?)", ("Maria Lopez", "Empleado"))
        c.execute("INSERT OR IGNORE INTO persons (name, role) VALUES (?, ?)", ("Proveedor S.A.", "Proveedor"))
        conn.commit()
    except Exception as e:
        print("Error insertando ejemplos:", e)

    conn.close()
    print("✅ Base de datos creada en:", DB)

if __name__ == "__main__":
    create_db()