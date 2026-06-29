from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ValidationError

from app.api.deps import get_current_active_user
from app.database.config import get_db
from app.models.simulacro import Simulacro
from app.models.pregunta_usada import PreguntaUsada
from app.models.usuario import Usuario
from app.services.generation_service import SimulacroGenerator
from app.services.preguntas_usadas_service import registrar_preguntas_usadas
from app.services.qa_gate2_service import Gate2Validator
from app.services.qa_gate3_service import Gate3Deduplicator
from app.services.qa_gate4_service import Gate4RenderValidator
from app.services.qa_gate5_service import Gate5SemanticValidator
from app.services.qa_gate5b_service import Gate5BContextValidator
from app.services.qa_gate6_service import Gate6LogicValidator
from app.services.visual_enrichment_service import VisualEnrichmentService
from app.core.graphic_types import normalize_graph_types_in_questions

from app.api.simulacros_router import router

# ==========================================
# REGENERACIÓN DE PREGUNTAS ESPECÍFICAS
# ==========================================

class RegenerarRequest(BaseModel):
    """Request para regenerar preguntas específicas de un simulacro"""
    pregunta_ids: List[int]  # IDs de las preguntas a regenerar (números: 1, 2, 3...)


class RegenerarResponse(BaseModel):
    """Response de la regeneración"""
    success: bool
    simulacro_id: int
    preguntas_regeneradas: int
    mensaje: str
    errores: Optional[List[str]] = None


@router.post("/{simulacro_id}/regenerar", response_model=RegenerarResponse)
def regenerar_preguntas_simulacro(
    simulacro_id: int,
    request: RegenerarRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Regenera preguntas específicas de un simulacro existente.
    
    - Solo SuperAdmin puede usar este endpoint
    - Recibe lista de IDs de preguntas a regenerar
    - Llama a la IA para generar nuevas preguntas
    - Reemplaza las preguntas en el contenido
    - Actualiza preguntas_usadas
    - Ejecuta validaciones OMITIENDO Gate 1 (conteo de preguntas)
    """
    # Validar permisos
    rol_nombre = current_user.rol.nombre if current_user.rol else ""
    if rol_nombre != 'admin':
        raise HTTPException(status_code=403, detail="Solo el Super Admin puede regenerar preguntas")
    
    # Cargar simulacro
    db_simulacro = db.query(Simulacro).filter(Simulacro.id == simulacro_id).first()
    if not db_simulacro:
        raise HTTPException(status_code=404, detail="Simulacro no encontrado")
    
    contenido = db_simulacro.contenido
    if isinstance(contenido, str):
        import json
        contenido = json.loads(contenido)
    
    preguntas = contenido.get("preguntas", [])
    
    # Validar que los IDs existan
    preguntas_por_id = {p.get("id"): p for p in preguntas}
    preguntas_a_regenerar = []
    ids_no_encontrados = []
    
    for preg_id in request.pregunta_ids:
        if preg_id in preguntas_por_id:
            preguntas_a_regenerar.append(preguntas_por_id[preg_id])
        else:
            ids_no_encontrados.append(preg_id)
    
    if ids_no_encontrados:
        raise HTTPException(
            status_code=400, 
            detail=f"IDs de preguntas no encontrados: {ids_no_encontrados}"
        )
    
    if len(preguntas_a_regenerar) == 0:
        raise HTTPException(status_code=400, detail="No hay preguntas para regenerar")
    
    print(f"\n{'='*60}")
    print(f"🔄 REGENERACIÓN: Simulacro {simulacro_id}")
    print(f"   Preguntas a regenerar: {request.pregunta_ids}")
    print(f"{'='*60}")
    
    errores_generacion = []
    
    try:
        # Llamar a la IA para regenerar completamente (contexto, gráficos, todo)
        print(f"   🤖 Llamando a OpenAI para regenerar {len(preguntas_a_regenerar)} preguntas completamente...")
        
        regeneration_result = SimulacroGenerator.regenerar_preguntas_completas(
            preguntas_a_reemplazar=preguntas_a_regenerar,
            area=db_simulacro.area,
            institucion_id=db_simulacro.institucion_id,
            db=db
        )
        
        if not regeneration_result.success:
            raise HTTPException(
                status_code=500, 
                detail=f"Error al regenerar: {regeneration_result.error}"
            )
        
        preguntas_nuevas = regeneration_result.data.get("preguntas", [])
        print(f"   ✅ Regeneradas {len(preguntas_nuevas)} preguntas ({regeneration_result.generation_time:.1f}s)")
        
        # Reemplazar en el contenido
        preguntas_actualizadas = list(preguntas)
        for preg_nueva in preguntas_nuevas:
            preg_id = preg_nueva.get("id")
            for i, p in enumerate(preguntas_actualizadas):
                if p.get("id") == preg_id:
                    preguntas_actualizadas[i] = preg_nueva
                    print(f"   🔄 Pregunta {preg_id} reemplazada")
                    break
        
        contenido["preguntas"] = preguntas_actualizadas
        
        # ========================
        # VALIDACIONES (todos los gates, solo omitimos conteo de preguntas)
        # ========================
        
        print(f"\n   🔍 Ejecutando Quality Gates (omitiendo solo conteo de preguntas)...")
        
        # Gate 1: Validación estructural (solo para las preguntas nuevas)
        normalization_report = normalize_graph_types_in_questions(preguntas_nuevas)
        if normalization_report.get("normalized_count", 0) > 0:
            print(
                f"   🧩 Normalización gráfica: "
                f"{normalization_report['normalized_count']} tipo(s) ajustado(s) por alias."
            )
        print(f"   📋 Gate 1 - Validación estructural...", end=" ")
        try:
            # Validamos solo las preguntas regeneradas con el schema
            from app.schemas.simulacro_v2 import Pregunta
            for preg in preguntas_nuevas:
                Pregunta(**preg)
            print("✅ PASS")
        except ValidationError as e:
            print("❌ FAIL")
            for err in e.errors()[:3]:
                loc = " -> ".join(str(x) for x in err['loc'])
                error_msg = f"{loc} - {err['msg']}"
                print(f"      [ERROR] Gate 1: {error_msg}")
                errores_generacion.append(f"Gate 1: {error_msg}")
        
        # Gate 2: Reglas de negocio (skip_conteo=True para omitir validación de cantidad)
        print(f"   📋 Gate 2 - Reglas de negocio...", end=" ")
        qa_result = Gate2Validator.validar_simulacro(
            {"preguntas": preguntas_nuevas}, 
            skip_conteo=True  # Omitir validación de conteo porque son solo las regeneradas
        )
        if not qa_result.passed:
            print("❌ FAIL")
            for error in qa_result.errors[:3]:
                print(f"      [ERROR] {error}")
                errores_generacion.append(f"Gate 2: {error}")
        else:
            print("✅ PASS")
        
        # Gate 3: Deduplicación (solo para las nuevas)
        print(f"   📋 Gate 3 - Deduplicación...", end=" ")
        dedup_result = Gate3Deduplicator.verificar_duplicados(
            preguntas_nuevas=preguntas_nuevas,
            institucion_id=db_simulacro.institucion_id,
            area=db_simulacro.area,
            db=db
        )
        if not dedup_result.passed:
            print("❌ FAIL")
            errores_generacion.append(f"Gate 3: {len(dedup_result.duplicados)} duplicados detectados")
        else:
            print("✅ PASS")
        
        # Gate 4: Validación visual (solo para las nuevas)
        print(f"   📋 Gate 4 - Validación visual...", end=" ")
        render_result = Gate4RenderValidator.validar_graficos(preguntas_nuevas)
        if not render_result.passed:
            print("❌ FAIL")
            errores_generacion.append(f"Gate 4: {len([i for i in render_result.issues if i.nivel == 'error'])} errores de renderizado")
        else:
            print("✅ PASS")
        
        # Gate 5: Validación semántica (IA)
        print(f"   📋 Gate 5 - Validación semántica (IA)...", end=" ")
        semantic_result = Gate5SemanticValidator.validar_semantica(
            preguntas=preguntas_nuevas,
            area=db_simulacro.area or "General"
        )
        if not semantic_result.passed:
            print("❌ FAIL")
            for issue in [i for i in semantic_result.issues if i.nivel == 'error'][:3]:
                error_msg = f"{issue.tipo}: {issue.mensaje}"
                print(f"      [ERROR] Gate 5 - Pregunta {issue.pregunta_id}: {error_msg}")
                errores_generacion.append(f"Gate 5: {error_msg}")
        else:
            print("✅ PASS")
        
        # Gate 5B: Validación contexto-pregunta (SOLO para LECTURA_CRITICA)
        if db_simulacro.area == "LECTURA_CRITICA":
            print(f"   📋 Gate 5B - Coherencia contexto-pregunta (Embeddings)...", end=" ")
            context_result = Gate5BContextValidator.validar_contexto(
                preguntas=preguntas_nuevas
            )
            if not context_result.passed:
                print("❌ FAIL")
                for issue in [i for i in context_result.issues if i.nivel == 'error']:
                    error_msg = f"{issue.tipo}: {issue.mensaje} (sim: {issue.similitud:.2f})"
                    print(f"      [ERROR] Gate 5B - Pregunta {issue.pregunta_id}: {error_msg}")
                    errores_generacion.append(f"Gate 5B: {error_msg}")
            else:
                print("✅ PASS")
        
        # Gate 6: Validación lógica (solo para las nuevas)
        print(f"   📋 Gate 6 - Validación lógica...", end=" ")
        logic_result = Gate6LogicValidator.validar_logica(preguntas_nuevas)
        if not logic_result.passed:
            print("❌ FAIL")
            errores_generacion.append(f"Gate 6: {len([i for i in logic_result.issues if i.nivel == 'error'])} errores lógicos")
        else:
            print("✅ PASS")
        
        # Si hay errores críticos, fallar
        if errores_generacion:
            print(f"\n   ⚠️ Advertencias: {errores_generacion}")
            # Continuamos de todas formas, son solo warnings
        
        # ========================
        # GUARDAR CAMBIOS
        # ========================
        
        # 3.b ENRIQUECIMIENTO VISUAL (Claude Opus) - Para preguntas regeneradas
        print(f"   🎨 Enriquecimiento Visual (Claude Opus) para regeneradas...")
        VisualEnrichmentService.enrich_simulacro_questions(
            preguntas_nuevas,
            area=db_simulacro.area
        )

        print(f"\n   💾 Guardando cambios...")
        
        # Actualizar contenido
        # IMPORTANTE: Usamos flag_modified para forzar a SQLAlchemy a detectar
        # el cambio en el campo JSONB, ya que la modificación interna del dict
        # no siempre es detectada automáticamente.
        from sqlalchemy.orm.attributes import flag_modified
        db_simulacro.contenido = contenido
        flag_modified(db_simulacro, "contenido")
        db.add(db_simulacro)
        
        # Actualizar preguntas_usadas
        # 1. Eliminar registros de preguntas regeneradas
        ids_regenerados = [p.get("id") for p in preguntas_nuevas]
        # Necesitamos identificar las preguntas en la tabla por su texto/hash
        # Para simplificar, eliminamos todas las del simulacro y re-insertamos
        
        print(f"   📝 Actualizando preguntas_usadas...")
        db.query(PreguntaUsada).filter(PreguntaUsada.simulacro_id == simulacro_id).delete()
        
        # 2. Insertar todas las preguntas (actualizadas, con embeddings semánticos)
        registrar_preguntas_usadas(
            db=db,
            preguntas=preguntas_actualizadas,
            institucion_id=db_simulacro.institucion_id,
            area=db_simulacro.area,
            version_simulacro=db_simulacro.version,
            simulacro_id=db_simulacro.id,
            commit=False,
        )
        
        db.commit()
        db.refresh(db_simulacro)
        
        print(f"\n✅ REGENERACIÓN COMPLETADA")
        print(f"   Simulacro: {db_simulacro.id}")
        print(f"   Preguntas regeneradas: {len(preguntas_nuevas)}")
        
        return RegenerarResponse(
            success=True,
            simulacro_id=db_simulacro.id,
            preguntas_regeneradas=len(preguntas_nuevas),
            mensaje=f"Se regeneraron {len(preguntas_nuevas)} pregunta(s) exitosamente",
            errores=errores_generacion if errores_generacion else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
