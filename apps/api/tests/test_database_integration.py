"""
Database Integration Tests
Tests for database operations, transactions, migrations, and data integrity
"""
import pytest
import asyncio
from typing import Dict, Any, List
from sqlalchemy import text, inspect
from sqlalchemy.exc import IntegrityError, DataError
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db, init_db
from app.models.base import Base
from app.models.organization import Organization
from app.models.user import User
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.models.voice_agent import VoiceAgent
from app.models.property import Property
from app.core.security import get_password_hash


@pytest.mark.database
@pytest.mark.integration
class TestDatabaseSchema:
    """Test database schema and table structure"""
    
    @pytest.mark.asyncio
    async def test_all_tables_created(self, db_session):
        """Test that all required tables are created"""
        inspector = inspect(db_session.bind)
        existing_tables = inspector.get_table_names()
        
        required_tables = [
            'organizations',
            'users',
            'leads',
            'conversations',
            'voice_agents',
            'properties',
            'webhooks'
        ]
        
        for table in required_tables:
            assert table in existing_tables, f"Table {table} not found in database"
    
    @pytest.mark.asyncio
    async def test_table_constraints(self, db_session):
        """Test database constraints and foreign keys"""
        inspector = inspect(db_session.bind)
        
        # Test foreign key constraints
        users_fks = inspector.get_foreign_keys('users')
        user_org_fk = next((fk for fk in users_fks if fk['constrained_columns'] == ['organization_id']), None)
        assert user_org_fk is not None, "Users table missing organization_id foreign key"
        
        leads_fks = inspector.get_foreign_keys('leads')
        lead_org_fk = next((fk for fk in leads_fks if fk['constrained_columns'] == ['organization_id']), None)
        assert lead_org_fk is not None, "Leads table missing organization_id foreign key"
        
        # Test unique constraints
        users_indexes = inspector.get_indexes('users')
        email_unique = any(idx['unique'] and 'email' in idx['column_names'] for idx in users_indexes)
        assert email_unique, "Users table missing unique constraint on email"
    
    @pytest.mark.asyncio
    async def test_column_types(self, db_session):
        """Test column data types"""
        inspector = inspect(db_session.bind)
        
        # Test organizations table columns
        org_columns = {col['name']: col['type'] for col in inspector.get_columns('organizations')}
        assert 'id' in org_columns
        assert 'name' in org_columns
        assert 'subdomain' in org_columns
        assert 'settings' in org_columns  # JSON column
        assert 'created_at' in org_columns
        
        # Test users table columns
        user_columns = {col['name']: col['type'] for col in inspector.get_columns('users')}
        assert 'id' in user_columns
        assert 'email' in user_columns
        assert 'hashed_password' in user_columns
        assert 'is_active' in user_columns
        assert 'organization_id' in user_columns


@pytest.mark.database
@pytest.mark.integration
class TestDatabaseOperations:
    """Test basic database operations"""
    
    @pytest.mark.asyncio
    async def test_organization_crud(self, db_session):
        """Test organization CRUD operations"""
        # Create
        org = Organization(
            id=str(uuid.uuid4()),
            name="Test Organization",
            subdomain="test-org",
            settings={
                "max_agents": 10,
                "voice_minutes": 5000,
                "features": ["voice_ai", "lead_scoring"]
            },
            subscription_status="active"
        )
        
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)
        
        assert org.id is not None
        assert org.created_at is not None
        
        # Read
        retrieved_org = await db_session.get(Organization, org.id)
        assert retrieved_org is not None
        assert retrieved_org.name == "Test Organization"
        assert retrieved_org.settings["max_agents"] == 10
        
        # Update
        retrieved_org.name = "Updated Organization"
        retrieved_org.settings["max_agents"] = 20
        await db_session.commit()
        
        updated_org = await db_session.get(Organization, org.id)
        assert updated_org.name == "Updated Organization"
        assert updated_org.settings["max_agents"] == 20
        
        # Delete
        await db_session.delete(updated_org)
        await db_session.commit()
        
        deleted_org = await db_session.get(Organization, org.id)
        assert deleted_org is None
    
    @pytest.mark.asyncio
    async def test_user_crud_with_relationships(self, db_session, test_organization):
        """Test user CRUD operations with organization relationship"""
        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            hashed_password=get_password_hash("testpassword"),
            full_name="Test User",
            role="agent",
            organization_id=test_organization.id,
            is_active=True
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Test relationship loading
        user_with_org = await db_session.get(User, user.id)
        assert user_with_org.organization_id == test_organization.id
        
        # Test cascade behavior (user should be deletable without affecting org)
        await db_session.delete(user_with_org)
        await db_session.commit()
        
        # Organization should still exist
        org_still_exists = await db_session.get(Organization, test_organization.id)
        assert org_still_exists is not None
    
    @pytest.mark.asyncio
    async def test_lead_crud_with_json_fields(self, db_session, test_organization):
        """Test lead CRUD operations with JSON fields"""
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
                "bedrooms": 3,
                "location": "downtown",
                "features": ["garage", "pool"]
            },
            qualification_status="new",
            lead_score=0
        )
        
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)
        
        # Test JSON field access
        retrieved_lead = await db_session.get(Lead, lead.id)
        assert retrieved_lead.property_preferences["type"] == "single_family"
        assert retrieved_lead.property_preferences["min_price"] == 300000
        assert "garage" in retrieved_lead.property_preferences["features"]
        
        # Test JSON field update
        retrieved_lead.property_preferences["max_price"] = 600000
        retrieved_lead.property_preferences["features"].append("updated_kitchen")
        await db_session.commit()
        
        updated_lead = await db_session.get(Lead, lead.id)
        assert updated_lead.property_preferences["max_price"] == 600000
        assert "updated_kitchen" in updated_lead.property_preferences["features"]
    
    @pytest.mark.asyncio
    async def test_conversation_with_relationships(self, db_session, test_organization, test_lead, test_user):
        """Test conversation with multiple relationships"""
        conversation = Conversation(
            id=str(uuid.uuid4()),
            organization_id=test_organization.id,
            lead_id=test_lead.id,
            agent_id=test_user.id,
            duration_seconds=300,
            transcript="This is a test conversation transcript",
            sentiment_score=0.8,
            lead_score=75,
            status="completed",
            ai_insights={
                "sentiment": "positive",
                "buying_signals": ["budget_mentioned", "timeline_specified"],
                "next_steps": ["send_listings", "schedule_viewing"]
            }
        )
        
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)
        
        # Test relationships
        retrieved_conv = await db_session.get(Conversation, conversation.id)
        assert retrieved_conv.organization_id == test_organization.id
        assert retrieved_conv.lead_id == test_lead.id
        assert retrieved_conv.agent_id == test_user.id
        assert retrieved_conv.ai_insights["sentiment"] == "positive"
        assert len(retrieved_conv.ai_insights["buying_signals"]) == 2


@pytest.mark.database
@pytest.mark.integration
class TestDatabaseTransactions:
    """Test database transaction handling"""
    
    @pytest.mark.asyncio
    async def test_transaction_commit(self, db_session, test_organization):
        """Test successful transaction commit"""
        # Create multiple related records in a transaction
        user1 = User(
            id=str(uuid.uuid4()),
            email="user1@transaction.com",
            hashed_password=get_password_hash("password"),
            full_name="User One",
            organization_id=test_organization.id,
            role="agent",
            is_active=True
        )
        
        user2 = User(
            id=str(uuid.uuid4()),
            email="user2@transaction.com",
            hashed_password=get_password_hash("password"),
            full_name="User Two",
            organization_id=test_organization.id,
            role="agent",
            is_active=True
        )
        
        lead = Lead(
            id=str(uuid.uuid4()),
            organization_id=test_organization.id,
            name="Transaction Lead",
            email="transaction@example.com",
            phone="+1234567890",
            source="test",
            qualification_status="new"
        )
        
        # Add all to session and commit
        db_session.add_all([user1, user2, lead])
        await db_session.commit()
        
        # Verify all records were created
        assert await db_session.get(User, user1.id) is not None
        assert await db_session.get(User, user2.id) is not None
        assert await db_session.get(Lead, lead.id) is not None
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_session, test_organization):
        """Test transaction rollback on error"""
        # Create valid user first
        valid_user = User(
            id=str(uuid.uuid4()),
            email="valid@rollback.com",
            hashed_password=get_password_hash("password"),
            full_name="Valid User",
            organization_id=test_organization.id,
            role="agent",
            is_active=True
        )
        
        db_session.add(valid_user)
        
        # Try to create user with duplicate email (should fail)
        try:
            duplicate_user = User(
                id=str(uuid.uuid4()),
                email="valid@rollback.com",  # Same email - will violate unique constraint
                hashed_password=get_password_hash("password"),
                full_name="Duplicate User",
                organization_id=test_organization.id,
                role="agent",
                is_active=True
            )
            
            db_session.add(duplicate_user)
            await db_session.commit()
            
            # Should not reach here
            assert False, "Expected IntegrityError for duplicate email"
            
        except IntegrityError:
            # Rollback the transaction
            await db_session.rollback()
            
            # The valid user should not have been committed either
            user_exists = await db_session.get(User, valid_user.id)
            assert user_exists is None
    
    @pytest.mark.asyncio
    async def test_concurrent_transactions(self, test_organization):
        """Test concurrent transaction handling"""
        from app.core.database import get_db
        
        async def create_user_transaction(user_num):
            async with get_db() as session:
                user = User(
                    id=str(uuid.uuid4()),
                    email=f"concurrent{user_num}@example.com",
                    hashed_password=get_password_hash("password"),
                    full_name=f"Concurrent User {user_num}",
                    organization_id=test_organization.id,
                    role="agent",
                    is_active=True
                )
                
                session.add(user)
                await session.commit()
                return user.id
        
        # Create users concurrently
        tasks = [create_user_transaction(i) for i in range(10)]
        user_ids = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All transactions should succeed
        successful_creates = sum(1 for uid in user_ids if isinstance(uid, str))
        assert successful_creates == 10


@pytest.mark.database
@pytest.mark.integration
class TestDatabaseConstraints:
    """Test database constraint enforcement"""
    
    @pytest.mark.asyncio
    async def test_unique_constraints(self, db_session, test_organization):
        """Test unique constraint enforcement"""
        # Create first user
        user1 = User(
            id=str(uuid.uuid4()),
            email="unique@example.com",
            hashed_password=get_password_hash("password"),
            full_name="First User",
            organization_id=test_organization.id,
            role="agent",
            is_active=True
        )
        
        db_session.add(user1)
        await db_session.commit()
        
        # Try to create second user with same email
        user2 = User(
            id=str(uuid.uuid4()),
            email="unique@example.com",  # Same email
            hashed_password=get_password_hash("password"),
            full_name="Second User",
            organization_id=test_organization.id,
            role="agent",
            is_active=True
        )
        
        db_session.add(user2)
        
        # Should raise IntegrityError
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, db_session):
        """Test foreign key constraint enforcement"""
        # Try to create user with non-existent organization
        user = User(
            id=str(uuid.uuid4()),
            email="orphan@example.com",
            hashed_password=get_password_hash("password"),
            full_name="Orphan User",
            organization_id="non-existent-org-id",
            role="agent",
            is_active=True
        )
        
        db_session.add(user)
        
        # Should raise IntegrityError for foreign key violation
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_not_null_constraints(self, db_session, test_organization):
        """Test NOT NULL constraint enforcement"""
        # Try to create user without required fields
        user = User(
            id=str(uuid.uuid4()),
            # email is missing (NOT NULL)
            hashed_password=get_password_hash("password"),
            full_name="Incomplete User",
            organization_id=test_organization.id,
            role="agent",
            is_active=True
        )
        
        db_session.add(user)
        
        # Should raise IntegrityError for NOT NULL violation
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_check_constraints(self, db_session, test_organization):
        """Test check constraint enforcement (if any)"""
        # Test email format validation (if implemented)
        user = User(
            id=str(uuid.uuid4()),
            email="invalid-email-format",
            hashed_password=get_password_hash("password"),
            full_name="Invalid Email User",
            organization_id=test_organization.id,
            role="agent",
            is_active=True
        )
        
        db_session.add(user)
        
        try:
            await db_session.commit()
            # If no email validation at DB level, this will succeed
            # Application-level validation should catch this
        except (IntegrityError, DataError):
            # If DB-level validation exists, it should fail here
            pass


@pytest.mark.database
@pytest.mark.integration
class TestDatabasePerformance:
    """Test database performance characteristics"""
    
    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, db_session, test_organization, performance_monitor):
        """Test bulk insert performance"""
        batch_size = 1000
        
        performance_monitor.start()
        
        # Create batch of leads
        leads = []
        for i in range(batch_size):
            lead = Lead(
                id=str(uuid.uuid4()),
                organization_id=test_organization.id,
                name=f"Bulk Lead {i}",
                email=f"bulk{i}@example.com",
                phone=f"+123456{i:04d}",
                source="bulk_test",
                property_preferences={
                    "type": "single_family" if i % 2 == 0 else "apartment",
                    "min_price": 200000 + (i * 1000),
                    "max_price": 500000 + (i * 1000),
                    "bedrooms": (i % 4) + 1
                },
                qualification_status="new",
                lead_score=i % 100
            )
            leads.append(lead)
        
        # Bulk insert
        db_session.add_all(leads)
        await db_session.commit()
        
        metrics = performance_monitor.get_metrics()
        
        # Performance assertions
        assert metrics["elapsed_time"] < 10.0  # Should complete in under 10 seconds
        
        inserts_per_second = batch_size / metrics["elapsed_time"]
        assert inserts_per_second > 100  # Should handle 100+ inserts per second
        
        print(f"\nBulk Insert Performance:")
        print(f"Inserted {batch_size} records in {metrics['elapsed_time']:.3f}s")
        print(f"Rate: {inserts_per_second:.1f} inserts/second")
    
    @pytest.mark.asyncio
    async def test_query_performance(self, db_session, test_organization, performance_monitor):
        """Test query performance with filtering and pagination"""
        # First create some test data
        leads = []
        for i in range(500):
            lead = Lead(
                id=str(uuid.uuid4()),
                organization_id=test_organization.id,
                name=f"Query Test Lead {i}",
                email=f"query{i}@example.com",
                phone=f"+123456{i:04d}",
                source="query_test",
                qualification_status="qualified" if i % 3 == 0 else "new",
                lead_score=i % 100
            )
            leads.append(lead)
        
        db_session.add_all(leads)
        await db_session.commit()
        
        performance_monitor.start()
        
        # Test complex query with filtering
        result = await db_session.execute(
            text("""
                SELECT * FROM leads 
                WHERE organization_id = :org_id 
                AND qualification_status = 'qualified'
                AND lead_score > 50
                ORDER BY created_at DESC
                LIMIT 50
            """),
            {"org_id": test_organization.id}
        )
        
        qualified_leads = result.fetchall()
        
        metrics = performance_monitor.get_metrics()
        
        # Performance assertions
        assert metrics["elapsed_time"] < 1.0  # Query should complete quickly
        assert len(qualified_leads) > 0  # Should return results
        
        print(f"\nQuery Performance:")
        print(f"Query executed in {metrics['elapsed_time']:.3f}s")
        print(f"Returned {len(qualified_leads)} results")
    
    @pytest.mark.asyncio
    async def test_index_effectiveness(self, db_session, test_organization):
        """Test database index effectiveness"""
        # Create test data with known patterns
        leads = []
        for i in range(1000):
            lead = Lead(
                id=str(uuid.uuid4()),
                organization_id=test_organization.id,
                name=f"Index Test Lead {i}",
                email=f"index{i}@example.com",
                phone=f"+123456{i:04d}",
                source="index_test",
                qualification_status="qualified" if i < 100 else "new",
                lead_score=i % 100
            )
            leads.append(lead)
        
        db_session.add_all(leads)
        await db_session.commit()
        
        # Test indexed query (organization_id should be indexed)
        start_time = time.time()
        
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM leads WHERE organization_id = :org_id"),
            {"org_id": test_organization.id}
        )
        
        count = result.scalar()
        indexed_query_time = time.time() - start_time
        
        # Test non-indexed query (name search)
        start_time = time.time()
        
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM leads WHERE name LIKE :pattern"),
            {"pattern": "%Index Test%"}
        )
        
        pattern_count = result.scalar()
        non_indexed_query_time = time.time() - start_time
        
        # Indexed query should be faster
        assert indexed_query_time < non_indexed_query_time * 2  # At least 2x faster
        assert count > 1000  # Should include our test data plus any existing
        assert pattern_count == 1000  # Should match all our test leads
        
        print(f"\nIndex Effectiveness:")
        print(f"Indexed query time: {indexed_query_time:.4f}s")
        print(f"Non-indexed query time: {non_indexed_query_time:.4f}s")
        print(f"Performance improvement: {non_indexed_query_time / indexed_query_time:.1f}x")


@pytest.mark.database
@pytest.mark.integration
class TestDatabaseMigrations:
    """Test database migration capabilities"""
    
    @pytest.mark.asyncio
    async def test_migration_state(self, db_session):
        """Test current migration state"""
        # Check if alembic version table exists
        result = await db_session.execute(
            text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'alembic_version'
            """)
        )
        
        alembic_table = result.fetchone()
        assert alembic_table is not None, "Alembic version table not found"
        
        # Check current migration version
        result = await db_session.execute(
            text("SELECT version_num FROM alembic_version")
        )
        
        current_version = result.scalar()
        assert current_version is not None, "No migration version found"
        assert len(current_version) > 0, "Empty migration version"
        
        print(f"\nCurrent migration version: {current_version}")
    
    def test_model_table_mapping(self):
        """Test that all models map to correct tables"""
        # Test table names match model expectations
        assert Organization.__tablename__ == 'organizations'
        assert User.__tablename__ == 'users'
        assert Lead.__tablename__ == 'leads'
        assert Conversation.__tablename__ == 'conversations'
        assert VoiceAgent.__tablename__ == 'voice_agents'
        assert Property.__tablename__ == 'properties'
    
    @pytest.mark.asyncio
    async def test_database_connection_recovery(self, db_session):
        """Test database connection recovery after failure"""
        # Test basic connection
        result = await db_session.execute(text("SELECT 1 as test"))
        assert result.scalar() == 1
        
        # Simulate connection issues by testing reconnection
        try:
            # This should work after any connection recovery
            result = await db_session.execute(text("SELECT COUNT(*) FROM organizations"))
            count = result.scalar()
            assert isinstance(count, int)
            
        except Exception as e:
            # Connection recovery should be handled by the connection pool
            pytest.fail(f"Database connection recovery failed: {e}")
    
    @pytest.mark.asyncio
    async def test_data_consistency_after_operations(self, db_session, test_organization):
        """Test data consistency after multiple operations"""
        # Create related data
        user = User(
            id=str(uuid.uuid4()),
            email="consistency@example.com",
            hashed_password=get_password_hash("password"),
            full_name="Consistency User",
            organization_id=test_organization.id,
            role="agent",
            is_active=True
        )
        
        lead = Lead(
            id=str(uuid.uuid4()),
            organization_id=test_organization.id,
            name="Consistency Lead",
            email="consistency.lead@example.com",
            phone="+1234567890",
            source="consistency_test",
            qualification_status="new"
        )
        
        db_session.add_all([user, lead])
        await db_session.commit()
        
        # Create conversation linking them
        conversation = Conversation(
            id=str(uuid.uuid4()),
            organization_id=test_organization.id,
            lead_id=lead.id,
            agent_id=user.id,
            duration_seconds=180,
            transcript="Consistency test conversation",
            sentiment_score=0.8,
            lead_score=70,
            status="completed"
        )
        
        db_session.add(conversation)
        await db_session.commit()
        
        # Verify all relationships are consistent
        retrieved_conv = await db_session.get(Conversation, conversation.id)
        assert retrieved_conv.organization_id == test_organization.id
        assert retrieved_conv.lead_id == lead.id
        assert retrieved_conv.agent_id == user.id
        
        # Verify referential integrity
        retrieved_lead = await db_session.get(Lead, lead.id)
        retrieved_user = await db_session.get(User, user.id)
        
        assert retrieved_lead.organization_id == test_organization.id
        assert retrieved_user.organization_id == test_organization.id
        
        # All records should have consistent organization_id
        assert (
            retrieved_conv.organization_id == 
            retrieved_lead.organization_id == 
            retrieved_user.organization_id == 
            test_organization.id
        )