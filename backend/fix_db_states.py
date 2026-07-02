from sqlalchemy import create_engine, text
from app.core.config import Settings

def fix_states():
    engine = create_engine(Settings.URI)
    with engine.connect() as conn:
        # 1. Convertir 'borrador' -> 'activo' con activo=False
        print("Migrando 'borrador' -> 'activo' (activo=False)...")
        result = conn.execute(text("UPDATE simulacros SET estado = 'activo', activo = false WHERE estado = 'borrador'"))
        print(f"Filas actualizadas: {result.rowcount}")
        
        # 2. Asegurarse que estado sea valido
        print("Verificando consistencia...")
        result = conn.execute(text("SELECT count(*) FROM simulacros WHERE estado NOT IN ('activo', 'finalizado')"))
        count = result.scalar()
        print(f"Simulacros con estado inválido restantes: {count}")
        
        if count > 0:
            # Forzar a activo si queda algo raro
            conn.execute(text("UPDATE simulacros SET estado = 'activo' WHERE estado NOT IN ('activo', 'finalizado')"))
            
        conn.commit()
    print("Corrección completada.")

if __name__ == "__main__":
    fix_states()
