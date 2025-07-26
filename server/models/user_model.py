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
    name: str = Field(..., description="User name", min_length=3)
    lastname: str = Field(..., description="User lastname", min_length=3)
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="Password")
    confirm_password: str = Field(..., description="Password confirmation")

    @model_validator(mode="before")
    @classmethod
    def trim_all_str_fields(cls, values: dict) -> dict:
        return {k: v.strip() if isinstance(v, str) else v for k, v in values.items()}

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
    name: str = Field(..., description="User name", min_length=3)
    lastname: str = Field(..., description="User lastname", min_length=3)
    email: EmailStr | None = Field(None, description="User email")
    isAdmin: bool | None = Field(None, description="Is user admin")
