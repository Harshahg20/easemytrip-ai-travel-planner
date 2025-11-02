from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import logging

logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL, constructing from components if needed"""
    return settings.resolved_database_url

# Create database engine lazily (only when needed)
_engine = None

def get_engine():
    """Get or create database engine"""
    global _engine
    if _engine is None:
        database_url = get_database_url()
        connect_args = {}
        engine_kwargs = {
            "pool_pre_ping": True,  # Verify connections before use
            "pool_recycle": 300,    # Recycle connections every 5 minutes
        }
        
        if "sqlite" in database_url:
            connect_args = {"check_same_thread": False}
            engine_kwargs["connect_args"] = connect_args
        elif "mysql" in database_url:
            connect_args = {
                "charset": "utf8mb4",
                "autocommit": False
            }
            # For MySQL 8.0+, ensure proper configuration
            engine_kwargs["connect_args"] = connect_args
            engine_kwargs["pool_size"] = 10
            engine_kwargs["max_overflow"] = 20
        
        _engine = create_engine(
            database_url,
            **engine_kwargs
        )
        
        # For MySQL, set proper SQL mode to handle modern syntax
        if "mysql" in database_url:
            @event.listens_for(_engine, "connect")
            def set_mysql_mode(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                # Set SQL mode to be compatible with modern MySQL
                cursor.execute("SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'")
                cursor.close()
            
            logger.info("MySQL engine configured with modern SQL mode")
    
    return _engine

# For backward compatibility, create engine at module level
# This will fail if DATABASE_URL can't be resolved, but that's intentional
engine = get_engine()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
