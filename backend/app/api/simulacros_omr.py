from fastapi import Depends, HTTPException, BackgroundTasks, Body, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from app.api.deps import get_current_active_user
from app.database.config import get_db
from app.models.simulacro import Simulacro
from app.models.usuario import Usuario
from app.models.respuesta_estudiante import RespuestaEstudiante
from app.services.analisis_service import AnalisisService

from app.api.simulacros_router import router

@router.get("/{simulacro_id}/pdf")
def download_simulacro_pdf(
    simulacro_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Genera y descarga el cuadernillo de preguntas del simulacro en PDF.
    Utiliza el servicio de generación profesional con soporte LaTeX.
    """
    from fastapi.responses import Response
    from app.services.pdf_generation_service import PDFGenerationService
    from app.models.institucion import Institucion
    
    # 1. Validar simulacro
    simulacro = db.query(Simulacro).filter(Simulacro.id == simulacro_id).first()
    if not simulacro:
        raise HTTPException(status_code=404, detail="Simulacro no encontrado")

    # 2. Validar permisos (Estudiantes solo si está activo/finalizado según reglas, Admins siempre)
    # Por ahora simplificamos: si tienes acceso al simulacro, puedes bajar el PDF
    if current_user.rol.nombre == 'estudiante':
        # Validar si el estudiante pertenece a la institución del simulacro
        if simulacro.institucion_id != current_user.institucion_id:
             raise HTTPException(status_code=403, detail="No tienes acceso a este simulacro")
             
    elif current_user.rol.nombre == 'admin':
        if simulacro.institucion_id != current_user.institucion_id:
            raise HTTPException(status_code=403, detail="No tienes acceso a este simulacro")

    # 3. Obtener nombre de la institución para la portada
    institucion = db.query(Institucion).filter(Institucion.id == simulacro.institucion_id).first()
    institucion_nombre = institucion.nombre if institucion else "SIMIC"

    # 4. Generar PDF
    try:
        generator = PDFGenerationService()
        pdf_bytes = generator.generate_booklet(simulacro, institucion_nombre)
        
        filename = f"Simulacro_{simulacro.titulo.replace(' ', '_')}_{simulacro.area}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")

@router.post("/{simulacro_id}/hojas-respuestas")
def generate_answer_sheets(
    simulacro_id: int,
    grupos_ids: List[int] = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Genera hojas de respuestas OMR personalizadas para estudiantes de los grupos seleccionados
    
    Args:
        simulacro_id: ID del simulacro
        grupos_ids: Lista de IDs de grupos
    
    Returns:
        PDF con hojas OMR personalizadas
    """
    from fastapi.responses import Response
    from app.models.grupo import Grupo
    from app.services.omr_sheet_service import OMRSheetGenerator
    
    # Verificar que el simulacro existe
    simulacro = db.query(Simulacro).filter(Simulacro.id == simulacro_id).first()
    if not simulacro:
        raise HTTPException(status_code=404, detail="Simulacro no encontrado")
    
    # Verificar permisos
    rol_nombre = current_user.rol.nombre if current_user.rol else ""
    if rol_nombre not in ['admin']:
        raise HTTPException(status_code=403, detail="No tienes permisos para generar hojas de respuestas")
    
    # Si es admin de institución, verificar que el simulacro pertenece a su institución
    if rol_nombre == 'admin':
        if simulacro.institucion_id != current_user.institucion_id:
            raise HTTPException(status_code=403, detail="No puedes generar hojas para simulacros de otra institución")
    
    # Obtener estudiantes de los grupos seleccionados
    estudiantes = db.query(Usuario).filter(
        Usuario.grupo_id.in_(grupos_ids),
        Usuario.rol.has(nombre='estudiante')
    ).order_by(
        Usuario.nombre
    ).all()
    
    if not estudiantes:
        raise HTTPException(status_code=404, detail="No se encontraron estudiantes en los grupos seleccionados")
    
    # Generar PDF con hojas OMR
    try:
        import traceback
        print(f"=== GENERANDO HOJAS OMR ===")
        print(f"Simulacro ID: {simulacro.id}, Título: {simulacro.titulo}")
        print(f"Total estudiantes: {len(estudiantes)}")
        print(f"Total preguntas: {simulacro.total_preguntas}")
        
        generator = OMRSheetGenerator()
        pdf_bytes = generator.generate_sheets(simulacro, estudiantes)
        
        print(f"PDF generado exitosamente. Tamaño: {len(pdf_bytes)} bytes")
        
        # Crear nombre de archivo
        filename = f"Hojas_OMR_{simulacro.titulo.replace(' ', '_')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"ERROR GENERANDO HOJAS OMR:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"Error generando hojas OMR: {str(e)}")


@router.post("/{simulacro_id}/procesar-omr")
async def process_omr_sheets(
    simulacro_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Procesa hojas de respuestas OMR escaneadas usando Claude Vision.
    
    Por ahora solo extrae y devuelve los datos sin guardar en BD.
    """
    from app.services.omr_processing_service import OMRProcessingService
    
    # Validar permisos - Solo admin
    rol_nombre = current_user.rol.nombre if current_user.rol else ""
    if rol_nombre != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Solo administradores de institución pueden procesar hojas OMR"
        )
    
    # Validar que el simulacro existe y pertenece a la institución
    simulacro = db.query(Simulacro).filter(Simulacro.id == simulacro_id).first()
    if not simulacro:
        raise HTTPException(status_code=404, detail="Simulacro no encontrado")
    
    if simulacro.institucion_id != current_user.institucion_id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este simulacro")
    
    # Validar que hay archivos
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No se recibieron archivos")
    
    # Obtener número de preguntas del simulacro
    num_preguntas = simulacro.total_preguntas or 35
    
    print(f"\n📋 [API] Procesando {len(files)} hojas OMR para simulacro {simulacro_id}")
    
    # Preparar imágenes para procesamiento
    images_data = []
    for file in files:
        # Leer contenido
        content = await file.read()
        
        # Validar tipo
        if not file.content_type.startswith("image/"):
            print(f"   ⚠️ Archivo ignorado (no es imagen): {file.filename}")
            continue
        
        images_data.append((content, file.content_type, file.filename))
    
    if not images_data:
        raise HTTPException(status_code=400, detail="No se encontraron imágenes válidas")
    
    # Procesar con el servicio OMR
    try:
        omr_service = OMRProcessingService()
        results = omr_service.process_batch(images_data, num_preguntas)

        # Formatear respuesta para frontend
        processed_results = []
        for result in results:
            if result["success"]:
                data = result["data"]
                
                # Determinar estado
                if data.get("qr_detectado") and data.get("qr_datos", {}).get("estudiante_id"):
                    status = "success"
                    student = data["qr_datos"].get("estudiante_nombre", f"ID: {data['qr_datos']['estudiante_id']}")
                elif data.get("qr_detectado"):
                    status = "warning"
                    student = None
                else:
                    status = "warning"
                    student = None
                
                processed_results.append({
                    "filename": result["filename"],
                    "status": status,
                    "student": student,
                    "confidence": int(data.get("confianza_general", 0) * 100),
                    "message": data.get("observaciones"),
                    "data": data  # Datos completos para debug
                })
            else:
                processed_results.append({
                    "filename": result["filename"],
                    "status": "error",
                    "message": result.get("error", "Error desconocido"),
                    "data": None
                })
        
        # Resumen
        summary = {
            "total": len(processed_results),
            "success": sum(1 for r in processed_results if r["status"] == "success"),
            "warnings": sum(1 for r in processed_results if r["status"] == "warning"),
            "errors": sum(1 for r in processed_results if r["status"] == "error")
        }
        
        print(f"✅ [API] Procesamiento completado: {summary}")
        
        return {
            "simulacro_id": simulacro_id,
            "results": processed_results,
            "summary": summary
        }
        
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"ERROR PROCESANDO OMR:\n{error_detail}")
        raise HTTPException(status_code=500, detail=f"Error procesando hojas OMR: {str(e)}")


@router.post("/{simulacro_id}/guardar-omr")
async def save_omr_results(
    simulacro_id: int,
    results: List[Dict[str, Any]] = Body(..., embed=True),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Guarda los resultados de procesamiento OMR en la base de datos.
    Recibe la lista de resultados exitosos del endpoint procesar-omr.
    """
    from app.services.analisis_service import AnalisisService
    
    # Validar permisos - Solo admin
    rol_nombre = current_user.rol.nombre if current_user.rol else ""
    if rol_nombre != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Solo administradores de institución pueden guardar resultados OMR"
        )
    
    # Obtener simulacro
    simulacro = db.query(Simulacro).filter(Simulacro.id == simulacro_id).first()
    if not simulacro:
        raise HTTPException(status_code=404, detail="Simulacro no encontrado")
    
    if simulacro.institucion_id != current_user.institucion_id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este simulacro")
    
    # Obtener contenido del simulacro para procesar respuestas
    contenido = simulacro.contenido
    if isinstance(contenido, str):
        import json
        contenido = json.loads(contenido)
    
    preguntas = contenido.get("preguntas", [])
    # Mapping by Index (1-based) to match OMR sheet visual order
    mapa_preguntas_idx = {str(i+1): p for i, p in enumerate(preguntas)}
    
    print(f"\n📥 [API] Guardando {len(results)} resultados OMR para simulacro {simulacro_id}")
    
    saved_results = []
    skipped_results = []
    error_results = []
    
    for result in results:
        # Solo procesar resultados exitosos con estudiante identificado
        if result.get("status") != "success":
            skipped_results.append({
                "filename": result.get("filename"),
                "reason": "Estado no exitoso"
            })
            continue
        
        data = result.get("data")
        if not data:
            skipped_results.append({
                "filename": result.get("filename"),
                "reason": "Sin datos"
            })
            continue
        
        qr_datos = data.get("qr_datos", {})
        estudiante_id = qr_datos.get("estudiante_id")
        
        if not estudiante_id:
            skipped_results.append({
                "filename": result.get("filename"),
                "reason": "Sin ID de estudiante"
            })
            continue
        
        # Buscar estudiante: primero por ID interno, luego por número de documento
        # (Claude puede leer el ID del QR o el número de documento impreso)
        estudiante = db.query(Usuario).filter(
            Usuario.id == estudiante_id,
            Usuario.institucion_id == current_user.institucion_id
        ).first()
        
        # Si no encontró por ID, intentar por número de documento
        if not estudiante:
            estudiante = db.query(Usuario).filter(
                Usuario.numero_documento == str(estudiante_id),
                Usuario.institucion_id == current_user.institucion_id
            ).first()
        
        if not estudiante:
            error_results.append({
                "filename": result.get("filename"),
                "estudiante_id": estudiante_id,
                "reason": "Estudiante no encontrado o no pertenece a esta institución"
            })
            continue
        
        # Verificar si ya respondió este simulacro
        existe = db.query(RespuestaEstudiante).filter(
            RespuestaEstudiante.simulacro_id == simulacro_id,
            RespuestaEstudiante.usuario_id == estudiante.id,  # Usar ID real
            RespuestaEstudiante.anulado.is_(False)
        ).first()
        
        if existe:
            skipped_results.append({
                "filename": result.get("filename"),
                "estudiante_id": estudiante_id,
                "estudiante_nombre": qr_datos.get("estudiante_nombre"),
                "reason": "Ya presentó este simulacro"
            })
            continue
        
        # Procesar respuestas (reutilizando lógica de /finalizar)
        respuestas_omr = data.get("respuestas", {})
        
        total_correctas = 0
        total_incorrectas = 0
        respuestas_detalladas = {}
        
        for idx_str, resp_usuario in respuestas_omr.items():
            # Lookup by Index match (1, 2, 3...) instead of ID
            pregunta_config = mapa_preguntas_idx.get(str(idx_str))
            
            # Normalizar respuesta (en caso de que venga como 'sin_respuesta' o 'multiple')
            resp_normalizada = resp_usuario if resp_usuario in ["A", "B", "C", "D"] else None
            
            detalles = {
                "respuesta_usuario": resp_normalizada,
                "es_correcta": False
            }
            
            if pregunta_config:
                # Store internal Question ID for traceability
                detalles["pregunta_id"] = pregunta_config.get("id")
                
                if resp_normalizada:
                    correcta = pregunta_config.get("respuesta_correcta")
                    es_correcta = (resp_normalizada == correcta)
                    
                    detalles["respuesta_correcta"] = correcta
                    detalles["es_correcta"] = es_correcta
                    
                    # Copiar metadatos
                    for meta in ["competencia", "componente", "tema"]:
                        if meta in pregunta_config:
                            detalles[meta] = pregunta_config[meta]
                    
                    if es_correcta:
                        total_correctas += 1
                    else:
                        total_incorrectas += 1
                else:
                    total_incorrectas += 1  # Sin respuesta cuenta como incorrecta
            else:
                # Question index out of range or not found in generated list
                # Should we count it? Maybe skip.
                continue
            
            respuestas_detalladas[idx_str] = detalles
        
        # Calcular puntaje
        total_preguntas = len(preguntas)
        puntaje = 0.0
        if total_preguntas > 0:
            puntaje = (total_correctas / total_preguntas) * 100.0
        
        # Crear registro
        try:
            nueva_respuesta = RespuestaEstudiante(
                simulacro_id=simulacro_id,
                usuario_id=estudiante.id,  # Usar ID real de la BD, no el del QR
                institucion_id=current_user.institucion_id,
                respuestas=respuestas_omr,
                respuestas_detalladas=respuestas_detalladas,
                total_correctas=total_correctas,
                total_incorrectas=total_incorrectas,
                puntaje_total=puntaje,
                tiempo_empleado=None,  # No aplica para OMR
                fecha_finalizacion=datetime.now(),
                fecha_inicio=datetime.now(),
                fraude=False  # OMR no tiene detección de fraude
            )
            
            db.add(nueva_respuesta)
            db.commit()
            db.refresh(nueva_respuesta)
            
            # Lanzar análisis IA en background
            if background_tasks:
                background_tasks.add_task(AnalisisService.procesar_respuesta, nueva_respuesta.id)
            
            saved_results.append({
                "filename": result.get("filename"),
                "estudiante_id": estudiante_id,
                "estudiante_nombre": qr_datos.get("estudiante_nombre") or estudiante.nombre,
                "respuesta_id": nueva_respuesta.id,
                "puntaje": float(puntaje),
                "correctas": total_correctas,
                "incorrectas": total_incorrectas
            })
            
            print(f"   ✅ Guardado: {estudiante.nombre or estudiante.email} - {puntaje:.1f}%")
            
        except Exception as e:
            db.rollback()
            error_results.append({
                "filename": result.get("filename"),
                "estudiante_id": estudiante_id,
                "reason": str(e)
            })
            print(f"   ❌ Error guardando: {e}")
    
    summary = {
        "guardados": len(saved_results),
        "omitidos": len(skipped_results),
        "errores": len(error_results)
    }
    
    print(f"\n✅ [API] Guardado completado: {summary}")
    
    return {
        "simulacro_id": simulacro_id,
        "summary": summary,
        "saved": saved_results,
        "skipped": skipped_results,
        "errors": error_results
    }
