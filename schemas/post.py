from pydantic import BaseModel
from datetime import datetime

# --- Post Schemas ---

class PostBase(BaseModel):
    """
    Base schema for post data.

    Contains common fields shared by other post schemas.
    """
    text: str # The content of the post

class PostCreate(PostBase):
    """
    Schema for creating a new post.

    Inherits from PostBase.
    """
    pass # No additional fields needed for creating a post beyond PostBase

class PostOut(PostBase):
    """
    Schema for the post data returned in responses.

    Includes the post ID, user ID, and creation timestamp.
    """
    id: int # Unique identifier for the post
    user_id: int # The ID of the user who created the post
    created_at: datetime # Timestamp indicating when the post was created

    class Config:
        # This setting tells Pydantic to read data from SQLAlchemy models
        # by attribute name (e.g., post.id) instead of just by key (e.g., {'id': ...})
        # from_attributes = True
        pass # Removed from_attributes for explicit dictionary validation 