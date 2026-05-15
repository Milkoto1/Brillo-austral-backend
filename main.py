import os
import resend # <--- Nuevo aliado
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
resend.api_key = os.environ.get("RESEND_API_KEY")

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

class ReporteServicio(BaseModel):
    cliente_nombre: str
    direccion: str
    email_cliente: str
    usuario_emisor: str
    telefono: Optional[str] = None
    items: List[ItemServicio]

@app.post("/reporte")
async def procesar(reporte: ReporteServicio):
    total = sum((i.ancho * i.alto * (2 if i.doble_cara else 1)) for i in reporte.items)
    total_final = round(total, 2)

    # Construimos el cuerpo del correo
    filas = "".join([f"<li>{i.nombre_item}: {i.ancho}x{i.alto}m ({'Doble' if i.doble_cara else 'Simple'}) - {i.comentario if i.comentario else ''}</li>" for i in reporte.items])
    
    html_content = f"""
    <h1>Reporte Brillo Austral PV</h1>
    <p><b>Cliente:</b> {reporte.cliente_nombre}<br>
    <b>Dirección:</b> {reporte.direccion}<br>
    <b>Trabajador:</b> {reporte.usuario_emisor}</p>
    <ul>{filas}</ul>
    <h2>TOTAL: {total_final} m²</h2>
    """

    try:
        # Enviamos usando Resend
        resend.Emails.send({
            "from": "Brillo Austral <onboarding@resend.dev>",
            "to": "brilloaustralpv@gmail.com", # <--- Tu correo donde recibes
            "subject": f"Nuevo Reporte: {reporte.cliente_nombre}",
            "html": html_content
        })
        return {"status": "ok"}
    except Exception as e:
        print(f"Error Resend: {e}")
        return {"status": "error"}
