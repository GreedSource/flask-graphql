from functools import wraps
from flask import g, request
from server.enums.http_error_code_enum import HTTPErrorCode
from server.utils.auth_utils import verify_token
from server.helpers.custom_graphql_exception_helper import CustomGraphQLExceptionHelper
from server.helpers.mongo_helper import MongoHelper
from bson import ObjectId

mongo = MongoHelper(allowed_collections=["users"])


def require_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()
        if not token:
            raise CustomGraphQLExceptionHelper(
                "Token no proporcionado", HTTPErrorCode.UNAUTHORIZED
            )

        payload = verify_token(token)
        user_id = payload.get("id")
        user = mongo.find_one("users", {"_id": ObjectId(user_id)})
        if not user:
            raise CustomGraphQLExceptionHelper("Usuario no encontrado")
        g.current_user = user

        return func(*args, **kwargs)

    return wrapper
