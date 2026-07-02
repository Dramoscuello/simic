"""
Servicio unificado para generar cuadernillos PDF de simulacros con calidad profesional.
Soporte para: formulación matemática (LaTeX), columnas estilo examen, y marcas de agua.
"""

import io
import re
from typing import List, Optional, Tuple
from datetime import datetime

# ReportLab libraries
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import cm, mm, inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, 
    Table, TableStyle, PageBreak, Frame, PageTemplate, BaseDocTemplate
)
from reportlab.lib.utils import ImageReader

# LaTeX rendering
import matplotlib
matplotlib.use('Agg')  # Backend no interactivo
import matplotlib.pyplot as plt
from matplotlib import mathtext

# Modelos
from app.models.simulacro import Simulacro
from app.models.institucion import Institucion

class PDFGenerationService:
    """
    Generador de cuadernillos PDF para SIMIC.
    Utiliza un diseño de 2 columnas similar al examen real.
    """
    
    def __init__(self):
        self.width, self.height = letter
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Configura estilos personalizados para el cuadernillo"""
        # Estilo para el enunciado de la pregunta
        self.style_question = ParagraphStyle(
            'Question',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12,
            spaceBefore=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        )
        
        # Estilo para las opciones de respuesta
        self.style_option = ParagraphStyle(
            'Option',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=11,
            leftIndent=15,
            spaceAfter=3,
            fontName='Helvetica'
        )
        
        # Estilo para contextos (textos largos de lectura)
        self.style_context = ParagraphStyle(
            'Context',
            parent=self.styles['Normal'],
            fontSize=9.5,
            leading=12,
            alignment=TA_JUSTIFY,
            borderPadding=5,
            borderColor=colors.HexColor('#e2e8f0'),
            borderWidth=1,
            backColor=colors.HexColor('#f8fafc'),
            spaceAfter=10,
            fontName='Helvetica-Oblique' # Italic para diferenciar
        )

        # Título de pregunta
        self.style_q_title = ParagraphStyle(
            'QTitle',
            parent=self.styles['Heading4'],
            fontSize=10,
            fontName='Helvetica-Bold',
            spaceBefore=15,
            textColor=colors.HexColor('#1e293b')
        )

    def _render_latex_to_image(self, formula: str, fontsize: int = 12) -> io.BytesIO:
        """
        Convierte una cadena LaTeX en una imagen PNG en memoria usando Matplotlib.
        """
        buf = io.BytesIO()
        
        # Configurar matplotlib para renderizar solo la fórmula
        fig = plt.figure(figsize=(0.1, 0.1)) # Tamaño dummy, se ajusta luego
        text = fig.text(0, 0, f"${formula}$", fontsize=fontsize)
        
        # Calcular bbox
        renderer = fig.canvas.get_renderer()
        bbox = text.get_window_extent(renderer=renderer)
        
        # Ajustar tamaño de figura al texto
        bbox_display = bbox.transformed(fig.dpi_scale_trans.inverted())
        fig.set_size_inches(bbox_display.width, bbox_display.height)
        
        # Reposicionar texto
        text.set_position((0, 0))
        
        # Guardar
        plt.axis('off')
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.05, transparent=True, dpi=300)
        plt.close(fig)
        
        buf.seek(0)
        return buf

    def _process_text_with_latex(self, text: str) -> List:
        """
        Detecta segmentos LaTeX entre delimitadores (...) o $...$ y los convierte a imágenes.
        Retorna una lista de objetos Flowable (Paragraphs e Images).
        """
        # Nota: Por simplicidad inicial, si el texto contiene LaTeX complejo, 
        # lo dividimos. Si es inline simple, lo dejamos como texto por ahora 
        # o usamos tags XML de reportlab <sub/sup> si es posible.
        # Esta implementación asume bloques de fórmula separados para máxima calidad.
        
        # Regex robusto para detectar LaTeX:
        # 1. Bloques $$...$$
        # 2. Bloques \[...\]
        # 3. Inline \(...\)
        # 4. Inline $...$ (evitando \$ escapados y monedas tipo $500 o $ 500)
        latex_blocks = re.split(r'(\$\$.*?\$\$|\\\[.*?\\\]|\\\(.*?\\\)|(?<!\\)\$(?!\s?\d).*?(?<!\\)\$)', text, flags=re.DOTALL)
        
        flowables = []
        
        for block in latex_blocks:
            if not block.strip():
                continue
                
            # Verificar si es un bloque de fórmulas
            # El chequeo simple de startswith('$') fallaría con '$500' si el regex fuera malo, 
            # pero como el regex split mantiene los delimitadores en el match, 
            # un bloque de texto que era '$500' NO será separado como un grupo independiente que empiece por $, 
            # sino que será parte del texto "normal".
            # Sin embargo, 'latex_blocks' contiene tando los matches como lo que hay entre ellos.
            # Los matches de fórmula empezarán por su delimitador.
            
            is_latex = False
            if (block.startswith('$$') or block.startswith('\\[') or block.startswith('\\(')):
                is_latex = True
            elif block.startswith('$'):
                # Verificación extra para inline $. 
                # Si el regex funcionó bien, este bloque ES una fórmula.
                # Pero doble chequeamos que no sea moneda por seguridad visual (aunque el regex ya filtra)
                # Si el bloque es literalmente "$500", el regex split NO lo habría capturado como grupo.
                is_latex = True
            
            if is_latex:
                # Limpiar delimitadores
                formula = block
                for delim in ['$$', '\\[', '\\]', '\\(', '\\)', '$']:
                    formula = formula.replace(delim, '')
                formula = formula.strip()
                try:
                    img_buffer = self._render_latex_to_image(formula)
                    # Crear imagen ReportLab
                    img = RLImage(img_buffer)
                    # Ajustar escala (reducir el high DPI)
                    img.drawHeight = img.drawHeight * 0.25 
                    img.drawWidth = img.drawWidth * 0.25
                    flowables.append(img)
                except Exception as e:
                    # Fallback si falla renderizado: mostrar código
                    flowables.append(Paragraph(f"<i>[Fórmula: {formula}]</i>", self.style_option))
            else:
                # Texto normal (procesar saltos de línea)
                # Reemplazar **negrita** con <b>...</b>
                formatted = block.replace('\n', '<br/>')
                formatted = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', formatted)
                
                # FIX: Reemplazo de caracteres Unicode (súper/subíndices) por etiquetas ReportLab
                # Helvetica (fuente base) no soporta estos carácteres unicode, causando cuadros negros.
                subs_map = {
                    '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', 
                    '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
                    '₋': '-', '₊': '+'
                }
                supers_map = {
                    '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', 
                    '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9', 
                    '⁻': '-', '⁺': '+'
                }
                
                for char, replacement in subs_map.items():
                    formatted = formatted.replace(char, f'<sub>{replacement}</sub>')
                for char, replacement in supers_map.items():
                    formatted = formatted.replace(char, f'<sup>{replacement}</sup>')
                
                flowables.append(Paragraph(formatted, self.style_question))
                
        return flowables

    def _render_graphic(self, config: dict, graphic_type: str) -> List:
        """Renderiza tablas o gráficos estadísticos reales usando Matplotlib y SVG con svglib"""
        flowables = []
        
        if not config:
            return flowables

        # 1. TABLAS DE DATOS
        if graphic_type == 'tabla_datos' and 'columnas' in config and 'filas' in config:
            data = [config['columnas']] + config['filas']
            
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#94a3b8')),
            ])
            
            col_width = (self.width - 3*cm - 1*cm) / 2 - 4*mm
            num_cols = len(config['columnas'])
            if num_cols > 0:
                col_widths = [col_width / num_cols] * num_cols
                t = Table(data, colWidths=col_widths)
            else:
                t = Table(data)
                
            t.setStyle(table_style)
            t.hAlign = 'CENTER'
            
            flowables.append(Spacer(1, 4))
            flowables.append(t)
            flowables.append(Spacer(1, 8))
            
        # 2. GRÁFICOS ESTADÍSTICOS (ChartJS -> Matplotlib)
        elif graphic_type and ('chartjs' in graphic_type or 'bar' in graphic_type or 'pie' in graphic_type):
            try:
                c_type = config.get('type', graphic_type.replace('chartjs_', ''))
                c_data = config.get('data', config)
                labels = c_data.get('labels', [])
                datasets = c_data.get('datasets', [])
                
                if labels and datasets:
                    plt.clf()
                    fig, ax = plt.subplots(figsize=(4, 3))
                    
                    dataset = datasets[0]
                    values = dataset.get('data', [])
                    label = dataset.get('label', '')
                    bg_colors = dataset.get('backgroundColor', '#3b82f6')
                    
                    if 'bar' in c_type:
                        bars = ax.bar(labels, values, color=bg_colors if isinstance(bg_colors, (str, list)) else '#3b82f6')
                        if label: ax.set_title(label, fontsize=9)
                        if len(labels) > 3: plt.xticks(rotation=45, ha='right', fontsize=7)
                        else: plt.xticks(fontsize=8)
                            
                    elif 'pie' in c_type or 'doughnut' in c_type:
                        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 7})
                        ax.axis('equal') 
                        if label: plt.title(label, fontsize=9)
                            
                    elif 'line' in c_type:
                        ax.plot(labels, values, marker='o', linestyle='-', color='#3b82f6', linewidth=2)
                        ax.grid(True, linestyle='--', alpha=0.5)
                        if len(labels) > 4: plt.xticks(rotation=45, ha='right', fontsize=7)
                    
                    plt.tight_layout()
                    
                    img_buf = io.BytesIO()
                    plt.savefig(img_buf, format='png', dpi=150, bbox_inches='tight')
                    plt.close(fig)
                    img_buf.seek(0)
                    
                    img = RLImage(img_buf)
                    col_w_pts = (self.width - 3*cm - 1*cm) / 2
                    aspect = img.imageHeight / img.imageWidth
                    target_w = col_w_pts - 10
                    img.drawWidth = target_w
                    img.drawHeight = target_w * aspect
                    
                    flowables.append(Spacer(1, 5))
                    flowables.append(img)
                    flowables.append(Spacer(1, 5))
            except Exception as e:
                print(f"Error renderizando gráfico backend: {e}")
                flowables.append(Paragraph(f"<font size=7 color='red'>[Error gráfico: {str(e)}]</font>", self.style_option))
                
        # 3. SVGS ARTÍSTICOS (Geometría, etc)
        elif graphic_type == 'svg_artistico':
             try:
                from svglib.svglib import svg2rlg
                
                svg_code = config.get('svg_code', '')
                if svg_code:
                    # Fix namespace si falta (common issue)
                    if 'xmlns' not in svg_code:
                        svg_code = svg_code.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"')
                    
                    # FIX: Reemplazar unicode sub/sup por tspans SVG estándar para svglib
                    # "Cu²" -> "Cu<tspan baseline-shift='super' font-size='65%'>2</tspan>"
                    # Esto evita cuadros vacíos por falta de glifos en la fuente default
                    subs_map = {'₀':'0','₁':'1','₂':'2','₃':'3','₄':'4','₅':'5','₆':'6','₇':'7','₈':'8','₉':'9'}
                    supers_map = {'²':'2','³':'3','⁻':'-','⁺':'+'}
                    
                    for k, v in subs_map.items():
                        # Tamaño drásticamente reducido (5%) por feedback de usuario
                        svg_code = svg_code.replace(k, f'<tspan baseline-shift="sub" font-size="5%">{v}</tspan>')
                    for k, v in supers_map.items():
                        svg_code = svg_code.replace(k, f'<tspan baseline-shift="super" font-size="5%">{v}</tspan>')

                    svg_file = io.BytesIO(svg_code.encode('utf-8'))
                    drawing = svg2rlg(svg_file)
                    
                    if drawing:
                        # FIX: Sanitizar strokeDashArray (evitar ValueError: dash cycle should be larger than zero)
                        def sanitize_dash(node):
                            if hasattr(node, 'strokeDashArray') and node.strokeDashArray:
                                # ReportLab falla si hay ceros en el dash array
                                # Convertimos a lista por si es tupla
                                d_array = list(node.strokeDashArray) if isinstance(node.strokeDashArray, (list, tuple)) else []
                                if any(x <= 0 for x in d_array):
                                    node.strokeDashArray = None # Línea sólida
                            
                            if hasattr(node, 'contents'):
                                for child in node.contents:
                                    sanitize_dash(child)
                        
                        sanitize_dash(drawing)

                        # Escalar dibujo
                        col_w_pts = (self.width - 3*cm - 1*cm) / 2
                        target_w = col_w_pts - 10 # margen
                        
                        d_width = drawing.width
                        d_height = drawing.height
                        
                        scale_factor = target_w / d_width
                        drawing.scale(scale_factor, scale_factor)
                        
                        # Wrap en una caja de renderizado de reportlab
                        drawing.width = d_width * scale_factor
                        drawing.height = d_height * scale_factor
                        
                        flowables.append(Spacer(1, 5))
                        flowables.append(drawing)
                        flowables.append(Spacer(1, 5))
             except Exception as e:
                print(f"Error rendering SVG: {e}")
                # Fallback
                p = Paragraph(f"<font size=7 color='red'>[Error visual: {str(e)}]</font>", self.style_option)
                flowables.append(p)

        return flowables

    def generate_booklet(self, simulacro: Simulacro, institucion_nombre: str) -> bytes:
        """
        Genera el cuadernillo completo del simulacro.
        """
        buffer = io.BytesIO()
        
        # Configurar documento con márgenes estrechos para aprovechar espacio
        doc = BookletDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        
        # --- Portada ---
        self._add_cover(story, simulacro, institucion_nombre)
        story.append(PageBreak())
        
        # --- Contenido (Preguntas) ---
        # Parsear JSONB
        contenido = simulacro.contenido
        if not contenido:
            story.append(Paragraph("Error: Simulacro sin contenido.", self.styles['Normal']))
        else:
            # Obtener preguntas (Soporte Español/Inglés)
            questions = contenido.get('preguntas', contenido.get('questions', []))
            
            # Agrupar preguntas por contexto consecutivo
            grouped_questions = []
            if questions:
                # Normalizar helper
                def get_ctx(q): return q.get('contexto') or q.get('context')
                
                first_q = questions[0]
                current_group = {'context': get_ctx(first_q), 'questions': [first_q]}
                
                for q in questions[1:]:
                    ctx = get_ctx(q)
                    # Si el contexto es idéntico al actual (y no es None/vacio), agrupar
                    if ctx and ctx == current_group['context']:
                        current_group['questions'].append(q)
                    else:
                        # Contexto cambió o es nulo -> cerrar grupo anterior e iniciar uno nuevo
                        grouped_questions.append(current_group)
                        current_group = {'context': ctx, 'questions': [q]}
                grouped_questions.append(current_group)
            
            # Contador global de preguntas para numeración correcta
            global_idx = 1
            
            for group in grouped_questions:
                questions_in_group = group['questions']
                start_idx = global_idx
                end_idx = global_idx + len(questions_in_group) - 1
                context_text = group['context']
                
                # Renderizar Contexto (si existe)
                if context_text:
                    # Título del rango
                    if start_idx == end_idx:
                        range_text = f"LA PREGUNTA {start_idx}"
                    else:
                        range_text = f"LAS PREGUNTAS {start_idx} A {end_idx}"
                        
                    story.append(Paragraph(
                        f"<b>RESPONDA {range_text} DE ACUERDO CON EL SIGUIENTE TEXTO</b>", 
                        self.style_q_title
                    ))
                    story.append(Spacer(1, 5))
                    # Texto del contexto
                    context_flowables = self._process_text_with_latex(context_text)
                    # Aplicar estilo de contexto a los párrafos resultantes
                    for f in context_flowables:
                        if isinstance(f, Paragraph):
                            f.style = self.style_context
                    story.extend(context_flowables)
                    story.append(Spacer(1, 10))
                
                # Renderizar preguntas del grupo
                for q in questions_in_group:
                    
                    # Renderizar Gráfico (si existe y tiene configuración)
                    # Buscamos claves en español o inglés
                    tiene_grafico = q.get('tiene_grafico', False)
                    config_grafico = q.get('configuracion_grafico')
                    tipo_grafico = q.get('tipo_grafico')
                    
                    if tiene_grafico and config_grafico:
                        graphic_flowables = self._render_graphic(config_grafico, tipo_grafico)
                        story.extend(graphic_flowables)
                    
                    # Enunciado de la pregunta
                    # Procesar LaTeX en el enunciado si existe
                    statement_clean = q.get('enunciado') or q.get('statement') or q.get('pregunta') or ''
                    statement_flowables = self._process_text_with_latex(f"<b>{global_idx}.</b> {statement_clean}")
                    story.extend(statement_flowables)
                    
                    # Opciones
                    options = q.get('opciones') or q.get('options') or []
                    opts_list = []
                    
                    # Caso 1: Lista de objetos [{'id': 'A', 'texto': '...'}, ...] (Formato SIMIC estándar)
                    if isinstance(options, list):
                        for opt in options:
                            if isinstance(opt, dict):
                                # Intenta obtener id/literal y texto/val
                                oid = opt.get('id') or opt.get('literal') or '?'
                                otext = opt.get('texto') or opt.get('text') or opt.get('val') or ''
                                opts_list.append((oid, otext))
                            else:
                                # Lista de strings
                                opts_list.append((chr(65+len(opts_list)), str(opt)))
                                
                    # Caso 2: Dict {'A': 'texto', ...}
                    elif isinstance(options, dict):
                        opts_list = sorted(options.items())

                    for key, val in opts_list:
                        val_str = str(val)
                        # Sanitize unicode sub/superscripts for options
                        subs = {'₀':'0', '₁':'1', '₂':'2', '₃':'3', '₄':'4', '₅':'5', '₆':'6', '₇':'7', '₈':'8', '₉':'9'}
                        supers = {'²':'2', '³':'3', '⁻':'-', '⁺':'+'}
                        for k,v in subs.items(): val_str = val_str.replace(k, f'<sub>{v}</sub>')
                        for k,v in supers.items(): val_str = val_str.replace(k, f'<sup>{v}</sup>')
                        
                        opt_line = f"<b>{key}.</b> {val_str}"
                        if '$' in val_str or '\\' in val_str:
                             # Renderizado complejo
                            opt_flowables = self._process_text_with_latex(opt_line)
                            for f in opt_flowables:
                                if isinstance(f, Paragraph):
                                    f.style = self.style_option
                            story.extend(opt_flowables)
                        else:
                            # Renderizado simple
                            story.append(Paragraph(opt_line, self.style_option))
                    
                    story.append(Spacer(1, 12)) # Espacio entre preguntas
                    global_idx += 1
        
        # Construir
        doc.build(story)
        
        buffer.seek(0)
        return buffer.read()

    def _add_cover(self, story, simulacro, institucion):
        """Diseya la portada del cuadernillo"""
        
        # Logo o Título Institucional
        story.append(Paragraph(institucion.upper(), 
            ParagraphStyle('CoverInst', parent=self.styles['Heading1'], alignment=TA_CENTER, fontSize=24, spaceAfter=30)))
            
        story.append(Spacer(1, 4*cm))
        
        # Título Simulacro
        story.append(Paragraph("SIMULACRO DE PRUEBA", 
            ParagraphStyle('CoverSubtitle', parent=self.styles['Normal'], alignment=TA_CENTER, fontSize=16, fontName='Helvetica')))
        
        story.append(Paragraph(simulacro.titulo.upper(), 
            ParagraphStyle('CoverTitle', parent=self.styles['Heading1'], alignment=TA_CENTER, fontSize=28, leading=32, spaceBefore=10)))
            
        story.append(Spacer(1, 6*cm))
        
        # Detalles
        detalles = [
            f"ÁREA: {simulacro.area.replace('_', ' ').upper()}",
            f"FECHA DE GENERACIÓN: {datetime.now().strftime('%d/%m/%Y')}",
            "MATERIAL CONFIDENCIAL - PROHIBIDA SU REPRODUCCIÓN"
        ]
        
        for d in detalles:
            story.append(Paragraph(d, 
                ParagraphStyle('CoverDetails', parent=self.styles['Normal'], alignment=TA_CENTER, fontSize=12, spaceAfter=6)))


class BookletDocTemplate(BaseDocTemplate):
    """
    Template personalizado para soportar diseño de 2 columnas en las páginas de contenido,
    pero 1 columna en la portada.
    """
    def __init__(self, filename, **kw):
        super().__init__(filename, **kw)
        
        # Definir Frames
        
        # Frame de 1 columna (Portada)
        frame_cover = Frame(
            self.leftMargin, self.bottomMargin, 
            self.width, self.height, 
            id='frame_cover'
        )
        
        # Frames de 2 columnas (Contenido)
        column_gap = 1*cm
        column_width = (self.width - column_gap) / 2
        
        frame_col1 = Frame(
            self.leftMargin, self.bottomMargin,
            column_width, self.height,
            id='col1'
        )
        
        frame_col2 = Frame(
            self.leftMargin + column_width + column_gap, self.bottomMargin,
            column_width, self.height,
            id='col2'
        )
        
        # Templates
        self.addPageTemplates([
            PageTemplate(id='Cover', frames=[frame_cover]), # Primera página
            PageTemplate(id='Content', frames=[frame_col1, frame_col2], onPage=self._header_footer) # Siguientes
        ])
    
    def _header_footer(self, canvas, doc):
        """Dibuja encabezado y pie de página en cada hoja de contenido"""
        canvas.saveState()
        
        # Footer: Paginación
        canvas.setFont('Helvetica', 9)
        canvas.drawCentredString(letter[0]/2, 1.5*cm, f"Página {doc.page}")
        
        # Header: Marca de agua pequeña o línea
        canvas.setStrokeColor(colors.HexColor('#94a3b8'))
        canvas.line(1.5*cm, letter[1] - 1.5*cm, letter[0]-1.5*cm, letter[1] - 1.5*cm)
        canvas.setFont('Helvetica-Bold', 8)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawString(1.5*cm, letter[1] - 1.3*cm, "SIMIC - Simulacro Oficial")
        
        canvas.restoreState()
