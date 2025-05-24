import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.user import User
from schemas.user import UserCreate, UserLogin, UserOut

SECRET_KEY = "your-secret-key"  # Replace with a secure key in production
ALGORITHM = "HS256"

class UserService:
    def __init__(self):
        self.db = next(get_db())

    async def signup(self, user_data: UserCreate) -> UserOut:
        """
        Signup method.
        Accepts email and password, hashes the password, and returns a token.
        """
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash the password
        hashed_password = bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt()).decode()

        # Create new user
        new_user = User(email=user_data.email, hashed_password=hashed_password)
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        # Generate token
        token = self._create_token(new_user.id)

        return UserOut(id=new_user.id, email=new_user.email, token=token)

    async def login(self, user_data: UserLogin) -> UserOut:
        """
        Login method.
        Accepts email and password, verifies credentials, and returns a token.
        """
        user = self.db.query(User).filter(User.email == user_data.email).first()
        if not user or not bcrypt.checkpw(user_data.password.encode(), user.hashed_password.encode()):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = self._create_token(user.id)
        return UserOut(id=user.id, email=user.email, token=token)

    def _create_token(self, user_id: int) -> str:
        """
        Helper method to create a JWT token.
        """
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(days=1)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM) 