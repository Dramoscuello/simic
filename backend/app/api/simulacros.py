"""
Router principal de simulacros.

Este archivo mantiene un solo `router` y registra endpoints por categoría
importando módulos especializados (side effects).
"""

from app.api.simulacros_router import router

# CRUD / Listados / Borrado
from app.api import simulacros_crud  # noqa: F401

# Generación (sync/async) + Jobs + Gates
from app.api import simulacros_generation  # noqa: F401

# OMR (hojas, procesamiento y guardado)
from app.api import simulacros_omr  # noqa: F401

# Regeneración de preguntas específicas
from app.api import simulacros_regeneration  # noqa: F401

# Intentos de estudiante (finalizar, mi intento, intentos por usuario)
from app.api import simulacros_attempts  # noqa: F401

# Reportes grupales
from app.api import simulacros_reports  # noqa: F401

# Optimización de gráficos SVG con visión
from app.api import simulacros_graphics  # noqa: F401

__all__ = ["router"]
