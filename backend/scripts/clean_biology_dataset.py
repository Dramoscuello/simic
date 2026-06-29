import json
import re

def clean_dataset(input_file, output_file):
    print(f"🧹 Iniciando limpieza de {input_file}...")
    
    # Patrones de exclusión (Ruido)
    EXCLUDE_PATTERNS = [
        r"Ministerio de Educación Nacional",
        r"Derechos reservados",
        r"ISBN",
        r"Ley 23 de 1982",
        r"Créditos editoriales",
        r"Equipo técnico",
        r"Tabla de contenido",
        r"Bibliografía",
        r"AGUIRRE ASESORES",
    ]
    
    # Patrones de actividades (No son hechos científicos)
    ACTIVITY_PATTERNS = [
        r"Resuelve en tu cuaderno",
        r"Reúnete con un compañero",
        r"Realiza los dibujos",
        r"Elabora una tabla",
        r"Consulta en la biblioteca",
        r"Dibuja en tu cuaderno",
    ]

    kept_count = 0
    removed_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as fin, \
         open(output_file, 'w', encoding='utf-8') as fout:
        
        for line in fin:
            try:
                data = json.loads(line)
                text = data.get("text", "")
                
                # 1. Filtro de Longitud (Evitar fragmentos muy cortos o vacíos)
                if len(text.split()) < 15:
                    removed_count += 1
                    continue
                
                # 2. Filtro de Ruido Legal/Editorial
                if any(re.search(pat, text, re.IGNORECASE) for pat in EXCLUDE_PATTERNS):
                    # Excepción: Si el chunk tiene mucho contenido útil además del copyright
                    if len(text) < 300: # Si es corto y tiene copyright -> Eliminar
                        removed_count += 1
                        continue

                # 3. Filtro de Actividades (Opcional: podemos ser menos estrictos aquí)
                # Si empieza muy explícitamente con una orden de tarea
                if any(text.strip().lower().startswith(pat.lower()) for pat in ["Resuelve", "Elabora", "Dibuja"]):
                     removed_count += 1
                     continue

                # Limpieza de texto (Quitar encabezados repetitivos dentro del texto)
                text = text.replace("Ministerio de Educación Nacional", "")
                text = text.replace("Secundaria Activa", "")
                data["text"] = " ".join(text.split()) # Normalizar espacios
                
                # Guardar
                fout.write(json.dumps(data, ensure_ascii=False) + "\n")
                kept_count += 1
                
            except json.JSONDecodeError:
                continue

    print(f"✅ Limpieza completada.")
    print(f"   Originales procesados: {kept_count + removed_count}")
    print(f"   Conservados (Útiles):  {kept_count}")
    print(f"   Eliminados (Ruido):    {removed_count}")
    print(f"   Archivo limpio generado en: {output_file}")

if __name__ == "__main__":
    INPUT = "/var/www/SIMIC/backend/static/ciencias_naturales/dataset/chunks.jsonl"
    OUTPUT = "/var/www/SIMIC/backend/static/ciencias_naturales/dataset/chunks_clean.jsonl"
    clean_dataset(INPUT, OUTPUT)
