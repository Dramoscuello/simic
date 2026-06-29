from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.institucion import Institucion
from app.models.mensajeria import Conversacion, Mensaje
from app.models.respuesta_estudiante import RespuestaEstudiante
from app.models.rol import Rol
from app.models.sede import Sede
from app.models.simulacro import Simulacro
from app.models.usuario import Usuario


def _suffix() -> str:
    return uuid4().hex[:8]


def create_role(db: Session, nombre: str, descripcion: str | None = None) -> Rol:
    role = db.query(Rol).filter(Rol.nombre == nombre).first()
    if role:
        return role
    role = Rol(nombre=nombre, descripcion=descripcion or f"Rol de {nombre}")
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def create_institucion(db: Session, **kwargs) -> Institucion:
    token = _suffix()
    data = {
        "nombre": f"Institucion {token}",
        "codigo_dane": token[:12],
        "nit": f"900{token}",
        "email_contacto": f"admin-{token}@test.com",
        "direccion": "Calle Test",
        "ciudad": "Bogota",
        "departamento": "Cundinamarca",
        "activo": True,
        "nombre_rector": f"Rector {token}",
        "email_rector": f"rector-{token}@test.com",
    }
    data.update(kwargs)
    inst = Institucion(**data)
    db.add(inst)
    db.commit()
    db.refresh(inst)

    # Crear sede principal por defecto para la institución
    sede_principal = Sede(
        nombre="Sede Principal",
        direccion=inst.direccion,
        telefono=inst.telefono,
        activo=True,
        institucion_id=inst.id,
    )
    db.add(sede_principal)
    db.commit()

    return inst


def create_user(
    db: Session,
    rol: Rol,
    institucion: Institucion,
    password: str = "Pass1234",
    activo: bool = True,
    **kwargs,
) -> Usuario:
    token = _suffix()
    data = {
        "nombre": f"Usuario {token}",
        "email": f"user-{token}@test.com",
        "hashed_password": get_password_hash(password),
        "tipo_documento": "CC",
        "numero_documento": f"1{token[:7]}",
        "institucion_id": institucion.id,
        "rol_id": rol.id,
        "activo": activo,
    }
    data.update(kwargs)
    user = Usuario(**data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_simulacro(
    db: Session,
    institucion: Institucion,
    area: str = "MATEMATICAS",
    preguntas: list[dict] | None = None,
    **kwargs,
) -> Simulacro:
    if preguntas is None:
        preguntas = [
            {"id": 1, "respuesta_correcta": "A", "competencia": "Comp 1", "componente": "Comp A", "tema": "Tema 1"},
            {"id": 2, "respuesta_correcta": "B", "competencia": "Comp 2", "componente": "Comp B", "tema": "Tema 2"},
            {"id": 3, "respuesta_correcta": "C", "competencia": "Comp 3", "componente": "Comp C", "tema": "Tema 3"},
        ]
    token = _suffix()
    data = {
        "titulo": f"Simulacro {token}",
        "descripcion": "Simulacro de prueba",
        "area": area,
        "contenido": {"preguntas": preguntas, "meta": {"total_preguntas": len(preguntas)}},
        "total_preguntas": len(preguntas),
        "duracion_minutos": 60,
        "institucion_id": institucion.id,
        "estado": "activo",
        "activo": True,
    }
    data.update(kwargs)
    simulacro = Simulacro(**data)
    db.add(simulacro)
    db.commit()
    db.refresh(simulacro)
    return simulacro


def create_conversacion(
    db: Session,
    institucion: Institucion,
    estado: str = "abierta",
    asunto: str = "Chat test",
    **kwargs,
) -> Conversacion:
    conv = Conversacion(institucion_id=institucion.id, asunto=asunto, estado=estado, **kwargs)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def create_mensaje(
    db: Session,
    conversacion: Conversacion,
    remitente: Usuario,
    **kwargs,
) -> Mensaje:
    data = {
        "conversacion_id": conversacion.id,
        "remitente_id": remitente.id,
        "tipo": "texto",
        "contenido": "hola",
    }
    data.update(kwargs)
    msg = Mensaje(**data)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def create_intento(
    db: Session,
    simulacro: Simulacro,
    usuario: Usuario,
    respuestas: dict | None = None,
    respuestas_detalladas: dict | None = None,
    fecha_inicio: datetime | None = None,
    fecha_finalizacion: datetime | None = None,
    **kwargs,
) -> RespuestaEstudiante:
    intento = RespuestaEstudiante(
        simulacro_id=simulacro.id,
        usuario_id=usuario.id,
        institucion_id=usuario.institucion_id,
        respuestas=respuestas or {},
        respuestas_detalladas=respuestas_detalladas or {},
        total_correctas=kwargs.pop("total_correctas", 0),
        total_incorrectas=kwargs.pop("total_incorrectas", 0),
        puntaje_total=kwargs.pop("puntaje_total", None),
        tiempo_empleado=kwargs.pop("tiempo_empleado", 0),
        fecha_inicio=fecha_inicio or datetime.now(timezone.utc),
        fecha_finalizacion=fecha_finalizacion,
        fraude=kwargs.pop("fraude", False),
        anulado=kwargs.pop("anulado", False),
        **kwargs,
    )
    db.add(intento)
    db.commit()
    db.refresh(intento)
    return intento
