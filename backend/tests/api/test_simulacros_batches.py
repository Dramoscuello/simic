import pytest
from tests.factories import create_institucion, create_role, create_simulacro, create_user
from tests.helpers.auth import auth_headers_for_user

pytestmark = [pytest.mark.integration]


def test_list_batches_returns_empty_when_no_batches(client, db_session):
    rol_admin = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=rol_admin, institucion=institucion)
    headers = auth_headers_for_user(user)

    response = client.get("/simulacros/batches", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_batches_returns_existing_batches(client, db_session):
    rol_admin = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=rol_admin, institucion=institucion)
    headers = auth_headers_for_user(user)

    # Crear simulacros con el mismo batch_id
    batch_id = "test_batch_2026"
    create_simulacro(db_session, institucion=institucion, batch_id=batch_id, area="MATEMATICAS")
    create_simulacro(db_session, institucion=institucion, batch_id=batch_id, area="LECTURA_CRITICA")

    response = client.get("/simulacros/batches", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["batch_id"] == batch_id
    assert len(data[0]["areas_cubiertas"]) == 2
    assert "MATEMATICAS" in data[0]["areas_cubiertas"]
    assert "LECTURA_CRITICA" in data[0]["areas_cubiertas"]
    assert data[0]["completo"] is False
    assert "sede_ids" in data[0]
    assert "duracion_minutos" in data[0]


def test_get_batch_detail(client, db_session):
    rol_admin = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=rol_admin, institucion=institucion)
    headers = auth_headers_for_user(user)

    batch_id = "detail_batch_123"
    create_simulacro(db_session, institucion=institucion, batch_id=batch_id, area="INGLES")

    response = client.get(f"/simulacros/batches/{batch_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["batch_id"] == batch_id
    assert "INGLES" in data["areas_cubiertas"]
    assert "MATEMATICAS" in data["areas_faltantes"]
    assert "sede_ids" in data
    assert data["duracion_minutos"] == 60


def test_batch_suggestions_only_returns_incomplete_batches(client, db_session):
    rol_admin = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=rol_admin, institucion=institucion)
    headers = auth_headers_for_user(user)

    # Batch completo (5 áreas)
    batch_completo = "completo_batch"
    areas = ["MATEMATICAS", "LECTURA_CRITICA", "CIENCIAS_NATURALES", "SOCIALES_CIUDADANAS", "INGLES"]
    for area in areas:
        create_simulacro(db_session, institucion=institucion, batch_id=batch_completo, area=area, titulo=f"Completo - {area}")

    # Batch incompleto (2 áreas)
    batch_incompleto = "incompleto_batch"
    create_simulacro(db_session, institucion=institucion, batch_id=batch_incompleto, area="MATEMATICAS", titulo="Incompleto - Matemáticas")
    create_simulacro(db_session, institucion=institucion, batch_id=batch_incompleto, area="INGLES", titulo="Incompleto - Inglés")

    # Obtener sugerencias buscando por prefijo o vacío
    response = client.get("/simulacros/batch-suggestions?nombre_base=Incompleto", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Debe retornar el incompleto, no el completo
    assert len(data) >= 1
    batch_ids = [b["batch_id"] for b in data]
    assert batch_incompleto in batch_ids
    assert batch_completo not in batch_ids
    assert "sede_ids" in data[0]
    assert "duracion_minutos" in data[0]


def test_super_admin_batch_endpoints(client, db_session):
    rol_admin = create_role(db_session, "admin")
    # Super Admin has institucion = None
    super_user = create_user(db_session, rol=rol_admin, institucion=None)
    headers = auth_headers_for_user(super_user)

    institucion = create_institucion(db_session)
    batch_id = "super_batch_1"
    create_simulacro(db_session, institucion=institucion, batch_id=batch_id, area="MATEMATICAS")

    # 1. Test listing batches as Super Admin without institucion_id (returns all batches)
    response = client.get("/simulacros/batches", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["batch_id"] == batch_id

    # 2. Test listing batches as Super Admin with specific institucion_id
    response2 = client.get(f"/simulacros/batches?institucion_id={institucion.id}", headers=headers)
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) == 1
    assert data2[0]["batch_id"] == batch_id

    # 3. Test get batch detail as Super Admin (deduces institucion_id automatically)
    response3 = client.get(f"/simulacros/batches/{batch_id}", headers=headers)
    assert response3.status_code == 200
    assert response3.json()["batch_id"] == batch_id

