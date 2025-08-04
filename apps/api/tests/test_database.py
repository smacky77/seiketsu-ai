"""
Comprehensive database and model tests
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import uuid
from app.models import User, Organization, Lead, Conversation, VoiceAgent, Property


class TestDatabaseModels:
    """Test database models and relationships"""
    
    @pytest.mark.asyncio
    async def test_organization_creation(self, db_session: AsyncSession):
        """Test organization model creation and constraints"""
        org = Organization(
            name="Test Real Estate Agency",
            subdomain="test-agency",
            settings={
                "max_agents": 50,
                "voice_minutes": 10000,
                "features": ["voice_ai", "lead_scoring", "market_intelligence"]
            },
            subscription_status="active",
            subscription_tier="enterprise"
        )
        
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)
        
        assert org.id is not None
        assert org.created_at is not None
        assert org.updated_at is not None
        assert org.subdomain == "test-agency"
        assert org.settings["max_agents"] == 50
        assert "voice_ai" in org.settings["features"]
    
    @pytest.mark.asyncio
    async def test_user_organization_relationship(self, db_session: AsyncSession, test_organization):
        """Test user-organization relationship"""
        user = User(
            email="agent@realestate.com",
            hashed_password="hashed_password_here",
            full_name="Test Agent",
            role="agent",
            organization_id=test_organization.id
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        # Test relationship
        assert user.organization_id == test_organization.id
        
        # Query with join
        result = await db_session.execute(
            select(User).options(selectinload(User.organization))
            .where(User.id == user.id)
        )
        loaded_user = result.scalar_one()
        assert loaded_user.organization.name == test_organization.name
    
    @pytest.mark.asyncio
    async def test_lead_model_constraints(self, db_session: AsyncSession, test_organization):
        """Test lead model with property preferences"""
        lead = Lead(
            organization_id=test_organization.id,
            name="John Buyer",
            email="buyer@example.com",
            phone="+1234567890",
            source="website",
            property_preferences={
                "type": "single_family",
                "min_price": 300000,
                "max_price": 500000,
                "bedrooms": 3,
                "bathrooms": 2,
                "location": "downtown",
                "features": ["garage", "pool"]
            },
            qualification_status="new",
            lead_score=0
        )
        
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)
        
        assert lead.property_preferences["min_price"] == 300000
        assert "garage" in lead.property_preferences["features"]
        assert lead.qualification_status == "new"
    
    @pytest.mark.asyncio
    async def test_conversation_lead_relationship(self, db_session: AsyncSession, 
                                               test_organization, test_lead, test_user):
        """Test conversation relationships with lead and agent"""
        conversation = Conversation(
            organization_id=test_organization.id,
            lead_id=test_lead.id,
            agent_id=test_user.id,
            duration_seconds=240,
            transcript="Hello, I'm interested in buying a home...",
            sentiment_score=0.82,
            lead_score=75,
            status="qualified",
            key_points=["Budget: $400k", "Needs 3 bedrooms", "Prefers downtown"],
            recording_url="https://storage.example.com/recording123.mp3"
        )
        
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)
        
        # Test relationships
        assert conversation.lead_id == test_lead.id
        assert conversation.agent_id == test_user.id
        assert len(conversation.key_points) == 3
        assert conversation.sentiment_score == 0.82
    
    @pytest.mark.asyncio
    async def test_voice_agent_configuration(self, db_session: AsyncSession, test_organization):
        """Test voice agent model with ElevenLabs configuration"""
        voice_agent = VoiceAgent(
            organization_id=test_organization.id,
            name="Sarah Professional",
            voice_id="elevenlabs_sarah_id",
            personality="professional_friendly",
            language="en-US",
            pitch=1.05,
            speed=0.95,
            script_template="real_estate_qualifier",
            greeting_message="Hello! I'm Sarah from Premier Real Estate. How can I help you today?",
            voice_settings={
                "stability": 0.75,
                "similarity_boost": 0.85,
                "style": "professional",
                "use_speaker_boost": True
            },
            is_active=True
        )
        
        db_session.add(voice_agent)
        await db_session.commit()
        await db_session.refresh(voice_agent)
        
        assert voice_agent.voice_settings["stability"] == 0.75
        assert voice_agent.personality == "professional_friendly"
        assert voice_agent.is_active is True
    
    @pytest.mark.asyncio
    async def test_property_listing_model(self, db_session: AsyncSession, test_organization):
        """Test property listing model with MLS data"""
        property = Property(
            organization_id=test_organization.id,
            mls_id="MLS2024-12345",
            address="123 Main Street, Downtown City, ST 12345",
            price=425000,
            original_price=450000,
            bedrooms=3,
            bathrooms=2.5,
            square_feet=2200,
            lot_size=0.25,
            year_built=2018,
            property_type="single_family",
            listing_status="active",
            features=["granite_counters", "hardwood_floors", "pool", "two_car_garage"],
            description="Beautiful modern home in prime downtown location...",
            images=[
                "https://storage.example.com/prop1/image1.jpg",
                "https://storage.example.com/prop1/image2.jpg"
            ],
            virtual_tour_url="https://tours.example.com/prop1",
            days_on_market=15
        )
        
        db_session.add(property)
        await db_session.commit()
        await db_session.refresh(property)
        
        assert property.price == 425000
        assert property.bathrooms == 2.5
        assert "pool" in property.features
        assert len(property.images) == 2


class TestDatabaseQueries:
    """Test complex database queries and filters"""
    
    @pytest.mark.asyncio
    async def test_multi_tenant_query_isolation(self, db_session: AsyncSession):
        """Test multi-tenant data isolation in queries"""
        # Create two organizations
        org1 = Organization(name="Agency 1", subdomain="agency1")
        org2 = Organization(name="Agency 2", subdomain="agency2")
        
        db_session.add_all([org1, org2])
        await db_session.commit()
        
        # Create leads for each organization
        lead1 = Lead(
            organization_id=org1.id,
            name="Org1 Lead",
            email="lead1@example.com"
        )
        lead2 = Lead(
            organization_id=org2.id,
            name="Org2 Lead",
            email="lead2@example.com"
        )
        
        db_session.add_all([lead1, lead2])
        await db_session.commit()
        
        # Query leads for org1 only
        from sqlalchemy import select
        result = await db_session.execute(
            select(Lead).where(Lead.organization_id == org1.id)
        )
        org1_leads = result.scalars().all()
        
        assert len(org1_leads) == 1
        assert org1_leads[0].name == "Org1 Lead"
        assert org1_leads[0].organization_id == org1.id
    
    @pytest.mark.asyncio
    async def test_conversation_analytics_query(self, db_session: AsyncSession, 
                                              test_organization):
        """Test complex analytics queries on conversations"""
        # Create multiple conversations with different scores
        conversations = []
        for i in range(10):
            conv = Conversation(
                organization_id=test_organization.id,
                lead_id=str(uuid.uuid4()),
                agent_id=str(uuid.uuid4()),
                duration_seconds=180 + (i * 30),
                sentiment_score=0.5 + (i * 0.05),
                lead_score=50 + (i * 5),
                status="qualified" if i >= 5 else "not_qualified",
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            conversations.append(conv)
        
        db_session.add_all(conversations)
        await db_session.commit()
        
        # Query average metrics
        from sqlalchemy import select, func
        result = await db_session.execute(
            select(
                func.avg(Conversation.duration_seconds).label("avg_duration"),
                func.avg(Conversation.sentiment_score).label("avg_sentiment"),
                func.avg(Conversation.lead_score).label("avg_lead_score"),
                func.count(Conversation.id).label("total_conversations")
            ).where(Conversation.organization_id == test_organization.id)
        )
        
        metrics = result.first()
        assert metrics.total_conversations == 10
        assert metrics.avg_duration > 180
        assert 0.5 < metrics.avg_sentiment < 1.0
        assert 50 < metrics.avg_lead_score < 100
    
    @pytest.mark.asyncio
    async def test_lead_search_with_filters(self, db_session: AsyncSession, 
                                          test_organization):
        """Test lead search with multiple filters"""
        # Create leads with different statuses and scores
        leads = [
            Lead(
                organization_id=test_organization.id,
                name=f"Lead {i}",
                email=f"lead{i}@example.com",
                qualification_status="qualified" if i % 2 == 0 else "not_qualified",
                lead_score=40 + (i * 10),
                source="website" if i < 5 else "phone",
                created_at=datetime.utcnow() - timedelta(days=i)
            )
            for i in range(10)
        ]
        
        db_session.add_all(leads)
        await db_session.commit()
        
        # Search qualified leads with score > 70
        from sqlalchemy import select, and_
        result = await db_session.execute(
            select(Lead).where(
                and_(
                    Lead.organization_id == test_organization.id,
                    Lead.qualification_status == "qualified",
                    Lead.lead_score > 70
                )
            ).order_by(Lead.lead_score.desc())
        )
        
        qualified_high_score_leads = result.scalars().all()
        assert len(qualified_high_score_leads) > 0
        assert all(lead.lead_score > 70 for lead in qualified_high_score_leads)
        assert all(lead.qualification_status == "qualified" for lead in qualified_high_score_leads)
    
    @pytest.mark.asyncio
    async def test_property_search_with_preferences(self, db_session: AsyncSession, 
                                                  test_organization):
        """Test property search matching lead preferences"""
        # Create properties with different characteristics
        properties = [
            Property(
                organization_id=test_organization.id,
                mls_id=f"MLS{i}",
                address=f"{i}00 Test St",
                price=300000 + (i * 50000),
                bedrooms=2 + (i % 3),
                bathrooms=1 + (i % 2),
                property_type="single_family" if i < 5 else "condo",
                listing_status="active"
            )
            for i in range(10)
        ]
        
        db_session.add_all(properties)
        await db_session.commit()
        
        # Search properties matching preferences
        min_price = 350000
        max_price = 500000
        min_bedrooms = 3
        property_type = "single_family"
        
        from sqlalchemy import select, and_
        result = await db_session.execute(
            select(Property).where(
                and_(
                    Property.organization_id == test_organization.id,
                    Property.price >= min_price,
                    Property.price <= max_price,
                    Property.bedrooms >= min_bedrooms,
                    Property.property_type == property_type,
                    Property.listing_status == "active"
                )
            ).order_by(Property.price)
        )
        
        matching_properties = result.scalars().all()
        assert all(min_price <= prop.price <= max_price for prop in matching_properties)
        assert all(prop.bedrooms >= min_bedrooms for prop in matching_properties)
        assert all(prop.property_type == property_type for prop in matching_properties)


class TestDatabaseTransactions:
    """Test database transactions and rollbacks"""
    
    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_session: AsyncSession, test_organization):
        """Test transaction rollback on error"""
        try:
            # Start transaction
            lead = Lead(
                organization_id=test_organization.id,
                name="Transaction Test Lead",
                email="transaction@example.com"
            )
            db_session.add(lead)
            
            # This should cause an error (duplicate email)
            duplicate_lead = Lead(
                organization_id=test_organization.id,
                name="Duplicate Lead",
                email="transaction@example.com"  # Same email
            )
            db_session.add(duplicate_lead)
            
            await db_session.commit()
        except Exception:
            await db_session.rollback()
        
        # Verify no leads were created
        from sqlalchemy import select
        result = await db_session.execute(
            select(Lead).where(Lead.email == "transaction@example.com")
        )
        leads = result.scalars().all()
        assert len(leads) == 0
    
    @pytest.mark.asyncio
    async def test_bulk_operations(self, db_session: AsyncSession, test_organization):
        """Test bulk insert and update operations"""
        # Bulk insert leads
        leads = [
            Lead(
                organization_id=test_organization.id,
                name=f"Bulk Lead {i}",
                email=f"bulk{i}@example.com",
                lead_score=50
            )
            for i in range(100)
        ]
        
        db_session.add_all(leads)
        await db_session.commit()
        
        # Verify all inserted
        from sqlalchemy import select, func
        count_result = await db_session.execute(
            select(func.count(Lead.id)).where(
                Lead.organization_id == test_organization.id,
                Lead.name.like("Bulk Lead%")
            )
        )
        assert count_result.scalar() == 100
        
        # Bulk update scores
        from sqlalchemy import update
        await db_session.execute(
            update(Lead)
            .where(Lead.organization_id == test_organization.id)
            .where(Lead.name.like("Bulk Lead%"))
            .values(lead_score=75)
        )
        await db_session.commit()
        
        # Verify updates
        result = await db_session.execute(
            select(Lead).where(
                Lead.organization_id == test_organization.id,
                Lead.name.like("Bulk Lead%")
            )
        )
        updated_leads = result.scalars().all()
        assert all(lead.lead_score == 75 for lead in updated_leads)


class TestDatabasePerformance:
    """Test database performance optimizations"""
    
    @pytest.mark.asyncio
    async def test_index_performance(self, db_session: AsyncSession, test_organization):
        """Test query performance with indexes"""
        import time
        
        # Create many conversations for performance testing
        conversations = []
        for i in range(1000):
            conv = Conversation(
                organization_id=test_organization.id,
                lead_id=str(uuid.uuid4()),
                agent_id=str(uuid.uuid4()),
                duration_seconds=180,
                lead_score=50 + (i % 50),
                status="qualified" if i % 3 == 0 else "not_qualified",
                created_at=datetime.utcnow() - timedelta(hours=i)
            )
            conversations.append(conv)
        
        db_session.add_all(conversations)
        await db_session.commit()
        
        # Test indexed query performance
        from sqlalchemy import select
        
        start_time = time.time()
        result = await db_session.execute(
            select(Conversation).where(
                Conversation.organization_id == test_organization.id,
                Conversation.status == "qualified"
            ).order_by(Conversation.created_at.desc())
            .limit(50)
        )
        qualified_convs = result.scalars().all()
        query_time = time.time() - start_time
        
        assert len(qualified_convs) == 50
        assert query_time < 0.1  # Query should be fast with indexes
    
    @pytest.mark.asyncio
    async def test_eager_loading_relationships(self, db_session: AsyncSession):
        """Test eager loading to prevent N+1 queries"""
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        # Create organization with users
        org = Organization(name="Test Org", subdomain="test")
        db_session.add(org)
        await db_session.commit()
        
        users = [
            User(
                email=f"user{i}@example.com",
                hashed_password="hash",
                full_name=f"User {i}",
                organization_id=org.id
            )
            for i in range(10)
        ]
        db_session.add_all(users)
        await db_session.commit()
        
        # Query with eager loading
        result = await db_session.execute(
            select(Organization)
            .options(selectinload(Organization.users))
            .where(Organization.id == org.id)
        )
        loaded_org = result.scalar_one()
        
        # Access users without additional queries
        assert len(loaded_org.users) == 10
        assert all(user.organization_id == org.id for user in loaded_org.users)