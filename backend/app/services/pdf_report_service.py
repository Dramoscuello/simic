
import os
import re
from typing import Dict, List, Tuple
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart


class NumberedCanvas(canvas.Canvas):
    """
    Canvas personalizado de ReportLab para numeración de páginas en dos pasadas (Página X de Y).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        page_w = self._pagesize[0]
        self.line(36, 28, page_w - 36, 28)
        self.drawString(36, 16, "SIMIC - Sistema Modular de Evaluación ICFES Saber 11 | Informe Diagnóstico Grupal Oficial")
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(page_w - 36, 16, page_text)
        self.restoreState()


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
    def generate_global_batch_report(buffer, report_data: Dict):
        """
        Genera PDF para reporte global multi-área (batch) con tabla por estudiante.
        Columnas: #, Estudiante, Grupo, [Áreas], Puntaje Global.
        """
        doc = SimpleDocTemplate(buffer, pagesize=LETTER, topMargin=36, bottomMargin=36, rightMargin=28, leftMargin=28)
        elements = []
        styles = getSampleStyleSheet()

        VIOLET = colors.HexColor("#7c3aed")
        SLATE_500 = colors.HexColor("#64748b")

        inst_name = report_data.get('institution_name', 'N/A')
        batch_id = report_data.get('batch_id', 'N/A')
        students_count = report_data.get('total_estudiantes', 0)
        avg_global = report_data.get('promedio_global')
        areas_display = report_data.get('areas_display', {})
        areas_incluidas = report_data.get('areas_incluidas', [])
        areas_faltantes = report_data.get('areas_faltantes', [])
        promedios = report_data.get('promedios_por_area', {})
        students = report_data.get('estudiantes', [])
        generated_at = report_data.get('generated_at', datetime.now().strftime("%Y-%m-%d %H:%M"))
        formula = report_data.get('formula_global', '')

        info_style = ParagraphStyle('GBInfoVal', parent=styles['Normal'], fontSize=10, leading=13)
        label_style = ParagraphStyle('GBInfoLbl', parent=styles['Normal'], fontSize=10, textColor=SLATE_500, leading=13)
        title_style = ParagraphStyle('GBTitle', parent=styles['Heading1'], fontSize=20, textColor=VIOLET, alignment=1, spaceAfter=4)
        subtitle_style = ParagraphStyle('GBSubtitle', parent=styles['Normal'], fontSize=11, textColor=SLATE_500, alignment=1, spaceAfter=14)

        elements.append(Paragraph("<b>Diagnóstico Global Multi-área</b>", title_style))
        elements.append(Paragraph(f"Batch: {batch_id}", subtitle_style))

        header_data = [
            [Paragraph("Institución:", label_style), Paragraph(f"<b>{inst_name}</b>", info_style)],
            [Paragraph("Estudiantes finalizados:", label_style), Paragraph(f"<b>{students_count}</b>", info_style)],
            [Paragraph("Promedio global:", label_style), Paragraph(f"<b>{avg_global:.1f}/100</b>" if avg_global is not None else "<b>N/A</b>", info_style)],
            [Paragraph("Fecha de emisión:", label_style), Paragraph(f"<b>{generated_at}</b>", info_style)],
        ]

        t_header = Table(header_data, colWidths=[180, 300])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 10))

        if areas_faltantes:
            faltantes_str = ", ".join(areas_display.get(a, a) for a in areas_faltantes)
            elements.append(Paragraph(
                f"<font color='#f59e0b'>Áreas faltantes: {faltantes_str}</font>",
                ParagraphStyle('GBWarn', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor("#f59e0b"))
            ))
            elements.append(Spacer(1, 6))

        elements.append(Paragraph("<b>Detalle por estudiante</b>", ParagraphStyle(
            'GBStudentTitle', parent=styles['Heading3'], fontSize=13, textColor=VIOLET, spaceAfter=8
        )))

        area_short = {k: v[:6] for k, v in areas_display.items()}

        num_cols = 3 + len(areas_incluidas) + 1
        col_widths = [26, 156, 48] + [52] * len(areas_incluidas) + [58]
        student_header = ["#", "ESTUDIANTE", "GRUPO"] + [area_short.get(a, a[:6]) for a in areas_incluidas] + ["GLOBAL"]

        student_table_data = [student_header]
        for idx, student in enumerate(students, start=1):
            row = [str(idx), student.get("nombre", f"E-{idx}"), student.get("grupo", "-")]
            for area in areas_incluidas:
                val = student.get(area.lower())
                row.append(f"{val:.1f}" if val is not None else "-")
            global_val = student.get("puntaje_global")
            row.append(f"{global_val:.1f}" if global_val is not None else "-")
            student_table_data.append(row)

        avg_row = ["", "PROMEDIOS", ""]
        for area in areas_incluidas:
            display_name = areas_display.get(area, area)
            avg_val = promedios.get(display_name)
            avg_row.append(f"{avg_val:.1f}" if avg_val is not None else "-")
        avg_row.append(f"{avg_global:.1f}" if avg_global is not None else "-")
        student_table_data.append(avg_row)

        if len(student_table_data) == 2 and len(students) == 0:
            student_table_data.append(["-", "Sin datos", ""] + ["-"] * len(areas_incluidas) + ["-"])

        t_students = Table(student_table_data, colWidths=col_widths, repeatRows=1)
        header_style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), VIOLET),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
        ]
        highlight_last_col_cmds = [
            ('BACKGROUND', (num_cols - 1, 0), (num_cols - 1, 0), colors.HexColor("#6d28d9")),
        ]
        avg_row_idx = len(student_table_data) - 1
        avg_highlight_cmds = [
            ('BACKGROUND', (0, avg_row_idx), (-1, avg_row_idx), colors.HexColor("#f5f3ff")),
            ('FONTNAME', (0, avg_row_idx), (-1, avg_row_idx), 'Helvetica-Bold'),
            ('FONTSIZE', (0, avg_row_idx), (-1, avg_row_idx), 7),
        ]
        base_style = TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, avg_row_idx - 1 if avg_row_idx > 2 else -1), [colors.white, colors.HexColor("#f8fafc")]),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('FONTSIZE', (0, 1), (-1, avg_row_idx - 1 if avg_row_idx > 2 else -1), 7),
        ])
        t_students.setStyle(TableStyle(
            header_style_cmds + highlight_last_col_cmds + avg_highlight_cmds + [
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, avg_row_idx - 1 if avg_row_idx > 2 else -1), [colors.white, colors.HexColor("#f8fafc")]),
                ('PADDING', (0, 0), (-1, -1), 4),
                ('FONTSIZE', (0, 1), (-1, avg_row_idx - 1 if avg_row_idx > 2 else -1), 7),
            ]
        ))
        elements.append(t_students)

        if formula:
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                f"Fórmula puntaje global: {formula}",
                ParagraphStyle('GBFormula', parent=styles['Normal'], fontSize=7.5, textColor=SLATE_500, alignment=1)
            ))

        elements.append(Spacer(1, 16))
        footer_style = ParagraphStyle('GBFooter', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=1)
        elements.append(Paragraph("Documento generado por SIMIC - Plataforma de Evaluación", footer_style))

        doc.build(elements)

    @staticmethod
    def generate_individual_ai_report(buffer, report_data: Dict):
        """
        Genera un PDF profesional con ReportLab para el reporte individual de estudiante por área.
        Incluye NumberedCanvas (Página X de Y), encabezado institucional, tarjeta de resumen de puntaje,
        clasificación de desempeño y el informe pedagógico detallado.
        """
        doc = SimpleDocTemplate(
            buffer,
            pagesize=LETTER,
            topMargin=40,
            bottomMargin=50,
            rightMargin=40,
            leftMargin=40
        )
        elements = []
        styles = getSampleStyleSheet()

        NAVY = colors.HexColor("#0f172a")
        ICFES_BLUE = colors.HexColor("#0033A0")
        SLATE_500 = colors.HexColor("#64748b")
        SLATE_100 = colors.HexColor("#f1f5f9")
        BORDER = colors.HexColor("#cbd5e1")

        score = float(report_data.get('score_100', 0))

        if score >= 80:
            level_name = "AVANZADO / SUPERIOR"
            score_bg = colors.HexColor("#15803d")
        elif score >= 65:
            level_name = "SATISFACTORIO / ALTO"
            score_bg = colors.HexColor("#0284c7")
        elif score >= 45:
            level_name = "MÍNIMO / MEDIO"
            score_bg = colors.HexColor("#d97706")
        else:
            level_name = "INSUFICIENTE / BAJO"
            score_bg = colors.HexColor("#dc2626")

        title_p = Paragraph(
            f"<b>{report_data.get('institution_name', 'INSTITUCIÓN EDUCATIVA')}</b>",
            ParagraphStyle("IndInstTitle", parent=styles["Heading1"], alignment=1, fontSize=15, textColor=ICFES_BLUE, spaceAfter=2)
        )
        subtitle_p = Paragraph(
            "<b>INFORME INDIVIDUAL DE DESEMPEÑO POR ÁREA</b>",
            ParagraphStyle("IndSubtitle", parent=styles["Heading2"], alignment=1, fontSize=11, textColor=SLATE_500, spaceAfter=14)
        )
        elements.append(title_p)
        elements.append(subtitle_p)

        info_lbl = ParagraphStyle("AIInfoLbl", parent=styles["Normal"], fontSize=9, textColor=SLATE_500, leading=12)
        info_val = ParagraphStyle("AIInfoVal", parent=styles["Normal"], fontSize=9.5, textColor=NAVY, leading=12)
        score_num_style = ParagraphStyle("ScoreNum", parent=styles["Normal"], fontSize=24, textColor=colors.white, alignment=1, leading=26)
        score_lbl_style = ParagraphStyle("ScoreLbl", parent=styles["Normal"], fontSize=8, textColor=colors.white, alignment=1, leading=10)

        left_data = [
            [Paragraph("Estudiante:", info_lbl), Paragraph(f"<b>{report_data.get('student_name', 'Estudiante')}</b>", info_val)],
            [Paragraph("N° Documento:", info_lbl), Paragraph(f"<b>{report_data.get('student_doc', 'N/A')}</b>", info_val)],
            [Paragraph("Grupo / Sede:", info_lbl), Paragraph(f"<b>{report_data.get('group_name', 'N/A')}</b>", info_val)],
            [Paragraph("Prueba:", info_lbl), Paragraph(f"<b>{report_data.get('simulacro_title', 'N/A')}</b>", info_val)],
            [Paragraph("Área evaluada:", info_lbl), Paragraph(f"<b>{report_data.get('area_display', 'N/A')}</b>", info_val)],
            [Paragraph("Fecha evaluación:", info_lbl), Paragraph(f"<b>{report_data.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M'))}</b>", info_val)],
        ]
        t_left = Table(left_data, colWidths=[90, 260])
        t_left.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))

        score_cell = [
            Paragraph("<b>PUNTAJE</b>", score_lbl_style),
            Spacer(1, 3),
            Paragraph(f"<b>{score:.1f}</b>", score_num_style),
            Paragraph("<b>/ 100</b>", score_lbl_style),
            Spacer(1, 3),
            Paragraph(f"<b>{level_name}</b>", score_lbl_style),
        ]

        summary_table = Table([[t_left, score_cell]], colWidths=[360, 172])
        summary_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (0, 0), SLATE_100),
            ("BACKGROUND", (1, 0), (1, 0), score_bg),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ("BOX", (0, 0), (-1, -1), 1, BORDER),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 16))

        elements.append(Paragraph(
            "<b>DIAGNÓSTICO Y ANÁLISIS CUALITATIVO DE COMPETENCIAS</b>",
            ParagraphStyle("AIContentTitle", parent=styles["Heading3"], fontSize=11, textColor=ICFES_BLUE, spaceAfter=8)
        ))

        report_markdown = report_data.get("report_markdown") or "Informe pedagógico registrado."
        PDFReportService._append_markdown_story(elements, report_markdown, styles)

        doc.build(elements, canvasmaker=NumberedCanvas)

    @staticmethod
    def generate_grupal_batch_pdf(buffer, report_data: Dict):
        """
        Genera un PDF profesional con ReportLab para el diagnóstico grupal por lote (5 áreas).
        Incluye encabezado con nombre de la institución, tabla de promedios por área,
        y tabla detallada de estudiantes con documento, nombre, puntajes individuales y global (0-500).
        """
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(LETTER),
            topMargin=36,
            bottomMargin=36,
            rightMargin=36,
            leftMargin=36
        )
        elements = []
        styles = getSampleStyleSheet()

        NAVY = colors.HexColor("#0F172A")
        BLUE = colors.HexColor("#0033A0")
        INDIGO = colors.HexColor("#4F46E5")
        SLATE_500 = colors.HexColor("#64748B")
        BORDER_COLOR = colors.HexColor("#E2E8F0")

        inst_name = report_data.get('institution_name', 'Institución Educativa')
        batch_id = report_data.get('batch_id', 'N/A')
        titulo_base = report_data.get('titulo_base', 'Simulacro Diagnóstico')
        total_estudiantes = report_data.get('total_estudiantes', 0)
        avg_global_500 = report_data.get('promedio_global_500', 0.0)
        promedios = report_data.get('promedios_por_area', {})
        estudiantes = report_data.get('estudiantes', [])
        generated_at = report_data.get('generated_at', datetime.now().strftime("%Y-%m-%d %H:%M"))

        # Encabezado Institucional
        title_style = ParagraphStyle('GBInstTitle', parent=styles['Heading1'], fontSize=18, textColor=NAVY, spaceAfter=2)
        subtitle_style = ParagraphStyle('GBSub', parent=styles['Normal'], fontSize=11, textColor=INDIGO, spaceAfter=2)
        batch_title_style = ParagraphStyle('GBBatchTitle', parent=styles['Normal'], fontSize=10, textColor=SLATE_500, spaceAfter=10)

        elements.append(Paragraph(f"<b>{inst_name.upper()}</b>", title_style))
        elements.append(Paragraph("<b>DIAGNÓSTICO GRUPAL CONSOLIDADO DE ESTUDIANTES - EVALUACIÓN SABER 11</b>", subtitle_style))
        elements.append(Paragraph(f"Examen / Lote: <b>{titulo_base}</b> (Código: {batch_id})", batch_title_style))

        # Tarjeta de KPIs / Resumen Estadístico
        info_label_style = ParagraphStyle('GBMetaLbl', parent=styles['Normal'], fontSize=8.5, textColor=SLATE_500)
        info_val_style = ParagraphStyle('GBMetaVal', parent=styles['Normal'], fontSize=9.5, textColor=NAVY)

        meta_data = [
            [
                Paragraph("Estudiantes con 5 áreas:", info_label_style),
                Paragraph(f"<b>{total_estudiantes}</b>", info_val_style),
                Paragraph("Promedio Global Institucional:", info_label_style),
                Paragraph(f"<b>{avg_global_500:.1f} / 500</b>", info_val_style),
                Paragraph("Fecha de Emisión:", info_label_style),
                Paragraph(f"<b>{generated_at}</b>", info_val_style),
            ]
        ]
        t_meta = Table(meta_data, colWidths=[110, 60, 150, 90, 110, 100])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
            ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t_meta)
        elements.append(Spacer(1, 10))

        # Tabla de Promedios por Área
        area_names = ["Lectura Crítica", "Matemáticas", "Ciencias Naturales", "Sociales y C.", "Inglés"]
        avg_headers = [Paragraph(f"<b>{an}</b>", ParagraphStyle('AH', parent=styles['Normal'], fontSize=8, textColor=colors.white, alignment=1)) for an in area_names]
        avg_values = [Paragraph(f"<b>{promedios.get(an, 0.0):.1f} pts</b>", ParagraphStyle('AV', parent=styles['Normal'], fontSize=9, textColor=NAVY, alignment=1)) for an in area_names]

        avg_table_data = [
            [Paragraph("<b>Promedio por Área (0-100)</b>", ParagraphStyle('ATH', parent=styles['Normal'], fontSize=8.5, textColor=colors.white))] + avg_headers,
            [Paragraph("Puntaje medio:", info_label_style)] + avg_values
        ]
        t_avg = Table(avg_table_data, colWidths=[170, 110, 110, 110, 110, 110])
        t_avg.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BLUE),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#F1F5F9")),
            ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(t_avg)
        elements.append(Spacer(1, 14))

        # Título de Sección
        elements.append(Paragraph(
            "<b>Tabla de Resultados de Estudiantes (5 Áreas Completadas)</b>",
            ParagraphStyle('STitle', parent=styles['Heading2'], fontSize=12, textColor=NAVY, spaceAfter=6)
        ))

        # Tabla de Estudiantes
        th_style = ParagraphStyle('THS', parent=styles['Normal'], fontSize=8, textColor=colors.white, alignment=1)
        th_left = ParagraphStyle('THL', parent=styles['Normal'], fontSize=8, textColor=colors.white, alignment=0)
        td_style = ParagraphStyle('TDS', parent=styles['Normal'], fontSize=8, textColor=NAVY, alignment=1)
        td_left = ParagraphStyle('TDL', parent=styles['Normal'], fontSize=8, textColor=NAVY, alignment=0)
        td_bold = ParagraphStyle('TDB', parent=styles['Normal'], fontSize=8.5, textColor=BLUE, alignment=1)

        student_headers = [
            Paragraph("<b>#</b>", th_style),
            Paragraph("<b>N° Documento</b>", th_left),
            Paragraph("<b>Nombre del Estudiante</b>", th_left),
            Paragraph("<b>Lectura Crítica</b>", th_style),
            Paragraph("<b>Matemáticas</b>", th_style),
            Paragraph("<b>Ciencias Nat.</b>", th_style),
            Paragraph("<b>Sociales y C.</b>", th_style),
            Paragraph("<b>Inglés</b>", th_style),
            Paragraph("<b>Puntaje Global</b>", th_style),
        ]

        table_rows = [student_headers]

        for idx, est in enumerate(estudiantes, start=1):
            row = [
                Paragraph(str(idx), td_style),
                Paragraph(str(est.get("numero_documento", "N/A")), td_left),
                Paragraph(str(est.get("nombre", "Estudiante")), td_left),
                Paragraph(f"{est.get('lectura_critica', 0.0):.1f}", td_style),
                Paragraph(f"{est.get('matematicas', 0.0):.1f}", td_style),
                Paragraph(f"{est.get('ciencias_naturales', 0.0):.1f}", td_style),
                Paragraph(f"{est.get('sociales_ciudadanas', 0.0):.1f}", td_style),
                Paragraph(f"{est.get('ingles', 0.0):.1f}", td_style),
                Paragraph(f"<b>{est.get('puntaje_total', 0.0):.1f} / 500</b>", td_bold),
            ]
            table_rows.append(row)

        if len(estudiantes) == 0:
            empty_row = [Paragraph("-", td_style), Paragraph("N/A", td_left), Paragraph("No hay estudiantes con las 5 áreas completadas", td_left)] + [Paragraph("-", td_style)] * 6
            table_rows.append(empty_row)

        # Col widths total = 720 pt (Landscape letter = 792 - 72 pt margins)
        t_students = Table(table_rows, colWidths=[25, 80, 215, 65, 65, 65, 65, 60, 80], repeatRows=1)
        t_students.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ('PADDING', (0, 0), (-1, -1), 4.5),
        ]))
        elements.append(t_students)

        doc.build(elements, canvasmaker=NumberedCanvas)
