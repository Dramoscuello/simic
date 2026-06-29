"""
Script para extraer texto de los PDFs de Inglés
"""
import pdfplumber
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AREA_DIR = os.path.join(BASE_DIR, "static", "ingles")
OUTPUT_DIR = os.path.join(AREA_DIR, "extracted")

os.makedirs(OUTPUT_DIR, exist_ok=True)

PDF_FILES = {
    "marco_referencia_ingles.pdf": "marco_referencia_ingles.txt",
    "niveles_desempeno_ingles.pdf": "niveles_desempeno_ingles.txt",
    "patron_simulacro_ingles.pdf": "patron_simulacro_ingles.txt",
}

def extract_pdf(pdf_path: str, output_path: str):
    print(f"\n📄 Procesando: {os.path.basename(pdf_path)}")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_text = []
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    all_text.append(f"\n--- Página {i} ---\n")
                    all_text.append(text)
                if i % 10 == 0:
                    print(f"   Procesadas {i}/{total_pages} páginas...")
            full_text = "\n".join(all_text)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            words = len(full_text.split())
            print(f"   ✅ Guardado: {os.path.basename(output_path)}")
            print(f"   📊 {total_pages} páginas, ~{words} palabras")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    print("="*60)
    print("🔬 Extracción de PDFs - INGLÉS")
    print("="*60)
    for pdf_name, output_name in PDF_FILES.items():
        pdf_path = os.path.join(AREA_DIR, pdf_name)
        output_path = os.path.join(OUTPUT_DIR, output_name)
        if os.path.exists(pdf_path):
            extract_pdf(pdf_path, output_path)
        else:
            print(f"\n⚠️ No encontrado: {pdf_name}")
    print("\n" + "="*60)
    print("✅ Extracción completada")
    print(f"📁 Archivos en: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
