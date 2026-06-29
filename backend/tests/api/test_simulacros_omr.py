import pytest

from app.models.respuesta_estudiante import RespuestaEstudiante
from tests.factories import create_intento, create_institucion, create_role, create_simulacro, create_user
from tests.helpers.auth import auth_headers_for_user

pytestmark = [pytest.mark.integration, pytest.mark.critical]


def _admin_context(db_session):
    role_admin = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    admin = create_user(db_session, rol=role_admin, institucion=institucion)
    return admin, institucion, auth_headers_for_user(admin)


def test_procesar_omr_rechaza_rol_no_autorizado(client, db_session):
    role_super = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    super_user = create_user(db_session, rol=role_super, institucion=institucion)
    headers = auth_headers_for_user(super_user)
    simulacro = create_simulacro(db_session, institucion=institucion)

    response = client.post(
        f"/simulacros/{simulacro.id}/procesar-omr",
        headers=headers,
        files=[("files", ("sheet.png", b"fake-image", "image/png"))],
    )

    assert response.status_code == 403


def test_procesar_omr_rechaza_archivos_no_imagen(client, db_session):
    _, institucion, headers = _admin_context(db_session)
    simulacro = create_simulacro(db_session, institucion=institucion)

    response = client.post(
        f"/simulacros/{simulacro.id}/procesar-omr",
        headers=headers,
        files=[("files", ("sheet.txt", b"text-file", "text/plain"))],
    )

    assert response.status_code == 400
    assert "imágenes válidas" in response.json()["detail"]


def test_procesar_omr_con_mock_exitoso_retorna_resumen_correcto(client, db_session, monkeypatch):
    _, institucion, headers = _admin_context(db_session)
    student_role = create_role(db_session, "estudiante")
    student = create_user(db_session, rol=student_role, institucion=institucion)
    simulacro = create_simulacro(db_session, institucion=institucion)

    class FakeOMRProcessingService:
        def process_batch(self, images_data, num_preguntas):
            return [
                {
                    "success": True,
                    "filename": "sheet.png",
                    "data": {
                        "qr_detectado": True,
                        "qr_datos": {
                            "estudiante_id": student.id,
                            "estudiante_nombre": student.nombre,
                        },
                        "respuestas": {"1": "A"},
                        "confianza_general": 0.93,
                        "observaciones": "ok",
                    },
                }
            ]

    monkeypatch.setattr(
        "app.services.omr_processing_service.OMRProcessingService",
        FakeOMRProcessingService,
    )

    response = client.post(
        f"/simulacros/{simulacro.id}/procesar-omr",
        headers=headers,
        files=[("files", ("sheet.png", b"fake-image", "image/png"))],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == {"total": 1, "success": 1, "warnings": 0, "errors": 0}


def test_guardar_omr_persiste_y_mapea_por_indice_visual(client, db_session, monkeypatch):
    analysis_calls = []
    monkeypatch.setattr(
        "app.api.simulacros_omr.AnalisisService.procesar_respuesta",
        lambda respuesta_id: analysis_calls.append(respuesta_id),
    )

    _, institucion, headers = _admin_context(db_session)
    role_student = create_role(db_session, "estudiante")
    student = create_user(db_session, rol=role_student, institucion=institucion)
    preguntas = [
        {"id": 10, "respuesta_correcta": "A", "competencia": "c1", "componente": "x1", "tema": "t1"},
        {"id": 30, "respuesta_correcta": "C", "competencia": "c2", "componente": "x2", "tema": "t2"},
        {"id": 99, "respuesta_correcta": "B", "competencia": "c3", "componente": "x3", "tema": "t3"},
    ]
    simulacro = create_simulacro(db_session, institucion=institucion, preguntas=preguntas, total_preguntas=3)

    payload = {
        "results": [
            {
                "status": "success",
                "filename": "sheet.png",
                "data": {
                    "qr_datos": {"estudiante_id": student.id, "estudiante_nombre": student.nombre},
                    "respuestas": {"1": "A", "2": "C", "3": "D"},
                },
            }
        ]
    }

    response = client.post(f"/simulacros/{simulacro.id}/guardar-omr", headers=headers, json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["guardados"] == 1

    saved = (
        db_session.query(RespuestaEstudiante)
        .filter(RespuestaEstudiante.simulacro_id == simulacro.id, RespuestaEstudiante.usuario_id == student.id)
        .first()
    )
    assert saved is not None
    assert saved.respuestas_detalladas["1"]["pregunta_id"] == 10
    assert saved.respuestas_detalladas["2"]["pregunta_id"] == 30
    assert saved.respuestas_detalladas["3"]["pregunta_id"] == 99
    assert saved.respuestas_detalladas["2"]["es_correcta"] is True
    assert len(analysis_calls) == 1


def test_guardar_omr_omite_duplicado_si_ya_presento(client, db_session):
    _, institucion, headers = _admin_context(db_session)
    role_student = create_role(db_session, "estudiante")
    student = create_user(db_session, rol=role_student, institucion=institucion)
    simulacro = create_simulacro(db_session, institucion=institucion)
    create_intento(db_session, simulacro=simulacro, usuario=student, fecha_finalizacion=None)

    payload = {
        "results": [
            {
                "status": "success",
                "filename": "sheet.png",
                "data": {
                    "qr_datos": {"estudiante_id": student.id},
                    "respuestas": {"1": "A"},
                },
            }
        ]
    }

    response = client.post(f"/simulacros/{simulacro.id}/guardar-omr", headers=headers, json=payload)

    assert response.status_code == 200
    assert response.json()["summary"]["omitidos"] == 1
    assert response.json()["summary"]["guardados"] == 0


def test_guardar_omr_maneja_estudiante_no_encontrado(client, db_session):
    _, institucion, headers = _admin_context(db_session)
    simulacro = create_simulacro(db_session, institucion=institucion)

    payload = {
        "results": [
            {
                "status": "success",
                "filename": "sheet.png",
                "data": {
                    "qr_datos": {"estudiante_id": 999999},
                    "respuestas": {"1": "A"},
                },
            }
        ]
    }

    response = client.post(f"/simulacros/{simulacro.id}/guardar-omr", headers=headers, json=payload)

    assert response.status_code == 200
    assert response.json()["summary"]["errores"] == 1
