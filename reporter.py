#!/usr/bin/env python3
"""
reporter.py - Generador de reportes periódicos y export CSV/PDF/HTML

Usos:
  python reporter.py once      # generar un reporte ahora
  python reporter.py cron      # loop que genera cada 8 horas (no recomendable en foreground)
"""
import sqlite3
import time
import sys
from pathlib import Path
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import matplotlib.pyplot as plt
from jinja2 import Template

BASE = Path(__file__).parent
DB = BASE / "people.db"
OUT = BASE / "reports"
OUT.mkdir(parents=True, exist_ok=True)

def fetch_events(limit=1000):
    conn = sqlite3.connect(DB)
    df = pd.read_sql("SELECT * FROM events ORDER BY id DESC LIMIT ?", conn, params=(limit,))
    conn.close()
    return df

def gen_pdf(df, outpath):
    doc = SimpleDocTemplate(str(outpath), pagesize=A4)
    styles = getSampleStyleSheet()
    elems = []
    elems.append(Paragraph("CCTV Inteligente — Reporte", styles['Title']))
    elems.append(Spacer(1, 8))

    if df.empty:
        elems.append(Paragraph("No se encontraron eventos.", styles['Normal']))
    else:
        # Resumen por rol
        roles = df['role'].fillna('Desconocido').value_counts()
        elems.append(Paragraph("Resumen por rol:", styles['Heading2']))
        for r, v in roles.items():
            elems.append(Paragraph(f"{r}: {v}", styles['Normal']))
        elems.append(Spacer(1, 8))

        # Gráfica simple (guardar temp)
        plt.figure(figsize=(6,3))
        roles.plot(kind='bar')
        plt.tight_layout()
        tmp_plot = OUT / "plot_tmp.png"
        plt.savefig(tmp_plot)
        plt.close()
        elems.append(Image(str(tmp_plot), width=450, height=200))
        elems.append(Spacer(1, 12))

        # Tabla con primeras 50 filas
        sample = df.head(50)
        data = [list(sample.columns)] + sample.values.tolist()
        tbl = Table(data)
        tbl.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)
        ]))
        elems.append(tbl)

    doc.build(elems)

def gen_html(df, outpath):
    tpl = Template("""
    <html><head><meta charset="utf-8"><title>Reporte CCTV</title>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css"/>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
    </head><body>
    <h1>Reporte CCTV</h1><p>Generado: {{ ts }}</p>
    {{ table|safe }}
    <script>$(document).ready(()=>$('#t').DataTable());</script>
    </body></html>
    """)
    html = tpl.render(ts=time.strftime("%Y-%m-%d %H:%M:%S"), table=df.to_html(index=False, table_id="t"))
    outpath.write_text(html, encoding="utf-8")

def generate_all():
    df = fetch_events(limit=5000)
    ts = time.strftime("%Y%m%d_%H%M%S")
    pdf_path = OUT / f"report_{ts}.pdf"
    html_path = OUT / f"report_{ts}.html"
    gen_pdf(df, pdf_path)
    gen_html(df, html_path)
    print("Reportes generados:", pdf_path, html_path)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "once"
    if mode == "once":
        generate_all()
    else:
        # loop modo cron (cada 8 horas)
        while True:
            generate_all()
            time.sleep(8*3600)