import sqlite3

conn = sqlite3.connect("people.db")
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS persons(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    type TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS events(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    camera TEXT,
    person TEXT
)""")

# Ejemplo inicial
c.execute("INSERT INTO persons(name,type) VALUES('Juan Pérez','Empleado')")
c.execute("INSERT INTO persons(name,type) VALUES('Cliente X','Cliente')")

conn.commit()
conn.close()
print("✅ Base de datos inicializada.")