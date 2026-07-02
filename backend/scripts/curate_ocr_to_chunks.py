#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
curate_ocr_to_chunks.py
OCR (si hace falta) + sanitización + export a chunks.jsonl

Salida estándar:
- docs.json
- chunks.jsonl   (FUENTE FACTUAL para backend)
- chunks.csv
- qc_report.json
- README.md

Requisitos:
  sudo apt install tesseract-ocr tesseract-ocr-spa
  pip install pymupdf pillow pytesseract

Uso:
  python curate_ocr_to_chunks.py --input "/ruta/libro.pdf" --out "/ruta/salida"
  python curate_ocr_to_chunks.py --input "libro.pdf" --out "salida" --force_ocr
  python curate_ocr_to_chunks.py --input "libro.pdf" --out "salida" --page_start 15 --page_end 300
"""

import argparse
import csv
import datetime as _dt
import hashlib
import io
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import fitz  # PyMuPDF
from PIL import Image
import pytesseract


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_file(path: str, block_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(block_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def word_count(s: str) -> int:
    return len(re.findall(r"\b\w+\b", s or ""))


def normalize_spaces(text: str) -> str:
    text = (text or "").replace("\u00ad", "")  # soft hyphen
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def has_text_layer(sample: str, min_words: int = 30) -> bool:
    return word_count(sample) >= min_words


# -------------------------
# Sanitization rules
# -------------------------

GLOBAL_KEEP_PLACES = [
    "Islas Galápagos","Galápagos","Amazonas","El Amazonas","Everest","El Everest",
    "Antártida","Antártica","Himalaya","Himalayas","Sahara","Ártico","Polo Norte","Polo Sur"
]

EDITORIAL_KILL = re.compile(
    r"\b(ISBN|derechos reservados|impreso en|edici[oó]n revisada|edici[oó]n actualizada|"
    r"cr[eé]ditos|realizaci[oó]n art[ií]stica|dise[nñ]o|diagramaci[oó]n|fotograf[ií]a|"
    r"registro|dep[oó]sito legal|editores|equipo|producci[oó]n|carta al estudiante|"
    r"c[oó]mo est[aá] organizado este libro|índice|índice tem[aá]tico|tabla de contenido|presentaci[oó]n)\b",
    re.IGNORECASE
)

INSTRUCTION_KILL = re.compile(
    r"\b(Re[uú]nete|Dibuja|Escribe|Contesta|Discute|Comenta|Consulta|Investiga|"
    r"En tu cuaderno|en parejas|en grupo|trabajo de laboratorio|trabajo de campo|webquest)\b",
    re.IGNORECASE
)

PAGE_REF = re.compile(r"\b(Ver|véase)\s+p[aá]g\.?\s*\d+\b", re.IGNORECASE)

INSTITUTION_KILL = re.compile(
    r"\b(Secretar[ií]a|Ministerio|BOE|Constituci[oó]n|SEP|Diario Oficial|ley\s+\d+)\b",
    re.IGNORECASE
)

CURRENCY = re.compile(r"(\€|MXN|pesos\s+mexicanos?|USD|\$|euros?)", re.IGNORECASE)

GEO_WORDS = [
    "México","Chiapas","Colombia","Argentina","Chile","Perú","Brasil","España",
    "Estados Unidos","EE.UU.","EUA","Europa","Bogotá","Madrid","Barcelona","Londres"
]
GEO_RE = re.compile(r"\b(" + "|".join([re.escape(x) for x in GEO_WORDS]) + r")\b", re.IGNORECASE)

BIOME_TERMS = [
    "selva húmeda","selva","bosque húmedo","bosque","desierto","tundra","sabana","pradera",
    "manglar","arrecife","océano","mar","lago","río","cordillera","montaña","glaciar",
    "humedal","estuario"
]
BIOME_RE = re.compile(r"\b(" + "|".join([re.escape(x) for x in BIOME_TERMS]) + r")\b", re.IGNORECASE)


def contains_global_place(text: str) -> bool:
    t = (text or "").lower()
    return any(p.lower() in t for p in GLOBAL_KEEP_PLACES)


def remove_currency_sentences(text: str) -> str:
    sents = re.split(r"(?<=[\.\!\?])\s+", text)
    kept = []
    for s in sents:
        if CURRENCY.search(s):
            continue
        kept.append(s)
    return " ".join([k for k in kept if k]).strip()


def generalize_geography(text: str) -> str:
    def repl_paren(m):
        inner = m.group(1)
        if contains_global_place(inner):
            return "(" + inner + ")"
        if BIOME_RE.search(inner):
            return ""
        return ""

    # Drop parenthetical political locations unless globally important
    text = re.sub(r"\(([^)]{2,120})\)", repl_paren, text)

    # Specific example pattern
    text = re.sub(
        r"\bEn\s+la\s+selva\s+de\s+[A-ZÁÉÍÓÚÑ][^,;\.\)\n]{2,60}",
        "En los ecosistemas de selva húmeda",
        text,
        flags=re.IGNORECASE
    )

    # More general: "en el bosque de X" -> "en ecosistemas de bosque"
    text = re.sub(
        r"\b(en\s+(?:la|el|los|las)\s+(" + "|".join([re.escape(x) for x in BIOME_TERMS]) + r"))\s+de\s+[A-ZÁÉÍÓÚÑ][^,;\.\)\n]{2,60}",
        r"en ecosistemas de \2",
        text,
        flags=re.IGNORECASE
    )

    # Remove political geography tokens unless global place is present
    if not contains_global_place(text):
        text = GEO_RE.sub("", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        text = re.sub(r"\s+,", ",", text)
        text = re.sub(r"\bde\s+(,|\.)", r"\1", text)
    return text


def sanitize_text(text: str) -> str:
    if not text:
        return ""
    text = normalize_spaces(text)

    out_lines = []
    for ln in text.split("\n"):
        ln = ln.strip()
        if not ln:
            continue
        if EDITORIAL_KILL.search(ln):
            continue
        if INSTRUCTION_KILL.search(ln):
            continue
        if INSTITUTION_KILL.search(ln) and not contains_global_place(ln):
            continue
        ln = PAGE_REF.sub("", ln).strip()
        if re.fullmatch(r"\d{1,4}", ln):
            continue
        out_lines.append(ln)

    text = " ".join(out_lines)
    text = remove_currency_sentences(text)
    text = generalize_geography(text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


# -------------------------
# OCR + extraction
# -------------------------

@dataclass
class OCRConfig:
    dpi: int = 140
    lang: str = "spa"
    tess_config: str = "--oem 1 --psm 6"
    timeout_sec: Optional[int] = None  # None = sin timeout


def extract_pages_textlayer(pdf_path: str, page_indices_0based: List[int]) -> List[Tuple[int, str]]:
    doc = fitz.open(pdf_path)
    out = []
    for i in page_indices_0based:
        page = doc.load_page(i)
        t = page.get_text("text") or ""
        out.append((i + 1, t))
    doc.close()
    return out


def extract_pages_ocr(pdf_path: str, page_indices_0based: List[int], cfg: OCRConfig) -> List[Tuple[int, str]]:
    doc = fitz.open(pdf_path)
    out = []
    mat = fitz.Matrix(cfg.dpi / 72, cfg.dpi / 72)

    for i in page_indices_0based:
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        if cfg.timeout_sec is None:
            t = pytesseract.image_to_string(img, lang=cfg.lang, config=cfg.tess_config)
        else:
            t = pytesseract.image_to_string(img, lang=cfg.lang, config=cfg.tess_config, timeout=cfg.timeout_sec)
        out.append((i + 1, t))

    doc.close()
    return out


def estimate_ocr_gaps(text: str) -> int:
    """Heurística simple de 'gaps' OCR: caracteres inválidos + palabras largas sin vocal."""
    if not text:
        return 0
    bad_char = text.count("\ufffd")
    tokens = re.findall(r"\b\w+\b", text.lower())
    no_vowel_long = 0
    for t in tokens:
        if len(t) >= 12 and not re.search(r"[aeiouáéíóúü]", t):
            no_vowel_long += 1
    return bad_char + no_vowel_long


def quality_tier_from_stats(wc: int, ocr_gaps: int) -> str:
    """Clasificación básica de calidad para el chunk."""
    if wc <= 0:
        return "low"
    gap_rate = ocr_gaps / max(1, wc)
    if wc < 80 or gap_rate > 0.02:
        return "low"
    if gap_rate > 0.005:
        return "ok"
    return "strict"


def detect_structure(raw_text: str) -> Dict[str, Optional[str]]:
    """Extrae estructura básica (unidad/section) y headings simples."""
    unit = None
    section = None
    headings: List[str] = []
    for ln in (raw_text or "").split("\n"):
        s = ln.strip()
        if not s:
            continue
        if EDITORIAL_KILL.search(s):
            continue
        if INSTRUCTION_KILL.search(s):
            continue
        if INSTITUTION_KILL.search(s) and not contains_global_place(s):
            continue
        if re.match(r"^(UNIDAD|CAP[IÍ]TULO|SECCI[ÓO]N|TEMA)\b", s, re.IGNORECASE):
            if re.match(r"^UNIDAD\b", s, re.IGNORECASE):
                unit = s
            elif re.match(r"^SECCI[ÓO]N\b", s, re.IGNORECASE):
                section = s
            else:
                headings.append(s)
            continue
        if s.isupper() and 2 <= word_count(s) <= 8 and len(s) <= 80:
            headings.append(s)
    return {
        "unidad": unit,
        "capitulo": None,
        "section_type": "expository",
        "headings": headings,
        "section": section,
    }


# -------------------------
# Chunking
# -------------------------

def chunk_text_by_words(text: str, target_words: int = 170, hard_max: int = 240, min_tail: int = 110) -> List[str]:
    words = (text or "").split()
    if not words:
        return []
    if len(words) <= hard_max:
        return [" ".join(words).strip()]

    chunks: List[str] = []
    start = 0
    while start < len(words):
        end = min(start + target_words, len(words))
        if len(words) - end < min_tail and end < len(words):
            end = min(start + hard_max, len(words))
        ch = " ".join(words[start:end]).strip()
        if word_count(ch) >= 55:
            chunks.append(ch)
        start = end
    return chunks


def chunk_text_by_sentences(text: str, target_words: int = 170, hard_max: int = 240) -> List[str]:
    """Agrupa por oraciones para evitar cortar ideas a la mitad."""
    if not text:
        return []
    sents = re.split(r"(?<=[\.\!\?])\s+", text.strip())
    if len(sents) <= 1:
        return chunk_text_by_words(text, target_words=target_words, hard_max=hard_max)

    chunks: List[str] = []
    current: List[str] = []
    current_wc = 0
    for s in sents:
        wc = word_count(s)
        if wc == 0:
            continue
        if current_wc + wc > hard_max and current:
            chunks.append(" ".join(current).strip())
            current = [s]
            current_wc = wc
        else:
            current.append(s)
            current_wc += wc
        if current_wc >= target_words:
            chunks.append(" ".join(current).strip())
            current = []
            current_wc = 0
    if current:
        chunks.append(" ".join(current).strip())
    # Filtrar muy cortos
    return [c for c in chunks if word_count(c) >= 55]


def run_pipeline(
    input_path: str,
    out_dir: str,
    force_ocr: bool,
    page_start: int,
    page_end: int,
    dpi: int,
    lang: str,
    timeout: Optional[int],
) -> Path:
    input_path = str(Path(input_path).expanduser().resolve())
    out_path = Path(out_dir).expanduser().resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(input_path)
    pages_total = doc.page_count
    doc.close()

    ps = max(1, page_start)
    pe = min(pages_total, page_end if page_end > 0 else pages_total)
    page_indices = list(range(ps - 1, pe))

    # detect text layer (muestreo de páginas)
    sample_texts = []
    try:
        doc = fitz.open(input_path)
        sample_indices = list(dict.fromkeys([
            page_indices[0],
            page_indices[len(page_indices) // 2],
            page_indices[-1],
        ]))
        for i in sample_indices:
            sample_texts.append(doc.load_page(i).get_text("text") or "")
        doc.close()
    except Exception:
        sample_texts = []

    sample_hits = sum(1 for t in sample_texts if has_text_layer(t, min_words=30))
    use_ocr_all = force_ocr or (sample_hits == 0)

    cfg = OCRConfig(dpi=dpi, lang=lang, timeout_sec=timeout)
    source_type = "pdf_scanned_ocr" if use_ocr_all else "pdf_text"

    sanitized_pages: List[Dict] = []
    ocr_pages_count = 0

    # extracción mixta: OCR solo si la página no tiene texto suficiente
    doc = fitz.open(input_path)
    for i in page_indices:
        page = doc.load_page(i)
        raw = page.get_text("text") or ""
        if use_ocr_all or not has_text_layer(raw, min_words=30):
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            if cfg.timeout_sec is None:
                raw = pytesseract.image_to_string(img, lang=cfg.lang, config=cfg.tess_config)
            else:
                raw = pytesseract.image_to_string(img, lang=cfg.lang, config=cfg.tess_config, timeout=cfg.timeout_sec)
            ocr_pages_count += 1
        s = sanitize_text(raw)
        if word_count(s) >= 55:
            sanitized_pages.append({
                "page": i + 1,
                "text": s,
                "raw": raw
            })
    doc.close()

    file_sha = sha256_file(input_path)
    doc_id = f"doc_{file_sha[:12]}"
    now = utc_now()

    chunks: List[Dict] = []
    for p in sanitized_pages:
        structure = detect_structure(p.get("raw", ""))
        for ch in chunk_text_by_sentences(p["text"]):
            wc = word_count(ch)
            ocr_gaps = estimate_ocr_gaps(ch)
            chunk_id = f"{doc_id}::chunk_{len(chunks)+1:05d}"
            chunks.append({
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "language": "es",
                "source_type": source_type,
                "quality_tier": quality_tier_from_stats(wc, ocr_gaps),
                "page_start": p["page"],
                "page_end": p["page"],
                "structure": structure,
                "text": ch,
                "word_count": wc,
                "ocr_gaps": ocr_gaps,
                "text_sha256": sha256_text(ch),
                "created_at_utc": now
            })

    docs = [{
        "doc_id": doc_id,
        "title": Path(input_path).stem,
        "language": "es",
        "publisher": None,
        "year": None,
        "pages_total": pages_total,
        "page_range_used": {"start": ps, "end": pe},
        "pages_sanitized": len(sanitized_pages),
        "source_type": source_type,
        "source_path": os.path.basename(input_path),
        "source_sha256": file_sha,
        "ingested_at_utc": now,
        "notes": "Reglas: universalización geográfica; eliminación de instituciones/leyes; eliminación de ejemplos monetarios; limpieza editorial."
    }]
    with open(out_path / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    return out_path


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="OCR + sanitización + chunks.jsonl (referente factual)")
    p.add_argument("--input", required=True, help="Ruta al PDF")
    p.add_argument("--out", required=True, help="Carpeta de salida")
    p.add_argument("--force_ocr", action="store_true", help="Fuerza OCR incluso si hay capa de texto")
    p.add_argument("--page_start", type=int, default=1, help="Página inicio (1-based, inclusive)")
    p.add_argument("--page_end", type=int, default=0, help="Página fin (1-based, inclusive). 0 = hasta el final")
    p.add_argument("--dpi", type=int, default=140, help="DPI OCR (110-220 recomendado). Más DPI = más lento.")
    p.add_argument("--lang", default="spa", help="Idioma Tesseract (ej: spa)")
    p.add_argument("--timeout", type=int, default=0, help="Timeout OCR por página (seg). 0 = sin timeout")
    return p


def main():
    args = build_argparser().parse_args()
    timeout = None if args.timeout == 0 else args.timeout
    out = run_pipeline(
        input_path=args.input,
        out_dir=args.out,
        force_ocr=args.force_ocr,
        page_start=args.page_start,
        page_end=args.page_end,
        dpi=args.dpi,
        lang=args.lang,
        timeout=timeout,
    )
    print(str(out))


if __name__ == "__main__":
    main()
