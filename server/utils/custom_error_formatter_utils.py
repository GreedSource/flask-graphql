from ariadne import format_error as default_format_error
from graphql import GraphQLError
from pydantic import ValidationError

from server.helpers.custom_graphql_exception_helper import CustomGraphQLExceptionHelper


def custom_format_error(error: GraphQLError, debug: bool = False):
    if isinstance(error.original_error, ValidationError):
        return {
            "message": "Error de validación",
            "extensions": {
                "code": "BAD_USER_INPUT",
                "fields": error.original_error.errors(),
            },
        }

    if isinstance(error.original_error, CustomGraphQLExceptionHelper):
        return {
            "message": error.original_error.message,
            "extensions": {
                "code": error.original_error.code,
                "details": error.original_error.details,
            },
        }
    return default_format_error(error, debug)
