'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface CREROIMetrics {
  monthlyROI: number
  quarterlyROI: number
  annualROI: number
  dealAcceleration: number
  clientRetention: number
  marketingEfficiency: number
  revenueIncrease: number
}

export default function CommercialRealEstateROICalculator() {
  const [inputs, setInputs] = useState({
    avgDealSize: 2500000,
    dealsPerYear: 24,
    salesCycleDays: 180,
    clientTouchpoints: 35,
    marketingBudget: 45000,
    currentCloseRate: 18
  })

  const [roi, setROI] = useState<CREROIMetrics>({
    monthlyROI: 0,
    quarterlyROI: 0,
    annualROI: 0,
    dealAcceleration: 0,
    clientRetention: 0,
    marketingEfficiency: 0,
    revenueIncrease: 0
  })

  const [isCalculating, setIsCalculating] = useState(false)

  useEffect(() => {
    calculateROI()
  }, [inputs])

  const calculateROI = async () => {
    setIsCalculating(true)
    
    await new Promise(resolve => setTimeout(resolve, 500))

    const { avgDealSize, dealsPerYear, salesCycleDays, clientTouchpoints, marketingBudget, currentCloseRate } = inputs

    // Seiketsu AI improvements for commercial real estate
    const cycleReduction = 0.42 // 42% faster sales cycles
    const closeRateImprovement = 2.3 // 2.3x improvement in close rates
    const clientEngagement = 0.85 // 85% better client engagement
    const marketingEfficiencyGain = 0.68 // 68% more efficient marketing
    const relationshipQuality = 0.75 // 75% improvement in relationship quality

    // Current performance
    const currentRevenue = avgDealSize * dealsPerYear * (currentCloseRate / 100)
    const currentCycle = salesCycleDays

    // Improved performance with Seiketsu AI
    const improvedCycle = salesCycleDays * (1 - cycleReduction)
    const improvedCloseRate = currentCloseRate * closeRateImprovement
    const additionalDealsPerYear = Math.floor((365 / improvedCycle) * (improvedCloseRate / 100)) - dealsPerYear
    const improvedRevenue = avgDealSize * (dealsPerYear + additionalDealsPerYear) * (improvedCloseRate / 100)

    // Cost calculations
    const seiketsuMonthlyCost = 2499 // Premium CRE package
    const annualSeiketsuCost = seiketsuMonthlyCost * 12
    const marketingOptimization = marketingBudget * marketingEfficiencyGain

    // ROI calculations
    const revenueIncrease = improvedRevenue - currentRevenue
    const totalAnnualBenefit = revenueIncrease + (marketingOptimization * 12)
    const annualROI = ((totalAnnualBenefit - annualSeiketsuCost) / annualSeiketsuCost) * 100
    const monthlyROI = annualROI / 12

    setROI({
      monthlyROI: Math.round(monthlyROI),
      quarterlyROI: Math.round(annualROI / 4),
      annualROI: Math.round(annualROI),
      dealAcceleration: Math.round(cycleReduction * 100),
      clientRetention: Math.round(88), // 88% client retention with AI
      marketingEfficiency: Math.round(marketingEfficiencyGain * 100),
      revenueIncrease: Math.round(revenueIncrease)
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
      summary: `Seiketsu AI Commercial Real Estate: ${roi.annualROI}% annual ROI with ${formatCurrency(roi.revenueIncrease)} revenue increase`
    }
    
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'seiketsu-cre-roi-report.json'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-primary">Commercial Real Estate ROI Calculator</h1>
        <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
          Accelerate commercial deals and strengthen client relationships with enterprise-grade AI voice intelligence
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Panel */}
        <Card className="p-6">
          <h2 className="text-2xl font-semibold mb-6">Your CRE Business</h2>
          
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="form-group">
                <label className="form-label">Average Deal Size</label>
                <Input
                  type="number"
                  value={inputs.avgDealSize}
                  onChange={(e) => handleInputChange('avgDealSize', e.target.value)}
                  className="form-input"
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Deals per Year</label>
                <Input
                  type="number"
                  value={inputs.dealsPerYear}
                  onChange={(e) => handleInputChange('dealsPerYear', e.target.value)}
                  className="form-input"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="form-group">
                <label className="form-label">Sales Cycle (Days)</label>
                <Input
                  type="number"
                  value={inputs.salesCycleDays}
                  onChange={(e) => handleInputChange('salesCycleDays', e.target.value)}
                  className="form-input"
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Client Touchpoints per Deal</label>
                <Input
                  type="number"
                  value={inputs.clientTouchpoints}
                  onChange={(e) => handleInputChange('clientTouchpoints', e.target.value)}
                  className="form-input"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="form-group">
                <label className="form-label">Monthly Marketing Budget</label>
                <Input
                  type="number"
                  value={inputs.marketingBudget}
                  onChange={(e) => handleInputChange('marketingBudget', e.target.value)}
                  className="form-input"
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Current Close Rate (%)</label>
                <Input
                  type="number"
                  step="0.1"
                  value={inputs.currentCloseRate}
                  onChange={(e) => handleInputChange('currentCloseRate', e.target.value)}
                  className="form-input"
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Results Panel */}
        <Card className="p-6">
          <h2 className="text-2xl font-semibold mb-6">Revenue Acceleration</h2>
          
          {isCalculating ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Key ROI Metrics */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-gradient-to-br from-amber-50 to-orange-100 dark:from-amber-950 dark:to-orange-900 rounded-lg">
                  <div className="text-3xl font-bold text-amber-600 dark:text-amber-400">
                    {roi.monthlyROI}%
                  </div>
                  <div className="text-sm text-amber-700 dark:text-amber-300">Monthly ROI</div>
                </div>
                
                <div className="text-center p-4 bg-gradient-to-br from-violet-50 to-purple-100 dark:from-violet-950 dark:to-purple-900 rounded-lg">
                  <div className="text-3xl font-bold text-violet-600 dark:text-violet-400">
                    {roi.quarterlyROI}%
                  </div>
                  <div className="text-sm text-violet-700 dark:text-violet-300">Quarterly ROI</div>
                </div>
                
                <div className="text-center p-4 bg-gradient-to-br from-rose-50 to-pink-100 dark:from-rose-950 dark:to-pink-900 rounded-lg">
                  <div className="text-3xl font-bold text-rose-600 dark:text-rose-400">
                    {roi.annualROI}%
                  </div>
                  <div className="text-sm text-rose-700 dark:text-rose-300">Annual ROI</div>
                </div>
              </div>

              {/* Business Impact */}
              <div className="space-y-4">
                <div className="flex justify-between items-center p-4 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-950 dark:to-teal-950 rounded-lg">
                  <span className="font-medium">Additional Annual Revenue</span>
                  <span className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                    {formatCurrency(roi.revenueIncrease)}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 rounded-lg">
                  <span className="font-medium">Sales Cycle Acceleration</span>
                  <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    -{roi.dealAcceleration}%
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-4 bg-gradient-to-r from-purple-50 to-violet-50 dark:from-purple-950 dark:to-violet-950 rounded-lg">
                  <span className="font-medium">Client Retention Rate</span>
                  <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {roi.clientRetention}%
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-4 bg-gradient-to-r from-orange-50 to-red-50 dark:from-orange-950 dark:to-red-950 rounded-lg">
                  <span className="font-medium">Marketing Efficiency Gain</span>
                  <span className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                    +{roi.marketingEfficiency}%
                  </span>
                </div>
              </div>

              {/* Competitive Advantages */}
              <div className="space-y-3 p-4 bg-muted/30 rounded-lg">
                <h3 className="font-semibold text-lg">Seiketsu CRE Advantages:</h3>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>AI-powered client relationship management</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span>Intelligent market analysis & property matching</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                    <span>Automated due diligence coordination</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                    <span>Multi-party negotiation assistance</span>
                  </li>
                </ul>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Deal Timeline Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <Card className="p-6">
          <h3 className="text-xl font-semibold mb-6 text-center">Traditional CRE Process</h3>
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-sm font-bold">1</div>
              <div>
                <div className="font-medium">Initial Contact</div>
                <div className="text-sm text-muted-foreground">Manual outreach, 24-48h response</div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center text-sm font-bold">2</div>
              <div>
                <div className="font-medium">Qualification</div>
                <div className="text-sm text-muted-foreground">Multiple meetings, 2-3 weeks</div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-gray-400 rounded-full flex items-center justify-center text-sm font-bold">3</div>
              <div>
                <div className="font-medium">Property Search</div>
                <div className="text-sm text-muted-foreground">Manual research, 4-6 weeks</div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center text-sm font-bold">4</div>
              <div>
                <div className="font-medium">Negotiation & Close</div>
                <div className="text-sm text-muted-foreground">Back-and-forth, 8-12 weeks</div>
              </div>
            </div>
            <div className="mt-4 p-3 bg-red-50 dark:bg-red-950 rounded-lg">
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600 dark:text-red-400">180 days</div>
                <div className="text-sm text-red-700 dark:text-red-300">Average cycle time</div>
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-xl font-semibold mb-6 text-center">Seiketsu AI-Powered Process</h3>
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-sm font-bold text-white">1</div>
              <div>
                <div className="font-medium">AI Initial Engagement</div>
                <div className="text-sm text-muted-foreground">Instant response, qualification in minutes</div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-sm font-bold text-white">2</div>
              <div>
                <div className="font-medium">Smart Matching</div>
                <div className="text-sm text-muted-foreground">AI property analysis, 3-5 days</div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-sm font-bold text-white">3</div>
              <div>
                <div className="font-medium">Automated Coordination</div>
                <div className="text-sm text-muted-foreground">AI schedules tours, due diligence, 1-2 weeks</div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center text-sm font-bold text-white">4</div>
              <div>
                <div className="font-medium">AI-Assisted Close</div>
                <div className="text-sm text-muted-foreground">Smart negotiation support, 4-6 weeks</div>
              </div>
            </div>
            <div className="mt-4 p-3 bg-green-50 dark:bg-green-950 rounded-lg">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">105 days</div>
                <div className="text-sm text-green-700 dark:text-green-300">42% faster cycle</div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Action Panel */}
      <Card className="p-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-center sm:text-left">
            <h3 className="text-xl font-semibold">Transform Your CRE Practice</h3>
            <p className="text-muted-foreground">
              Join elite CRE firms already using Seiketsu AI for competitive advantage
            </p>
          </div>
          
          <div className="flex gap-3">
            <Button onClick={exportReport} variant="outline">
              Export Analysis
            </Button>
            <Button className="bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-700 hover:to-purple-700">
              Request Enterprise Demo
            </Button>
          </div>
        </div>
      </Card>

      {/* Market Impact */}
      <Card className="p-6">
        <h3 className="text-xl font-semibold mb-4">Market Positioning</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">${formatCurrency(inputs.avgDealSize * inputs.dealsPerYear * 0.18 / 100).slice(1)}</div>
            <div className="text-sm text-muted-foreground">Current Annual Revenue</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">{Math.round(inputs.currentCloseRate * 2.3)}%</div>
            <div className="text-sm text-muted-foreground">Improved Close Rate</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600 mb-2">{inputs.salesCycleDays - Math.round(inputs.salesCycleDays * 0.42)}</div>
            <div className="text-sm text-muted-foreground">Days Saved per Deal</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-orange-600 mb-2">{formatCurrency(roi.revenueIncrease)}</div>
            <div className="text-sm text-muted-foreground">Additional Revenue</div>
          </div>
        </div>
      </Card>
    </div>
  )
}