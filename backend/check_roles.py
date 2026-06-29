from sqlalchemy import text
from app.database.config import session_Local

def list_roles():
    db = session_Local()
    try:
        print("Consultando roles en la BD...")
        result = db.execute(text("SELECT id, nombre FROM roles"))
        for row in result:
            print(f"ID: {row[0]}, Nombre: '{row[1]}'")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    list_roles()
