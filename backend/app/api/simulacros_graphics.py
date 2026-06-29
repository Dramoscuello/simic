from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.api.deps import get_current_active_user
from app.database.config import get_db
from app.models.simulacro import Simulacro
from app.models.usuario import Usuario

from app.api.simulacros_router import router

# ============================================================================
# OPTIMIZAR GRÁFICO SVG CON IA VISION
# ============================================================================
class OptimizarGraficoRequest(BaseModel):
    pregunta_id: int
    imagen_base64: str  # Imagen PNG del SVG renderizado en base64
    instrucciones_adicionales: Optional[str] = None

class OptimizarGraficoResponse(BaseModel):
    success: bool
    pregunta_id: int
    mensaje: str
    cambios: Optional[List[str]] = None
    tokens_usados: Optional[int] = None

@router.post("/{simulacro_id}/optimizar-grafico")
async def optimizar_grafico(
    simulacro_id: int,
    request: Dict[str, Any], # DEBUG: Dict genérico para ver qué llega
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Optimiza un gráfico SVG usando IA con visión.
    Solo SuperAdmins pueden usar esta funcionalidad.
    """
    # DEBUG: Imprimir payload de entrada
    print(f"\n🔍 [DEBUG OPTIMIZAR] Payload recibido: {request.keys()}")
    if "imagen_base64" in request:
        print(f"   🖼️ Tamaño imagen: {len(request['imagen_base64'])} caracteres")
    else:
        print("   ❌ FALTA imagen_base64")

    # Reconstruir objeto o valdear manualmente
    try:
        pregunta_id = request.get("pregunta_id")
        imagen_base64 = request.get("imagen_base64")
        instrucciones = request.get("instrucciones_adicionales")
        
        if not pregunta_id or not imagen_base64:
             raise HTTPException(status_code=400, detail=f"Faltan campos. Recibido: {request.keys()}")
             
    except Exception as e:
        print(f"   ❌ Error parseando request: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    # Verificar permisos
    if current_user.rol.nombre != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo SuperAdmins pueden optimizar gráficos"
        )
    
    # Buscar el simulacro
    db_simulacro = db.query(Simulacro).filter(Simulacro.id == simulacro_id).first()
    if not db_simulacro:
        raise HTTPException(status_code=404, detail="Simulacro no encontrado")
    
    # Obtener contenido
    contenido = db_simulacro.contenido
    if not contenido:
        raise HTTPException(status_code=400, detail="Simulacro sin contenido")
    
    preguntas = contenido.get("preguntas", [])
    
    # Buscar la pregunta específica
    pregunta_actual = None
    pregunta_index = None
    for i, p in enumerate(preguntas):
        if p.get("id") == pregunta_id:
            pregunta_actual = p
            pregunta_index = i
            break
    
    if not pregunta_actual:
        raise HTTPException(
            status_code=404,
            detail=f"Pregunta {pregunta_id} no encontrada en el simulacro"
        )
    
    # Verificar que tiene gráfico
    if not pregunta_actual.get("tiene_grafico"):
        raise HTTPException(
            status_code=400,
            detail="La pregunta no tiene gráfico para optimizar"
        )
    
    # Obtener el svg_spec actual o crear uno básico desde otros formatos
    config_grafico = pregunta_actual.get("configuracion_grafico", {})
    tipo_grafico = pregunta_actual.get("tipo_grafico", "")
    svg_spec_actual = config_grafico.get("svg_spec")
    
    # Fallback: Si no hay svg_spec, intentar reconstruir desde otros formatos
    if not svg_spec_actual:
        # Caso 1: svg_code (generado por Claude Opus en svg_artistico)
        if config_grafico.get("svg_code"):
            print(f"   ⚠️ No hay svg_spec, pero hay svg_code. Reconstruyendo desde imagen...")
            svg_spec_actual = {
                "viewBox": "0 0 400 300",
                "shapes": [],
                "_source": "reconstruction_from_svg_code",
                "_original_type": tipo_grafico
            }
        # Caso 2: Chart.js (datasets)
        elif config_grafico.get("datasets") or config_grafico.get("labels"):
            print(f"   ⚠️ Es un gráfico Chart.js. Reconstruyendo desde imagen...")
            svg_spec_actual = {
                "viewBox": "0 0 400 300",
                "shapes": [],
                "_source": "reconstruction_from_chartjs",
                "_original_type": tipo_grafico,
                "_chart_data": {
                    "labels": config_grafico.get("labels", []),
                    "datasets": config_grafico.get("datasets", [])
                }
            }
        # Caso 3: Tabla de datos
        elif config_grafico.get("rows") or config_grafico.get("headers"):
            raise HTTPException(
                status_code=400,
                detail="Las tablas de datos no son optimizables como SVG. Edita los datos directamente."
            )
        # Caso 4: descripcion_visual (svg_artistico pendiente de generar)
        elif config_grafico.get("descripcion_visual"):
            print(f"   ⚠️ Hay descripcion_visual pero no svg_code. Generando desde imagen...")
            svg_spec_actual = {
                "viewBox": "0 0 400 300",
                "shapes": [],
                "_source": "reconstruction_from_description",
                "_original_type": tipo_grafico,
                "_description": config_grafico.get("descripcion_visual", "")
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"La pregunta no tiene configuración gráfica optimizable. Tipo: {tipo_grafico}"
            )
    
    print(f"\n{'='*60}")
    print(f"🎨 OPTIMIZANDO GRÁFICO: Simulacro {simulacro_id}, Pregunta {pregunta_id}")
    print(f"   Tipo original: {tipo_grafico}")
    print(f"   Instrucciones Adicionales: '{instrucciones}'")
    print(f"{'='*60}")
    
    # Importar el servicio de optimización
    from app.services.grafico_optimizer_service import GraficoOptimizer
    
    # Llamar al optimizador
    result = GraficoOptimizer.optimizar(
        imagen_base64=imagen_base64,
        svg_spec_actual=svg_spec_actual,
        contexto_pregunta=pregunta_actual.get("contexto", ""),
        enunciado_pregunta=pregunta_actual.get("enunciado", pregunta_actual.get("pregunta", "")),
        area=db_simulacro.area,
        instrucciones_adicionales=instrucciones
    )
    
    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=f"Error en optimización: {result.error}"
        )
    
    # Actualizar el svg_spec en la pregunta
    if "configuracion_grafico" not in preguntas[pregunta_index]:
        preguntas[pregunta_index]["configuracion_grafico"] = {}
    
    preguntas[pregunta_index]["configuracion_grafico"]["svg_spec"] = result.svg_spec
    
    # Limpieza post-optimización: Eliminar formatos viejos que ya no se usarán
    old_type = preguntas[pregunta_index].get("tipo_grafico", "")
    if "svg_code" in preguntas[pregunta_index]["configuracion_grafico"]:
        del preguntas[pregunta_index]["configuracion_grafico"]["svg_code"]
        print(f"   🧹 Eliminado svg_code viejo (migrado a svg_spec)")
    
    # Actualizar tipo_grafico a svg_geometrico para que el frontend use SvgSpecRenderer
    if old_type in ["svg_artistico", "chartjs_bar", "chartjs_pie", "chartjs_line"]:
        preguntas[pregunta_index]["tipo_grafico"] = "svg_geometrico"
        print(f"   🔄 tipo_grafico cambiado de '{old_type}' a 'svg_geometrico'")
    
    # Guardar cambios
    from sqlalchemy.orm.attributes import flag_modified
    db_simulacro.contenido = contenido
    flag_modified(db_simulacro, "contenido")
    db.add(db_simulacro)
    db.commit()
    db.refresh(db_simulacro)
    
    print(f"   ✅ Gráfico optimizado y guardado")
    print(f"{'='*60}\n")
    
    return OptimizarGraficoResponse(
        success=True,
        pregunta_id=pregunta_id,
        mensaje="Gráfico optimizado correctamente",
        cambios=result.svg_spec.get("cambios_realizados") if isinstance(result.svg_spec, dict) else None,
        tokens_usados=result.tokens_used
    )
