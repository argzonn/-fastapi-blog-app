from fastapi import HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.post import Post
from schemas.post import PostCreate, PostOut
from auth import get_current_user
from cache import cache
import bcrypt
import jwt
from datetime import datetime, timedelta
import sys

class PostService:
    """
    Handles post-related business logic, including creating, retrieving, and deleting posts.
    Interacts with the database and implements caching for retrieving posts.
    """
    def __init__(self):
        """
        Initializes the PostService with a database session.
        """
        # Get a new database session for each service instance
        try:
            self.db = next(get_db())
            print("Database session obtained successfully for PostService.", file=sys.stderr)
        except Exception as e:
            print(f"Error getting database session for PostService: {e}", file=sys.stderr)
            raise HTTPException(status_code=500, detail="Database connection error") from e

    async def add_post(self, post_data: PostCreate, token: str) -> PostOut:
        """
        Creates a new post for the authenticated user.

        Validates the post text size, creates the post in the database,
        and invalidates the cache for the user's posts.

        Args:
            post_data (PostCreate): The post data (text).
            token (str): The JWT token from the request header.

        Returns:
            PostOut: The created post's details.

        Raises:
            HTTPException: If the token is invalid (401), if the post content is too large (400),
                           or if there's an unexpected database error (500).
        """
        print("Attempting to add post...", file=sys.stderr)
        try:
            user_id = get_current_user(token)
            print(f"User ID from token: {user_id}", file=sys.stderr)

            # Optional: Add a check for payload size if needed
            if len(post_data.text) > 1000000: # Example size limit matching VARCHAR(1000000) or TEXT
                 raise HTTPException(status_code=400, detail="Post content too large")

            post = Post(user_id=user_id, text=post_data.text)
            print("Post object created.", file=sys.stderr)
            self.db.add(post)
            print("Post added to session. Committing...", file=sys.stderr)
            self.db.commit()
            print("Commit successful. Refreshing post object...", file=sys.stderr)
            self.db.refresh(post)
            print(f"Post object refreshed. Post ID: {post.id}", file=sys.stderr)

            # Invalidate cache for this user's posts after adding a new post
            cache_key = f"user_posts:{user_id}"
            if cache_key in cache:
                del cache[cache_key]
                print(f"Cache invalidated for user: {user_id}", file=sys.stderr)

            return PostOut.model_validate(post) # Use model_validate for Pydantic v2+

        except HTTPException as e:
            print(f"Caught HTTPException during add_post: {e.detail}", file=sys.stderr)
            self.db.rollback()
            raise e
        except Exception as e:
            print(f"Caught unexpected exception during add_post: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error during add_post") from e

    async def get_posts(self, token: str) -> list[PostOut]:
        """
        Retrieves all posts for the authenticated user.

        Checks the cache first, and if not found, fetches from the database,
        caches the result, and returns the posts.

        Args:
            token (str): The JWT token from the request header.

        Returns:
            list[PostOut]: A list of the user's posts, ordered by creation date (latest first).

        Raises:
            HTTPException: If the token is invalid (401),
                           or if there's an unexpected database or cache error (500).
        """
        print("Attempting to get posts...", file=sys.stderr)
        try:
            user_id = get_current_user(token)
            print(f"User ID from token for getting posts: {user_id}", file=sys.stderr)

            cache_key = f"user_posts:{user_id}"
            
            # Try to get posts from cache
            if cache_key in cache:
                post_list = cache[cache_key]
                print(f"Returning posts from cache for user: {user_id}", file=sys.stderr)
                return post_list

            print(f"Fetching posts from database for user: {user_id}", file=sys.stderr)
            # If not in cache, get posts from the database
            # Order by creation date descending
            posts = self.db.query(Post).filter(Post.user_id == user_id).order_by(Post.created_at.desc()).all()
            
            # Convert SQLAlchemy models to Pydantic models for caching and return
            post_list = [PostOut.model_validate(post) for post in posts]
            
            # Cache the result for 5 minutes (300 seconds)
            cache[cache_key] = post_list # Corrected: Use dictionary assignment
            print(f"Cached posts for user: {user_id}", file=sys.stderr)

            return post_list

        except HTTPException as e:
            print(f"Caught HTTPException during get_posts: {e.detail}", file=sys.stderr)
            self.db.rollback()
            raise e
        except Exception as e:
            print(f"Caught unexpected exception during get_posts: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error during get_posts") from e

    async def delete_post(self, post_id: int, token: str):
        """
        Deletes a post for the authenticated user.

        Deletes the post from the database and invalidates the cache
        for the user's posts.

        Args:
            post_id (int): The ID of the post to delete.
            token (str): The JWT token from the request header.

        Returns:
            dict: A confirmation message.

        Raises:
            HTTPException: If the token is invalid (401), if the post is not found
                           or doesn't belong to the user (404), or if there's an
                           unexpected database error (500).
        """
        print(f"Attempting to delete post with ID: {post_id}...", file=sys.stderr)
        try:
            user_id = get_current_user(token)
            print(f"User ID from token for deleting post: {user_id}", file=sys.stderr)

            post = self.db.query(Post).filter(Post.id == post_id, Post.user_id == user_id).first()
            if not post:
                print(f"Post with ID {post_id} not found for user {user_id}.", file=sys.stderr)
                raise HTTPException(status_code=404, detail="Post not found")

            self.db.delete(post)
            print(f"Post with ID {post_id} marked for deletion. Committing...", file=sys.stderr)
            self.db.commit()
            print("Commit successful.", file=sys.stderr)

            # Invalidate cache for this user's posts after deletion
            cache_key = f"user_posts:{user_id}"
            if cache_key in cache:
                del cache[cache_key]
                print(f"Cache invalidated for user: {user_id}", file=sys.stderr)

            return {"message": "Post deleted successfully"}

        except HTTPException as e:
            print(f"Caught HTTPException during delete_post: {e.detail}", file=sys.stderr)
            self.db.rollback()
            raise e
        except Exception as e:
            print(f"Caught unexpected exception during delete_post: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Internal Server Error during delete_post") from e 