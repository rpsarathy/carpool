import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from datetime import datetime

# Database configuration with environment-aware fallback
def get_database_url():
    """Get database URL with local fallback for development"""
    # Try environment variable first
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        print(f"Using DATABASE_URL: {db_url[:50]}...")
        return db_url
    
    # Check if we're in a Cloud Run environment
    if os.getenv("K_SERVICE"):  # Cloud Run environment variable
        print("Cloud Run detected but no DATABASE_URL, falling back to SQLite")
        return "sqlite:///./carpool_local.db"
    
    # Local development fallback - use SQLite for simplicity
    print("⚠️  Using SQLite for local development. Set DATABASE_URL for PostgreSQL.")
    return "sqlite:///./carpool_local.db"

DATABASE_URL = get_database_url()

# Create engine with appropriate configuration
if DATABASE_URL.startswith("postgresql"):
    # PostgreSQL configuration with connection pooling for Cloud Run
    try:
        engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300
        )
        # Test the connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ PostgreSQL connection successful")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("🔄 Falling back to SQLite")
        DATABASE_URL = "sqlite:///./carpool_local.db"
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
else:
    # SQLite configuration for local development
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # SQLite specific
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)  # Allow null for Google OAuth users
    google_id = Column(String, nullable=True, index=True)  # Google OAuth ID
    created_at = Column(DateTime, default=datetime.utcnow)

class Group(Base):
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    departure_time = Column(String, nullable=False)
    days_of_week = Column(String, nullable=False)  # JSON string of day indices
    driver = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    members = Column(Text)  # JSON string of member emails
    created_at = Column(DateTime, default=datetime.utcnow)

class OnDemandRequest(Base):
    __tablename__ = "on_demand_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=False)
    origin = Column(String, nullable=False)
    origin_lat = Column(Float, nullable=True)
    origin_lng = Column(Float, nullable=True)
    destination = Column(String, nullable=False)
    dest_lat = Column(Float, nullable=True)
    dest_lng = Column(Float, nullable=True)
    dest_place_id = Column(String, nullable=True)
    dest_address = Column(String, nullable=True)
    date = Column(String, nullable=False)
    preferred_driver = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper functions
def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)

def health_check():
    """Check database connectivity"""
    try:
        db = SessionLocal()
        # Simple query to test connection
        if DATABASE_URL.startswith("postgresql"):
            db.execute(text("SELECT 1"))
        else:
            db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        print(f"Database health check failed: {e}")
        return False

def get_database_info():
    """Get information about the current database configuration"""
    return {
        "url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
        "type": "PostgreSQL" if DATABASE_URL.startswith("postgresql") else "SQLite",
        "environment": "production" if os.getenv("K_SERVICE") else "development"
    }
