// Real Estate Property Service
import { apiClient } from '../client';
import { API_CONFIG } from '../config';

// Types
export interface Property {
  id: string;
  mlsId?: string;
  address: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
    coordinates?: {
      lat: number;
      lng: number;
    };
  };
  details: {
    propertyType: 'single_family' | 'condo' | 'townhouse' | 'multi_family' | 'land' | 'commercial';
    bedrooms?: number;
    bathrooms?: number;
    squareFeet?: number;
    lotSize?: number;
    yearBuilt?: number;
    stories?: number;
    garage?: number;
    pool?: boolean;
    fireplace?: boolean;
  };
  pricing: {
    listPrice: number;
    originalPrice?: number;
    priceHistory: PriceChange[];
    estimatedValue?: number;
    pricePerSqFt?: number;
    monthlyPayment?: number;
    taxes?: number;
    hoa?: number;
  };
  status: 'active' | 'pending' | 'sold' | 'off_market' | 'coming_soon';
  listing: {
    agentId: string;
    agentName: string;
    agentPhone: string;
    agentEmail: string;
    brokerageName: string;
    listingDate: string;
    daysOnMarket: number;
    description: string;
    features: string[];
    photos: string[];
    virtualTour?: string;
  };
  market: {
    neighborhood: string;
    schoolDistrict?: string;
    walkScore?: number;
    comps?: Property[];
    marketTrends?: MarketTrend;
  };
  createdAt: string;
  updatedAt: string;
}

export interface PriceChange {
  date: string;
  oldPrice: number;
  newPrice: number;
  changeType: 'increase' | 'decrease' | 'initial';
}

export interface MarketTrend {
  medianPrice: number;
  averageDays: number;
  priceChange: number;
  inventoryLevel: number;
  absorption: number;
}

export interface PropertySearchParams {
  location?: string;
  minPrice?: number;
  maxPrice?: number;
  propertyType?: string[];
  minBedrooms?: number;
  maxBedrooms?: number;
  minBathrooms?: number;
  maxBathrooms?: number;
  minSquareFeet?: number;
  maxSquareFeet?: number;
  minYearBuilt?: number;
  maxYearBuilt?: number;
  features?: string[];
  status?: string[];
  sortBy?: 'price' | 'date' | 'size' | 'relevance';
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export interface PropertyAnalytics {
  totalProperties: number;
  averagePrice: number;
  medianPrice: number;
  priceRange: {
    min: number;
    max: number;
  };
  propertyTypes: Array<{
    type: string;
    count: number;
    percentage: number;
  }>;
  statusDistribution: Array<{
    status: string;
    count: number;
    percentage: number;
  }>;
  marketTrends: {
    priceChanges: Array<{
      date: string;
      averagePrice: number;
      median: number;
    }>;
    inventory: Array<{
      date: string;
      count: number;
    }>;
  };
}

// Property Service Class
class PropertyService {
  // Search properties
  async searchProperties(params: PropertySearchParams): Promise<{
    properties: Property[];
    total: number;
    pagination: {
      page: number;
      limit: number;
      totalPages: number;
    };
  }> {
    return apiClient.get<{
      properties: Property[];
      total: number;
      pagination: {
        page: number;
        limit: number;
        totalPages: number;
      };
    }>(API_CONFIG.ENDPOINTS.PROPERTIES.SEARCH, params);
  }

  // Get all properties
  async getProperties(params?: {
    limit?: number;
    offset?: number;
    status?: string;
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
  }): Promise<{
    properties: Property[];
    total: number;
  }> {
    return apiClient.get<{
      properties: Property[];
      total: number;
    }>(API_CONFIG.ENDPOINTS.PROPERTIES.LIST, params);
  }

  // Get property by ID
  async getProperty(id: string): Promise<Property> {
    return apiClient.get<Property>(
      API_CONFIG.ENDPOINTS.PROPERTIES.DETAILS,
      undefined,
      { id }
    );
  }

  // Create property
  async createProperty(data: Partial<Property>): Promise<Property> {
    return apiClient.post<Property>(API_CONFIG.ENDPOINTS.PROPERTIES.LIST, data);
  }

  // Update property
  async updateProperty(id: string, data: Partial<Property>): Promise<Property> {
    return apiClient.put<Property>(
      API_CONFIG.ENDPOINTS.PROPERTIES.DETAILS,
      data,
      { id }
    );
  }

  // Delete property
  async deleteProperty(id: string): Promise<void> {
    return apiClient.delete(
      API_CONFIG.ENDPOINTS.PROPERTIES.DETAILS,
      { id }
    );
  }

  // Sync with MLS
  async syncWithMLS(params?: {
    region?: string;
    lastSync?: string;
    forceSync?: boolean;
  }): Promise<{
    status: string;
    jobId: string;
    estimated: number;
  }> {
    return apiClient.post<{
      status: string;
      jobId: string;
      estimated: number;
    }>(API_CONFIG.ENDPOINTS.PROPERTIES.MLS_SYNC, params);
  }

  // Get MLS sync status
  async getMlsSyncStatus(jobId: string): Promise<{
    status: 'pending' | 'running' | 'completed' | 'failed';
    progress: number;
    processed: number;
    total: number;
    errors: string[];
  }> {
    return apiClient.get<{
      status: 'pending' | 'running' | 'completed' | 'failed';
      progress: number;
      processed: number;
      total: number;
      errors: string[];
    }>(API_CONFIG.ENDPOINTS.PROPERTIES.MLS_SYNC, { jobId });
  }

  // Get comparable properties
  async getComparables(propertyId: string, params?: {
    radius?: number;
    maxResults?: number;
    timeframe?: number;
  }): Promise<Property[]> {
    return apiClient.get<Property[]>(
      API_CONFIG.ENDPOINTS.PROPERTIES.DETAILS,
      { ...params, action: 'comparables' },
      { id: propertyId }
    );
  }

  // Get property analytics
  async getPropertyAnalytics(params?: {
    location?: string;
    propertyType?: string;
    startDate?: string;
    endDate?: string;
  }): Promise<PropertyAnalytics> {
    return apiClient.get<PropertyAnalytics>(
      API_CONFIG.ENDPOINTS.PROPERTIES.ANALYTICS,
      params
    );
  }

  // Get property valuation
  async getValuation(propertyId: string): Promise<{
    estimatedValue: number;
    confidence: number;
    factors: Array<{
      factor: string;
      impact: number;
      description: string;
    }>;
    comparables: Property[];
    marketTrends: MarketTrend;
  }> {
    return apiClient.get<{
      estimatedValue: number;
      confidence: number;
      factors: Array<{
        factor: string;
        impact: number;
        description: string;
      }>;
      comparables: Property[];
      marketTrends: MarketTrend;
    }>(
      API_CONFIG.ENDPOINTS.PROPERTIES.DETAILS,
      { action: 'valuation' },
      { id: propertyId }
    );
  }

  // Get neighborhood insights
  async getNeighborhoodInsights(location: string): Promise<{
    demographics: {
      population: number;
      medianAge: number;
      medianIncome: number;
      education: { [level: string]: number };
    };
    amenities: {
      schools: Array<{ name: string; rating: number; distance: number }>;
      restaurants: Array<{ name: string; rating: number; cuisine: string }>;
      shopping: Array<{ name: string; type: string; distance: number }>;
      transportation: Array<{ type: string; name: string; distance: number }>;
    };
    safety: {
      crimeRate: number;
      safetyScore: number;
      trends: Array<{ year: number; incidents: number }>;
    };
    market: {
      medianPrice: number;
      pricePerSqFt: number;
      daysOnMarket: number;
      appreciation: number;
    };
  }> {
    return apiClient.get<{
      demographics: {
        population: number;
        medianAge: number;
        medianIncome: number;
        education: { [level: string]: number };
      };
      amenities: {
        schools: Array<{ name: string; rating: number; distance: number }>;
        restaurants: Array<{ name: string; rating: number; cuisine: string }>;
        shopping: Array<{ name: string; type: string; distance: number }>;
        transportation: Array<{ type: string; name: string; distance: number }>;
      };
      safety: {
        crimeRate: number;
        safetyScore: number;
        trends: Array<{ year: number; incidents: number }>;
      };
      market: {
        medianPrice: number;
        pricePerSqFt: number;
        daysOnMarket: number;
        appreciation: number;
      };
    }>(API_CONFIG.ENDPOINTS.PROPERTIES.DETAILS, { location, action: 'neighborhood' });
  }

  // Save property to favorites
  async saveToFavorites(propertyId: string): Promise<void> {
    return apiClient.post(
      API_CONFIG.ENDPOINTS.PROPERTIES.DETAILS,
      { action: 'favorite' },
      { id: propertyId }
    );
  }

  // Remove property from favorites
  async removeFromFavorites(propertyId: string): Promise<void> {
    return apiClient.delete(
      API_CONFIG.ENDPOINTS.PROPERTIES.DETAILS,
      { id: propertyId, action: 'favorite' }
    );
  }

  // Get saved properties
  async getSavedProperties(): Promise<Property[]> {
    return apiClient.get<Property[]>(
      API_CONFIG.ENDPOINTS.PROPERTIES.LIST,
      { saved: true }
    );
  }
}

// Create singleton instance
export const propertyService = new PropertyService();

export default propertyService;