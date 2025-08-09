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
    const response = await apiClient.get<MarketTrend[]>(
      API_CONFIG.ENDPOINTS.MARKET.TRENDS,
      params
    );
    return response.data;
  }

  // Get market trend for specific location
  async getLocationTrend(location: string, period?: string): Promise<MarketTrend> {
    const response = await apiClient.get<MarketTrend>(
      API_CONFIG.ENDPOINTS.MARKET.TRENDS,
      { location, period }
    );
    return response.data;
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
    const response = await apiClient.get<{
      insights: MarketInsight[];
      total: number;
    }>(API_CONFIG.ENDPOINTS.MARKET.INSIGHTS, params);
    return response.data;
  }

  // Get market insight by ID
  async getMarketInsight(id: string): Promise<MarketInsight> {
    const response = await apiClient.get<MarketInsight>(
      API_CONFIG.ENDPOINTS.MARKET.INSIGHTS,
      undefined,
      { id }
    );
    return response.data;
  }

  // Create custom market insight
  async createMarketInsight(data: Partial<MarketInsight>): Promise<MarketInsight> {
    const response = await apiClient.post<MarketInsight>(
      API_CONFIG.ENDPOINTS.MARKET.INSIGHTS,
      data
    );
    return response.data;
  }

  // Get market forecasts
  async getMarketForecasts(params?: {
    location?: string;
    timeframe?: string[];
    includeScenarios?: boolean;
  }): Promise<MarketForecast[]> {
    const response = await apiClient.get<MarketForecast[]>(
      API_CONFIG.ENDPOINTS.MARKET.FORECASTS,
      params
    );
    return response.data;
  }

  // Get forecast for specific location
  async getLocationForecast(location: string, timeframe?: string): Promise<MarketForecast> {
    const response = await apiClient.get<MarketForecast>(
      API_CONFIG.ENDPOINTS.MARKET.FORECASTS,
      { location, timeframe }
    );
    return response.data;
  }

  // Generate custom forecast
  async generateForecast(data: {
    location: string;
    timeframe: string;
    factors?: Record<string, number>;
    scenarios?: string[];
  }): Promise<MarketForecast> {
    const response = await apiClient.post<MarketForecast>(
      API_CONFIG.ENDPOINTS.MARKET.FORECASTS,
      data
    );
    return response.data;
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
    const response = await apiClient.get<{
      competitors: CompetitorAnalysis[];
      total: number;
    }>(API_CONFIG.ENDPOINTS.MARKET.COMPETITORS, params);
    return response.data;
  }

  // Get specific competitor
  async getCompetitor(id: string): Promise<CompetitorAnalysis> {
    const response = await apiClient.get<CompetitorAnalysis>(
      API_CONFIG.ENDPOINTS.MARKET.COMPETITORS,
      undefined,
      { id }
    );
    return response.data;
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
    const response = await apiClient.post<{
      myPerformance: Record<string, number>;
      competitors: Array<{
        name: string;
        performance: Record<string, number>;
        ranking: number;
      }>;
      marketAverage: Record<string, number>;
      insights: string[];
    }>(API_CONFIG.ENDPOINTS.MARKET.COMPETITORS, params);
    return response.data;
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
    const response = await apiClient.get<{
      opportunities: MarketOpportunity[];
      total: number;
    }>(API_CONFIG.ENDPOINTS.MARKET.INSIGHTS, {
      ...params,
      opportunitiesOnly: true
    });
    return response.data;
  }

  // Track market opportunity
  async trackOpportunity(id: string): Promise<void> {
    await apiClient.post(
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
    const response = await apiClient.get<{
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
    return response.data;
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
    const response = await apiClient.get<{
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
    return response.data;
  }

  // Subscribe to market alerts
  async subscribeToAlerts(params: {
    location: string;
    alertTypes: string[];
    thresholds?: Record<string, number>;
    frequency?: 'immediate' | 'daily' | 'weekly';
  }): Promise<{ subscriptionId: string }> {
    const response = await apiClient.post<{ subscriptionId: string }>(
      API_CONFIG.ENDPOINTS.MARKET.INSIGHTS,
      { ...params, action: 'subscribe' }
    );
    return response.data;
  }

  // Unsubscribe from market alerts
  async unsubscribeFromAlerts(subscriptionId: string): Promise<void> {
    await apiClient.delete(
      API_CONFIG.ENDPOINTS.MARKET.INSIGHTS,
      { subscriptionId }
    );
  }
}

// Create singleton instance
export const marketService = new MarketService();

export default marketService;