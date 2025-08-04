"""
Database configuration and connection for Seiketsu AI API
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event
from sqlalchemy.pool import NullPool
import logging

from app.core.config import settings

logger = logging.getLogger("seiketsu.database")

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False
)

# Create declarative base
Base = declarative_base()


async def init_db():
    """Initialize database connection and create tables if needed"""
    try:
        # Test connection
        async with engine.begin() as conn:
            logger.info("Database connection established successfully")
            
            # In development, create tables
            if settings.ENVIRONMENT == "development":
                logger.info("Creating database tables...")
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Database tables created successfully")
        
        logger.info("Database initialization complete")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def get_db() -> AsyncSession:
    """Get database session dependency"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def close_db():
    """Close database engine"""
    await engine.dispose()
    logger.info("Database engine disposed")


# Event listeners for connection management
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas if using SQLite"""
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@event.listens_for(engine.sync_engine, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    """Ping connection on checkout to ensure it's alive"""
    try:
        dbapi_connection.ping(reconnect=True)
    except Exception:
        # Connection is invalid, will be recreated
        raise


# Transaction management utilities
class DatabaseTransaction:
    """Context manager for database transactions"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def __aenter__(self):
        await self.session.begin()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
            logger.error(f"Transaction rolled back due to: {exc_val}")
        else:
            await self.session.commit()
            logger.debug("Transaction committed successfully")