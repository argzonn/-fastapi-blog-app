import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from db import get_db
from models.user import User
from schemas.user import UserCreate, UserLogin, UserOut
import sys

class UserService:
    """
    Handles user-related business logic, including signup and login.
    Interacts with the database for user data persistence.
    """
    def __init__(self):
        """
        Initializes the UserService with a database session.
        """
        # Get a new database session for each service instance
        try:
            self.db = next(get_db())
            print("Database session obtained successfully.", file=sys.stderr)
        except Exception as e:
            print(f"Error getting database session: {e}", file=sys.stderr)
            # Depending on how critical this is, you might want to re-raise or handle differently
            raise HTTPException(status_code=500, detail="Database connection error") from e

    async def signup(self, user_data: UserCreate):
        """
        Registers a new user.

        Hashes the provided password and saves the user to the database.

        Args:
            user_data (UserCreate): The user data including email and password.

        Returns:
            User: The newly created user SQLAlchemy model instance after database refresh.
                  This instance is expected to have the 'id' populated.

        Raises:
            HTTPException: If a user with the same email already exists (400),
                           or if there's an unexpected error during database operations (500).
        """
        print("Attempting user signup...", file=sys.stderr)
        try:
            # Check if user already exists
            print(f"Checking for existing user with email: {user_data.email}", file=sys.stderr)
            existing_user = self.db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                print("User already exists.", file=sys.stderr)
                raise HTTPException(status_code=400, detail="Email already registered")
            
            print("Hashing password...", file=sys.stderr)
            # Hash the password
            hashed_password = bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt())
            print("Password hashed.", file=sys.stderr)

            print("Creating new user object...", file=sys.stderr)
            # Create new user
            user = User(
                email=user_data.email,
                hashed_password=hashed_password.decode()
            )
            print("User object created.", file=sys.stderr)

            print("Adding user to session...", file=sys.stderr)
            self.db.add(user)
            print("User added to session. Committing...", file=sys.stderr)
            self.db.commit()
            print("Commit successful. Refreshing user object...", file=sys.stderr)
            # The refresh is crucial to get the generated ID from the database
            self.db.refresh(user)
            print(f"User object refreshed. User ID: {user.id}", file=sys.stderr)
            
            # Check if user.id is populated after refresh
            if user.id is None:
                 print("Error: User ID is None after refresh!", file=sys.stderr)
                 raise HTTPException(status_code=500, detail="Could not retrieve user ID after signup")

            print("Generating token...", file=sys.stderr)
            # Generate token
            token = self._create_token(user.id)
            print("Token generated.", file=sys.stderr)

            # Create a dictionary matching the UserOut schema
            response_data = {"id": user.id, "email": user.email, "token": token}
            print(f"Data being returned: {response_data}", file=sys.stderr)

            # Return an instance of UserOut
            return UserOut(**response_data)

        except HTTPException as e:
            # Re-raise HTTPException as they are expected for business logic errors (e.g., email exists)
            print(f"Caught HTTPException: {e.detail}", file=sys.stderr)
            self.db.rollback() # Rollback in case of expected errors after some db operations
            raise e
        except Exception as e:
            # Catch any other unexpected exceptions
            print(f"Caught unexpected exception during signup: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self.db.rollback() # Rollback in case of unexpected errors
            raise HTTPException(status_code=500, detail="Internal Server Error during signup") from e

    async def login(self, user_data: UserLogin):
        """
        Authenticates an existing user.

        Verifies the provided email and password against the database.

        Args:
            user_data (UserLogin): The user credentials including email and password.

        Returns:
            User: The authenticated user SQLAlchemy model instance with a JWT token attached.

        Raises:
            HTTPException: If the credentials are invalid (401),
                           or if there's an unexpected error during database operations (500).
        """
        print("Attempting user login...", file=sys.stderr)
        try:
            user = self.db.query(User).filter(User.email == user_data.email).first()
            if not user or not bcrypt.checkpw(user_data.password.encode(), user.hashed_password.encode()):
                print("Invalid credentials during login.", file=sys.stderr)
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            print(f"User found for login. User ID: {user.id}", file=sys.stderr)
            token = self._create_token(user.id)
            print("Token generated for login.", file=sys.stderr)

            response_data = {"id": user.id, "email": user.email, "token": token}
            print(f"Returning login data: {response_data}", file=sys.stderr)
            # Return an instance of UserOut for login as well
            return UserOut(**response_data)

        except HTTPException as e:
            print(f"Caught HTTPException during login: {e.detail}", file=sys.stderr)
            self.db.rollback() # Rollback in case of expected errors after some db operations
            raise e
        except Exception as e:
            print(f"Caught unexpected exception during login: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self.db.rollback() # Rollback in case of unexpected errors
            raise HTTPException(status_code=500, detail="Internal Server Error during login") from e


    def _create_token(self, user_id: int) -> str:
        """
        Creates a JWT token for a given user ID.

        Args:
            user_id (int): The ID of the user for whom the token is being created.

        Returns:
            str: The encoded JWT token.
        """
        payload = {
            "sub": str(user_id),
            "exp": datetime.utcnow() + timedelta(days=1)
        }
        # Using your-secret-key as defined, ensure this is secure in production
        return jwt.encode(payload, "your-secret-key", algorithm="HS256") 