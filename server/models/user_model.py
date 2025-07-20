import re
from pydantic import (
    BaseModel,
    Field,
    computed_field,
    field_validator,
    model_validator,
    EmailStr,
)

from server.helpers.custom_graphql_exception_helper import CustomGraphQLExceptionHelper
from server.utils.auth_utils import hash_password


class RegisterModel(BaseModel):
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="Password")
    confirm_password: str = Field(..., description="Password confirmation")

    @model_validator(mode="after")
    def check_password_match(self):
        if self.password != self.confirm_password:
            raise CustomGraphQLExceptionHelper("Password mismatch.")
        self.password = hash_password(self.password)
        del self.__dict__["confirm_password"]
        return self

    @field_validator("password", "confirm_password")
    def strong_password(cls, v):
        # Al menos 8 caracteres, una mayúscula, una minúscula, un número y un símbolo
        pattern = (
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        )
        if not re.match(pattern, v):
            raise CustomGraphQLExceptionHelper(
                "La contraseña debe tener al menos 8 caracteres, incluyendo una mayúscula, "
                "una minúscula, un número y un carácter especial (@$!%*?&)."
            )
        return v

    @computed_field
    @property
    def isAdmin(cls) -> bool:
        return True


class UpdateUserModel(BaseModel):
    username: str | None = Field(None, description="Username")
    email: EmailStr | None = Field(None, description="User email")
    isAdmin: bool | None = Field(None, description="Is user admin")

    @field_validator("username")
    def validate_username(cls, v):
        if v is None:
            return v
        if not re.match(r"^[a-zA-Z0-9_.-]{3,30}$", v):
            raise CustomGraphQLExceptionHelper(
                "El nombre de usuario debe tener entre 3 y 30 caracteres y solo puede contener letras, números, guiones bajos, puntos o guiones."
            )
        return v
