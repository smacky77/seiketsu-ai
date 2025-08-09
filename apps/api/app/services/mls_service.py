"""
MLS (Multiple Listing Service) Integration
Real estate data access with caching and rate limiting
"""

import asyncio
import logging
import json
import aiohttp
import time
import hashlib
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ..core.config import settings
from ..core.exceptions import ExternalServiceException, RateLimitException, ServiceUnavailableException
from ..utils.circuit_breaker import CircuitBreaker
from ..utils.retry_decorator import retry_async
from ..utils.rate_limiter import RateLimiter
from ..services.usage_service import UsageService

logger = logging.getLogger(__name__)

class PropertyType(Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    LAND = "land"
    RENTAL = "rental"

class PropertyStatus(Enum):
    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"

class SortOrder(Enum):
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    DATE_ASC = "date_asc"
    DATE_DESC = "date_desc"
    SQFT_ASC = "sqft_asc"
    SQFT_DESC = "sqft_desc"

@dataclass
class PropertySearchFilters:
    property_type: Optional[PropertyType] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    min_beds: Optional[int] = None
    max_beds: Optional[int] = None
    min_baths: Optional[float] = None
    max_baths: Optional[float] = None
    min_sqft: Optional[int] = None
    max_sqft: Optional[int] = None
    zip_codes: Optional[List[str]] = None
    cities: Optional[List[str]] = None
    counties: Optional[List[str]] = None
    status: Optional[PropertyStatus] = None
    days_on_market: Optional[int] = None
    year_built_min: Optional[int] = None
    year_built_max: Optional[int] = None
    
@dataclass
class PropertyDetails:
    listing_id: str
    mls_number: str
    property_type: str
    status: str
    list_price: int
    address: Dict[str, str]
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    square_feet: Optional[int]
    lot_size: Optional[float]
    year_built: Optional[int]
    description: Optional[str]
    photos: List[str]
    agent_info: Dict[str, str]
    listing_date: datetime
    updated_date: datetime
    days_on_market: int
    price_per_sqft: Optional[float]
    property_features: List[str]
    school_district: Optional[str]
    hoa_fees: Optional[float]
    taxes: Optional[Dict[str, Any]]

class MLSService:
    """
    Production-ready MLS integration for real estate data
    """
    
    def __init__(self):
        self.api_key = settings.MLS_API_KEY
        self.base_url = "https://api.mlsgrid.com/v2"
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.usage_service = UsageService()
        
        # Circuit breaker for fault tolerance
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=ExternalServiceException
        )
        
        # Rate limiter for API calls (MLS typically has strict limits)
        self.rate_limiter = RateLimiter(
            requests_per_second=2,  # Conservative rate for MLS APIs
            burst_size=5
        )
        
        # Session for connection reuse
        self.session = None
        
        # Data cache for performance
        self._property_cache = {}
        self._search_cache = {}
        self._cache_ttl = 1800  # 30 minutes for property data
        self._search_cache_ttl = 300  # 5 minutes for search results
        self._cache_updated = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def _ensure_session(self):
        """Ensure HTTP session is initialized"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=50,
                limit_per_host=20,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": f"Seiketsu-AI/{settings.APP_VERSION}"
                }
            )
            
    def _generate_cache_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate cache key from parameters"""
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"{prefix}:{params_hash}"
        
    def _is_cache_valid(self, cache_key: str, ttl: int) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache_updated:
            return False
        cache_time = self._cache_updated[cache_key]
        return time.time() - cache_time < ttl
        
    @retry_async(max_attempts=3, backoff_factor=2.0)
    async def search_properties(
        self,
        filters: PropertySearchFilters,
        client_id: str,
        limit: int = 50,
        offset: int = 0,
        sort: SortOrder = SortOrder.DATE_DESC,
        include_photos: bool = True,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Search properties based on filters
        
        Args:
            filters: Search filters
            client_id: Client identifier for usage tracking
            limit: Maximum results to return
            offset: Results offset for pagination
            sort: Sort order
            include_photos: Include property photos
            include_details: Include detailed property information
            
        Returns:
            Search results with properties and metadata
        """
        try:
            await self._ensure_session()
            await self.rate_limiter.acquire()
            
            # Build search parameters
            search_params = self._build_search_params(filters, limit, offset, sort)
            
            # Check cache
            cache_key = self._generate_cache_key("search", {
                **search_params,
                "include_photos": include_photos,
                "include_details": include_details
            })
            
            if self._is_cache_valid(cache_key, self._search_cache_ttl):
                cached_result = self._search_cache.get(cache_key)
                if cached_result:
                    logger.info(f"Returning cached search results for client {client_id}")
                    return {**cached_result, "from_cache": True}
            
            # Track MLS query usage
            usage_result = await self.usage_service.track_api_usage(
                client_id=client_id,
                service="mls",
                usage_data={
                    "queries_made": 1,
                    "query_type": "property_search",
                    "filters": len([f for f in [
                        filters.property_type, filters.min_price, filters.max_price,
                        filters.min_beds, filters.status
                    ] if f is not None])
                }
            )
            
            if not usage_result.get("success"):
                raise ExternalServiceException("mls", f"Usage limit exceeded: {usage_result.get('error')}")
            
            start_time = time.time()
            
            async with self.circuit_breaker:
                # Make API request
                url = f"{self.base_url}/Property"
                
                async with self.session.get(url, params=search_params) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 300))
                        raise RateLimitException(
                            message="MLS API rate limit exceeded",
                            retry_after=retry_after
                        )
                    
                    if response.status >= 400:
                        error_data = await response.text()
                        logger.error(f"MLS API error {response.status}: {error_data}")
                        raise ExternalServiceException(
                            "mls",
                            f"Property search failed: {error_data}",
                            service_error_code=str(response.status)
                        )
                    
                    data = await response.json()
                    
                    # Process results
                    properties = await self._process_search_results(
                        data.get("value", []),
                        include_photos,
                        include_details
                    )
                    
                    result = {
                        "success": True,
                        "properties": properties,
                        "total_count": data.get("@odata.count", len(properties)),
                        "returned_count": len(properties),
                        "offset": offset,
                        "limit": limit,
                        "has_more": len(properties) == limit,
                        "search_filters": filters.__dict__,
                        "response_time": response_time,
                        "from_cache": False
                    }
                    
                    # Cache results
                    self._search_cache[cache_key] = result
                    self._cache_updated[cache_key] = time.time()
                    
                    logger.info(f"Property search completed: {len(properties)} results in {response_time:.2f}s")
                    
                    return result
                    
        except (RateLimitException, ExternalServiceException):
            raise
        except Exception as e:
            logger.error(f"Property search failed: {str(e)}")
            raise ExternalServiceException("mls", f"Property search failed: {str(e)}")
            
    def _build_search_params(
        self,
        filters: PropertySearchFilters,
        limit: int,
        offset: int,
        sort: SortOrder
    ) -> Dict[str, Any]:
        """Build OData query parameters for search"""
        params = {
            "$top": limit,
            "$skip": offset,
            "$count": "true"
        }
        
        # Build filter conditions
        filter_conditions = []
        
        if filters.property_type:
            filter_conditions.append(f"PropertyType eq '{filters.property_type.value}'")
            
        if filters.status:
            filter_conditions.append(f"StandardStatus eq '{filters.status.value}'")
            
        if filters.min_price is not None:
            filter_conditions.append(f"ListPrice ge {filters.min_price}")
            
        if filters.max_price is not None:
            filter_conditions.append(f"ListPrice le {filters.max_price}")
            
        if filters.min_beds is not None:
            filter_conditions.append(f"BedroomsTotal ge {filters.min_beds}")
            
        if filters.max_beds is not None:
            filter_conditions.append(f"BedroomsTotal le {filters.max_beds}")
            
        if filters.min_baths is not None:
            filter_conditions.append(f"BathroomsTotalDecimal ge {filters.min_baths}")
            
        if filters.max_baths is not None:
            filter_conditions.append(f"BathroomsTotalDecimal le {filters.max_baths}")
            
        if filters.min_sqft is not None:
            filter_conditions.append(f"LivingArea ge {filters.min_sqft}")
            
        if filters.max_sqft is not None:
            filter_conditions.append(f"LivingArea le {filters.max_sqft}")
            
        if filters.year_built_min is not None:
            filter_conditions.append(f"YearBuilt ge {filters.year_built_min}")
            
        if filters.year_built_max is not None:
            filter_conditions.append(f"YearBuilt le {filters.year_built_max}")
            
        if filters.days_on_market is not None:
            filter_conditions.append(f"DaysOnMarket le {filters.days_on_market}")
            
        if filters.zip_codes:
            zip_filter = " or ".join([f"PostalCode eq '{zip_code}'" for zip_code in filters.zip_codes])
            filter_conditions.append(f"({zip_filter})")
            
        if filters.cities:
            city_filter = " or ".join([f"City eq '{city}'" for city in filters.cities])
            filter_conditions.append(f"({city_filter})")
            
        if filters.counties:
            county_filter = " or ".join([f"CountyOrParish eq '{county}'" for county in filters.counties])
            filter_conditions.append(f"({county_filter})")
        
        # Add basic active listing filter by default
        if not filters.status:
            filter_conditions.append("StandardStatus eq 'Active'")
            
        if filter_conditions:
            params["$filter"] = " and ".join(filter_conditions)
        
        # Add sorting
        sort_mapping = {
            SortOrder.PRICE_ASC: "ListPrice asc",
            SortOrder.PRICE_DESC: "ListPrice desc",
            SortOrder.DATE_ASC: "OnMarketDate asc",
            SortOrder.DATE_DESC: "OnMarketDate desc",
            SortOrder.SQFT_ASC: "LivingArea asc",
            SortOrder.SQFT_DESC: "LivingArea desc"
        }
        
        params["$orderby"] = sort_mapping.get(sort, "OnMarketDate desc")
        
        return params
        
    async def _process_search_results(
        self,
        raw_properties: List[Dict[str, Any]],
        include_photos: bool,
        include_details: bool
    ) -> List[Dict[str, Any]]:
        """Process and enhance search results"""
        processed_properties = []
        
        for prop in raw_properties:
            try:
                processed_prop = {
                    "listing_id": prop.get("ListingId"),
                    "mls_number": prop.get("MLSNumber"),
                    "property_type": prop.get("PropertyType"),
                    "status": prop.get("StandardStatus"),
                    "list_price": prop.get("ListPrice"),
                    "address": {
                        "street": prop.get("UnparsedAddress"),
                        "city": prop.get("City"),
                        "state": prop.get("StateOrProvince"),
                        "zip_code": prop.get("PostalCode"),
                        "county": prop.get("CountyOrParish")
                    },
                    "bedrooms": prop.get("BedroomsTotal"),
                    "bathrooms": prop.get("BathroomsTotalDecimal"),
                    "square_feet": prop.get("LivingArea"),
                    "lot_size": prop.get("LotSizeSquareFeet"),
                    "year_built": prop.get("YearBuilt"),
                    "days_on_market": prop.get("DaysOnMarket"),
                    "listing_date": prop.get("OnMarketDate"),
                    "updated_date": prop.get("ModificationTimestamp"),
                }
                
                # Calculate price per square foot
                if processed_prop["list_price"] and processed_prop["square_feet"]:
                    processed_prop["price_per_sqft"] = round(
                        processed_prop["list_price"] / processed_prop["square_feet"], 2
                    )
                    
                # Add photos if requested
                if include_photos:
                    processed_prop["photos"] = await self._get_property_photos(
                        prop.get("ListingId")
                    )
                    
                # Add detailed information if requested
                if include_details:
                    processed_prop.update(await self._get_property_details(
                        prop.get("ListingId")
                    ))
                    
                processed_properties.append(processed_prop)
                
            except Exception as e:
                logger.warning(f"Failed to process property {prop.get('ListingId')}: {str(e)}")
                continue
                
        return processed_properties
        
    async def _get_property_photos(self, listing_id: str) -> List[str]:
        """Get property photos URLs"""
        try:
            # Check cache first
            cache_key = f"photos:{listing_id}"
            if self._is_cache_valid(cache_key, self._cache_ttl):
                cached_photos = self._property_cache.get(cache_key)
                if cached_photos is not None:
                    return cached_photos
            
            url = f"{self.base_url}/Media"
            params = {
                "$filter": f"ResourceRecordKey eq '{listing_id}'",
                "$select": "MediaURL,MediaType"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    photos = [
                        media.get("MediaURL") 
                        for media in data.get("value", [])
                        if media.get("MediaType") == "Photo" and media.get("MediaURL")
                    ]
                    
                    # Cache photos
                    self._property_cache[cache_key] = photos
                    self._cache_updated[cache_key] = time.time()
                    
                    return photos
                else:
                    logger.warning(f"Failed to fetch photos for listing {listing_id}")
                    return []
                    
        except Exception as e:
            logger.warning(f"Error fetching photos for listing {listing_id}: {str(e)}")
            return []
            
    async def _get_property_details(self, listing_id: str) -> Dict[str, Any]:
        """Get additional property details"""
        try:
            # Check cache first
            cache_key = f"details:{listing_id}"
            if self._is_cache_valid(cache_key, self._cache_ttl):
                cached_details = self._property_cache.get(cache_key)
                if cached_details is not None:
                    return cached_details
            
            details = {
                "description": "",
                "property_features": [],
                "school_district": None,
                "hoa_fees": None,
                "taxes": {}
            }
            
            # This would be expanded based on specific MLS API capabilities
            # For now, return basic structure
            
            # Cache details
            self._property_cache[cache_key] = details
            self._cache_updated[cache_key] = time.time()
            
            return details
            
        except Exception as e:
            logger.warning(f"Error fetching details for listing {listing_id}: {str(e)}")
            return {}
            
    @retry_async(max_attempts=3, backoff_factor=2.0)
    async def get_property_by_id(
        self,
        listing_id: str,
        client_id: str,
        include_photos: bool = True,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Get specific property by listing ID
        
        Args:
            listing_id: MLS listing ID
            client_id: Client identifier for usage tracking
            include_photos: Include property photos
            include_details: Include detailed information
            
        Returns:
            Property details
        """
        try:
            await self._ensure_session()
            await self.rate_limiter.acquire()
            
            # Check cache
            cache_key = self._generate_cache_key("property", {
                "listing_id": listing_id,
                "include_photos": include_photos,
                "include_details": include_details
            })
            
            if self._is_cache_valid(cache_key, self._cache_ttl):
                cached_result = self._property_cache.get(cache_key)
                if cached_result:
                    logger.info(f"Returning cached property {listing_id}")
                    return {**cached_result, "from_cache": True}
            
            # Track usage
            usage_result = await self.usage_service.track_api_usage(
                client_id=client_id,
                service="mls",
                usage_data={
                    "queries_made": 1,
                    "query_type": "property_detail",
                    "listing_id": listing_id
                }
            )
            
            if not usage_result.get("success"):
                raise ExternalServiceException("mls", f"Usage limit exceeded: {usage_result.get('error')}")
            
            start_time = time.time()
            
            async with self.circuit_breaker:
                url = f"{self.base_url}/Property"
                params = {
                    "$filter": f"ListingId eq '{listing_id}'"
                }
                
                async with self.session.get(url, params=params) as response:
                    response_time = time.time() - start_time
                    
                    if response.status >= 400:
                        error_data = await response.text()
                        raise ExternalServiceException(
                            "mls",
                            f"Property lookup failed: {error_data}",
                            service_error_code=str(response.status)
                        )
                    
                    data = await response.json()
                    properties = data.get("value", [])
                    
                    if not properties:
                        raise ExternalServiceException("mls", f"Property not found: {listing_id}")
                    
                    # Process the property
                    processed_properties = await self._process_search_results(
                        properties,
                        include_photos,
                        include_details
                    )
                    
                    if not processed_properties:
                        raise ExternalServiceException("mls", f"Failed to process property: {listing_id}")
                    
                    result = {
                        "success": True,
                        "property": processed_properties[0],
                        "response_time": response_time,
                        "from_cache": False
                    }
                    
                    # Cache result
                    self._property_cache[cache_key] = result
                    self._cache_updated[cache_key] = time.time()
                    
                    logger.info(f"Property lookup completed: {listing_id} in {response_time:.2f}s")
                    
                    return result
                    
        except ExternalServiceException:
            raise
        except Exception as e:
            logger.error(f"Property lookup failed: {str(e)}")
            raise ExternalServiceException("mls", f"Property lookup failed: {str(e)}")
            
    async def get_market_statistics(
        self,
        filters: PropertySearchFilters,
        client_id: str,
        period_days: int = 90
    ) -> Dict[str, Any]:
        """
        Get market statistics for given filters
        
        Args:
            filters: Market area filters
            client_id: Client identifier
            period_days: Period for statistics calculation
            
        Returns:
            Market statistics and trends
        """
        try:
            await self._ensure_session()
            await self.rate_limiter.acquire()
            
            # Track usage
            await self.usage_service.track_api_usage(
                client_id=client_id,
                service="mls",
                usage_data={
                    "queries_made": 1,
                    "query_type": "market_stats",
                    "period_days": period_days
                }
            )
            
            # For this example, we'll calculate basic statistics
            # In a real implementation, this might involve multiple API calls
            # or a specialized statistics endpoint
            
            # Get recent sales
            filters.status = PropertyStatus.SOLD
            search_params = self._build_search_params(filters, 1000, 0, SortOrder.DATE_DESC)
            
            # Add date filter for the period
            date_cutoff = datetime.now() - timedelta(days=period_days)
            date_filter = f"CloseDate ge {date_cutoff.isoformat()}"
            
            if search_params.get("$filter"):
                search_params["$filter"] += f" and {date_filter}"
            else:
                search_params["$filter"] = date_filter
            
            async with self.circuit_breaker:
                url = f"{self.base_url}/Property"
                
                async with self.session.get(url, params=search_params) as response:
                    if response.status >= 400:
                        error_data = await response.text()
                        raise ExternalServiceException(
                            "mls",
                            f"Market statistics failed: {error_data}",
                            service_error_code=str(response.status)
                        )
                    
                    data = await response.json()
                    properties = data.get("value", [])
                    
                    # Calculate statistics
                    stats = self._calculate_market_stats(properties, period_days)
                    
                    return {
                        "success": True,
                        "statistics": stats,
                        "period_days": period_days,
                        "sample_size": len(properties),
                        "generated_at": datetime.utcnow().isoformat()
                    }
                    
        except ExternalServiceException:
            raise
        except Exception as e:
            logger.error(f"Market statistics failed: {str(e)}")
            raise ExternalServiceException("mls", f"Market statistics failed: {str(e)}")
            
    def _calculate_market_stats(self, properties: List[Dict[str, Any]], period_days: int) -> Dict[str, Any]:
        """Calculate market statistics from property data"""
        if not properties:
            return {
                "total_sales": 0,
                "average_price": 0,
                "median_price": 0,
                "average_days_on_market": 0,
                "price_per_sqft": {"average": 0, "median": 0},
                "inventory_trends": "insufficient_data"
            }
        
        prices = [p.get("ListPrice", 0) for p in properties if p.get("ListPrice")]
        days_on_market = [p.get("DaysOnMarket", 0) for p in properties if p.get("DaysOnMarket")]
        
        # Price per square foot
        price_per_sqft = []
        for p in properties:
            if p.get("ListPrice") and p.get("LivingArea"):
                price_per_sqft.append(p["ListPrice"] / p["LivingArea"])
        
        stats = {
            "total_sales": len(properties),
            "average_price": sum(prices) / len(prices) if prices else 0,
            "median_price": sorted(prices)[len(prices) // 2] if prices else 0,
            "average_days_on_market": sum(days_on_market) / len(days_on_market) if days_on_market else 0,
            "price_per_sqft": {
                "average": sum(price_per_sqft) / len(price_per_sqft) if price_per_sqft else 0,
                "median": sorted(price_per_sqft)[len(price_per_sqft) // 2] if price_per_sqft else 0
            }
        }
        
        # Determine trend (simplified)
        if stats["average_days_on_market"] < 30:
            stats["market_trend"] = "hot"
        elif stats["average_days_on_market"] < 60:
            stats["market_trend"] = "balanced"
        else:
            stats["market_trend"] = "slow"
            
        return stats
        
    async def health_check(self) -> Dict[str, Any]:
        """Health check for MLS service"""
        try:
            if not self.api_key:
                return {
                    "service": "mls",
                    "status": "unhealthy",
                    "error": "API key not configured",
                    "last_checked": datetime.utcnow().isoformat()
                }
            
            start_time = time.time()
            
            # Test API connectivity
            await self._ensure_session()
            
            url = f"{self.base_url}/Property"
            params = {"$top": 1}
            
            async with self.session.get(url, params=params) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    return {
                        "service": "mls",
                        "status": "healthy",
                        "response_time": response_time,
                        "api_key_configured": True,
                        "circuit_breaker_state": self.circuit_breaker.state,
                        "cache_entries": len(self._property_cache),
                        "last_checked": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "service": "mls",
                        "status": "unhealthy",
                        "error": f"API returned status {response.status}",
                        "circuit_breaker_state": self.circuit_breaker.state,
                        "last_checked": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            return {
                "service": "mls",
                "status": "unhealthy",
                "error": str(e),
                "circuit_breaker_state": self.circuit_breaker.state,
                "last_checked": datetime.utcnow().isoformat()
            }
            
    async def clear_cache(self):
        """Clear all cached data"""
        self._property_cache.clear()
        self._search_cache.clear()
        self._cache_updated.clear()
        logger.info("MLS cache cleared")
        
    async def cleanup(self):
        """Clean up resources"""
        if self.session and not self.session.closed:
            await self.session.close()
        self.clear_cache()