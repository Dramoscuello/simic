from typing import List, Optional, Union, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.core.graphic_types import (
    SUPPORTED_GRAPH_TYPES,
    normalize_graph_type,
)

# --- Enums y Tipos Básicos ---

from enum import Enum

class DificultadEnum(str, Enum):
    facil = "facil"
    media = "media"
    dificil = "dificil"

class OpcionLetra(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"

# --- Modelos de Opciones ---

class Opcion(BaseModel):
    id: OpcionLetra
    texto: str

# --- Modelos de Gráficos: TABLAS y CHARTS ---

class TablaDatosConfig(BaseModel):
    columnas: List[str]
    filas: List[List[Union[str, int, float]]]
    descripcion_accesible: Optional[str] = None  # Descripción para accesibilidad

class ChartJsConfig(BaseModel):
    # 'type' es opcional porque ya viene en tipo_grafico del nivel pregunta
    type: Optional[str] = Field(None, description="Tipo de gráfico Chart.js (bar, line, pie, etc) - opcional, ya que tipo_grafico lo define")
    data: Dict[str, Any]
    options: Optional[Dict[str, Any]] = None
    descripcion_accesible: Optional[str] = None  # Algunos LLMs lo incluyen aquí

# --- Modelos de Gráficos: SVG GEOMETRICO (Visual Engine 2.0) ---

# Primitivas
class SvgRect(BaseModel):
    type: Literal["rect"]
    x: float
    y: float
    width: float
    height: float
    fill: Optional[str] = None
    stroke: Optional[str] = None
    transform: Optional[str] = None
    label: Optional[str] = None # A veces usado en primitivas

class SvgCircle(BaseModel):
    type: Literal["circle"]
    cx: float
    cy: float
    r: float
    fill: Optional[str] = None
    stroke: Optional[str] = None
    label: Optional[str] = None

class SvgLine(BaseModel):
    type: Literal["line"]
    x1: float
    y1: float
    x2: float
    y2: float
    stroke: Optional[str] = None
    stroke_width: Optional[float] = None

class SvgArrow(BaseModel):
    type: Literal["arrow"]
    x1: float
    y1: float
    x2: float
    y2: float
    label: Optional[str] = None
    color: Optional[str] = None # red, blue, etc.

class SvgText(BaseModel):
    type: Literal["text"]
    x: float
    y: float
    value: str
    fontSize: Optional[int] = 12
    fill: Optional[str] = None

class SvgPath(BaseModel):
    type: Literal["path"]
    d: str
    fill: Optional[str] = None
    stroke: Optional[str] = None
    transform: Optional[str] = None

class SvgPolygon(BaseModel):
    type: Literal["polygon"]
    points: str  # "x1,y1 x2,y2 x3,y3 ..."
    fill: Optional[str] = None
    stroke: Optional[str] = None

class SvgPolyline(BaseModel):
    type: Literal["polyline"]
    points: str
    fill: Optional[str] = None
    stroke: Optional[str] = None

class SvgEllipse(BaseModel):
    type: Literal["ellipse"]
    cx: float
    cy: float
    rx: float
    ry: float
    fill: Optional[str] = None
    stroke: Optional[str] = None

class SvgGroup(BaseModel):
    type: Literal["g", "group"]
    children: Optional[List[Any]] = None  # Shapes anidados
    transform: Optional[str] = None
    fill: Optional[str] = None
    stroke: Optional[str] = None

# Componentes Inteligentes (Smart Components)
class SvgComponentBase(BaseModel):
    type: Literal["component"]
    name: str
    x: Optional[float] = None
    y: Optional[float] = None
    label: Optional[str] = None
    # Params es un dict flexible, pero podríamos hacerlo estricto si quisiéramos
    # Por ahora lo dejamos flexible para permitir evolución rápida, 
    # o definimos campos específicos para los más comunes en el nivel superior si fuera necesario.
    params: Optional[Dict[str, Any]] = None 
    
    # Propiedades comunes que a veces se usan en top-level en vez de params
    width: Optional[float] = None
    height: Optional[float] = None
    x1: Optional[float] = None
    y1: Optional[float] = None
    x2: Optional[float] = None
    y2: Optional[float] = None
    rotation: Optional[float] = None
    
    # Props específicas de Biología/Genética que a veces salen directo
    p1: Optional[str] = None
    p2: Optional[str] = None
    size: Optional[float] = None

# Unión de todas las formas posibles
SvgShape = Union[
    SvgRect, SvgCircle, SvgLine, SvgArrow, SvgText, SvgPath,
    SvgPolygon, SvgPolyline, SvgEllipse, SvgGroup, SvgComponentBase
]

class SvgSpec(BaseModel):
    viewBox: str = "0 0 400 300"
    shapes: List[SvgShape]

class SvgGeometricoConfig(BaseModel):
    svg_spec: SvgSpec
    descripcion_accesible: Optional[str] = None

# --- Configuración Gráfica Polimórfica ---

class ConfiguracionGrafico(BaseModel):
    # Este modelo actúa como wrapper o unión manual
    # Para simplicidad en Pydantic V2 con JSON Schema, a veces es mejor un Dict
    # pero intentaremos validación estructural si es posible.
    # Dado que el campo en la DB es JSONB, aquí validamos la estructura interna.
    
    # OJO: La estructura del JSON plano a veces pone las claves directo en el objeto configuracion_grafico
    # Ejemplo ChartJS: { "labels": [...], "datasets": [...] } -> Esto no machea directo con los modelos de arriba.
    # Ejemplo SVG: { "svg_spec": {...} } -> Esto sí.
    
    # Para ser pragmáticos y compatibles con lo que el LLM genera (que a veces varía un poco),
    # usaremos un Dict genérico pero con validadores opcionales inteligentes.
    pass

# --- Pregunta ---

from pydantic import BaseModel, Field, field_validator, model_validator

# ... (Previous code remains)

class Pregunta(BaseModel):
    id: int
    competencia: str
    componente: str
    tema: str
    dificultad: Union[DificultadEnum, str]
    contexto: str
    enunciado: str
    texto_id: Optional[int] = None  # Para preguntas que referencian un texto compartido
    
    tiene_grafico: bool = False
    tipo_grafico: Optional[str] = None # svg_geometrico, chartjs_bar, tabla_datos, null
    # Permitir Dict[str, Any] como fallback para estructuras no estándar
    # La validación detallada se hace en Gate 4 (Visual)
    configuracion_grafico: Optional[Union[SvgGeometricoConfig, TablaDatosConfig, ChartJsConfig, Dict[str, Any]]] = None
    
    opciones: List[Opcion]
    respuesta_correcta: OpcionLetra
    justificacion: str

    @field_validator('opciones')
    def validar_cuatro_opciones(cls, v):
        if len(v) != 4:
            raise ValueError('Debe haber exactamente 4 opciones (A, B, C, D)')
        return v
    
    @field_validator('dificultad', mode='before')
    def normalizar_dificultad(cls, v):
        if isinstance(v, str):
            v = v.lower()
            if 'f' in v and 'cil' in v: return 'facil'
            if 'med' in v: return 'media'
            if 'dificil' in v or 'dif' in v: return 'dificil'
        return v

    @model_validator(mode='after')
    def validar_consistencia_grafica(self):
        if not self.tiene_grafico:
            return self

        if not self.tipo_grafico:
            # Si tiene_grafico es True pero no hay tipo, es sospechoso pero pase por ahora salvo q config exista
            if self.configuracion_grafico:
                raise ValueError("Se proporcionó configuracion_grafico pero tipo_grafico es nulo")
            return self

        tipo_normalizado = normalize_graph_type(self.tipo_grafico)
        if not tipo_normalizado:
            raise ValueError("tipo_grafico vacío o inválido")

        if tipo_normalizado not in SUPPORTED_GRAPH_TYPES:
            allowed = ", ".join(sorted(SUPPORTED_GRAPH_TYPES))
            raise ValueError(f"tipo_grafico no soportado: '{self.tipo_grafico}'. Permitidos: {allowed}")

        # Persistimos el valor canónico para consistencia interna.
        self.tipo_grafico = tipo_normalizado

        if self.tipo_grafico in ['svg_geometrico', 'diagrama_svg']:
            if not isinstance(self.configuracion_grafico, SvgGeometricoConfig):
                # Pydantic a veces convierte a dict si falla la validación del modelo específico antes de llegar aquí?
                # No, si Dict no está en Union, habrá fallado antes. 
                # Pero si es None:
                if self.configuracion_grafico is None:
                    raise ValueError("tipo_grafico es 'svg_geometrico' pero configuracion_grafico es nula")
                # Si llegó aquí es porque matcheó con otro tipo de la Union? Raro.
                # O porque es un objeto Pydantic de otro tipo.
        
        elif self.tipo_grafico == 'tabla_datos':
            if not isinstance(self.configuracion_grafico, TablaDatosConfig):
                 if self.configuracion_grafico is None:
                    raise ValueError("tipo_grafico es 'tabla_datos' pero configuracion_grafico es nula")

        elif self.tipo_grafico in ['chartjs_bar', 'chartjs_line', 'chartjs_pie', 'chartjs_scatter']:
            if not isinstance(self.configuracion_grafico, ChartJsConfig):
                 if self.configuracion_grafico is None:
                    raise ValueError(f"tipo_grafico es '{self.tipo_grafico}' pero configuracion_grafico es nula")

        return self

# --- Simulacro Completo ---

class SimulacroMetadata(BaseModel):
    area: str
    fecha_generacion: str
    total_preguntas: int

class Simulacro(BaseModel):
    meta: SimulacroMetadata
    preguntas: List[Pregunta]
