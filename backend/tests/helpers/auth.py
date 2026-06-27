from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models.usuario import Usuario


def login(client: TestClient, username: str, password: str):
    return client.post("/auth/login", data={"username": username, "password": password})


def auth_headers_for_user(user: Usuario) -> dict[str, str]:
    token_payload = {
        "sub": str(user.id),
        "rol": user.rol.nombre if user.rol else None,
        "institucion_id": user.institucion_id,
    }
    token = create_access_token(data=token_payload)
    return {"Authorization": f"Bearer {token}"}
