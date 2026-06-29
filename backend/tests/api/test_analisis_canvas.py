from datetime import datetime, timedelta, timezone

import pytest

from app.models.grupo import Grupo
from tests.factories import create_intento, create_institucion, create_role, create_simulacro, create_user
from tests.helpers.auth import auth_headers_for_user

pytestmark = [pytest.mark.integration, pytest.mark.critical]


def _create_group(db_session, institucion_id: int, nombre: str) -> Grupo:
    group = Grupo(nombre=nombre, institucion_id=institucion_id)
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


def _admin_context(db_session):
    role_admin = create_role(db_session, "admin")
    role_student = create_role(db_session, "estudiante")
    institucion = create_institucion(db_session)

    admin = create_user(db_session, rol=role_admin, institucion=institucion)
    grupo = _create_group(db_session, institucion_id=institucion.id, nombre="11-A")
    estudiante = create_user(db_session, rol=role_student, institucion=institucion, grupo_id=grupo.id)
    return admin, grupo, estudiante


def test_grupos_canvas_scope_admin(client, db_session):
    admin, grupo_own, _ = _admin_context(db_session)
    headers = auth_headers_for_user(admin)

    # Grupo de otra institución no debe aparecer
    other_inst = create_institucion(db_session)
    _create_group(db_session, institucion_id=other_inst.id, nombre="11-Z")

    response = client.get("/analisis/canvas/grupos", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["meta"]["grupo_id"] == grupo_own.id


def test_estudiantes_canvas_grupo_sin_estudiantes(client, db_session):
    admin, grupo, _ = _admin_context(db_session)
    headers = auth_headers_for_user(admin)

    response = client.get(f"/analisis/canvas/grupos/{grupo.id}/estudiantes", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1  # hay estudiante inicialmente

    # Crear grupo vacío real para validar estado vacío
    grupo_vacio = _create_group(db_session, institucion_id=admin.institucion_id, nombre="11-B")
    response_empty = client.get(f"/analisis/canvas/grupos/{grupo_vacio.id}/estudiantes", headers=headers)
    assert response_empty.status_code == 200
    assert response_empty.json() == []


def test_areas_canvas_sin_intentos_validos(client, db_session):
    admin, grupo, estudiante = _admin_context(db_session)
    headers = auth_headers_for_user(admin)

    response = client.get(
        f"/analisis/canvas/grupos/{grupo.id}/estudiantes/{estudiante.id}/areas",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json() == []


def test_metricas_area_tendencia_estable_con_un_intento(client, db_session):
    admin, grupo, estudiante = _admin_context(db_session)
    headers = auth_headers_for_user(admin)

    simulacro = create_simulacro(db_session, institucion=estudiante.institucion, area="MATEMATICAS")
    create_intento(
        db_session,
        simulacro=simulacro,
        usuario=estudiante,
        puntaje_total=55,
        fecha_inicio=datetime.now(timezone.utc) - timedelta(hours=1),
        fecha_finalizacion=datetime.now(timezone.utc),
        respuestas_detalladas={
            "1": {"competencia": "Interpretación y representación", "es_correcta": True},
            "2": {"competencia": "Formulación y ejecución", "es_correcta": False},
        },
    )

    response = client.get(
        f"/analisis/canvas/grupos/{grupo.id}/estudiantes/{estudiante.id}/areas/MATEMATICAS/metricas",
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tendencia"]["estado"] == "estable"
    assert payload["tendencia"]["pendiente"] == 0
    assert payload["tendencia"]["confiabilidad_baja"] is True
    assert len(payload["serie_puntaje"]) == 1


def test_metricas_excluye_fraude_y_anulado_y_detecta_tendencia(client, db_session):
    admin, grupo, estudiante = _admin_context(db_session)
    headers = auth_headers_for_user(admin)

    s1 = create_simulacro(db_session, institucion=estudiante.institucion, area="MATEMATICAS")
    s2 = create_simulacro(db_session, institucion=estudiante.institucion, area="MATEMATICAS")
    s3 = create_simulacro(db_session, institucion=estudiante.institucion, area="MATEMATICAS")
    s4 = create_simulacro(db_session, institucion=estudiante.institucion, area="MATEMATICAS")
    s5 = create_simulacro(db_session, institucion=estudiante.institucion, area="MATEMATICAS")

    base = datetime.now(timezone.utc) - timedelta(days=4)
    create_intento(
        db_session,
        simulacro=s1,
        usuario=estudiante,
        puntaje_total=40,
        fecha_inicio=base,
        fecha_finalizacion=base + timedelta(minutes=30),
        respuestas_detalladas={"1": {"competencia": "C1", "es_correcta": True}},
    )
    create_intento(
        db_session,
        simulacro=s2,
        usuario=estudiante,
        puntaje_total=55,
        fecha_inicio=base + timedelta(days=1),
        fecha_finalizacion=base + timedelta(days=1, minutes=30),
        respuestas_detalladas={"1": {"competencia": "C1", "acierto": True}},
    )
    create_intento(
        db_session,
        simulacro=s3,
        usuario=estudiante,
        puntaje_total=70,
        fecha_inicio=base + timedelta(days=2),
        fecha_finalizacion=base + timedelta(days=2, minutes=30),
        respuestas_detalladas={"1": {"competencia": "C1", "es_correcta": True}},
    )

    # Excluidos
    create_intento(
        db_session,
        simulacro=s4,
        usuario=estudiante,
        puntaje_total=100,
        fraude=True,
        fecha_inicio=base + timedelta(days=3),
        fecha_finalizacion=base + timedelta(days=3, minutes=30),
        respuestas_detalladas={"1": {"competencia": "C1", "es_correcta": True}},
    )
    create_intento(
        db_session,
        simulacro=s5,
        usuario=estudiante,
        puntaje_total=0,
        anulado=True,
        fecha_inicio=base + timedelta(days=4),
        fecha_finalizacion=base + timedelta(days=4, minutes=30),
        respuestas_detalladas={"1": {"competencia": "C1", "es_correcta": False}},
    )

    response = client.get(
        f"/analisis/canvas/grupos/{grupo.id}/estudiantes/{estudiante.id}/areas/MATEMATICAS/metricas",
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tendencia"]["estado"] == "subiendo"
    assert len(payload["serie_puntaje"]) == 3


def test_scope_cross_institucion_retorna_403(client, db_session):
    admin, _, _ = _admin_context(db_session)
    headers = auth_headers_for_user(admin)

    other_admin, other_group, _ = _admin_context(db_session)
    assert other_admin.institucion_id != admin.institucion_id

    response = client.get(f"/analisis/canvas/grupos/{other_group.id}/estudiantes", headers=headers)
    assert response.status_code == 403
