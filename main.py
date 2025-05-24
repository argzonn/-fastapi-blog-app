from fastapi import FastAPI, Depends, Header
from services.user_service import UserService
from services.post_service import PostService
from schemas.user import UserCreate, UserLogin, UserOut
from schemas.post import PostCreate, PostOut
from auth import get_current_user

# Create the FastAPI application instance
app = FastAPI()

# --- Dependency Injection Functions ---

# Dependency injection for UserService
def get_user_service() -> UserService:
    """
    Provides a UserService instance with a database session.
    This is used by FastAPI's dependency injection.
    """
    return UserService()

# Dependency injection for PostService
def get_post_service() -> PostService:
    """
    Provides a PostService instance with a database session.
    This is used by FastAPI's dependency injection.
    """
    return PostService()

# --- API Endpoints ---

@app.post("/signup", response_model=UserOut)
async def signup(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Handles user signup.

    Accepts user details (email and password), hashes the password,
    and creates a new user in the database.

    Returns:
        UserOut: The created user's ID, email, and a JWT token.

    Raises:
        HTTPException: If the email is already registered (400).
    """
    return await user_service.signup(user_data)

@app.post("/login", response_model=UserOut)
async def login(
    user_data: UserLogin,
    user_service: UserService = Depends(get_user_service)
):
    """
    Handles user login.

    Accepts user credentials (email and password) and verifies them
    against the database.

    Returns:
        UserOut: The logged-in user's ID, email, and a new JWT token upon successful authentication.

    Raises:
        HTTPException: If the credentials are invalid (401).
    """
    return await user_service.login(user_data)

@app.post("/posts", response_model=PostOut)
async def create_post(
    post_data: PostCreate,
    token: str = Header(...),
    post_service: PostService = Depends(get_post_service)
):
    """
    Creates a new post.

    Requires a valid JWT token in the 'token' header for authentication.
    Validates the post text payload size.
    Saves the post to the database.

    Args:
        post_data (PostCreate): The post data (text).
        token (str): The JWT token from the request header.
        post_service (PostService): Dependency injected PostService instance.

    Returns:
        PostOut: The created post's details.

    Raises:
        HTTPException: If the token is invalid/missing (401), or if the post content is too large (400).
    """
    return await post_service.add_post(post_data, token)

@app.get("/posts", response_model=list[PostOut])
async def get_posts(
    token: str = Header(...),
    post_service: PostService = Depends(get_post_service)
):
    """
    Retrieves all posts for the authenticated user.

    Requires a valid JWT token in the 'token' header for authentication.
    Uses in-memory caching for responses for up to 5 minutes per user.

    Args:
        token (str): The JWT token from the request header.
        post_service (PostService): Dependency injected PostService instance.

    Returns:
        list[PostOut]: A list of the user's posts, ordered by creation date (latest first).

    Raises:
        HTTPException: If the token is invalid/missing (401).
    """
    return await post_service.get_posts(token)

@app.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    token: str = Header(...),
    post_service: PostService = Depends(get_post_service)
):
    """
    Deletes a specific post for the authenticated user.

    Requires a valid JWT token in the 'token' header for authentication.

    Args:
        post_id (int): The ID of the post to delete.
        token (str): The JWT token from the request header.
        post_service (PostService): Dependency injected PostService instance.

    Returns:
        dict: A confirmation message.

    Raises:
        HTTPException: If the token is invalid/missing (401), or if the post is not found or doesn't belong to the user (404).
    """
    return await post_service.delete_post(post_id, token)
