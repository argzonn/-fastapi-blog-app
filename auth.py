import jwt
from fastapi import HTTPException
import sys

# --- Authentication Configuration ---

SECRET_KEY = "your-secret-key"  # Replace with a strong, unique, and secret key in production
ALGORITHM = "HS256"

# --- Token Validation Function ---

def get_current_user(token: str) -> int:
    """
    Decodes and validates a JWT token from the request header.

    This function is used as a dependency in authenticated endpoints
    to extract the user ID from the provided token.

    Args:
        token (str): The JWT token extracted from the 'token' request header.

    Returns:
        int: The user ID (subject 'sub') from the token payload.

    Raises:
        HTTPException: If the token is invalid, expired, or missing (401 Unauthorized).
                       Also raised if the token payload does not contain a user ID.
    """
    try:
        # Decode the token using the secret key and specified algorithm
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Extract the user ID from the token payload (assuming 'sub' claim is used)
        user_id = payload.get("sub")

        # Check if user_id is present in the payload
        if user_id is None:
            print("Token payload missing user ID ('sub').", file=sys.stderr)
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Ensure user_id is an integer (as stored in the database)
        # In this case, our create_token function stores it as str, so convert
        return int(user_id)

    except jwt.ExpiredSignatureError:
        # Handle token expiration
        print("Token has expired.", file=sys.stderr)
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        # Handle other JWT validation errors
        print("Invalid token structure or signature.", file=sys.stderr)
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        # Catch any other unexpected errors during token processing
        print(f"Unexpected error during token validation: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail="Internal server error during token validation") from e 