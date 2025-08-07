'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface ROIMetrics {
  monthlyROI: number
  quarterlyROI: number
  annualROI: number
  monthlySavings: number
  additionalRevenue: number
  efficiency: number
}

export default function RealEstateAgencyROICalculator() {
  const [inputs, setInputs] = useState({
    agents: 10,
    avgDealValue: 25000,
    leadsPerMonth: 150,
    conversionRate: 3.5,
    avgResponseTime: 24,
    currentCosts: 8000
  })

  const [roi, setROI] = useState<ROIMetrics>({
    monthlyROI: 0,
    quarterlyROI: 0,
    annualROI: 0,
    monthlySavings: 0,
    additionalRevenue: 0,
    efficiency: 0
  })

  const [isCalculating, setIsCalculating] = useState(false)

  useEffect(() => {
    calculateROI()
  }, [inputs])

  const calculateROI = async () => {
    setIsCalculating(true)
    
    // Simulate real-time calculation
    await new Promise(resolve => setTimeout(resolve, 300))

    const { agents, avgDealValue, leadsPerMonth, conversionRate, avgResponseTime, currentCosts } = inputs

    // Seiketsu AI improvements
    const improvedConversionRate = conversionRate * 2.8 // 180% improvement
    const responseTimeReduction = 0.5 // 30 seconds vs 24 hours
    const agentEfficiencyGain = 0.65 // 65% more productive
    const costReduction = 0.45 // 45% cost savings

    // Current performance
    const currentDealsPerMonth = (leadsPerMonth * conversionRate) / 100
    const currentRevenue = currentDealsPerMonth * avgDealValue

    // Improved performance with Seiketsu AI
    const improvedDealsPerMonth = (leadsPerMonth * improvedConversionRate) / 100
    const improvedRevenue = improvedDealsPerMonth * avgDealValue

    // Cost calculations
    const seiketsuMonthlyCost = agents * 299 // $299 per agent/month
    const operationalSavings = currentCosts * costReduction
    const netMonthlyCost = seiketsuMonthlyCost - operationalSavings

    // ROI calculations
    const additionalRevenue = improvedRevenue - currentRevenue
    const monthlySavings = operationalSavings
    const totalMonthlyBenefit = additionalRevenue + monthlySavings
    const monthlyROI = ((totalMonthlyBenefit - seiketsuMonthlyCost) / seiketsuMonthlyCost) * 100

    setROI({
      monthlyROI: Math.round(monthlyROI),
      quarterlyROI: Math.round(monthlyROI * 3),
      annualROI: Math.round(monthlyROI * 12),
      monthlySavings: Math.round(monthlySavings),
      additionalRevenue: Math.round(additionalRevenue),
      efficiency: Math.round(agentEfficiencyGain * 100)
    })

    setIsCalculating(false)
  }

  const handleInputChange = (field: string, value: string) => {
    setInputs(prev => ({
      ...prev,
      [field]: parseFloat(value) || 0
    }))
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(amount)
  }

  const exportReport = () => {
    const report = {
      calculatedAt: new Date().toISOString(),
      inputs,
      results: roi,
      summary: `Seiketsu AI delivers ${roi.monthlyROI}% monthly ROI for ${inputs.agents} agents`
    }
    
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'seiketsu-roi-report.json'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-primary">Real Estate Agency ROI Calculator</h1>
        <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
          Discover how Seiketsu AI can transform your real estate agency with intelligent voice agents that deliver proven 200-400% ROI
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Panel */}
        <Card className="p-6">
          <h2 className="text-2xl font-semibold mb-6">Your Agency Details</h2>
          
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="form-group">
                <label className="form-label">Number of Agents</label>
                <Input
                  type="number"
                  value={inputs.agents}
                  onChange={(e) => handleInputChange('agents', e.target.value)}
                  className="form-input"
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Avg Commission per Deal</label>
                <Input
                  type="number"
                  value={inputs.avgDealValue}
                  onChange={(e) => handleInputChange('avgDealValue', e.target.value)}
                  className="form-input"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="form-group">
                <label className="form-label">Leads per Month</label>
                <Input
                  type="number"
                  value={inputs.leadsPerMonth}
                  onChange={(e) => handleInputChange('leadsPerMonth', e.target.value)}
                  className="form-input"
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Current Conversion Rate (%)</label>
                <Input
                  type="number"
                  step="0.1"
                  value={inputs.conversionRate}
                  onChange={(e) => handleInputChange('conversionRate', e.target.value)}
                  className="form-input"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="form-group">
                <label className="form-label">Avg Response Time (hours)</label>
                <Input
                  type="number"
                  value={inputs.avgResponseTime}
                  onChange={(e) => handleInputChange('avgResponseTime', e.target.value)}
                  className="form-input"
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Current Monthly Costs</label>
                <Input
                  type="number"
                  value={inputs.currentCosts}
                  onChange={(e) => handleInputChange('currentCosts', e.target.value)}
                  className="form-input"
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Results Panel */}
        <Card className="p-6">
          <h2 className="text-2xl font-semibold mb-6">Seiketsu AI Impact</h2>
          
          {isCalculating ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Key ROI Metrics */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-950 dark:to-green-900 rounded-lg">
                  <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                    {roi.monthlyROI}%
                  </div>
                  <div className="text-sm text-green-700 dark:text-green-300">Monthly ROI</div>
                </div>
                
                <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900 rounded-lg">
                  <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                    {roi.quarterlyROI}%
                  </div>
                  <div className="text-sm text-blue-700 dark:text-blue-300">Quarterly ROI</div>
                </div>
                
                <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-950 dark:to-purple-900 rounded-lg">
                  <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
                    {roi.annualROI}%
                  </div>
                  <div className="text-sm text-purple-700 dark:text-purple-300">Annual ROI</div>
                </div>
              </div>

              {/* Financial Impact */}
              <div className="space-y-4">
                <div className="flex justify-between items-center p-4 bg-gradient-to-r from-emerald-50 to-green-50 dark:from-emerald-950 dark:to-green-950 rounded-lg">
                  <span className="font-medium">Additional Monthly Revenue</span>
                  <span className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {formatCurrency(roi.additionalRevenue)}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-4 bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950 dark:to-cyan-950 rounded-lg">
                  <span className="font-medium">Monthly Cost Savings</span>
                  <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {formatCurrency(roi.monthlySavings)}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-4 bg-gradient-to-r from-orange-50 to-yellow-50 dark:from-orange-950 dark:to-yellow-950 rounded-lg">
                  <span className="font-medium">Agent Efficiency Gain</span>
                  <span className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                    +{roi.efficiency}%
                  </span>
                </div>
              </div>

              {/* Key Improvements */}
              <div className="space-y-3 p-4 bg-muted/30 rounded-lg">
                <h3 className="font-semibold text-lg">Seiketsu AI Delivers:</h3>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>180% higher conversion rates with instant AI responses</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span>24/7 lead engagement with human-like conversations</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                    <span>65% agent productivity improvement</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                    <span>45% reduction in operational costs</span>
                  </li>
                </ul>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Action Panel */}
      <Card className="p-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-center sm:text-left">
            <h3 className="text-xl font-semibold">Ready to Transform Your Agency?</h3>
            <p className="text-muted-foreground">
              Join 500+ real estate agencies already using Seiketsu AI
            </p>
          </div>
          
          <div className="flex gap-3">
            <Button onClick={exportReport} variant="outline">
              Export Report
            </Button>
            <Button className="bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700">
              Start Free Trial
            </Button>
          </div>
        </div>
      </Card>

      {/* Industry Benchmarks */}
      <Card className="p-6">
        <h3 className="text-xl font-semibold mb-4">Industry Comparison</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-red-500 mb-2">2.5%</div>
            <div className="text-sm text-muted-foreground">Industry Average Conversion</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-500 mb-2">24h</div>
            <div className="text-sm text-muted-foreground">Average Response Time</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-500 mb-2">{Math.round(inputs.conversionRate * 2.8)}%</div>
            <div className="text-sm text-muted-foreground">Your Rate with Seiketsu</div>
          </div>
        </div>
      </Card>
    </div>
  )
}