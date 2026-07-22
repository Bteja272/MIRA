from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class RegisterRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=12,
        max_length=128,
    )

    @field_validator(
        "email",
        mode="before",
    )
    @classmethod
    def normalize_email(
        cls,
        value,
    ) -> str:
        return str(value).strip().lower()


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    user_id: str
    email: EmailStr
    is_active: bool
    created_at: datetime


class RegistrationResponse(BaseModel):
    user: UserResponse
    development_notice: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int