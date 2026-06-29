import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    analisis,
    auth,
    dashboard,
    estudiantes,
    grupos,
    instituciones,
    mensajeria,
    notificaciones,
    reportes,
    reviews,
    roles,
    sedes,
    setup,
    simulacros,
    usuarios,
)
from app.api.endpoints import monitoreo
from app.database.config import Base, engine, session_Local
from app.models.institucion import Institucion
from app.models.rol import Rol
from app.models.simulacro import Simulacro
from app.models.usuario import Usuario


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


def create_initial_data() -> None:
    db = session_Local()
    try:
        roles = ["admin", "estudiante", "docente"]
        for role_name in roles:
            role = db.query(Rol).filter(Rol.nombre == role_name).first()
            if not role:
                role = Rol(nombre=role_name, descripcion=f"Rol de {role_name}")
                db.add(role)
                db.commit()
                db.refresh(role)
    except Exception as e:
        print(f"Error inicializando roles: {e}")
    finally:
        db.close()


def bootstrap_data() -> None:
    create_tables()
    create_initial_data()


def _bootstrap_enabled() -> bool:
    value = os.getenv("APP_BOOTSTRAP_ON_STARTUP", "true").strip().lower()
    return value in {"1", "true", "yes", "on"}


def create_app() -> FastAPI:
    app = FastAPI(title="ICFES Simulation API", version="1.0.0")

    origins = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "https://SIMIC.vercel.app",
    ]

    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        origins.append(frontend_url)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup_bootstrap() -> None:
        if _bootstrap_enabled():
            bootstrap_data()

    app.include_router(auth.router)
    app.include_router(setup.router)
    app.include_router(instituciones.router)
    app.include_router(roles.router)
    app.include_router(usuarios.router)
    app.include_router(simulacros.router)
    app.include_router(grupos.router, prefix="/grupos", tags=["grupos"])
    app.include_router(estudiantes.router)
    app.include_router(mensajeria.router)
    app.include_router(sedes.router)
    app.include_router(reviews.router)
    app.include_router(reportes.router)
    app.include_router(dashboard.router)
    app.include_router(analisis.router)
    app.include_router(notificaciones.router)
    app.include_router(monitoreo.router)

    @app.get("/")
    def read_root():
        return {"message": "Welcome to ICFES Simulation API"}

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
