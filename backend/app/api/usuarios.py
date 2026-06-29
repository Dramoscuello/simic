from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.config import get_db
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.sede import Sede
from app.models.respuesta_estudiante import RespuestaEstudiante
from app.schemas.usuario import Usuario as UsuarioSchema, UsuarioCreate, UsuarioUpdate
from app.schemas.respuesta_estudiante import RespuestaEstudianteResponse
from app.core.security import get_password_hash
from app.api.deps import get_current_active_user

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"]
)

def _is_super_admin(user: Usuario) -> bool:
    return user.rol.nombre == 'admin' and user.institucion_id is None

def _is_institucion_admin(user: Usuario) -> bool:
    return user.rol.nombre == 'admin' and user.institucion_id is not None

def _is_docente(user: Usuario) -> bool:
    return user.rol.nombre == 'docente'

@router.get("/", response_model=List[UsuarioSchema])
def read_usuarios(
    skip: int = 0, 
    limit: int = 100, 
    rol: str = None,
    grupo_id: Optional[int] = None,
    sede_id: Optional[int] = None,
    institucion_id: Optional[int] = None,
    sin_grupo: bool = False,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    query = db.query(Usuario)
    
    if _is_institucion_admin(current_user):
        query = query.filter(Usuario.institucion_id == current_user.institucion_id)
    elif _is_docente(current_user):
        query = query.filter(Usuario.institucion_id == current_user.institucion_id)
    elif _is_super_admin(current_user):
        if institucion_id:
            query = query.filter(Usuario.institucion_id == institucion_id)
    elif institucion_id:
        query = query.filter(Usuario.institucion_id == institucion_id)
            
    if rol:
        query = query.join(Rol).filter(Rol.nombre == rol)
        
    if grupo_id is not None:
        query = query.filter(Usuario.grupo_id == grupo_id)

    if sede_id is not None:
        query = query.filter(Usuario.sede_id == sede_id)

    if sin_grupo:
        query = query.filter(Usuario.grupo_id == None)
        
    usuarios = query.offset(skip).limit(limit).all()
    return usuarios

@router.post("/", response_model=UsuarioSchema)
def create_usuario(
    usuario: UsuarioCreate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    if _is_docente(current_user):
        raise HTTPException(status_code=403, detail="No tiene permisos para crear usuarios")

    db_user_doc = db.query(Usuario).filter(Usuario.numero_documento == usuario.numero_documento).first()
    if db_user_doc:
        raise HTTPException(status_code=400, detail="El número de documento ya está registrado")
    
    if usuario.email:
        db_user_email = db.query(Usuario).filter(Usuario.email == usuario.email).first()
        if db_user_email:
            raise HTTPException(status_code=400, detail="El email ya está registrado")

    institucion_id = usuario.institucion_id
    sede_id = usuario.sede_id

    if _is_institucion_admin(current_user):
        institucion_id = current_user.institucion_id
        if sede_id:
            sede = db.query(Sede).filter(
                Sede.id == sede_id,
                Sede.institucion_id == institucion_id,
                Sede.activo == True
            ).first()
            if not sede:
                raise HTTPException(status_code=400, detail="La sede no pertenece a la institución o no existe")

    hashed_pwd = get_password_hash(usuario.password)
    user_data = usuario.model_dump(exclude={'password'})
    user_data['institucion_id'] = institucion_id
    db_usuario = Usuario(**user_data, hashed_password=hashed_pwd)
    
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@router.get("/me", response_model=UsuarioSchema)
def read_user_me(current_user: Usuario = Depends(get_current_active_user)):
    return current_user

@router.get("/{usuario_id}", response_model=UsuarioSchema)
def read_usuario(
    usuario_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_usuario

@router.put("/{usuario_id}", response_model=UsuarioSchema)
def update_usuario(
    usuario_id: int, 
    usuario: UsuarioUpdate, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    rol_nombre = current_user.rol.nombre if current_user.rol else None

    if rol_nombre == 'estudiante':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Los estudiantes no pueden editar datos personales. Use /auth/change-password para actualizar su contraseña."
        )

    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if _is_institucion_admin(current_user) or _is_docente(current_user):
        if db_usuario.institucion_id != current_user.institucion_id:
            raise HTTPException(status_code=403, detail="No tiene permisos para editar usuarios de otra institución")
    elif not _is_super_admin(current_user):
        if current_user.id != usuario_id:
            raise HTTPException(status_code=403, detail="No tiene permisos para editar este usuario")
    
    update_data = usuario.model_dump(exclude_unset=True)
    
    if 'password' in update_data:
        update_data['hashed_password'] = get_password_hash(update_data.pop('password'))

    if 'sede_id' in update_data and update_data['sede_id'] is not None:
        sede = db.query(Sede).filter(
            Sede.id == update_data['sede_id'],
            Sede.institucion_id == db_usuario.institucion_id,
            Sede.activo == True
        ).first()
        if not sede:
            raise HTTPException(status_code=400, detail="La sede no pertenece a la institución o no existe")
        
    for key, value in update_data.items():
        setattr(db_usuario, key, value)
    
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_usuario(
    usuario_id: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if db_usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db.delete(db_usuario)
    db.commit()
    return None

@router.get("/{usuario_id}/intentos", response_model=List[RespuestaEstudianteResponse])
def read_usuario_intentos(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    target_user = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if _is_institucion_admin(current_user) or _is_docente(current_user):
        if target_user.institucion_id != current_user.institucion_id:
             raise HTTPException(status_code=403, detail="No tiene permisos para ver este usuario")
              
    intentos = db.query(RespuestaEstudiante).filter(
        RespuestaEstudiante.usuario_id == usuario_id,
        RespuestaEstudiante.anulado.is_(False)
    ).all()
    return intentos
