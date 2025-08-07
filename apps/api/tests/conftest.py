"""
Enhanced pytest configuration and shared fixtures for Seiketsu AI API tests.
Includes comprehensive test setup, fixtures, and utilities.
"""
import pytest
import asyncio
import asyncpg
import redis.asyncio as redis
from typing import Generator, AsyncGenerator, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from alembic import command
from alembic.config import Config
import os
import sys
from datetime import datetime
import uuid
import logging
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
import tempfile
import shutil

# Add app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from app.core.config import settings
from app.core.database import get_db, init_db
from app.core.auth import create_access_token

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


# Additional configuration and utilities
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")


# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings and markers"""
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests (slower, with external services)")
    config.addinivalue_line("markers", "performance: Performance and load tests")
    config.addinivalue_line("markers", "security: Security and compliance tests")
    config.addinivalue_line("markers", "ai: AI service tests")
    config.addinivalue_line("markers", "voice: Voice processing tests")
    config.addinivalue_line("markers", "database: Database-related tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "websocket: WebSocket connection tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "external: Tests requiring external services")
    config.addinivalue_line("markers", "mock: Tests using mocked services")


@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def temp_directory():
    """Create temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
async def redis_client():
    """Create Redis client for tests"""
    client = redis.from_url(TEST_REDIS_URL)
    await client.flushdb()  # Clear test database
    yield client
    await client.flushdb()  # Cleanup
    await client.close()


# Authentication fixtures
@pytest.fixture
def access_token(test_user):
    """Create access token for test user"""
    return create_access_token(data={"sub": test_user.email, "user_id": test_user.id})


@pytest.fixture
def admin_token(test_admin_user):
    """Create access token for admin user"""
    return create_access_token(data={"sub": test_admin_user.email, "user_id": test_admin_user.id})


@pytest.fixture
def authorized_headers(access_token):
    """Create headers with auth token"""
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_headers(admin_token):
    """Create headers with admin auth token"""
    return {"Authorization": f"Bearer {admin_token}"}


# Test data fixtures
@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing"""
    return {
        "name": "John Smith",
        "email": "john.smith@example.com",
        "phone": "+1234567890",
        "source": "website",
        "property_preferences": {
            "type": "single_family",
            "bedrooms": 3,
            "bathrooms": 2,
            "min_price": 300000,
            "max_price": 500000,
            "location": "downtown",
            "features": ["garage", "pool", "updated_kitchen"]
        },
        "timeline": "3_months",
        "notes": "Interested in properties with good schools nearby"
    }


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing"""
    return {
        "type": "outbound_call",
        "duration_seconds": 420,
        "transcript": "Agent: Hello, thank you for your interest in our properties.\nLead: Hi, I'm looking for a family home in a good neighborhood.",
        "sentiment_score": 0.8,
        "lead_score": 75,
        "status": "qualified",
        "ai_insights": {
            "intent": "property_search",
            "emotions": ["interested", "engaged"],
            "urgency": "medium",
            "buying_signals": ["budget_mentioned", "timeline_specified"]
        }
    }


@pytest.fixture
def sample_property_data():
    """Sample property data for testing"""
    return {
        "mls_id": "MLS789012",
        "address": "456 Oak Avenue, Testville",
        "city": "Testville",
        "state": "CA",
        "zip_code": "90210",
        "price": 575000,
        "bedrooms": 4,
        "bathrooms": 2.5,
        "square_feet": 2800,
        "lot_size": 0.25,
        "property_type": "single_family",
        "listing_status": "active",
        "year_built": 2010,
        "features": ["garage", "fireplace", "hardwood_floors", "updated_kitchen", "master_suite"],
        "description": "Beautiful family home in desirable neighborhood",
        "images": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
    }


# Utility fixtures
@pytest.fixture
def assert_timing():
    """Utility for asserting operation timing"""
    import time
    
    class TimingAssertion:
        def __init__(self):
            self.start_time = None
            
        def start(self):
            self.start_time = time.perf_counter()
            
        def assert_under(self, max_seconds, message="Operation took too long"):
            if self.start_time is None:
                raise ValueError("Must call start() first")
            
            elapsed = time.perf_counter() - self.start_time
            assert elapsed < max_seconds, f"{message}: {elapsed:.3f}s > {max_seconds}s"
            
        def get_elapsed(self):
            if self.start_time is None:
                return 0
            return time.perf_counter() - self.start_time
    
    return TimingAssertion()


@pytest.fixture
def performance_monitor():
    """Monitor performance metrics during tests"""
    import psutil
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.process = psutil.Process()
            self.start_time = None
            self.start_memory = None
            self.start_cpu = None
            
        def start(self):
            self.start_time = time.perf_counter()
            self.start_memory = self.process.memory_info().rss
            self.start_cpu = self.process.cpu_percent()
            
        def get_metrics(self):
            if self.start_time is None:
                return {}
                
            return {
                "elapsed_time": time.perf_counter() - self.start_time,
                "memory_delta": self.process.memory_info().rss - self.start_memory,
                "cpu_percent": self.process.cpu_percent(),
                "memory_mb": self.process.memory_info().rss / 1024 / 1024
            }
    
    return PerformanceMonitor()


# Custom pytest hooks
def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption("--runslow", action="store_true", default=False, help="Run slow tests")
    parser.addoption("--runexternal", action="store_true", default=False, help="Run tests requiring external services")


def pytest_runtest_setup(item):
    """Set up before each test"""
    # Skip slow tests unless explicitly requested
    if "slow" in [mark.name for mark in item.iter_markers()]:
        if not item.config.getoption("--runslow", default=False):
            pytest.skip("Skipping slow test (use --runslow to run)")


def pytest_sessionstart(session):
    """Validate test configuration at session start"""
    logger.info("Starting Seiketsu AI test session")
    logger.info(f"Test database: {TEST_DATABASE_URL}")
    logger.info(f"Test Redis: {TEST_REDIS_URL}")


def pytest_sessionfinish(session, exitstatus):
    """Clean up at session end"""
    logger.info(f"Test session finished with exit status: {exitstatus}")


# Cleanup fixtures
@pytest.fixture(autouse=True)
async def cleanup_database(db_session: AsyncSession):
    """Clean up database after each test"""
    yield
    # Cleanup is handled by transaction rollback in db_session fixture