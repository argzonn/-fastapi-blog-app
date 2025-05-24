from fastapi import HTTPException
from sqlalchemy.orm import Session
# from db import get_db # Comment out database import
from models.post import Post
from schemas.post import PostCreate, PostOut
from auth import get_current_user
from cache import cache
import bcrypt
import jwt
from datetime import datetime, timedelta
import sys

# In-memory storage for posts and a counter for generating IDs
_in_memory_posts = []
_next_post_id = 1

class PostService:
    """
    Handles post-related business logic using in-memory storage.
    """
    # Remove or comment out database session initialization
    # def __init__(self):
    #     """
    #     Initializes the PostService with a database session.
    #     """
    #     # Get a new database session for each service instance
    #     try:
    #         self.db = next(get_db())
    #         print("Database session obtained successfully for PostService.", file=sys.stderr)
    #     except Exception as e:
    #         print(f"Error getting database session for PostService: {e}", file=sys.stderr)
    #         raise HTTPException(status_code=500, detail="Database connection error") from e
    
    # Simple __init__ for in-memory version
    def __init__(self):
        pass # No database session needed for in-memory storage

    async def add_post(self, post_data: PostCreate, token: str) -> PostOut:
        """
        Creates a new post for the authenticated user in memory.

        Validates the post text size and adds the post to in-memory storage.

        Args:
            post_data (PostCreate): The post data (text).
            token (str): The JWT token from the request header.

        Returns:
            PostOut: The created post's details.

        Raises:
            HTTPException: If the token is invalid (401), if the post content is too large (400).
        """
        print("Attempting to add post (in-memory)...", file=sys.stderr)
        global _next_post_id, _in_memory_posts
        try:
            user_id = get_current_user(token)
            print(f"User ID from token: {user_id}", file=sys.stderr)

            # Optional: Add a check for payload size if needed
            if len(post_data.text) > 1000000: # Example size limit matching VARCHAR(1000000) or TEXT
                 raise HTTPException(status_code=400, detail="Post content too large")

            # Create in-memory post object
            new_post = {
                "id": _next_post_id,
                "user_id": user_id,
                "text": post_data.text,
                "created_at": datetime.now()
            }
            _in_memory_posts.append(new_post)
            post_id = _next_post_id
            _next_post_id += 1
            
            print(f"Post added to in-memory storage. Post ID: {post_id}", file=sys.stderr)

            # Invalidate cache for this user's posts after adding a new post (if caching is still desired for in-memory)
            cache_key = f"user_posts:{user_id}"
            if cache_key in cache:
                del cache[cache_key]
                print(f"Cache invalidated for user: {user_id}", file=sys.stderr)

            # Return the created post details
            return PostOut(id=new_post["id"], user_id=new_post["user_id"], text=new_post["text"], created_at=new_post["created_at"])

        except HTTPException as e:
            print(f"Caught HTTPException during add_post (in-memory): {e.detail}", file=sys.stderr)
            raise e
        except Exception as e:
            print(f"Caught unexpected exception during add_post (in-memory): {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise HTTPException(status_code=500, detail="Internal Server Error during add_post") from e

    async def get_posts(self, token: str) -> list[PostOut]:
        """
        Retrieves all posts for the authenticated user from in-memory storage.

        Checks the cache first, and if not found, fetches from in-memory storage,
        caches the result, and returns the posts.

        Args:
            token (str): The JWT token from the request header.

        Returns:
            list[PostOut]: A list of the user's posts, ordered by creation date (latest first).

        Raises:
            HTTPException: If the token is invalid (401),
                           or if there's an unexpected error (500).
        """
        print("Attempting to get posts (in-memory)...", file=sys.stderr)
        try:
            user_id = get_current_user(token)
            print(f"User ID from token for getting posts: {user_id}", file=sys.stderr)

            cache_key = f"user_posts:{user_id}"
            
            # Try to get posts from cache
            if cache_key in cache:
                post_list = cache[cache_key]
                print(f"Returning posts from cache for user: {user_id}", file=sys.stderr)
                return post_list

            print(f"Fetching posts from in-memory storage for user: {user_id}", file=sys.stderr)
            # Filter posts from in-memory storage for the current user
            user_posts = [post for post in _in_memory_posts if post["user_id"] == user_id]
            
            # Order by creation date descending
            user_posts.sort(key=lambda x: x["created_at"], reverse=True)
            
            # Convert in-memory dicts to Pydantic models for caching and return
            post_list = [PostOut(id=post["id"], user_id=post["user_id"], text=post["text"], created_at=post["created_at"]) for post in user_posts]
            
            # Cache the result for 5 minutes (300 seconds)
            cache[cache_key] = post_list # Use dictionary assignment
            print(f"Cached posts for user: {user_id}", file=sys.stderr)

            return post_list

        except HTTPException as e:
            print(f"Caught HTTPException during get_posts (in-memory): {e.detail}", file=sys.stderr)
            raise e
        except Exception as e:
            print(f"Caught unexpected exception during get_posts (in-memory): {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise HTTPException(status_code=500, detail="Internal Server Error during get_posts") from e

    async def delete_post(self, post_id: int, token: str):
        """
        Deletes a post for the authenticated user from in-memory storage.

        Deletes the post from in-memory storage and invalidates the cache
        for the user's posts.

        Args:
            post_id (int): The ID of the post to delete.
            token (str): The JWT token from the request header.

        Returns:
            dict: A confirmation message.

        Raises:
            HTTPException: If the token is invalid (401), if the post is not found
                           or doesn't belong to the user (404).
        """
        print(f"Attempting to delete post with ID: {post_id} (in-memory)...", file=sys.stderr)
        global _in_memory_posts
        try:
            user_id = get_current_user(token)
            print(f"User ID from token for deleting post: {user_id}", file=sys.stderr)

            # Find the post in in-memory storage
            post_to_delete = None
            for i, post in enumerate(_in_memory_posts):
                if post["id"] == post_id and post["user_id"] == user_id:
                    post_to_delete = post
                    del _in_memory_posts[i]
                    break

            if not post_to_delete:
                print(f"Post with ID {post_id} not found for user {user_id} (in-memory).", file=sys.stderr)
                raise HTTPException(status_code=404, detail="Post not found")

            print(f"Post with ID {post_id} deleted from in-memory storage.", file=sys.stderr)

            # Invalidate cache for this user's posts after deletion
            cache_key = f"user_posts:{user_id}"
            if cache_key in cache:
                del cache[cache_key]
                print(f"Cache invalidated for user: {user_id}", file=sys.stderr)

            return {"message": "Post deleted successfully"}

        except HTTPException as e:
            print(f"Caught HTTPException during delete_post (in-memory): {e.detail}", file=sys.stderr)
            raise e
        except Exception as e:
            print(f"Caught unexpected exception during delete_post (in-memory): {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise HTTPException(status_code=500, detail="Internal Server Error during delete_post") from e 