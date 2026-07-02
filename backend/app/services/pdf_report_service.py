
import os
import re
from typing import Dict, List, Tuple
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart

class PDFReportService:
    AREA_FILES = {
        "MATEMATICAS": "matematicas/extracted/niveles_desempeno_matematicas.md",
        "LECTURA_CRITICA": "lectura_critica/extracted/niveles_desempeno_lectura_critica.md",
        "SOCIALES_CIUDADANAS": "sociales/extracted/niveles_desempeno_sociales.md",
        "CIENCIAS_NATURALES": "ciencias_naturales/extracted/niveles_desempeno_ciencia_naturales.md",
        "INGLES": "ingles/extracted/niveles_desempeno_ingles.md"
    }

    @staticmethod
    def _parse_markdown_levels(area: str) -> List[Dict]:
        """
        Parses the markdown file for the given area to extract levels, ranges and skills.
        Improved regex to handle variations in markdown format.
        """
        file_rel_path = PDFReportService.AREA_FILES.get(area)
        if not file_rel_path:
            return []

        # Resolver ubicación de estáticos robustamente.
        # Prioridad: backend/static (ruta actual real), con fallback a app/static.
        cwd = os.getcwd()
        current_dir = os.path.dirname(__file__)
        base_candidates = [
            os.path.join(cwd, "backend", "static"),
            os.path.join(cwd, "static"),
            os.path.join(cwd, "backend", "app", "static"),
            os.path.join(cwd, "app", "static"),
            os.path.abspath(os.path.join(current_dir, "..", "..", "static")),
            os.path.abspath(os.path.join(current_dir, "..", "static")),
        ]

        file_path = None
        seen = set()
        for base in base_candidates:
            abs_base = os.path.abspath(base)
            if abs_base in seen:
                continue
            seen.add(abs_base)

            candidate = os.path.join(abs_base, file_rel_path)
            if os.path.exists(candidate):
                file_path = candidate
                break

        if not file_path:
            print(f"File not found for area {area}. Tried: {', '.join(sorted(seen))}")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        levels = []
        ranges = {} 
        
        # 1. Extract Ranges (e.g. "* **Nivel 1:** 0 a 35" OR "### Nivel 1 (0–35)")
        # Pattern A: Bullet list range - Exact match for " * **Nivel X:** Y a Z "
        range_pattern_a = re.compile(r'\*\s*\*\*Nivel\s*(\d+)[:]?\*\*\s*(\d+)\s*a\s*(\d+)', re.IGNORECASE)
        for match in range_pattern_a.finditer(content):
            ranges[int(match.group(1))] = (int(match.group(2)), int(match.group(3)))
            
        # Pattern B: Header range (fallback if A fails or complements)
        # Handle unicode dashes (–)
        range_pattern_b = re.compile(r'### Nivel\s*(\d+)\s*\((\d+)[-–—](\d+)\)', re.IGNORECASE)
        for match in range_pattern_b.finditer(content):
            ranges[int(match.group(1))] = (int(match.group(2)), int(match.group(3)))

        # 2. Extract Skills
        # Sections usually start with "### Nivel X"
        sections = re.split(r'### Nivel\s*(\d+)', content)
        
        # sections[0] = intro
        # sections[1] = level_num, sections[2] = content...
        for i in range(1, len(sections), 2):
            try:
                lvl_num = int(sections[i])
                text_content = sections[i+1]
                
                # Extract bullets (lines starting with * or -)
                bullets = []
                for line in text_content.split('\n'):
                    line = line.strip()
                    # Check for bullet points
                    if line.startswith('* ') or line.startswith('- '):
                        # Avoid capturing the range definition line if it appears here (e.g. * **Nivel 1:** 0 a 35)
                        if "**Nivel" in line:
                            continue
                            
                        clean_line = line[2:].strip()
                        # Clean markdown bold/italics
                        clean_line = clean_line.replace('**', '').replace('*', '').replace('__', '').replace('_', '')
                        if clean_line:
                            bullets.append(clean_line)
                
                # Assign default range if not found (fallback)
                default_ranges = {1: (0,35), 2: (36,50), 3: (51,70), 4: (71,100)}
                min_s, max_s = ranges.get(lvl_num, default_ranges.get(lvl_num, (0,100)))
                
                # Only add if we have skills or it's a valid level
                if bullets or lvl_num in ranges:
                    levels.append({
                        'level': lvl_num,
                        'min': min_s,
                        'max': max_s,
                        'skills': bullets
                    })
            except Exception as e:
                print(f"Error parsing section {i}: {e}")

        # Sort by level
        return sorted(levels, key=lambda x: x['level'])

    @staticmethod
    def _get_level_for_score(score: float, levels: List[Dict]) -> Dict:
        """Determines the level for a given score."""
        score = round(score)
        for lvl in levels:
            if lvl['min'] <= score <= lvl['max']:
                return lvl
        return levels[0] if levels else {}

    @staticmethod
    def _escape_and_format_inline_markdown(text: str) -> str:
        """
        Convierte markdown inline básico a formato compatible con Paragraph.
        Soporta: **bold**, __bold__, `code`.
        """
        if not text:
            return ""

        safe = (
            text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
        safe = re.sub(r"__(.+?)__", r"<b>\1</b>", safe)
        safe = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", safe)
        return safe

    @staticmethod
    def _append_markdown_story(elements: List, markdown_text: str, styles):
        """
        Parsea markdown básico (títulos, viñetas, texto) y lo agrega al story.
        """
        h1_style = ParagraphStyle(
            "AIH1",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#0033A0"),
            spaceBefore=10,
            spaceAfter=8,
        )
        h2_style = ParagraphStyle(
            "AIH2",
            parent=styles["Heading2"],
            fontSize=15,
            textColor=colors.HexColor("#1d4ed8"),
            spaceBefore=8,
            spaceAfter=6,
        )
        h3_style = ParagraphStyle(
            "AIH3",
            parent=styles["Heading3"],
            fontSize=12,
            textColor=colors.HexColor("#334155"),
            spaceBefore=6,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "AIBody",
            parent=styles["Normal"],
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=6,
        )
        bullet_style = ParagraphStyle(
            "AIBullet",
            parent=body_style,
            leftIndent=14,
            firstLineIndent=-10,
            spaceAfter=4,
        )

        lines = (markdown_text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
        paragraph_buffer: List[str] = []

        def flush_paragraph():
            if not paragraph_buffer:
                return
            content = " ".join(paragraph_buffer).strip()
            paragraph_buffer.clear()
            if content:
                elements.append(Paragraph(PDFReportService._escape_and_format_inline_markdown(content), body_style))

        for raw_line in lines:
            line = raw_line.strip()

            if not line:
                flush_paragraph()
                continue

            if line.startswith("# "):
                flush_paragraph()
                elements.append(Paragraph(PDFReportService._escape_and_format_inline_markdown(line[2:].strip()), h1_style))
                continue

            if line.startswith("## "):
                flush_paragraph()
                elements.append(Paragraph(PDFReportService._escape_and_format_inline_markdown(line[3:].strip()), h2_style))
                continue

            if line.startswith("### "):
                flush_paragraph()
                elements.append(Paragraph(PDFReportService._escape_and_format_inline_markdown(line[4:].strip()), h3_style))
                continue

            bullet_match = re.match(r"^[-*]\s+(.+)$", line)
            if bullet_match:
                flush_paragraph()
                bullet = bullet_match.group(1).strip()
                elements.append(Paragraph(f"• {PDFReportService._escape_and_format_inline_markdown(bullet)}", bullet_style))
                continue

            numbered_match = re.match(r"^(\d+)\.\s+(.+)$", line)
            if numbered_match:
                flush_paragraph()
                number = numbered_match.group(1)
                text = numbered_match.group(2).strip()
                elements.append(Paragraph(f"{number}. {PDFReportService._escape_and_format_inline_markdown(text)}", bullet_style))
                continue

            paragraph_buffer.append(line)

        flush_paragraph()

    @staticmethod
    def generate_individual_report(buffer, student_data: Dict, result_data: Dict):
        doc = SimpleDocTemplate(buffer, pagesize=LETTER, topMargin=40, bottomMargin=40, rightMargin=40, leftMargin=40)
        elements = []
        styles = getSampleStyleSheet()
        
        # Colors
        ICFES_ORANGE = colors.HexColor("#FF6B00")
        ICFES_BLUE = colors.HexColor("#0033A0")
        SLATE_500 = colors.HexColor("#64748b")
        
        # --- Heading ---
        title = Paragraph("<b>Reporte Individual de Resultados</b>", 
                          ParagraphStyle('Title', parent=styles['Heading1'], alignment=0, fontSize=22, textColor=ICFES_BLUE, spaceAfter=2))
        subtitle = Paragraph(f"Simulacro Saber 11° - {result_data['area'].replace('_', ' ')}", 
                             ParagraphStyle('SubTitle', parent=styles['Heading2'], alignment=0, fontSize=14, textColor=SLATE_500))
        
        elements.append(title)
        elements.append(subtitle)
        elements.append(Spacer(1, 25))

        # --- Student Info Grid ---
        # 2 Columns: (Label: Value) (Label: Value)
        # Using a Paragraph within table to allow wrapping if needed, but simple string is usually fine here.
        info_style = ParagraphStyle('InfoVal', parent=styles['Normal'], fontSize=10, leading=12)
        label_style = ParagraphStyle('InfoLbl', parent=styles['Normal'], fontSize=10, textColor=SLATE_500, leading=12)

        data = [
            [Paragraph("Estudiante", label_style), Paragraph(f"<b>{student_data['nombre']}</b>", info_style),
             Paragraph("Documento", label_style), Paragraph(f"<b>{student_data['documento']}</b>", info_style)],
             
            [Paragraph("Institución", label_style), Paragraph(f"<b>{student_data['institucion']}</b>", info_style),
             Paragraph("Grupo", label_style), Paragraph(f"<b>{student_data['grupo'] or 'N/A'}</b>", info_style)],
             
            [Paragraph("Fecha", label_style), Paragraph(f"<b>{result_data['fecha']}</b>", info_style),
             Paragraph("Prueba", label_style), Paragraph(f"<b>{result_data['area'].replace('_', ' ')}</b>", info_style)]
        ]

        t_info = Table(data, colWidths=[70, 200, 70, 150])
        t_info.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
            ('LINEABOVE', (0,0), (-1,0), 1, colors.HexColor("#e2e8f0")),
        ]))
        elements.append(t_info)
        elements.append(Spacer(1, 30))

        # --- Score & Level Logic ---
        levels = PDFReportService._parse_markdown_levels(result_data['area'])
        current_level = PDFReportService._get_level_for_score(result_data['puntaje'], levels)
        
        # --- Results Visual Section (Side by Side) ---
        # Left: Score (Circle/Big Number). Right: Level Bar.
        
        # 1. Score Drawing
        score_drawing = Drawing(150, 100)
        # Circle
        # ReportLab shapes.Circle(x, y, r)
        from reportlab.graphics.shapes import Circle
        
        # Background light circle
        c_bg = Circle(75, 50, 45)
        c_bg.fillColor = colors.HexColor("#f8fafc")
        c_bg.strokeColor = ICFES_BLUE
        c_bg.strokeWidth = 2
        score_drawing.add(c_bg)
        
        # Text Score using String because Paragraph inside Drawing is tricky
        s_score = String(75, 55, f"{int(result_data['puntaje'])}", textAnchor='middle')
        s_score.fontName = 'Helvetica-Bold'
        s_score.fontSize = 28
        s_score.fillColor = ICFES_BLUE
        score_drawing.add(s_score)
        
        s_total = String(75, 35, "/ 100", textAnchor='middle')
        s_total.fontName = 'Helvetica'
        s_total.fontSize = 12
        s_total.fillColor = SLATE_500
        score_drawing.add(s_total)
        
        s_label = String(75, 10, "PUNTAJE", textAnchor='middle')
        s_label.fontSize = 8
        s_label.fillColor = SLATE_500
        score_drawing.add(s_label)
        
        # 2. Level Bar Drawing
        # We need a visual representation of 4 levels, highlighting the current one.
        # Layout:
        # [ 1 ] [ 2 ] [ 3 ] [ 4 ]
        #  0-35  36-50  ...
        
        bar_drawing = Drawing(350, 100)
        bar_w = 80
        bar_h = 40
        gap = 5
        start_x = 0
        current_lvl_num = current_level.get('level', 0)
        
        colors_map = {1: colors.HexColor("#ef4444"), 2: colors.HexColor("#f97316"), 3: colors.HexColor("#eab308"), 4: colors.HexColor("#22c55e")}

        for i in range(1, 5):
            x_pos = start_x + (i-1)*(bar_w + gap)
            is_active = (i == current_lvl_num)
            
            # The Box
            r = Rect(x_pos, 40, bar_w, bar_h, fill=1, stroke=0)
            base_color = colors_map.get(i, colors.grey)
            
            if is_active:
                r.fillColor = base_color
                # Add an indicator triangle or marker above?
                # Maybe just stronger color vs washout
            else:
                 # Washout manually
                r.fillColor = colors.Color(base_color.red, base_color.green, base_color.blue, alpha=0.15)
            
            bar_drawing.add(r)
            
            # Level Number Text
            s_num = String(x_pos + bar_w/2, 55, f"{i}", textAnchor='middle')
            s_num.fontName = 'Helvetica-Bold'
            s_num.fontSize = 16
            s_num.fillColor = colors.white if is_active else base_color
            bar_drawing.add(s_num)

            # Range Text below
            lvl_match = next((l for l in levels if l['level'] == i), None)
            range_str = f"{lvl_match['min']} - {lvl_match['max']}" if lvl_match else "?"
            
            s_range = String(x_pos + bar_w/2, 25, range_str, textAnchor='middle')
            s_range.fontSize = 10
            s_range.fillColor = colors.black
            bar_drawing.add(s_range)
            
            # "Nivel" Label
            if i == 1:
                s_lbl = String(x_pos + bar_w/2, 75, "Nivel de Desempeño", textAnchor='start')
                # Actually label is usually centered above the whole chart or per block.
                # Let's put a single label above the active one or just rely on the box number.
        
        # Indicator Text
        if current_lvl_num > 0:
            active_x = start_x + (current_lvl_num-1)*(bar_w + gap) + bar_w/2
            s_curr = String(active_x, 90, "TU NIVEL", textAnchor='middle')
            s_curr.fontSize = 8
            s_curr.fontName = 'Helvetica-Bold'
            s_curr.fillColor = colors.black
            bar_drawing.add(s_curr)

        # Place Score and Bar in a table to align them Side-by-Side
        result_table = Table([[score_drawing, bar_drawing]], colWidths=[150, 360])
        result_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (0,0), 'CENTER'),
            ('ALIGN', (1,0), (1,0), 'LEFT'),
        ]))
        
        elements.append(result_table)
        elements.append(Spacer(1, 20))

        # --- Evidence / Skills Section ---
        elements.append(Paragraph("¿Qué habilidades reflejan este nivel?", ParagraphStyle('H4', parent=styles['Heading4'], fontSize=12, textColor=ICFES_BLUE)))
        elements.append(Spacer(1, 10))
        
        skills = current_level.get('skills', [])
        if skills:
            for skill in skills:
                # Bullet styling
                # Use Table for bullet layout to ensure alignment of text
                # bullet_char = "•"
                p_text = Paragraph(skill, ParagraphStyle('Evidence', parent=styles['Normal'], fontSize=10, leading=14))
                
                # Simple list item
                elements.append(Paragraph(f"• {skill}", ParagraphStyle('Bullet', parent=styles['Normal'], leftIndent=15, firstLineIndent=-10, spaceAfter=6, leading=14)))
        else:
             elements.append(Paragraph("No hay descripción de evidencias disponible para este nivel en el marco de referencia.", styles['Normal']))

        # Footer
        elements.append(Spacer(1, 40))
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=1)
        elements.append(Paragraph("Reporte generado automáticamente por SIMIC", footer_style))
        elements.append(Paragraph(f"Fecha de impresión: {datetime.now().strftime('%Y-%m-%d %H:%M')}", footer_style))

        doc.build(elements)

    def generate_group_area_report(buffer, report_data: Dict):
        """
        Genera PDF para reporte grupal numérico por área (escala 0-100).
        """
        doc = SimpleDocTemplate(buffer, pagesize=LETTER, topMargin=40, bottomMargin=40, rightMargin=40, leftMargin=40)
        elements = []
        styles = getSampleStyleSheet()

        ICFES_BLUE = colors.HexColor("#0033A0")
        SLATE_500 = colors.HexColor("#64748b")

        inst_name = report_data.get('institution_name', 'N/A')
        students_count = report_data.get('students_count', 0)
        area_name = report_data.get('area_display') or (report_data.get('area', 'N/A').replace('_', ' ').title())
        avg_score = float(report_data.get('average_score_100', 0))
        min_score = report_data.get('min_score_100', 0)
        max_score = report_data.get('max_score_100', 0)
        performance_level = report_data.get('performance_level', 'N/A')
        performance_interval = report_data.get('performance_interval', 'N/A')
        students = report_data.get('students', [])
        generated_at = report_data.get('generated_at', datetime.now().strftime("%Y-%m-%d %H:%M"))
        progress = max(0.0, min(100.0, avg_score))

        info_style = ParagraphStyle('GroupInfoVal', parent=styles['Normal'], fontSize=11, leading=14)
        label_style = ParagraphStyle('GroupInfoLbl', parent=styles['Normal'], fontSize=11, textColor=SLATE_500, leading=14)
        section_title_style = ParagraphStyle('GroupSectionTitle', parent=styles['Heading2'], fontSize=18, textColor=ICFES_BLUE, alignment=1)

        header_data = [
            [Paragraph("Institución:", label_style), Paragraph(f"<b>{inst_name}</b>", info_style)],
            [Paragraph("Área:", label_style), Paragraph(f"<b>{area_name}</b>", info_style)],
            [Paragraph("Estudiantes finalizados:", label_style), Paragraph(f"<b>{students_count}</b>", info_style)],
            [Paragraph("Fecha de emisión:", label_style), Paragraph(f"<b>{generated_at}</b>", info_style)],
        ]

        t_header = Table(header_data, colWidths=[170, 350])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 44))

        elements.append(Paragraph("<b>Reporte general</b>", section_title_style))
        elements.append(Spacer(1, 20))

        drawing = Drawing(240, 220)
        drawing.hAlign = 'CENTER'
        from reportlab.graphics.shapes import Circle, Wedge

        cx, cy = 120, 110
        outer_r = 74
        inner_r = 55

        # Fondo del anillo
        ring_bg = Circle(cx, cy, outer_r)
        ring_bg.fillColor = colors.white
        ring_bg.strokeColor = colors.HexColor("#e2e8f0")
        ring_bg.strokeWidth = 12
        drawing.add(ring_bg)

        # Progreso circular tipo loader (0-100)
        theta = 360.0 * (progress / 100.0)
        if theta > 0:
            # Wedge en ReportLab dibuja en sentido antihorario entre start/end.
            # Esta combinación garantiza que se pinte exactamente "theta" grados.
            wedge = Wedge(cx, cy, outer_r, 90 - theta, 90)
            wedge.fillColor = ICFES_BLUE
            wedge.strokeColor = ICFES_BLUE
            drawing.add(wedge)

        # Hueco interno para efecto donut
        center_cut = Circle(cx, cy, inner_r)
        center_cut.fillColor = colors.white
        center_cut.strokeColor = colors.white
        drawing.add(center_cut)

        # Textos del centro
        s_score = String(cx, 120, f"{avg_score:.1f}", textAnchor='middle')
        s_score.fontName = 'Helvetica-Bold'
        s_score.fontSize = 32
        s_score.fillColor = ICFES_BLUE
        drawing.add(s_score)

        s_max = String(cx, 92, "/ 100", textAnchor='middle')
        s_max.fontName = 'Helvetica'
        s_max.fontSize = 13
        s_max.fillColor = SLATE_500
        drawing.add(s_max)

        s_level = String(cx, 72, f"{performance_level}", textAnchor='middle')
        s_level.fontName = 'Helvetica-Bold'
        s_level.fontSize = 10
        s_level.fillColor = colors.HexColor("#1d4ed8")
        drawing.add(s_level)

        # Separación extra para que la leyenda no quede pegada al anillo.
        s_label = String(cx, 200, "PROMEDIO GRUPAL", textAnchor='middle')
        s_label.fontName = 'Helvetica-Bold'
        s_label.fontSize = 12
        s_label.fillColor = ICFES_BLUE
        drawing.add(s_label)

        elements.append(drawing)
        elements.append(Spacer(1, 14))

        summary_data = [
            ["MÉTRICA", "VALOR"],
            ["Promedio grupal (área)", f"{avg_score}/100"],
            ["Nivel de desempeño (promedio)", f"{performance_level} ({performance_interval})"],
            ["Puntaje mínimo", f"{min_score}/100"],
            ["Puntaje máximo", f"{max_score}/100"],
        ]

        t_summary = Table(summary_data, colWidths=[320, 200])
        t_summary.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ICFES_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(t_summary)

        elements.append(Spacer(1, 26))

        elements.append(Paragraph("<b>Detalle por estudiante</b>", ParagraphStyle(
            'StudentDetailTitle',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=ICFES_BLUE
        )))
        elements.append(Spacer(1, 8))

        student_table_data = [["#", "ESTUDIANTE", "NOTA (N/100)"]]
        for idx, student in enumerate(students, start=1):
            nombre = student.get("name", f"Estudiante {idx}")
            nota = student.get("score_100", 0)
            student_table_data.append([str(idx), nombre, f"{nota}/100"])

        if len(student_table_data) == 1:
            student_table_data.append(["-", "Sin datos", "0/100"])

        t_students = Table(student_table_data, colWidths=[45, 345, 130], repeatRows=1)
        t_students.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), ICFES_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t_students)

        elements.append(Spacer(1, 20))
        footer_style = ParagraphStyle('GroupFooter', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=1)
        elements.append(Paragraph("Documento generado por SIMIC - Plataforma de Evaluación", footer_style))

        doc.build(elements)

    @staticmethod
    def generate_individual_ai_report(buffer, report_data: Dict):
        """
        Genera PDF del informe IA individual usando ReportLab (sin rasterizar HTML).
        """
        doc = SimpleDocTemplate(buffer, pagesize=LETTER, topMargin=40, bottomMargin=40, rightMargin=40, leftMargin=40)
        elements = []
        styles = getSampleStyleSheet()

        ICFES_BLUE = colors.HexColor("#0033A0")
        SLATE_500 = colors.HexColor("#64748b")
        BORDER = colors.HexColor("#e2e8f0")

        title = Paragraph(
            "<b>Informe de Análisis IA</b>",
            ParagraphStyle("AITitle", parent=styles["Heading1"], alignment=1, fontSize=22, textColor=ICFES_BLUE, spaceAfter=6)
        )
        subtitle = Paragraph(
            "Reporte Individual",
            ParagraphStyle("AISubTitle", parent=styles["Heading2"], alignment=1, fontSize=13, textColor=SLATE_500, spaceAfter=14)
        )
        elements.append(title)
        elements.append(subtitle)

        info_lbl = ParagraphStyle("AIInfoLbl", parent=styles["Normal"], fontSize=10, textColor=SLATE_500, leading=13)
        info_val = ParagraphStyle("AIInfoVal", parent=styles["Normal"], fontSize=10.5, textColor=colors.HexColor("#0f172a"), leading=13)

        info_data = [
            [Paragraph("Estudiante:", info_lbl), Paragraph(f"<b>{report_data.get('student_name', 'Estudiante')}</b>", info_val)],
            [Paragraph("Documento:", info_lbl), Paragraph(f"<b>{report_data.get('student_doc', 'N/A')}</b>", info_val)],
            [Paragraph("Institución:", info_lbl), Paragraph(f"<b>{report_data.get('institution_name', 'N/A')}</b>", info_val)],
            [Paragraph("Grupo:", info_lbl), Paragraph(f"<b>{report_data.get('group_name', 'N/A')}</b>", info_val)],
            [Paragraph("Simulacro:", info_lbl), Paragraph(f"<b>{report_data.get('simulacro_title', 'N/A')}</b>", info_val)],
            [Paragraph("Área:", info_lbl), Paragraph(f"<b>{report_data.get('area_display', 'N/A')}</b>", info_val)],
            [Paragraph("Puntaje:", info_lbl), Paragraph(f"<b>{report_data.get('score_100', 0)}/100</b>", info_val)],
            [Paragraph("Generado:", info_lbl), Paragraph(f"<b>{report_data.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M'))}</b>", info_val)],
        ]

        t_header = Table(info_data, colWidths=[110, 410])
        t_header.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, -1), 1, BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 18))

        elements.append(Paragraph(
            "<b>Contenido del informe</b>",
            ParagraphStyle("AIContentTitle", parent=styles["Heading3"], fontSize=14, textColor=ICFES_BLUE, spaceAfter=8)
        ))

        report_markdown = report_data.get("report_markdown") or "Contenido no disponible."
        PDFReportService._append_markdown_story(elements, report_markdown, styles)

        elements.append(Spacer(1, 18))
        footer_style = ParagraphStyle("AIFooter", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=1)
        elements.append(Paragraph("Documento generado por SIMIC - Plataforma de Evaluación", footer_style))

        doc.build(elements)
