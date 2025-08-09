'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  TrendingUp, 
  TrendingDown, 
  Building2, 
  DollarSign, 
  Users, 
  MapPin,
  BarChart3,
  PieChart,
  LineChart,
  Target,
  Zap,
  Award
} from 'lucide-react'

interface MarketMetric {
  label: string
  value: string
  change: number
  trend: 'up' | 'down' | 'stable'
  icon: React.ComponentType<any>
}

interface PropertyPrediction {
  address: string
  currentValue: number
  predictedValue: number
  confidence: number
  timeframe: string
}

export function MarketIntelligenceDashboard() {
  const [selectedTimeframe, setSelectedTimeframe] = useState('30d')
  
  const marketMetrics: MarketMetric[] = [
    {
      label: 'Average Property Value',
      value: '$485,000',
      change: 12.5,
      trend: 'up',
      icon: DollarSign
    },
    {
      label: 'Market Velocity',
      value: '23 days',
      change: -8.2,
      trend: 'down',
      icon: Zap
    },
    {
      label: 'Inventory Levels',
      value: '2,847 units',
      change: 3.4,
      trend: 'up',
      icon: Building2
    },
    {
      label: 'Buyer Demand Index',
      value: '78/100',
      change: 15.7,
      trend: 'up',
      icon: Users
    }
  ]

  const propertyPredictions: PropertyPrediction[] = [
    {
      address: '123 Oak Street, Downtown',
      currentValue: 425000,
      predictedValue: 467000,
      confidence: 87,
      timeframe: '6 months'
    },
    {
      address: '456 Maple Ave, Suburbia',
      currentValue: 315000,
      predictedValue: 329000,
      confidence: 92,
      timeframe: '6 months'
    },
    {
      address: '789 Pine Road, Riverside',
      currentValue: 580000,
      predictedValue: 634000,
      confidence: 75,
      timeframe: '6 months'
    }
  ]

  const competitiveInsights = [
    {
      competitor: 'Prestige Realty Group',
      marketShare: 18.5,
      averageCommission: 2.8,
      clientSatisfaction: 4.2,
      strength: 'Luxury market dominance'
    },
    {
      competitor: 'Metro Home Solutions',
      marketShare: 14.2,
      averageCommission: 2.5,
      clientSatisfaction: 4.5,
      strength: 'Digital marketing excellence'
    },
    {
      competitor: 'Citywide Properties',
      marketShare: 12.1,
      averageCommission: 3.1,
      clientSatisfaction: 3.9,
      strength: 'Commercial expertise'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Market Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {marketMetrics.map((metric, index) => {
          const Icon = metric.icon
          return (
            <Card key={index} className="relative overflow-hidden">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {metric.label}
                </CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metric.value}</div>
                <div className="flex items-center space-x-1 text-sm">
                  {metric.trend === 'up' ? (
                    <TrendingUp className="h-3 w-3 text-green-600" />
                  ) : (
                    <TrendingDown className="h-3 w-3 text-red-600" />
                  )}
                  <span className={metric.trend === 'up' ? 'text-green-600' : 'text-red-600'}>
                    {Math.abs(metric.change)}%
                  </span>
                  <span className="text-muted-foreground">from last period</span>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Tabbed Analysis */}
      <Tabs defaultValue="predictions" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="predictions">Value Predictions</TabsTrigger>
          <TabsTrigger value="trends">Market Trends</TabsTrigger>
          <TabsTrigger value="competitive">Competition</TabsTrigger>
          <TabsTrigger value="insights">AI Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="predictions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-blue-600" />
                Property Value Predictions
              </CardTitle>
              <CardDescription>
                AI-powered property value forecasts with confidence intervals
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {propertyPredictions.map((prediction, index) => (
                  <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <MapPin className="h-4 w-4 text-slate-500" />
                        <span className="font-medium">{prediction.address}</span>
                      </div>
                      <div className="text-sm text-slate-600">
                        Confidence: {prediction.confidence}% • {prediction.timeframe}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-slate-600">Current Value</div>
                      <div className="font-bold">${prediction.currentValue.toLocaleString()}</div>
                      <div className="text-sm text-green-600 font-medium">
                        ↗ ${prediction.predictedValue.toLocaleString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LineChart className="h-5 w-5 text-purple-600" />
                  Price Trends
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 bg-gradient-to-t from-purple-50 to-white rounded-lg border-2 border-dashed border-purple-200 flex items-center justify-center">
                  <div className="text-center space-y-2">
                    <BarChart3 className="h-12 w-12 text-purple-400 mx-auto" />
                    <p className="text-sm text-slate-600">Interactive price trend chart</p>
                    <p className="text-xs text-slate-400">12-month rolling average</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="h-5 w-5 text-orange-600" />
                  Market Segmentation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 bg-gradient-to-t from-orange-50 to-white rounded-lg border-2 border-dashed border-orange-200 flex items-center justify-center">
                  <div className="text-center space-y-2">
                    <PieChart className="h-12 w-12 text-orange-400 mx-auto" />
                    <p className="text-sm text-slate-600">Market segment distribution</p>
                    <p className="text-xs text-slate-400">By property type & price range</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="competitive" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Award className="h-5 w-5 text-amber-600" />
                Competitive Analysis
              </CardTitle>
              <CardDescription>
                Market position and competitor insights
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {competitiveInsights.map((competitor, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <div className="font-semibold text-lg">{competitor.competitor}</div>
                      <div className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        {competitor.marketShare}% Market Share
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <div className="text-slate-600">Avg. Commission</div>
                        <div className="font-medium">{competitor.averageCommission}%</div>
                      </div>
                      <div>
                        <div className="text-slate-600">Client Rating</div>
                        <div className="font-medium">{competitor.clientSatisfaction}/5.0</div>
                      </div>
                      <div>
                        <div className="text-slate-600">Key Strength</div>
                        <div className="font-medium text-green-700">{competitor.strength}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="border-l-4 border-l-blue-500">
              <CardHeader>
                <CardTitle className="text-blue-900">Market Opportunity</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-700 mb-3">
                  First-time buyer segment shows 34% growth potential in Q2. 
                  Consider targeting properties under $400K with enhanced digital marketing.
                </p>
                <Button size="sm" variant="outline">
                  Explore Opportunity
                </Button>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-amber-500">
              <CardHeader>
                <CardTitle className="text-amber-900">Risk Alert</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-700 mb-3">
                  Luxury segment ($800K+) showing 12% decline in buyer inquiries. 
                  Monitor interest rate impacts on high-value transactions.
                </p>
                <Button size="sm" variant="outline">
                  Review Strategy
                </Button>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-green-500">
              <CardHeader>
                <CardTitle className="text-green-900">Growth Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-700 mb-3">
                  Suburban markets outperforming urban by 18%. Inventory levels 
                  suggest expansion opportunities in emerging neighborhoods.
                </p>
                <Button size="sm" variant="outline">
                  View Details
                </Button>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-purple-500">
              <CardHeader>
                <CardTitle className="text-purple-900">AI Recommendation</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-700 mb-3">
                  Implement dynamic pricing strategy for listings over 60 days. 
                  AI models suggest 15% faster sales with price optimization.
                </p>
                <Button size="sm" variant="outline">
                  Implement Strategy
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}