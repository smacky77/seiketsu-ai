"""
Factory classes for generating test data using Factory Boy.
Provides realistic test data for comprehensive testing.
"""
import factory
import factory.fuzzy
from datetime import datetime, timedelta
from faker import Faker
import random
import uuid

from app.models.organization import Organization
from app.models.user import User
from app.models.lead import Lead
from app.models.conversation import Conversation
from app.models.voice_agent import VoiceAgent
from app.models.property import Property
from app.models.webhook import Webhook

fake = Faker()


class OrganizationFactory(factory.Factory):
    """Factory for creating test organizations"""
    
    class Meta:
        model = Organization
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.Faker('company')
    subdomain = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-').replace(',', ''))
    
    settings = factory.LazyFunction(lambda: {
        "max_agents": random.randint(5, 100),
        "voice_minutes": random.randint(1000, 10000),
        "features": random.sample([
            "voice_ai",
            "lead_scoring", 
            "market_intelligence",
            "automated_follow_up",
            "advanced_analytics",
            "crm_integration"
        ], k=random.randint(2, 5))
    })
    
    subscription_status = factory.fuzzy.FuzzyChoice(['active', 'trial', 'suspended'])
    subscription_tier = factory.fuzzy.FuzzyChoice(['starter', 'professional', 'enterprise'])
    
    billing_email = factory.Faker('email')
    phone = factory.Faker('phone_number')
    address = factory.Faker('address')
    
    created_at = factory.LazyFunction(
        lambda: fake.date_time_between(start_date='-2y', end_date='now')
    )
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at + timedelta(days=random.randint(1, 30)))


class UserFactory(factory.Factory):
    """Factory for creating test users"""
    
    class Meta:
        model = User
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    email = factory.Faker('email')
    full_name = factory.Faker('name')
    
    role = factory.fuzzy.FuzzyChoice(['agent', 'manager', 'admin'])
    
    phone = factory.Faker('phone_number')
    timezone = factory.fuzzy.FuzzyChoice([
        'America/New_York',
        'America/Chicago', 
        'America/Denver',
        'America/Los_Angeles',
        'America/Toronto'
    ])
    
    is_active = factory.fuzzy.FuzzyChoice([True, False], probability_true=0.9)
    is_superuser = factory.LazyAttribute(lambda obj: obj.role == 'admin')
    
    preferences = factory.LazyFunction(lambda: {
        "notification_email": random.choice([True, False]),
        "notification_sms": random.choice([True, False]),
        "dashboard_layout": random.choice(['compact', 'detailed', 'custom']),
        "auto_assign_leads": random.choice([True, False])
    })
    
    created_at = factory.LazyFunction(
        lambda: fake.date_time_between(start_date='-1y', end_date='now')
    )
    last_login = factory.LazyAttribute(
        lambda obj: obj.created_at + timedelta(days=random.randint(1, 365))
    )


class LeadFactory(factory.Factory):
    """Factory for creating test leads"""
    
    class Meta:
        model = Lead
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.Faker('name')
    email = factory.Faker('email')
    phone = factory.Faker('phone_number')
    
    source = factory.fuzzy.FuzzyChoice([
        'website',
        'referral',
        'cold_call',
        'social_media',
        'google_ads',
        'facebook_ads',
        'zillow',
        'realtor_com',
        'open_house',
        'walk_in'
    ])
    
    property_preferences = factory.LazyFunction(lambda: {
        "type": random.choice(['single_family', 'condo', 'townhouse', 'multi_family']),
        "bedrooms": random.randint(1, 6),
        "bathrooms": random.randint(1, 4),
        "min_price": random.randint(150000, 400000),
        "max_price": random.randint(500000, 1500000),
        "square_feet_min": random.randint(800, 2000),
        "square_feet_max": random.randint(2500, 5000),
        "location": fake.city(),
        "features": random.sample([
            "garage",
            "pool",
            "fireplace",
            "hardwood_floors",
            "updated_kitchen",
            "master_suite",
            "basement",
            "deck_patio",
            "security_system",
            "solar_panels"
        ], k=random.randint(2, 5))
    })
    
    qualification_status = factory.fuzzy.FuzzyChoice([
        'new',
        'contacted',
        'interested', 
        'qualified',
        'hot_lead',
        'not_interested',
        'callback_requested',
        'appointment_scheduled',
        'closed_won',
        'closed_lost'
    ])
    
    lead_score = factory.fuzzy.FuzzyInteger(0, 100)
    
    timeline = factory.fuzzy.FuzzyChoice([
        'immediate',
        '1_month',
        '3_months',
        '6_months',
        '1_year',
        'just_looking'
    ])
    
    budget_verified = factory.fuzzy.FuzzyChoice([True, False], probability_true=0.6)
    pre_approved = factory.fuzzy.FuzzyChoice([True, False], probability_true=0.4)
    first_time_buyer = factory.fuzzy.FuzzyChoice([True, False], probability_true=0.5)
    
    tcpa_consent = factory.LazyFunction(lambda: {
        "voice_calls": random.choice([True, False]),
        "text_messages": random.choice([True, False]),
        "consent_date": fake.date_time_between(start_date='-1y', end_date='now').isoformat(),
        "consent_method": random.choice(['web_form', 'phone_call', 'email', 'in_person']),
        "ip_address": fake.ipv4(),
        "user_agent": fake.user_agent()
    })
    
    notes = factory.Faker('text', max_nb_chars=500)
    
    created_at = factory.LazyFunction(
        lambda: fake.date_time_between(start_date='-6m', end_date='now')
    )
    updated_at = factory.LazyAttribute(
        lambda obj: obj.created_at + timedelta(days=random.randint(0, 30))
    )


class ConversationFactory(factory.Factory):
    """Factory for creating test conversations"""
    
    class Meta:
        model = Conversation
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    
    type = factory.fuzzy.FuzzyChoice([
        'inbound_call',
        'outbound_call',
        'callback',
        'scheduled_call',
        'follow_up_call'
    ])
    
    duration_seconds = factory.fuzzy.FuzzyInteger(30, 1800)  # 30 seconds to 30 minutes
    
    transcript = factory.LazyFunction(lambda: generate_realistic_conversation_transcript())
    
    sentiment_score = factory.fuzzy.FuzzyFloat(0.0, 1.0)
    lead_score = factory.fuzzy.FuzzyInteger(0, 100)
    
    status = factory.fuzzy.FuzzyChoice([
        'completed',
        'qualified',
        'interested',
        'not_interested',
        'callback_requested',
        'appointment_scheduled',
        'follow_up_needed',
        'closed_won',
        'closed_lost'
    ])
    
    quality_score = factory.fuzzy.FuzzyFloat(0.0, 10.0)
    
    ai_insights = factory.LazyFunction(lambda: {
        "intent_detected": random.choice([
            "property_search",
            "price_inquiry",
            "schedule_viewing",
            "financing_questions",
            "market_information",
            "general_inquiry"
        ]),
        "emotion_detected": random.choice([
            "neutral", "positive", "excited", "concerned", "frustrated", "interested"
        ]),
        "urgency_level": random.choice(["low", "medium", "high"]),
        "buying_signals": random.sample([
            "budget_mentioned",
            "timeline_specified",
            "location_narrowed",
            "feature_requirements_clear",
            "ready_to_view_properties"
        ], k=random.randint(0, 3)),
        "objections": random.sample([
            "price_concerns",
            "location_issues",
            "timing_not_right",
            "feature_mismatch",
            "financing_concerns"
        ], k=random.randint(0, 2))
    })
    
    recording_url = factory.LazyFunction(
        lambda: f"https://recordings.seiketsu.ai/{uuid.uuid4()}.mp3"
    )
    
    created_at = factory.LazyFunction(
        lambda: fake.date_time_between(start_date='-3m', end_date='now')
    )


class VoiceAgentFactory(factory.Factory):
    """Factory for creating test voice agents"""
    
    class Meta:
        model = VoiceAgent
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    
    name = factory.LazyFunction(lambda: f"{fake.first_name()} {random.choice(['Professional', 'Friendly', 'Expert', 'Specialist'])}")
    
    voice_id = factory.LazyFunction(lambda: f"voice_{random.randint(1000, 9999)}")
    
    personality = factory.fuzzy.FuzzyChoice([
        'professional',
        'friendly',
        'energetic',
        'calm',
        'authoritative',
        'warm',
        'consultative'
    ])
    
    language = factory.fuzzy.FuzzyChoice(['en-US', 'en-GB', 'en-CA', 'es-US'])
    
    pitch = factory.fuzzy.FuzzyFloat(0.7, 1.3)
    speed = factory.fuzzy.FuzzyFloat(0.8, 1.2)
    stability = factory.fuzzy.FuzzyFloat(0.5, 1.0)
    similarity_boost = factory.fuzzy.FuzzyFloat(0.5, 1.0)
    
    script_template = factory.fuzzy.FuzzyChoice([
        'standard_qualifier',
        'luxury_specialist',
        'first_time_buyer',
        'investor_focused',
        'commercial_specialist'
    ])
    
    is_active = factory.fuzzy.FuzzyChoice([True, False], probability_true=0.8)
    
    performance_metrics = factory.LazyFunction(lambda: {
        "total_conversations": random.randint(50, 1000),
        "average_call_duration": random.randint(180, 600),
        "qualification_rate": round(random.uniform(0.4, 0.9), 2),
        "customer_satisfaction": round(random.uniform(3.5, 5.0), 1),
        "conversion_rate": round(random.uniform(0.1, 0.4), 2)
    })
    
    created_at = factory.LazyFunction(
        lambda: fake.date_time_between(start_date='-1y', end_date='now')
    )


class PropertyFactory(factory.Factory):
    """Factory for creating test properties"""
    
    class Meta:
        model = Property
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    mls_id = factory.LazyFunction(lambda: f"MLS{random.randint(100000, 999999)}")
    
    address = factory.Faker('address')
    city = factory.Faker('city')
    state = factory.Faker('state_abbr')
    zip_code = factory.Faker('zipcode')
    
    price = factory.fuzzy.FuzzyInteger(200000, 2000000)
    
    bedrooms = factory.fuzzy.FuzzyInteger(1, 6)
    bathrooms = factory.fuzzy.FuzzyFloat(1.0, 4.5, precision=0.5)
    square_feet = factory.fuzzy.FuzzyInteger(800, 5000)
    lot_size = factory.fuzzy.FuzzyFloat(0.1, 2.0, precision=0.1)
    
    property_type = factory.fuzzy.FuzzyChoice([
        'single_family',
        'condo',
        'townhouse',
        'multi_family',
        'land',
        'commercial',
        'mobile_home'
    ])
    
    listing_status = factory.fuzzy.FuzzyChoice([
        'active',
        'pending',
        'sold',
        'withdrawn',
        'expired'
    ])
    
    year_built = factory.fuzzy.FuzzyInteger(1950, 2024)
    
    features = factory.LazyFunction(lambda: random.sample([
        "garage",
        "pool",
        "fireplace", 
        "hardwood_floors",
        "updated_kitchen",
        "master_suite",
        "basement",
        "deck_patio",
        "security_system",
        "solar_panels",
        "home_office",
        "guest_house",
        "workshop",
        "wine_cellar",
        "gym",
        "theater_room"
    ], k=random.randint(3, 8)))
    
    description = factory.LazyFunction(lambda: generate_property_description())
    
    images = factory.LazyFunction(lambda: [
        f"https://images.seiketsu.ai/properties/{uuid.uuid4()}.jpg"
        for _ in range(random.randint(5, 20))
    ])
    
    market_data = factory.LazyFunction(lambda: {
        "days_on_market": random.randint(1, 180),
        "price_per_sqft": random.randint(100, 500),
        "neighborhood_avg_price": random.randint(300000, 800000),
        "appreciation_rate": round(random.uniform(-0.05, 0.15), 3),
        "walkability_score": random.randint(20, 100),
        "school_rating": random.randint(1, 10)
    })
    
    created_at = factory.LazyFunction(
        lambda: fake.date_time_between(start_date='-2y', end_date='now')
    )
    updated_at = factory.LazyAttribute(
        lambda obj: obj.created_at + timedelta(days=random.randint(0, 30))
    )


class WebhookFactory(factory.Factory):
    """Factory for creating test webhooks"""
    
    class Meta:
        model = Webhook
    
    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    url = factory.Faker('url')
    
    events = factory.LazyFunction(lambda: random.sample([
        'lead.created',
        'lead.updated',
        'lead.qualified',
        'conversation.started',
        'conversation.completed',
        'appointment.scheduled',
        'appointment.completed',
        'property.matched',
        'deal.closed'
    ], k=random.randint(2, 5)))
    
    is_active = factory.fuzzy.FuzzyChoice([True, False], probability_true=0.8)
    
    secret = factory.LazyFunction(lambda: f"webhook_secret_{uuid.uuid4().hex[:16]}")
    
    retry_attempts = factory.fuzzy.FuzzyInteger(1, 5)
    timeout_seconds = factory.fuzzy.FuzzyInteger(10, 60)
    
    headers = factory.LazyFunction(lambda: {
        "Content-Type": "application/json",
        "User-Agent": "Seiketsu-Webhook/1.0",
        "X-Custom-Header": f"custom_{random.randint(1000, 9999)}"
    })
    
    delivery_stats = factory.LazyFunction(lambda: {
        "total_attempts": random.randint(0, 1000),
        "successful_deliveries": random.randint(0, 950),
        "failed_deliveries": random.randint(0, 50),
        "last_success": fake.date_time_between(start_date='-1w', end_date='now').isoformat(),
        "last_failure": fake.date_time_between(start_date='-1m', end_date='-1w').isoformat() if random.choice([True, False]) else None
    })
    
    created_at = factory.LazyFunction(
        lambda: fake.date_time_between(start_date='-6m', end_date='now')
    )


# Helper functions for generating realistic data

def generate_realistic_conversation_transcript():
    """Generate realistic conversation transcript"""
    agent_intros = [
        "Hello! This is Sarah from Premier Real Estate. How are you today?",
        "Hi there! I'm calling from Downtown Realty regarding your property inquiry.",
        "Good morning! This is Mike from Luxury Homes. Thanks for your interest in our listings."
    ]
    
    client_responses = [
        "Hi Sarah, I'm doing well. I'm actually looking for a new home.",
        "Oh yes, I submitted a form on your website yesterday.",
        "Good morning! I've been searching for properties in the downtown area."
    ]
    
    agent_follow_ups = [
        "That's wonderful! I'd love to help you find the perfect home. What type of property are you looking for?",
        "Great! I see you're interested in 3-bedroom homes. What's your preferred neighborhood?",
        "Excellent! The downtown market is really exciting right now. What's your budget range?"
    ]
    
    # Generate multi-turn conversation
    transcript_parts = [
        f"Agent: {random.choice(agent_intros)}",
        f"Client: {random.choice(client_responses)}",
        f"Agent: {random.choice(agent_follow_ups)}",
        f"Client: {generate_client_response()}",
        f"Agent: {generate_agent_response()}",
        f"Client: {generate_client_response()}",
        f"Agent: {generate_closing_statement()}"
    ]
    
    return "\n\n".join(transcript_parts)


def generate_client_response():
    """Generate realistic client response"""
    responses = [
        "I'm looking for a 3-bedroom house with a good school district. My budget is around $500,000.",
        "We need something with at least 2,000 square feet and a garage. Location is flexible.",
        "I'm interested in condos downtown, preferably with modern amenities and parking.",
        "We're first-time buyers, so we need something move-in ready under $400,000.",
        "I'm looking for investment properties, maybe multi-family homes or duplexes.",
        "We want something in a quiet neighborhood, good for kids, with a backyard.",
        "I need to be close to public transportation for my commute to the city."
    ]
    return random.choice(responses)


def generate_agent_response():
    """Generate realistic agent response"""
    responses = [
        "Perfect! I have several properties that match your criteria. Let me show you some options.",
        "That sounds great! The school district you mentioned is excellent. I can arrange viewings this weekend.",
        "Wonderful! I know exactly the type of property you're looking for. Are you pre-approved for financing?",
        "Excellent choice for first-time buyers! I have some great starter homes to show you.",
        "Investment properties are a smart choice in this market. I specialize in rental properties.",
        "Family-friendly neighborhoods are my specialty. I have some perfect options for you.",
        "Transportation access is crucial. I have listings near three different transit lines."
    ]
    return random.choice(responses)


def generate_closing_statement():
    """Generate realistic conversation closing"""
    closings = [
        "I'll send you some listings that match your criteria and we can schedule viewings. When works best for you?",
        "This has been a great start! I'll prepare a market analysis and call you tomorrow to discuss next steps.",
        "I'm excited to help you find your perfect home! Let me know if you have any other questions.",
        "I'll get those property details to you today. Thanks for taking the time to speak with me!",
        "Based on our conversation, I have the perfect properties in mind. I'll be in touch soon!"
    ]
    return random.choice(closings)


def generate_property_description():
    """Generate realistic property description"""
    templates = [
        "Beautiful {bedrooms}-bedroom {property_type} in desirable {neighborhood}. Features {feature1}, {feature2}, and {feature3}. Perfect for {buyer_type}. {highlight}",
        "Stunning {property_type} with {bedrooms} bedrooms and {bathrooms} bathrooms. This home boasts {feature1}, {feature2}, and {feature3}. Located in {neighborhood}. {highlight}",
        "Move-in ready {property_type} featuring {bedrooms} spacious bedrooms. Highlights include {feature1}, {feature2}, and {feature3}. Great {neighborhood} location. {highlight}"
    ]
    
    template = random.choice(templates)
    
    features = ["updated kitchen", "hardwood floors", "master suite", "two-car garage", 
               "backyard patio", "fireplace", "basement", "home office"]
    
    neighborhoods = ["downtown", "suburban", "waterfront", "historic district", 
                    "family-friendly", "up-and-coming"]
    
    buyer_types = ["families", "first-time buyers", "professionals", "investors", "retirees"]
    
    highlights = [
        "Don't miss this opportunity!",
        "Priced to sell quickly.",
        "Virtual tour available.",
        "Schedule your showing today!",
        "New to market - won't last long!"
    ]
    
    return template.format(
        bedrooms=random.randint(2, 5),
        bathrooms=random.randint(1, 4),
        property_type=random.choice(["home", "house", "property", "residence"]),
        neighborhood=random.choice(neighborhoods),
        feature1=random.choice(features),
        feature2=random.choice([f for f in features if f != template]),
        feature3=random.choice([f for f in features if f not in [template]]),
        buyer_type=random.choice(buyer_types),
        highlight=random.choice(highlights)
    )


# Factory trait classes for specific test scenarios

class QualifiedLeadFactory(LeadFactory):
    """Factory for qualified leads"""
    qualification_status = 'qualified'
    lead_score = factory.fuzzy.FuzzyInteger(75, 100)
    budget_verified = True
    tcpa_consent = factory.LazyFunction(lambda: {
        "voice_calls": True,
        "text_messages": True,
        "consent_date": fake.date_time_between(start_date='-1m', end_date='now').isoformat(),
        "consent_method": "web_form"
    })


class HotLeadFactory(LeadFactory):
    """Factory for hot leads"""
    qualification_status = 'hot_lead'
    lead_score = factory.fuzzy.FuzzyInteger(85, 100)
    budget_verified = True
    pre_approved = True
    timeline = factory.fuzzy.FuzzyChoice(['immediate', '1_month'])


class LuxuryPropertyFactory(PropertyFactory):
    """Factory for luxury properties"""
    price = factory.fuzzy.FuzzyInteger(1000000, 5000000)
    square_feet = factory.fuzzy.FuzzyInteger(3000, 8000)
    bedrooms = factory.fuzzy.FuzzyInteger(4, 8)
    bathrooms = factory.fuzzy.FuzzyFloat(3.0, 6.5, precision=0.5)
    
    features = factory.LazyFunction(lambda: [
        "gourmet_kitchen", "wine_cellar", "home_theater", "gym", "pool", 
        "guest_house", "security_system", "smart_home", "marble_counters", 
        "hardwood_floors", "fireplace", "master_suite", "walk_in_closets"
    ])


class CommercialPropertyFactory(PropertyFactory):
    """Factory for commercial properties"""
    property_type = 'commercial'
    price = factory.fuzzy.FuzzyInteger(500000, 10000000)
    square_feet = factory.fuzzy.FuzzyInteger(2000, 50000)
    
    features = factory.LazyFunction(lambda: [
        "parking_lot", "loading_dock", "office_space", "warehouse", 
        "retail_space", "conference_rooms", "elevator", "security_system"
    ])


# Batch factories for creating multiple related objects

def create_organization_with_users_and_leads(num_users=5, num_leads=20):
    """Create an organization with users and leads"""
    org = OrganizationFactory()
    
    users = []
    for _ in range(num_users):
        user = UserFactory(organization_id=org.id)
        users.append(user)
    
    leads = []
    for _ in range(num_leads):
        lead = LeadFactory(
            organization_id=org.id,
            assigned_agent_id=random.choice(users).id if users else None
        )
        leads.append(lead)
    
    return {
        'organization': org,
        'users': users,
        'leads': leads
    }


def create_complete_sales_scenario():
    """Create a complete sales scenario with related objects"""
    org = OrganizationFactory()
    agent = UserFactory(organization_id=org.id, role='agent')
    lead = QualifiedLeadFactory(organization_id=org.id, assigned_agent_id=agent.id)
    
    # Create conversation between agent and lead
    conversation = ConversationFactory(
        organization_id=org.id,
        lead_id=lead.id,
        agent_id=agent.id,
        status='qualified'
    )
    
    # Create matching properties
    properties = []
    for _ in range(3):
        prop = PropertyFactory(
            organization_id=org.id,
            bedrooms=lead.property_preferences['bedrooms'],
            price=random.randint(
                lead.property_preferences['min_price'],
                lead.property_preferences['max_price']
            )
        )
        properties.append(prop)
    
    return {
        'organization': org,
        'agent': agent,
        'lead': lead,
        'conversation': conversation,
        'properties': properties
    }