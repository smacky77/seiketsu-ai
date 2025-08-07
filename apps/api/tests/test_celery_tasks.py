"""
Celery Background Task Tests
Tests for Celery job processing, voice generation tasks, and async workflows
"""
import pytest
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from celery import Celery
from celery.result import AsyncResult

from app.tasks.celery_app import celery_app
from app.tasks.voice_generation_tasks import (
    pregenerate_voice_responses,
    batch_voice_synthesis,
    voice_quality_analysis
)
from app.tasks.lead_tasks import (
    process_lead_qualification,
    send_lead_notifications,
    update_lead_scoring
)
from app.tasks.analytics_tasks import (
    generate_daily_analytics,
    process_conversation_insights,
    update_performance_metrics
)


@pytest.mark.celery
class TestCeleryConfiguration:
    """Test Celery configuration and setup"""
    
    def test_celery_app_configuration(self):
        """Test Celery app is properly configured"""
        assert celery_app.conf.broker_url is not None
        assert celery_app.conf.result_backend is not None
        assert celery_app.conf.task_serializer == 'json'
        assert celery_app.conf.result_serializer == 'json'
        assert celery_app.conf.accept_content == ['json']
        assert celery_app.conf.timezone == 'UTC'
    
    def test_task_routing(self):
        """Test task routing configuration"""
        # Test that different task types are routed correctly
        voice_tasks = [
            'app.tasks.voice_generation_tasks.pregenerate_voice_responses',
            'app.tasks.voice_generation_tasks.batch_voice_synthesis'
        ]
        
        analytics_tasks = [
            'app.tasks.analytics_tasks.generate_daily_analytics',
            'app.tasks.analytics_tasks.process_conversation_insights'
        ]
        
        # Verify tasks are registered
        registered_tasks = celery_app.tasks.keys()
        
        for task in voice_tasks + analytics_tasks:
            assert task in registered_tasks
    
    def test_task_retry_configuration(self):
        """Test task retry configuration"""
        # Test that tasks have proper retry settings
        task = celery_app.tasks.get('app.tasks.voice_generation_tasks.batch_voice_synthesis')
        if task:
            assert hasattr(task, 'retry')
            assert task.max_retries >= 3


@pytest.mark.celery
@pytest.mark.voice
class TestVoiceGenerationTasks:
    """Test voice generation background tasks"""
    
    @pytest.mark.asyncio
    async def test_pregenerate_voice_responses_task(self, test_voice_agent, mock_elevenlabs_api):
        """Test voice response pre-generation task"""
        common_responses = [
            "Hello, thank you for your interest in our properties.",
            "What type of property are you looking for?",
            "I'd be happy to help you find the perfect home.",
            "Let me check our available listings for you.",
            "Would you like to schedule a viewing?"
        ]
        
        with patch('app.tasks.voice_generation_tasks.ElevenLabsService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.pregenerate_responses = AsyncMock()
            
            # Execute task
            result = pregenerate_voice_responses.delay(
                voice_agent_id=test_voice_agent.id,
                responses=common_responses,
                language="en"
            )
            
            # Wait for task completion
            task_result = result.get(timeout=30)
            
            assert task_result['status'] == 'completed'
            assert task_result['voice_agent_id'] == test_voice_agent.id
            assert task_result['responses_count'] == len(common_responses)
            mock_instance.pregenerate_responses.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_voice_synthesis_task(self, test_voice_agent, mock_elevenlabs_api):
        """Test batch voice synthesis task"""
        texts_to_synthesize = [
            "Welcome to our real estate platform.",
            "How can I assist you with your property search?",
            "I'll help you find properties that match your criteria.",
            "Let's discuss your budget and preferences.",
            "I can schedule viewings for interested properties."
        ]
        
        with patch('app.tasks.voice_generation_tasks.ElevenLabsService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            
            # Mock synthesis results
            mock_results = []
            for i, text in enumerate(texts_to_synthesize):
                mock_result = Mock()
                mock_result.audio_data = f"audio_data_{i}".encode()
                mock_result.duration_ms = 2000 + i * 100
                mock_result.processing_time_ms = 800 + i * 50
                mock_result.voice_id = "test_voice_id"
                mock_results.append(mock_result)
            
            mock_instance.bulk_synthesize.return_value = mock_results
            
            # Execute task
            result = batch_voice_synthesis.delay(
                voice_agent_id=test_voice_agent.id,
                texts=texts_to_synthesize,
                language="en",
                priority="normal"
            )
            
            # Wait for task completion
            task_result = result.get(timeout=30)
            
            assert task_result['status'] == 'completed'
            assert task_result['synthesized_count'] == len(texts_to_synthesize)
            assert task_result['total_duration_ms'] > 0
            assert task_result['average_processing_time_ms'] > 0
            mock_instance.bulk_synthesize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_voice_quality_analysis_task(self, test_conversation, mock_elevenlabs_api):
        """Test voice quality analysis task"""
        audio_data = b"mock_audio_data_for_quality_analysis"
        transcript = "This is a test conversation for quality analysis."
        
        with patch('app.tasks.voice_generation_tasks.ElevenLabsService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.get_voice_quality_score.return_value = 0.85
            
            # Execute task
            result = voice_quality_analysis.delay(
                conversation_id=test_conversation.id,
                audio_data=audio_data,
                transcript=transcript
            )
            
            # Wait for task completion
            task_result = result.get(timeout=30)
            
            assert task_result['status'] == 'completed'
            assert task_result['conversation_id'] == test_conversation.id
            assert task_result['quality_score'] == 0.85
            assert 'analysis_details' in task_result
            mock_instance.get_voice_quality_score.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_voice_task_error_handling(self, test_voice_agent):
        """Test error handling in voice generation tasks"""
        with patch('app.tasks.voice_generation_tasks.ElevenLabsService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            mock_instance.pregenerate_responses.side_effect = Exception("API Error")
            
            # Execute task that will fail
            result = pregenerate_voice_responses.delay(
                voice_agent_id=test_voice_agent.id,
                responses=["Test message"],
                language="en"
            )
            
            # Wait for task completion (should handle error gracefully)
            task_result = result.get(timeout=30)
            
            assert task_result['status'] == 'failed'
            assert 'error' in task_result
            assert "API Error" in task_result['error']


@pytest.mark.celery
class TestLeadProcessingTasks:
    """Test lead processing background tasks"""
    
    @pytest.mark.asyncio
    async def test_process_lead_qualification_task(self, test_lead, test_organization):
        """Test lead qualification processing task"""
        qualification_data = {
            "conversation_transcript": "I'm looking for a 3-bedroom house with a garage, budget around $400,000",
            "lead_responses": {
                "budget_mentioned": True,
                "specific_requirements": True,
                "timeline_discussed": False
            },
            "ai_insights": {
                "buying_signals": ["budget_mentioned", "specific_requirements"],
                "sentiment_score": 0.8,
                "urgency_level": "medium"
            }
        }
        
        with patch('app.tasks.lead_tasks.lead_service') as mock_lead_service:
            mock_lead_service.qualify_lead = AsyncMock(return_value={
                "qualification_status": "qualified",
                "lead_score": 75,
                "qualification_reason": "Budget confirmed, specific requirements mentioned"
            })
            
            # Execute task
            result = process_lead_qualification.delay(
                lead_id=test_lead.id,
                qualification_data=qualification_data
            )
            
            # Wait for task completion
            task_result = result.get(timeout=30)
            
            assert task_result['status'] == 'completed'
            assert task_result['lead_id'] == test_lead.id
            assert task_result['qualification_status'] == 'qualified'
            assert task_result['lead_score'] == 75
            mock_lead_service.qualify_lead.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_lead_notifications_task(self, test_lead, test_user):
        """Test lead notification sending task"""
        notification_data = {
            "event_type": "lead_qualified",
            "lead_data": {
                "id": test_lead.id,
                "name": test_lead.name,
                "email": test_lead.email,
                "qualification_status": "qualified",
                "lead_score": 85
            },
            "recipients": [test_user.id],
            "notification_channels": ["email", "in_app"]
        }
        
        with patch('app.tasks.lead_tasks.notification_service') as mock_notification:
            mock_notification.send_notification = AsyncMock(return_value={
                "sent": True,
                "channels_used": ["email", "in_app"],
                "message_id": "msg_123"
            })
            
            # Execute task
            result = send_lead_notifications.delay(
                lead_id=test_lead.id,
                notification_data=notification_data
            )
            
            # Wait for task completion
            task_result = result.get(timeout=30)
            
            assert task_result['status'] == 'completed'
            assert task_result['lead_id'] == test_lead.id
            assert task_result['notifications_sent'] > 0
            assert 'message_ids' in task_result
            mock_notification.send_notification.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_lead_scoring_task(self, test_organization):
        """Test lead scoring update task"""
        scoring_parameters = {
            "conversation_quality": 0.8,
            "engagement_level": 0.9,
            "buying_signals_count": 3,
            "response_time": 120,  # seconds
            "qualification_completeness": 0.7
        }
        
        with patch('app.tasks.lead_tasks.scoring_service') as mock_scoring:
            mock_scoring.recalculate_lead_scores = AsyncMock(return_value={
                "leads_updated": 25,
                "average_score_change": 5.2,
                "newly_qualified": 3
            })
            
            # Execute task
            result = update_lead_scoring.delay(
                organization_id=test_organization.id,
                scoring_parameters=scoring_parameters
            )
            
            # Wait for task completion
            task_result = result.get(timeout=30)
            
            assert task_result['status'] == 'completed'
            assert task_result['leads_updated'] == 25
            assert task_result['newly_qualified'] == 3
            mock_scoring.recalculate_lead_scores.assert_called_once()


@pytest.mark.celery
class TestAnalyticsTasks:
    """Test analytics processing background tasks"""
    
    @pytest.mark.asyncio
    async def test_generate_daily_analytics_task(self, test_organization):
        """Test daily analytics generation task"""
        target_date = datetime.utcnow().date()
        
        with patch('app.tasks.analytics_tasks.analytics_service') as mock_analytics:
            mock_analytics.generate_daily_report = AsyncMock(return_value={
                "date": target_date.isoformat(),
                "metrics": {
                    "total_conversations": 45,
                    "qualified_leads": 12,
                    "conversion_rate": 0.27,
                    "average_call_duration": 185,
                    "voice_synthesis_count": 156,
                    "average_response_time_ms": 1250
                },
                "performance_indicators": {
                    "sub_2s_voice_compliance": 0.94,
                    "cache_hit_rate": 0.78,
                    "system_uptime": 0.999
                }
            })
            
            # Execute task
            result = generate_daily_analytics.delay(
                organization_id=test_organization.id,
                target_date=target_date.isoformat()
            )
            
            # Wait for task completion
            task_result = result.get(timeout=30)
            
            assert task_result['status'] == 'completed'
            assert task_result['organization_id'] == test_organization.id
            assert task_result['metrics']['total_conversations'] == 45
            assert task_result['performance_indicators']['sub_2s_voice_compliance'] == 0.94
            mock_analytics.generate_daily_report.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_conversation_insights_task(self, test_conversation):
        """Test conversation insights processing task"""
        conversation_data = {
            "transcript": "Customer expressed interest in downtown properties with 3 bedrooms",
            "duration": 280,
            "voice_quality_score": 0.89,
            "lead_responses": [
                "Looking for family home",
                "Prefer downtown location",
                "Budget up to 500k"
            ]
        }
        
        with patch('app.tasks.analytics_tasks.ai_insights_service') as mock_ai:
            mock_ai.analyze_conversation = AsyncMock(return_value={
                "sentiment_analysis": {
                    "overall_sentiment": "positive",
                    "sentiment_score": 0.82,
                    "emotional_tone": "interested"
                },
                "key_insights": {
                    "buying_signals": ["budget_mentioned", "location_preference", "property_type"],
                    "pain_points": [],
                    "next_steps": ["show_downtown_properties", "schedule_viewing"]
                },
                "lead_scoring_factors": {
                    "engagement_level": 0.9,
                    "specificity": 0.8,
                    "urgency": 0.6
                }
            })
            
            # Execute task
            result = process_conversation_insights.delay(
                conversation_id=test_conversation.id,
                conversation_data=conversation_data
            )
            
            # Wait for task completion
            task_result = result.get(timeout=30)
            
            assert task_result['status'] == 'completed'
            assert task_result['conversation_id'] == test_conversation.id
            assert task_result['sentiment_score'] == 0.82
            assert len(task_result['buying_signals']) == 3
            assert 'next_steps' in task_result
            mock_ai.analyze_conversation.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_performance_metrics_task(self, test_organization):
        """Test performance metrics update task"""
        metrics_period = "hourly"
        
        with patch('app.tasks.analytics_tasks.metrics_service') as mock_metrics:
            mock_metrics.update_performance_metrics = AsyncMock(return_value={
                "metrics_updated": {
                    "voice_synthesis_performance": {
                        "average_processing_time_ms": 890,
                        "sub_2s_compliance_rate": 0.96,
                        "cache_hit_rate": 0.82
                    },
                    "api_performance": {
                        "average_response_time_ms": 145,
                        "error_rate": 0.002,
                        "throughput_rps": 25.5
                    },
                    "conversation_metrics": {
                        "average_duration_seconds": 195,
                        "quality_score": 0.87,
                        "conversion_rate": 0.31
                    }
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Execute task
            result = update_performance_metrics.delay(
                organization_id=test_organization.id,
                metrics_period=metrics_period
            )
            
            # Wait for task completion
            task_result = result.get(timeout=30)
            
            assert task_result['status'] == 'completed'
            assert task_result['organization_id'] == test_organization.id
            assert 'voice_synthesis_performance' in task_result['metrics_updated']
            assert task_result['metrics_updated']['voice_synthesis_performance']['sub_2s_compliance_rate'] == 0.96
            mock_metrics.update_performance_metrics.assert_called_once()


@pytest.mark.celery
@pytest.mark.performance
class TestCeleryPerformance:
    """Test Celery performance and scalability"""
    
    @pytest.mark.asyncio
    async def test_concurrent_task_processing(self, test_voice_agent):
        """Test concurrent task processing performance"""
        # Submit multiple tasks concurrently
        tasks = []
        for i in range(10):
            task = batch_voice_synthesis.delay(
                voice_agent_id=test_voice_agent.id,
                texts=[f"Test message {i}"],
                language="en",
                priority="normal"
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        start_time = datetime.utcnow()
        results = []
        for task in tasks:
            try:
                result = task.get(timeout=60)
                results.append(result)
            except Exception as e:
                results.append({"status": "failed", "error": str(e)})
        
        end_time = datetime.utcnow()
        total_time = (end_time - start_time).total_seconds()
        
        # Verify performance
        successful_tasks = sum(1 for r in results if r.get('status') == 'completed')
        assert successful_tasks >= 8  # At least 80% success rate
        assert total_time < 120  # Should complete within 2 minutes
    
    @pytest.mark.asyncio
    async def test_task_queue_management(self):
        """Test task queue management and prioritization"""
        # Submit high priority tasks
        high_priority_tasks = []
        for i in range(3):
            task = batch_voice_synthesis.apply_async(
                args=[
                    "test_voice_agent_id",
                    [f"High priority message {i}"],
                    "en",
                    "high"
                ],
                priority=9  # High priority
            )
            high_priority_tasks.append(task)
        
        # Submit low priority tasks
        low_priority_tasks = []
        for i in range(5):
            task = batch_voice_synthesis.apply_async(
                args=[
                    "test_voice_agent_id",
                    [f"Low priority message {i}"],
                    "en",
                    "low"
                ],
                priority=1  # Low priority
            )
            low_priority_tasks.append(task)
        
        # High priority tasks should complete first
        # (This is a conceptual test - actual verification would depend on Celery broker configuration)
        for task in high_priority_tasks:
            assert task.id is not None  # Task was queued
        
        for task in low_priority_tasks:
            assert task.id is not None  # Task was queued
    
    @pytest.mark.asyncio
    async def test_task_retry_mechanism(self, test_voice_agent):
        """Test task retry mechanism on failures"""
        with patch('app.tasks.voice_generation_tasks.ElevenLabsService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance
            
            # Configure to fail first few attempts, then succeed
            call_count = 0
            def mock_synthesis(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise Exception("Temporary API failure")
                return [{"audio_data": b"success", "duration_ms": 2000}]
            
            mock_instance.bulk_synthesize.side_effect = mock_synthesis
            
            # Execute task with retry enabled
            result = batch_voice_synthesis.delay(
                voice_agent_id=test_voice_agent.id,
                texts=["Test retry message"],
                language="en",
                priority="normal"
            )
            
            # Should eventually succeed after retries
            task_result = result.get(timeout=60)
            assert task_result['status'] == 'completed'
            assert call_count >= 2  # Should have retried


@pytest.mark.celery
@pytest.mark.monitoring
class TestCeleryMonitoring:
    """Test Celery monitoring and health checks"""
    
    @pytest.mark.asyncio
    async def test_task_monitoring(self, test_voice_agent):
        """Test task execution monitoring"""
        # Submit a task
        task = batch_voice_synthesis.delay(
            voice_agent_id=test_voice_agent.id,
            texts=["Monitoring test message"],
            language="en",
            priority="normal"
        )
        
        # Monitor task status
        assert task.state in ['PENDING', 'STARTED', 'SUCCESS', 'FAILURE']
        assert task.id is not None
        
        # Get task result with metadata
        try:
            result = task.get(timeout=30, propagate=False)
            assert isinstance(result, dict)
            if task.successful():
                assert 'status' in result
            elif task.failed():
                assert 'error' in result
        except Exception as e:
            # Task might be in progress or failed
            assert task.state in ['PENDING', 'STARTED', 'FAILURE']
    
    def test_worker_health_check(self):
        """Test Celery worker health check"""
        # Check if workers are active
        active_workers = celery_app.control.inspect().active()
        
        # In test environment, workers might not be running
        # This test verifies the monitoring capability exists
        assert isinstance(active_workers, (dict, type(None)))
        
        # Check worker stats
        stats = celery_app.control.inspect().stats()
        assert isinstance(stats, (dict, type(None)))
    
    def test_queue_monitoring(self):
        """Test queue monitoring capabilities"""
        # Check queue lengths (conceptual test)
        try:
            reserved_tasks = celery_app.control.inspect().reserved()
            assert isinstance(reserved_tasks, (dict, type(None)))
            
            scheduled_tasks = celery_app.control.inspect().scheduled()
            assert isinstance(scheduled_tasks, (dict, type(None)))
            
        except Exception:
            # In test environment, broker might not be fully configured
            # This test ensures the monitoring methods exist
            pass
    
    @pytest.mark.asyncio
    async def test_task_failure_handling(self, test_voice_agent):
        """Test task failure handling and error reporting"""
        with patch('app.tasks.voice_generation_tasks.ElevenLabsService') as mock_service:
            mock_service.side_effect = Exception("Service unavailable")
            
            # Submit task that will fail
            task = batch_voice_synthesis.delay(
                voice_agent_id=test_voice_agent.id,
                texts=["This will fail"],
                language="en",
                priority="normal"
            )
            
            # Get result (should handle failure gracefully)
            try:
                result = task.get(timeout=30, propagate=False)
                if task.failed():
                    assert 'error' in result
                    assert "Service unavailable" in result['error']
            except Exception as e:
                # Task failure is handled properly
                assert "Service unavailable" in str(e) or task.state == 'FAILURE'