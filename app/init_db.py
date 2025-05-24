from db import engine, Base
from models.user import User
from models.post import Post

def init_db():
    """
    Initialize the database by creating all tables.
    """
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db() 