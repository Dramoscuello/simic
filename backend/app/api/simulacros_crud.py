from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import ValidationError
from datetime import datetime, timezone

from app.api.deps import get_current_active_user
from app.database.config import get_db
from app.models.simulacro import Simulacro
from app.models.respuesta_estudiante import RespuestaEstudiante
from app.models.reporte_grupal import ReporteGrupal
from app.models.usuario import Usuario
from app.models.pregunta_usada import PreguntaUsada
from app.models.sede import Sede
from app.schemas.simulacro import Simulacro as SimulacroSchema, SimulacroCreate, SimulacroUpdate, SimulacroResetRequest
from app.schemas.simulacro_v2 import Simulacro as SimulacroV2
from app.services.preguntas_usadas_service import registrar_preguntas_usadas
from app.services.qa_gate2_service import Gate2Validator
from app.services.qa_gate3_service import Gate3Deduplicator
from app.services.qa_gate4_service import Gate4RenderValidator
from app.services.qa_gate5_service import Gate5SemanticValidator
from app.services.qa_gate6_service import Gate6LogicValidator

from app.api.simulacros_router import router

@router.get("/", response_model=List[SimulacroSchema])
def read_simulacros(
    skip: int = 0, 
    limit: int = 100, 
    estado: str = 'pendiente',  # pendiente, realizado, todos
    institucion_id: Optional[int] = None,  # Filtro por institución (superadmin)
    sede_id: Optional[int] = None,  # Filtro por sede
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Lista simulacros con filtros opcionales.
    - Estudiantes: ven solo simulacros de su institución, filtrados por estado (pendiente/realizado)
    - Super Admin: ve todos, puede filtrar por institucion_id
    - Admin Institución: ve solo los de su institución
    """
    rol_nombre = current_user.rol.nombre if current_user.rol else ""
    
    if rol_nombre == 'estudiante':
        intentos_activos = db.query(RespuestaEstudiante.simulacro_id)\
                        .filter(RespuestaEstudiante.usuario_id == current_user.id)\
                        .filter(RespuestaEstudiante.fecha_finalizacion.is_(None))\
                        .filter(RespuestaEstudiante.anulado.is_(False))\
                        .all()
        intentos_activos_ids = {r[0] for r in intentos_activos}

        respondidos = db.query(RespuestaEstudiante.simulacro_id)\
                        .filter(RespuestaEstudiante.usuario_id == current_user.id)\
                        .filter(RespuestaEstudiante.fecha_finalizacion.isnot(None))\
                        .filter(RespuestaEstudiante.anulado.is_(False))\
                        .all()
        respondidos_ids = [r[0] for r in respondidos]
        
        query = db.query(Simulacro).filter(Simulacro.activo == True)
        
        if current_user.institucion_id:
            query = query.filter(Simulacro.institucion_id == current_user.institucion_id)

        if sede_id:
            query = query.filter(Simulacro.sede_id == sede_id)

        if estado == 'pendiente':
            if respondidos_ids:
                query = query.filter(Simulacro.id.notin_(respondidos_ids))
        elif estado == 'realizado':
            if respondidos_ids:
                query = query.filter(Simulacro.id.in_(respondidos_ids))
            else:
                return []
        
        simulacros = query.offset(skip).limit(limit).all()
    elif rol_nombre == 'docente':
        query = db.query(Simulacro)
        if current_user.institucion_id:
            query = query.filter(Simulacro.institucion_id == current_user.institucion_id)
        if current_user.sede_id:
            query = query.filter(Simulacro.sede_id == current_user.sede_id)
        if estado == 'activo':
             query = query.filter(Simulacro.estado == 'activo')
        elif estado == 'finalizado':
             query = query.filter(Simulacro.estado == 'finalizado')
        simulacros = query.order_by(Simulacro.created_at.desc()).offset(skip).limit(limit).all()
    elif rol_nombre == 'admin':
        query = db.query(Simulacro)
        if current_user.institucion_id:
            query = query.filter(Simulacro.institucion_id == current_user.institucion_id)
        else:
            if institucion_id:
                query = query.filter(Simulacro.institucion_id == institucion_id)
        if sede_id:
            query = query.filter(Simulacro.sede_id == sede_id)
        if current_user.institucion_id:
            if estado == 'activo':
                 query = query.filter(Simulacro.estado == 'activo')
            elif estado == 'finalizado':
                 query = query.filter(Simulacro.estado == 'finalizado')
        simulacros = query.order_by(Simulacro.created_at.desc()).offset(skip).limit(limit).all()
        
    # Enriquecer con info del creador
    creator_ids = [s.created_by for s in simulacros if s.created_by]
    creators_info = {}
    if creator_ids:
        creators_db = db.query(Usuario).filter(Usuario.id.in_(creator_ids)).all()
        for u in creators_db:
            rol_nombre_creator = u.rol.nombre if u.rol else "desconocido"
            if rol_nombre_creator == "admin":
                creators_info[u.id] = {"nombre": "SuperAdmin", "tipo": "superadmin"}
            else:
                # Para admin, mostrar nombre de su institución
                inst_nombre = u.institucion.nombre if u.institucion else "Institución"
                creators_info[u.id] = {"nombre": inst_nombre, "tipo": "institucion"}
    
    # Nombres de sedes
    sede_ids = [s.sede_id for s in simulacros if s.sede_id]
    sedes_info = {}
    if sede_ids:
        sedes_db = db.query(Sede).filter(Sede.id.in_(sede_ids)).all()
        for sede in sedes_db:
            sedes_info[sede.id] = sede.nombre

    # Construir respuesta enriquecida
    result = []
    for sim in simulacros:
        sim_dict = {
            "id": sim.id,
            "titulo": sim.titulo,
            "descripcion": sim.descripcion,
            "area": sim.area,
            "version": sim.version,
            "contenido": sim.contenido,
            "total_preguntas": sim.total_preguntas,
            "duracion_minutos": sim.duracion_minutos,
            "institucion_id": sim.institucion_id,
            "sede_id": sim.sede_id,
            "sede_nombre": sedes_info.get(sim.sede_id) if sim.sede_id else None,
            "estado": sim.estado,
            "activo": sim.activo,
            "fecha_disponible_desde": sim.fecha_disponible_desde,
            "fecha_disponible_hasta": sim.fecha_disponible_hasta,
            "mi_intento_activo": sim.id in intentos_activos_ids if rol_nombre == 'estudiante' else False,
            "created_by": sim.created_by,
            "created_by_nombre": creators_info.get(sim.created_by, {}).get("nombre") if sim.created_by else None,
            "created_by_tipo": creators_info.get(sim.created_by, {}).get("tipo") if sim.created_by else None,
            "created_at": sim.created_at,
            "updated_at": sim.updated_at
        }
        result.append(sim_dict)
    
    return result

@router.post("/", response_model=SimulacroSchema)
def create_simulacro(
    simulacro: SimulacroCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Crea un nuevo simulacro y registra automáticamente las preguntas en preguntas_usadas.
    Solo Super Admin puede crear simulacros.
    """
    # Validar permisos
    rol_nombre = current_user.rol.nombre if current_user.rol else ""
    if rol_nombre != 'admin':
        raise HTTPException(status_code=403, detail="Solo el Super Admin puede crear simulacros")
    
    # --- GATE 1: VALIDACIÓN ESTRUCTURAL (Simulacro V2) ---
    try:
        contenido = simulacro.contenido
        if isinstance(contenido, str):
            import json
            contenido = json.loads(contenido)
        SimulacroV2(**contenido)
    except ValidationError as e:
        error_msg = f"Error de Validación Estructural (V2): {e.errors()[0]['msg']} en {e.errors()[0]['loc']}"
        raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error procesando JSON de contenido: {str(e)}")
    
    # --- GATE 2: REGLAS DE NEGOCIO ---
    qa_result = Gate2Validator.validar_simulacro(contenido)
    if not qa_result.passed:
        raise HTTPException(
            status_code=400,
            detail={
                "gate": "Gate 2 - Reglas de Negocio",
                "errors": qa_result.errors,
                "warnings": qa_result.warnings,
                "stats": qa_result.stats
            }
        )
    
    # --- GATE 3: DEDUPLICACIÓN ---
    # Solo verificar duplicados si hay institución y área asignada
    if simulacro.institucion_id and simulacro.area:
        dedup_result = Gate3Deduplicator.verificar_duplicados(
            preguntas_nuevas=contenido.get("preguntas", []),
            institucion_id=simulacro.institucion_id,
            area=simulacro.area,
            db=db
        )
        if not dedup_result.passed:
            raise HTTPException(
                status_code=400,
                detail={
                    "gate": "Gate 3 - Deduplicación",
                    "message": f"Se encontraron {len(dedup_result.duplicados)} preguntas duplicadas",
                    "duplicados": dedup_result.to_dict()["duplicados"],
                    "stats": dedup_result.stats
                }
            )
    
    # --- GATE 4: VALIDACIÓN VISUAL (Chart.js y Tablas) ---
    render_result = Gate4RenderValidator.validar_graficos(contenido.get("preguntas", []))
    if not render_result.passed:
        raise HTTPException(
            status_code=400,
            detail={
                "gate": "Gate 4 - Validación Visual",
                "message": f"Se encontraron {len([i for i in render_result.issues if i.nivel == 'error'])} errores de renderizado",
                "issues": render_result.to_dict()["issues"],
                "stats": render_result.stats
            }
        )
    
    # --- GATE 5: VALIDACIÓN SEMÁNTICA (IA) ---
    # Solo se ejecuta si hay API key de Groq configurada
    semantic_result = Gate5SemanticValidator.validar_semantica(
        preguntas=contenido.get("preguntas", []),
        area=simulacro.area or "General"
    )
    if not semantic_result.passed:
        raise HTTPException(
            status_code=400,
            detail={
                "gate": "Gate 5 - Validación Semántica (IA)",
                "message": f"Se detectaron {len([i for i in semantic_result.issues if i.nivel == 'error'])} problemas de coherencia",
                "issues": semantic_result.to_dict()["issues"],
                "stats": semantic_result.stats
            }
        )
    
    # --- GATE 6: VALIDACIÓN LÓGICA (Light) ---
    logic_result = Gate6LogicValidator.validar_logica(contenido.get("preguntas", []))
    if not logic_result.passed:
        raise HTTPException(
            status_code=400,
            detail={
                "gate": "Gate 6 - Validación Lógica",
                "message": f"Se encontraron {len([i for i in logic_result.issues if i.nivel == 'error'])} problemas lógicos",
                "issues": logic_result.to_dict()["issues"],
                "stats": logic_result.stats
            }
        )
    
    # Crear el simulacro
    simulacro_data = simulacro.model_dump()
    simulacro_data["created_by"] = current_user.id  # Usuario que creó el simulacro
    db_simulacro = Simulacro(**simulacro_data)
    db.add(db_simulacro)
    db.commit()
    db.refresh(db_simulacro)
    
    # Registrar preguntas en preguntas_usadas (si tiene institución asignada)
    if db_simulacro.institucion_id:
        contenido = db_simulacro.contenido
        if isinstance(contenido, str):
            import json
            contenido = json.loads(contenido)

        registrar_preguntas_usadas(
            db=db,
            preguntas=contenido.get("preguntas", []),
            institucion_id=db_simulacro.institucion_id,
            area=db_simulacro.area,
            version_simulacro=db_simulacro.version,
            simulacro_id=db_simulacro.id,
            commit=True,
        )
    
    return db_simulacro

@router.get("/{simulacro_id}", response_model=SimulacroSchema)
def read_simulacro(
    simulacro_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_simulacro = db.query(Simulacro).filter(Simulacro.id == simulacro_id).first()
    if db_simulacro is None:
        raise HTTPException(status_code=404, detail="Simulacro no encontrado")
    
    # Enriquecer con información de la institución y sede
    from app.models.institucion import Institucion

    response_dict = {
        "id": db_simulacro.id,
        "titulo": db_simulacro.titulo,
        "descripcion": db_simulacro.descripcion,
        "area": db_simulacro.area,
        "version": db_simulacro.version,
        "contenido": db_simulacro.contenido,
        "total_preguntas": db_simulacro.total_preguntas,
        "duracion_minutos": db_simulacro.duracion_minutos,
        "institucion_id": db_simulacro.institucion_id,
        "sede_id": db_simulacro.sede_id,
        "estado": db_simulacro.estado,
        "activo": db_simulacro.activo,
        "fecha_disponible_desde": db_simulacro.fecha_disponible_desde,
        "fecha_disponible_hasta": db_simulacro.fecha_disponible_hasta,
        "created_by": db_simulacro.created_by,
        "created_at": db_simulacro.created_at,
        "updated_at": db_simulacro.updated_at,
    }

    # Agregar nombre de institución
    if db_simulacro.institucion_id:
        institucion = db.query(Institucion).filter(Institucion.id == db_simulacro.institucion_id).first()
        if institucion:
            response_dict["institucion_nombre"] = institucion.nombre

    # Agregar nombre de sede
    if db_simulacro.sede_id:
        sede = db.query(Sede).filter(Sede.id == db_simulacro.sede_id).first()
        if sede:
            response_dict["sede_nombre"] = sede.nombre
    
    # Información del creador
    if db_simulacro.created_by:
        creator = db.query(Usuario).filter(Usuario.id == db_simulacro.created_by).first()
        if creator:
            rol_nombre = creator.rol.nombre if creator.rol else "desconocido"
            if rol_nombre == "admin":
                response_dict["created_by_nombre"] = "SuperAdmin"
                response_dict["created_by_tipo"] = "superadmin"
            else:
                inst_nombre = creator.institucion.nombre if creator.institucion else "Institución"
                response_dict["created_by_nombre"] = inst_nombre
                response_dict["created_by_tipo"] = "institucion"
    
    return response_dict

@router.put("/{simulacro_id}", response_model=SimulacroSchema)
def update_simulacro(
    simulacro_id: int, 
    simulacro: SimulacroUpdate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_simulacro = db.query(Simulacro).filter(Simulacro.id == simulacro_id).first()
    if db_simulacro is None:
        raise HTTPException(status_code=404, detail="Simulacro no encontrado")
    
    rol_nombre = current_user.rol.nombre if current_user.rol else ""
    update_data = simulacro.model_dump(exclude_unset=True)
    
    # --- VALIDACIÓN DE PERMISOS: SuperAdmin y AdminIE pueden modificar 'activo' ---
    # Solo roles inferiores (docentes, estudiantes) no pueden cambiar visibilidad
    if 'activo' in update_data and rol_nombre not in ['admin']:
        # Roles sin permiso: se ignora silenciosamente
        del update_data['activo']

    # --- VALIDACIÓN STRICT (Simulacro V2) ---
    if 'contenido' in update_data:
        try:
            contenido = update_data['contenido']
            if isinstance(contenido, str):
                import json
                contenido = json.loads(contenido)
            SimulacroV2(**contenido)
        except ValidationError as e:
            error_msg = f"Error de Validación Estructural (V2): {e.errors()[0]['msg']} en {e.errors()[0]['loc']}"
            raise HTTPException(status_code=400, detail=error_msg)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error procesando JSON de contenido: {str(e)}")
        
        # --- GATE 2: REGLAS DE NEGOCIO ---
        qa_result = Gate2Validator.validar_simulacro(contenido)
        if not qa_result.passed:
            raise HTTPException(
                status_code=400,
                detail={
                    "gate": "Gate 2 - Reglas de Negocio",
                    "errors": qa_result.errors,
                    "warnings": qa_result.warnings,
                    "stats": qa_result.stats
                }
            )

    for key, value in update_data.items():
        setattr(db_simulacro, key, value)
    
    db.add(db_simulacro)
    db.commit()
    db.refresh(db_simulacro)

    # Actualizar preguntas_usadas si cambió el contenido
    if 'contenido' in update_data and db_simulacro.institucion_id:
        # 1. Eliminar preguntas usadas anteriores de este simulacro
        db.query(PreguntaUsada).filter(PreguntaUsada.simulacro_id == simulacro_id).delete()
        
        # 2. Registrar las nuevas preguntas (incluye embeddings semánticos)
        contenido = db_simulacro.contenido
        if isinstance(contenido, str):
            import json
            contenido = json.loads(contenido)

        registrar_preguntas_usadas(
            db=db,
            preguntas=contenido.get("preguntas", []),
            institucion_id=db_simulacro.institucion_id,
            area=db_simulacro.area,
            version_simulacro=db_simulacro.version,
            simulacro_id=db_simulacro.id,
            commit=True,
        )

    return db_simulacro

@router.get("/institucion/{institucion_id}", response_model=List[SimulacroSchema])
def read_simulacros_by_institucion(
    institucion_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    simulacros = db.query(Simulacro).filter(Simulacro.institucion_id == institucion_id).all()
    return simulacros


@router.post("/{simulacro_id}/reset")
def reset_simulacro(
    simulacro_id: int,
    payload: SimulacroResetRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Reactiva un simulacro finalizado y anula todos los intentos y reportes vinculados.
    Solo admin.
    """
    if current_user.rol.nombre != "admin":
        raise HTTPException(status_code=403, detail="Solo admin puede reintentar simulacros")

    db_simulacro = db.query(Simulacro).filter(Simulacro.id == simulacro_id).first()
    if not db_simulacro:
        raise HTTPException(status_code=404, detail="Simulacro no encontrado")

    if current_user.institucion_id and db_simulacro.institucion_id != current_user.institucion_id:
        raise HTTPException(status_code=403, detail="No autorizado para este simulacro")

    if db_simulacro.estado != "finalizado":
        raise HTTPException(status_code=400, detail="Solo se pueden reintentar simulacros finalizados")

    now = datetime.now(timezone.utc)
    motivo = payload.motivo or f"Reset manual por admin {current_user.id}"

    # Anular intentos (solo activos)
    user_ids = [
        r[0] for r in db.query(RespuestaEstudiante.usuario_id)
        .filter(
            RespuestaEstudiante.simulacro_id == simulacro_id,
            RespuestaEstudiante.anulado.is_(False)
        )
        .distinct()
        .all()
    ]

    intentos_anulados = db.query(RespuestaEstudiante).filter(
        RespuestaEstudiante.simulacro_id == simulacro_id,
        RespuestaEstudiante.anulado.is_(False)
    ).update({
        RespuestaEstudiante.anulado: True,
        RespuestaEstudiante.reset_at: now,
        RespuestaEstudiante.reset_by: current_user.id,
        RespuestaEstudiante.reset_reason: motivo
    }, synchronize_session=False)

    # Anular reportes grupales del simulacro
    reportes_grupales_anulados = db.query(ReporteGrupal).filter(
        ReporteGrupal.simulacro_id == simulacro_id,
        ReporteGrupal.institucion_id == current_user.institucion_id,
        ReporteGrupal.anulado.is_(False)
    ).update({
        ReporteGrupal.anulado: True
    }, synchronize_session=False)

    db_simulacro.estado = "activo"
    db_simulacro.activo = True
    db.add(db_simulacro)
    db.commit()

    return {
        "ok": True,
        "simulacro_id": simulacro_id,
        "estado": db_simulacro.estado,
        "intentos_anulados": intentos_anulados,
        "reportes_grupales_anulados": reportes_grupales_anulados
    }

@router.delete("/{simulacro_id}", status_code=204)
async def delete_simulacro(
    simulacro_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Elimina un simulacro y sus preguntas_usadas asociadas.
    Solo SuperAdmins pueden eliminar simulacros.
    """
    # Verificar permisos
    if current_user.rol.nombre != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo SuperAdmins pueden eliminar simulacros"
        )
    
    # Buscar el simulacro
    db_simulacro = db.query(Simulacro).filter(Simulacro.id == simulacro_id).first()
    
    if not db_simulacro:
        raise HTTPException(status_code=404, detail="Simulacro no encontrado")
    
    print(f"\n{'='*60}")
    print(f"🗑️  ELIMINANDO SIMULACRO: {simulacro_id}")
    print(f"   Título: {db_simulacro.titulo}")
    print(f"   Usuario: {current_user.email}")
    print(f"{'='*60}")
    
    try:
        # Eliminar respuestas de estudiantes asociadas
        respuestas_eliminadas = db.query(RespuestaEstudiante).filter(
            RespuestaEstudiante.simulacro_id == simulacro_id
        ).delete(synchronize_session=False)
        
        print(f"   ✅ Respuestas de estudiantes eliminadas: {respuestas_eliminadas}")
        
        # Eliminar preguntas_usadas asociadas
        preguntas_eliminadas = db.query(PreguntaUsada).filter(
            PreguntaUsada.simulacro_id == simulacro_id
        ).delete(synchronize_session=False)
        
        print(f"   ✅ Preguntas usadas eliminadas: {preguntas_eliminadas}")
        
        # Eliminar el simulacro
        db.delete(db_simulacro)
        db.commit()
        
        print(f"   ✅ Simulacro eliminado exitosamente")
        print(f"{'='*60}\n")
        
        return None  # 204 No Content
        
    except Exception as e:
        db.rollback()
        print(f"   ❌ Error al eliminar: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar el simulacro: {str(e)}"
        )
