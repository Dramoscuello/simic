
import csv
import json
import os
import re
import logging
from collections import defaultdict
from typing import List, Dict, Set, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class AnalyticIssue:
    pregunta_id: int
    nivel_esperado: str
    porcentaje_off_level: float
    palabras_dificiles: List[str]
    mensaje: str

@dataclass
class GateEnglishAnalyticResult:
    passed: bool = True
    issues: List[AnalyticIssue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

class GateEnglishAnalyticValidator:
    """
    Gate 9 (Analítico): Validador de Nivel de Inglés basado en Frecuencia Léxica.
    Usa el corpus Oxford 3000/5000 (CEFR) para auditar la dificultad del vocabulario.
    """
    
    _lexicon: Dict[str, str] = {}
    _loaded = False
    
    # Mapeo de Niveles CEFR a valores numéricos para comparación
    LEVEL_RANK = {
        "a1": 1, "a2": 2, 
        "b1": 3, "b2": 4, 
        "c1": 5, "c2": 6
    }
    
    # Mapeo de Partes del Examen a Nivel Máximo Permitido
    PART_MAX_LEVEL = {
        "Parte 1": "a2", # Avisos (A1/A2)
        "Parte 2": "a2", # Vocabulario (A1/A2)
        "Parte 3": "a2", # Conversaciones (A2)
        "Parte 4": "b1", # Gramática I (A2/B1)
        "Parte 5": "b1", # Literal (B1)
        "Parte 6": "b2", # Inferencial (B1+)
        "Parte 7": "b2"  # Gramática II (B1+)
    }

    @classmethod
    def _load_lexicon(cls):
        """Carga el CSV de Oxford CEFR en memoria (Singleton)"""
        if cls._loaded:
            return

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_path = os.path.join(base_dir, "data", "cefr_lexicon.csv")
        
        if not os.path.exists(csv_path):
            logger.warning(f"⚠️ Gate Inglés: No se encontró {csv_path}. Saltando validación analítica.")
            return

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    word = row.get("word", "").lower().strip()
                    level = row.get("level", "").lower().strip()
                    if word and level:
                        # Si la palabra ya existe, nos quedamos con el nivel más bajo (conservador)
                        if word not in cls._lexicon:
                            cls._lexicon[word] = level
                        else:
                            # Comparar niveles y guardar el menor
                            current_rank = cls.LEVEL_RANK.get(cls._lexicon[word], 0)
                            new_rank = cls.LEVEL_RANK.get(level, 0)
                            if new_rank < current_rank:
                                cls._lexicon[word] = level
                        count += 1
            
            cls._loaded = True
            print(f"📚 Gate Inglés: Cargadas {len(cls._lexicon)} palabras del léxico CEFR.")
            
        except Exception as e:
            logger.error(f"Error cargando léxico CEFR: {e}")

    @classmethod
    def _consultar_juez_llm(cls, texto: str, nivel_target: str, palabras_flagged: List[str]) -> bool:
        """
        FALLBACK: Consulta a GPT-4o-mini si las palabras marcadas hacen el texto incomprensible.
        Retorna True si el LLM 'salva' la pregunta (Aprueba).
        Retorna False si el LLM confirma que es muy difícil (Rechaza).
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            prompt = f"""
ACT AS AN ENGLISH TEACHER (CEFR EXPERT).

CONTEXT:
I have a text intended for Level **{nivel_target.upper()}**.
My vocabulary algorithm flagged these words as too difficult: {', '.join(palabras_flagged)}.

TEXT TO EVALUATE:
"{texto[:500]}..."

DECISION:
Are these words problematic for a {nivel_target.upper()} student in this specific context?
- If the words are cognates (easy to guess for Spanish speakers) or defined in context -> APPROVE.
- If the words block comprehension -> REJECT.

RESPONSE FORMAT (JSON):
{{ "verdict": "APPROVE" | "REJECT", "reason": "brief explanation" }}
"""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0
            )
            data = json.loads(response.choices[0].message.content)
            
            if data.get("verdict") == "APPROVE":
                print(f"         ⚖️ Juez LLM: APELACIÓN ACEPTADA ({data.get('reason')})")
                return True
            else:
                print(f"         ⚖️ Juez LLM: CONFIRMA RECHAZO ({data.get('reason')})")
                return False
                
        except Exception as e:
            logger.error(f"Error en Juez LLM Fallback: {e}")
            return False # Ante error, mantenemos el rechazo estricto

    @classmethod
    def validar_nivel_analitico(cls, preguntas: List[Dict]) -> GateEnglishAnalyticResult:
        """
        Valida que el vocabulario de las preguntas no exceda el nivel permitido.
        Regla: Si > 20% de las palabras significativas exceden el nivel -> Fallback a LLM.
        """
        # Asegurar carga
        cls._load_lexicon()
        
        result = GateEnglishAnalyticResult()
        
        if not cls._loaded:
            result.stats["status"] = "skipped_missing_lexicon"
            return result

        preguntas_ingles = [p for p in preguntas if "Parte" in p.get("componente", "")]
        print(f"\n🇬🇧 Gate 9 (Analítico + Híbrido): Auditando léxico de {len(preguntas_ingles)} preguntas...")
        
        issues_count = 0
        
        for p in preguntas_ingles:
            parte_raw = p.get("componente", "Desconocido")
            # Normalizar nombre parte
            parte_key = next((k for k in cls.PART_MAX_LEVEL if k in parte_raw), None)
            
            if not parte_key:
                continue
                
            max_level_str = cls.PART_MAX_LEVEL[parte_key]
            max_rank = cls.LEVEL_RANK.get(max_level_str, 100)
            
            # Extraer texto total
            full_text = f"{p.get('contexto', '')} {p.get('enunciado', '')}"
            opciones = p.get("opciones", [])
            if isinstance(opciones, list):
                full_text += " " + " ".join([o.get("texto", "") for o in opciones])
            
            # Tokenización simple
            words = re.findall(r"\b[a-zA-Z]{2,}\b", full_text.lower())
            
            total_scorable = 0
            off_level_words = []
            
            for w in words:
                if w not in cls._lexicon:
                    continue
                
                word_level = cls._lexicon[w]
                word_rank = cls.LEVEL_RANK.get(word_level, 0)
                
                total_scorable += 1
                
                if word_rank > max_rank:
                    off_level_words.append(f"{w}({word_level})")
            
            if total_scorable > 0:
                percent_off = len(off_level_words) / total_scorable
                
                # UMBRAL DE TOLERANCIA: 20%
                if percent_off > 0.20:
                    msg_base = f"Exceso de complejidad léxica ({percent_off:.0%}). Nivel máx: {max_level_str.upper()}."
                    sample_words = list(set(off_level_words))[:8] # Unique words snippet
                    
                    print(f"      ⚠️ ALERTA [Q{p.get('id')}] ({parte_key}): {msg_base}. Consultando Juez LLM...")
                    
                    # FALLBACK: Consultar al Juez LLM
                    aprobado_por_juez = cls._consultar_juez_llm(full_text, max_level_str, sample_words)
                    
                    if not aprobado_por_juez:
                        issues_count += 1
                        result.issues.append(AnalyticIssue(
                            pregunta_id=p.get("id"),
                            nivel_esperado=max_level_str,
                            porcentaje_off_level=percent_off,
                            palabras_dificiles=sample_words,
                            mensaje=msg_base + " (Confirmado por IA)"
                        ))
                    # Si aprobado_por_juez es True, no hacemos nada (pasa)
                else:
                    pass

        result.passed = (issues_count == 0)
        result.stats["errores"] = issues_count
        
        return result
