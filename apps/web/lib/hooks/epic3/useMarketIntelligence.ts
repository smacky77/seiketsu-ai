'use client'

import { useState, useEffect, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Epic3Service } from '@/lib/api/services/epic3.service'
import { 
  MarketAnalysisRequest,
  PropertyValuePrediction,
  MarketTrend,
  CompetitiveAnalysis 
} from '@/lib/api/services/epic3.service'

// Market Intelligence Hook
export function useMarketIntelligence() {
  const [location, setLocation] = useState<string>('')
  const [timeframe, setTimeframe] = useState<'30d' | '90d' | '1y'>('90d')
  const queryClient = useQueryClient()

  const {
    data: marketAnalysis,
    isLoading: isLoadingAnalysis,
    error: analysisError,
    refetch: refetchAnalysis
  } = useQuery({
    queryKey: ['market-analysis', location, timeframe],
    queryFn: () => Epic3Service.market.getMarketAnalysis({
      location,
      timeframe
    }),
    enabled: !!location,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000 // 30 minutes
  })

  const {
    data: marketTrends,
    isLoading: isLoadingTrends,
    error: trendsError
  } = useQuery({
    queryKey: ['market-trends', location, timeframe],
    queryFn: () => Epic3Service.market.getMarketTrends(location, timeframe),
    enabled: !!location,
    staleTime: 10 * 60 * 1000,
    gcTime: 60 * 60 * 1000
  })

  const {
    data: competitiveAnalysis,
    isLoading: isLoadingCompetitive,
    error: competitiveError
  } = useQuery({
    queryKey: ['competitive-analysis', location],
    queryFn: () => Epic3Service.market.getCompetitiveAnalysis(location),
    enabled: !!location,
    staleTime: 15 * 60 * 1000,
    gcTime: 60 * 60 * 1000
  })

  const generateReportMutation = useMutation({
    mutationFn: (request: MarketAnalysisRequest) => 
      Epic3Service.market.generateMarketReport(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['market-analysis'] })
    }
  })

  const getPropertyPredictionsMutation = useMutation({
    mutationFn: (propertyIds: string[]) => 
      Epic3Service.market.getPropertyPredictions(propertyIds)
  })

  const generateReport = useCallback((request?: Partial<MarketAnalysisRequest>) => {
    const fullRequest = {
      location,
      timeframe,
      ...request
    }
    return generateReportMutation.mutate(fullRequest)
  }, [location, timeframe, generateReportMutation])

  const getPropertyPredictions = useCallback((propertyIds: string[]) => {
    return getPropertyPredictionsMutation.mutateAsync(propertyIds)
  }, [getPropertyPredictionsMutation])

  const refreshData = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['market-analysis'] })
    queryClient.invalidateQueries({ queryKey: ['market-trends'] })
    queryClient.invalidateQueries({ queryKey: ['competitive-analysis'] })
  }, [queryClient])

  return {
    // State
    location,
    setLocation,
    timeframe,
    setTimeframe,

    // Data
    marketAnalysis,
    marketTrends,
    competitiveAnalysis,

    // Loading states
    isLoadingAnalysis,
    isLoadingTrends,
    isLoadingCompetitive,
    isGeneratingReport: generateReportMutation.isPending,
    isGettingPredictions: getPropertyPredictionsMutation.isPending,

    // Errors
    analysisError,
    trendsError,
    competitiveError,
    reportError: generateReportMutation.error,
    predictionsError: getPropertyPredictionsMutation.error,

    // Actions
    generateReport,
    getPropertyPredictions,
    refreshData,
    refetchAnalysis,

    // Computed values
    hasData: !!(marketAnalysis || marketTrends || competitiveAnalysis),
    isLoading: isLoadingAnalysis || isLoadingTrends || isLoadingCompetitive,
    hasErrors: !!(analysisError || trendsError || competitiveError)
  }
}

// Property Predictions Hook
export function usePropertyPredictions(propertyIds?: string[]) {
  const {
    data: predictions,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['property-predictions', propertyIds],
    queryFn: () => Epic3Service.market.getPropertyPredictions(propertyIds!),
    enabled: !!(propertyIds && propertyIds.length > 0),
    staleTime: 15 * 60 * 1000,
    gcTime: 60 * 60 * 1000
  })

  const getAccuracyMetrics = useCallback(() => {
    if (!predictions) return null

    const totalPredictions = predictions.length
    const highConfidence = predictions.filter(p => p.confidence >= 80).length
    const mediumConfidence = predictions.filter(p => p.confidence >= 60 && p.confidence < 80).length
    const lowConfidence = predictions.filter(p => p.confidence < 60).length

    return {
      total: totalPredictions,
      highConfidence,
      mediumConfidence,
      lowConfidence,
      averageConfidence: predictions.reduce((sum, p) => sum + p.confidence, 0) / totalPredictions
    }
  }, [predictions])

  const getPredictionsByConfidence = useCallback((minConfidence: number = 0) => {
    return predictions?.filter(p => p.confidence >= minConfidence) || []
  }, [predictions])

  return {
    predictions,
    isLoading,
    error,
    refetch,
    getAccuracyMetrics,
    getPredictionsByConfidence,
    hasData: !!(predictions && predictions.length > 0)
  }
}

// Market Insights Hook
export function useMarketInsights(location: string) {
  const [insights, setInsights] = useState<any[]>([])
  const [isProcessing, setIsProcessing] = useState(false)

  const { marketAnalysis, marketTrends, competitiveAnalysis } = useMarketIntelligence()

  const generateInsights = useCallback(async () => {
    if (!marketAnalysis || !marketTrends || !competitiveAnalysis) return

    setIsProcessing(true)
    try {
      // Simulate AI-generated insights based on market data
      const newInsights = []

      // Price trend insights
      const latestTrend = marketTrends[marketTrends.length - 1]
      if (latestTrend.priceChange > 10) {
        newInsights.push({
          type: 'opportunity',
          title: 'Strong Market Growth',
          description: `Property values increased by ${latestTrend.priceChange.toFixed(1)}% this period. Consider focusing on seller leads.`,
          impact: 'high',
          confidence: 85
        })
      }

      // Inventory insights
      const avgDaysOnMarket = marketTrends.reduce((sum, t) => sum + t.daysOnMarket, 0) / marketTrends.length
      if (avgDaysOnMarket < 30) {
        newInsights.push({
          type: 'trend',
          title: 'Fast-Moving Market',
          description: `Properties sell in ${avgDaysOnMarket.toFixed(0)} days on average. Quick response times are crucial.`,
          impact: 'medium',
          confidence: 90
        })
      }

      // Competitive insights
      const topCompetitor = competitiveAnalysis.reduce((prev, current) => 
        prev.marketShare > current.marketShare ? prev : current
      )
      if (topCompetitor.marketShare > 25) {
        newInsights.push({
          type: 'risk',
          title: 'Market Concentration Risk',
          description: `${topCompetitor.competitor} dominates with ${topCompetitor.marketShare}% market share. Focus on differentiation.`,
          impact: 'medium',
          confidence: 75
        })
      }

      setInsights(newInsights)
    } catch (error) {
      console.error('Error generating insights:', error)
    } finally {
      setIsProcessing(false)
    }
  }, [marketAnalysis, marketTrends, competitiveAnalysis])

  useEffect(() => {
    if (marketAnalysis && marketTrends && competitiveAnalysis) {
      generateInsights()
    }
  }, [generateInsights, marketAnalysis, marketTrends, competitiveAnalysis])

  return {
    insights,
    isProcessing,
    regenerateInsights: generateInsights,
    hasInsights: insights.length > 0
  }
}

// Market Alerts Hook
export function useMarketAlerts(location: string) {
  const [alerts, setAlerts] = useState<any[]>([])
  const [alertThresholds, setAlertThresholds] = useState({
    priceChange: 15, // Percentage
    daysOnMarket: 45, // Days
    inventoryChange: 20 // Percentage
  })

  const { marketTrends } = useMarketIntelligence()

  const checkAlerts = useCallback(() => {
    if (!marketTrends || marketTrends.length < 2) return

    const newAlerts: any[] = []
    const latest = marketTrends[marketTrends.length - 1]
    const previous = marketTrends[marketTrends.length - 2]

    // Price change alerts
    if (Math.abs(latest.priceChange) > alertThresholds.priceChange) {
      newAlerts.push({
        id: `price-change-${Date.now()}`,
        type: latest.priceChange > 0 ? 'opportunity' : 'warning',
        title: 'Significant Price Movement',
        message: `Average prices ${latest.priceChange > 0 ? 'increased' : 'decreased'} by ${Math.abs(latest.priceChange).toFixed(1)}%`,
        timestamp: new Date(),
        data: { priceChange: latest.priceChange }
      })
    }

    // Days on market alerts
    if (latest.daysOnMarket > alertThresholds.daysOnMarket) {
      newAlerts.push({
        id: `dom-${Date.now()}`,
        type: 'warning',
        title: 'Market Slowing Down',
        message: `Properties taking ${latest.daysOnMarket} days to sell on average`,
        timestamp: new Date(),
        data: { daysOnMarket: latest.daysOnMarket }
      })
    }

    // Inventory change alerts
    const inventoryChange = ((latest.volumeSold - previous.volumeSold) / previous.volumeSold) * 100
    if (Math.abs(inventoryChange) > alertThresholds.inventoryChange) {
      newAlerts.push({
        id: `inventory-${Date.now()}`,
        type: inventoryChange > 0 ? 'info' : 'warning',
        title: 'Inventory Level Change',
        message: `Sales volume ${inventoryChange > 0 ? 'increased' : 'decreased'} by ${Math.abs(inventoryChange).toFixed(1)}%`,
        timestamp: new Date(),
        data: { inventoryChange }
      })
    }

    setAlerts(prev => [...prev, ...newAlerts])
  }, [marketTrends, alertThresholds])

  useEffect(() => {
    if (marketTrends) {
      checkAlerts()
    }
  }, [checkAlerts, marketTrends])

  const dismissAlert = useCallback((alertId: string) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId))
  }, [])

  const updateThresholds = useCallback((newThresholds: Partial<typeof alertThresholds>) => {
    setAlertThresholds(prev => ({ ...prev, ...newThresholds }))
  }, [])

  return {
    alerts,
    alertThresholds,
    dismissAlert,
    updateThresholds,
    hasAlerts: alerts.length > 0
  }
}