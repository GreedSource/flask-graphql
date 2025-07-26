from enum import Enum


class HTTPErrorCode(Enum):
    BAD_REQUEST = (400, "BAD_REQUEST")
    UNAUTHORIZED = (401, "UNAUTHORIZED")
    FORBIDDEN = (403, "FORBIDDEN")
    NOT_FOUND = (404, "NOT_FOUND")
    METHOD_NOT_ALLOWED = (405, "METHOD_NOT_ALLOWED")
    CONFLICT = (409, "CONFLICT")
    INTERNAL_SERVER_ERROR = (500, "INTERNAL_SERVER_ERROR")
    SERVICE_UNAVAILABLE = (503, "SERVICE_UNAVAILABLE")

    def __init__(self, status_code, code_name):
        self.status_code = status_code
        self.code_name = code_name
