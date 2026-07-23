import os
os.environ["DATABASE_URL"] = "postgresql://dramoscuello@localhost:5432/icfes_test"
os.environ["APP_BOOTSTRAP_ON_STARTUP"] = "false"

from fastapi.testclient import TestClient
from app.main import create_app
from app.database.config import get_db
from tests.factories import create_role, create_institucion, create_user
from tests.helpers.auth import auth_headers_for_user
from sqlalchemy.orm import Session

app = create_app()
client = TestClient(app)

db = next(get_db())
rol_admin = create_role(db, "admin")
institucion = create_institucion(db)
user = create_user(db, rol=rol_admin, institucion=institucion)
headers = auth_headers_for_user(user)

response = client.get("/simulacros/batches", headers=headers)
print("STATUS:", response.status_code)
print("JSON:", response.json())
