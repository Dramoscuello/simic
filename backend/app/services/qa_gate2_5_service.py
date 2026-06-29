from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class QAResult25:
    """Resultado de la validación de Gate 2.5 (Distribución de Dificultad Dinámica)"""
    passed: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict) # Para guardar los porcentajes reales
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "stats": self.stats
        }

class Gate25Validator:
    """
    Gate 2.5: Validación de Distribución de Dificultad
    ==================================================
    Valida que la distribución de preguntas generada coincida con 
    la configuración solicitada por el usuario (ej: 30% Fácil, 40% Media, 30% Difícil).
    
    Niveles de severidad:
    - Desviación < 10%: OK (Pasa silenciosamente)
    - Desviación 10-15%: WARNING (Pasa pero alerta)
    - Desviación > 15%: ERROR (Falla y activa Repair Loop)
    """
    
    # Tolerancias (en porcentaje decimal)
    TOLERANCIA_WARNING = 0.10
    TOLERANCIA_ERROR = 0.15
    
    @classmethod
    def validar(cls, contenido: Dict, config_dificultad: Optional[Dict[str, int]] = None) -> QAResult25:
        """
        Valida la distribución de dificultad.
        
        Args:
            contenido: El JSON del simulacro generado.
            config_dificultad: Dict con { 'facil': 30, 'medio': 40, 'dificil': 30 }
                               Si es None, se asume distribución por defecto o se omite validación estricta.
        """
        result = QAResult25()
        preguntas = contenido.get("preguntas", [])
        total = len(preguntas)
        
        if total == 0:
            result.errors.append("No hay preguntas para validar.")
            result.passed = False
            return result
            
        # Si no hay config, validamos solo que existan los campos (básico)
        if not config_dificultad:
            # Podríamos definir un default, pero mejor retornar pass con warning
            result.warnings.append("No se especificó configuración de dificultad, saltando validación estricta.")
            return result
            
        # 1. Normalizar configuración solicitada (convertir de 30 a 0.30)
        # Asumimos que viene en enteros 0-100
        solicitado = {
            "facil": config_dificultad.get("facil", 0) / 100.0,
            "medio": config_dificultad.get("medio", 0) / 100.0,
            "dificil": config_dificultad.get("dificil", 0) / 100.0
        }
        
        # 2. Calcular distribución real
        conteo = {"facil": 0, "medio": 0, "dificil": 0}
        no_clasificadas = 0
        
        for p in preguntas:
            raw_dif = str(p.get("dificultad", "")).lower().strip()
            
            # Normalización robusta
            if any(x in raw_dif for x in ["facil", "fác", "easy", "baja", "basico"]):
                conteo["facil"] += 1
            elif any(x in raw_dif for x in ["medio", "media", "medium", "intermedia"]):
                conteo["medio"] += 1
            elif any(x in raw_dif for x in ["dificil", "difícil", "hard", "alta", "compleja"]):
                conteo["dificil"] += 1
            else:
                no_clasificadas += 1
                
        # Guardar stats para debug
        result.stats = {
            "total": total,
            "conteo": conteo,
            "no_clasificadas": no_clasificadas
        }
        
        # 3. Validar no clasificadas
        if no_clasificadas > 0:
            # Si más del 10% no tienen clasificación válida, es un error grave
            pct_no_clas = no_clasificadas / total
            msg = f"{no_clasificadas} preguntas ({pct_no_clas:.1%}) tienen dificultad inválida o vacía."
            
            if pct_no_clas > cls.TOLERANCIA_ERROR:
                result.errors.append(msg)
            else:
                result.warnings.append(msg)
        
        # 4. Validar desviaciones por nivel
        for nivel, target_pct in solicitado.items():
            if target_pct == 0: continue # Ignorar niveles no solicitados
            
            real_count = conteo.get(nivel, 0)
            real_pct = real_count / total
            desviacion = abs(real_pct - target_pct)
            
            # Formatear mensaje
            msg = (f"Dificultad '{nivel}': Real {real_pct:.1%} vs Solicitado {target_pct:.1%} "
                   f"(Desviación: {desviacion:.1%})")
            
            # Evaluar severidad
            if desviacion > cls.TOLERANCIA_ERROR:
                result.errors.append(f"{msg} -> Excede tolerancia máxima de {cls.TOLERANCIA_ERROR:.0%}")
            elif desviacion > cls.TOLERANCIA_WARNING:
                result.warnings.append(f"{msg} -> Advertencia (tolerancia {cls.TOLERANCIA_WARNING:.0%})")
                
        # 5. Resultado final
        result.passed = len(result.errors) == 0
        
        return result
