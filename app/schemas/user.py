from pydantic import BaseModel, EmailStr, constr

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: constr(min_length=8)

class UserLogin(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    token: str

    class Config:
        orm_mode = True 