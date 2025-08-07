"""
Locust load testing configuration for Seiketsu AI API
Run with: locust -f tests/locustfile.py --host=http://localhost:8000
"""
import json
import random
import base64
from locust import HttpUser, task, between, SequentialTaskSet
from faker import Faker

fake = Faker()


class AuthenticatedUser(HttpUser):
    """Base user class with authentication"""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Login and get authentication token"""
        # Try to login with test credentials
        login_data = {
            "email": "loadtest@seiketsu.ai",
            "password": "LoadTest123!"
        }
        
        response = self.client.post("/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            # If login fails, register new user
            register_data = {
                "email": f"loadtest_{random.randint(1000, 9999)}@seiketsu.ai",
                "password": "LoadTest123!",
                "full_name": fake.name(),
                "role": "agent"
            }
            
            response = self.client.post("/api/v1/auth/register", json=register_data)
            if response.status_code == 201:
                self.token = response.json().get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
            else:
                self.headers = {}


class RealEstateAgentWorkflow(SequentialTaskSet):
    """Sequential workflow simulating real estate agent activities"""
    
    def on_start(self):
        """Initialize agent workflow"""
        self.lead_ids = []
        self.conversation_ids = []
        self.property_ids = []
    
    @task
    def check_dashboard(self):
        """Check dashboard analytics"""
        with self.client.get("/api/v1/analytics/dashboard", 
                           headers=self.user.headers,
                           name="Check Dashboard") as response:
            if response.status_code == 200:
                data = response.json()
                # Store metrics for later use
                self.dashboard_data = data
    
    @task
    def view_leads_list(self):
        """View leads list"""
        with self.client.get("/api/v1/leads?page=1&page_size=20",
                           headers=self.user.headers,
                           name="View Leads List") as response:
            if response.status_code == 200:
                leads = response.json().get("results", [])
                if leads:
                    self.lead_ids = [lead["id"] for lead in leads[:5]]
    
    @task
    def create_new_lead(self):
        """Create a new lead"""
        lead_data = {
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "source": random.choice(["website", "referral", "cold_call", "social_media"]),
            "property_preferences": {
                "type": random.choice(["single_family", "condo", "townhouse"]),
                "bedrooms": random.randint(2, 5),
                "bathrooms": random.randint(1, 4),
                "min_price": random.randint(200000, 400000),
                "max_price": random.randint(500000, 800000),
                "location": fake.city()
            },
            "timeline": random.choice(["immediate", "3_months", "6_months", "1_year"]),
            "notes": fake.text(max_nb_chars=200)
        }
        
        with self.client.post("/api/v1/leads",
                            json=lead_data,
                            headers=self.user.headers,
                            name="Create New Lead") as response:
            if response.status_code == 201:
                lead_id = response.json().get("id")
                if lead_id:
                    self.lead_ids.append(lead_id)
    
    @task
    def start_voice_conversation(self):
        """Start a voice conversation with a lead"""
        if not self.lead_ids:
            return
        
        lead_id = random.choice(self.lead_ids)
        conversation_data = {
            "lead_id": lead_id,
            "type": "outbound_call",
            "voice_agent_id": "default_agent",
            "phone_number": fake.phone_number()
        }
        
        with self.client.post("/api/v1/conversations",
                            json=conversation_data,
                            headers=self.user.headers,
                            name="Start Voice Conversation") as response:
            if response.status_code == 201:
                conv_id = response.json().get("id")
                if conv_id:
                    self.conversation_ids.append(conv_id)
    
    @task
    def update_conversation(self):
        """Update conversation with transcript and scoring"""
        if not self.conversation_ids:
            return
        
        conv_id = random.choice(self.conversation_ids)
        update_data = {
            "transcript": fake.text(max_nb_chars=500),
            "duration_seconds": random.randint(120, 600),
            "sentiment_score": random.uniform(0.3, 1.0),
            "lead_score": random.randint(40, 100),
            "status": random.choice(["interested", "qualified", "not_interested", "callback_requested"]),
            "next_action": random.choice(["follow_up_call", "send_listings", "schedule_viewing", "no_action"])
        }
        
        with self.client.patch(f"/api/v1/conversations/{conv_id}",
                             json=update_data,
                             headers=self.user.headers,
                             name="Update Conversation") as response:
            pass
    
    @task
    def search_properties(self):
        """Search for properties"""
        search_criteria = {
            "bedrooms": random.randint(2, 5),
            "bathrooms": random.randint(1, 4),
            "min_price": random.randint(200000, 400000),
            "max_price": random.randint(500000, 800000),
            "property_type": random.choice(["single_family", "condo", "townhouse"]),
            "location": fake.city(),
            "features": random.sample(
                ["garage", "pool", "updated_kitchen", "hardwood_floors", "fireplace"],
                k=random.randint(1, 3)
            )
        }
        
        with self.client.post("/api/v1/properties/search",
                            json=search_criteria,
                            headers=self.user.headers,
                            name="Search Properties") as response:
            if response.status_code == 200:
                properties = response.json().get("properties", [])
                if properties:
                    self.property_ids = [prop["id"] for prop in properties[:3]]
    
    @task
    def get_property_details(self):
        """Get detailed property information"""
        if not self.property_ids:
            return
        
        property_id = random.choice(self.property_ids)
        
        with self.client.get(f"/api/v1/properties/{property_id}",
                           headers=self.user.headers,
                           name="Get Property Details") as response:
            pass
    
    @task
    def schedule_appointment(self):
        """Schedule property viewing appointment"""
        if not self.lead_ids or not self.property_ids:
            return
        
        appointment_data = {
            "lead_id": random.choice(self.lead_ids),
            "property_id": random.choice(self.property_ids),
            "requested_date": fake.future_datetime(end_date="+30d").isoformat(),
            "type": "property_viewing",
            "duration_minutes": random.choice([30, 45, 60]),
            "notes": fake.text(max_nb_chars=100)
        }
        
        with self.client.post("/api/v1/appointments",
                            json=appointment_data,
                            headers=self.user.headers,
                            name="Schedule Appointment") as response:
            pass


class VoiceProcessingUser(AuthenticatedUser):
    """User focused on voice processing tasks"""
    
    @task(5)
    def synthesize_speech(self):
        """Test text-to-speech synthesis"""
        messages = [
            "Hello, thank you for your interest in our properties.",
            "I'd be happy to help you find the perfect home for your family.",
            "Based on your preferences, I have several excellent options to show you.",
            "Would you like to schedule a viewing for this weekend?",
            "I'll send you the property details and follow up tomorrow."
        ]
        
        tts_data = {
            "text": random.choice(messages),
            "voice_id": random.choice(["sarah_professional", "mike_friendly", "lisa_warm"]),
            "settings": {
                "stability": random.uniform(0.5, 1.0),
                "similarity_boost": random.uniform(0.5, 1.0),
                "pitch": random.uniform(0.8, 1.2),
                "speed": random.uniform(0.8, 1.2)
            }
        }
        
        with self.client.post("/api/v1/voice/synthesize",
                            json=tts_data,
                            headers=self.headers,
                            name="Text-to-Speech") as response:
            pass
    
    @task(3)
    def transcribe_audio(self):
        """Test speech-to-text transcription"""
        # Simulate audio file upload
        fake_audio = base64.b64encode(b"fake_audio_data_" + fake.text(50).encode()).decode()
        
        transcription_data = {
            "audio_data": fake_audio,
            "format": "wav",
            "language": "en-US"
        }
        
        with self.client.post("/api/v1/voice/transcribe",
                            json=transcription_data,
                            headers=self.headers,
                            name="Speech-to-Text") as response:
            pass
    
    @task(2)
    def process_voice_session(self):
        """Process real-time voice session"""
        session_data = {
            "lead_id": f"load_test_lead_{random.randint(1, 1000)}",
            "voice_agent_id": "default_agent",
            "session_type": "qualification_call"
        }
        
        with self.client.post("/api/v1/voice/sessions",
                            json=session_data,
                            headers=self.headers,
                            name="Voice Session") as response:
            if response.status_code == 201:
                session_id = response.json().get("session_id")
                
                # Simulate session activity
                if session_id:
                    # Send audio chunks
                    for _ in range(3):
                        chunk_data = {
                            "session_id": session_id,
                            "audio_chunk": base64.b64encode(fake.text(100).encode()).decode(),
                            "timestamp": fake.date_time().isoformat()
                        }
                        
                        self.client.post("/api/v1/voice/sessions/audio",
                                       json=chunk_data,
                                       headers=self.headers,
                                       name="Send Audio Chunk")
                    
                    # End session
                    self.client.post(f"/api/v1/voice/sessions/{session_id}/end",
                                   headers=self.headers,
                                   name="End Voice Session")


class AnalyticsUser(AuthenticatedUser):
    """User focused on analytics and reporting"""
    
    @task(4)
    def view_dashboard(self):
        """View main analytics dashboard"""
        with self.client.get("/api/v1/analytics/dashboard",
                           headers=self.headers,
                           name="Analytics Dashboard") as response:
            pass
    
    @task(3)
    def agent_performance(self):
        """View agent performance metrics"""
        params = {
            "period": random.choice(["day", "week", "month"]),
            "metric": random.choice(["conversion_rate", "call_duration", "lead_score"])
        }
        
        with self.client.get("/api/v1/analytics/agent-performance",
                           params=params,
                           headers=self.headers,
                           name="Agent Performance") as response:
            pass
    
    @task(2)
    def conversation_analytics(self):
        """View conversation analytics"""
        with self.client.get("/api/v1/analytics/conversations",
                           headers=self.headers,
                           name="Conversation Analytics") as response:
            pass
    
    @task(2)
    def lead_source_analysis(self):
        """Analyze lead sources"""
        with self.client.get("/api/v1/analytics/lead-sources",
                           headers=self.headers,
                           name="Lead Source Analysis") as response:
            pass
    
    @task(1)
    def export_report(self):
        """Export analytics report"""
        report_data = {
            "report_type": random.choice(["daily_summary", "weekly_summary", "monthly_summary"]),
            "format": random.choice(["pdf", "csv", "json"]),
            "date_range": {
                "start": fake.past_date(days=30).isoformat(),
                "end": fake.date().isoformat()
            },
            "include_metrics": [
                "conversation_count",
                "lead_qualification_rate",
                "average_call_duration",
                "sentiment_scores"
            ]
        }
        
        with self.client.post("/api/v1/analytics/export",
                            json=report_data,
                            headers=self.headers,
                            name="Export Report") as response:
            pass


class AdminUser(AuthenticatedUser):
    """Administrative user performing management tasks"""
    
    @task(3)
    def manage_voice_agents(self):
        """Manage voice agents"""
        # List voice agents
        with self.client.get("/api/v1/voice-agents",
                           headers=self.headers,
                           name="List Voice Agents") as response:
            pass
        
        # Create new voice agent
        agent_data = {
            "name": f"Load Test Agent {random.randint(1, 1000)}",
            "voice_id": random.choice(["voice_1", "voice_2", "voice_3"]),
            "personality": random.choice(["professional", "friendly", "energetic"]),
            "language": "en-US",
            "pitch": random.uniform(0.8, 1.2),
            "speed": random.uniform(0.8, 1.2),
            "script_template": "standard_qualifier"
        }
        
        with self.client.post("/api/v1/voice-agents",
                            json=agent_data,
                            headers=self.headers,
                            name="Create Voice Agent") as response:
            pass
    
    @task(2)
    def manage_webhooks(self):
        """Manage webhook configurations"""
        # List webhooks
        with self.client.get("/api/v1/webhooks",
                           headers=self.headers,
                           name="List Webhooks") as response:
            pass
        
        # Create webhook
        webhook_data = {
            "url": f"https://httpbin.org/post?id={random.randint(1, 1000)}",
            "events": random.sample(
                ["lead.created", "conversation.completed", "appointment.scheduled"],
                k=random.randint(1, 3)
            ),
            "active": True,
            "retry_attempts": 3
        }
        
        with self.client.post("/api/v1/webhooks",
                            json=webhook_data,
                            headers=self.headers,
                            name="Create Webhook") as response:
            pass
    
    @task(2)
    def organization_settings(self):
        """Manage organization settings"""
        with self.client.get("/api/v1/organizations/current",
                           headers=self.headers,
                           name="Get Organization") as response:
            pass
        
        settings_update = {
            "settings": {
                "max_concurrent_calls": random.randint(10, 50),
                "default_voice_agent": "sarah_professional",
                "lead_scoring_threshold": random.randint(60, 90),
                "auto_follow_up_enabled": random.choice([True, False])
            }
        }
        
        with self.client.patch("/api/v1/organizations/settings",
                             json=settings_update,
                             headers=self.headers,
                             name="Update Organization Settings") as response:
            pass
    
    @task(1)
    def system_health_check(self):
        """Check system health and status"""
        with self.client.get("/api/health/detailed",
                           headers=self.headers,
                           name="System Health Check") as response:
            pass


# User classes with different behaviors
class RealEstateAgentUser(AuthenticatedUser):
    """Real estate agent performing daily tasks"""
    tasks = [RealEstateAgentWorkflow]
    weight = 5  # Most common user type


class VoiceProcessingFocusedUser(VoiceProcessingUser):
    """User heavily using voice processing features"""
    weight = 2


class AnalyticsFocusedUser(AnalyticsUser):
    """User focused on analytics and reporting"""
    weight = 2


class AdminFocusedUser(AdminUser):
    """Administrative user"""
    weight = 1


# Load test scenarios
class PeakHoursLoadTest(HttpUser):
    """Simulate peak business hours load"""
    wait_time = between(0.5, 2)  # Faster pace during peak hours
    
    tasks = {
        RealEstateAgentWorkflow: 6,
        VoiceProcessingUser: 3,
        AnalyticsUser: 1
    }


class StressTest(HttpUser):
    """High-intensity stress testing"""
    wait_time = between(0.1, 0.5)  # Minimal wait time
    
    @task(10)
    def rapid_api_calls(self):
        """Make rapid API calls to test system limits"""
        endpoints = [
            "/api/v1/leads",
            "/api/v1/conversations",
            "/api/v1/analytics/dashboard",
            "/api/health"
        ]
        
        endpoint = random.choice(endpoints)
        with self.client.get(endpoint, headers=getattr(self, 'headers', {})) as response:
            pass


if __name__ == "__main__":
    # This allows running the file directly for testing
    import subprocess
    import sys
    
    print("Starting Locust load test...")
    print("Available user classes:")
    print("- RealEstateAgentUser (weight: 5)")
    print("- VoiceProcessingFocusedUser (weight: 2)")  
    print("- AnalyticsFocusedUser (weight: 2)")
    print("- AdminFocusedUser (weight: 1)")
    print("\nRun with: locust -f tests/locustfile.py --host=http://localhost:8000")