import os
import asyncio
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

# Configuración de conexión (todo desde .env)
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "").replace(" ", ""),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    # Lógica inteligente: Si es puerto 465 usar SSL, si es 587 usar STARTTLS
    MAIL_STARTTLS=False if int(os.getenv("MAIL_PORT", 587)) == 465 else True,
    MAIL_SSL_TLS=True if int(os.getenv("MAIL_PORT", 587)) == 465 else False,
    # Configuración de timeouts y debug
    TIMEOUT=60,  # Aumentar timeout a 60 segundos
    MAIL_DEBUG=1,  # Activar debug logs SMTP
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


class EmailService:
    """Servicio para envío de emails transaccionales."""
    PRIMARY_COLOR = "#4f46e5"
    TEXT_COLOR = "#333333"
    FOOTER_COLOR = "#6b7280"
    SURFACE_COLOR = "#f9fafb"
    BORDER_COLOR = "#e5e7eb"

    @staticmethod
    async def send_email(
        subject: str,
        recipients: List[EmailStr],
        body: str,
        template_name: Optional[str] = None
    ):
        """
        Envía un correo electrónico.
        Si se usa un template, body puede ser un dict con el contexto.
        """
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            body=body,
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message)
        return True

    @staticmethod
    def _build_email_html(
        title: str,
        body_html: str,
        cta_label: Optional[str] = None,
        cta_href: Optional[str] = None
    ) -> str:
        """Plantilla base para correos transaccionales con tema unificado."""
        cta_html = ""
        if cta_label and cta_href:
            cta_html = f"""
                <div style="text-align: center;">
                    <a href="{cta_href}" class="button">{cta_label}</a>
                </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: {EmailService.TEXT_COLOR}; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {EmailService.PRIMARY_COLOR}; color: white; padding: 15px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ padding: 20px; border: 1px solid {EmailService.BORDER_COLOR}; border-top: none; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background-color: {EmailService.PRIMARY_COLOR}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .detail {{ background-color: {EmailService.SURFACE_COLOR}; padding: 14px 16px; border-radius: 8px; margin: 14px 0; }}
                ul {{ background-color: {EmailService.SURFACE_COLOR}; padding: 15px 30px; border-radius: 8px; }}
                li {{ margin-bottom: 5px; }}
                .footer {{ text-align: center; color: {EmailService.FOOTER_COLOR}; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{title}</h2>
                </div>
                <div class="content">
                    {body_html}
                    {cta_html}
                </div>
                <div class="footer">
                    <p>Este es un mensaje automático, por favor no responder.</p>
                    <p>© 2026 SIMIC. Todos los derechos reservados.</p>
                </div>
            </div>
        </body>
        </html>
        """


