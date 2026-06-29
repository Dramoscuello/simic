import pytest

from app.core.security import verify_password
from tests.factories import create_institucion, create_role, create_user
from tests.helpers.auth import auth_headers_for_user, login

pytestmark = [pytest.mark.integration, pytest.mark.critical]


def test_login_exitoso_por_email(client, db_session):
    rol = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=rol, institucion=institucion, password="Pass1234")

    response = login(client, user.email, "Pass1234")

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_exitoso_por_numero_documento(client, db_session):
    rol = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=rol, institucion=institucion, password="Pass1234")

    response = login(client, user.numero_documento, "Pass1234")

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_credenciales_invalidas_retorna_401(client, db_session):
    rol = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    create_user(db_session, rol=rol, institucion=institucion, password="Pass1234")

    response = login(client, "does-not-exist@test.com", "bad-password")

    assert response.status_code == 401


def test_login_usuario_inactivo_retorna_400(client, db_session):
    rol = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(
        db_session,
        rol=rol,
        institucion=institucion,
        password="Pass1234",
        activo=False,
    )

    response = login(client, user.email, "Pass1234")

    assert response.status_code == 400
    assert "inactivo" in response.json()["detail"].lower()


def test_change_password_exitoso(client, db_session):
    rol = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=rol, institucion=institucion, password="Pass1234")
    headers = auth_headers_for_user(user)

    response = client.post(
        "/auth/change-password",
        headers=headers,
        json={"current_password": "Pass1234", "new_password": "Nueva1234"},
    )

    assert response.status_code == 200
    db_session.refresh(user)
    assert verify_password("Nueva1234", user.hashed_password)


def test_change_password_falla_con_actual_incorrecta(client, db_session):
    rol = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=rol, institucion=institucion, password="Pass1234")
    headers = auth_headers_for_user(user)

    response = client.post(
        "/auth/change-password",
        headers=headers,
        json={"current_password": "Mala1234", "new_password": "Nueva1234"},
    )

    assert response.status_code == 400


def test_change_password_falla_si_no_cumple_regla_letra_numero(client, db_session):
    rol = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=rol, institucion=institucion, password="Pass1234")
    headers = auth_headers_for_user(user)

    response = client.post(
        "/auth/change-password",
        headers=headers,
        json={"current_password": "Pass1234", "new_password": "sololetras"},
    )

    assert response.status_code == 400
    assert "letra y un número" in response.json()["detail"]


def test_change_password_falla_si_nueva_igual_a_actual(client, db_session):
    rol = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=rol, institucion=institucion, password="Pass1234")
    headers = auth_headers_for_user(user)

    response = client.post(
        "/auth/change-password",
        headers=headers,
        json={"current_password": "Pass1234", "new_password": "Pass1234"},
    )

    assert response.status_code == 400
