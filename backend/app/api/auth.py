from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from sqlalchemy import or_

from app.database.config import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_refresh_token
from app.core.config import Settings
from app.models.usuario import Usuario
from app.schemas.token import Token, RefreshTokenRequest

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Buscar usuario por email O numero_documento
    user = db.query(Usuario).filter(
        or_(
            Usuario.email == form_data.username,
            Usuario.numero_documento == form_data.username
        )
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
        
    access_token_expires = timedelta(minutes=Settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # En el token guardamos info útil
    token_payload = {
        "sub": str(user.id),
        "rol": user.rol.nombre if user.rol else None,
        "institucion_id": user.institucion_id
    }
    
    access_token = create_access_token(
        data=token_payload,
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(data=token_payload)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh")
def refresh_access_token(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Renueva el access_token usando un refresh_token válido."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_refresh_token(body.refresh_token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    # Verificar que el usuario sigue existiendo y activo
    user = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if not user or not user.activo:
        raise credentials_exception
    
    # Generar nuevo access_token
    token_payload = {
        "sub": str(user.id),
        "rol": user.rol.nombre if user.rol else None,
        "institucion_id": user.institucion_id
    }
    
    access_token_expires = timedelta(minutes=Settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data=token_payload,
        expires_delta=access_token_expires
    )
    
    return {"access_token": new_access_token, "token_type": "bearer"}


from app.schemas.password import PasswordChange
from app.api.deps import get_current_active_user
from app.core.security import get_password_hash

@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    # 1. Verificar contraseña actual
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="La contraseña actual es incorrecta"
        )
            
    # 2. Validar reglas de complejidad adicionales si se desea (aunque Pydantic ya valida longitud)
    # Por ejemplo, exigir números y letras (backend enforcement)
    import re
    if not re.search(r"[A-Za-z]", password_data.new_password) or not re.search(r"\d", password_data.new_password):
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe contener al menos una letra y un número"
         )

    if password_data.current_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe ser diferente a la contraseña actual"
        )

    # 3. Guardar nueva contraseña hasheada
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.add(current_user)
    db.commit()
    
    return {"message": "Contraseña actualizada correctamente"}
