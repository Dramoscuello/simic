import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from typing import List, Optional


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.config import session_Local
from app.models.pregunta_usada import PreguntaUsada
from app.services.embedding_service import EmbeddingService, EmbeddingServiceError


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("backfill_preguntas_usadas_embeddings")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Backfill embeddings en preguntas_usadas (idempotente: solo embedding IS NULL)."
    )
    parser.add_argument("--institucion-id", type=int, default=None)
    parser.add_argument("--area", type=str, default=None)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--embed-batch-size", type=int, default=64)
    parser.add_argument("--limit", type=int, default=None, help="Máximo total de filas a procesar.")
    parser.add_argument(
        "--start-id",
        type=int,
        default=0,
        help="Cursor inicial (procesa ids > start-id).",
    )
    parser.add_argument("--model", type=str, default=EmbeddingService.DEFAULT_MODEL)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _build_query(db, args, last_id: int, remaining: Optional[int]):
    query = (
        db.query(PreguntaUsada)
        .filter(PreguntaUsada.embedding.is_(None), PreguntaUsada.id > last_id)
        .order_by(PreguntaUsada.id.asc())
    )
    if args.institucion_id:
        query = query.filter(PreguntaUsada.institucion_id == args.institucion_id)
    if args.area:
        query = query.filter(PreguntaUsada.area == args.area)

    batch_size = args.batch_size
    if remaining is not None:
        batch_size = min(batch_size, remaining)

    return query.limit(batch_size).all()


def run_backfill(args) -> int:
    db = session_Local()
    last_id = args.start_id
    processed = 0
    updated = 0
    failed = 0
    started_at = datetime.now(timezone.utc)

    try:
        while True:
            remaining = None
            if args.limit is not None:
                remaining = args.limit - processed
                if remaining <= 0:
                    break

            rows: List[PreguntaUsada] = _build_query(db, args, last_id, remaining)
            if not rows:
                break

            last_id = rows[-1].id
            processed += len(rows)

            texts = [(row.pregunta or "").strip() for row in rows]
            non_empty = sum(1 for text in texts if text)
            logger.info(
                "Batch ids=[%s..%s] size=%s non_empty=%s",
                rows[0].id,
                rows[-1].id,
                len(rows),
                non_empty,
            )

            if args.dry_run:
                continue

            try:
                embeddings = EmbeddingService.embed_texts(
                    texts,
                    model=args.model,
                    batch_size=args.embed_batch_size,
                )
            except EmbeddingServiceError as exc:
                logger.error("Error embedding batch ids=[%s..%s]: %s", rows[0].id, rows[-1].id, exc)
                db.rollback()
                failed += len(rows)
                continue

            now_utc = datetime.now(timezone.utc)
            for row, vector in zip(rows, embeddings):
                if not vector:
                    failed += 1
                    continue
                row.embedding = vector
                row.embedding_model = args.model
                row.embedding_updated_at = now_utc
                updated += 1

            db.commit()
            logger.info(
                "Batch commit ok: updated=%s processed=%s failed=%s",
                updated,
                processed,
                failed,
            )

    except KeyboardInterrupt:
        logger.warning("Backfill interrumpido por usuario.")
    finally:
        db.close()

    ended_at = datetime.now(timezone.utc)
    elapsed = (ended_at - started_at).total_seconds()
    logger.info(
        "Resumen backfill: processed=%s updated=%s failed=%s start_id=%s elapsed=%.1fs",
        processed,
        updated,
        failed,
        args.start_id,
        elapsed,
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    arguments = parse_args()
    raise SystemExit(run_backfill(arguments))
