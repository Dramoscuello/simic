"""
Configuración de Redis para Job Locking y Caché
"""
import os
import redis
from typing import Optional
import threading
import uuid
import logging


logger = logging.getLogger(__name__)

# URL de conexión a Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Cliente Redis singleton
_redis_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    """Obtiene el cliente Redis (singleton)"""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,  # Retorna strings en vez de bytes
            socket_timeout=5,
            socket_connect_timeout=5
        )
    
    return _redis_client


def is_redis_available() -> bool:
    """Verifica si Redis está disponible"""
    try:
        client = get_redis()
        client.ping()
        return True
    except (redis.ConnectionError, redis.TimeoutError):
        return False


# ==========================================
# JOB LOCKING
# ==========================================

class JobLock:
    """
    Gestor de locks para evitar doble generación.
    
    Uso:
        lock = JobLock(institucion_id=5, area="MATEMATICAS")
        
        if not lock.acquire():
            raise HTTPException(409, "Ya hay una generación en curso")
        
        try:
            # ... generar simulacro ...
        finally:
            lock.release()
    """
    
    # Lua scripts atómicos para ownership-safe lock handling
    _RELEASE_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """

    _REFRESH_SCRIPT = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("expire", KEYS[1], tonumber(ARGV[2]))
    else
        return 0
    end
    """

    def __init__(
        self,
        institucion_id: int,
        area: str,
        ttl_seconds: int = 300,
        renew_interval_seconds: int = 20
    ):
        self.key = f"lock:simulacro_gen:{institucion_id}:{area}"
        self.ttl = ttl_seconds  # 5 minutos por defecto
        self.redis = get_redis()
        self._acquired = False
        self.owner_token = uuid.uuid4().hex
        # Renovar con margen suficiente para tolerar latencias/eventos puntuales.
        max_safe_interval = max(5, self.ttl // 3)
        self.renew_interval_seconds = min(max(5, renew_interval_seconds), max_safe_interval)
        self._renew_stop = threading.Event()
        self._renew_thread: Optional[threading.Thread] = None
    
    def acquire(self) -> bool:
        """
        Intenta adquirir el lock.
        
        Returns:
            True si se adquirió el lock, False si ya existe.
        """
        # SET con NX (solo si no existe) y EX (expiración), guardando owner_token.
        result = self.redis.set(self.key, self.owner_token, nx=True, ex=self.ttl)
        self._acquired = result is True
        if self._acquired:
            self.start_auto_renew()
        return self._acquired

    def refresh(self) -> bool:
        """
        Renueva TTL solo si el lock sigue siendo de este proceso.
        """
        if not self._acquired:
            return False
        try:
            refreshed = self.redis.eval(
                self._REFRESH_SCRIPT,
                1,
                self.key,
                self.owner_token,
                self.ttl
            )
            ok = refreshed == 1
            if not ok:
                # Perdimos ownership (expiró o fue reemplazado).
                self._acquired = False
            return ok
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning("JobLock refresh failed for %s: %s", self.key, e)
            return False

    def _renew_loop(self):
        """Heartbeat: renueva periódicamente el lock mientras esté adquirido."""
        while not self._renew_stop.wait(self.renew_interval_seconds):
            refreshed = self.refresh()
            if refreshed:
                continue
            if not self._acquired:
                logger.warning("JobLock heartbeat lost ownership for %s", self.key)
                break
            logger.warning("JobLock heartbeat transient failure for %s; retrying", self.key)

    def start_auto_renew(self):
        """Inicia hilo de renovación periódica del TTL."""
        if not self._acquired:
            return
        if self._renew_thread and self._renew_thread.is_alive():
            return
        self._renew_stop.clear()
        self._renew_thread = threading.Thread(
            target=self._renew_loop,
            name=f"joblock-renew-{self.key}",
            daemon=True
        )
        self._renew_thread.start()

    def stop_auto_renew(self):
        """Detiene el heartbeat de renovación."""
        self._renew_stop.set()
        if self._renew_thread and self._renew_thread.is_alive():
            self._renew_thread.join(timeout=2)
        self._renew_thread = None
    
    def release(self) -> bool:
        """
        Libera el lock.
        
        Returns:
            True si se liberó, False si no existía o no era nuestro.
        """
        self.stop_auto_renew()
        if not self._acquired:
            return False
        try:
            released = self.redis.eval(
                self._RELEASE_SCRIPT,
                1,
                self.key,
                self.owner_token
            )
            self._acquired = False
            return released == 1
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning("JobLock release failed for %s: %s", self.key, e)
            self._acquired = False
            return False
    
    def is_locked(self) -> bool:
        """Verifica si el lock existe (sin intentar adquirirlo)"""
        return self.redis.exists(self.key) == 1
    
    def __enter__(self):
        """Context manager: with JobLock(...) as lock"""
        if not self.acquire():
            raise Exception(f"No se pudo adquirir lock: {self.key}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Libera automáticamente al salir del contexto"""
        self.release()
        return False  # No suprimir excepciones


# ==========================================
# CACHÉ DE CONTEXTO ESTÁTICO
# ==========================================

class ContextCache:
    """
    Caché para contexto estático (archivos .md).
    
    Reduce lecturas de disco de ~50ms a ~1ms.
    
    Uso:
        cache = ContextCache()
        
        # Obtener contenido (desde caché o disco)
        contenido = cache.get("MATEMATICAS", "marco_referencia.md", fallback_loader)
        
        # Invalidar caché de un área
        cache.invalidate("MATEMATICAS")
        
        # Invalidar todo
        cache.invalidate_all()
    """
    
    # TTL por defecto: 1 hora (3600 segundos)
    DEFAULT_TTL = 3600
    
    # Prefijo para las claves de caché
    PREFIX = "ctx"
    
    def __init__(self, ttl_seconds: int = None):
        self.ttl = ttl_seconds or self.DEFAULT_TTL
        self.redis = get_redis()
    
    def _key(self, area: str, filename: str) -> str:
        """Genera la clave de caché"""
        return f"{self.PREFIX}:{area}:{filename}"
    
    def get(self, area: str, filename: str, loader_fn=None) -> Optional[str]:
        """
        Obtiene contenido del caché o lo carga y cachea.
        
        Args:
            area: Nombre del área (MATEMATICAS, CIENCIAS_NATURALES, etc.)
            filename: Nombre del archivo (marco_referencia.md, etc.)
            loader_fn: Función que carga el contenido si no está en caché.
                       Debe retornar str o None.
        
        Returns:
            Contenido del archivo o None si no existe.
        """
        key = self._key(area, filename)
        
        try:
            # Intentar desde caché
            cached = self.redis.get(key)
            if cached is not None:
                return cached
            
            # Si no está en caché y hay loader, cargar y cachear
            if loader_fn:
                content = loader_fn()
                if content:
                    self.set(area, filename, content)
                    return content
            
            return None
            
        except (redis.ConnectionError, redis.TimeoutError):
            # Si Redis falla, usar loader directamente
            if loader_fn:
                return loader_fn()
            return None
    
    def set(self, area: str, filename: str, content: str) -> bool:
        """
        Guarda contenido en el caché.
        
        Args:
            area: Nombre del área
            filename: Nombre del archivo
            content: Contenido a cachear
        
        Returns:
            True si se guardó correctamente.
        """
        key = self._key(area, filename)
        try:
            self.redis.setex(key, self.ttl, content)
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            return False
    
    def invalidate(self, area: str, filename: str = None) -> int:
        """
        Invalida el caché de un área o archivo específico.
        
        Args:
            area: Nombre del área
            filename: Si se especifica, solo invalida ese archivo.
                      Si es None, invalida todos los archivos del área.
        
        Returns:
            Número de claves eliminadas.
        """
        try:
            if filename:
                key = self._key(area, filename)
                return self.redis.delete(key)
            else:
                # Buscar todas las claves del área
                pattern = f"{self.PREFIX}:{area}:*"
                keys = list(self.redis.scan_iter(pattern))
                if keys:
                    return self.redis.delete(*keys)
                return 0
        except (redis.ConnectionError, redis.TimeoutError):
            return 0
    
    def invalidate_all(self) -> int:
        """
        Invalida todo el caché de contexto.
        
        Returns:
            Número de claves eliminadas.
        """
        try:
            pattern = f"{self.PREFIX}:*"
            keys = list(self.redis.scan_iter(pattern))
            if keys:
                return self.redis.delete(*keys)
            return 0
        except (redis.ConnectionError, redis.TimeoutError):
            return 0
    
    def stats(self) -> dict:
        """
        Obtiene estadísticas del caché.
        
        Returns:
            Dict con conteo de claves por área.
        """
        stats = {}
        try:
            pattern = f"{self.PREFIX}:*"
            for key in self.redis.scan_iter(pattern):
                parts = key.split(":")
                if len(parts) >= 2:
                    area = parts[1]
                    stats[area] = stats.get(area, 0) + 1
        except (redis.ConnectionError, redis.TimeoutError):
            pass
        return stats


# ==========================================
# JOB TRACKER (Para tareas asíncronas)
# ==========================================

import json
import uuid
from datetime import datetime

class JobTracker:
    """
    Rastreador de jobs asíncronos usando Redis.
    
    Uso:
        tracker = JobTracker()
        
        # Crear job
        job_id = tracker.create_job(institucion_id=5, areas=["MATEMATICAS"])
        
        # Actualizar progreso
        tracker.update_progress(job_id, area="MATEMATICAS", status="generating")
        
        # Obtener estado
        job = tracker.get_job(job_id)
        
        # Marcar completado
        tracker.complete_job(job_id, results=[...])
    """
    
    PREFIX = "job"
    TTL = 3600  # 1 hora (suficiente para consultar resultado después)
    
    def __init__(self):
        self.redis = get_redis()
    
    def _key(self, job_id: str) -> str:
        return f"{self.PREFIX}:{job_id}"
    
    def create_job(self, institucion_id: int, areas: list, user_id: int = None) -> str:
        """
        Crea un nuevo job de generación.
        
        Returns:
            job_id: UUID del job creado
        """
        job_id = str(uuid.uuid4())[:8]  # 8 caracteres suficientes
        
        job_data = {
            "id": job_id,
            "status": "queued",
            "institucion_id": institucion_id,
            "areas": areas,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "progress": {area: "pending" for area in areas},
            "results": [],
            "error": None,
            "completados": 0,
            "errores": 0
        }
        
        self.redis.setex(
            self._key(job_id),
            self.TTL,
            json.dumps(job_data)
        )
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[dict]:
        """Obtiene el estado actual del job"""
        data = self.redis.get(self._key(job_id))
        if data:
            return json.loads(data)
        return None
    
    def update_progress(self, job_id: str, area: str, status: str, error: str = None):
        """
        Actualiza el progreso de un área específica.
        
        status: pending, generating, validating, repairing, completed, error
        """
        job = self.get_job(job_id)
        if not job:
            return False
        
        job["progress"][area] = status
        job["updated_at"] = datetime.now().isoformat()
        job["status"] = "running"
        
        if status == "completed":
            job["completados"] = job.get("completados", 0) + 1
        elif status == "error":
            job["errores"] = job.get("errores", 0) + 1
        
        self.redis.setex(
            self._key(job_id),
            self.TTL,
            json.dumps(job)
        )
        return True
    
    def add_result(self, job_id: str, result: dict):
        """Agrega un resultado al job"""
        job = self.get_job(job_id)
        if not job:
            return False
        
        job["results"].append(result)
        job["updated_at"] = datetime.now().isoformat()
        
        self.redis.setex(
            self._key(job_id),
            self.TTL,
            json.dumps(job)
        )
        return True
    
    def complete_job(self, job_id: str, status: str = "completed"):
        """Marca el job como completado"""
        job = self.get_job(job_id)
        if not job:
            return False
        
        job["status"] = status
        job["updated_at"] = datetime.now().isoformat()
        job["completed_at"] = datetime.now().isoformat()
        
        self.redis.setex(
            self._key(job_id),
            self.TTL,
            json.dumps(job)
        )
        return True
    
    def fail_job(self, job_id: str, error: str):
        """Marca el job como fallido"""
        job = self.get_job(job_id)
        if not job:
            return False
        
        job["status"] = "failed"
        job["error"] = error
        job["updated_at"] = datetime.now().isoformat()
        
        self.redis.setex(
            self._key(job_id),
            self.TTL,
            json.dumps(job)
        )
        return True


# ==========================================
# CHAT VIEWING TRACKER
# ==========================================

CHAT_VIEWING_PREFIX = "chat:viewing"
CHAT_VIEWING_TTL = 60  # seconds


def set_chat_viewing(user_id: int, conversacion_id: int) -> None:
    try:
        r = get_redis()
        r.setex(f"{CHAT_VIEWING_PREFIX}:{user_id}", CHAT_VIEWING_TTL, str(conversacion_id))
    except (redis.ConnectionError, redis.TimeoutError):
        pass


def is_viewing_chat(user_id: int, conversacion_id: int) -> bool:
    try:
        r = get_redis()
        val = r.get(f"{CHAT_VIEWING_PREFIX}:{user_id}")
        return val is not None and str(val) == str(conversacion_id)
    except (redis.ConnectionError, redis.TimeoutError):
        return False
