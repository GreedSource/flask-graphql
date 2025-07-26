import os
from ariadne import QueryType, MutationType
from bson import ObjectId
from flask import g, url_for
from itsdangerous import URLSafeTimedSerializer
from pymongo import ASCENDING

from server.decorators.require_token_decorator import require_token
from server.helpers.custom_graphql_exception_helper import CustomGraphQLExceptionHelper
from server.helpers.logger_helper import LoggerHelper
from server.helpers.mail_helper import MailHelper
from server.utils.auth_utils import (
    verify_password,
    create_token,
    create_refresh_token,
    verify_refresh_token,
)
from server.models.user_model import RegisterModel
from server.helpers.mongo_helper import MongoHelper


class AuthResolver:
    def __init__(self):
        self.__query = QueryType()
        self.__mutation = MutationType()
        self.__mongo_helper = MongoHelper(allowed_collections=["users"])
        self.mail_helper = MailHelper()
        self._create_indexes()
        self._bind_mutations()
        self._bind_queries()
        self.serializer = URLSafeTimedSerializer(os.getenv("SECRET_KEY", "SECRET_KEY"))
        LoggerHelper.info(f"{self.__class__.__name__} initialed")

    def _bind_queries(self):
        self.__query.set_field("profile", self.resolve_profile)

    def _bind_mutations(self):
        self.__mutation.set_field("register", self.resolve_register)
        self.__mutation.set_field("login", self.resolve_login)
        self.__mutation.set_field("refreshToken", self.resolve_refresh_token)
        self.__mutation.set_field("recoverPassword", self.resolve_recover_password)

    def _create_indexes(self):
        self.__mongo_helper.create_index(
            "users", [("email", ASCENDING)], name="UQ_EMAIL_IDX", unique=True
        )

    def user_to_dict(self, user):
        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "lastname": user["lastname"],
            "email": user["email"],
            "isAdmin": user.get("isAdmin", False),
        }

    def resolve_register(self, _, info, input):
        model = RegisterModel(**input)
        user_data = model.model_dump()
        inserted_id = self.__mongo_helper.insert_one("users", user_data)
        user_data["_id"] = inserted_id

        access_token = create_token({"id": str(user_data["_id"])})
        refresh_token = create_refresh_token({"id": str(user_data["_id"])})

        return {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "user": self.user_to_dict(user_data),
        }

    def resolve_login(self, _, info, input):
        user = self.__mongo_helper.find_one("users", {"email": input["email"]})
        if not user or not verify_password(input["password"], user["password"]):
            raise CustomGraphQLExceptionHelper("Credenciales inválidas")

        access_token = create_token({"id": str(user["_id"])})
        refresh_token = create_refresh_token({"id": str(user["_id"])})

        return {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "user": self.user_to_dict(user),
        }

    @require_token
    def resolve_profile(self, _, info):
        return self.user_to_dict(g.current_user)

    def resolve_refresh_token(self, _, info, refreshToken):
        LoggerHelper.info("Refrescando token...")
        payload = verify_refresh_token(refreshToken)
        user = self.__mongo_helper.find_one("users", {"_id": ObjectId(payload["id"])})
        if not user:
            raise CustomGraphQLExceptionHelper("Usuario no encontrado")

        new_access_token = create_token({"id": str(user["_id"])})
        return {"accessToken": new_access_token}

    def resolve_recover_password(self, _, info, email):
        user = self.__mongo_helper.find_one("users", {"email": email})
        if not user:
            LoggerHelper.info("Usuario no encontrado...")
            return False  # O lanzar error personalizado
        # Generar token que expire en 1 hora (3600 seg)
        token = self.serializer.dumps(email, salt="recover-password")

        # # Crear URL de recuperación (ajustar URL frontend/backend)
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        reset_url = f"{frontend_url}/reset-password/{token}"
        # # Enviar correo (async o sync)
        subject = "Recupera tu contraseña"
        recipients = [email]
        html_template = (
            "emails/reset_password.html"  # plantilla jinja2 con {{ reset_url }}
        )

        sent = self.mail_helper.send_email(
            subject=subject,
            recipients=recipients,
            html_template=html_template,
            context={"reset_url": reset_url},
            async_send=True,
        )

        return sent

    def get_resolvers(self):
        return [self.__query, self.__mutation]
