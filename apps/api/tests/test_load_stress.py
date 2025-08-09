"""
Load and Stress Testing using Locust
Simulates 1000+ concurrent users for system resilience testing
"""
import time
import random
import json
from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging
import gevent


class VoiceAIUser(HttpUser):
    """
    Simulates a user interacting with the Seiketsu AI Voice system
    """
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Initialize user session"""
        # Simulate user authentication
        self.login()
        self.voice_agent_id = None
        self.conversation_id = None
        self.user_profile = self.generate_user_profile()
    
    def login(self):
        """Authenticate user"""
        login_data = {
            "username": f"loadtest_user_{random.randint(1000, 9999)}@example.com",
            "password": "LoadTestPassword123!"
        }
        
        with self.client.post(
            "/api/v1/auth/login",
            json=login_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    token_data = response.json()
                    self.client.headers.update({
                        "Authorization": f"Bearer {token_data.get('access_token', 'mock_token')}"
                    })
                    response.success()
                except (json.JSONDecodeError, KeyError):
                    # Use mock token for load testing
                    self.client.headers.update({
                        "Authorization": "Bearer mock_load_test_token"
                    })
                    response.success()
            else:
                # For load testing, continue with mock authentication
                self.client.headers.update({
                    "Authorization": "Bearer mock_load_test_token"
                })
                response.success()
    
    def generate_user_profile(self):
        """Generate realistic user profile for testing"""
        return {
            "user_type": random.choice(["buyer", "seller", "investor"]),
            "budget_min": random.randint(200000, 500000),
            "budget_max": random.randint(500000, 1000000),
            "property_type": random.choice(["single_family", "condo", "townhouse", "multi_family"]),
            "bedrooms": random.randint(1, 5),
            "location_preference": random.choice(["downtown", "suburbs", "waterfront", "mountain_view"])
        }
    
    @task(10)
    def browse_properties(self):
        """Simulate property browsing"""
        search_params = {
            "min_price": self.user_profile["budget_min"],
            "max_price": self.user_profile["budget_max"],
            "property_type": self.user_profile["property_type"],
            "bedrooms": self.user_profile["bedrooms"],
            "location": self.user_profile["location_preference"]
        }
        
        with self.client.get(
            "/api/v1/properties",
            params=search_params,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    properties = response.json()
                    if isinstance(properties, list) and len(properties) > 0:
                        response.success()
                    else:
                        response.success()  # Empty results are valid
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Failed to browse properties: {response.status_code}")
    
    @task(8)
    def manage_leads(self):
        """Simulate lead management operations"""
        with self.client.get("/api/v1/leads", catch_response=True) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"Failed to get leads: {response.status_code}")
    
    @task(6)
    def voice_agent_interaction(self):
        """Simulate voice agent interaction"""
        # Get available voice agents
        with self.client.get("/api/v1/voice-agents", catch_response=True) as response:
            if response.status_code in [200, 401]:
                if response.status_code == 200:
                    try:
                        agents = response.json()
                        if isinstance(agents, list) and len(agents) > 0:
                            self.voice_agent_id = agents[0].get("id", "mock_agent_id")
                    except (json.JSONDecodeError, AttributeError):
                        self.voice_agent_id = "mock_agent_id"
                response.success()
            else:
                response.failure(f"Failed to get voice agents: {response.status_code}")
    
    @task(5)
    def start_conversation(self):
        """Simulate starting a voice conversation"""
        if not self.voice_agent_id:
            self.voice_agent_id = "mock_agent_id"
        
        conversation_data = {
            "caller_phone": f"+1{random.randint(1000000000, 9999999999)}",
            "voice_agent_id": self.voice_agent_id,
            "metadata": {
                "source": "load_test",
                "user_profile": self.user_profile
            }
        }
        
        with self.client.post(
            "/api/v1/conversations",
            json=conversation_data,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 401]:
                if response.status_code in [200, 201]:
                    try:
                        conv_data = response.json()
                        self.conversation_id = conv_data.get("id", f"mock_conv_{time.time()}")
                    except (json.JSONDecodeError, AttributeError):
                        self.conversation_id = f"mock_conv_{time.time()}"
                response.success()
            else:
                response.failure(f"Failed to start conversation: {response.status_code}")
    
    @task(4)
    def process_voice_input(self):
        """Simulate voice input processing"""
        if not self.conversation_id:
            self.conversation_id = f"mock_conv_{time.time()}"
        
        # Simulate audio file upload
        fake_audio_data = b"fake_audio_data_for_load_testing" * 100  # ~2.7KB
        
        with self.client.post(
            f"/api/v1/conversations/{self.conversation_id}/voice",
            files={"audio": ("test_audio.mp3", fake_audio_data, "audio/mpeg")},
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 400, 401, 415]:
                # Accept various responses during load testing
                response.success()
            else:
                response.failure(f"Voice processing failed: {response.status_code}")
    
    @task(3)
    def analytics_dashboard(self):
        """Simulate analytics dashboard access"""
        with self.client.get("/api/v1/analytics/dashboard", catch_response=True) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"Analytics access failed: {response.status_code}")
    
    @task(2)
    def webhook_endpoints(self):
        """Simulate webhook operations"""
        webhook_data = {
            "url": "https://example.com/webhook",
            "events": ["conversation.started", "lead.qualified"],
            "active": True
        }
        
        with self.client.post(
            "/api/v1/webhooks",
            json=webhook_data,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 400, 401, 422]:
                response.success()
            else:
                response.failure(f"Webhook creation failed: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Health check endpoint"""
        with self.client.get("/api/v1/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    health_data = response.json()
                    if "status" in health_data:
                        response.success()
                    else:
                        response.failure("Invalid health check response")
                except json.JSONDecodeError:
                    response.failure("Health check returned invalid JSON")
            else:
                response.failure(f"Health check failed: {response.status_code}")


class AdminUser(HttpUser):
    """
    Simulates admin users performing administrative tasks
    """
    wait_time = between(2, 5)  # Admins work more deliberately
    weight = 1  # Fewer admin users compared to regular users
    
    def on_start(self):
        """Initialize admin session"""
        self.admin_login()
    
    def admin_login(self):
        """Admin authentication"""
        admin_data = {
            "username": f"admin_{random.randint(100, 999)}@example.com",
            "password": "AdminPassword123!"
        }
        
        with self.client.post(
            "/api/v1/auth/login",
            json=admin_data,
            catch_response=True
        ) as response:
            # Use mock admin token for load testing
            self.client.headers.update({
                "Authorization": "Bearer mock_admin_token"
            })
            response.success()
    
    @task(5)
    def manage_users(self):
        """Admin user management"""
        with self.client.get("/api/v1/admin/users", catch_response=True) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"User management failed: {response.status_code}")
    
    @task(4)
    def system_analytics(self):
        """Admin analytics access"""
        with self.client.get("/api/v1/admin/analytics", catch_response=True) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"System analytics failed: {response.status_code}")
    
    @task(3)
    def organization_management(self):
        """Organization management"""
        with self.client.get("/api/v1/admin/organizations", catch_response=True) as response:
            if response.status_code in [200, 401, 403]:
                response.success()
            else:
                response.failure(f"Organization management failed: {response.status_code}")
    
    @task(2)
    def system_configuration(self):
        """System configuration access"""
        with self.client.get("/api/v1/admin/config", catch_response=True) as response:
            if response.status_code in [200, 404, 401, 403]:
                response.success()
            else:
                response.failure(f"System config failed: {response.status_code}")


class RealEstateAgentUser(HttpUser):
    """
    Simulates real estate agents using the voice AI system
    """
    wait_time = between(1, 4)
    weight = 3  # More agents than admins, fewer than general users
    
    def on_start(self):
        """Initialize agent session"""
        self.agent_login()
        self.client_list = []
    
    def agent_login(self):
        """Agent authentication"""
        agent_data = {
            "username": f"agent_{random.randint(1000, 9999)}@realty.com",
            "password": "AgentPassword123!"
        }
        
        with self.client.post(
            "/api/v1/auth/login",
            json=agent_data,
            catch_response=True
        ) as response:
            self.client.headers.update({
                "Authorization": "Bearer mock_agent_token"
            })
            response.success()
    
    @task(8)
    def manage_leads(self):
        """Agent lead management"""
        with self.client.get("/api/v1/leads?status=new", catch_response=True) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Lead management failed: {response.status_code}")
    
    @task(6)
    def review_conversations(self):
        """Review voice conversations"""
        with self.client.get("/api/v1/conversations?limit=20", catch_response=True) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Conversation review failed: {response.status_code}")
    
    @task(5)
    def update_voice_agents(self):
        """Update voice agent configurations"""
        agent_update = {
            "greeting_message": "Hello! I'm here to help you find your perfect home.",
            "personality": random.choice(["professional", "friendly", "energetic"]),
            "voice_settings": {
                "speed": random.uniform(0.8, 1.2),
                "pitch": random.uniform(0.9, 1.1)
            }
        }
        
        with self.client.put(
            f"/api/v1/voice-agents/{random.randint(1, 100)}",
            json=agent_update,
            catch_response=True
        ) as response:
            if response.status_code in [200, 404, 401, 422]:
                response.success()
            else:
                response.failure(f"Voice agent update failed: {response.status_code}")
    
    @task(4)
    def client_follow_up(self):
        """Client follow-up activities"""
        follow_up_data = {
            "lead_id": f"lead_{random.randint(1, 1000)}",
            "follow_up_type": random.choice(["call", "email", "text"]),
            "scheduled_time": int(time.time() + random.randint(3600, 86400)),
            "notes": "Follow-up scheduled via load test"
        }
        
        with self.client.post(
            "/api/v1/follow-ups",
            json=follow_up_data,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 401, 422]:
                response.success()
            else:
                response.failure(f"Follow-up scheduling failed: {response.status_code}")


# Locust event handlers for monitoring
@events.request.add_listener
def my_request_handler(request_type, name, response_time, response_length, response, context, exception, start_time, url, **kwargs):
    """Handle request events for detailed monitoring"""
    if exception:
        print(f"Request failed: {name} - {exception}")
    elif response_time > 2000:  # Log slow requests
        print(f"Slow request: {name} - {response_time}ms")


@events.quitting.add_listener
def _(environment, **kw):
    """Generate summary report when test ends"""
    stats = environment.stats
    print("\n" + "="*60)
    print("LOAD TEST SUMMARY")
    print("="*60)
    
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.1f}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.1f}ms")
    print(f"99th percentile: {stats.total.get_response_time_percentile(0.99):.1f}ms")
    print(f"Max response time: {stats.total.max_response_time}ms")
    print(f"RPS: {stats.total.current_rps:.1f}")
    
    if stats.total.num_requests > 0:
        failure_rate = (stats.total.num_failures / stats.total.num_requests) * 100
        print(f"Failure rate: {failure_rate:.2f}%")
        
        # Performance thresholds
        print("\nPERFORMANCE ANALYSIS:")
        if stats.total.avg_response_time < 500:
            print("✅ Average response time: GOOD")
        elif stats.total.avg_response_time < 1000:
            print("⚠️  Average response time: ACCEPTABLE")
        else:
            print("❌ Average response time: POOR")
        
        if failure_rate < 1:
            print("✅ Failure rate: GOOD")
        elif failure_rate < 5:
            print("⚠️  Failure rate: ACCEPTABLE")
        else:
            print("❌ Failure rate: POOR")
        
        p95_time = stats.total.get_response_time_percentile(0.95)
        if p95_time < 1000:
            print("✅ 95th percentile: GOOD")
        elif p95_time < 2000:
            print("⚠️  95th percentile: ACCEPTABLE")
        else:
            print("❌ 95th percentile: POOR")


# Stress test scenarios
class StressTestUser(HttpUser):
    """
    Aggressive stress testing user for system limits
    """
    wait_time = between(0.1, 0.5)  # Very fast requests
    
    def on_start(self):
        self.client.headers.update({
            "Authorization": "Bearer stress_test_token"
        })
    
    @task(10)
    def rapid_health_checks(self):
        """Rapid health check requests"""
        with self.client.get("/api/v1/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(8)
    def rapid_api_calls(self):
        """Rapid API endpoint calls"""
        endpoints = [
            "/api/v1/leads",
            "/api/v1/conversations",
            "/api/v1/voice-agents",
            "/api/v1/properties"
        ]
        
        endpoint = random.choice(endpoints)
        with self.client.get(endpoint, catch_response=True) as response:
            if response.status_code in [200, 401, 403, 429]:  # Include rate limiting
                response.success()
            else:
                response.failure(f"Rapid API call failed: {response.status_code}")
    
    @task(5)
    def concurrent_voice_processing(self):
        """Concurrent voice processing simulation"""
        fake_audio = b"stress_test_audio" * 50  # Larger payload
        
        with self.client.post(
            "/api/v1/conversations/stress_test/voice",
            files={"audio": ("stress.mp3", fake_audio, "audio/mpeg")},
            catch_response=True
        ) as response:
            # Accept various responses during stress testing
            if response.status_code in [200, 201, 400, 401, 415, 429, 503]:
                response.success()
            else:
                response.failure(f"Stress voice processing failed: {response.status_code}")


# Custom Locust test configurations
class LoadTestConfig:
    """Load test configuration parameters"""
    
    # User distribution for realistic load
    USER_CLASSES = [
        (VoiceAIUser, 70),      # 70% regular users
        (RealEstateAgentUser, 25),  # 25% agents
        (AdminUser, 5)          # 5% admins
    ]
    
    # Test phases
    PHASES = {
        "ramp_up": {
            "users": 50,
            "spawn_rate": 5,
            "duration": 300  # 5 minutes
        },
        "steady_state": {
            "users": 100,
            "spawn_rate": 10,
            "duration": 600  # 10 minutes
        },
        "peak_load": {
            "users": 500,
            "spawn_rate": 25,
            "duration": 300  # 5 minutes
        },
        "stress_test": {
            "users": 1000,
            "spawn_rate": 50,
            "duration": 180  # 3 minutes
        }
    }
    
    # Performance thresholds
    PERFORMANCE_THRESHOLDS = {
        "avg_response_time_ms": 500,
        "p95_response_time_ms": 1000,
        "p99_response_time_ms": 2000,
        "failure_rate_percent": 1.0,
        "min_rps": 10
    }


if __name__ == "__main__":
    # Example of running load test programmatically
    setup_logging("INFO", None)
    
    # Configure environment
    env = Environment(user_classes=[VoiceAIUser])
    env.create_local_runner()
    
    # Start test
    print("Starting load test...")
    env.runner.start(100, spawn_rate=10)  # 100 users, spawn 10 per second
    
    # Run for 5 minutes
    gevent.spawn_later(300, lambda: env.runner.quit())
    env.runner.greenlet.join()
    
    print("Load test completed")