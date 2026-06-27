import os
import json
from openai import OpenAI
from openai import OpenAI
import logging
from datetime import datetime
from app.database.config import session_Local
from app.models.respuesta_estudiante import RespuestaEstudiante
from app.models.simulacro import Simulacro
from app.models.reporte_grupal import ReporteGrupal

# Configuración
logger = logging.getLogger(__name__)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "o3-mini"

# =====================================================================
# CONSTANTES OFICIALES ICFES - LECTURA CRÍTICA (Feb 2026)
# =====================================================================
AFIRMACIONES_LECTURA_CRITICA = {
    "Identificar y entender contenidos locales": {
        "nivel": "Literal",
        "porcentaje_oficial": 25,
        "descripcion": "Comprensión de palabras, frases y eventos explícitos"
    },
    "Comprender cómo se articulan las partes": {
        "nivel": "Inferencial", 
        "porcentaje_oficial": 42,
        "descripcion": "Estructura, relaciones entre partes, voces e ideas principales"
    },
    "Reflexionar y evaluar un texto": {
        "nivel": "Crítico",
        "porcentaje_oficial": 33,
        "descripcion": "Validez de argumentos, estrategias discursivas, relaciones intertextuales"
    }
}

EVIDENCIAS_LECTURA_CRITICA = [
    # Literal
    "Entiende el significado de elementos locales (palabras, frases)",
    "Identifica eventos, personajes y acciones explícitos",
    # Inferencial
    "Comprende la estructura formal del texto y su función",
    "Identifica voces o situaciones presentes en el texto",
    "Comprende relaciones entre partes o enunciados del texto",
    "Identifica y caracteriza ideas en textos informativos",
    "Identifica relaciones en textos discontinuos (tablas, gráficas)",
    # Crítico
    "Establece validez e implicaciones de enunciados",
    "Establece relaciones intertextuales",
    "Reconoce contenidos valorativos del texto",
    "Reconoce estrategias discursivas del autor",
    "Contextualiza adecuadamente el texto"
]

# =====================================================================
# CONSTANTES OFICIALES ICFES - SOCIALES Y CIUDADANAS (Feb 2026)
# =====================================================================
COMPETENCIAS_SOCIALES = {
    "Pensamiento Social": "30%",
    "Interpretación y análisis de perspectivas": "40%",
    "Pensamiento reflexivo y sistémico": "30%"
}

AFIRMACIONES_SOCIALES = [
    # Pensamiento Social
    "Comprende modelos conceptuales, sus características y contextos de aplicación",
    "Comprende dimensiones espaciales y temporales de eventos, problemáticas y prácticas sociales",
    # Interpretación
    "Contextualiza y evalúa usos de fuentes y argumentos",
    "Comprende perspectivas de distintos actores y grupos sociales",
    # Sistémico
    "Evalúa usos sociales de las ciencias sociales",
    "Comprende que los problemas y sus soluciones involucran distintas dimensiones y reconoce relaciones entre estas"
]

class AnalisisService:
    @staticmethod
    def procesar_respuesta(respuesta_id: int):
        """
        Calcula estadísticas detalladas y genera informe cualitativo con IA
        """
        db = session_Local()
        try:
            respuesta = db.query(RespuestaEstudiante).filter(RespuestaEstudiante.id == respuesta_id).first()
            if not respuesta:
                logger.error(f"RespuestaEstudiante {respuesta_id} no encontrada")
                return

            if respuesta.anulado:
                logger.warning(f"Abortando análisis para respuesta {respuesta_id}: intento anulado.")
                return

            if respuesta.fraude:
                logger.warning(f"Abortando análisis para respuesta {respuesta_id}: marcada como fraude.")
                return

            logger.info(f"Iniciando análisis para respuesta {respuesta_id}")

            # ---------------------------------------------------------
            # 1. CÁLCULO ESTADÍSTICO (Traducción de lógica JS)
            # ---------------------------------------------------------
            detalladas = respuesta.respuestas_detalladas or {}
            if not detalladas:
                logger.warning("No hay respuestas detalladas para analizar. Se generará informe con datos vacíos.")

            total_preguntas = 0
            aciertos = 0
            fallos = 0
            
            stats_competencias = {}
            stats_componentes = {}
            stats_temas = {}

            # Iterar sobre respuestas
            # detalladas es un dict: {"1": {...}, "2": {...}}
            for num, datos in detalladas.items():
                total_preguntas += 1
                es_acierto = datos.get("es_correcta", False) # Nota: Frontend/Backend guardan "es_correcta"
                
                if es_acierto:
                    aciertos += 1
                else:
                    fallos += 1
                
                # Helpers para agrupar
                def update_stats(store, key, hit):
                    if not key: key = "Sin Clasificar"
                    if key not in store:
                        store[key] = {"total": 0, "aciertos": 0, "fallos": 0}
                    store[key]["total"] += 1
                    if hit:
                        store[key]["aciertos"] += 1
                    else:
                        store[key]["fallos"] += 1

                update_stats(stats_competencias, datos.get("competencia"), es_acierto)
                update_stats(stats_componentes, datos.get("componente"), es_acierto)
                update_stats(stats_temas, datos.get("tema"), es_acierto)

            # Calcular porcentajes y estructuras finales
            porcentaje_general = round((aciertos / total_preguntas) * 100) if total_preguntas > 0 else 0
            
            def format_stats(store):
                result = []
                for nombre, s in store.items():
                    pct = round((s["aciertos"] / s["total"]) * 100) if s["total"] > 0 else 0
                    result.append({
                        "nombre": nombre,
                        "aciertos": s["aciertos"],
                        "total": s["total"],
                        "porcentaje": pct
                    })
                return result

            competencias_array = format_stats(stats_competencias)
            componentes_array = format_stats(stats_componentes)
            
            # Debilidades (< 60%)
            temas_list = format_stats(stats_temas)
            debilidades = sorted(
                [t for t in temas_list if t["porcentaje"] < 60],
                key=lambda x: x["porcentaje"]
            )[:5]
            
            # Fortalezas (>= 80%)
            fortalezas = sorted(
                [t for t in temas_list if t["porcentaje"] >= 80],
                key=lambda x: x["porcentaje"],
                reverse=True
            )[:3]
            
            # -------------------------------------------------------------------------
            # 1.5 CÁLCULO DE NIVEL ICFES (Dinámico por Área)
            # -------------------------------------------------------------------------
            area_raw = respuesta.simulacro.area
            # Normalizar nombre de área para matching
            area_key = "DEFAULT"
            if "matem" in area_raw.lower(): area_key = "MATEMATICAS"
            elif "natural" in area_raw.lower(): area_key = "CIENCIAS_NATURALES"
            elif "social" in area_raw.lower() or "ciudadan" in area_raw.lower(): area_key = "SOCIALES_CIUDADANAS"
            elif "lectura" in area_raw.lower(): area_key = "LECTURA_CRITICA"
            elif "ingl" in area_raw.lower(): area_key = "INGLES"

            # Definición de Niveles Oficiales (Score Ranges & Descriptores)
            NIVELES_ICFES = {
                "MATEMATICAS": [
                    {"nivel": 1, "min": 0, "max": 35, "desc": "Lee información puntual en tablas/gráficas con escala explícita. Dificultad con comparaciones complejas."},
                    {"nivel": 2, "min": 36, "max": 50, "desc": "Compara datos de dos variables, identifica patrones básicos y entiende promedios simples."},
                    {"nivel": 3, "min": 51, "max": 70, "desc": "Selecciona información pertinente para resolver problemas con aritmética. Interpreta gráficas no convencionales."},
                    {"nivel": 4, "min": 71, "max": 100, "desc": "Resuelve problemas complejos de probabilidad condicional, modelado algebraico y argumentación formal."}
                ],
                "CIENCIAS_NATURALES": [
                    {"nivel": 1, "min": 0, "max": 40, "desc": "Reconoce información explícita en tablas y gráficas de una variable con lenguaje cotidiano."},
                    {"nivel": 2, "min": 41, "max": 55, "desc": "Relaciona esquemas con nociones básicas (velocidad, filtración) e identifica patrones simples."},
                    {"nivel": 3, "min": 56, "max": 70, "desc": "Establece relaciones causa-efecto, interpreta modelos para predecir y diferencia evidencias de conclusiones."},
                    {"nivel": 4, "min": 71, "max": 100, "desc": "Usa conceptos y leyes para resolver problemas abstractos y contrasta modelos teóricos con la realidad."}
                ],
                "SOCIALES_CIUDADANAS": [
                    {"nivel": 1, "min": 0, "max": 40, "desc": "Reconoce derechos y factores de conflicto en situaciones sencillas. Identifica creencias básicas."},
                    {"nivel": 2, "min": 41, "max": 55, "desc": "Conoce deberes del Estado (Constitución) y relaciona conductas con cosmovisiones. Contextualiza fuentes."},
                    {"nivel": 3, "min": 56, "max": 70, "desc": "Identifica prejuicios, intereses y dimensiones en problemas sociales. Valora fuentes y reconoce conceptos básicos."},
                    {"nivel": 4, "min": 71, "max": 100, "desc": "Analiza mecanismos de participación y reforma. Compara argumentos complejos e infiere intenciones en fuentes."}
                ],
                "LECTURA_CRITICA": [
                    {"nivel": 1, "min": 0, "max": 35, "desc": "Identifica elementos literales en textos continuos y discontinuos sin establecer relaciones de significado."},
                    {"nivel": 2, "min": 36, "max": 50, "desc": "Comprende textos de manera literal, relaciona información explícita con contexto e identifica estructura básica."},
                    {"nivel": 3, "min": 51, "max": 65, "desc": "Infiere contenidos implícitos, jerarquiza información y reconoce estrategias discursivas y juicios valorativos."},
                    {"nivel": 4, "min": 66, "max": 100, "desc": "Reflexiona sobre la visión del autor, evalúa argumentos, relaciona múltiples textos y asume postura crítica."}
                ],
                "INGLES": [
                    {"nivel": "Pre A1", "min": 0, "max": 36, "desc": "Reconoce vocabulario muy básico y comprende instrucciones simples con lenguaje familiar."},
                    {"nivel": "A1", "min": 37, "max": 57, "desc": "Comprende información personal y cotidiana simple. Entiende avisos y textos cortos familiares."},
                    {"nivel": "A2", "min": 58, "max": 70, "desc": "Comprende textos sencillos sobre temas cotidianos (ocupaciones, familia). Identifica ideas en pasado/futuro."},
                    {"nivel": "B1", "min": 71, "max": 100, "desc": "Infiere significado en diversos textos (académico, laboral). Identifica puntos de vista y sentimientos."}
                ],
                "DEFAULT": [ # Fallback genérico
                    {"nivel": 1, "min": 0, "max": 39, "desc": "Desempeño inicial. Requiere refuerzo en conceptos fundamentales."},
                    {"nivel": 2, "min": 40, "max": 59, "desc": "Desempeño básico. Comprende conceptos literales pero falla en inferencias."},
                    {"nivel": 3, "min": 60, "max": 79, "desc": "Desempeño satisfactorio. Capacidad de análisis e inferencia correcta."},
                    {"nivel": 4, "min": 80, "max": 100, "desc": "Desempeño avanzado. Dominio profundo y capacidad crítica."}
                ]
            }

            # Seleccionar tabla de niveles adecuada
            niveles_area = NIVELES_ICFES.get(area_key, NIVELES_ICFES["DEFAULT"])
            
            # Calcular Nivel
            nivel_obj = niveles_area[0] # Default nivel 1
            for n in niveles_area:
                if n["min"] <= porcentaje_general <= n["max"]:
                    nivel_obj = n
                    break
            
            # Ajuste para Inglés que usa texto (A1, B1) en vez de números
            if area_key == "INGLES":
                nivel_texto = f"Nivel {nivel_obj['nivel']} (MCER) - ({nivel_obj['min']}-{nivel_obj['max']})"
            else:
                nivel_texto = f"Nivel {nivel_obj['nivel']} ({nivel_obj['min']}-{nivel_obj['max']})"
            
            nivel_descripcion = nivel_obj['desc']

            # CORRECCIÓN PARA PUNTAJE CERO (Evitar contradicciones en el informe)
            if porcentaje_general == 0:
                if area_key == "LECTURA_CRITICA":
                    nivel_descripcion = "El estudiante no evidencia desarrollo de competencias lectoras básicas en esta prueba. Se requiere iniciar con ejercicios de literalidad simple."
                elif area_key == "INGLES":
                    nivel_descripcion = "El estudiante no demuestra conocimientos básicos de vocabulario o gramática en esta prueba (Inferior a Pre-A1)."
                elif area_key == "SOCIALES_CIUDADANAS":
                    nivel_descripcion = "El estudiante no evidencia comprensión de los conceptos básicos de sociales ni competencias ciudadanas en esta prueba."
                else:
                    nivel_descripcion = "El desempeño es insuficiente. No se evidencia dominio de los conceptos básicos evaluados."

            analisis_estructurado = {
                "general": {
                    "total": total_preguntas,
                    "aciertos": aciertos,
                    "fallos": fallos,
                    "porcentaje": porcentaje_general,
                    "nivel": nivel_texto, # UI mostrará "Nivel X"
                    "nivel_descripcion": nivel_descripcion
                },
                "competencias": competencias_array,
                "componentes": componentes_array,
                "debilidades": debilidades,
                "fortalezas": fortalezas
            }

            # -------------------------------------------------------------------------
            # 2. GENERACIÓN DE INFORME CON IA (Groq)
            # -------------------------------------------------------------------------
            
            # Lógica Condicional: Temas vs Competencias según Área
            usar_competencias_como_debilidad = area_key in ["INGLES", "LECTURA_CRITICA", "SOCIALES_CIUDADANAS"]
            
            # Para Lectura Crítica: Enriquecer competencias con nivel oficial
            if area_key == "LECTURA_CRITICA":
                for comp in competencias_array:
                    afirm_info = AFIRMACIONES_LECTURA_CRITICA.get(comp["nombre"])
                    if afirm_info:
                        # Agregar nivel (Literal/Inferencial/Crítico) al nombre para claridad
                        comp["nombre_display"] = f"{afirm_info['nivel']}: {comp['nombre']}"
                        comp["nivel"] = afirm_info["nivel"]
                    else:
                        comp["nombre_display"] = comp["nombre"]
                        comp["nivel"] = "General"
                
                txt_competencias = "\n".join([
                    f"- {c.get('nombre_display', c['nombre'])}: {c['porcentaje']}% acierto" 
                    for c in competencias_array
                ])
            elif area_key == "SOCIALES_CIUDADANAS":
                # Enriquecer con porcentaje oficial esperado
                for comp in competencias_array:
                    pct_oficial = COMPETENCIAS_SOCIALES.get(comp["nombre"], "")
                    if pct_oficial:
                        comp["nombre_display"] = f"{comp['nombre']} (Meta: {pct_oficial})"
                    else:
                        comp["nombre_display"] = comp["nombre"]

                txt_competencias = "\n".join([
                    f"- {c.get('nombre_display', c['nombre'])}: {c['porcentaje']}% acierto" 
                    for c in competencias_array
                ])
            else:
                txt_competencias = "\n".join([f"- {c['nombre']}: {c['porcentaje']}% acierto" for c in competencias_array])
            
            if usar_competencias_como_debilidad:
                # Para Inglés/Lectura/Sociales: Usar AFIRMACIONES o COMPONENTES como estructurales
                
                # Selección de fuente de debilidades
                if area_key == "SOCIALES_CIUDADANAS":
                    # En Sociales, las Afirmaciones están en 'componentes'
                    source_array = componentes_array
                else:
                    # En Lectura e Inglés, preferimos competencias (que son las afirmaciones grandes o skills)
                    # a menos que solo haya componentes
                    source_array = competencias_array if competencias_array else componentes_array

                debilidades_estructurales = sorted(source_array, key=lambda x: x["porcentaje"])[:3]
                
                if area_key == "LECTURA_CRITICA":
                    txt_debilidades = "\n".join([
                        f"- {d.get('nombre_display', d['nombre'])} ({d['porcentaje']}% acierto)" 
                        for d in debilidades_estructurales
                    ]) or "Ninguna crítica"
                    label_debilidades = "AFIRMACIONES CRÍTICAS (Literal/Inferencial/Crítico)"
                elif area_key == "SOCIALES_CIUDADANAS":
                    txt_debilidades = "\n".join([
                         f"- {d['nombre']} ({d['porcentaje']}% acierto)"
                         for d in debilidades_estructurales
                    ]) or "Ninguna crítica"
                    label_debilidades = "AFIRMACIONES CRÍTICAS (Conceptos y Perspectivas)"
                else:
                    txt_debilidades = "\n".join([f"- {d['nombre']} ({d['porcentaje']}% acierto)" for d in debilidades_estructurales]) or "Ninguna crítica"
                    label_debilidades = "COMPETENCIAS/COMPONENTES CRÍTICOS"
            else:
                # Para Matemáticas/Ciencias/Sociales: Usar TEMAS específicos
                txt_debilidades = "\n".join([f"- {d['nombre']} ({d['porcentaje']}% acierto)" for d in debilidades]) or "Ninguna crítica"
                label_debilidades = "TEMAS CRÍTICOS (Conceptos específicos)"

            # Identificar competencia más débil para el prompt
            comp_debil = min(competencias_array, key=lambda x: x['porcentaje']) if competencias_array else None
            txt_comp_debil = f"{comp_debil['nombre']} ({comp_debil['porcentaje']}%)" if comp_debil else "N/A"

            student_name = respuesta.usuario.nombre if respuesta.usuario else "Estudiante"
            student_doc = respuesta.usuario.documento if respuesta.usuario and hasattr(respuesta.usuario, 'documento') else "N/A"

            prompt = f"""
ANÁLISIS PEDAGÓGICO DE SIMULACRO ICFES ({area_raw})

ESTUDIANTE: {student_name}
PUNTAJE GLOBAL: {porcentaje_general}% ({aciertos}/{total_preguntas} aciertos)

📌 DIAGNÓSTICO DE NIVEL (SEGÚN ESTÁNDAR ICFES):
El estudiante se ubica en el **{nivel_texto}**.
Descripción del Nivel: "{nivel_descripcion}"

📉 ANÁLISIS DE BRECHAS:
Competencia más débil: {txt_comp_debil}
{label_debilidades} A REFORZAR:
{txt_debilidades}

📊 DESGLOSE DE COMPETENCIAS:
{txt_competencias}

---
TU TAREA:
Genera un informe pedagógico profesional en TERCERA PERSONA, redactado para que lo lea un docente o coordinador académico (NO el estudiante directamente).
Usa tono profesional, objetivo y pedagógico. NO uses "tú", "te", ni te dirijas al estudiante. Habla SOBRE el estudiante.

ESTRUCTURA DEL INFORME (Markdown):

## 📋 Reporte de Desempeño: {student_name}
(Un título así para iniciar)

1. **Nivel de Desempeño Alcanzado**: Explica qué significa que {student_name} esté en {nivel_texto}. Usa la descripción provista.

2. **Áreas de Oportunidad**: Analiza la competencia más débil del estudiante. Explica por qué está fallando ahí, relacionándolo con los *{label_debilidades.title()}* listados.
   - NOTA PARA LECTURA CRÍTICA: Las 3 afirmaciones oficiales son:
     * Literal (25%): Identificar y entender contenidos locales (palabras, eventos explícitos)
     * Inferencial (42%): Comprender cómo se articulan las partes (estructura, relaciones, voces)
     * Crítico (33%): Reflexionar y evaluar un texto (validez, estrategias discursivas, intertextualidad)
   - Enfócate en qué nivel de lectura tiene más dificultad y por qué.

3. **Recomendaciones de Refuerzo**: Sugiere 3 acciones concretas que el docente puede implementar con este estudiante.
   - Para Lectura Crítica: Sugiere ejercicios según el nivel débil:
     * Si falla en Literal: Ejercicios de vocabulario, identificación de eventos
     * Si falla en Inferencial: Análisis de estructura textual, identificación de tesis
     * Si falla en Crítico: Ejercicios de argumentación, comparación de textos

4. **Fortalezas Identificadas**: Breve reconocimiento de lo que hace bien.

---
INSTRUCCIÓN DE RAZONAMIENTO (CHAIN-OF-THOUGHT IMPLÍCITO):
Antes de escribir el informe final, realiza internamente el siguiente diagnóstico clínico:
1. **Identifica el Patrón de Error**: ¿La falla es por falta de conocimiento base (Nivel 1) o por falta de profundidad analítica (Nivel 3)?
   - Si es Lectura Crítica: ¿Falla en extraer datos (Literal) o en conectar ideas (Inferencial)?
   - Si es Matemáticas: ¿Falla en el cálculo (Ejecución) o en el planteamiento (Formulación)?
2. **Prioriza la Intervención**: Selecciona la recomendación que tendría MAYOR impacto inmediato. No des consejos genéricos como "estudiar más". Sé específico (ej: "Practicar regla de tres simple", "Identificar la voz pasiva").
3. **Redacta el Informe**: Usa este análisis previo para escribir las secciones de 'Áreas de Oportunidad' y 'Recomendaciones' de forma precisa y quirúrgica.
"""

            logger.info("Enviando solicitud a OpenAI (o3-mini)...")
            
            informe_texto = "No se pudo generar el informe."
            
            if OPENAI_API_KEY:
                try:
                    client = OpenAI(api_key=OPENAI_API_KEY)
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[
                             {
                                "role": "system",
                                "content": "Eres un analista pedagógico experto del ICFES colombiano. Generas informes profesionales en tercera persona para que los lean docentes y coordinadores académicos, NO estudiantes. Tu lenguaje es técnico, objetivo y orientado a la acción pedagógica."
                             },
                             {
                                "role": "user",
                                "content": prompt
                             }
                        ],
                        reasoning_effort="high"
                    )
                    informe_texto = response.choices[0].message.content
                except Exception as e:
                    logger.error(f"Excepción llamando a OpenAI: {e}")
                    informe_texto = f"Error al generar informe IA: {str(e)}"
            else:
                 logger.warning("OPENAI_API_KEY no configurada. Saltando generación IA.")
                 informe_texto = "El servicio de IA no está configurado. Análisis estadístico disponible."

            # ---------------------------------------------------------
            # 2.9 VERIFICACIÓN DE CONDICIÓN DE CARRERA (Race Condition Fix)
            # ---------------------------------------------------------
            # Refrescamos desde BD para ver si un Admin marcó fraude mientras procesábamos
            db.refresh(respuesta)
            if respuesta.fraude:
                logger.warning(f"Abortando guardado de análisis IA para respuesta {respuesta_id}: Marcada como fraude.")
                # Asegurar limpieza por si acaso
                respuesta.analisis_ia = None
                respuesta.informe_generado = False
                respuesta.informe_url = None
                db.commit()
                return

            # ---------------------------------------------------------
            # 3. GUARDAR RESULTADOS
            # ---------------------------------------------------------
            analisis_completo = {
                "estadisticas": analisis_estructurado,
                "informe_ia": informe_texto,
                "metadata": {
                    "modelo": MODEL_NAME,
                    "generado_el": "now()" # Placeholder
                }
            }
            
            respuesta.analisis_ia = analisis_completo
            respuesta.informe_generado = True
            
            db.commit()
            logger.info(f"Análisis guardado exitosamente para respuesta {respuesta_id}")

        except Exception as e:
            logger.error(f"Error crítico en AnalisisService: {e}")
            db.rollback()
        finally:
            db.close()

    def generar_reporte_grupal(simulacro_id: int, institucion_id: int):
        """
        Genera reporte grupal NUMÉRICO (determinístico) para un simulacro/área.
        Reglas:
        - Solo considera intentos finalizados
        - Incluye fraude como puntaje 0
        """
        db = session_Local()
        try:
            # 1. Obtener respuestas finalizadas de la institución para el simulacro
            respuestas = db.query(RespuestaEstudiante).filter(
                RespuestaEstudiante.simulacro_id == simulacro_id,
                RespuestaEstudiante.institucion_id == institucion_id,
                RespuestaEstudiante.fecha_finalizacion.isnot(None),
                RespuestaEstudiante.anulado.is_(False)
            ).all()
            
            if not respuestas:
                return None, {"error": "No hay respuestas finalizadas para analizar"}
            if len(respuestas) <= 1:
                return None, {"error": "Se requieren al menos 2 respuestas finalizadas para generar el reporte grupal"}

            simulacro = db.query(Simulacro).filter(Simulacro.id == simulacro_id).first()
            if not simulacro:
                return None, {"error": "Simulacro no encontrado"}

            def normalizar_area(area_raw: str):
                n = (area_raw or "").lower()
                if "matem" in n:
                    return "MATEMATICAS", "Matemáticas"
                if "lectura" in n:
                    return "LECTURA_CRITICA", "Lectura Crítica"
                if "social" in n or "ciudadan" in n:
                    return "SOCIALES_CIUDADANAS", "Sociales y Ciudadanas"
                if "natural" in n or "ciencia" in n:
                    return "CIENCIAS_NATURALES", "Ciencias Naturales"
                if "ingl" in n:
                    return "INGLES", "Inglés"
                fallback = (area_raw or "GENERAL").upper().replace(" ", "_")
                return fallback, (area_raw or "General")

            area_code, area_display = normalizar_area(simulacro.area)

            institucion_nombre = respuestas[0].institucion.nombre if respuestas[0].institucion else "Institución"

            # 2. Cálculo determinístico (fraude cuenta como 0)
            puntajes = []
            estudiantes_reporte = []
            for r in respuestas:
                estudiante_nombre = r.usuario.nombre if r.usuario and r.usuario.nombre else f"Estudiante {r.usuario_id}"
                if r.fraude:
                    score = 0.0
                else:
                    score = float(r.puntaje_total) if r.puntaje_total is not None else 0.0
                score = round(score, 2)
                puntajes.append(score)
                estudiantes_reporte.append({
                    "name": estudiante_nombre,
                    "score_100": score
                })

            estudiantes_reporte = sorted(estudiantes_reporte, key=lambda x: x["name"].lower())

            total_estudiantes = len(puntajes)
            promedio = round(sum(puntajes) / total_estudiantes, 2)
            min_score = round(min(puntajes), 2)
            max_score = round(max(puntajes), 2)
            generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

            # 3. Nivel de desempeño del promedio grupal (intervalos por área)
            level_ranges = {
                "MATEMATICAS": [
                    (0, 35, "Nivel 1"),
                    (36, 50, "Nivel 2"),
                    (51, 70, "Nivel 3"),
                    (71, 100, "Nivel 4"),
                ],
                "LECTURA_CRITICA": [
                    (0, 35, "Nivel 1"),
                    (36, 50, "Nivel 2"),
                    (51, 65, "Nivel 3"),
                    (66, 100, "Nivel 4"),
                ],
                "CIENCIAS_NATURALES": [
                    (0, 40, "Nivel 1"),
                    (41, 55, "Nivel 2"),
                    (56, 70, "Nivel 3"),
                    (71, 100, "Nivel 4"),
                ],
                "SOCIALES_CIUDADANAS": [
                    (0, 40, "Nivel 1"),
                    (41, 55, "Nivel 2"),
                    (56, 70, "Nivel 3"),
                    (71, 100, "Nivel 4"),
                ],
                "INGLES": [
                    (0, 36, "Pre A1"),
                    (37, 57, "A1"),
                    (58, 70, "A2"),
                    (71, 100, "B1"),
                ],
                "DEFAULT": [
                    (0, 39, "Nivel 1"),
                    (40, 59, "Nivel 2"),
                    (60, 79, "Nivel 3"),
                    (80, 100, "Nivel 4"),
                ],
            }

            selected_ranges = level_ranges.get(area_code, level_ranges["DEFAULT"])
            performance_level = "N/A"
            performance_interval = "N/A"
            for min_v, max_v, lvl in selected_ranges:
                if min_v <= promedio <= max_v:
                    performance_level = lvl
                    performance_interval = f"{min_v}-{max_v}"
                    break

            metadata = {
                "tipo_reporte": "grupal_numerico",
                "scale": "0-100",
                "simulacro_id": simulacro_id,
                "simulacro_titulo": simulacro.titulo,
                "institucion_id": institucion_id,
                "institution_name": institucion_nombre,
                "area": area_code,
                "area_display": area_display,
                "students_count": total_estudiantes,
                "average_score_100": promedio,
                "min_score_100": min_score,
                "max_score_100": max_score,
                "performance_level": performance_level,
                "performance_interval": performance_interval,
                "generated_at": generated_at,
                "students": estudiantes_reporte
            }

            # Markdown de compatibilidad para no romper vistas legacy.
            tabla_header = "| # | Estudiante | Nota (N/100) |\n|---|---|---|\n"
            tabla_rows = []
            for idx, est in enumerate(estudiantes_reporte, start=1):
                tabla_rows.append(f"| {idx} | {est['name']} | {est['score_100']}/100 |")
            tabla_md = tabla_header + "\n".join(tabla_rows)

            informe_txt = (
                "## Reporte Grupal Numérico\n\n"
                f"- **Institución:** {institucion_nombre}\n"
                f"- **Área:** {area_display}\n"
                f"- **Cantidad de estudiantes (finalizados):** {total_estudiantes}\n"
                f"- **Promedio grupal:** **{promedio}/100**\n"
                f"- **Nivel de desempeño del promedio:** **{performance_level}** (rango {performance_interval})\n"
                f"- **Rango:** {min_score}/100 a {max_score}/100\n"
                f"- **Fecha de generación:** {generated_at}\n\n"
                "### Reporte general\n\n"
                f"{tabla_md}\n"
            )

            return informe_txt, metadata

        except Exception as e:
            logger.error(f"Error reporte grupal: {e}")
            return None, {"error": str(e)}
        finally:
            db.close()


