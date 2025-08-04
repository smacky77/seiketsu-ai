// Market Intelligence Service
import { apiClient } from '../client';
import { API_CONFIG } from '../config';

// Types
export interface MarketTrend {
  location: string;
  period: string;
  metrics: {
    medianPrice: number;
    averagePrice: number;
    priceChange: number;
    priceChangePercent: number;
    daysOnMarket: number;
    inventory: number;
    absorption: number;
    monthsOfSupply: number;
    listToSaleRatio: number;
  };
  propertyTypes: Array<{
    type: string;
    medianPrice: number;
    count: number;
    change: number;
  }>;
  priceRanges: Array<{
    range: string;
    count: number;
    percentage: number;
    change: number;
  }>;
  updatedAt: string;
}

export interface MarketInsight {
  id: string;
  title: string;
  summary: string;
  content: string;
  type: 'trend' | 'opportunity' | 'risk' | 'forecast';
  priority: 'low' | 'medium' | 'high' | 'critical';
  locations: string[];
  metrics: Record<string, number>;
  sources: string[];
  confidence: number;
  createdAt: string;
  expiresAt?: string;
}

export interface MarketForecast {
  location: string;
  timeframe: '3_months' | '6_months' | '1_year' | '2_years' | '5_years';
  predictions: {
    price: {
      change: number;
      changePercent: number;
      confidence: number;
      range: {
        low: number;
        high: number;
      };
    };
    inventory: {
      change: number;
      changePercent: number;
      confidence: number;
    };
    demand: {
      level: 'low' | 'moderate' | 'high' | 'very_high';
      change: number;
      confidence: number;
    };
  };
  factors: Array<{
    factor: string;
    impact: number;
    description: string;
  }>;
  scenarios: Array<{
    name: string;
    probability: number;
    outcome: string;
    priceImpact: number;
  }>;
  updatedAt: string;
}

export interface CompetitorAnalysis {
  id: string;
  name: string;
  type: 'brokerage' | 'agent' | 'team';
  marketShare: number;
  performance: {
    listings: number;
    sales: number;
    averageDays: number;
    averagePrice: number;
    listToSaleRatio: number;
  };
  strengths: string[];
  weaknesses: string[];
  strategies: string[];
  locations: string[];
  updatedAt: string;
}

export interface MarketOpportunity {
  id: string;
  title: string;
  description: string;
  type: 'undervalued' | 'emerging' | 'high_demand' | 'low_competition';
  location: string;
  potential: {
    score: number;
    priceAppreciation: number;
    demandGrowth: number;
    competitionLevel: number;
  };
  timeline: string;
  requiredActions: string[];
  risks: string[];
  confidence: number;
  createdAt: string;
}

// Market Service Class
class MarketService {
  // Get market trends
  async getMarketTrends(params?: {
    location?: string;
    propertyType?: string;
    period?: '1_month' | '3_months' | '6_months' | '1_year';
    includeComparison?: boolean;
  }): Promise<MarketTrend[]> {
    return apiClient.get<MarketTrend[]>(
      API_CONFIG.ENDPOINTS.MARKET.TRENDS,
      params
    );
  }

  // Get market trend for specific location
  async getLocationTrend(location: string, period?: string): Promise<MarketTrend> {
    return apiClient.get<MarketTrend>(
      API_CONFIG.ENDPOINTS.MARKET.TRENDS,
      { location, period }
    );
  }

  // Get market insights
  async getMarketInsights(params?: {
    location?: string;
    type?: string[];
    priority?: string[];
    limit?: number;
    includeExpired?: boolean;
  }): Promise<{
    insights: MarketInsight[];
    total: number;
  }> {
    return apiClient.get<{
      insights: MarketInsight[];
      total: number;
    }>(API_CONFIG.ENDPOINTS.MARKET.INSIGHTS, params);
  }

  // Get market insight by ID
  async getMarketInsight(id: string): Promise<MarketInsight> {
    return apiClient.get<MarketInsight>(
      API_CONFIG.ENDPOINTS.MARKET.INSIGHTS,
      undefined,
      { id }
    );
  }

  // Create custom market insight
  async createMarketInsight(data: Partial<MarketInsight>): Promise<MarketInsight> {
    return apiClient.post<MarketInsight>(
      API_CONFIG.ENDPOINTS.MARKET.INSIGHTS,
      data
    );
  }

  // Get market forecasts
  async getMarketForecasts(params?: {
    location?: string;
    timeframe?: string[];
    includeScenarios?: boolean;
  }): Promise<MarketForecast[]> {
    return apiClient.get<MarketForecast[]>(
      API_CONFIG.ENDPOINTS.MARKET.FORECASTS,
      params
    );
  }

  // Get forecast for specific location
  async getLocationForecast(location: string, timeframe?: string): Promise<MarketForecast> {
    return apiClient.get<MarketForecast>(
      API_CONFIG.ENDPOINTS.MARKET.FORECASTS,
      { location, timeframe }
    );
  }

  // Generate custom forecast
  async generateForecast(data: {
    location: string;
    timeframe: string;
    factors?: Record<string, number>;
    scenarios?: string[];
  }): Promise<MarketForecast> {
    return apiClient.post<MarketForecast>(
      API_CONFIG.ENDPOINTS.MARKET.FORECASTS,
      data
    );
  }

  // Get competitor analysis
  async getCompetitorAnalysis(params?: {
    location?: string;
    type?: string[];
    includePerformance?: boolean;
    limit?: number;
  }): Promise<{
    competitors: CompetitorAnalysis[];
    total: number;
  }> {
    return apiClient.get<{
      competitors: CompetitorAnalysis[];
      total: number;
    }>(API_CONFIG.ENDPOINTS.MARKET.COMPETITORS, params);
  }

  // Get specific competitor
  async getCompetitor(id: string): Promise<CompetitorAnalysis> {
    return apiClient.get<CompetitorAnalysis>(
      API_CONFIG.ENDPOINTS.MARKET.COMPETITORS,
      undefined,
      { id }
    );
  }

  // Compare with competitors
  async compareWithCompetitors(params: {
    location: string;
    metrics: string[];
    period?: string;
  }): Promise<{
    myPerformance: Record<string, number>;
    competitors: Array<{
      name: string;
      performance: Record<string, number>;
      ranking: number;
    }>;
    marketAverage: Record<string, number>;
    insights: string[];
  }> {
    return apiClient.post<{
      myPerformance: Record<string, number>;
      competitors: Array<{
        name: string;
        performance: Record<string, number>;
        ranking: number;
      }>;
      marketAverage: Record<string, number>;
      insights: string[];
    }>(API_CONFIG.ENDPOINTS.MARKET.COMPETITORS, params);
  }

  // Get market opportunities
  async getMarketOpportunities(params?: {
    location?: string;
    type?: string[];
    minScore?: number;
    sortBy?: 'score' | 'potential' | 'timeline';
    limit?: number;
  }): Promise<{
    opportunities: MarketOpportunity[];
    total: number;
  }> {
    return apiClient.get<{
      opportunities: MarketOpportunity[];
      total: number;
    }>(API_CONFIG.ENDPOINTS.MARKET.INSIGHTS, {
      ...params,
      opportunitiesOnly: true
    });
  }

  // Track market opportunity
  async trackOpportunity(id: string): Promise<void> {
    return apiClient.post(
      API_CONFIG.ENDPOINTS.MARKET.INSIGHTS,
      { action: 'track' },
      { id }
    );
  }

  // Get market summary
  async getMarketSummary(location: string): Promise<{
    overview: {
      medianPrice: number;
      priceChange: number;
      inventory: number;
      daysOnMarket: number;
      trend: 'up' | 'down' | 'stable';
    };
    keyInsights: MarketInsight[];
    topOpportunities: MarketOpportunity[];
    competitorHighlights: {
      topPerformer: string;
      marketLeader: string;
      emergingCompetitor: string;
    };
    forecast: {
      shortTerm: string;
      longTerm: string;
      confidence: number;
    };
  }> {
    return apiClient.get<{
      overview: {
        medianPrice: number;
        priceChange: number;
        inventory: number;
        daysOnMarket: number;
        trend: 'up' | 'down' | 'stable';
      };
      keyInsights: MarketInsight[];
      topOpportunities: MarketOpportunity[];
      competitorHighlights: {
        topPerformer: string;
        marketLeader: string;
        emergingCompetitor: string;
      };
      forecast: {
        shortTerm: string;
        longTerm: string;
        confidence: number;
      };
    }>(API_CONFIG.ENDPOINTS.MARKET.INSIGHTS, { 
      location, 
      summary: true 
    });
  }

  // Get historical market data
  async getHistoricalData(params: {
    location: string;
    metrics: string[];
    startDate: string;
    endDate: string;
    interval?: 'daily' | 'weekly' | 'monthly';
  }): Promise<{
    data: Array<{
      date: string;
      values: Record<string, number>;
    }>;
    summary: Record<string, {
      min: number;
      max: number;
      average: number;
      trend: number;
    }>;
  }> {
    return apiClient.get<{
      data: Array<{
        date: string;
        values: Record<string, number>;
      }>;
      summary: Record<string, {
        min: number;
        max: number;
        average: number;
        trend: number;
      }>;
    }>(API_CONFIG.ENDPOINTS.MARKET.TRENDS, {
      ...params,
      historical: true
    });
  }

  // Subscribe to market alerts
  async subscribeToAlerts(params: {
    location: string;
    alertTypes: string[];
    thresholds?: Record<string, number>;
    frequency?: 'immediate' | 'daily' | 'weekly';
  }): Promise<{ subscriptionId: string }> {
    return apiClient.post<{ subscriptionId: string }>(
      API_CONFIG.ENDPOINTS.MARKET.INSIGHTS,
      { ...params, action: 'subscribe' }
    );
  }

  // Unsubscribe from market alerts
  async unsubscribeFromAlerts(subscriptionId: string): Promise<void> {
    return apiClient.delete(
      API_CONFIG.ENDPOINTS.MARKET.INSIGHTS,
      { subscriptionId }
    );
  }
}

// Create singleton instance
export const marketService = new MarketService();

export default marketService;