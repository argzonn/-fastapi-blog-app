from fastapi import FastAPI, Depends, HTTPException, Header
from typing import Optional
from services.user_service import UserService
from services.post_service import PostService
from schemas.user import UserCreate, UserLogin, UserOut
from schemas.post import PostCreate, PostOut
from auth import get_current_user

app = FastAPI()

# Dependency injection for user service
def get_user_service():
    return UserService()

# Dependency injection for post service
def get_post_service():
    return PostService()

@app.post("/signup", response_model=UserOut)
async def signup(user_data: UserCreate, user_service: UserService = Depends(get_user_service)):
    """
    Signup endpoint.
    Accepts email and password, returns a token.
    """
    return await user_service.signup(user_data)

@app.post("/login", response_model=UserOut)
async def login(user_data: UserLogin, user_service: UserService = Depends(get_user_service)):
    """
    Login endpoint.
    Accepts email and password, returns a token upon successful login.
    """
    return await user_service.login(user_data)

@app.post("/addpost", response_model=PostOut)
async def add_post(post_data: PostCreate, token: str = Header(...), post_service: PostService = Depends(get_post_service)):
    """
    AddPost endpoint.
    Accepts text and a token for authentication.
    Validates payload size (limit to 1 MB), saves the post, and returns postID.
    """
    return await post_service.add_post(post_data, token)

@app.get("/getposts", response_model=list[PostOut])
async def get_posts(token: str = Header(...), post_service: PostService = Depends(get_post_service)):
    """
    GetPosts endpoint.
    Requires a token for authentication.
    Returns all user's posts with caching for up to 5 minutes.
    """
    return await post_service.get_posts(token)

@app.delete("/deletepost/{post_id}")
async def delete_post(post_id: int, token: str = Header(...), post_service: PostService = Depends(get_post_service)):
    """
    DeletePost endpoint.
    Accepts postID and a token for authentication.
    Deletes the corresponding post.
    """
    return await post_service.delete_post(post_id, token) 