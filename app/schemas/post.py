from pydantic import BaseModel, constr
from datetime import datetime

class PostBase(BaseModel):
    text: constr(max_length=1000000)  # Limit to 1 MB

class PostCreate(PostBase):
    pass

class PostOut(PostBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True 