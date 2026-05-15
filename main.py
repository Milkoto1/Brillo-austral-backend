import os
import resend
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
    foto_base64: Optional[str] = None # Agregado para recibir la foto del celular

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

    # 1. Creamos las filas de la tabla
    filas_tabla = ""
    for idx, i in enumerate(reporte.items):
        m2 = round(i.ancho * i.alto, 2)
        total_item = m2 * 2 if i.doble_cara else m2
        comentario_texto = f"<br><i style='color: #666;'>Nota: {i.comentario}</i>" if i.comentario else ""
        
        filas_tabla += f"""
        <tr style="border-bottom: 1px solid #eee;">
            <td style="padding: 10px; border-bottom: 1px solid #eee;">
                <b>{i.nombre_item} #{idx+1}</b>{comentario_texto}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">
                {i.ancho} x {i.alto}m
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">
                {'Doble (x2)' if i.doble_cara else 'Simple'}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right; font-weight: bold;">
                {total_item} m²
            </td>
        </tr>
        """

    # 2. Generamos el HTML de las fotografías
    fotos_html = ""
    for idx, i in enumerate(reporte.items):
        if i.foto_base64:
            fotos_html += f"""
            <div style="margin-top: 20px; text-align: center; border-top: 1px solid #eee; padding-top: 10px;">
                <p style="font-size: 14px; color: #666; margin-bottom: 10px;">Foto ítem #{idx+1} ({i.nombre_item})</p>
                <img src="{i.foto_base64}" style="max-width: 100%; border-radius: 8px; border: 1px solid #ddd; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />
            </div>
            """

    # 3. Diseño profesional del HTML Final
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 10px; overflow: hidden;">
            <div style="background-color: #005f8d; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">REPORTE DE SERVICIO</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Brillo Austral PV</p>
            </div>
            
            <div style="padding: 20px;">
                <p style="margin: 0 0 10px 0;"><strong>Cliente:</strong> {reporte.cliente_nombre}</p>
                <p style="margin: 0 0 10px 0;"><strong>Dirección:</strong> {reporte.direccion}</p>
                <p style="margin: 0 0 10px 0;"><strong>Trabajador:</strong> {reporte.usuario_emisor}</p>
                {f'<p style="margin: 0 0 10px 0;"><strong>Teléfono:</strong> {reporte.telefono}</p>' if reporte.telefono else ''}
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
                            <th style="padding: 10px; text-align: left; border-bottom: 2px solid #005f8d;">Ítem</th>
                            <th style="padding: 10px; text-align: center; border-bottom: 2px solid #005f8d;">Medidas</th>
                            <th style="padding: 10px; text-align: center; border-bottom: 2px solid #005f8d;">Cara</th>
                            <th style="padding: 10px; text-align: right; border-bottom: 2px solid #005f8d;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_tabla}
                    </tbody>
                </table>
                
                <div style="margin-top: 30px; padding: 15px; background-color: #0f172a; color: white; text-align: right; border-radius: 8px;">
                    <span style="font-size: 18px;">TOTAL SUPERFICIE: </span>
                    <span style="font-size: 24px; font-weight: bold; margin-left: 10px;">{total_final} m²</span>
                </div>

                {fotos_html}

            </div>
            
            <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 12px; color: #777;">
                Este es un reporte automático generado por la App de Brillo Austral PV.
            </div>
        </div>
    </body>
    </html>
    """

    try:
        resend.Emails.send({
            "from": "Brillo Austral <onboarding@resend.dev>",
            "to": "brilloaustralpv@gmail.com",
            "subject": f"✅ Reporte: {reporte.cliente_nombre} ({total_final} m2)",
            "html": html_content
        })
        return {"status": "ok"}
    except Exception as e:
        print(f"Error Resend: {e}")
        return {"status": "error"}
