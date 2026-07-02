from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.config import get_db
from app.models.rol import Rol
from app.schemas.rol import Rol as RolSchema, RolCreate, RolUpdate
from app.api.deps import get_current_active_user
from app.models.usuario import Usuario

router = APIRouter(
    prefix="/roles",
    tags=["roles"]
)

@router.get("/", response_model=List[RolSchema])
def read_roles(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    roles = db.query(Rol).offset(skip).limit(limit).all()
    return roles

@router.post("/", response_model=RolSchema)
def create_rol(
    rol: RolCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_rol = Rol(**rol.model_dump())
    db.add(db_rol)
    db.commit()
    db.refresh(db_rol)
    return db_rol

@router.get("/{rol_id}", response_model=RolSchema)
def read_rol(
    rol_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if db_rol is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return db_rol

@router.put("/{rol_id}", response_model=RolSchema)
def update_rol(
    rol_id: int, 
    rol: RolUpdate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if db_rol is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    
    update_data = rol.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rol, key, value)
    
    db.add(db_rol)
    db.commit()
    db.refresh(db_rol)
    return db_rol
