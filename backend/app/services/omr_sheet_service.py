"""
Servicio para generar hojas de respuestas OMR (Optical Mark Recognition)
personalizadas para estudiantes.
"""
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
import qrcode
from datetime import datetime
from typing import List


class OMRSheetGenerator:
    """Generador de hojas de respuestas OMR para simulacros"""
    
    def __init__(self):
        self.page_width, self.page_height = letter
        self.margin = 15 * mm
        
        # Colores
        self.primary_color = HexColor('#6366f1')  # Indigo
        self.gray_color = HexColor('#64748b')
        self.light_gray = HexColor('#f1f5f9')
        
    def generate_sheets(self, simulacro, estudiantes: List) -> bytes:
        """
        Genera un PDF con una hoja OMR por estudiante
        
        Args:
            simulacro: Objeto Simulacro
            estudiantes: Lista de objetos Usuario (estudiantes)
        
        Returns:
            bytes: Contenido del PDF
        """
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        
        for estudiante in estudiantes:
            self._draw_sheet(c, simulacro, estudiante)
            c.showPage()
        
        c.save()
        buffer.seek(0)
        return buffer.read()
    
    def _draw_sheet(self, c, simulacro, estudiante):
        """Dibuja una hoja OMR individual"""
        
        # Header
        self._draw_header(c, simulacro)
        
        # Información del estudiante
        self._draw_student_info(c, simulacro, estudiante)
        
        # Grid de respuestas
        self._draw_answer_grid(c, simulacro.total_preguntas or 30)
        
        # Footer
        self._draw_footer(c)
        
    def _draw_header(self, c, simulacro):
        """Dibuja el header de la hoja"""
        y = self.page_height - 30 * mm
        
        # Barra superior indigo
        c.setFillColor(self.primary_color)
        c.rect(0, y, self.page_width, 12 * mm, fill=True, stroke=False)
        
        # Título
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(self.page_width / 2, y + 7 * mm, "SIMIC - HOJA DE RESPUESTAS")
        
        y -= 8 * mm
        
        # Información del simulacro
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(self.page_width / 2, y, simulacro.titulo)
        
        y -= 5 * mm
        
        # Área y detalles
        c.setFont("Helvetica", 9)
        area_labels = {
            'MATEMATICAS': 'Matemáticas',
            'LECTURA_CRITICA': 'Lectura Crítica',
            'CIENCIAS_NATURALES': 'Ciencias Naturales',
            'SOCIALES_CIUDADANAS': 'Sociales y Ciudadanas',
            'INGLES': 'Inglés'
        }
        area_text = area_labels.get(simulacro.area, simulacro.area if simulacro.area else 'General')
        total_preguntas = simulacro.total_preguntas or 30
        duracion = simulacro.duracion_minutos or 60
        detalles = f"{area_text} • {total_preguntas} preguntas • {duracion} minutos"
        c.drawCentredString(self.page_width / 2, y, detalles)
        
        y -= 5 * mm
        
        # Línea separadora
        c.setStrokeColor(self.gray_color)
        c.setLineWidth(0.5)
        c.line(self.margin, y, self.page_width - self.margin, y)
        
    def _draw_student_info(self, c, simulacro, estudiante):
        """Dibuja la sección de información del estudiante"""
        y = self.page_height - 60 * mm
        
        # Recuadro con fondo gris claro
        box_height = 25 * mm
        c.setFillColor(self.light_gray)
        c.rect(self.margin, y - box_height, self.page_width - (self.margin * 2), box_height, fill=True, stroke=False)
        
        # Borde izquierdo indigo
        c.setFillColor(self.primary_color)
        c.rect(self.margin, y - box_height, 3, box_height, fill=True, stroke=False)
        
        # Información del estudiante
        c.setFillColor(black)
        x_text = self.margin + 6 * mm
        y_text = y - 6 * mm
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_text, y_text, "ESTUDIANTE:")
        
        c.setFont("Helvetica", 10)
        nombre_completo = estudiante.nombre.upper()
        c.drawString(x_text + 28 * mm, y_text, nombre_completo)
        
        y_text -= 6 * mm
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_text, y_text, "Documento:")
        c.setFont("Helvetica", 9)
        c.drawString(x_text + 25 * mm, y_text, str(estudiante.numero_documento or 'N/A'))
        
        # Grupo (si existe)
        if estudiante.grupo:
            grupo_nombre = estudiante.grupo.nombre
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x_text + 70 * mm, y_text, "Grupo:")
            c.setFont("Helvetica", 9)
            c.drawString(x_text + 85 * mm, y_text, grupo_nombre)
        
        y_text -= 6 * mm
        
        # Fecha
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x_text, y_text, "Fecha:")
        c.setFont("Helvetica", 9)
        fecha_str = datetime.now().strftime("%d/%m/%Y")
        c.drawString(x_text + 15 * mm, y_text, fecha_str)
        
        # QR Code
        qr_data = f"SIM:{simulacro.id}|EST:{estudiante.id}|FECHA:{datetime.now().strftime('%Y%m%d')}"
        qr_img = self._generate_qr(qr_data)
        
        # Dibujar QR en la esquina derecha
        qr_x = self.page_width - self.margin - 22 * mm
        qr_y = y - box_height + 2 * mm
        c.drawInlineImage(qr_img, qr_x, qr_y, 20 * mm, 20 * mm)
        
    def _draw_answer_grid(self, c, num_preguntas: int):
        """Dibuja el grid de respuestas OMR"""
        y_start = self.page_height - 95 * mm
        
        # Título de instrucciones
        c.setFont("Helvetica-Bold", 9)
        c.drawString(self.margin, y_start, "INSTRUCCIONES: Marque con X o rellene completamente el círculo de su respuesta")
        
        y_start -= 8 * mm
        
        # Configuración del grid
        circle_radius = 3 * mm
        question_spacing = 8 * mm  # Espacio vertical entre preguntas
        option_spacing = 12 * mm   # Espacio horizontal entre opciones

        # Patrón requerido para optimizar uso de hoja:
        # - 10 preguntas: 1 columna de 10
        # - 20 preguntas: 2 columnas de 10
        # - 30 preguntas: 2 columnas de 15
        # Fallback para otros casos: 2 columnas balanceadas.
        if num_preguntas <= 10:
            columnas = 1
            preguntas_por_columna = 10
        elif num_preguntas <= 20:
            columnas = 2
            preguntas_por_columna = 10
        elif num_preguntas <= 30:
            columnas = 2
            preguntas_por_columna = 15
        else:
            columnas = 2
            preguntas_por_columna = (num_preguntas + 1) // 2

        x_col1 = self.margin + 5 * mm
        x_col2 = self.page_width / 2 + 10 * mm

        for i in range(num_preguntas):
            # Determinar columna y posición
            if columnas == 1 or i < preguntas_por_columna:
                x_base = x_col1
                y = y_start - (i * question_spacing)
            else:
                x_base = x_col2
                y = y_start - ((i - preguntas_por_columna) * question_spacing)
            
            # Número de pregunta
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x_base, y, f"{i + 1}.")
            
            # Opciones (A, B, C, D)
            opciones = ['A', 'B', 'C', 'D']
            for j, opcion in enumerate(opciones):
                x_option = x_base + 8 * mm + (j * option_spacing)
                
                # Círculo
                c.setStrokeColor(black)
                c.setLineWidth(0.5)
                c.circle(x_option, y + 1.5 * mm, circle_radius, fill=False, stroke=True)
                
                # Letra
                c.setFont("Helvetica", 8)
                c.drawCentredString(x_option, y + 0.5 * mm, opcion)
    
    def _draw_footer(self, c):
        """Dibuja el footer de la hoja"""
        y = 25 * mm
        
        # Línea separadora
        c.setStrokeColor(self.gray_color)
        c.setLineWidth(0.3)
        c.line(self.margin, y + 5 * mm, self.page_width - self.margin, y + 5 * mm)
        
        # Texto de instrucciones
        c.setFont("Helvetica", 7)
        c.setFillColor(self.gray_color)
        c.drawCentredString(self.page_width / 2, y, "No doble ni arrugue esta hoja • Use lápiz o bolígrafo negro • Marque solo una opción por pregunta")
        
        # Pequeño QR de verificación
        qr_data_footer = f"VERIFY:{datetime.now().strftime('%Y%m%d%H%M%S')}"
        qr_img_small = self._generate_qr(qr_data_footer, box_size=2)
        
        qr_x = self.margin
        qr_y = y - 8 * mm
        c.drawInlineImage(qr_img_small, qr_x, qr_y, 10 * mm, 10 * mm)
        
        c.setFont("Helvetica", 6)
        c.drawString(qr_x + 12 * mm, qr_y + 3 * mm, "QR de verificación")
    
    def _generate_qr(self, data: str, box_size: int = 5):
        """Genera un código QR y devuelve el objeto PIL Image"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=1,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Devolver el objeto PIL Image directamente
        img = qr.make_image(fill_color="black", back_color="white")
        
        return img
