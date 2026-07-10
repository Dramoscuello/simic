from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database.config import get_db
from app.models.sede import Sede
from app.models.usuario import Usuario
from app.schemas.sede import Sede as SedeSchema, SedeCreate, SedeUpdate

router = APIRouter(prefix="/sedes", tags=["sedes"])


def _es_admin(current_user: Usuario):
    return current_user.rol.nombre == "admin"


def _listar_query(db: Session, current_user: Usuario, institucion_id: Optional[int] = None):
    query = db.query(Sede)
    if _es_admin(current_user):
        if institucion_id:
            query = query.filter(Sede.institucion_id == institucion_id)
    else:
        # Admin institución solo ve sedes de su institución
        if current_user.institucion_id:
            query = query.filter(Sede.institucion_id == current_user.institucion_id)
        else:
            query = query.filter(False)
    return query.filter(Sede.activo == True).order_by(Sede.nombre)


@router.get("/", response_model=List[SedeSchema])
def listar_sedes(
    institucion_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    return _listar_query(db, current_user, institucion_id).all()


@router.post("/", response_model=SedeSchema)
def crear_sede(
    payload: SedeCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    if _es_admin(current_user):
        institucion_id = payload.institucion_id or current_user.institucion_id
    else:
        institucion_id = current_user.institucion_id

    if not institucion_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo determinar la institución")

    sede = Sede(
        nombre=payload.nombre,
        direccion=payload.direccion,
        telefono=payload.telefono,
        activo=payload.activo,
        institucion_id=institucion_id,
    )
    db.add(sede)
    db.commit()
    db.refresh(sede)
    return sede


@router.get("/{sede_id}", response_model=SedeSchema)
def obtener_sede(
    sede_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    sede = db.query(Sede).filter(Sede.id == sede_id, Sede.activo == True).first()
    if not sede:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")

    if not _es_admin(current_user) and sede.institucion_id != current_user.institucion_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    return sede


@router.put("/{sede_id}", response_model=SedeSchema)
def actualizar_sede(
    sede_id: int,
    payload: SedeUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    sede = db.query(Sede).filter(Sede.id == sede_id).first()
    if not sede:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")

    if not _es_admin(current_user) and sede.institucion_id != current_user.institucion_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sede, key, value)

    db.commit()
    db.refresh(sede)
    return sede


@router.delete("/{sede_id}")
def eliminar_sede(
    sede_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    sede = db.query(Sede).filter(Sede.id == sede_id).first()
    if not sede:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sede no encontrada")

    if not _es_admin(current_user) and sede.institucion_id != current_user.institucion_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")

    sede.activo = False
    db.commit()
    return {"message": "Sede eliminada"}
