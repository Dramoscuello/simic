from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.config import get_db
from app.models import ReviewPregunta, Simulacro, Usuario
from app.models.institucion import Institucion
from app.schemas.review_pregunta import (
    ReviewPreguntaCreate, 
    ReviewPreguntaUpdate, 
    ReviewPreguntaResponse,
    ReviewPreguntaListResponse
)
from app.api.deps import get_current_active_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"]
)


class ReviewFullResponse(BaseModel):
    """Response con datos completos para la vista de gestión"""
    id: int
    simulacro_id: int
    simulacro_titulo: str
    pregunta_numero: int
    pregunta_enunciado: Optional[str] = None
    usuario_id: Optional[int] = None
    usuario_nombre: Optional[str] = None
    revision: str
    resuelto: bool
    created_at: datetime
    updated_at: datetime
    # Datos relacionados
    institucion_id: Optional[int] = None
    institucion_nombre: Optional[str] = None
    sede_id: Optional[int] = None
    sede_nombre: Optional[str] = None
    area: Optional[str] = None
    
    class Config:
        from_attributes = True


class ReviewsAllResponse(BaseModel):
    """Response para listar todas las reviews"""
    total: int
    pendientes: int
    resueltas: int
    reviews: List[ReviewFullResponse]


@router.get("/all", response_model=ReviewsAllResponse)
def get_all_reviews(
    resuelto: Optional[bool] = None,
    institucion_id: Optional[int] = None,
    sede_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener todas las revisiones con información completa.
    Solo admin o docente puede acceder a este endpoint.
    """
    rol_nombre = current_user.rol.nombre if current_user.rol else ""
    if rol_nombre not in ["admin", "docente"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo admin o docente puede ver las revisiones"
        )
    
    # Query base con joins
    query = db.query(ReviewPregunta).join(
        Simulacro, ReviewPregunta.simulacro_id == Simulacro.id
    )
    
    # Filtros
    if resuelto is not None:
        query = query.filter(ReviewPregunta.resuelto == resuelto)
    
    if sede_id:
        query = query.filter(Simulacro.sede_id == sede_id)
    elif institucion_id:
        query = query.filter(Simulacro.institucion_id == institucion_id)
    
    if rol_nombre == 'docente' and current_user.institucion_id:
        query = query.filter(Simulacro.institucion_id == current_user.institucion_id)
        if current_user.sede_id:
            query = query.filter(Simulacro.sede_id == current_user.sede_id)
    
    reviews = query.order_by(ReviewPregunta.created_at.desc()).all()
    
    # Obtener datos relacionados
    simulacro_ids = list(set([r.simulacro_id for r in reviews]))
    simulacros = {s.id: s for s in db.query(Simulacro).filter(Simulacro.id.in_(simulacro_ids)).all()}
    
    user_ids = [r.usuario_id for r in reviews if r.usuario_id]
    users = {u.id: u.nombre for u in db.query(Usuario).filter(Usuario.id.in_(user_ids)).all()}
    
    institucion_ids = list(set([s.institucion_id for s in simulacros.values() if s.institucion_id]))
    instituciones = {i.id: i.nombre for i in db.query(Institucion).filter(Institucion.id.in_(institucion_ids)).all()}

    from app.models.sede import Sede
    sede_ids = list(set([s.sede_id for s in simulacros.values() if s.sede_id]))
    sedes_map = {s.id: s.nombre for s in db.query(Sede).filter(Sede.id.in_(sede_ids)).all()}
    
    # Construir respuesta
    result = []
    for r in reviews:
        sim = simulacros.get(r.simulacro_id)
        if not sim:
            continue
        
        # Obtener enunciado de la pregunta del contenido JSONB
        pregunta_enunciado = None
        if sim.contenido:
            contenido = sim.contenido
            if isinstance(contenido, str):
                import json
                contenido = json.loads(contenido)
            preguntas = contenido.get("preguntas", [])
            for p in preguntas:
                if p.get("id") == r.pregunta_numero or p.get("numero") == r.pregunta_numero:
                    pregunta_enunciado = p.get("enunciado", p.get("pregunta", ""))[:200]
                    break
        
        result.append(ReviewFullResponse(
            id=r.id,
            simulacro_id=r.simulacro_id,
            simulacro_titulo=sim.titulo,
            pregunta_numero=r.pregunta_numero,
            pregunta_enunciado=pregunta_enunciado,
            usuario_id=r.usuario_id,
            usuario_nombre=users.get(r.usuario_id) if r.usuario_id else None,
            revision=r.revision,
            resuelto=r.resuelto,
            created_at=r.created_at,
            updated_at=r.updated_at,
            institucion_id=sim.institucion_id,
            institucion_nombre=instituciones.get(sim.institucion_id) if sim.institucion_id else None,
            sede_id=sim.sede_id,
            sede_nombre=sedes_map.get(sim.sede_id) if sim.sede_id else None,
            area=sim.area
        ))
    
    # Estadísticas
    all_reviews = db.query(ReviewPregunta).all()
    total = len(all_reviews)
    pendientes = sum(1 for r in all_reviews if not r.resuelto)
    resueltas_count = sum(1 for r in all_reviews if r.resuelto)
    
    return ReviewsAllResponse(
        total=total,
        pendientes=pendientes,
        resueltas=resueltas_count,
        reviews=result
    )


def check_permission(current_user: Usuario):
    """Verifica que el usuario sea admin"""
    rol_nombre = current_user.rol.nombre if current_user.rol else ""
    allowed_roles = ["admin"]
    if rol_nombre not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo SuperAdmin y Administradores Institucionales pueden gestionar revisiones"
        )
    return rol_nombre


@router.post("/", response_model=ReviewPreguntaResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    review: ReviewPreguntaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Crear una nueva revisión para una pregunta.
    Solo admin, rector y coordinador pueden crear revisiones.
    """
    check_permission(current_user)
    
    # Verificar que el simulacro existe
    simulacro = db.query(Simulacro).filter(Simulacro.id == review.simulacro_id).first()
    if not simulacro:
        raise HTTPException(status_code=404, detail="Simulacro no encontrado")
    
    # Verificar que la pregunta existe en el simulacro
    contenido = simulacro.contenido
    if isinstance(contenido, str):
        import json
        contenido = json.loads(contenido)
    
    preguntas = contenido.get("preguntas", [])
    pregunta_existe = any(p.get("id") == review.pregunta_numero or p.get("numero") == review.pregunta_numero for p in preguntas)
    
    if not pregunta_existe:
        raise HTTPException(status_code=404, detail=f"Pregunta {review.pregunta_numero} no encontrada en el simulacro")
    
    # Crear la revisión
    db_review = ReviewPregunta(
        simulacro_id=review.simulacro_id,
        pregunta_numero=review.pregunta_numero,
        usuario_id=current_user.id,
        revision=review.revision,
        resuelto=False
    )
    
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    return ReviewPreguntaResponse(
        id=db_review.id,
        simulacro_id=db_review.simulacro_id,
        pregunta_numero=db_review.pregunta_numero,
        usuario_id=db_review.usuario_id,
        revision=db_review.revision,
        resuelto=db_review.resuelto,
        created_at=db_review.created_at,
        updated_at=db_review.updated_at,
        usuario_nombre=current_user.nombre
    )


@router.get("/simulacro/{simulacro_id}", response_model=ReviewPreguntaListResponse)
def get_reviews_by_simulacro(
    simulacro_id: int,
    resuelto: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener todas las revisiones de un simulacro.
    Opcionalmente filtrar por estado (resuelto/pendiente).
    """
    check_permission(current_user)
    
    # Verificar que el simulacro existe
    simulacro = db.query(Simulacro).filter(Simulacro.id == simulacro_id).first()
    if not simulacro:
        raise HTTPException(status_code=404, detail="Simulacro no encontrado")
    
    # Construir query
    query = db.query(ReviewPregunta).filter(ReviewPregunta.simulacro_id == simulacro_id)
    
    if resuelto is not None:
        query = query.filter(ReviewPregunta.resuelto == resuelto)
    
    reviews = query.order_by(ReviewPregunta.pregunta_numero).all()
    
    # Obtener nombres de usuarios
    user_ids = [r.usuario_id for r in reviews if r.usuario_id]
    users = {u.id: u.nombre for u in db.query(Usuario).filter(Usuario.id.in_(user_ids)).all()}
    
    # Contar estadísticas
    all_reviews = db.query(ReviewPregunta).filter(ReviewPregunta.simulacro_id == simulacro_id).all()
    total = len(all_reviews)
    pendientes = sum(1 for r in all_reviews if not r.resuelto)
    resueltas = sum(1 for r in all_reviews if r.resuelto)
    
    return ReviewPreguntaListResponse(
        total=total,
        pendientes=pendientes,
        resueltas=resueltas,
        reviews=[
            ReviewPreguntaResponse(
                id=r.id,
                simulacro_id=r.simulacro_id,
                pregunta_numero=r.pregunta_numero,
                usuario_id=r.usuario_id,
                revision=r.revision,
                resuelto=r.resuelto,
                created_at=r.created_at,
                updated_at=r.updated_at,
                usuario_nombre=users.get(r.usuario_id) if r.usuario_id else None
            )
            for r in reviews
        ]
    )


@router.get("/pregunta/{simulacro_id}/{pregunta_numero}", response_model=List[ReviewPreguntaResponse])
def get_reviews_by_pregunta(
    simulacro_id: int,
    pregunta_numero: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtener todas las revisiones de una pregunta específica.
    """
    check_permission(current_user)
    
    reviews = db.query(ReviewPregunta).filter(
        ReviewPregunta.simulacro_id == simulacro_id,
        ReviewPregunta.pregunta_numero == pregunta_numero
    ).order_by(ReviewPregunta.created_at.desc()).all()
    
    # Obtener nombres de usuarios
    user_ids = [r.usuario_id for r in reviews if r.usuario_id]
    users = {u.id: u.nombre for u in db.query(Usuario).filter(Usuario.id.in_(user_ids)).all()}
    
    return [
        ReviewPreguntaResponse(
            id=r.id,
            simulacro_id=r.simulacro_id,
            pregunta_numero=r.pregunta_numero,
            usuario_id=r.usuario_id,
            revision=r.revision,
            resuelto=r.resuelto,
            created_at=r.created_at,
            updated_at=r.updated_at,
            usuario_nombre=users.get(r.usuario_id) if r.usuario_id else None
        )
        for r in reviews
    ]


@router.patch("/{review_id}", response_model=ReviewPreguntaResponse)
def update_review(
    review_id: int,
    review_update: ReviewPreguntaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Actualizar una revisión (editar nota o marcar como resuelta).
    """
    check_permission(current_user)
    
    db_review = db.query(ReviewPregunta).filter(ReviewPregunta.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Revisión no encontrada")
    
    # Actualizar campos
    update_data = review_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_review, key, value)
    
    db.commit()
    db.refresh(db_review)
    
    # Obtener nombre del usuario
    usuario_nombre = None
    if db_review.usuario_id:
        user = db.query(Usuario).filter(Usuario.id == db_review.usuario_id).first()
        usuario_nombre = user.nombre if user else None
    
    return ReviewPreguntaResponse(
        id=db_review.id,
        simulacro_id=db_review.simulacro_id,
        pregunta_numero=db_review.pregunta_numero,
        usuario_id=db_review.usuario_id,
        revision=db_review.revision,
        resuelto=db_review.resuelto,
        created_at=db_review.created_at,
        updated_at=db_review.updated_at,
        usuario_nombre=usuario_nombre
    )


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Eliminar una revisión.
    Solo admin puede eliminar revisiones.
    """
    rol_nombre = current_user.rol.nombre if current_user.rol else ""
    if rol_nombre != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo SuperAdmin puede eliminar revisiones"
        )
    
    db_review = db.query(ReviewPregunta).filter(ReviewPregunta.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Revisión no encontrada")
    
    db.delete(db_review)
    db.commit()
    
    return None
