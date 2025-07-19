class CustomGraphQLExceptionHelper(Exception):
    def __init__(self, message, code="BAD_REQUEST", details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self):
        return {
            "message": self.message,
            "extensions": {
                "code": self.code,
                "details": self.details,
            },
        }
