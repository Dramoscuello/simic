from datetime import datetime, timedelta, timezone

import pytest

import app.api.simulacros_attempts as attempts_api
import app.core.redis_config as redis_config
from app.models.respuesta_estudiante import RespuestaEstudiante
from tests.factories import create_intento, create_institucion, create_role, create_simulacro, create_user
from tests.helpers.auth import auth_headers_for_user

pytestmark = [pytest.mark.integration, pytest.mark.critical]


class _FakeRedis:
    def __init__(self, acquire: bool):
        self.acquire = acquire
        self.deleted_keys = []

    def set(self, *args, **kwargs):
        return self.acquire

    def delete(self, key):
        self.deleted_keys.append(key)


def _student_context(db_session, duracion_minutos=60):
    role_student = create_role(db_session, "estudiante")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=role_student, institucion=institucion)
    simulacro = create_simulacro(
        db_session,
        institucion=institucion,
        duracion_minutos=duracion_minutos,
        activo=True,
        estado="activo",
    )
    return user, simulacro, auth_headers_for_user(user)


def test_iniciar_crea_intento_si_no_existe(client, db_session):
    _, simulacro, headers = _student_context(db_session)

    response = client.post(f"/simulacros/{simulacro.id}/iniciar", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["simulacro_id"] == simulacro.id
    assert data["fecha_inicio"] is not None


def test_iniciar_bloquea_reintento_si_ya_finalizo(client, db_session):
    user, simulacro, headers = _student_context(db_session)
    create_intento(
        db_session,
        simulacro=simulacro,
        usuario=user,
        fecha_finalizacion=datetime.now(timezone.utc),
    )

    response = client.post(f"/simulacros/{simulacro.id}/iniciar", headers=headers)

    assert response.status_code == 400
    assert "No se permiten reintentos" in response.json()["detail"]


def test_guardar_combina_respuestas_parciales(client, db_session):
    _, simulacro, headers = _student_context(db_session)
    client.post(f"/simulacros/{simulacro.id}/iniciar", headers=headers)

    r1 = client.patch(
        f"/simulacros/{simulacro.id}/guardar",
        headers=headers,
        json={"respuestas_parciales": {"1": "A"}, "tiempo_empleado": 10},
    )
    r2 = client.patch(
        f"/simulacros/{simulacro.id}/guardar",
        headers=headers,
        json={"respuestas_parciales": {"2": "B"}, "tiempo_empleado": 20},
    )

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json()["respuestas"] == {"1": "A", "2": "B"}


def test_finalizar_calcula_resultados_y_puntaje(client, db_session, monkeypatch):
    monkeypatch.setattr(attempts_api.AnalisisService, "procesar_respuesta", lambda *args, **kwargs: None)
    user, simulacro, headers = _student_context(db_session, duracion_minutos=None)
    client.post(f"/simulacros/{simulacro.id}/iniciar", headers=headers)

    response = client.post(
        f"/simulacros/{simulacro.id}/finalizar",
        headers=headers,
        json={"respuestas": {"1": "A", "2": "X", "3": "C"}, "tiempo_empleado": 50},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_correctas"] == 2
    assert data["total_incorrectas"] == 1
    assert float(data["puntaje_total"]) == pytest.approx(66.6666, rel=1e-2)


def test_finalizar_respeta_minimo_30_por_ciento(client, db_session, monkeypatch):
    monkeypatch.setattr(attempts_api.AnalisisService, "procesar_respuesta", lambda *args, **kwargs: None)
    _, simulacro, headers = _student_context(db_session, duracion_minutos=60)
    client.post(f"/simulacros/{simulacro.id}/iniciar", headers=headers)

    response = client.post(
        f"/simulacros/{simulacro.id}/finalizar",
        headers=headers,
        json={"respuestas": {"1": "A"}, "tiempo_empleado": 10},
    )

    assert response.status_code == 400
    assert "30% del tiempo" in response.json()["detail"]


def test_finalizar_expirado_guarda_parcial_y_retorna_400(client, db_session, monkeypatch):
    monkeypatch.setattr(attempts_api.AnalisisService, "procesar_respuesta", lambda *args, **kwargs: None)
    user, simulacro, headers = _student_context(db_session, duracion_minutos=1)
    intento = create_intento(
        db_session,
        simulacro=simulacro,
        usuario=user,
        respuestas={"1": "A"},
        fecha_inicio=datetime.now(timezone.utc) - timedelta(minutes=10),
    )

    response = client.post(
        f"/simulacros/{simulacro.id}/finalizar",
        headers=headers,
        json={"respuestas": {"2": "B"}, "tiempo_empleado": 100},
    )

    assert response.status_code == 400
    assert "ha expirado" in response.json()["detail"]
    db_session.refresh(intento)
    assert intento.fecha_finalizacion is not None
    assert "1" in (intento.respuestas or {})


def test_finalizar_lock_redis_no_adquirido_retorna_409(client, db_session, monkeypatch):
    user, simulacro, headers = _student_context(db_session, duracion_minutos=None)
    create_intento(db_session, simulacro=simulacro, usuario=user, fecha_inicio=datetime.now(timezone.utc))

    fake_redis = _FakeRedis(acquire=False)
    monkeypatch.setattr(redis_config, "is_redis_available", lambda: True)
    monkeypatch.setattr(redis_config, "get_redis", lambda: fake_redis)
    monkeypatch.setattr(attempts_api, "get_redis", lambda: fake_redis)

    response = client.post(
        f"/simulacros/{simulacro.id}/finalizar",
        headers=headers,
        json={"respuestas": {"1": "A"}, "tiempo_empleado": 30},
    )

    assert response.status_code == 409
    assert "siendo procesada" in response.json()["detail"]


def test_finalizar_lock_redis_adquirido_y_libera_al_final(client, db_session, monkeypatch):
    monkeypatch.setattr(attempts_api.AnalisisService, "procesar_respuesta", lambda *args, **kwargs: None)
    user, simulacro, headers = _student_context(db_session, duracion_minutos=None)
    create_intento(db_session, simulacro=simulacro, usuario=user, fecha_inicio=datetime.now(timezone.utc))

    fake_redis = _FakeRedis(acquire=True)
    monkeypatch.setattr(redis_config, "is_redis_available", lambda: True)
    monkeypatch.setattr(redis_config, "get_redis", lambda: fake_redis)
    monkeypatch.setattr(attempts_api, "get_redis", lambda: fake_redis)

    response = client.post(
        f"/simulacros/{simulacro.id}/finalizar",
        headers=headers,
        json={"respuestas": {"1": "A", "2": "B", "3": "C"}, "tiempo_empleado": 30},
    )

    assert response.status_code == 200
    assert any(str(simulacro.id) in key for key in fake_redis.deleted_keys)
