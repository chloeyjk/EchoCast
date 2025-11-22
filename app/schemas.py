from pydantic import BaseModel
from typing import List, Optional

class PreferenceBase(BaseModel):
    topic: str

class PreferenceCreate(PreferenceBase):
    pass

class Preference(PreferenceBase):
    id: int
    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    preferences: List[Preference] = []
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
