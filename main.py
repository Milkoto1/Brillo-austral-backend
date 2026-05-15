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
    foto_base64: Optional[str] = None

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

    # 1. Filas de la tabla
    filas_tabla = ""
    for idx, i in enumerate(reporte.items):
        m2 = round(i.ancho * i.alto, 2)
        total_item = m2 * 2 if i.doble_cara else m2
        comentario_texto = f"<br><i style='color: #666; font-size: 11px;'>Nota: {i.comentario}</i>" if i.comentario else ""
        
        filas_tabla += f"""
        <tr style="border-bottom: 1px solid #eee;">
            <td style="padding: 10px; border-bottom: 1px solid #eee;">
                <span style="font-size: 14px;"><b>{i.nombre_item} #{idx+1}</b></span>{comentario_texto}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center; font-size: 14px;">
                {i.ancho} x {i.alto}m
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center; font-size: 14px;">
                {'Doble' if i.doble_cara else 'Simple'}
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right; font-weight: bold; font-size: 14px;">
                {total_item} m²
            </td>
        </tr>
        """

    # 2. HTML de las fotos (Ajustado para mejor visualización)
    fotos_html = ""
    for idx, i in enumerate(reporte.items):
        if i.foto_base64:
            fotos_html += f"""
            <div style="margin-top: 30px; text-align: center; border-top: 1px solid #eee; padding-top: 20px;">
                <p style="font-size: 13px; color: #555; margin-bottom: 10px; font-weight: bold;">FOTO ÍTEM #{idx+1} - {i.nombre_item.upper()}</p>
                <img src="{i.foto_base64}" alt="Foto {idx+1}" style="width: 100%; max-width: 500px; height: auto; border-radius: 10px; border: 1px solid #ccc; display: block; margin: 0 auto;" />
            </div>
            """

    # 3. Diseño HTML Final
    html_content = f"""
    <html>
    <body style="font-family: 'Helvetica', Arial, sans-serif; color: #333; line-height: 1.5; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 12px; overflow: hidden; background-color: #ffffff; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
            <div style="background-color: #005f8d; color: white; padding: 25px; text-align: center;">
                <h1 style="margin: 0; font-size: 22px; letter-spacing: 1px;">REPORTE DE SERVICIO</h1>
                <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.8;">Brillo Austral PV - Puerto Varas</p>
            </div>
            
            <div style="padding: 25px;">
                <div style="margin-bottom: 20px; font-size: 14px;">
                    <p style="margin: 4px 0;"><strong>Cliente:</strong> {reporte.cliente_nombre}</p>
                    <p style="margin: 4px 0;"><strong>Dirección:</strong> {reporte.direccion}</p>
                    <p style="margin: 4px 0;"><strong>Trabajador:</strong> {reporte.usuario_emisor}</p>
                    {f'<p style="margin: 4px 0;"><strong>Teléfono:</strong> {reporte.telefono}</p>' if reporte.telefono else ''}
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <thead>
                        <tr style="background-color: #f2f2f2;">
                            <th style="padding: 12px 10px; text-align: left; border-bottom: 2px solid #005f8d; font-size: 13px;">ÍTEM</th>
                            <th style="padding: 12px 10px; text-align: center; border-bottom: 2px solid #005f8d; font-size: 13px;">MEDIDAS</th>
                            <th style="padding: 12px 10px; text-align: center; border-bottom: 2px solid #005f8d; font-size: 13px;">CARA</th>
                            <th style="padding: 12px 10px; text-align: right; border-bottom: 2px solid #005f8d; font-size: 13px;">TOTAL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_tabla}
                    </tbody>
                </table>
                
                <div style="margin-top: 25px; padding: 15px; background-color: #0f172a; color: white; text-align: right; border-radius: 8px;">
                    <span style="font-size: 16px;">TOTAL SUPERFICIE: </span>
                    <span style="font-size: 22px; font-weight: bold; margin-left: 10px;">{total_final} m²</span>
                </div>

                {fotos_html}
            </div>
            
            <div style="background-color: #eeeeee; padding: 15px; text-align: center; font-size: 11px; color: #888;">
                Generado automáticamente por la aplicación Brillo Austral PV.
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
