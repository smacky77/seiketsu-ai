"""
Property model for real estate listings
"""
from sqlalchemy import Column, String, Boolean, Integer, Float, Text, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List

from .base import BaseModel, TenantMixin, AuditMixin


class PropertyStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    DRAFT = "draft"


class PropertyType(str, Enum):
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    COMMERCIAL = "commercial"
    LAND = "land"
    MANUFACTURED = "manufactured"
    OTHER = "other"


class ListingType(str, Enum):
    FOR_SALE = "for_sale"
    FOR_RENT = "for_rent"
    SOLD = "sold"
    RENTED = "rented"


class Property(BaseModel, TenantMixin, AuditMixin):
    """Real estate property listing"""
    __tablename__ = "properties"
    
    # MLS and identification
    mls_number = Column(String(100), unique=True, index=True)
    internal_id = Column(String(100), index=True)
    
    # Basic information
    title = Column(String(500), nullable=False)
    description = Column(Text)
    property_type = Column(SQLEnum(PropertyType), nullable=False)
    listing_type = Column(SQLEnum(ListingType), default=ListingType.FOR_SALE)
    status = Column(SQLEnum(PropertyStatus), default=PropertyStatus.DRAFT)
    
    # Address
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False, index=True)
    postal_code = Column(String(20), index=True)
    country = Column(String(100), default="US")
    county = Column(String(100))
    
    # Geographic coordinates
    latitude = Column(Float, index=True)
    longitude = Column(Float, index=True)
    
    # Property details
    bedrooms = Column(Integer, index=True)
    bathrooms = Column(Float, index=True)
    half_bathrooms = Column(Integer)
    square_feet = Column(Integer, index=True)
    lot_size_sqft = Column(Float)
    lot_size_acres = Column(Float)
    
    # Building details
    year_built = Column(Integer, index=True)
    stories = Column(Integer)
    garage_spaces = Column(Integer)
    parking_spaces = Column(Integer)
    
    # Pricing
    list_price = Column(Integer, nullable=False, index=True)
    original_price = Column(Integer)
    price_per_sqft = Column(Float)
    
    # For rentals
    rent_price = Column(Integer, index=True)
    security_deposit = Column(Integer)
    
    # HOA and fees
    hoa_fee = Column(Float)
    hoa_fee_frequency = Column(String(50))  # "monthly", "quarterly", "annually"
    
    # Property features
    features = Column(JSON, default=list)  # ["pool", "fireplace", "hardwood_floors"]
    appliances = Column(JSON, default=list)  # ["refrigerator", "washer", "dryer"]
    utilities_included = Column(JSON, default=list)  # ["water", "sewer", "electric"]
    
    # Listing details
    listing_date = Column(DateTime, index=True)
    days_on_market = Column(Integer, default=0)
    
    # Media
    primary_photo_url = Column(String(500))
    photo_urls = Column(JSON, default=list)
    virtual_tour_url = Column(String(500))
    video_tour_url = Column(String(500))
    
    # School information
    school_district = Column(String(255))
    elementary_school = Column(String(255))
    middle_school = Column(String(255))
    high_school = Column(String(255))
    
    # Neighborhood data
    neighborhood = Column(String(255), index=True)
    walkability_score = Column(Integer)  # 0-100
    transit_score = Column(Integer)  # 0-100
    bike_score = Column(Integer)  # 0-100
    
    # Agent information
    listing_agent_name = Column(String(255))
    listing_agent_phone = Column(String(50))
    listing_agent_email = Column(String(255))
    listing_office = Column(String(255))
    
    # Showing information
    showing_instructions = Column(Text)
    lockbox_code = Column(String(100))  # Encrypted
    showing_restrictions = Column(Text)
    
    # Marketing
    marketing_remarks = Column(Text)
    private_remarks = Column(Text)  # Internal notes
    
    # Financial details
    taxes_annual = Column(Float)
    tax_year = Column(Integer)
    zoning = Column(String(100))
    
    # Additional data
    custom_fields = Column(JSON, default=dict)
    amenities = Column(JSON, default=list)
    nearby_attractions = Column(JSON, default=list)
    
    # Syndication and feeds
    syndicated_to = Column(JSON, default=list)  # ["zillow", "realtor.com", "trulia"]
    feed_last_updated = Column(DateTime)
    
    # Organization relationship
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False, index=True)
    organization = relationship("Organization", back_populates="properties")
    
    def __repr__(self):
        return f"<Property(id={self.id}, mls={self.mls_number}, address={self.address_line1})>"
    
    @property
    def full_address(self) -> str:
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.extend([self.city, self.state, self.postal_code])
        return ", ".join(filter(None, parts))
    
    @property
    def price_formatted(self) -> str:
        if self.listing_type == ListingType.FOR_RENT:
            return f"${self.rent_price:,}/month" if self.rent_price else "Price not available"
        return f"${self.list_price:,}" if self.list_price else "Price not available"
    
    @property
    def bedrooms_bathrooms_display(self) -> str:
        bed_str = f"{self.bedrooms} bed" if self.bedrooms else "- bed"
        bath_str = f"{self.bathrooms} bath" if self.bathrooms else "- bath"
        return f"{bed_str}, {bath_str}"
    
    @property
    def is_active_listing(self) -> bool:
        return self.status == PropertyStatus.ACTIVE
    
    @property
    def coordinates(self) -> Optional[Dict[str, float]]:
        if self.latitude and self.longitude:
            return {"lat": self.latitude, "lng": self.longitude}
        return None
    
    def calculate_days_on_market(self):
        """Calculate and update days on market"""
        if self.listing_date:
            self.days_on_market = (datetime.utcnow() - self.listing_date).days
        return self.days_on_market
    
    def calculate_price_per_sqft(self):
        """Calculate and update price per square foot"""
        if self.list_price and self.square_feet and self.square_feet > 0:
            self.price_per_sqft = round(self.list_price / self.square_feet, 2)
        return self.price_per_sqft
    
    def add_feature(self, feature: str):
        """Add a feature to the property"""
        features = self.features or []
        if feature not in features:
            features.append(feature)
            self.features = features
    
    def remove_feature(self, feature: str):
        """Remove a feature from the property"""
        features = self.features or []
        if feature in features:
            features.remove(feature)
            self.features = features
    
    def update_from_mls_data(self, mls_data: Dict[str, Any]):
        """Update property from MLS data feed"""
        mapping = {
            "ListPrice": "list_price",
            "Bedrooms": "bedrooms", 
            "Bathrooms": "bathrooms",
            "SquareFeet": "square_feet",
            "YearBuilt": "year_built",
            "LotSize": "lot_size_sqft",
            "ListingDate": "listing_date",
            "Status": "status",
            "PublicRemarks": "description"
        }
        
        for mls_field, property_field in mapping.items():
            if mls_field in mls_data:
                setattr(self, property_field, mls_data[mls_field])
        
        # Update calculated fields
        self.calculate_days_on_market()
        self.calculate_price_per_sqft()
        self.feed_last_updated = datetime.utcnow()
    
    def get_search_keywords(self) -> List[str]:
        """Generate search keywords for property"""
        keywords = []
        
        # Location
        keywords.extend([self.city, self.state, self.neighborhood, self.postal_code])
        
        # Property type
        keywords.append(self.property_type.value.replace("_", " "))
        
        # Features
        if self.features:
            keywords.extend(self.features)
        
        # Price range
        if self.list_price:
            if self.list_price < 200000:
                keywords.append("affordable")
            elif self.list_price > 1000000:
                keywords.append("luxury")
        
        # Size
        if self.bedrooms:
            keywords.append(f"{self.bedrooms} bedroom")
        
        return [k.lower() for k in keywords if k]