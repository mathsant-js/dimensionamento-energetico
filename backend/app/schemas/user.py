from pydantic import BaseModel, Field
from typing import Optional

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5)
    hashed_password: str = Field(..., min_length=8)

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True