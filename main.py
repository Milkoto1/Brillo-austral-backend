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
                {total_item} m2
            </td>
        </tr>
        """

    attachments = []
    fotos_html = ""
    
    for idx, i in enumerate(reporte.items):
        if i.foto_base64 and "base64," in i.foto_base64:
            # Separamos el encabezado de los datos reales de la imagen
            content_type, b64_data = i.foto_base64.split("base64,")
            filename = f"foto_{idx+1}.jpg"
            
            # Agregamos como adjunto oficial (CID)
            attachments.append({
                "content": b64_data,
                "filename": filename,
                "content_id": filename 
            })
            
            # El HTML ahora llama al CID, que es el metodo estandar para ver fotos en Gmail
            fotos_html += f"""
            <div style="margin-top: 25px; text-align: center; border-top: 1px solid #eee; padding-top: 15px;">
                <p style="font-size: 12px; color: #555; margin-bottom: 8px; font-weight: bold;">FOTO #{idx+1} - {i.nombre_item.upper()}</p>
                <img src="cid:{filename}" style="width: 100%; max-width: 450px; height: auto; border-radius: 8px; display: block; margin: 0 auto;" />
            </div>
            """

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.5; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 600px; margin: auto; border: 1px solid #ddd; border-radius: 12px; overflow: hidden; background-color: #ffffff;">
            <div style="background-color: #005f8d; color: white; padding: 25px; text-align: center;">
                <h1 style="margin: 0; font-size: 20px; text-transform: uppercase;">Reporte de Servicio</h1>
                <p style="margin: 5px 0 0 0; font-size: 13px; opacity: 0.8;">Brillo Austral PV - Puerto Varas</p>
            </div>
            
            <div style="padding: 25px;">
                <div style="margin-bottom: 15px; font-size: 14px;">
                    <p style="margin: 4px 0;"><strong>Cliente:</strong> {reporte.cliente_nombre}</p>
                    <p style="margin: 4px 0;"><strong>Direccion:</strong> {reporte.direccion}</p>
                    <p style="margin: 4px 0;"><strong>Trabajador:</strong> {reporte.usuario_emisor}</p>
                    {f'<p style="margin: 4px 0;"><strong>Telefono:</strong> {reporte.telefono}</p>' if reporte.telefono else ''}
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <thead>
                        <tr style="background-color: #f2f2f2;">
                            <th style="padding: 10px; text-align: left; border-bottom: 2px solid #005f8d; font-size: 12px;">ITEM</th>
                            <th style="padding: 10px; text-align: center; border-bottom: 2px solid #005f8d; font-size: 12px;">MEDIDAS</th>
                            <th style="padding: 10px; text-align: center; border-bottom: 2px solid #005f8d; font-size: 12px;">CARA</th>
                            <th style="padding: 10px; text-align: right; border-bottom: 2px solid #005f8d; font-size: 12px;">TOTAL</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_tabla}
                    </tbody>
                </table>
                
                <div style="margin-top: 20px; padding: 12px; background-color: #0f172a; color: white; text-align: right; border-radius: 8px;">
                    <span style="font-size: 15px;">TOTAL SUPERFICIE: </span>
                    <span style="font-size: 20px; font-weight: bold; margin-left: 8px;">{total_final} m2</span>
                </div>

                {fotos_html}
            </div>
            
            <div style="background-color: #eeeeee; padding: 12px; text-align: center; font-size: 10px; color: #888;">
                Generado por la aplicacion Brillo Austral PV.
            </div>
        </div>
    </body>
    </html>
    """

    try:
        resend.Emails.send({
            "from": "Brillo Austral <onboarding@resend.dev>",
            "to": "brilloaustralpv@gmail.com",
            "subject": f"Reporte: {reporte.cliente_nombre} ({total_final} m2)",
            "html": html_content,
            "attachments": attachments
        })
        return {"status": "ok"}
    except Exception as e:
        print(f"Error Resend: {{e}}")
        return {"status": "error"}
