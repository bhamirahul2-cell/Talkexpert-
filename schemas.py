from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    role: str = "user"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ExpertIn(BaseModel):
    category: str = Field(min_length=2, max_length=80)
    bio: str = Field(default="", max_length=1000)
    credentials_note: str = Field(default="", max_length=500)

class BookingIn(BaseModel):
    expert_id: int
