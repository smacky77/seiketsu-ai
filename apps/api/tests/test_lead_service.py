"""
Comprehensive unit tests for LeadService
Tests lead management, scoring, and business logic
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from app.services.lead_service import LeadService
from app.models.lead import Lead, LeadStatus, LeadSource
from app.models.conversation import Conversation


@pytest.mark.asyncio
@pytest.mark.unit
class TestLeadService:
    """Test suite for LeadService functionality"""

    @pytest.fixture
    async def lead_service(self):
        """Create LeadService instance with mocked dependencies"""
        with patch('app.services.lead_service.WebhookService') as mock_webhook, \
             patch('app.services.lead_service.AnalyticsService') as mock_analytics:
            
            mock_webhook.return_value = AsyncMock()
            mock_analytics.return_value = AsyncMock()
            
            service = LeadService()
            yield service

    @pytest.fixture
    def sample_lead_data(self):
        """Sample lead data for testing"""
        return {
            "first_name": "John",
            "last_name": "Smith",
            "email": "john.smith@example.com",
            "phone": "+1234567890",
            "budget_min": 300000,
            "budget_max": 500000,
            "timeline": "3_months",
            "property_type": "single_family",
            "bedrooms": 3,
            "bathrooms": 2,
            "location": "downtown",
            "notes": "Looking for move-in ready home"
        }

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    async def test_create_lead_from_conversation_success(self, lead_service, sample_lead_data, mock_db_session, test_organization):
        """Test successful lead creation from conversation"""
        conversation_id = "test_conv_id"
        organization_id = test_organization.id
        
        # Mock Lead creation
        with patch('app.services.lead_service.Lead') as mock_lead_class:
            mock_lead = Mock(spec=Lead)
            mock_lead.id = "new_lead_id"
            mock_lead.lead_score = 75
            mock_lead.update_lead_score = Mock()
            mock_lead_class.return_value = mock_lead
            
            result = await lead_service.create_lead_from_conversation(
                conversation_id, sample_lead_data, organization_id, mock_db_session
            )
            
            # Verify lead creation
            mock_lead_class.assert_called_once()
            call_kwargs = mock_lead_class.call_args.kwargs
            assert call_kwargs["first_name"] == "John"
            assert call_kwargs["last_name"] == "Smith"
            assert call_kwargs["email"] == "john.smith@example.com"
            assert call_kwargs["organization_id"] == organization_id
            assert call_kwargs["conversation_id"] == conversation_id
            assert call_kwargs["source"] == LeadSource.VOICE_CALL
            assert call_kwargs["status"] == LeadStatus.NEW
            
            # Verify database operations
            mock_db_session.add.assert_called_once_with(mock_lead)
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once_with(mock_lead)
            
            # Verify lead scoring
            mock_lead.update_lead_score.assert_called_once()
            
            assert result == mock_lead

    async def test_create_lead_qualified_status(self, lead_service, sample_lead_data, mock_db_session, test_organization):
        """Test lead creation with qualified status based on score"""
        with patch('app.services.lead_service.Lead') as mock_lead_class:
            mock_lead = Mock(spec=Lead)
            mock_lead.lead_score = 65  # High score
            mock_lead.update_lead_score = Mock()
            mock_lead_class.return_value = mock_lead
            
            await lead_service.create_lead_from_conversation(
                "conv_id", sample_lead_data, test_organization.id, mock_db_session
            )
            
            # Should set status to qualified for high score
            assert mock_lead.status == LeadStatus.QUALIFIED

    async def test_create_lead_error_handling(self, lead_service, sample_lead_data, test_organization):
        """Test error handling in lead creation"""
        with patch('app.services.lead_service.Lead', side_effect=Exception("Database error")):
            with pytest.raises(Exception, match="Database error"):
                await lead_service.create_lead_from_conversation(
                    "conv_id", sample_lead_data, test_organization.id, None
                )

    async def test_get_lead_success(self, lead_service, mock_db_session):
        """Test successful lead retrieval"""
        lead_id = "test_lead_id"
        mock_lead = Mock(spec=Lead)
        mock_lead.id = lead_id
        
        # Mock database result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_lead
        mock_db_session.execute.return_value = mock_result
        
        result = await lead_service.get_lead(lead_id, mock_db_session)
        
        assert result == mock_lead
        mock_db_session.execute.assert_called_once()

    async def test_get_lead_not_found(self, lead_service, mock_db_session):
        """Test lead retrieval when lead doesn't exist"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        result = await lead_service.get_lead("nonexistent_id", mock_db_session)
        
        assert result is None

    async def test_get_lead_database_error(self, lead_service, mock_db_session):
        """Test lead retrieval with database error"""
        mock_db_session.execute.side_effect = Exception("DB connection failed")
        
        result = await lead_service.get_lead("test_id", mock_db_session)
        
        assert result is None  # Should handle error gracefully

    async def test_get_leads_for_organization_basic(self, lead_service, mock_db_session, test_organization):
        """Test basic lead retrieval for organization"""
        mock_leads = [Mock(spec=Lead), Mock(spec=Lead)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_leads
        mock_db_session.execute.return_value = mock_result
        
        result = await lead_service.get_leads_for_organization(
            test_organization.id, mock_db_session
        )
        
        assert result == mock_leads
        mock_db_session.execute.assert_called_once()

    async def test_get_leads_with_filters(self, lead_service, mock_db_session, test_organization):
        """Test lead retrieval with status and source filters"""
        mock_leads = [Mock(spec=Lead)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_leads
        mock_db_session.execute.return_value = mock_result
        
        result = await lead_service.get_leads_for_organization(
            test_organization.id,
            mock_db_session,
            status_filter=LeadStatus.QUALIFIED,
            source_filter=LeadSource.VOICE_CALL,
            limit=10,
            offset=0
        )
        
        assert result == mock_leads

    async def test_get_leads_with_search(self, lead_service, mock_db_session, test_organization):
        """Test lead retrieval with search query"""
        search_query = "john smith"
        mock_leads = [Mock(spec=Lead)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_leads
        mock_db_session.execute.return_value = mock_result
        
        result = await lead_service.get_leads_for_organization(
            test_organization.id,
            mock_db_session,
            search_query=search_query
        )
        
        assert result == mock_leads

    async def test_update_lead_status_success(self, lead_service, mock_db_session):
        """Test successful lead status update"""
        lead_id = "test_lead_id"
        new_status = LeadStatus.QUALIFIED
        notes = "Qualified during phone call"
        user_id = "agent_user_id"
        
        # Mock existing lead
        mock_lead = Mock(spec=Lead)
        mock_lead.id = lead_id
        mock_lead.status = LeadStatus.NEW
        mock_lead.notes = "Initial contact"
        mock_lead.organization_id = "org_id"
        mock_lead.updated_at = datetime.utcnow()
        
        with patch.object(lead_service, 'get_lead', return_value=mock_lead):
            result = await lead_service.update_lead_status(
                lead_id, new_status, mock_db_session, notes, user_id
            )
            
            # Verify status update
            assert mock_lead.status == new_status
            assert mock_lead.updated_by == user_id
            assert notes in mock_lead.notes
            
            # Verify database commit
            mock_db_session.commit.assert_called_once()
            
            # Verify webhook and analytics calls
            lead_service.webhook_service.send_webhook.assert_called_once()
            lead_service.analytics_service.track_event.assert_called_once()
            
            assert result == mock_lead

    async def test_update_lead_status_not_found(self, lead_service, mock_db_session):
        """Test lead status update when lead doesn't exist"""
        with patch.object(lead_service, 'get_lead', return_value=None):
            result = await lead_service.update_lead_status(
                "nonexistent_id", LeadStatus.QUALIFIED, mock_db_session
            )
            
            assert result is None

    async def test_assign_lead_to_agent_success(self, lead_service, mock_db_session):
        """Test successful lead assignment to agent"""
        lead_id = "test_lead_id"
        agent_user_id = "agent_123"
        assigned_by_user_id = "manager_456"
        
        mock_lead = Mock(spec=Lead)
        mock_lead.id = lead_id
        mock_lead.assigned_agent_id = None
        mock_lead.notes = "Initial notes"
        mock_lead.organization_id = "org_id"
        
        with patch.object(lead_service, 'get_lead', return_value=mock_lead):
            result = await lead_service.assign_lead_to_agent(
                lead_id, agent_user_id, mock_db_session, assigned_by_user_id
            )
            
            # Verify assignment
            assert mock_lead.assigned_agent_id == agent_user_id
            assert mock_lead.updated_by == assigned_by_user_id
            assert "assigned to agent" in mock_lead.notes.lower()
            
            # Verify webhook notification
            lead_service.webhook_service.send_webhook.assert_called_once()
            
            assert result == mock_lead

    async def test_assign_lead_reassignment(self, lead_service, mock_db_session):
        """Test lead reassignment from one agent to another"""
        mock_lead = Mock(spec=Lead)
        mock_lead.assigned_agent_id = "old_agent_123"
        mock_lead.notes = "Previous notes"
        
        with patch.object(lead_service, 'get_lead', return_value=mock_lead):
            await lead_service.assign_lead_to_agent(
                "lead_id", "new_agent_456", mock_db_session
            )
            
            # Should indicate reassignment in notes
            assert "reassigned from" in mock_lead.notes.lower()
            assert mock_lead.assigned_agent_id == "new_agent_456"

    async def test_update_lead_contact_info_success(self, lead_service, mock_db_session):
        """Test successful lead contact information update"""
        lead_id = "test_lead_id"
        contact_data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.com",
            "phone": "+0987654321",
            "city": "New York",
            "state": "NY"
        }
        
        mock_lead = Mock(spec=Lead)
        mock_lead.id = lead_id
        mock_lead.update_lead_score = Mock()
        
        with patch.object(lead_service, 'get_lead', return_value=mock_lead):
            result = await lead_service.update_lead_contact_info(
                lead_id, contact_data, mock_db_session, "user_id"
            )
            
            # Verify contact info updates
            assert mock_lead.first_name == "Jane"
            assert mock_lead.last_name == "Doe"
            assert mock_lead.email == "jane.doe@example.com"
            assert mock_lead.phone == "+0987654321"
            assert mock_lead.city == "New York"
            assert mock_lead.state == "NY"
            assert mock_lead.updated_by == "user_id"
            
            # Verify lead score recalculation
            mock_lead.update_lead_score.assert_called_once()
            
            # Verify database commit
            mock_db_session.commit.assert_called_once()
            
            assert result == mock_lead

    async def test_add_lead_note_success(self, lead_service, mock_db_session):
        """Test successful note addition to lead"""
        lead_id = "test_lead_id"
        note = "Follow-up call scheduled for tomorrow"
        user_id = "agent_123"
        
        mock_lead = Mock(spec=Lead)
        mock_lead.id = lead_id
        mock_lead.notes = "Previous notes"
        
        with patch.object(lead_service, 'get_lead', return_value=mock_lead):
            result = await lead_service.add_lead_note(
                lead_id, note, mock_db_session, user_id
            )
            
            # Verify note addition
            assert note in mock_lead.notes
            assert user_id in mock_lead.notes
            assert "Previous notes" in mock_lead.notes  # Should preserve existing
            
            # Verify database commit
            mock_db_session.commit.assert_called_once()
            
            assert result == mock_lead

    async def test_get_hot_leads_success(self, lead_service, mock_db_session, test_organization):
        """Test hot leads retrieval"""
        # Mock leads with different scores
        mock_lead1 = Mock(spec=Lead)
        mock_lead1.is_hot_lead = True
        mock_lead1.lead_score = 85
        
        mock_lead2 = Mock(spec=Lead)
        mock_lead2.is_hot_lead = False
        mock_lead2.lead_score = 45
        
        mock_lead3 = Mock(spec=Lead)
        mock_lead3.is_hot_lead = True
        mock_lead3.lead_score = 90
        
        all_leads = [mock_lead1, mock_lead2, mock_lead3]
        
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = all_leads
        mock_db_session.execute.return_value = mock_result
        
        result = await lead_service.get_hot_leads(
            test_organization.id, mock_db_session, limit=20
        )
        
        # Should only return hot leads
        assert len(result) == 2
        assert mock_lead1 in result
        assert mock_lead3 in result
        assert mock_lead2 not in result

    async def test_get_leads_needing_follow_up(self, lead_service, mock_db_session, test_organization):
        """Test retrieval of leads needing follow-up"""
        mock_leads = [Mock(spec=Lead), Mock(spec=Lead)]
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_leads
        mock_db_session.execute.return_value = mock_result
        
        result = await lead_service.get_leads_needing_follow_up(
            test_organization.id, mock_db_session, limit=50
        )
        
        assert result == mock_leads
        mock_db_session.execute.assert_called_once()

    async def test_bulk_update_lead_tags_success(self, lead_service, mock_db_session):
        """Test bulk tag updates for multiple leads"""
        lead_ids = ["lead1", "lead2", "lead3"]
        tags_to_add = ["high_priority", "qualified"]
        tags_to_remove = ["unqualified"]
        user_id = "manager_123"
        
        # Mock leads
        mock_leads = []
        for i, lead_id in enumerate(lead_ids):
            mock_lead = Mock(spec=Lead)
            mock_lead.id = lead_id
            mock_lead.tags = ["existing_tag", "unqualified"] if i == 0 else ["other_tag"]
            mock_leads.append(mock_lead)
        
        def get_lead_side_effect(lead_id, db_session):
            for lead in mock_leads:
                if lead.id == lead_id:
                    return lead
            return None
        
        with patch.object(lead_service, 'get_lead', side_effect=get_lead_side_effect):
            updated_count = await lead_service.bulk_update_lead_tags(
                lead_ids, tags_to_add, tags_to_remove, mock_db_session, user_id
            )
            
            assert updated_count == 3
            
            # Verify tag updates
            for mock_lead in mock_leads:
                assert "high_priority" in mock_lead.tags
                assert "qualified" in mock_lead.tags
                assert "unqualified" not in mock_lead.tags
                assert mock_lead.updated_by == user_id
            
            # Verify database commit
            mock_db_session.commit.assert_called_once()

    async def test_bulk_update_lead_tags_partial_success(self, lead_service, mock_db_session):
        """Test bulk tag updates with some leads not found"""
        lead_ids = ["lead1", "nonexistent_lead", "lead3"]
        tags_to_add = ["new_tag"]
        tags_to_remove = []
        
        def get_lead_side_effect(lead_id, db_session):
            if lead_id == "nonexistent_lead":
                return None
            mock_lead = Mock(spec=Lead)
            mock_lead.id = lead_id
            mock_lead.tags = []
            return mock_lead
        
        with patch.object(lead_service, 'get_lead', side_effect=get_lead_side_effect):
            updated_count = await lead_service.bulk_update_lead_tags(
                lead_ids, tags_to_add, tags_to_remove, mock_db_session
            )
            
            assert updated_count == 2  # Only 2 leads found and updated

    async def test_bulk_update_lead_tags_error_handling(self, lead_service, mock_db_session):
        """Test error handling in bulk tag updates"""
        with patch.object(lead_service, 'get_lead', side_effect=Exception("DB error")):
            updated_count = await lead_service.bulk_update_lead_tags(
                ["lead1"], ["tag"], [], mock_db_session
            )
            
            assert updated_count == 0  # No leads updated due to error


@pytest.mark.asyncio
@pytest.mark.integration
class TestLeadServiceIntegration:
    """Integration tests for LeadService with database"""
    
    async def test_full_lead_lifecycle_integration(self, db_session, test_organization, test_conversation):
        """Test complete lead lifecycle from creation to qualification"""
        lead_service = LeadService()
        
        # Create lead from conversation
        lead_data = {
            "first_name": "Integration",
            "last_name": "Test",
            "email": "integration@test.com",
            "phone": "+1111111111",
            "budget_min": 200000,
            "budget_max": 400000,
            "timeline": "6_months",
            "property_type": "condo",
            "bedrooms": 2
        }
        
        # Mock webhook and analytics services
        with patch.object(lead_service, 'webhook_service'), \
             patch.object(lead_service, 'analytics_service'):
            
            # Create lead
            lead = await lead_service.create_lead_from_conversation(
                test_conversation.id, lead_data, test_organization.id, db_session
            )
            
            assert lead is not None
            assert lead.first_name == "Integration"
            assert lead.email == "integration@test.com"
            assert lead.organization_id == test_organization.id
            
            # Retrieve lead
            retrieved_lead = await lead_service.get_lead(lead.id, db_session)
            assert retrieved_lead.id == lead.id
            
            # Update status
            updated_lead = await lead_service.update_lead_status(
                lead.id, LeadStatus.CONTACTED, db_session,
                notes="Made initial contact", updated_by_user_id="agent_123"
            )
            
            assert updated_lead.status == LeadStatus.CONTACTED
            assert "Made initial contact" in updated_lead.notes
            
            # Assign to agent
            assigned_lead = await lead_service.assign_lead_to_agent(
                lead.id, "agent_456", db_session, "manager_789"
            )
            
            assert assigned_lead.assigned_agent_id == "agent_456"
            
            # Add note
            noted_lead = await lead_service.add_lead_note(
                lead.id, "Scheduled property viewing", db_session, "agent_456"
            )
            
            assert "Scheduled property viewing" in noted_lead.notes

    async def test_lead_search_integration(self, db_session, test_organization):
        """Test lead search functionality with real database"""
        lead_service = LeadService()
        
        # Create test leads with different attributes
        test_leads_data = [
            {
                "first_name": "John", "last_name": "Smith",
                "email": "john.smith@example.com", "phone": "+1111111111",
                "status": LeadStatus.NEW, "source": LeadSource.VOICE_CALL
            },
            {
                "first_name": "Jane", "last_name": "Doe",
                "email": "jane.doe@example.com", "phone": "+2222222222",
                "status": LeadStatus.QUALIFIED, "source": LeadSource.WEBSITE
            },
            {
                "first_name": "Bob", "last_name": "Johnson",
                "email": "bob.johnson@example.com", "phone": "+3333333333",
                "status": LeadStatus.NEW, "source": LeadSource.VOICE_CALL
            }
        ]
        
        created_leads = []
        for lead_data in test_leads_data:
            lead = Lead(
                organization_id=test_organization.id,
                first_name=lead_data["first_name"],
                last_name=lead_data["last_name"],
                email=lead_data["email"],
                phone=lead_data["phone"],
                status=lead_data["status"],
                source=lead_data["source"],
                created_at=datetime.utcnow()
            )
            db_session.add(lead)
            created_leads.append(lead)
        
        await db_session.commit()
        
        # Test basic retrieval
        all_leads = await lead_service.get_leads_for_organization(
            test_organization.id, db_session
        )
        assert len(all_leads) >= 3
        
        # Test status filter
        qualified_leads = await lead_service.get_leads_for_organization(
            test_organization.id, db_session, status_filter=LeadStatus.QUALIFIED
        )
        assert len(qualified_leads) >= 1
        qualified_emails = [lead.email for lead in qualified_leads]
        assert "jane.doe@example.com" in qualified_emails
        
        # Test source filter
        voice_leads = await lead_service.get_leads_for_organization(
            test_organization.id, db_session, source_filter=LeadSource.VOICE_CALL
        )
        assert len(voice_leads) >= 2
        
        # Test search query
        search_results = await lead_service.get_leads_for_organization(
            test_organization.id, db_session, search_query="john"
        )
        # Should find both John Smith and Bob Johnson
        assert len(search_results) >= 2

    @pytest.mark.performance
    async def test_lead_service_performance(self, db_session, test_organization):
        """Test LeadService performance with multiple operations"""
        lead_service = LeadService()
        
        # Mock external services to focus on database performance
        with patch.object(lead_service, 'webhook_service'), \
             patch.object(lead_service, 'analytics_service'):
            
            # Create multiple leads quickly
            start_time = time.time()
            
            lead_creation_tasks = []
            for i in range(10):
                lead_data = {
                    "first_name": f"Test{i}",
                    "last_name": "User",
                    "email": f"test{i}@example.com",
                    "phone": f"+123456{i:04d}"
                }
                
                task = lead_service.create_lead_from_conversation(
                    f"conv_{i}", lead_data, test_organization.id, db_session
                )
                lead_creation_tasks.append(task)
            
            # Create all leads
            created_leads = await asyncio.gather(*lead_creation_tasks)
            creation_time = time.time() - start_time
            
            assert len(created_leads) == 10
            assert creation_time < 5.0, f"Lead creation took too long: {creation_time}s"
            
            # Test bulk retrieval performance
            start_time = time.time()
            all_leads = await lead_service.get_leads_for_organization(
                test_organization.id, db_session, limit=100
            )
            retrieval_time = time.time() - start_time
            
            assert len(all_leads) >= 10
            assert retrieval_time < 1.0, f"Lead retrieval took too long: {retrieval_time}s"
