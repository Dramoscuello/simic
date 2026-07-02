"""
Utilidades compartidas para normalización y validación de tipos gráficos.
"""

from typing import Any, Dict, List


SUPPORTED_GRAPH_TYPES = {
    "chartjs_bar",
    "chartjs_line",
    "chartjs_pie",
    "chartjs_scatter",
    "tabla_datos",
    "svg_artistico",
    "svg_geometrico",
    "diagrama_svg",
}


GRAPH_TYPE_ALIASES = {
    # Variantes Chart.js comunes
    "bar": "chartjs_bar",
    "line": "chartjs_line",
    "pie": "chartjs_pie",
    "scatter": "chartjs_scatter",
    "chartjs_doughnut": "chartjs_pie",
    "chartjs_donut": "chartjs_pie",
    "doughnut": "chartjs_pie",
    "donut": "chartjs_pie",
    # Variantes de mixtos no soportadas: degradar a bar para compatibilidad
    "chartjs_combined": "chartjs_bar",
    "chartjs_combo": "chartjs_bar",
    "chartjs_mixed": "chartjs_bar",
    "chartjs_mix": "chartjs_bar",
    # Variantes de tabla/svg
    "tabla": "tabla_datos",
    "table": "tabla_datos",
    "svg": "svg_artistico",
    "svg_art": "svg_artistico",
}


def normalize_graph_type(tipo: Any) -> str:
    """
    Normaliza un tipo gráfico a formato canónico (lowercase + alias mapping).
    """
    if tipo is None:
        return ""

    value = str(tipo).strip().lower().replace("-", "_").replace(" ", "_")
    if not value:
        return ""

    return GRAPH_TYPE_ALIASES.get(value, value)


def is_supported_graph_type(tipo: Any) -> bool:
    return normalize_graph_type(tipo) in SUPPORTED_GRAPH_TYPES


def normalize_graph_types_in_questions(preguntas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Normaliza `tipo_grafico` en una lista de preguntas in-place.

    Returns:
        dict con métricas de normalización para logging.
    """
    normalized_count = 0
    unsupported = []

    for p in preguntas or []:
        if not isinstance(p, dict):
            continue

        raw = p.get("tipo_grafico")
        if raw is None:
            continue

        normalized = normalize_graph_type(raw)
        if not normalized:
            continue

        raw_str = str(raw).strip()
        if raw_str != normalized:
            p["tipo_grafico"] = normalized
            normalized_count += 1

        if p.get("tiene_grafico") is True and normalized not in SUPPORTED_GRAPH_TYPES:
            unsupported.append({
                "pregunta_id": p.get("id"),
                "tipo_original": raw_str,
                "tipo_normalizado": normalized,
            })

    return {
        "normalized_count": normalized_count,
        "unsupported": unsupported,
    }
