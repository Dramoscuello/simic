import pytest
from sqlalchemy.orm import Session

from app.models.mensajeria import Conversacion, Mensaje
from tests.factories import create_conversacion, create_institucion, create_role, create_user
from tests.helpers.auth import auth_headers_for_user

pytestmark = [pytest.mark.integration, pytest.mark.critical]


def _admin_ie_headers(db_session: Session):
    role_admin = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=role_admin, institucion=institucion)
    return user, institucion, auth_headers_for_user(user)


def _admin_con_destinatario(db_session: Session):
    user, institucion, headers = _admin_ie_headers(db_session)
    role_docente = create_role(db_session, "docente")
    destinatario = create_user(db_session, rol=role_docente, institucion=institucion)
    return user, institucion, headers, destinatario


def test_enviar_mensaje_texto_con_destinatario(client, db_session, monkeypatch):
    _, _, headers, destinatario = _admin_con_destinatario(db_session)

    payload = {
        "tipo": "texto",
        "contenido": "Hola",
        "destinatario_id": destinatario.id,
    }
    response = client.post("/mensajeria/enviar", json=payload, headers=headers)

    assert response.status_code == 200
    assert response.json()["contenido"] == "Hola"


def test_enviar_mensaje_sin_conversacion_ni_destinatario_retorna_400(client, db_session, monkeypatch):
    _, _, headers = _admin_ie_headers(db_session)

    payload = {"tipo": "texto", "contenido": "sin destino"}
    response = client.post("/mensajeria/enviar", json=payload, headers=headers)

    assert response.status_code == 400
    assert "conversacion_id o destinatario_id" in response.json()["detail"]


def test_enviar_mensaje_con_metadata(client, db_session, monkeypatch):
    _, _, headers, destinatario = _admin_con_destinatario(db_session)

    payload = {
        "tipo": "solicitud_simulacro",
        "contenido": "Solicito simulacro",
        "destinatario_id": destinatario.id,
        "metadata_msg": {"num_preguntas": 20, "areas": ["MATEMATICAS"]},
    }
    response = client.post("/mensajeria/enviar", json=payload, headers=headers)

    assert response.status_code == 200


def test_admin_ie_crea_nueva_conversacion_sin_conversacion_id(client, db_session, monkeypatch):
    _, institucion, headers, destinatario = _admin_con_destinatario(db_session)

    before = db_session.query(Conversacion).filter(Conversacion.institucion_id == institucion.id).count()
    payload = {
        "tipo": "texto",
        "contenido": "Hola, abro un chat nuevo",
        "destinatario_id": destinatario.id,
    }
    response = client.post("/mensajeria/enviar", json=payload, headers=headers)
    after = db_session.query(Conversacion).filter(Conversacion.institucion_id == institucion.id).count()

    assert response.status_code == 200
    assert after == before + 1


def test_enviar_a_conversacion_cerrada_retorna_409(client, db_session, monkeypatch):
    user, institucion, headers = _admin_ie_headers(db_session)
    role_docente = create_role(db_session, "docente")
    otro = create_user(db_session, rol=role_docente, institucion=institucion)
    p1, p2 = sorted([user.id, otro.id])
    conv = create_conversacion(
        db_session,
        institucion=institucion,
        estado="cerrada",
        asunto="Chat cerrado",
        participante_1_id=p1,
        participante_2_id=p2,
    )

    payload = {"conversacion_id": conv.id, "tipo": "texto", "contenido": "mensaje"}
    response = client.post("/mensajeria/enviar", json=payload, headers=headers)

    assert response.status_code == 409


def test_enviar_a_conversacion_de_otra_institucion_retorna_403(client, db_session, monkeypatch):
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
