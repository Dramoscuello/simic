import pytest
from tests.factories import (
    create_institucion,
    create_role,
    create_simulacro,
    create_user,
    create_reporte_grupal,
)
from tests.helpers.auth import auth_headers_for_user

pytestmark = [pytest.mark.integration]


def test_dashboard_groups_reportes_grupales_by_batch(client, db_session):
    rol_admin = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=rol_admin, institucion=institucion)
    headers = auth_headers_for_user(user)

    # Crear batch común
    batch_id = "group_batch_test"
    sim_mat = create_simulacro(db_session, institucion=institucion, batch_id=batch_id, area="MATEMATICAS", titulo="Sim - Matemáticas")
    sim_lec = create_simulacro(db_session, institucion=institucion, batch_id=batch_id, area="LECTURA_CRITICA", titulo="Sim - Lectura Crítica")

    # Crear reportes grupales
    create_reporte_grupal(db_session, simulacro=sim_mat, institucion=institucion)
    create_reporte_grupal(db_session, simulacro=sim_lec, institucion=institucion)

    response = client.get("/reportes/dashboard", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    grupales = data["grupales"]
    # Debería haber una agrupación grupal_batch
    assert len(grupales) >= 1
    batch_item = next((g for g in grupales if g["tipo_reporte"] == "grupal_batch"), None)
    assert batch_item is not None
    assert batch_item["metadata"]["batch_id"] == batch_id
    assert len(batch_item["areas"]) == 2


def test_detalle_grupal_batch(client, db_session):
    rol_admin = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=rol_admin, institucion=institucion)
    headers = auth_headers_for_user(user)

    batch_id = "detailed_group_batch"
    sim_mat = create_simulacro(db_session, institucion=institucion, batch_id=batch_id, area="MATEMATICAS", titulo="Sim - Matemáticas")
    create_reporte_grupal(db_session, simulacro=sim_mat, institucion=institucion)

    # Buscar detalle
    response = client.get(f"/reportes/detalle/grupal-batch?batch_id={batch_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["subtitulo"] == "Sim"
    assert len(data["areas"]) == 1
    assert data["areas"][0]["area"] == "MATEMATICAS"


def test_lista_reportes_grupales_with_batch(client, db_session):
    rol_admin = create_role(db_session, "admin")
    institucion = create_institucion(db_session)
    user = create_user(db_session, rol=rol_admin, institucion=institucion)
    headers = auth_headers_for_user(user)

    batch_id = "list_group_batch"
    sim_mat = create_simulacro(db_session, institucion=institucion, batch_id=batch_id, area="MATEMATICAS", titulo="Sim - Matemáticas")
    sim_lec = create_simulacro(db_session, institucion=institucion, batch_id=batch_id, area="LECTURA_CRITICA", titulo="Sim - Lectura Crítica")
    create_reporte_grupal(db_session, simulacro=sim_mat, institucion=institucion)
    create_reporte_grupal(db_session, simulacro=sim_lec, institucion=institucion)

    response = client.get("/reportes/lista/grupal", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 1
    batch_item = next((g for g in data if g["tipo_reporte"] == "grupal_batch"), None)
    assert batch_item is not None
    assert batch_item["metadata"]["batch_id"] == batch_id
