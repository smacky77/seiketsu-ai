/**
 * Comprehensive Analytics Service
 * Client-side service for Seiketsu AI analytics dashboard
 */

import { apiClient } from '../api/client'

// Types
export interface ClientAcquisitionMetrics {
  leadGeneration: number
  demoConversion: number
  pilotEnrollment: number
  trialToPaid: number
  pipelineValue: number
  acquisitionCost: number
}

export interface ClientSuccessMetrics {
  satisfactionScore: number
  uptime: number
  responseTime: number
  ticketResolution: number
  retention: number
  churn: number
}

export interface BusinessMetrics {
  mrr: number
  revenuePerClient: number
  ltv: number
  profitability: number
  growth: number
}

export interface TechnicalMetrics {
  apiResponseTime: number
  errorRate: number
  voiceQuality: number
  systemAvailability: number
  integrationSuccess: number
}

export interface RealTimeMetrics {
  activeUsers: number
  currentCalls: number
  todayLeads: number
  systemLoad: number
  alerts: Alert[]
}

export interface Alert {
  id: string
  type: 'warning' | 'error' | 'success' | 'info'
  message: string
  timestamp: Date
  resolved: boolean
}

export interface DashboardData {
  clientAcquisition: ClientAcquisitionMetrics
  clientSuccess: ClientSuccessMetrics
  businessPerformance: BusinessMetrics
  technicalPerformance: TechnicalMetrics
  realTimeData: RealTimeMetrics
  predictiveInsights?: PredictiveInsights
}

export interface PredictiveInsights {
  revenueForecast: Record<string, number>
  churnPrediction: Record<string, number>
  leadScoringAccuracy: number
  optimalPricing: Record<string, any>
  capacityPlanning: Record<string, any>
  riskAssessment: Array<Record<string, any>>
}

export interface ReportRequest {
  reportType: 'daily' | 'weekly' | 'monthly' | 'quarterly'
  includePredictions: boolean
  includeRecommendations: boolean
  format: 'json' | 'pdf' | 'excel'
  emailRecipients?: string[]
}

export interface ReportStatus {
  reportId: string
  status: 'generating' | 'completed' | 'failed'
  progress: number
  downloadUrl?: string
}

export interface ForecastRequest {
  horizon: '30d' | '90d' | '6m' | '1y'
  modelType: 'revenue' | 'growth' | 'churn' | 'satisfaction'
  confidenceLevel: number
}

export interface ForecastResponse {
  modelType: string
  forecast: Record<string, number>
  currentValue: number
  predictionAccuracy: number
  confidenceIntervals: {
    lowerBound: Record<string, number>
    upperBound: Record<string, number>
  }
}

export class AnalyticsService {
  private readonly baseUrl = '/api/v1/comprehensive-analytics'

  /**
   * Get comprehensive dashboard data
   */
  async getDashboardData(
    timeRange: string = '30d',
    includePredictions: boolean = false,
    includeRealTime: boolean = true
  ): Promise<DashboardData> {
    try {
      const params = new URLSearchParams({
        time_range: timeRange,
        include_predictions: includePredictions.toString(),
        include_real_time: includeRealTime.toString()
      })

      const response = await apiClient.get(`${this.baseUrl}/dashboard/comprehensive?${params}`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch dashboard data: ${response.statusText}`)
      }

      const data = await response.json()
      
      // Transform API response to match frontend interface
      return {
        clientAcquisition: {
          leadGeneration: data.client_acquisition.lead_generation_rate,
          demoConversion: data.client_acquisition.demo_conversion_rate,
          pilotEnrollment: data.client_acquisition.pilot_enrollment_rate,
          trialToPaid: data.client_acquisition.trial_to_paid_rate,
          pipelineValue: data.client_acquisition.pipeline_value,
          acquisitionCost: data.client_acquisition.customer_acquisition_cost
        },
        clientSuccess: {
          satisfactionScore: data.client_success.satisfaction_score,
          uptime: data.client_success.system_uptime,
          responseTime: data.client_success.avg_response_time,
          ticketResolution: data.client_success.ticket_resolution_time,
          retention: data.client_success.retention_rate,
          churn: data.client_success.churn_rate
        },
        businessPerformance: {
          mrr: data.business_performance.monthly_recurring_revenue,
          revenuePerClient: data.business_performance.revenue_per_client,
          ltv: data.business_performance.lifetime_value,
          profitability: data.business_performance.profit_margin,
          growth: data.business_performance.growth_rate
        },
        technicalPerformance: {
          apiResponseTime: data.technical_performance.api_response_time,
          errorRate: data.technical_performance.error_rate,
          voiceQuality: data.technical_performance.voice_quality_score,
          systemAvailability: data.technical_performance.system_availability,
          integrationSuccess: data.technical_performance.integration_success_rate
        },
        realTimeData: data.real_time_data ? {
          activeUsers: data.real_time_data.active_metrics.users,
          currentCalls: data.real_time_data.active_metrics.conversations,
          todayLeads: data.real_time_data.today_metrics.leads,
          systemLoad: data.real_time_data.active_metrics.system_load,
          alerts: data.real_time_data.alerts.map((alert: any) => ({
            id: alert.id,
            type: alert.type,
            message: alert.message,
            timestamp: new Date(alert.timestamp),
            resolved: alert.resolved
          }))
        } : {
          activeUsers: 0,
          currentCalls: 0,
          todayLeads: 0,
          systemLoad: 0,
          alerts: []
        },
        predictiveInsights: data.predictive_insights ? {
          revenueForecast: data.predictive_insights.revenue_forecast,
          churnPrediction: data.predictive_insights.churn_prediction,
          leadScoringAccuracy: data.predictive_insights.lead_scoring_accuracy,
          optimalPricing: data.predictive_insights.optimal_pricing,
          capacityPlanning: data.predictive_insights.capacity_planning,
          riskAssessment: data.predictive_insights.risk_assessment
        } : undefined
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      throw error
    }
  }

  /**
   * Get detailed client acquisition metrics
   */
  async getClientAcquisitionDetails(
    days: number = 30,
    includeFunnel: boolean = true,
    includeTrends: boolean = true
  ): Promise<any> {
    try {
      const params = new URLSearchParams({
        days: days.toString(),
        include_funnel: includeFunnel.toString(),
        include_trends: includeTrends.toString()
      })

      const response = await apiClient.get(`${this.baseUrl}/client-acquisition/detailed?${params}`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch acquisition details: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Failed to fetch client acquisition details:', error)
      throw error
    }
  }

  /**
   * Get client satisfaction tracking
   */
  async getSatisfactionTracking(
    days: number = 30,
    includeNPS: boolean = true,
    includeFeedback: boolean = false
  ): Promise<any> {
    try {
      const params = new URLSearchParams({
        days: days.toString(),
        include_nps: includeNPS.toString(),
        include_feedback: includeFeedback.toString()
      })

      const response = await apiClient.get(`${this.baseUrl}/client-success/satisfaction-tracking?${params}`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch satisfaction tracking: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Failed to fetch satisfaction tracking:', error)
      throw error
    }
  }

  /**
   * Get real-time live dashboard
   */
  async getLiveDashboard(refreshRate: number = 30): Promise<any> {
    try {
      const params = new URLSearchParams({
        refresh_rate: refreshRate.toString()
      })

      const response = await apiClient.get(`${this.baseUrl}/real-time/live-dashboard?${params}`)
      
      if (!response.ok) {
        throw new Error(`Failed to fetch live dashboard: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Failed to fetch live dashboard:', error)
      throw error
    }
  }

  /**
   * Generate executive report
   */
  async generateExecutiveReport(request: ReportRequest): Promise<{ reportId: string; statusUrl: string }> {
    try {
      const response = await apiClient.post(`${this.baseUrl}/reports/executive/generate`, request)
      
      if (!response.ok) {
        throw new Error(`Failed to generate report: ${response.statusText}`)
      }

      const data = await response.json()
      return {
        reportId: data.report_id,
        statusUrl: data.status_url
      }
    } catch (error) {
      console.error('Failed to generate executive report:', error)
      throw error
    }
  }

  /**
   * Get report generation status
   */
  async getReportStatus(reportId: string): Promise<ReportStatus> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/reports/${reportId}/status`)
      
      if (!response.ok) {
        throw new Error(`Failed to get report status: ${response.statusText}`)
      }

      const data = await response.json()
      return {
        reportId: data.report_id,
        status: data.status,
        progress: data.progress_percentage,
        downloadUrl: data.download_url
      }
    } catch (error) {
      console.error('Failed to get report status:', error)
      throw error
    }
  }

  /**
   * Get predictive forecasts
   */
  async getPredictiveForecast(request: ForecastRequest): Promise<ForecastResponse> {
    try {
      const params = new URLSearchParams({
        horizon: request.horizon,
        model_type: request.modelType,
        confidence_level: request.confidenceLevel.toString()
      })

      const response = await apiClient.get(`${this.baseUrl}/predictions/forecast?${params}`)
      
      if (!response.ok) {
        throw new Error(`Failed to get predictive forecast: ${response.statusText}`)
      }

      const data = await response.json()
      return {
        modelType: data.model_type,
        forecast: data.forecast,
        currentValue: data.current_value,
        predictionAccuracy: data.prediction_accuracy,
        confidenceIntervals: data.confidence_intervals
      }
    } catch (error) {
      console.error('Failed to get predictive forecast:', error)
      throw error
    }
  }

  /**
   * Configure analytics alert
   */
  async configureAlert(alertConfig: {
    metricName: string
    thresholdValue: number
    comparisonType: 'above' | 'below' | 'equals'
    notificationChannels: string[]
    isActive: boolean
  }): Promise<{ alertId: string }> {
    try {
      const response = await apiClient.post(`${this.baseUrl}/alerts/configure`, alertConfig)
      
      if (!response.ok) {
        throw new Error(`Failed to configure alert: ${response.statusText}`)
      }

      const data = await response.json()
      return { alertId: data.alert_id }
    } catch (error) {
      console.error('Failed to configure alert:', error)
      throw error
    }
  }

  /**
   * Export dashboard data
   */
  async exportDashboard(format: 'json' | 'csv' | 'pdf', timeRange: string = '30d'): Promise<Blob> {
    try {
      const params = new URLSearchParams({
        format,
        time_range: timeRange
      })

      const response = await apiClient.get(`${this.baseUrl}/export/dashboard?${params}`)
      
      if (!response.ok) {
        throw new Error(`Failed to export dashboard: ${response.statusText}`)
      }

      return await response.blob()
    } catch (error) {
      console.error('Failed to export dashboard:', error)
      throw error
    }
  }

  /**
   * Get historical trends
   */
  async getHistoricalTrends(
    metric: string,
    days: number = 90,
    granularity: 'daily' | 'weekly' | 'monthly' = 'daily'
  ): Promise<Array<{ date: string; value: number }>> {
    try {
      const params = new URLSearchParams({
        metric,
        days: days.toString(),
        granularity
      })

      const response = await apiClient.get(`${this.baseUrl}/trends/historical?${params}`)
      
      if (!response.ok) {
        throw new Error(`Failed to get historical trends: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Failed to get historical trends:', error)
      throw error
    }
  }

  /**
   * Get competitive benchmarks
   */
  async getCompetitiveBenchmarks(): Promise<Record<string, any>> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/benchmarks/competitive`)
      
      if (!response.ok) {
        throw new Error(`Failed to get competitive benchmarks: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Failed to get competitive benchmarks:', error)
      throw error
    }
  }

  /**
   * Set up real-time data subscription
   */
  setupRealTimeSubscription(
    callback: (data: RealTimeMetrics) => void,
    refreshInterval: number = 30000
  ): () => void {
    const interval = setInterval(async () => {
      try {
        const data = await this.getLiveDashboard(refreshInterval / 1000)
        if (data.real_time_data) {
          callback({
            activeUsers: data.active_metrics.users,
            currentCalls: data.active_metrics.conversations,
            todayLeads: data.today_metrics.leads,
            systemLoad: data.active_metrics.system_load,
            alerts: data.alerts.map((alert: any) => ({
              id: alert.id,
              type: alert.type,
              message: alert.message,
              timestamp: new Date(alert.timestamp),
              resolved: alert.resolved
            }))
          })
        }
      } catch (error) {
        console.error('Real-time data subscription error:', error)
      }
    }, refreshInterval)

    // Return cleanup function
    return () => clearInterval(interval)
  }
}

// Export singleton instance
export const analyticsService = new AnalyticsService()
export default analyticsService