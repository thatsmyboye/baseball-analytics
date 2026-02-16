import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL not found in environment variables.\n"
        "Please create a .env file in the project root with:\n"
        "DATABASE_URL=postgresql://user:password@host:port/database\n"
        "See .env.example for a template."
    )

# Create engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_database():
    """Initialize database with schema"""
    with open('src/database/schema.sql', 'r') as f:
        schema = f.read()
    
    with engine.connect() as conn:
        # Execute each statement separately to handle errors individually
        statements = [s.strip() for s in schema.split(';') if s.strip()]
        for statement in statements:
            try:
                conn.execute(text(statement))
            except Exception as e:
                # Skip if object already exists, otherwise raise
                if 'already exists' not in str(e):
                    raise
        conn.commit()
    
    print("✅ Database initialized successfully")

def get_session():
    """Get a database session"""
    return SessionLocal()

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False