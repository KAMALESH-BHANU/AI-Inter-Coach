from pydantic import BaseModel, EmailStr
from typing import List, Optional

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    skills: List[str] = []

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    full_name: str
    email: str

class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    skills: List[str]
