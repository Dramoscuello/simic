"""
Script para ELIMINAR TODOS los simulacros y datos relacionados.
Uso: python3 backend/nuke_simulacros.py
"""
import sys
import os

# Agregar directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import session_Local, engine
from app.models.simulacro import Simulacro
from app.models.pregunta_usada import PreguntaUsada
from app.models.respuesta_estudiante import RespuestaEstudiante
from sqlalchemy import text

def nuke_data():
    db = session_Local()
    try:
        print("☢️  INICIANDO ELIMINACIÓN DE DATOS DE SIMULACROS...")
        
        # 1. Eliminar Respuestas de Estudiantes (dependen de Simulacros)
        deleted_resp = db.query(RespuestaEstudiante).delete()
        print(f"   🗑️  Eliminadas {deleted_resp} respuestas de estudiantes.")
        
        # 2. Eliminar Preguntas Usadas (dependen de Simulacros)
        deleted_preg = db.query(PreguntaUsada).delete()
        print(f"   🗑️  Eliminadas {deleted_preg} preguntas usadas.")
        
        # 3. Eliminar Simulacros
        deleted_sim = db.query(Simulacro).delete()
        print(f"   🗑️  Eliminados {deleted_sim} simulacros.")
        
        db.commit()
        print("\n✨ ¡Limpieza completada con éxito! Tablas vacías.")
        
    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    confirm = input("⚠️  ¿Estás SEGURO de borrar todos los simulacros? (y/n): ")
    if confirm.lower() == 'y':
        nuke_data()
    else:
        print("Operación cancelada.")
