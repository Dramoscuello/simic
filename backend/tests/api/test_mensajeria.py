import pytest
from sqlalchemy.orm import Session

from app.models.mensajeria import Conversacion, Mensaje
from tests.factories import create_conversacion, create_institucion, create_role, create_user
from tests.helpers.auth import auth_headers_for_user

pytestmark = [pytest.mark.integration, pytest.mark.critical]


def _patch_notification_side_effects(monkeypatch):
    pass


def _admin_ie_headers(db_session: Session):
    role_admin = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=role_admin, institucion=institucion)
    return user, institucion, auth_headers_for_user(user)


def test_enviar_solicitud_simulacro_num_preguntas_valido(client, db_session, monkeypatch):
    _patch_notification_side_effects(monkeypatch)
    _, _, headers = _admin_ie_headers(db_session)

    payload = {
        "tipo": "solicitud_simulacro",
        "contenido": "Solicito simulacro",
        "metadata_msg": {"num_preguntas": 20, "areas": ["MATEMATICAS"]},
    }
    response = client.post("/mensajeria/enviar", json=payload, headers=headers)

    assert response.status_code == 200
    assert response.json()["metadata_msg"]["num_preguntas"] == 20


def test_enviar_solicitud_simulacro_num_preguntas_invalido_retorna_400(client, db_session, monkeypatch):
    _patch_notification_side_effects(monkeypatch)
    _, _, headers = _admin_ie_headers(db_session)

    payload = {
        "tipo": "solicitud_simulacro",
        "contenido": "Solicito simulacro",
        "metadata_msg": {"num_preguntas": 15},
    }
    response = client.post("/mensajeria/enviar", json=payload, headers=headers)

    assert response.status_code == 400
    assert "10, 20 o 30" in response.json()["detail"]


def test_enviar_solicitud_simulacro_sin_metadata_asigna_default_30(client, db_session, monkeypatch):
    _patch_notification_side_effects(monkeypatch)
    _, _, headers = _admin_ie_headers(db_session)

    payload = {
        "tipo": "solicitud_simulacro",
        "contenido": "Solicito simulacro sin metadata",
    }
    response = client.post("/mensajeria/enviar", json=payload, headers=headers)

    assert response.status_code == 200
    assert response.json()["metadata_msg"]["num_preguntas"] == 30


def test_admin_ie_crea_nueva_conversacion_sin_conversacion_id(client, db_session, monkeypatch):
    _patch_notification_side_effects(monkeypatch)
    _, institucion, headers = _admin_ie_headers(db_session)

    before = db_session.query(Conversacion).filter(Conversacion.institucion_id == institucion.id).count()
    payload = {"tipo": "texto", "contenido": "Hola, abro un chat nuevo"}
    response = client.post("/mensajeria/enviar", json=payload, headers=headers)
    after = db_session.query(Conversacion).filter(Conversacion.institucion_id == institucion.id).count()

    assert response.status_code == 200
    assert after == before + 1


def test_enviar_a_conversacion_cerrada_retorna_409(client, db_session, monkeypatch):
    _patch_notification_side_effects(monkeypatch)
    user, institucion, headers = _admin_ie_headers(db_session)
    conv = create_conversacion(db_session, institucion=institucion, estado="cerrada")

    payload = {"conversacion_id": conv.id, "tipo": "texto", "contenido": "mensaje"}
    response = client.post("/mensajeria/enviar", json=payload, headers=headers)

    assert response.status_code == 409


def test_enviar_a_conversacion_de_otra_institucion_retorna_403(client, db_session, monkeypatch):
    _patch_notification_side_effects(monkeypatch)
    _, _, headers = _admin_ie_headers(db_session)
    other_inst = create_institucion(db_session)
    other_user_role = create_role(db_session, "docente")
    other_user = create_user(db_session, rol=other_user_role, institucion=other_inst)
    conv = create_conversacion(db_session, institucion=other_inst, estado="abierta")
    create_msg = Mensaje(conversacion_id=conv.id, remitente_id=other_user.id, tipo="texto", contenido="x")
    db_session.add(create_msg)
    db_session.commit()

    payload = {"conversacion_id": conv.id, "tipo": "texto", "contenido": "No autorizado"}
    response = client.post("/mensajeria/enviar", json=payload, headers=headers)

    assert response.status_code == 403
