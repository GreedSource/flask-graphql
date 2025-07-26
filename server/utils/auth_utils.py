from typing import Any, Dict
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone

from server.enums.http_error_code_enum import HTTPErrorCode
from server.helpers.custom_graphql_exception_helper import CustomGraphQLExceptionHelper

SECRET_KEY = "your-secret"
REFRESH_SECRET_KEY = "your-refresh-secret"


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(payload: dict, expires_in: int = 15) -> str:
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expires_in)
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")


def create_refresh_token(payload: dict, expires_in: int = 60 * 24 * 7) -> str:
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expires_in)
    return jwt.encode(data, REFRESH_SECRET_KEY, algorithm="HS256")


def verify_refresh_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, REFRESH_SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise CustomGraphQLExceptionHelper("Refresh token expirado")
    except jwt.InvalidTokenError:
        raise CustomGraphQLExceptionHelper("Refresh token inválido")


def verify_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise CustomGraphQLExceptionHelper(
            "Access token expirado", HTTPErrorCode.UNAUTHORIZED
        )
    except jwt.InvalidTokenError:
        raise CustomGraphQLExceptionHelper(
            "Access token inválido", HTTPErrorCode.UNAUTHORIZED
        )
