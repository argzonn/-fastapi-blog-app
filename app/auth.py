import jwt
from fastapi import HTTPException

SECRET_KEY = "your-secret-key"  # Replace with a secure key in production
ALGORITHM = "HS256"

def get_current_user(token: str) -> int:
    """
    Decode and validate JWT token.
    Returns the user_id if valid, otherwise raises an HTTPException.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token") 