from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ItemServicio(BaseModel):
    nombre_item: str
    ancho: float
    alto: float
    doble_cara: bool
    comentario: Optional[str] = None # Nuevo campo
    foto_base64: Optional[str] = None

class ReporteServicio(BaseModel):
    cliente_nombre: str
    direccion: str
    email_cliente: str
    usuario_emisor: str
    telefono: Optional[str] = None
    items: List[ItemServicio]

def enviar_correo_gmail(reporte, total_final):
    remitente = "brilloaustralpv@gmail.com"
    password = "tvdl imxx lqex byph" # <--- TU CLAVE AQUÍ
    
    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = remitente
    msg['Subject'] = f"REPORTE: {reporte.cliente_nombre} - Por {reporte.usuario_emisor}"

    filas_items = ""
    for idx, i in enumerate(reporte.items):
        m2 = round(i.ancho * i.alto, 2)
        total_item = m2 * 2 if i.doble_cara else m2
        comentario_html = f"<p style='margin:0; font-size:12px; color:#666;'>Nota: {i.comentario}</p>" if i.comentario else ""
        
        filas_items += f"""
        <li style="margin-bottom: 15px;">
            <b>{i.nombre_item} #{idx+1}</b>: {i.ancho}x{i.alto}m ({'Doble cara' if i.doble_cara else 'Simple'}) - <b>{total_item} m²</b>
            {comentario_html}
        </li>"""

    cuerpo_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: #005f8d; color: white; padding: 20px; border-radius: 10px;">
                <h1 style="margin: 0;">BRILLO AUSTRAL PV</h1>
                <p>Generado por: <b>{reporte.usuario_emisor}</b></p>
            </div>
            <p><b>Cliente:</b> {reporte.cliente_nombre}<br>
            <b>Dirección:</b> {reporte.direccion}<br>
            <b>Teléfono:</b> {reporte.telefono if reporte.telefono else 'N/A'}</p>
            <hr>
            <h3>Detalle del Servicio:</h3>
            <ul>{filas_items}</ul>
            <h2 style="background: #0f172a; color: white; padding: 15px; text-align: center; border-radius: 8px;">TOTAL: {total_final} m²</h2>
        </body>
    </html>
    """
    msg.attach(MIMEText(cuerpo_html, 'html'))

    for idx, i in enumerate(reporte.items):
        if i.foto_base64 and "base64," in i.foto_base64:
            try:
                header, encoded = i.foto_base64.split("base64,")
                foto_data = base64.b64decode(encoded)
                imagen = MIMEImage(foto_data)
                imagen.add_header('Content-Disposition', 'attachment', filename=f"item_{idx+1}.jpg")
                msg.attach(imagen)
            except: pass

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, remitente, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

@app.post("/reporte")
async def procesar(reporte: ReporteServicio):
    total = sum((i.ancho * i.alto * (2 if i.doble_cara else 1)) for i in reporte.items)
    exito = enviar_correo_gmail(reporte, round(total, 2))
    return {"status": "ok" if exito else "error", "total": round(total, 2)}