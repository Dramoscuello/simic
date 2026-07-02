import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.pregunta_usada import PreguntaUsada
from app.services.embedding_service import EmbeddingService, EmbeddingServiceError


logger = logging.getLogger(__name__)


def _stringify_contexto(contexto) -> str:
    if contexto is None:
        return ""
    if isinstance(contexto, str):
        return contexto
    if isinstance(contexto, (dict, list)):
        return json.dumps(contexto, ensure_ascii=False, sort_keys=True)
    return str(contexto)


def _build_texto_completo(pregunta: Dict) -> tuple[str, str, str]:
    texto_pregunta = pregunta.get("pregunta") or pregunta.get("enunciado") or ""
    contexto = _stringify_contexto(pregunta.get("contexto", ""))

    if not isinstance(texto_pregunta, str):
        texto_pregunta = str(texto_pregunta or "")

    if contexto and texto_pregunta:
        texto_completo = f"{contexto}\n{texto_pregunta}"
    else:
        texto_completo = texto_pregunta or contexto

    return texto_completo, contexto, texto_pregunta


def _calcular_hash(contexto: str, enunciado: str) -> str:
    texto = f"{contexto.strip().lower()} {enunciado.strip().lower()}"
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def registrar_preguntas_usadas(
    *,
    db: Session,
    preguntas: List[Dict],
    institucion_id: int,
    area: str,
    version_simulacro: Optional[str],
    simulacro_id: int,
    embedding_model: str = EmbeddingService.DEFAULT_MODEL,
    commit: bool = True,
) -> int:
    if not preguntas or not institucion_id or not area:
        return 0

    prepared_rows: List[dict] = []
    embedding_inputs: List[str] = []

    for preg in preguntas:
        texto_completo, contexto, texto_pregunta = _build_texto_completo(preg)
        if not texto_completo:
            continue

        prepared_rows.append(
            {
                "pregunta": preg,
                "texto_completo": texto_completo,
                "hash_contenido": _calcular_hash(contexto, texto_pregunta),
            }
        )
        embedding_inputs.append(f"{contexto}\n{texto_pregunta}".strip())

    if not prepared_rows:
        return 0

    embeddings: Optional[List[List[float]]] = None
    try:
        embeddings = EmbeddingService.embed_texts(embedding_inputs, model=embedding_model)
    except EmbeddingServiceError as e:
        logger.warning("Embeddings no disponibles para preguntas_usadas (fail-open): %s", e)

    now_utc = datetime.now(timezone.utc)

    for i, row in enumerate(prepared_rows):
        embedding_vector = embeddings[i] if embeddings else None
        p = row["pregunta"]
        db.add(
            PreguntaUsada(
                institucion_id=institucion_id,
                area=area,
                pregunta=row["texto_completo"],
                tema=p.get("tema"),
                componente=p.get("componente"),
                competencia=p.get("competencia"),
                version_simulacro=version_simulacro,
                simulacro_id=simulacro_id,
                hash_contenido=row["hash_contenido"],
                embedding=embedding_vector,
                embedding_model=embedding_model if embedding_vector is not None else None,
                embedding_updated_at=now_utc if embedding_vector is not None else None,
            )
        )

    if commit:
        db.commit()

    return len(prepared_rows)
