import os
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
    comentario: Optional[str] = None
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
    # IMPORTANTE: Aquí lee la clave de Render
    password = os.environ.get("PASSWORD_GMAIL") 
    
    if not password:
        print("ERROR: No se configuró PASSWORD_GMAIL en Render")
        return False

    msg = MIMEMultipart()
    msg['From'] = remitente
    msg['To'] = remitente
    msg['Subject'] = f"REPORTE: {reporte.cliente_nombre} - {total_final} m2"

    # Construcción del HTML
    filas = ""
    for idx, i in enumerate(reporte.items):
        m2 = round(i.ancho * i.alto, 2)
        total_i = m2 * 2 if i.doble_cara else m2
        filas += f"<li>{i.nombre_item}: {total_i} m2 {'(Doble)' if i.doble_cara else ''}</li>"

    msg.attach(MIMEText(f"<html><body><h2>Resumen</h2><ul>{filas}</ul><h3>Total: {total_final} m2</h3></body></html>", 'html'))

    # Adjuntar fotos
    for idx, i in enumerate(reporte.items):
        if i.foto_base64 and "base64," in i.foto_base64:
            try:
                header, encoded = i.foto_base64.split("base64,")
                img = MIMEImage(base64.b64decode(encoded))
                img.add_header('Content-Disposition', 'attachment', filename=f"foto_{idx+1}.jpg")
                msg.attach(img)
            except: pass

    try:
        # Forzamos la conexión a smtp.gmail.com
        # Usamos el puerto 465 (SSL) que es el estándar para nubes
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15)
        
        # Saludamos al servidor
        server.ehlo()
        
        # Iniciamos sesión
        server.login(remitente, password)
        
        # Enviamos
        server.sendmail(remitente, remitente, msg.as_string())
        
        server.quit()
        return True
    except Exception as e:
        # Esto nos dirá en los logs exactamente qué pasó
        print(f"Error SMTP detallado: {type(e).__name__} - {e}")
        return False

@app.post("/reporte")
async def procesar(reporte: ReporteServicio):
    total = sum((i.ancho * i.alto * (2 if i.doble_cara else 1)) for i in reporte.items)
    exito = enviar_correo_gmail(reporte, round(total, 2))
    return {"status": "ok" if exito else "error"}
