"""
Script para extraer texto de PDFs de Ciencias Naturales
y generar archivos de texto para el contexto estático.
"""
import pdfplumber
import os

# Directorio de PDFs
PDF_DIR = "/Users/dramoscuello/icfes_project/backend/static/ciencias_naturales"
OUTPUT_DIR = "/Users/dramoscuello/icfes_project/backend/static/ciencias_naturales/extracted"

# Crear directorio de salida
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_text_from_pdf(pdf_path, output_path):
    """Extrae texto de un PDF y lo guarda en un archivo .txt"""
    print(f"\n📄 Procesando: {os.path.basename(pdf_path)}")
    
    full_text = []
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"   Total de páginas: {total_pages}")
        
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                full_text.append(f"\n--- Página {i+1} ---\n")
                full_text.append(text)
            
            # Progreso cada 10 páginas
            if (i + 1) % 10 == 0:
                print(f"   Procesadas {i+1}/{total_pages} páginas...")
    
    # Guardar texto extraído
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(full_text))
    
    # Estadísticas
    total_chars = sum(len(t) for t in full_text)
    total_words = sum(len(t.split()) for t in full_text)
    
    print(f"   ✅ Guardado en: {os.path.basename(output_path)}")
    print(f"   📊 Caracteres: {total_chars:,} | Palabras: ~{total_words:,} | Tokens estimados: ~{total_words * 1.3:.0f}")
    
    return total_chars, total_words

def main():
    print("=" * 60)
    print("🔍 Extractor de Texto PDF - Ciencias Naturales")
    print("=" * 60)
    
    pdfs = [
        ("marco_referencia_ciencias.pdf", "marco_referencia.txt"),
        ("niveles_desempeno_ciencias.pdf", "niveles_desempeno.txt"),
        ("simulacro_ciencias_001.pdf", "simulacro_ejemplo.txt"),
    ]
    
    total_stats = {"chars": 0, "words": 0}
    
    for pdf_name, txt_name in pdfs:
        pdf_path = os.path.join(PDF_DIR, pdf_name)
        output_path = os.path.join(OUTPUT_DIR, txt_name)
        
        if os.path.exists(pdf_path):
            chars, words = extract_text_from_pdf(pdf_path, output_path)
            total_stats["chars"] += chars
            total_stats["words"] += words
        else:
            print(f"⚠️  No encontrado: {pdf_name}")
    
    print("\n" + "=" * 60)
    print("📈 RESUMEN TOTAL")
    print("=" * 60)
    print(f"   Caracteres totales: {total_stats['chars']:,}")
    print(f"   Palabras totales: ~{total_stats['words']:,}")
    print(f"   Tokens estimados: ~{int(total_stats['words'] * 1.3):,}")
    print(f"\n   📁 Archivos guardados en: {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
