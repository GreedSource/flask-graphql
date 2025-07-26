import os
import threading
from flask_mail import Mail, Message
from flask import Flask, render_template
from typing import List, Optional

from server.decorators.singleton_decorator import singleton
from server.helpers.custom_graphql_exception_helper import CustomGraphQLExceptionHelper
from server.helpers.logger_helper import LoggerHelper


@singleton
class MailHelper:
    def __init__(self):
        self.app: Optional[Flask] = None
        self.mail: Optional[Mail] = None
        self._initialized = False

    def init_app(self, app: Flask):
        if self._initialized:
            return  # ya inicializado

        self.app = app

        self.app.config["MAIL_SERVER"] = os.environ.get(
            "MAIL_SERVER", "smtp.mailgun.org"
        )
        self.app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
        self.app.config["MAIL_USE_TLS"] = (
            os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
        )
        self.app.config["MAIL_USE_SSL"] = (
            os.environ.get("MAIL_USE_SSL", "false").lower() == "true"
        )
        self.app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
        self.app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
        self.app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")

        self.mail = Mail(self.app)
        LoggerHelper.info(f"{self.__class__.__name__} initialized")
        self._initialized = True

    def send_email(
        self,
        subject: str,
        recipients: List[str],
        body: Optional[str] = None,
        html_template: Optional[str] = None,
        context: Optional[dict] = None,
        sender: Optional[str] = None,
        async_send: bool = False,
    ) -> bool:
        if not self._initialized:
            raise CustomGraphQLExceptionHelper(
                "MailHelper no está inicializado. Llama a init_app(app) primero."
            )

        html = None
        if html_template:
            html = render_template(html_template, **(context or {}))

        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body or "",
            html=html,
            sender=sender or self.app.config.get("MAIL_DEFAULT_SENDER"),
        )

        try:
            if async_send:
                self.app.logger.info(
                    f"[MailHelper] Enviando email async a: {recipients} - Asunto: {subject}"
                )
                thread = threading.Thread(target=self._send_async, args=(msg,))
                thread.start()
                return True
            else:
                self.app.logger.info(
                    f"[MailHelper] Enviando email sync a: {recipients} - Asunto: {subject}"
                )
                return self._send(msg)
        except Exception as e:
            self.app.logger.error(f"[MailHelper] Error al enviar correo (enviar): {e}")
            return False

    def _send(self, msg) -> bool:
        try:
            self.mail.send(msg)
            self.app.logger.info(
                f"[MailHelper] Correo enviado correctamente a: {msg.recipients} - Asunto: {msg.subject}"
            )
            return True
        except Exception as e:
            self.app.logger.error(f"[MailHelper] Error al enviar correo (send): {e}")
            return False

    def _send_async(self, msg):
        with self.app.app_context():
            self._send(msg)
