"""
Pytest configuration and shared fixtures for Seiketsu AI API tests
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from alembic import command
from alembic.config import Config
import os
from datetime import datetime
import uuid

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://test_user:test_pass@localhost/seiketsu_test"
)

# Create async engine for tests
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# Session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Set up test database schema"""
    # Run migrations
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL.replace("+asyncpg", ""))
    
    # Create all tables
    command.upgrade(alembic_cfg, "head")
    
    yield
    
    # Clean up - drop all tables
    command.downgrade(alembic_cfg, "base")


@pytest.fixture(scope="function")
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Get a test database session"""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest.fixture(scope="function")
async def test_organization(db_session: AsyncSession):
    """Create a test organization"""
    from app.models.organization import Organization
    
    org = Organization(
        id=str(uuid.uuid4()),
        name="Test Real Estate Agency",
        subdomain="test-agency",
        settings={
            "max_agents": 10,
            "voice_minutes": 5000,
            "features": ["voice_ai", "lead_scoring"]
        },
        subscription_status="active",
        created_at=datetime.utcnow()
    )
    
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    
    return org


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession, test_organization):
    """Create a test user"""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Test User",
        role="agent",
        organization_id=test_organization.id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture(scope="function")
async def test_admin_user(db_session: AsyncSession, test_organization):
    """Create a test admin user"""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    admin = User(
        id=str(uuid.uuid4()),
        email="admin@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Test Admin",
        role="admin",
        organization_id=test_organization.id,
        is_active=True,
        is_superuser=True,
        created_at=datetime.utcnow()
    )
    
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    return admin


@pytest.fixture(scope="function")
async def test_lead(db_session: AsyncSession, test_organization):
    """Create a test lead"""
    from app.models.lead import Lead
    
    lead = Lead(
        id=str(uuid.uuid4()),
        organization_id=test_organization.id,
        name="Test Lead",
        email="lead@example.com",
        phone="+1234567890",
        source="website",
        property_preferences={
            "type": "single_family",
            "min_price": 300000,
            "max_price": 500000,
            "bedrooms": 3
        },
        qualification_status="new",
        lead_score=0,
        created_at=datetime.utcnow()
    )
    
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)
    
    return lead


@pytest.fixture(scope="function")
async def test_conversation(db_session: AsyncSession, test_organization, test_lead, test_user):
    """Create a test conversation"""
    from app.models.conversation import Conversation
    
    conversation = Conversation(
        id=str(uuid.uuid4()),
        organization_id=test_organization.id,
        lead_id=test_lead.id,
        agent_id=test_user.id,
        duration_seconds=180,
        transcript="Test conversation transcript...",
        sentiment_score=0.75,
        lead_score=65,
        status="qualified",
        recording_url="https://example.com/recording.mp3",
        created_at=datetime.utcnow()
    )
    
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)
    
    return conversation


@pytest.fixture(scope="function")
async def test_voice_agent(db_session: AsyncSession, test_organization):
    """Create a test voice agent"""
    from app.models.voice_agent import VoiceAgent
    
    agent = VoiceAgent(
        id=str(uuid.uuid4()),
        organization_id=test_organization.id,
        name="Test Voice Agent",
        voice_id="elevenlabs_test_voice",
        personality="professional",
        language="en-US",
        pitch=1.0,
        speed=1.0,
        script_template="standard_qualifier",
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db_session.add(agent)
    await db_session.commit()
    await db_session.refresh(agent)
    
    return agent


@pytest.fixture(scope="function")
async def test_property(db_session: AsyncSession, test_organization):
    """Create a test property"""
    from app.models.property import Property
    
    property = Property(
        id=str(uuid.uuid4()),
        organization_id=test_organization.id,
        mls_id="MLS123456",
        address="123 Test St, Test City",
        price=425000,
        bedrooms=3,
        bathrooms=2,
        square_feet=2200,
        property_type="single_family",
        listing_status="active",
        features=["garage", "pool", "updated_kitchen"],
        created_at=datetime.utcnow()
    )
    
    db_session.add(property)
    await db_session.commit()
    await db_session.refresh(property)
    
    return property


@pytest.fixture
def mock_elevenlabs_api(monkeypatch):
    """Mock ElevenLabs API calls"""
    import httpx
    
    class MockResponse:
        def __init__(self, content, status_code=200):
            self.content = content
            self.status_code = status_code
            self.headers = {"content-type": "audio/mpeg"}
        
        def raise_for_status(self):
            if self.status_code >= 400:
                raise httpx.HTTPStatusError("Error", request=None, response=self)
    
    async def mock_post(*args, **kwargs):
        # Mock audio synthesis
        if "text-to-speech" in args[0]:
            return MockResponse(b"fake_audio_data")
        # Mock other endpoints
        return MockResponse(b'{"status": "success"}')
    
    async def mock_get(*args, **kwargs):
        # Mock voice list
        if "voices" in args[0]:
            return MockResponse(b'{"voices": [{"voice_id": "test", "name": "Test Voice"}]}')
        return MockResponse(b'{"status": "success"}')
    
    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)
    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)


@pytest.fixture
def mock_supabase_client(monkeypatch):
    """Mock Supabase client for tests"""
    class MockSupabase:
        def __init__(self):
            self.auth = MockAuth()
            self.table = MockTable()
            self.storage = MockStorage()
    
    class MockAuth:
        async def sign_up(self, credentials):
            return {"user": {"id": "test_id"}, "session": {"access_token": "test_token"}}
        
        async def sign_in_with_password(self, credentials):
            return {"user": {"id": "test_id"}, "session": {"access_token": "test_token"}}
        
        async def sign_out(self):
            return {"error": None}
        
        async def get_user(self, token):
            return {"user": {"id": "test_id", "email": "test@example.com"}}
    
    class MockTable:
        def __init__(self):
            self.data = []
        
        def select(self, *args):
            return self
        
        def insert(self, data):
            self.data.append(data)
            return self
        
        def update(self, data):
            return self
        
        def delete(self):
            return self
        
        def eq(self, field, value):
            return self
        
        def single(self):
            return {"data": self.data[0] if self.data else None}
        
        def execute(self):
            return {"data": self.data, "error": None}
    
    class MockStorage:
        def from_(self, bucket):
            return self
        
        def upload(self, path, file):
            return {"data": {"path": path}, "error": None}
        
        def download(self, path):
            return b"fake_file_content"
        
        def get_public_url(self, path):
            return f"https://example.com/storage/{path}"
    
    monkeypatch.setattr("app.core.supabase.client", MockSupabase())


@pytest.fixture
def mock_redis_client(monkeypatch):
    """Mock Redis client for tests"""
    class MockRedis:
        def __init__(self):
            self.data = {}
        
        async def get(self, key):
            return self.data.get(key)
        
        async def set(self, key, value, ex=None):
            self.data[key] = value
            return True
        
        async def delete(self, key):
            if key in self.data:
                del self.data[key]
            return True
        
        async def exists(self, key):
            return key in self.data
        
        async def expire(self, key, seconds):
            return True
        
        async def ttl(self, key):
            return 3600  # Mock TTL
    
    monkeypatch.setattr("app.core.cache.redis_client", MockRedis())


# Environment variable fixtures
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("SECRET_KEY", "test_secret_key_for_testing_only")
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test_supabase_key")
    monkeypatch.setenv("ELEVEN_LABS_API_KEY", "test_eleven_labs_key")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")
    monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000"]')


# Cleanup fixtures
@pytest.fixture(autouse=True)
async def cleanup_database(db_session: AsyncSession):
    """Clean up database after each test"""
    yield
    # Cleanup is handled by transaction rollback in db_session fixture