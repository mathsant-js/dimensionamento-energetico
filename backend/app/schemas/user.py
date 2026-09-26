from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserRead(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True