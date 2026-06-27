from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.config import get_db
from app.models.grupo import Grupo
from app.models.sede import Sede
from app.models.usuario import Usuario
from app.schemas.grupo import GrupoCreate, GrupoUpdate, Grupo as GrupoSchema
from app.api.deps import get_current_active_user

router = APIRouter()

def _is_super_admin(user: Usuario) -> bool:
    return user.rol.nombre == 'admin' and user.institucion_id is None

def _is_institucion_admin(user: Usuario) -> bool:
    return user.rol.nombre == 'admin' and user.institucion_id is not None

@router.get("/", response_model=List[GrupoSchema])
def read_grupos(
    institucion_id: Optional[int] = None,
    sede_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    query = db.query(Grupo)
    
    if _is_institucion_admin(current_user):
        query = query.filter(Grupo.institucion_id == current_user.institucion_id)
    elif _is_super_admin(current_user):
        if institucion_id:
            query = query.filter(Grupo.institucion_id == institucion_id)

    if sede_id is not None:
        query = query.filter(Grupo.sede_id == sede_id)
    
    grupos = query.offset(skip).limit(limit).all()
    
    result = []
    for grupo in grupos:
        grupo_dict = {
            "id": grupo.id,
            "nombre": grupo.nombre,
            "institucion_id": grupo.institucion_id,
            "sede_id": grupo.sede_id,
            "sede": grupo.sede,
            "created_at": grupo.created_at,
            "updated_at": grupo.updated_at,
            "estudiantes_count": len(grupo.estudiantes) if grupo.estudiantes else 0
        }
        result.append(grupo_dict)
    
    return result

@router.post("/", response_model=GrupoSchema)
def create_grupo(
    grupo: GrupoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    if current_user.rol.nombre not in ['admin']:
        raise HTTPException(status_code=403, detail="No tiene permisos")
    
    institucion_id = grupo.institucion_id
    
    if _is_institucion_admin(current_user):
        institucion_id = current_user.institucion_id
    elif _is_super_admin(current_user):
        if not institucion_id:
            raise HTTPException(status_code=400, detail="Super Admin debe especificar el ID de la institución")
    
    sede_id = grupo.sede_id
    
    if sede_id:
        sede = db.query(Sede).filter(Sede.id == sede_id, Sede.institucion_id == institucion_id, Sede.activo == True).first()
        if not sede:
            raise HTTPException(status_code=400, detail="La sede no pertenece a la institución o no existe")
    else:
        sedes_count = db.query(Sede).filter(Sede.institucion_id == institucion_id, Sede.activo == True).count()
        if sedes_count == 1:
            sede = db.query(Sede).filter(Sede.institucion_id == institucion_id, Sede.activo == True).first()
            sede_id = sede.id

    db_grupo = Grupo(
        nombre=grupo.nombre,
        institucion_id=institucion_id,
        sede_id=sede_id
    )
    db.add(db_grupo)
    db.commit()
    db.refresh(db_grupo)
    return db_grupo

@router.put("/{grupo_id}", response_model=GrupoSchema)
def update_grupo(
    grupo_id: int,
    grupo_update: GrupoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_grupo = db.query(Grupo).filter(Grupo.id == grupo_id).first()
    if not db_grupo:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")
        
    if _is_institucion_admin(current_user):
        if db_grupo.institucion_id != current_user.institucion_id:
            raise HTTPException(status_code=403, detail="No tiene permisos sobre este grupo")
    elif not _is_super_admin(current_user):
        raise HTTPException(status_code=403, detail="No tiene permisos")

    if grupo_update.nombre is not None:
        db_grupo.nombre = grupo_update.nombre

    if grupo_update.sede_id is not None:
        sede = db.query(Sede).filter(
            Sede.id == grupo_update.sede_id,
            Sede.institucion_id == db_grupo.institucion_id,
            Sede.activo == True
        ).first()
        if not sede:
            raise HTTPException(status_code=400, detail="La sede no pertenece a la institución o no existe")
        db_grupo.sede_id = grupo_update.sede_id
    
    db.commit()
    db.refresh(db_grupo)
    return db_grupo

@router.delete("/{grupo_id}")
def delete_grupo(
    grupo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_grupo = db.query(Grupo).filter(Grupo.id == grupo_id).first()
    if not db_grupo:
        raise HTTPException(status_code=404, detail="Grupo no encontrado")

    if _is_institucion_admin(current_user):
        if db_grupo.institucion_id != current_user.institucion_id:
            raise HTTPException(status_code=403, detail="No tiene permisos sobre este grupo")
    elif not _is_super_admin(current_user):
        raise HTTPException(status_code=403, detail="No tiene permisos")

    db.delete(db_grupo)
    db.commit()
    return {"message": "Grupo eliminado"}
