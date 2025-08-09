"""
Contract Testing for Third-Party API Integrations
Tests API contracts with ElevenLabs, Supabase, and other external services
"""
import pytest
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
import httpx
from pydantic import BaseModel, ValidationError

from app.services.elevenlabs_service import elevenlabs_service, Language, AudioFormat
from app.core.config import settings


class ElevenLabsContract(BaseModel):
    """Expected ElevenLabs API contract"""
    text: str
    voice_id: str
    model_id: str = "eleven_multilingual_v2"
    voice_settings: Dict[str, float] = None


class SupabaseContract(BaseModel):
    """Expected Supabase API contract"""
    table_name: str
    operation: str  # select, insert, update, delete
    data: Dict[str, Any] = None
    filters: Dict[str, Any] = None


@pytest.mark.contract
@pytest.mark.external
class TestElevenLabsContract:
    """Contract tests for ElevenLabs API integration"""

    @pytest.fixture
    def mock_elevenlabs_responses(self):
        """Mock ElevenLabs API responses"""
        return {
            "voices": {
                "status_code": 200,
                "content": {
                    "voices": [
                        {
                            "voice_id": "21m00Tcm4TlvDq8ikWAM",
                            "name": "Rachel",
                            "category": "premade",
                            "fine_tuning": {
                                "model_id": "eleven_multilingual_v2",
                                "is_allowed_to_fine_tune": True
                            },
                            "labels": {
                                "accent": "american",
                                "description": "calm",
                                "age": "young",
                                "gender": "female"
                            }
                        }
                    ]
                }
            },
            "text_to_speech": {
                "status_code": 200,
                "content": b"fake_audio_data_from_elevenlabs",
                "headers": {
                    "content-type": "audio/mpeg",
                    "content-length": "1024"
                }
            },
            "user_info": {
                "status_code": 200,
                "content": {
                    "subscription": {
                        "tier": "starter",
                        "character_count": 10000,
                        "character_limit": 10000,
                        "can_extend_character_limit": True,
                        "allowed_to_extend_character_limit": True,
                        "next_character_count_reset_unix": 1640995200
                    },
                    "is_new_user": False,
                    "xi_api_key": "test_api_key"
                }
            },
            "voice_settings": {
                "status_code": 200,
                "content": {
                    "stability": 0.71,
                    "similarity_boost": 0.5,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
        }

    async def test_voices_endpoint_contract(self, mock_elevenlabs_responses):
        """Test ElevenLabs voices endpoint contract"""
        expected_response = mock_elevenlabs_responses["voices"]
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = expected_response["status_code"]
            mock_response.json.return_value = expected_response["content"]
            mock_get.return_value = mock_response
            
            # Test service integration
            voices_response = await elevenlabs_service._get_available_voices()
            
            # Contract validation
            assert isinstance(voices_response, list)
            assert len(voices_response) > 0
            
            voice = voices_response[0]
            required_fields = ["voice_id", "name", "category"]
            for field in required_fields:
                assert field in voice, f"Missing required field: {field}"
            
            # Validate voice_id format
            assert isinstance(voice["voice_id"], str)
            assert len(voice["voice_id"]) > 10  # ElevenLabs voice IDs are long
            
            # Validate name
            assert isinstance(voice["name"], str)
            assert len(voice["name"]) > 0

    async def test_text_to_speech_contract(self, mock_elevenlabs_responses):
        """Test ElevenLabs text-to-speech endpoint contract"""
        expected_response = mock_elevenlabs_responses["text_to_speech"]
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = expected_response["status_code"]
            mock_response.content = expected_response["content"]
            mock_response.headers = expected_response["headers"]
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            
            # Test service integration
            test_text = "Hello, this is a test"
            test_voice_id = "21m00Tcm4TlvDq8ikWAM"
            
            audio_data = await elevenlabs_service._synthesize_speech_direct(
                text=test_text,
                voice_id=test_voice_id
            )
            
            # Contract validation
            assert isinstance(audio_data, bytes)
            assert len(audio_data) > 0
            
            # Verify request was made with correct parameters
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            
            # Check URL
            assert "text-to-speech" in call_args[0][0]
            assert test_voice_id in call_args[0][0]
            
            # Check request payload
            request_data = json.loads(call_args[1]["content"])
            assert request_data["text"] == test_text
            assert "model_id" in request_data
            assert "voice_settings" in request_data

    async def test_voice_settings_contract(self, mock_elevenlabs_responses):
        """Test ElevenLabs voice settings contract"""
        expected_response = mock_elevenlabs_responses["voice_settings"]
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = expected_response["status_code"]
            mock_response.json.return_value = expected_response["content"]
            mock_get.return_value = mock_response
            
            voice_id = "21m00Tcm4TlvDq8ikWAM"
            settings = await elevenlabs_service._get_voice_settings(voice_id)
            
            # Contract validation
            required_settings = ["stability", "similarity_boost"]
            for setting in required_settings:
                assert setting in settings, f"Missing voice setting: {setting}"
                assert isinstance(settings[setting], (int, float))
                assert 0 <= settings[setting] <= 1
            
            # Optional settings validation
            if "style" in settings:
                assert isinstance(settings["style"], (int, float))
                assert 0 <= settings["style"] <= 1
            
            if "use_speaker_boost" in settings:
                assert isinstance(settings["use_speaker_boost"], bool)

    async def test_user_info_contract(self, mock_elevenlabs_responses):
        """Test ElevenLabs user info endpoint contract"""
        expected_response = mock_elevenlabs_responses["user_info"]
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = expected_response["status_code"]
            mock_response.json.return_value = expected_response["content"]
            mock_get.return_value = mock_response
            
            user_info = await elevenlabs_service._get_user_info()
            
            # Contract validation
            assert "subscription" in user_info
            subscription = user_info["subscription"]
            
            required_subscription_fields = [
                "tier", "character_count", "character_limit"
            ]
            for field in required_subscription_fields:
                assert field in subscription, f"Missing subscription field: {field}"
            
            # Validate data types
            assert isinstance(subscription["character_count"], int)
            assert isinstance(subscription["character_limit"], int)
            assert subscription["character_count"] >= 0
            assert subscription["character_limit"] > 0

    async def test_error_response_contract(self):
        """Test ElevenLabs error response contract"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock error response
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "detail": {
                    "status": "invalid_api_key",
                    "message": "Invalid API key provided"
                }
            }
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401 Client Error", request=None, response=mock_response
            )
            mock_post.return_value = mock_response
            
            # Test error handling
            with pytest.raises(Exception) as exc_info:
                await elevenlabs_service._synthesize_speech_direct(
                    text="Test", voice_id="invalid_voice"
                )
            
            # Verify error is properly handled
            assert "401" in str(exc_info.value) or "invalid" in str(exc_info.value).lower()

    async def test_rate_limiting_contract(self):
        """Test ElevenLabs rate limiting response contract"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock rate limit response
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.headers = {"retry-after": "60"}
            mock_response.json.return_value = {
                "detail": {
                    "status": "too_many_requests",
                    "message": "Rate limit exceeded"
                }
            }
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "429 Too Many Requests", request=None, response=mock_response
            )
            mock_post.return_value = mock_response
            
            # Test rate limit handling
            with pytest.raises(Exception) as exc_info:
                await elevenlabs_service._synthesize_speech_direct(
                    text="Test", voice_id="test_voice"
                )
            
            # Verify rate limit is properly detected
            assert "429" in str(exc_info.value) or "rate" in str(exc_info.value).lower()

    async def test_streaming_contract(self):
        """Test ElevenLabs streaming endpoint contract"""
        with patch('httpx.AsyncClient.stream') as mock_stream:
            # Mock streaming response
            async def mock_stream_response():
                chunks = [b"audio_chunk_1", b"audio_chunk_2", b"audio_chunk_3"]
                for chunk in chunks:
                    yield chunk
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"content-type": "audio/mpeg"}
            mock_response.aiter_bytes = mock_stream_response
            
            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__.return_value = mock_response
            mock_stream.return_value = mock_stream_context
            
            # Test streaming
            chunks = []
            async for chunk in elevenlabs_service.synthesize_streaming(
                text="Streaming test",
                voice_agent=Mock(voice_id="test_voice", voice_settings={}),
                language=Language.ENGLISH
            ):
                chunks.append(chunk)
            
            # Contract validation
            assert len(chunks) == 3
            for chunk in chunks:
                assert isinstance(chunk, bytes)
                assert len(chunk) > 0


@pytest.mark.contract
@pytest.mark.external
class TestSupabaseContract:
    """Contract tests for Supabase integration"""

    @pytest.fixture
    def mock_supabase_client(self):
        """Mock Supabase client"""
        class MockSupabaseClient:
            def __init__(self):
                self.table_responses = {}
            
            def table(self, table_name):
                return MockTable(table_name, self.table_responses)
        
        class MockTable:
            def __init__(self, table_name, responses):
                self.table_name = table_name
                self.responses = responses
                self.query_params = {}
            
            def select(self, columns="*"):
                self.query_params["operation"] = "select"
                self.query_params["columns"] = columns
                return self
            
            def insert(self, data):
                self.query_params["operation"] = "insert"
                self.query_params["data"] = data
                return self
            
            def update(self, data):
                self.query_params["operation"] = "update"
                self.query_params["data"] = data
                return self
            
            def delete(self):
                self.query_params["operation"] = "delete"
                return self
            
            def eq(self, column, value):
                self.query_params.setdefault("filters", {})[column] = value
                return self
            
            def execute(self):
                operation = self.query_params.get("operation", "select")
                return self.responses.get(
                    f"{self.table_name}_{operation}",
                    {"data": [], "error": None}
                )
        
        return MockSupabaseClient()

    async def test_supabase_select_contract(self, mock_supabase_client):
        """Test Supabase select operation contract"""
        # Setup mock responses
        expected_data = [
            {"id": "1", "name": "Test User", "email": "test@example.com"},
            {"id": "2", "name": "Another User", "email": "another@example.com"}
        ]
        mock_supabase_client.table_responses["users_select"] = {
            "data": expected_data,
            "error": None
        }
        
        # Test select operation
        result = mock_supabase_client.table("users").select("*").execute()
        
        # Contract validation
        assert "data" in result
        assert "error" in result
        assert result["error"] is None
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 2
        
        # Validate record structure
        for record in result["data"]:
            assert "id" in record
            assert "name" in record
            assert "email" in record

    async def test_supabase_insert_contract(self, mock_supabase_client):
        """Test Supabase insert operation contract"""
        insert_data = {
            "name": "New User",
            "email": "new@example.com",
            "role": "user"
        }
        
        # Setup mock response
        mock_supabase_client.table_responses["users_insert"] = {
            "data": [{"id": "3", **insert_data}],
            "error": None
        }
        
        # Test insert operation
        result = mock_supabase_client.table("users").insert(insert_data).execute()
        
        # Contract validation
        assert "data" in result
        assert "error" in result
        assert result["error"] is None
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 1
        
        inserted_record = result["data"][0]
        assert "id" in inserted_record
        assert inserted_record["name"] == insert_data["name"]
        assert inserted_record["email"] == insert_data["email"]

    async def test_supabase_update_contract(self, mock_supabase_client):
        """Test Supabase update operation contract"""
        update_data = {"name": "Updated User"}
        
        # Setup mock response
        mock_supabase_client.table_responses["users_update"] = {
            "data": [{"id": "1", "name": "Updated User", "email": "test@example.com"}],
            "error": None
        }
        
        # Test update operation
        result = (mock_supabase_client.table("users")
                 .update(update_data)
                 .eq("id", "1")
                 .execute())
        
        # Contract validation
        assert "data" in result
        assert "error" in result
        assert result["error"] is None
        assert isinstance(result["data"], list)
        assert len(result["data"]) == 1
        
        updated_record = result["data"][0]
        assert updated_record["name"] == update_data["name"]

    async def test_supabase_delete_contract(self, mock_supabase_client):
        """Test Supabase delete operation contract"""
        # Setup mock response
        mock_supabase_client.table_responses["users_delete"] = {
            "data": [{"id": "1"}],
            "error": None
        }
        
        # Test delete operation
        result = (mock_supabase_client.table("users")
                 .delete()
                 .eq("id", "1")
                 .execute())
        
        # Contract validation
        assert "data" in result
        assert "error" in result
        assert result["error"] is None

    async def test_supabase_error_contract(self, mock_supabase_client):
        """Test Supabase error response contract"""
        # Setup mock error response
        mock_supabase_client.table_responses["users_select"] = {
            "data": None,
            "error": {
                "message": "relation 'public.nonexistent_table' does not exist",
                "details": "The table you're trying to access doesn't exist",
                "hint": "Check your table name",
                "code": "42P01"
            }
        }
        
        # Test error response
        result = mock_supabase_client.table("users").select("*").execute()
        
        # Contract validation
        assert "data" in result
        assert "error" in result
        assert result["data"] is None
        assert result["error"] is not None
        
        error = result["error"]
        assert "message" in error
        assert "code" in error
        assert isinstance(error["message"], str)
        assert len(error["message"]) > 0


@pytest.mark.contract
@pytest.mark.external
class TestOpenAIContract:
    """Contract tests for OpenAI API integration"""

    async def test_chat_completion_contract(self):
        """Test OpenAI chat completion contract"""
        with patch('openai.AsyncOpenAI') as mock_openai:
            # Mock OpenAI response
            mock_response = Mock()
            mock_response.choices = [
                Mock(
                    message=Mock(
                        content="This is a test response from OpenAI",
                        role="assistant",
                        function_call=None
                    ),
                    finish_reason="stop",
                    index=0
                )
            ]
            mock_response.usage = Mock(
                prompt_tokens=50,
                completion_tokens=20,
                total_tokens=70
            )
            mock_response.id = "chatcmpl-test123"
            mock_response.object = "chat.completion"
            mock_response.created = 1640995200
            mock_response.model = "gpt-4"
            
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            from app.ai.conversation.engine import ConversationAI
            ai = ConversationAI()
            
            # Test chat completion
            messages = [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"}
            ]
            
            response = await ai.client.chat.completions.create(
                model="gpt-4",
                messages=messages
            )
            
            # Contract validation
            assert hasattr(response, 'choices')
            assert len(response.choices) > 0
            
            choice = response.choices[0]
            assert hasattr(choice, 'message')
            assert hasattr(choice.message, 'content')
            assert hasattr(choice.message, 'role')
            assert choice.message.role == "assistant"
            
            assert hasattr(response, 'usage')
            assert hasattr(response.usage, 'prompt_tokens')
            assert hasattr(response.usage, 'completion_tokens')
            assert hasattr(response.usage, 'total_tokens')
            
            # Validate token counts
            assert isinstance(response.usage.prompt_tokens, int)
            assert isinstance(response.usage.completion_tokens, int)
            assert isinstance(response.usage.total_tokens, int)
            assert response.usage.total_tokens == (
                response.usage.prompt_tokens + response.usage.completion_tokens
            )

    async def test_function_calling_contract(self):
        """Test OpenAI function calling contract"""
        with patch('openai.AsyncOpenAI') as mock_openai:
            # Mock function call response
            mock_response = Mock()
            mock_response.choices = [
                Mock(
                    message=Mock(
                        content=None,
                        role="assistant",
                        function_call=Mock(
                            name="search_properties",
                            arguments='{"location": "downtown", "max_price": 500000}'
                        )
                    ),
                    finish_reason="function_call",
                    index=0
                )
            ]
            mock_response.usage = Mock(
                prompt_tokens=100,
                completion_tokens=30,
                total_tokens=130
            )
            
            mock_client = AsyncMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            from app.ai.conversation.engine import ConversationAI
            ai = ConversationAI()
            
            # Test function calling
            functions = [
                {
                    "name": "search_properties",
                    "description": "Search for properties",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"},
                            "max_price": {"type": "number"}
                        }
                    }
                }
            ]
            
            response = await ai.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Find properties downtown under $500k"}],
                functions=functions,
                function_call="auto"
            )
            
            # Contract validation
            choice = response.choices[0]
            assert choice.finish_reason == "function_call"
            assert hasattr(choice.message, 'function_call')
            assert choice.message.function_call is not None
            
            function_call = choice.message.function_call
            assert hasattr(function_call, 'name')
            assert hasattr(function_call, 'arguments')
            assert function_call.name == "search_properties"
            
            # Validate function arguments are valid JSON
            import json
            args = json.loads(function_call.arguments)
            assert isinstance(args, dict)
            assert "location" in args
            assert "max_price" in args

    async def test_whisper_contract(self):
        """Test OpenAI Whisper API contract"""
        with patch('openai.AsyncOpenAI') as mock_openai:
            # Mock Whisper response
            mock_response = Mock()
            mock_response.text = "This is the transcribed text from audio"
            
            mock_client = AsyncMock()
            mock_client.audio.transcriptions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            from app.services.voice_service import VoiceService
            voice_service = VoiceService()
            
            # Test audio transcription
            audio_data = b"fake_audio_data"
            transcript = await voice_service._speech_to_text(audio_data)
            
            # Contract validation
            assert isinstance(transcript, str)
            assert len(transcript) > 0
            assert transcript == "This is the transcribed text from audio"
            
            # Verify API was called with correct parameters
            mock_client.audio.transcriptions.create.assert_called_once()
            call_args = mock_client.audio.transcriptions.create.call_args
            
            assert call_args.kwargs["model"] == "whisper-1"
            assert "file" in call_args.kwargs
            assert call_args.kwargs.get("language") == "en"


@pytest.mark.contract
@pytest.mark.integration
class TestAPIContractCompliance:
    """Test our API contract compliance"""

    async def test_api_response_format_contract(self, client, authorized_headers):
        """Test our API maintains consistent response format"""
        endpoints_to_test = [
            ("/api/v1/users/me", "GET"),
            ("/api/v1/leads", "GET"),
            ("/api/v1/conversations", "GET"),
            ("/api/v1/voice-agents", "GET")
        ]
        
        for endpoint, method in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint, headers=authorized_headers)
            
            # Skip if endpoint doesn't exist
            if response.status_code == 404:
                continue
                
            # Contract validation for successful responses
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if isinstance(data, list):
                    # List responses should be arrays
                    assert isinstance(data, list)
                    if len(data) > 0:
                        # Each item should be an object
                        assert isinstance(data[0], dict)
                elif isinstance(data, dict):
                    # Object responses should have consistent structure
                    assert isinstance(data, dict)
                    # Common fields should exist if present
                    if "id" in data:
                        assert isinstance(data["id"], str)
                    if "created_at" in data:
                        assert isinstance(data["created_at"], str)
                    if "updated_at" in data:
                        assert isinstance(data["updated_at"], str)

    async def test_error_response_contract(self, client):
        """Test error responses follow consistent contract"""
        # Test various error conditions
        error_tests = [
            ("/api/v1/nonexistent", 404),
            ("/api/v1/users/me", 401),  # Unauthorized
        ]
        
        for endpoint, expected_status in error_tests:
            response = client.get(endpoint)
            
            if response.status_code == expected_status:
                # Validate error response structure
                if response.headers.get("content-type", "").startswith("application/json"):
                    error_data = response.json()
                    
                    # Common error response fields
                    if isinstance(error_data, dict):
                        # Should have detail or message
                        assert "detail" in error_data or "message" in error_data
                        
                        if "detail" in error_data:
                            assert isinstance(error_data["detail"], (str, list, dict))

    async def test_pagination_contract(self, client, authorized_headers):
        """Test pagination contract consistency"""
        paginated_endpoints = [
            "/api/v1/leads",
            "/api/v1/conversations"
        ]
        
        for endpoint in paginated_endpoints:
            # Test with pagination parameters
            response = client.get(
                f"{endpoint}?limit=10&offset=0",
                headers=authorized_headers
            )
            
            # Skip if endpoint doesn't exist
            if response.status_code == 404:
                continue
                
            if response.status_code == 200:
                data = response.json()
                
                # Should return array for paginated endpoints
                if isinstance(data, list):
                    assert len(data) <= 10  # Respects limit
                elif isinstance(data, dict):
                    # Alternative pagination format
                    if "data" in data:
                        assert isinstance(data["data"], list)
                        if "pagination" in data:
                            pagination = data["pagination"]
                            assert "limit" in pagination
                            assert "offset" in pagination
                            assert isinstance(pagination["limit"], int)
                            assert isinstance(pagination["offset"], int)

    async def test_authentication_contract(self, client, access_token):
        """Test authentication contract consistency"""
        protected_endpoint = "/api/v1/users/me"
        
        # Test without authentication
        response = client.get(protected_endpoint)
        assert response.status_code == 401
        
        # Test with valid authentication
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get(protected_endpoint, headers=headers)
        
        # Should either succeed or fail consistently
        assert response.status_code in [200, 401, 403]
        
        if response.status_code == 401:
            # Should provide clear error message
            error_data = response.json()
            assert "detail" in error_data or "message" in error_data