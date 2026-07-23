from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database.config import get_db
from app.models.usuario import Usuario
from app.schemas.analisis import AreaMetricasResponse, CanvasNodeDTO
from app.services.analisis_canvas_service import AnalisisCanvasService

router = APIRouter(prefix="/analisis/canvas", tags=["analisis-canvas"])


@router.get("/grupos", response_model=list[CanvasNodeDTO])
def get_grupos_canvas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    return AnalisisCanvasService.get_group_nodes(db=db, admin_user=current_user)


@router.get("/grupos/{grupo_id}/estudiantes", response_model=list[CanvasNodeDTO])
def get_estudiantes_canvas(
    grupo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    return AnalisisCanvasService.get_student_nodes(db=db, admin_user=current_user, grupo_id=grupo_id)


@router.get("/grupos/{grupo_id}/estudiantes/{estudiante_id}/areas", response_model=list[CanvasNodeDTO])
def get_areas_canvas(
    grupo_id: int,
    estudiante_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    return AnalisisCanvasService.get_area_nodes(
        db=db,
        admin_user=current_user,
        grupo_id=grupo_id,
        estudiante_id=estudiante_id,
    )


@router.get(
    "/grupos/{grupo_id}/estudiantes/{estudiante_id}/areas/{area}/competencias",
    response_model=list[CanvasNodeDTO],
)
def get_competencias_canvas(
    grupo_id: int,
    estudiante_id: int,
    area: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    return AnalisisCanvasService.get_competencia_nodes(
        db=db,
        admin_user=current_user,
        grupo_id=grupo_id,
        estudiante_id=estudiante_id,
        area_code=area,
    )


@router.get(
    "/grupos/{grupo_id}/estudiantes/{estudiante_id}/areas/{area}/metricas",
    response_model=AreaMetricasResponse,
)
def get_metricas_area_canvas(
    grupo_id: int,
    estudiante_id: int,
    area: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    return AnalisisCanvasService.get_area_metricas(
        db=db,
        admin_user=current_user,
        grupo_id=grupo_id,
        estudiante_id=estudiante_id,
        area_code=area,
    )
