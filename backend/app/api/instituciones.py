from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.config import get_db
from app.models.institucion import Institucion
from app.schemas.institucion import Institucion as InstitucionSchema, InstitucionCreate, InstitucionUpdate
from app.api.deps import get_current_active_user
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.schemas.usuario import Usuario as UsuarioSchema
from app.core.security import get_password_hash
from io import BytesIO
import pandas as pd
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix="/instituciones",
    tags=["instituciones"]
)


@router.get("/", response_model=List[InstitucionSchema])
def read_instituciones(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    # Single-institution mode: retorna solo la institución del usuario
    if current_user.institucion_id:
        institucion = db.query(Institucion).filter(Institucion.id == current_user.institucion_id).first()
        return [institucion] if institucion else []
    return []


@router.post("/", response_model=InstitucionSchema)
def create_institucion(
    institucion: InstitucionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    raise HTTPException(status_code=403, detail="Las instituciones se crean únicamente durante la configuración inicial")


@router.get("/{institucion_id}", response_model=InstitucionSchema)
def read_institucion(
    institucion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    if current_user.rol.nombre != "admin" or current_user.institucion_id != institucion_id:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver esta institución")

    db_institucion = db.query(Institucion).filter(Institucion.id == institucion_id).first()
    if db_institucion is None:
        raise HTTPException(status_code=404, detail="Institución no encontrada")
    return db_institucion


@router.put("/{institucion_id}", response_model=InstitucionSchema)
def update_institucion(
    institucion_id: int,
    institucion: InstitucionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    if current_user.rol.nombre != "admin" or current_user.institucion_id != institucion_id:
        raise HTTPException(status_code=403, detail="No tiene permisos para editar esta institución")

    db_institucion = db.query(Institucion).filter(Institucion.id == institucion_id).first()
    if db_institucion is None:
        raise HTTPException(status_code=404, detail="Institución no encontrada")

    update_data = institucion.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_institucion, key, value)

    db.add(db_institucion)
    db.commit()
    db.refresh(db_institucion)
    return db_institucion


@router.get("/{institucion_id}/usuarios", response_model=List[UsuarioSchema])
def read_institucion_usuarios(
    institucion_id: int,
    rol: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    if current_user.rol.nombre != "admin" or current_user.institucion_id != institucion_id:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver usuarios de esta institución")

    query = db.query(Usuario).filter(Usuario.institucion_id == institucion_id)

    if rol:
        query = query.join(Rol).filter(Rol.nombre == rol)

    usuarios = query.offset(skip).limit(limit).all()
    return usuarios


@router.post("/{institucion_id}/usuarios/import")
async def import_usuarios(
    institucion_id: int,
    file: UploadFile = File(...),
    rol_nombre: str = Form(...),
    grupo_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    if current_user.rol.nombre != "admin" or current_user.institucion_id != institucion_id:
        raise HTTPException(status_code=403, detail="No tiene permisos para importar usuarios en esta institución")

    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un Excel (.xlsx)")

    rol_obj = db.query(Rol).filter(Rol.nombre == rol_nombre).first()
    if not rol_obj:
        raise HTTPException(status_code=400, detail=f"Rol '{rol_nombre}' no válido")

    try:
        content = await file.read()
        df = pd.read_excel(BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el archivo Excel: {str(e)}")

    required_cols = ['nombre', 'tipo_documento', 'numero_documento', 'email', 'password']
    df.columns = [c.lower().strip() for c in df.columns]

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Faltan columnas requeridas: {', '.join(missing)}")

    creados = 0
    errores = []
    df = df.where(pd.notnull(df), None)

    for index, row in df.iterrows():
        try:
            if not row['numero_documento'] or pd.isna(row['numero_documento']):
               errores.append(f"Fila {index+2}: Falta numero_documento")
               continue

            doc = str(row['numero_documento']).split('.')[0].strip()

            tipo_doc = str(row['tipo_documento']).strip() if pd.notna(row['tipo_documento']) else 'TI'
            nombre = str(row['nombre']).strip() if pd.notna(row['nombre']) else 'Sin Nombre'

            if db.query(Usuario).filter(Usuario.numero_documento == doc).first():
                errores.append(f"Fila {index+2}: Documento {doc} ya existe")
                continue

            email = row['email']
            if pd.isna(email) or not str(email).strip():
                email = None
            else:
                email = str(email).strip()
                if db.query(Usuario).filter(Usuario.email == email).first():
                    errores.append(f"Fila {index+2}: Email {email} ya existe")
                    continue

            pwd_raw = str(row['password']).strip() if pd.notna(row['password']) else doc
            hashed_pwd = get_password_hash(pwd_raw)

            new_user = Usuario(
                nombre=nombre,
                tipo_documento=tipo_doc,
                numero_documento=doc,
                email=email,
                hashed_password=hashed_pwd,
                institucion_id=institucion_id,
                rol_id=rol_obj.id,
                grupo_id=grupo_id,
                activo=True
            )

            try:
                db.add(new_user)
                db.commit()
                creados += 1
            except IntegrityError:
                db.rollback()
                errores.append(f"Fila {index+2}: Usuario ya existe en base de datos (Duplicado)")
            except Exception as e:
                db.rollback()
                errores.append(f"Fila {index+2}: Error al guardar: {str(e)}")

        except Exception as e:
            errores.append(f"Fila {index+2}: Error de proceso: {str(e)}")

    return {
        "status": "success",
        "total_procesados": len(df),
        "creados": creados,
        "errores": errores
    }
