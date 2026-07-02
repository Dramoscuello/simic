import os
from pathlib import Path
from dotenv import load_dotenv

# Robust .env loading
# Intenta buscar .env en la raíz del backend o en la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent # backend/
ROOT_DIR = BASE_DIR.parent # icfes_project/

env_path = BASE_DIR / '.env'
if not env_path.exists():
    # Check in app dir (backend/app/.env)
    env_path = BASE_DIR / 'app' / '.env'

if not env_path.exists():
    env_path = ROOT_DIR / '.env'

load_dotenv(dotenv_path=env_path)


class Settings:
    POSTGRES_USER: str = os.getenv("USER_POSTGRES", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("PASS_POSTGRES", "postgres")
    POSTGRES_DB: str = os.getenv("DB_POSTGRES", "icfes_db")
    POSTGRES_HOST: str = os.getenv("HOST_POSTGRES", "localhost")
    POSTGRES_PORT: str = os.getenv("PORT_POSTGRES", '5432')

    # Priority to DATABASE_URL for Railway/Heroku
    URI: str = os.getenv("DATABASE_URL")
    # Fix for SQLAlchemy (Postgres dialect name)
    if URI and URI.startswith("postgres://"):
        URI = URI.replace("postgres://", "postgresql://", 1)
    
    # Construir URI si no existe
    if not URI:
        if POSTGRES_HOST:
             URI = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
        else:
             # Fallback final si nada está configurado (evita el None error, aunque fallará al conectar si no existe DB)
             URI = "sqlite:///./test.db" 

    # JWT Config
    SECRET_KEY: str = os.getenv("SECRET_KEY", "insecure_default_secret_key_change_me")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

Settings = Settings()