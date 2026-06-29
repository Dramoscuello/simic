from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.config import get_db
from app.core.websocket_manager import manager
from app.api.deps import get_current_active_user
from app.models.usuario import Usuario
from app.models.respuesta_estudiante import RespuestaEstudiante
from app.models.simulacro import Simulacro
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(
    prefix="/monitoreo",
    tags=["monitoreo"]
)

# -----------------------------------------------------------------------------
# WEBSOCKETS
# -----------------------------------------------------------------------------

@router.websocket("/ws/alertas/{institucion_id}")
async def websocket_alertas_endpoint(
    websocket: WebSocket,
    institucion_id: int,
    # token: str -- En WS es complicado pasar headers, suele ir en query param ?token=...
    # Se valida dentro del connect o usando un dependency especial
):
    """
    Canal de ESCUCHA para Admins.
    Se conectan aquí para recibir notificaciones en tiempo real sobre su institución.
    """
    # TODO: Validar token del admin para seguridad. Por ahora simple.
    await manager.connect(websocket, institucion_id)
    try:
        while True:
            # Mantener conexión viva y escuchar comandos del admin (opcional)
            data = await websocket.receive_text()
            # Si el admin envía algo como "ping", responder "pong"
            # await websocket.send_text(f"Admin dice: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, institucion_id)


@router.websocket("/ws/reportar/{institucion_id}")
async def websocket_reportar_endpoint(
    websocket: WebSocket,
    institucion_id: int
):
    """
    Canal de EMISIÓN para Estudiantes.
    El frontend del estudiante se conecta aquí para enviar eventos 'focus_lost'.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # Estructura esperada data:
            # {
            #   "tipo": "focus_lost",
            #   "estudiante_id": 123,
            #   "estudiante_nombre": "Juan",
            #   "simulacro_id": 45,
            #   "simulacro_titulo": "Matemáticas 10-1",
            #   "timestamp": "..."
            # }
            
            tipo = data.get("tipo")
            if tipo == "focus_lost":
                # Reenviar al canal de admins de esa institución
                payload = {
                    "evento": "fraude_detectado",
                    "data": data,
                    "server_time": datetime.now().isoformat()
                }
                print(f"🚨 Alerta Fraude recibida: {data.get('estudiante_nombre')} - Inst {institucion_id}")
                await manager.broadcast_to_institution(payload, institucion_id)
                
    except WebSocketDisconnect:
        print(f"Estudiante desconectado del canal de reporte Inst {institucion_id}")


# -----------------------------------------------------------------------------
# REST API (Acciones)
# -----------------------------------------------------------------------------

class FraudeRequest(BaseModel):
    confirmado: bool = True
    motivo: str = "Pérdida de foco detectada por monitor"

@router.put("/respuestas/{respuesta_id}/fraude")
def marcar_fraude(
    respuesta_id: int,
    request: FraudeRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Marca un intento de simulacro como FRAUDE.
    - Pone nota 0.
    - Activa flag fraude=True.
    """
    # Validar permisos (Solo Admin Institución o Super Admin)
    allowed_roles = ['admin']
    if not current_user.rol or current_user.rol.nombre not in allowed_roles:
         raise HTTPException(status_code=403, detail="No autorizado para sancionar fraude")

    respuesta = db.query(RespuestaEstudiante).get(respuesta_id)
    if not respuesta:
        raise HTTPException(status_code=404, detail="Respuesta no encontrada")

    # Validar que pertenezca a su institución
    is_super = current_user.rol.nombre == 'admin'
    if not is_super and respuesta.institucion_id != current_user.institucion_id:
        raise HTTPException(status_code=403, detail="No puede sancionar estudiantes de otra institución")

    # Aplicar Sanción
    respuesta.fraude = request.confirmado
    
    if request.confirmado:
        # Anular nota
        respuesta.puntaje_total = 0.0
        # Invalidar/Borrar informes generados
        respuesta.informe_generado = False
        respuesta.informe_url = None
        respuesta.analisis_ia = None # "Asignar a null" solicitado
        
        # Opcional: Agregar motivo en algun log o metadata si existiera campo
    
    db.commit()
    db.refresh(respuesta)
    
    return {"status": "ok", "fraude": respuesta.fraude, "puntaje": respuesta.puntaje_total}
