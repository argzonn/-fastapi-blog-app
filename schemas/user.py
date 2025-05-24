from pydantic import BaseModel, EmailStr

# --- User Schemas ---

class UserBase(BaseModel):
    """
    Base schema for user data.

    Contains common fields shared by other user schemas.
    """
    email: EmailStr # User's email address (validated as an email format)

class UserCreate(UserBase):
    """
    Schema for creating a new user.

    Includes the password field required for signup.
    """
    password: str # User's password

class UserLogin(UserBase):
    """
    Schema for user login.

    Includes the password field for authentication.
    """
    password: str # User's password

class UserOut(UserBase):
    """
    Schema for the user data returned in responses.

    Includes the user ID and a JWT token.
    """
    id: int # Unique identifier for the user
    token: str # JWT token for authentication

    # Pydantic's configuration class
    # We removed from_attributes = True as we are explicitly creating the return dictionary/model instance

    # class Config:
    #     from_attributes = True # Removed this line 