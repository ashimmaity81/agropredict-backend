from pydantic import BaseModel, EmailStr

class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: str
    password: str