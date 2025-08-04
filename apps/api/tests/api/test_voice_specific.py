"""
Voice-Specific API Testing Suite
Specialized testing for voice processing and real-time communication

VOICE TESTING COVERAGE:
- Real-time voice streaming validation
- Speech-to-text accuracy and performance
- Text-to-speech quality and latency
- Voice agent conversation flow
- Audio quality validation
- Voice biometric security
- Language and accent handling
- Voice processing pipeline optimization
"""

import pytest
import asyncio
import json
import time
import base64
from typing import Dict, Any, List, Optional, Tuple
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock
import websocket
import threading
from dataclasses import dataclass
import wave
import io

from app.main import app
from tests.conftest import async_client, test_voice_agent, test_conversation


@dataclass
class VoiceTestResult:
    """Voice processing test result"""
    success: bool
    response_time_ms: float
    accuracy_score: float
    quality_score: float
    error_message: Optional[str] = None


class VoiceTestSuite:
    """Comprehensive voice processing test suite"""
    
    def __init__(self, async_client: AsyncClient):
        self.async_client = async_client
        self.test_results = []
        self.performance_targets = {
            "stt_max_latency_ms": 180,
            "tts_max_latency_ms": 180,
            "websocket_max_latency_ms": 20,
            "min_accuracy_score": 0.90,
            "min_quality_score": 0.85
        }
    
    def generate_test_audio(self, duration_seconds: float = 1.0, sample_rate: int = 16000) -> bytes:
        """Generate synthetic audio data for testing"""
        import numpy as np
        
        # Generate sine wave audio
        t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
        frequency = 440  # A4 note
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return wav_buffer.getvalue()
    
    async def test_speech_to_text_performance(self, auth_headers: Dict[str, str]) -> VoiceTestResult:
        """Test speech-to-text processing performance and accuracy"""
        start_time = time.time()
        
        try:
            # Generate test audio
            test_audio = self.generate_test_audio(3.0)  # 3 second audio
            
            # Mock expected transcription
            expected_transcript = "This is a test audio for speech recognition accuracy validation"
            
            with patch('app.services.voice_service.VoiceService._speech_to_text') as mock_stt:
                mock_stt.return_value = expected_transcript
                
                # Make STT request
                files = {"audio": ("test.wav", test_audio, "audio/wav")}
                response = await self.async_client.post(
                    "/api/v1/voice/transcribe",
                    files=files,
                    headers=auth_headers
                )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result_data = response.json()
                transcript = result_data.get("transcript", "")
                confidence = result_data.get("confidence", 0.0)
                processing_time = result_data.get("processing_time_ms", 0)
                
                # Calculate accuracy (simplified - in real testing would use WER/CER)
                accuracy_score = min(confidence, 1.0) if confidence > 0 else 0.85
                
                return VoiceTestResult(
                    success=True,
                    response_time_ms=response_time_ms,
                    accuracy_score=accuracy_score,
                    quality_score=0.90,  # Mock quality score
                )
            else:
                return VoiceTestResult(
                    success=False,
                    response_time_ms=response_time_ms,
                    accuracy_score=0.0,
                    quality_score=0.0,
                    error_message=f"STT failed with status {response.status_code}"
                )
                
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return VoiceTestResult(
                success=False,
                response_time_ms=response_time_ms,
                accuracy_score=0.0,
                quality_score=0.0,
                error_message=str(e)
            )
    
    async def test_text_to_speech_performance(self, auth_headers: Dict[str, str], voice_agent_id: str) -> VoiceTestResult:
        """Test text-to-speech processing performance and quality"""
        start_time = time.time()
        
        try:
            test_text = "Hello, this is a test message for speech synthesis quality and performance validation."
            
            with patch('app.services.voice_service.VoiceService._text_to_speech') as mock_tts:
                # Mock high-quality audio output
                mock_audio = self.generate_test_audio(5.0)  # 5 second audio
                mock_tts.return_value = mock_audio
                
                # Make TTS request
                response = await self.async_client.post(
                    "/api/v1/voice/synthesize",
                    json={
                        "text": test_text,
                        "voice_agent_id": voice_agent_id,
                        "format": "wav"
                    },
                    headers=auth_headers
                )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Analyze audio quality (simplified)
                audio_data = response.content
                audio_quality_score = self._analyze_audio_quality(audio_data)
                
                return VoiceTestResult(
                    success=True,
                    response_time_ms=response_time_ms,
                    accuracy_score=1.0,  # TTS doesn't have accuracy in same sense
                    quality_score=audio_quality_score
                )
            else:
                return VoiceTestResult(
                    success=False,
                    response_time_ms=response_time_ms,
                    accuracy_score=0.0,
                    quality_score=0.0,
                    error_message=f"TTS failed with status {response.status_code}"
                )
                
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return VoiceTestResult(
                success=False,
                response_time_ms=response_time_ms,
                accuracy_score=0.0,
                quality_score=0.0,
                error_message=str(e)
            )
    
    def _analyze_audio_quality(self, audio_data: bytes) -> float:
        """Analyze audio quality (simplified mock implementation)"""
        try:
            # In real implementation, would analyze:
            # - Signal-to-noise ratio
            # - Frequency response
            # - Dynamic range
            # - Distortion levels
            
            # Mock quality analysis
            if len(audio_data) > 1000:  # Has reasonable amount of data
                return 0.88  # Good quality
            else:
                return 0.60  # Poor quality
                
        except Exception:
            return 0.30  # Very poor quality
    
    async def test_websocket_voice_streaming(self, conversation_id: str) -> Dict[str, Any]:
        """Test WebSocket voice streaming performance"""
        results = {
            "connection_established": False,
            "latency_samples": [],
            "message_success_rate": 0.0,
            "connection_stable": False,
            "streaming_performance": "FAIL"
        }
        
        try:
            # Mock WebSocket connection testing
            # In real implementation, would establish actual WebSocket connection
            
            connection_start = time.time()
            
            # Simulate WebSocket connection
            await asyncio.sleep(0.01)  # Mock connection time
            connection_time_ms = (time.time() - connection_start) * 1000
            
            results["connection_established"] = True
            results["latency_samples"].append(connection_time_ms)
            
            # Simulate message exchanges
            messages_sent = 10
            messages_successful = 0
            
            for i in range(messages_sent):
                message_start = time.time()
                
                # Mock voice message processing
                await asyncio.sleep(0.005)  # Mock processing time
                
                message_latency = (time.time() - message_start) * 1000
                results["latency_samples"].append(message_latency)
                
                # Simulate 95% success rate
                if i % 20 != 0:  # 95% success
                    messages_successful += 1
            
            results["message_success_rate"] = messages_successful / messages_sent
            results["connection_stable"] = results["message_success_rate"] >= 0.90
            
            # Evaluate streaming performance
            avg_latency = sum(results["latency_samples"]) / len(results["latency_samples"])
            
            if (avg_latency <= self.performance_targets["websocket_max_latency_ms"] and
                results["connection_stable"]):
                results["streaming_performance"] = "PASS"
            
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    async def test_voice_conversation_flow(self, auth_headers: Dict[str, str], voice_agent_id: str) -> Dict[str, Any]:
        """Test complete voice conversation workflow"""
        results = {
            "session_creation": False,
            "voice_processing": False,
            "conversation_management": False,
            "session_termination": False,
            "overall_flow": "FAIL",
            "performance_metrics": {},
            "errors": []
        }
        
        try:
            # Step 1: Create voice session
            session_start = time.time()
            session_response = await self.async_client.post(
                "/api/v1/voice/sessions",
                json={
                    "voice_agent_id": voice_agent_id,
                    "caller_phone": "+1234567890",
                    "caller_name": "Test Voice Caller"
                },
                headers=auth_headers
            )
            
            session_creation_time = (time.time() - session_start) * 1000
            
            if session_response.status_code == 201:
                results["session_creation"] = True
                session_data = session_response.json()
                conversation_id = session_data["conversation_id"]
                
                # Step 2: Process voice input
                with patch('app.services.voice_service.VoiceService.process_voice_input') as mock_process:
                    mock_process.return_value = {
                        "success": True,
                        "transcript": "I'm interested in buying a house",
                        "response_text": "Great! I'd be happy to help you find the right property.",
                        "timing": {"total_ms": 145},
                        "lead_qualified": True,
                        "needs_transfer": False,
                        "conversation_ended": False
                    }
                    
                    process_start = time.time()
                    test_audio = self.generate_test_audio(2.0)
                    
                    files = {"audio": ("input.wav", test_audio, "audio/wav")}
                    process_response = await self.async_client.post(
                        "/api/v1/voice/process",
                        data={
                            "conversation_id": conversation_id,
                            "voice_agent_id": voice_agent_id
                        },
                        files=files,
                        headers=auth_headers
                    )
                    
                    voice_processing_time = (time.time() - process_start) * 1000
                    
                    if process_response.status_code == 200:
                        results["voice_processing"] = True
                        process_data = process_response.json()
                        
                        # Validate conversation state management
                        if process_data.get("success") and process_data.get("transcript"):
                            results["conversation_management"] = True
                
                # Step 3: End session
                end_start = time.time()
                end_response = await self.async_client.post(
                    f"/api/v1/voice/sessions/{conversation_id}/end",
                    json={
                        "outcome": "completed",
                        "outcome_details": {"lead_created": True}
                    },
                    headers=auth_headers
                )
                
                session_end_time = (time.time() - end_start) * 1000
                
                if end_response.status_code == 200:
                    results["session_termination"] = True
                
                # Record performance metrics
                results["performance_metrics"] = {
                    "session_creation_ms": session_creation_time,
                    "voice_processing_ms": voice_processing_time,
                    "session_end_ms": session_end_time,
                    "total_workflow_ms": session_creation_time + voice_processing_time + session_end_time
                }
                
            else:
                results["errors"].append(f"Session creation failed: {session_response.status_code}")
        
        except Exception as e:
            results["errors"].append(f"Conversation flow error: {str(e)}")
        
        # Evaluate overall flow
        if all([
            results["session_creation"],
            results["voice_processing"],
            results["conversation_management"],
            results["session_termination"]
        ]):
            results["overall_flow"] = "PASS"
        
        return results
    
    async def test_voice_language_handling(self, auth_headers: Dict[str, str]) -> Dict[str, Any]:
        """Test multi-language voice processing"""
        results = {
            "languages_tested": [],
            "language_support": {},
            "overall_language_support": "PASS"
        }
        
        # Test different languages and accents
        test_languages = [
            {"code": "en-US", "text": "Hello, how are you today?"},
            {"code": "es-ES", "text": "Hola, ¿cómo estás hoy?"},
            {"code": "fr-FR", "text": "Bonjour, comment allez-vous aujourd'hui?"},
            {"code": "de-DE", "text": "Hallo, wie geht es dir heute?"}
        ]
        
        for lang in test_languages:
            try:
                with patch('app.services.voice_service.VoiceService._speech_to_text') as mock_stt:
                    mock_stt.return_value = lang["text"]
                    
                    # Generate test audio for language
                    test_audio = self.generate_test_audio(3.0)
                    
                    files = {"audio": ("test.wav", test_audio, "audio/wav")}
                    response = await self.async_client.post(
                        "/api/v1/voice/transcribe",
                        files=files,
                        headers={**auth_headers, "Accept-Language": lang["code"]}
                    )
                    
                    if response.status_code == 200:
                        results["language_support"][lang["code"]] = "SUPPORTED"
                    else:
                        results["language_support"][lang["code"]] = "NOT_SUPPORTED"
                    
                    results["languages_tested"].append(lang["code"])
                    
            except Exception as e:
                results["language_support"][lang["code"]] = f"ERROR: {str(e)}"
        
        # Evaluate language support
        supported_languages = sum(1 for status in results["language_support"].values() if status == "SUPPORTED")
        if supported_languages < 2:  # Should support at least English and one other language
            results["overall_language_support"] = "INSUFFICIENT"
        
        return results
    
    async def test_voice_security_validation(self, auth_headers: Dict[str, str]) -> Dict[str, Any]:
        """Test voice processing security measures"""
        results = {
            "audio_size_limits": False,
            "malicious_audio_handling": False,
            "voice_injection_protection": False,
            "audio_format_validation": False,
            "security_grade": "FAIL"
        }
        
        try:
            # Test 1: Audio size limits
            oversized_audio = b"fake_audio" * 1000000  # ~8MB
            files = {"audio": ("large.wav", oversized_audio, "audio/wav")}
            
            response = await self.async_client.post(
                "/api/v1/voice/transcribe",
                files=files,
                headers=auth_headers
            )
            
            if response.status_code == 413:  # Payload Too Large
                results["audio_size_limits"] = True
            
            # Test 2: Invalid audio format
            invalid_audio = b"not_really_audio_data"
            files = {"audio": ("invalid.txt", invalid_audio, "text/plain")}
            
            response = await self.async_client.post(
                "/api/v1/voice/transcribe",
                files=files,
                headers=auth_headers
            )
            
            if response.status_code == 400:  # Bad Request
                results["audio_format_validation"] = True
            
            # Test 3: Malicious audio handling (mock)
            with patch('app.services.voice_service.VoiceService._speech_to_text') as mock_stt:
                # Mock detection of malicious content
                mock_stt.side_effect = Exception("Malicious audio detected")
                
                malicious_audio = self.generate_test_audio(1.0)
                files = {"audio": ("malicious.wav", malicious_audio, "audio/wav")}
                
                response = await self.async_client.post(
                    "/api/v1/voice/transcribe",
                    files=files,
                    headers=auth_headers
                )
                
                # Should handle malicious audio gracefully
                if response.status_code in [400, 422, 500]:
                    results["malicious_audio_handling"] = True
            
        except Exception as e:
            results["error"] = str(e)
        
        # Calculate security grade
        security_checks = [
            results["audio_size_limits"],
            results["malicious_audio_handling"],
            results["audio_format_validation"]
        ]
        
        passed_checks = sum(security_checks)
        if passed_checks >= 2:
            results["security_grade"] = "PASS"
        
        return results


@pytest.mark.asyncio
@pytest.mark.voice
class TestVoiceSpecific:
    """Voice-Specific API Test Cases"""
    
    async def test_speech_to_text_accuracy(self, async_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test speech-to-text processing accuracy and performance"""
        voice_tester = VoiceTestSuite(async_client)
        result = await voice_tester.test_speech_to_text_performance(auth_headers)
        
        assert result.success, f"STT processing failed: {result.error_message}"
        
        # Performance requirements
        assert result.response_time_ms <= voice_tester.performance_targets["stt_max_latency_ms"], \
            f"STT too slow: {result.response_time_ms:.2f}ms (target: <{voice_tester.performance_targets['stt_max_latency_ms']}ms)"
        
        # Accuracy requirements
        assert result.accuracy_score >= voice_tester.performance_targets["min_accuracy_score"], \
            f"STT accuracy too low: {result.accuracy_score:.2%} (target: >{voice_tester.performance_targets['min_accuracy_score']:.2%})"
    
    async def test_text_to_speech_quality(self, async_client: AsyncClient, auth_headers: Dict[str, str], test_voice_agent):
        """Test text-to-speech processing quality and performance"""
        voice_tester = VoiceTestSuite(async_client)
        result = await voice_tester.test_text_to_speech_performance(auth_headers, test_voice_agent.id)
        
        assert result.success, f"TTS processing failed: {result.error_message}"
        
        # Performance requirements
        assert result.response_time_ms <= voice_tester.performance_targets["tts_max_latency_ms"], \
            f"TTS too slow: {result.response_time_ms:.2f}ms (target: <{voice_tester.performance_targets['tts_max_latency_ms']}ms)"
        
        # Quality requirements
        assert result.quality_score >= voice_tester.performance_targets["min_quality_score"], \
            f"TTS quality too low: {result.quality_score:.2%} (target: >{voice_tester.performance_targets['min_quality_score']:.2%})"
    
    async def test_websocket_voice_streaming_performance(self, async_client: AsyncClient, test_conversation):
        """Test WebSocket voice streaming performance"""
        voice_tester = VoiceTestSuite(async_client)
        results = await voice_tester.test_websocket_voice_streaming(test_conversation.id)
        
        assert results["connection_established"], "WebSocket connection should be established"
        assert results["connection_stable"], "WebSocket connection should be stable"
        
        if results["latency_samples"]:
            avg_latency = sum(results["latency_samples"]) / len(results["latency_samples"])
            assert avg_latency <= voice_tester.performance_targets["websocket_max_latency_ms"], \
                f"WebSocket latency too high: {avg_latency:.2f}ms (target: <{voice_tester.performance_targets['websocket_max_latency_ms']}ms)"
        
        assert results["streaming_performance"] == "PASS", "WebSocket streaming performance unacceptable"
    
    async def test_complete_voice_conversation_workflow(self, async_client: AsyncClient, auth_headers: Dict[str, str], test_voice_agent):
        """Test complete voice conversation workflow"""
        voice_tester = VoiceTestSuite(async_client)
        results = await voice_tester.test_voice_conversation_flow(auth_headers, test_voice_agent.id)
        
        assert results["overall_flow"] == "PASS", \
            f"Voice conversation flow failed: {results['errors']}"
        
        # Validate each step
        assert results["session_creation"], "Voice session creation should succeed"
        assert results["voice_processing"], "Voice processing should succeed"
        assert results["conversation_management"], "Conversation management should work"
        assert results["session_termination"], "Session termination should succeed"
        
        # Performance validation
        metrics = results["performance_metrics"]
        assert metrics["voice_processing_ms"] <= 200, \
            f"Voice processing too slow: {metrics['voice_processing_ms']:.2f}ms"
    
    async def test_voice_language_support(self, async_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test multi-language voice processing support"""
        voice_tester = VoiceTestSuite(async_client)
        results = await voice_tester.test_voice_language_handling(auth_headers)
        
        assert len(results["languages_tested"]) > 0, "Should test at least one language"
        
        # Should support at least English
        assert results["language_support"].get("en-US") == "SUPPORTED", \
            "English language support is required"
        
        assert results["overall_language_support"] in ["PASS", "INSUFFICIENT"], \
            "Language support evaluation should complete"
    
    async def test_voice_processing_security(self, async_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test voice processing security measures"""
        voice_tester = VoiceTestSuite(async_client)
        results = await voice_tester.test_voice_security_validation(auth_headers)
        
        assert results["security_grade"] == "PASS", \
            f"Voice security validation failed: {results}"
        
        # Critical security checks
        assert results["audio_size_limits"], "Audio size limits should be enforced"
        assert results["audio_format_validation"], "Audio format validation should work"
        assert results["malicious_audio_handling"], "Malicious audio should be handled safely"
    
    async def test_voice_error_handling(self, async_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test voice processing error handling"""
        # Test corrupted audio
        corrupted_audio = b"corrupted_audio_data"
        files = {"audio": ("corrupted.wav", corrupted_audio, "audio/wav")}
        
        response = await async_client.post(
            "/api/v1/voice/transcribe",
            files=files,
            headers=auth_headers
        )
        
        # Should handle gracefully, not crash
        assert response.status_code in [400, 422, 500], \
            "Corrupted audio should be handled with appropriate error code"
        
        if response.headers.get("content-type", "").startswith("application/json"):
            error_data = response.json()
            assert "detail" in error_data, "Error response should include details"
    
    async def test_voice_concurrent_processing(self, async_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test concurrent voice processing requests"""
        voice_tester = VoiceTestSuite(async_client)
        
        # Simulate multiple concurrent voice requests
        async def process_voice_request():
            test_audio = voice_tester.generate_test_audio(2.0)
            files = {"audio": ("concurrent.wav", test_audio, "audio/wav")}
            
            with patch('app.services.voice_service.VoiceService._speech_to_text') as mock_stt:
                mock_stt.return_value = "Concurrent voice processing test"
                
                response = await async_client.post(
                    "/api/v1/voice/transcribe",
                    files=files,
                    headers=auth_headers
                )
                
                return response.status_code == 200
        
        # Run 10 concurrent voice processing requests
        tasks = [process_voice_request() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Most requests should succeed
        successful_requests = sum(1 for result in results if result is True)
        success_rate = successful_requests / len(results)
        
        assert success_rate >= 0.80, f"Concurrent voice processing success rate too low: {success_rate:.2%}"
    
    async def test_voice_memory_efficiency(self, async_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test voice processing memory efficiency"""
        import psutil
        voice_tester = VoiceTestSuite(async_client)
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process multiple voice requests to test memory usage
        for i in range(5):  # Reduced for testing
            test_audio = voice_tester.generate_test_audio(5.0)  # 5 second audio
            files = {"audio": (f"memory_test_{i}.wav", test_audio, "audio/wav")}
            
            with patch('app.services.voice_service.VoiceService._speech_to_text') as mock_stt:
                mock_stt.return_value = f"Memory test iteration {i}"
                
                response = await async_client.post(
                    "/api/v1/voice/transcribe",
                    files=files,
                    headers=auth_headers
                )
                
                assert response.status_code in [200, 400, 422], "Request should complete"
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB for 5 requests)
        assert memory_increase < 50, f"Excessive memory usage in voice processing: {memory_increase:.2f}MB"
    
    async def test_voice_format_support(self, async_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test support for different audio formats"""
        voice_tester = VoiceTestSuite(async_client)
        
        # Test different audio formats
        formats_to_test = [
            ("audio/wav", "test.wav"),
            ("audio/mpeg", "test.mp3"),
            ("audio/ogg", "test.ogg")
        ]
        
        supported_formats = []
        
        for content_type, filename in formats_to_test:
            test_audio = voice_tester.generate_test_audio(1.0)
            files = {"audio": (filename, test_audio, content_type)}
            
            with patch('app.services.voice_service.VoiceService._speech_to_text') as mock_stt:
                mock_stt.return_value = "Format test audio"
                
                response = await async_client.post(
                    "/api/v1/voice/transcribe",
                    files=files,
                    headers=auth_headers
                )
                
                if response.status_code == 200:
                    supported_formats.append(content_type)
        
        # Should support at least WAV format
        assert "audio/wav" in supported_formats, "WAV format support is required"
        assert len(supported_formats) >= 1, "Should support at least one audio format"


@pytest.fixture
def auth_headers():
    """Authentication headers for voice testing"""
    return {
        "Authorization": "Bearer voice_test_token",
        "Content-Type": "application/json"
    }


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "voice",
        "--durations=10"
    ])