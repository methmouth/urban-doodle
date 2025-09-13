import sqlite3, pandas as pd
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

DB_PATH = "people.db"

def generar_reporte():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM events ORDER BY id DESC LIMIT 200", conn)
    conn.close()

    fname = f"reports/reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(fname)
    styles = getSampleStyleSheet()
    elems = [Paragraph("Reporte de Eventos CCTV", styles['Title']), Spacer(1,20)]
    for _, row in df.iterrows():
        elems.append(Paragraph(f"{row['timestamp']} — {row['camera']} — {row['person']}", styles['Normal']))
    doc.build(elems)
    print(f"✅ Reporte generado: {fname}")

if __name__ == "__main__":
    generar_reporte()