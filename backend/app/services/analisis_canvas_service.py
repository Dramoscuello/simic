from __future__ import annotations

import unicodedata
from collections import defaultdict
from datetime import datetime
from typing import Dict, Iterable, List, Tuple

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.grupo import Grupo
from app.models.respuesta_estudiante import RespuestaEstudiante
from app.models.rol import Rol
from app.models.simulacro import Simulacro
from app.models.usuario import Usuario
from app.schemas.analisis import (
    AreaMetricasResponse,
    AreaMetricasTendencia,
    AreaRef,
    CanvasNodeDTO,
    EntityRef,
    ResumenCompetenciaItem,
    SerieCompetenciaItem,
    SerieCompetenciaPunto,
    SeriePuntajeItem,
)


class AnalisisCanvasService:
    AREA_DISPLAY_MAP: Dict[str, str] = {
        "MATEMATICAS": "Matemáticas",
        "LECTURA_CRITICA": "Lectura Crítica",
        "CIENCIAS_NATURALES": "Ciencias Naturales",
        "SOCIALES_CIUDADANAS": "Sociales y Ciudadanas",
        "INGLES": "Inglés",
    }

    AREA_ALIASES: Dict[str, set[str]] = {
        "MATEMATICAS": {"MATEMATICAS"},
        "LECTURA_CRITICA": {"LECTURA_CRITICA", "LECTURA CRITICA"},
        "CIENCIAS_NATURALES": {"CIENCIAS_NATURALES", "CIENCIAS NATURALES"},
        "SOCIALES_CIUDADANAS": {
            "SOCIALES_CIUDADANAS",
            "SOCIALES CIUDADANAS",
            "CIENCIAS SOCIALES",
            "SOCIALES Y CIUDADANAS",
        },
        "INGLES": {"INGLES"},
    }

    @classmethod
    def _normalize_text(cls, value: str) -> str:
        text = unicodedata.normalize("NFKD", value or "")
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        return text.upper().strip().replace("-", " ").replace("_", " ")

    @classmethod
    def normalize_area_code(cls, value: str) -> str | None:
        normalized = cls._normalize_text(value)
        for code, aliases in cls.AREA_ALIASES.items():
            if normalized in aliases:
                return code
        return None

    @classmethod
    def area_display_name(cls, code: str) -> str:
        return cls.AREA_DISPLAY_MAP.get(code, code.replace("_", " ").title())

    @classmethod
    def _area_raw_values(cls, code: str) -> List[str]:
        if code == "MATEMATICAS":
            return ["MATEMATICAS", "Matemáticas"]
        if code == "LECTURA_CRITICA":
            return ["LECTURA_CRITICA", "Lectura Crítica"]
        if code == "CIENCIAS_NATURALES":
            return ["CIENCIAS_NATURALES", "Ciencias Naturales"]
        if code == "SOCIALES_CIUDADANAS":
            return ["SOCIALES_CIUDADANAS", "Ciencias Sociales", "Sociales y Ciudadanas"]
        if code == "INGLES":
            return ["INGLES", "Inglés"]
        return [code]

    @staticmethod
    def _validar_admin(admin_user: Usuario) -> None:
        role_name = admin_user.rol.nombre if admin_user.rol else None
        if role_name not in ["admin", "docente"]:
            raise HTTPException(status_code=403, detail="Solo admin o docente puede usar este módulo")
        if not admin_user.institucion_id:
            raise HTTPException(status_code=400, detail="El usuario no tiene institución asignada")

    @staticmethod
    def _obtener_grupo(db: Session, grupo_id: int) -> Grupo:
        grupo = db.query(Grupo).filter(Grupo.id == grupo_id).first()
        if not grupo:
            raise HTTPException(status_code=404, detail="Grupo no encontrado")
        return grupo

    @staticmethod
    def _obtener_estudiante(db: Session, estudiante_id: int) -> Usuario:
        estudiante = db.query(Usuario).filter(Usuario.id == estudiante_id).first()
        if not estudiante:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        return estudiante

    @classmethod
    def _validar_scope(
        cls,
        db: Session,
        admin_user: Usuario,
        grupo_id: int,
        estudiante_id: int,
    ) -> Tuple[Grupo, Usuario]:
        cls._validar_admin(admin_user)
        grupo = cls._obtener_grupo(db, grupo_id)
        estudiante = cls._obtener_estudiante(db, estudiante_id)

        if grupo.institucion_id != admin_user.institucion_id:
            raise HTTPException(status_code=403, detail="No tiene permisos sobre este grupo")

        if estudiante.institucion_id != admin_user.institucion_id:
            raise HTTPException(status_code=403, detail="No tiene permisos sobre este estudiante")

        if estudiante.grupo_id != grupo_id:
            raise HTTPException(status_code=403, detail="El estudiante no pertenece al grupo indicado")

        return grupo, estudiante

    @staticmethod
    def _safe_float(value) -> float:
        if value is None:
            return 0.0
        return round(float(value), 2)

    @staticmethod
    def _is_hit(detalle: Dict) -> bool:
        if "es_correcta" in detalle and detalle.get("es_correcta") is not None:
            return bool(detalle.get("es_correcta"))
        return bool(detalle.get("acierto"))

    @classmethod
    def _calcular_tendencia(cls, serie: List[SeriePuntajeItem]) -> AreaMetricasTendencia:
        if len(serie) < 2:
            return AreaMetricasTendencia(
                estado="estable",
                pendiente=0.0,
                umbral_estable=1.0,
                delta_primer_ultimo=0.0,
                confiabilidad_baja=True,
            )

        y_values = [p.puntaje_total for p in serie]
        n = len(y_values)
        x_values = list(range(1, n + 1))

        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xx = sum(x * x for x in x_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        denominator = (n * sum_xx) - (sum_x * sum_x)
        slope = 0.0 if denominator == 0 else ((n * sum_xy) - (sum_x * sum_y)) / denominator
        slope = round(float(slope), 4)

        if slope > 1.0:
            state = "subiendo"
        elif slope < -1.0:
            state = "bajando"
        else:
            state = "estable"

        delta = round(y_values[-1] - y_values[0], 2)
        return AreaMetricasTendencia(
            estado=state,
            pendiente=slope,
            umbral_estable=1.0,
            delta_primer_ultimo=delta,
            confiabilidad_baja=False,
        )

    @classmethod
    def _query_valid_attempts(cls, db: Session, estudiante_id: int, area_code: str | None = None):
        query = (
            db.query(RespuestaEstudiante, Simulacro)
            .join(Simulacro, Simulacro.id == RespuestaEstudiante.simulacro_id)
            .filter(
                RespuestaEstudiante.usuario_id == estudiante_id,
                RespuestaEstudiante.fecha_finalizacion.isnot(None),
                RespuestaEstudiante.anulado.is_(False),
                RespuestaEstudiante.fraude.is_(False),
                RespuestaEstudiante.puntaje_total.isnot(None),
            )
        )
        if area_code:
            query = query.filter(Simulacro.area.in_(cls._area_raw_values(area_code)))
        return query.order_by(
            RespuestaEstudiante.fecha_finalizacion.asc(),
            RespuestaEstudiante.created_at.asc(),
        )

    @classmethod
    def get_group_nodes(cls, db: Session, admin_user: Usuario) -> List[CanvasNodeDTO]:
        cls._validar_admin(admin_user)

        is_docente = admin_user.rol.nombre == 'docente'

        student_counts_query = (
            db.query(Usuario.grupo_id, func.count(Usuario.id))
            .join(Rol, Rol.id == Usuario.rol_id)
            .filter(
                Usuario.institucion_id == admin_user.institucion_id,
                Usuario.grupo_id.isnot(None),
                Rol.nombre == "estudiante",
            )
        )
        if is_docente and admin_user.sede_id:
            student_counts_query = student_counts_query.filter(Usuario.sede_id == admin_user.sede_id)
        student_counts = dict(student_counts_query.group_by(Usuario.grupo_id).all())

        groups_query = (
            db.query(Grupo)
            .filter(Grupo.institucion_id == admin_user.institucion_id)
        )
        if is_docente and admin_user.sede_id:
            groups_query = groups_query.filter(Grupo.sede_id == admin_user.sede_id)
        groups = groups_query.order_by(Grupo.nombre.asc()).all()

        return [
            CanvasNodeDTO(
                id=f"group-{g.id}",
                type="group",
                label=g.nombre,
                meta={
                    "grupo_id": g.id,
                    "estudiantes": int(student_counts.get(g.id, 0)),
                    "sede_id": g.sede_id,
                    "sede_nombre": g.sede.nombre if g.sede else None,
                },
            )
            for g in groups
        ]

    @classmethod
    def get_student_nodes(cls, db: Session, admin_user: Usuario, grupo_id: int) -> List[CanvasNodeDTO]:
        cls._validar_admin(admin_user)
        grupo = cls._obtener_grupo(db, grupo_id)
        if grupo.institucion_id != admin_user.institucion_id:
            raise HTTPException(status_code=403, detail="No tiene permisos sobre este grupo")

        students = (
            db.query(Usuario)
            .join(Rol, Rol.id == Usuario.rol_id)
            .filter(
                Usuario.institucion_id == admin_user.institucion_id,
                Usuario.grupo_id == grupo_id,
                Rol.nombre == "estudiante",
            )
            .order_by(Usuario.nombre.asc())
            .all()
        )

        return [
            CanvasNodeDTO(
                id=f"student-{s.id}",
                type="student",
                label=s.nombre,
                meta={
                    "estudiante_id": s.id,
                    "grupo_id": grupo_id,
                    "numero_documento": s.numero_documento,
                },
            )
            for s in students
        ]

    @classmethod
    def get_area_nodes(
        cls,
        db: Session,
        admin_user: Usuario,
        grupo_id: int,
        estudiante_id: int,
    ) -> List[CanvasNodeDTO]:
        cls._validar_scope(db, admin_user, grupo_id, estudiante_id)
        attempts = cls._query_valid_attempts(db, estudiante_id).all()

        area_stats: Dict[str, Dict[str, float]] = {}
        for intento, simulacro in attempts:
            code = cls.normalize_area_code(simulacro.area)
            if not code:
                continue
            if code not in area_stats:
                area_stats[code] = {"sum": 0.0, "count": 0}
            area_stats[code]["sum"] += float(intento.puntaje_total or 0.0)
            area_stats[code]["count"] += 1

        nodes: List[CanvasNodeDTO] = []
        for code in sorted(area_stats.keys()):
            count = int(area_stats[code]["count"])
            average = round(area_stats[code]["sum"] / count, 2) if count else 0.0
            nodes.append(
                CanvasNodeDTO(
                    id=f"area-{estudiante_id}-{code}",
                    type="area",
                    label=cls.area_display_name(code),
                    meta={
                        "grupo_id": grupo_id,
                        "estudiante_id": estudiante_id,
                        "area": code,
                        "promedio": average,
                        "intentos": count,
                    },
                )
            )
        return nodes

    @classmethod
    def get_competencia_nodes(
        cls,
        db: Session,
        admin_user: Usuario,
        grupo_id: int,
        estudiante_id: int,
        area_code: str,
    ) -> List[CanvasNodeDTO]:
        cls._validar_scope(db, admin_user, grupo_id, estudiante_id)
        canonical_area = cls.normalize_area_code(area_code)
        if not canonical_area:
            raise HTTPException(status_code=404, detail="Área inválida")

        attempts = cls._query_valid_attempts(db, estudiante_id, canonical_area).all()
        agg: Dict[str, Dict[str, float]] = defaultdict(lambda: {"aciertos": 0.0, "total": 0.0})

        for intento, _ in attempts:
            detailed = intento.respuestas_detalladas or {}
            if not isinstance(detailed, dict):
                continue
            for item in detailed.values():
                if not isinstance(item, dict):
                    continue
                name = str(item.get("competencia") or "Sin Competencia").strip() or "Sin Competencia"
                agg[name]["total"] += 1
                if cls._is_hit(item):
                    agg[name]["aciertos"] += 1

        nodes = []
        for idx, (name, stats) in enumerate(sorted(agg.items(), key=lambda kv: kv[0].lower())):
            total = stats["total"]
            promedio = round((stats["aciertos"] / total) * 100, 2) if total > 0 else 0.0
            nodes.append(
                CanvasNodeDTO(
                    id=f"competencia-{estudiante_id}-{canonical_area}-{idx}",
                    type="competencia",
                    label=name,
                    meta={
                        "grupo_id": grupo_id,
                        "estudiante_id": estudiante_id,
                        "area": canonical_area,
                        "competencia": name,
                        "promedio": promedio,
                    },
                )
            )

        return nodes

    @classmethod
    def get_area_metricas(
        cls,
        db: Session,
        admin_user: Usuario,
        grupo_id: int,
        estudiante_id: int,
        area_code: str,
    ) -> AreaMetricasResponse:
        grupo, estudiante = cls._validar_scope(db, admin_user, grupo_id, estudiante_id)
        canonical_area = cls.normalize_area_code(area_code)
        if not canonical_area:
            raise HTTPException(status_code=404, detail="Área inválida")

        attempts = cls._query_valid_attempts(db, estudiante_id, canonical_area).all()
        if not attempts:
            return AreaMetricasResponse(
                estudiante=EntityRef(id=estudiante.id, nombre=estudiante.nombre),
                grupo=EntityRef(id=grupo.id, nombre=grupo.nombre),
                area=AreaRef(codigo=canonical_area, nombre=cls.area_display_name(canonical_area)),
                tendencia=AreaMetricasTendencia(
                    estado="estable",
                    pendiente=0.0,
                    umbral_estable=1.0,
                    delta_primer_ultimo=0.0,
                    confiabilidad_baja=True,
                ),
                serie_puntaje=[],
                series_competencia=[],
                resumen_competencias=[],
            )

        score_series: List[SeriePuntajeItem] = []
        competition_points: Dict[str, List[SerieCompetenciaPunto]] = defaultdict(list)

        for intento, simulacro in attempts:
            date_ref = intento.fecha_finalizacion or intento.created_at or datetime.utcnow()
            score = cls._safe_float(intento.puntaje_total)
            score_series.append(
                SeriePuntajeItem(
                    respuesta_id=intento.id,
                    fecha=date_ref,
                    puntaje_total=score,
                    simulacro_titulo=simulacro.titulo or f"Simulacro {simulacro.id}",
                )
            )

            detailed = intento.respuestas_detalladas or {}
            if not isinstance(detailed, dict):
                continue

            per_attempt = defaultdict(lambda: {"aciertos": 0.0, "total": 0.0})
            for item in detailed.values():
                if not isinstance(item, dict):
                    continue
                name = str(item.get("competencia") or "Sin Competencia").strip() or "Sin Competencia"
                per_attempt[name]["total"] += 1
                if cls._is_hit(item):
                    per_attempt[name]["aciertos"] += 1

            for name, stats in per_attempt.items():
                total = stats["total"]
                value = round((stats["aciertos"] / total) * 100, 2) if total > 0 else 0.0
                competition_points[name].append(
                    SerieCompetenciaPunto(
                        fecha=date_ref,
                        valor=value,
                        respuesta_id=intento.id,
                    )
                )

        trend = cls._calcular_tendencia(score_series)
        competition_series = [
            SerieCompetenciaItem(competencia=name, puntos=points)
            for name, points in sorted(competition_points.items(), key=lambda kv: kv[0].lower())
        ]

        summary: List[ResumenCompetenciaItem] = []
        for serie in competition_series:
            values = [p.valor for p in serie.puntos]
            if not values:
                continue
            average = round(sum(values) / len(values), 2)
            last = round(values[-1], 2)
            variation = round(last - values[0], 2) if len(values) > 1 else 0.0
            summary.append(
                ResumenCompetenciaItem(
                    competencia=serie.competencia,
                    promedio=average,
                    ultimo=last,
                    variacion=variation,
                )
            )

        return AreaMetricasResponse(
            estudiante=EntityRef(id=estudiante.id, nombre=estudiante.nombre),
            grupo=EntityRef(id=grupo.id, nombre=grupo.nombre),
            area=AreaRef(codigo=canonical_area, nombre=cls.area_display_name(canonical_area)),
            tendencia=trend,
            serie_puntaje=score_series,
            series_competencia=competition_series,
            resumen_competencias=summary,
        )
