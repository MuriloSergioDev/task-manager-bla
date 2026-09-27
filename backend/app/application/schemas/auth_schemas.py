from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    # Bounded even though a wrong-length password just fails auth anyway:
    # Argon2's hashing cost scales with input size, and this is the one
    # password field an unauthenticated caller can hit repeatedly.
    password: str = Field(min_length=1, max_length=128)
