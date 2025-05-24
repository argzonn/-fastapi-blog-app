from fastapi import HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.post import Post
from schemas.post import PostCreate, PostOut
from auth import get_current_user
from cache import cache

class PostService:
    def __init__(self):
        self.db = next(get_db())

    async def add_post(self, post_data: PostCreate, token: str) -> PostOut:
        """
        AddPost method.
        Accepts text and a token for authentication.
        Validates payload size (limit to 1 MB), saves the post, and returns postID.
        """
        user_id = get_current_user(token)
        new_post = Post(user_id=user_id, text=post_data.text)
        self.db.add(new_post)
        self.db.commit()
        self.db.refresh(new_post)
        return PostOut(id=new_post.id, user_id=new_post.user_id, text=new_post.text, created_at=new_post.created_at)

    async def get_posts(self, token: str) -> list[PostOut]:
        """
        GetPosts method.
        Requires a token for authentication.
        Returns all user's posts with caching for up to 5 minutes.
        """
        user_id = get_current_user(token)
        cache_key = f"posts_{user_id}"
        cached_posts = cache.get(cache_key)
        if cached_posts:
            return cached_posts

        posts = self.db.query(Post).filter(Post.user_id == user_id).all()
        post_list = [PostOut(id=post.id, user_id=post.user_id, text=post.text, created_at=post.created_at) for post in posts]
        cache.set(cache_key, post_list, 300)  # Cache for 5 minutes
        return post_list

    async def delete_post(self, post_id: int, token: str) -> dict:
        """
        DeletePost method.
        Accepts postID and a token for authentication.
        Deletes the corresponding post.
        """
        user_id = get_current_user(token)
        post = self.db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        self.db.delete(post)
        self.db.commit()
        return {"message": "Post deleted successfully"} 