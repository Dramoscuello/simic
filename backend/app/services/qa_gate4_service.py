"""
Gate 4: Validación Visual (Render Test) - Chart.js, Tablas y SVG Artístico
===========================================================================
Este servicio valida que los gráficos tengan estructuras consistentes
que se rendericen correctamente.

Checks implementados:
- Chart.js: labels.length === data.length para cada dataset
- Tablas: filas[i].length === columnas.length para cada fila
- SVG Artístico (Pre-enriquecimiento):
  - descripcion_visual presente y ≥30 caracteres
  - descripcion_visual no genérica ("un gráfico", etc.)
- SVG Artístico (Post-enriquecimiento):
  - svg_code tiene estructura válida (<svg>...</svg>)
  - svg_code tiene tamaño razonable (100B - 100KB)
  - svg_code no contiene scripts o event handlers (seguridad)
- Datos no vacíos

Nota: svg_spec (primitivas) se valida por SimulacroV2 Schema + SvgSpecRenderer.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from app.core.graphic_types import (
    SUPPORTED_GRAPH_TYPES,
    normalize_graph_type,
    normalize_graph_types_in_questions,
)


@dataclass
class RenderIssue:
    """Representa un problema de renderizado detectado"""
    pregunta_id: int
    tipo_grafico: str
    nivel: str  # "error" o "warning"
    mensaje: str


@dataclass
class Gate4Result:
    """Resultado de la validación de Gate 4"""
    passed: bool = True
    issues: List[RenderIssue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "issues": [
                {
                    "pregunta_id": i.pregunta_id,
                    "tipo_grafico": i.tipo_grafico,
                    "nivel": i.nivel,
                    "mensaje": i.mensaje
                }
                for i in self.issues
            ],
            "stats": self.stats
        }


class Gate4RenderValidator:
    """
    Validación de renderizado para gráficos Chart.js y Tablas
    
    Uso:
        result = Gate4RenderValidator.validar_graficos(contenido["preguntas"])
        if not result.passed:
            raise HTTPException(400, detail=result.to_dict())
    """
    
    @classmethod
    def validar_graficos(cls, preguntas: List[Dict]) -> Gate4Result:
        """
        Valida todos los gráficos del simulacro.
        
        Args:
            preguntas: Lista de preguntas del simulacro
            
        Returns:
            Gate4Result con issues encontrados
        """
        result = Gate4Result()
        result.stats["total_preguntas"] = len(preguntas)
        result.stats["con_grafico"] = 0
        result.stats["chartjs_validados"] = 0
        result.stats["tablas_validadas"] = 0
        result.stats["tipos_no_soportados"] = 0

        # Normaliza alias conocidos antes de validar (in-place).
        normalization_report = normalize_graph_types_in_questions(preguntas)
        if normalization_report.get("normalized_count", 0) > 0:
            result.stats["tipos_normalizados"] = normalization_report["normalized_count"]
        
        for pregunta in preguntas:
            if not pregunta.get("tiene_grafico", False):
                continue
            
            result.stats["con_grafico"] += 1
            pregunta_id = pregunta.get("id", 0)
            tipo_raw = pregunta.get("tipo_grafico", "")
            tipo = normalize_graph_type(tipo_raw)
            if tipo and tipo != tipo_raw:
                pregunta["tipo_grafico"] = tipo
            config = pregunta.get("configuracion_grafico")

            if not tipo or tipo not in SUPPORTED_GRAPH_TYPES:
                result.stats["tipos_no_soportados"] += 1
                allowed = ", ".join(sorted(SUPPORTED_GRAPH_TYPES))
                result.issues.append(RenderIssue(
                    pregunta_id=pregunta_id,
                    tipo_grafico=tipo or str(tipo_raw),
                    nivel="error",
                    mensaje=f"tipo_grafico no soportado. Permitidos: {allowed}"
                ))
                continue
            
            if not config:
                continue
            
            # Validar según tipo
            if tipo in {"chartjs_bar", "chartjs_line", "chartjs_pie", "chartjs_scatter"}:
                cls._validar_chartjs(pregunta_id, tipo, config, result)
                result.stats["chartjs_validados"] += 1
            elif tipo == "tabla_datos":
                cls._validar_tabla(pregunta_id, config, result)
                result.stats["tablas_validadas"] += 1
            elif tipo == "svg_artistico":
                cls._validar_svg_artistico(pregunta_id, config, result)
                result.stats["svg_artistico_validados"] = result.stats.get("svg_artistico_validados", 0) + 1
        
        # El gate pasa si no hay errores (warnings están OK)
        result.passed = not any(i.nivel == "error" for i in result.issues)
        
        return result

    @classmethod
    def _validar_svg_artistico(cls, pregunta_id: int, config: Dict, result: Gate4Result):
        """
        Valida SVG Artístico en dos fases:
        1. Pre-enriquecimiento: Verifica que descripcion_visual sea suficiente
        2. Post-enriquecimiento: Verifica que svg_code sea válido (si existe)
        """
        descripcion = config.get("descripcion_visual", "")
        svg_code = config.get("svg_code", "")
        
        # ===== FASE 1: Validación de descripcion_visual =====
        if not descripcion or not isinstance(descripcion, str):
            result.issues.append(RenderIssue(
                pregunta_id=pregunta_id,
                tipo_grafico="svg_artistico",
                nivel="error",
                mensaje="Falta 'descripcion_visual' para que el artista pueda dibujar"
            ))
            return
        
        descripcion_clean = descripcion.strip()
        
        # Check 1: Longitud mínima (30 chars para escenas útiles)
        if len(descripcion_clean) < 30:
            result.issues.append(RenderIssue(
                pregunta_id=pregunta_id,
                tipo_grafico="svg_artistico",
                nivel="error",
                mensaje=f"'descripcion_visual' muy corta ({len(descripcion_clean)} chars). Mínimo 30 para una escena clara."
            ))
        
        # Check 2: Descripciones demasiado genéricas (no aportan info al artista)
        descripciones_vagas = [
            "un gráfico", "una imagen", "un dibujo", "una figura",
            "a graph", "an image", "a drawing", "a figure"
        ]
        if descripcion_clean.lower() in descripciones_vagas:
            result.issues.append(RenderIssue(
                pregunta_id=pregunta_id,
                tipo_grafico="svg_artistico",
                nivel="error",
                mensaje="'descripcion_visual' es demasiado genérica. Debe describir la escena específica."
            ))
        
        # ===== FASE 2: Validación de svg_code (post-enriquecimiento) =====
        if svg_code:
            # Check 3: Estructura SVG básica
            if not svg_code.strip().startswith("<svg") or "</svg>" not in svg_code:
                result.issues.append(RenderIssue(
                    pregunta_id=pregunta_id,
                    tipo_grafico="svg_artistico",
                    nivel="error",
                    mensaje="'svg_code' no tiene estructura SVG válida (debe empezar con <svg> y terminar con </svg>)"
                ))
            
            # Check 4: Tamaño razonable (muy pequeño = vacío, muy grande = problema)
            svg_size = len(svg_code)
            if svg_size < 100:
                result.issues.append(RenderIssue(
                    pregunta_id=pregunta_id,
                    tipo_grafico="svg_artistico",
                    nivel="warning",
                    mensaje=f"'svg_code' muy pequeño ({svg_size} bytes). Podría ser un SVG vacío o incompleto."
                ))
            elif svg_size > 100000:  # 100KB
                result.issues.append(RenderIssue(
                    pregunta_id=pregunta_id,
                    tipo_grafico="svg_artistico",
                    nivel="warning",
                    mensaje=f"'svg_code' muy grande ({svg_size // 1000}KB). Podría causar problemas de rendimiento."
                ))
            
            # Check 5: Seguridad - No scripts maliciosos
            svg_lower = svg_code.lower()
            if "<script" in svg_lower or "javascript:" in svg_lower:
                result.issues.append(RenderIssue(
                    pregunta_id=pregunta_id,
                    tipo_grafico="svg_artistico",
                    nivel="error",
                    mensaje="'svg_code' contiene scripts JavaScript. Esto es un riesgo de seguridad."
                ))
            
            # Check 6: No event handlers inline
            event_handlers = ["onclick", "onload", "onerror", "onmouseover", "onfocus"]
            for handler in event_handlers:
                if handler in svg_lower:
                    result.issues.append(RenderIssue(
                        pregunta_id=pregunta_id,
                        tipo_grafico="svg_artistico",
                        nivel="error",
                        mensaje=f"'svg_code' contiene handler '{handler}'. Esto es un riesgo de seguridad."
                    ))
                    break  # Reportar solo el primero encontrado
    
    @classmethod
    def _validar_chartjs(cls, pregunta_id: int, tipo: str, config: Dict, result: Gate4Result):
        """Valida estructura de gráfico Chart.js"""
        
        # Puede venir como config.data o config directamente
        data = config.get("data", config)
        
        datasets = data.get("datasets", [])
        
        # Check 1: Datasets no vacío (aplica a todos)
        if not datasets:
            result.issues.append(RenderIssue(
                pregunta_id=pregunta_id,
                tipo_grafico=tipo,
                nivel="error",
                mensaje="El gráfico no tiene 'datasets' o está vacío"
            ))
            return
        
        # SCATTER usa puntos {x, y} - NO tiene labels
        if "scatter" in tipo.lower():
            cls._validar_chartjs_scatter(pregunta_id, tipo, datasets, result)
        else:
            # BAR, LINE, PIE usan labels
            cls._validar_chartjs_con_labels(pregunta_id, tipo, data, datasets, result)
    
    @classmethod
    def _validar_chartjs_scatter(cls, pregunta_id: int, tipo: str, datasets: List, result: Gate4Result):
        """Valida scatter que usa puntos {x, y} en vez de labels"""
        for idx, dataset in enumerate(datasets):
            dataset_data = dataset.get("data", [])
            
            if not dataset_data:
                result.issues.append(RenderIssue(
                    pregunta_id=pregunta_id,
                    tipo_grafico=tipo,
                    nivel="error",
                    mensaje=f"Dataset {idx + 1} no tiene 'data' o está vacío"
                ))
                continue
            
            # Verificar que cada punto tenga x e y
            for point_idx, point in enumerate(dataset_data):
                if not isinstance(point, dict):
                    result.issues.append(RenderIssue(
                        pregunta_id=pregunta_id,
                        tipo_grafico=tipo,
                        nivel="error",
                        mensaje=f"Dataset {idx + 1}, punto {point_idx + 1}: debe ser objeto {{x, y}}"
                    ))
                elif "x" not in point or "y" not in point:
                    result.issues.append(RenderIssue(
                        pregunta_id=pregunta_id,
                        tipo_grafico=tipo,
                        nivel="error",
                        mensaje=f"Dataset {idx + 1}, punto {point_idx + 1}: falta 'x' o 'y'"
                    ))
    
    @classmethod
    def _validar_chartjs_con_labels(cls, pregunta_id: int, tipo: str, data: Dict, datasets: List, result: Gate4Result):
        """Valida bar, line, pie que usan labels"""
        labels = data.get("labels", [])
        
        # Check: Labels no vacío
        if not labels:
            result.issues.append(RenderIssue(
                pregunta_id=pregunta_id,
                tipo_grafico=tipo,
                nivel="error",
                mensaje="El gráfico no tiene 'labels' o está vacío"
            ))
            return
        
        labels_count = len(labels)
        
        for idx, dataset in enumerate(datasets):
            dataset_data = dataset.get("data", [])
            
            if not dataset_data:
                result.issues.append(RenderIssue(
                    pregunta_id=pregunta_id,
                    tipo_grafico=tipo,
                    nivel="error",
                    mensaje=f"Dataset {idx + 1} no tiene 'data' o está vacío"
                ))
                continue
            
            data_count = len(dataset_data)
            
            if data_count != labels_count:
                result.issues.append(RenderIssue(
                    pregunta_id=pregunta_id,
                    tipo_grafico=tipo,
                    nivel="error",
                    mensaje=f"Dataset {idx + 1}: tiene {data_count} valores pero hay {labels_count} labels (deben coincidir)"
                ))
        
        # Check (Warning): Dataset sin label
        for idx, dataset in enumerate(datasets):
            if not dataset.get("label"):
                result.issues.append(RenderIssue(
                    pregunta_id=pregunta_id,
                    tipo_grafico=tipo,
                    nivel="warning",
                    mensaje=f"Dataset {idx + 1} no tiene 'label' (leyenda) definido"
                ))
    
    @classmethod
    def _validar_tabla(cls, pregunta_id: int, config: Dict, result: Gate4Result):
        """Valida estructura de tabla de datos"""
        
        columnas = config.get("columnas", [])
        filas = config.get("filas", [])
        
        # Check 1: Columnas no vacío
        if not columnas:
            result.issues.append(RenderIssue(
                pregunta_id=pregunta_id,
                tipo_grafico="tabla_datos",
                nivel="error",
                mensaje="La tabla no tiene 'columnas' o está vacío"
            ))
            return
        
        # Check 2: Filas no vacío
        if not filas:
            result.issues.append(RenderIssue(
                pregunta_id=pregunta_id,
                tipo_grafico="tabla_datos",
                nivel="error",
                mensaje="La tabla no tiene 'filas' o está vacío"
            ))
            return
        
        # Check 3: Cada fila tiene mismo número de elementos que columnas
        columnas_count = len(columnas)
        
        for idx, fila in enumerate(filas):
            fila_count = len(fila)
            
            if fila_count != columnas_count:
                result.issues.append(RenderIssue(
                    pregunta_id=pregunta_id,
                    tipo_grafico="tabla_datos",
                    nivel="error",
                    mensaje=f"Fila {idx + 1}: tiene {fila_count} celdas pero hay {columnas_count} columnas (deben coincidir)"
                ))
        
        # Check 4 (Warning): Celdas vacías
        for idx_fila, fila in enumerate(filas):
            for idx_col, celda in enumerate(fila):
                if celda is None or (isinstance(celda, str) and not celda.strip()):
                    result.issues.append(RenderIssue(
                        pregunta_id=pregunta_id,
                        tipo_grafico="tabla_datos",
                        nivel="warning",
                        mensaje=f"Fila {idx_fila + 1}, Columna {idx_col + 1}: celda vacía"
                    ))
