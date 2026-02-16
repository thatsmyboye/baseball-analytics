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

# Validate DATABASE_URL doesn't contain placeholder values
def contains_placeholder(url, placeholder):
    """Check if URL contains a specific placeholder value"""
    if placeholder == 'user':
        # user appears after :// and before : or @
        return f'://{placeholder}:' in url or f'://{placeholder}@' in url
    elif placeholder == 'password':
        # password appears after : and before @
        return f':{placeholder}@' in url
    elif placeholder == 'host':
        # host appears after @ and before :
        return f'@{placeholder}:' in url
    elif placeholder == 'port':
        # port appears after : and before /
        return f':{placeholder}/' in url
    elif placeholder == 'database':
        # database is the last segment after the final /
        return url.split('/')[-1] == placeholder
    return False

placeholder_values = ['user', 'password', 'host', 'port', 'database']
if all(contains_placeholder(DATABASE_URL, placeholder) for placeholder in placeholder_values):
    raise ValueError(
        "DATABASE_URL contains placeholder values.\n"
        "Please update your .env file with actual database credentials:\n"
        "  - Replace 'user' with your database username\n"
        "  - Replace 'password' with your database password\n"
        "  - Replace 'host' with your database host (e.g., localhost)\n"
        "  - Replace 'port' with your database port (e.g., 5432)\n"
        "  - Replace 'database' with your database name\n\n"
        "Example valid URLs:\n"
        "  postgresql://postgres:mypassword@localhost:5432/baseball\n"
        "  postgresql://admin:secret@db.example.com:5432/analytics"
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