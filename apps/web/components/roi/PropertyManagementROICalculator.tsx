'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

interface PMROIMetrics {
  monthlyROI: number
  quarterlyROI: number
  annualROI: number
  timeSavingsHours: number
  costReduction: number
  tenantSatisfaction: number
  operationalEfficiency: number
}

export default function PropertyManagementROICalculator() {
  const [inputs, setInputs] = useState({
    properties: 250,
    avgRent: 1800,
    tenantInteractions: 45,
    maintenanceRequests: 28,
    staffHours: 160,
    currentOpsCost: 15000
  })

  const [roi, setROI] = useState<PMROIMetrics>({
    monthlyROI: 0,
    quarterlyROI: 0,
    annualROI: 0,
    timeSavingsHours: 0,
    costReduction: 0,
    tenantSatisfaction: 0,
    operationalEfficiency: 0
  })

  const [isCalculating, setIsCalculating] = useState(false)

  useEffect(() => {
    calculateROI()
  }, [inputs])

  const calculateROI = async () => {
    setIsCalculating(true)
    
    await new Promise(resolve => setTimeout(resolve, 400))

    const { properties, avgRent, tenantInteractions, maintenanceRequests, staffHours, currentOpsCost } = inputs

    // Seiketsu AI improvements for property management
    const automationRate = 0.78 // 78% of interactions automated
    const responseTimeImprovement = 0.92 // 92% faster responses
    const maintenanceEfficiency = 0.65 // 65% more efficient maintenance coordination
    const tenantRetentionImprovement = 0.25 // 25% better retention
    const costReductionRate = 0.52 // 52% operational cost reduction

    // Current metrics
    const monthlyRevenue = properties * avgRent
    const currentTurnoverRate = 0.15 // 15% annual turnover (industry average)
    const turnoverCost = avgRent * 2.5 // Cost to replace tenant

    // Improvements with Seiketsu AI
    const automatedInteractions = tenantInteractions * automationRate
    const timeSaved = (automatedInteractions * 0.5) + (maintenanceRequests * 0.75) // Hours saved per interaction
    const operationalSavings = currentOpsCost * costReductionRate
    const retentionRevenue = (properties * currentTurnoverRate * tenantRetentionImprovement) * turnoverCost

    // Seiketsu costs
    const seiketsuMonthlyCost = Math.ceil(properties / 50) * 499 // $499 per 50 properties
    
    // ROI calculations
    const totalMonthlySavings = operationalSavings + (retentionRevenue / 12)
    const monthlyROI = ((totalMonthlySavings - seiketsuMonthlyCost) / seiketsuMonthlyCost) * 100

    setROI({
      monthlyROI: Math.round(monthlyROI),
      quarterlyROI: Math.round(monthlyROI * 3),
      annualROI: Math.round(monthlyROI * 12),
      timeSavingsHours: Math.round(timeSaved),
      costReduction: Math.round(operationalSavings),
      tenantSatisfaction: Math.round(92), // 92% satisfaction rate
      operationalEfficiency: Math.round(automationRate * 100)
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
      summary: `Seiketsu AI Property Management: ${roi.monthlyROI}% monthly ROI for ${inputs.properties} properties`
    }
    
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'seiketsu-pm-roi-report.json'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-primary">Property Management ROI Calculator</h1>
        <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
          Transform your property management operations with AI-powered tenant communication and maintenance coordination
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Panel */}
        <Card className="p-6">
          <h2 className="text-2xl font-semibold mb-6">Your Portfolio Details</h2>
          
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="form-group">
                <label className="form-label">Number of Properties</label>
                <Input
                  type="number"
                  value={inputs.properties}
                  onChange={(e) => handleInputChange('properties', e.target.value)}
                  className="form-input"
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Average Monthly Rent</label>
                <Input
                  type="number"
                  value={inputs.avgRent}
                  onChange={(e) => handleInputChange('avgRent', e.target.value)}
                  className="form-input"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="form-group">
                <label className="form-label">Tenant Interactions/Month</label>
                <Input
                  type="number"
                  value={inputs.tenantInteractions}
                  onChange={(e) => handleInputChange('tenantInteractions', e.target.value)}
                  className="form-input"
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Maintenance Requests/Month</label>
                <Input
                  type="number"
                  value={inputs.maintenanceRequests}
                  onChange={(e) => handleInputChange('maintenanceRequests', e.target.value)}
                  className="form-input"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="form-group">
                <label className="form-label">Staff Hours/Month</label>
                <Input
                  type="number"
                  value={inputs.staffHours}
                  onChange={(e) => handleInputChange('staffHours', e.target.value)}
                  className="form-input"
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Monthly Operational Costs</label>
                <Input
                  type="number"
                  value={inputs.currentOpsCost}
                  onChange={(e) => handleInputChange('currentOpsCost', e.target.value)}
                  className="form-input"
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Results Panel */}
        <Card className="p-6">
          <h2 className="text-2xl font-semibold mb-6">Operational Transformation</h2>
          
          {isCalculating ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Key ROI Metrics */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-gradient-to-br from-emerald-50 to-green-100 dark:from-emerald-950 dark:to-green-900 rounded-lg">
                  <div className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">
                    {roi.monthlyROI}%
                  </div>
                  <div className="text-sm text-emerald-700 dark:text-emerald-300">Monthly ROI</div>
                </div>
                
                <div className="text-center p-4 bg-gradient-to-br from-cyan-50 to-blue-100 dark:from-cyan-950 dark:to-blue-900 rounded-lg">
                  <div className="text-3xl font-bold text-cyan-600 dark:text-cyan-400">
                    {roi.quarterlyROI}%
                  </div>
                  <div className="text-sm text-cyan-700 dark:text-cyan-300">Quarterly ROI</div>
                </div>
                
                <div className="text-center p-4 bg-gradient-to-br from-indigo-50 to-purple-100 dark:from-indigo-950 dark:to-purple-900 rounded-lg">
                  <div className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                    {roi.annualROI}%
                  </div>
                  <div className="text-sm text-indigo-700 dark:text-indigo-300">Annual ROI</div>
                </div>
              </div>

              {/* Operational Metrics */}
              <div className="space-y-4">
                <div className="flex justify-between items-center p-4 bg-gradient-to-r from-orange-50 to-yellow-50 dark:from-orange-950 dark:to-yellow-950 rounded-lg">
                  <span className="font-medium">Time Savings per Month</span>
                  <span className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                    {roi.timeSavingsHours}h
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-4 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 rounded-lg">
                  <span className="font-medium">Monthly Cost Reduction</span>
                  <span className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {formatCurrency(roi.costReduction)}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-4 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-950 dark:to-pink-950 rounded-lg">
                  <span className="font-medium">Tenant Satisfaction Score</span>
                  <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {roi.tenantSatisfaction}%
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 rounded-lg">
                  <span className="font-medium">Process Automation</span>
                  <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {roi.operationalEfficiency}%
                  </span>
                </div>
              </div>

              {/* Key Features */}
              <div className="space-y-3 p-4 bg-muted/30 rounded-lg">
                <h3 className="font-semibold text-lg">Seiketsu PM Features:</h3>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>Automated tenant communication & screening</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span>Smart maintenance request routing & scheduling</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                    <span>Rent collection reminders & payment processing</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                    <span>Property inspection scheduling & reporting</span>
                  </li>
                </ul>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Efficiency Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <Card className="p-6">
          <h3 className="text-xl font-semibold mb-4 text-red-600">Without Seiketsu AI</h3>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span>Response Time</span>
              <span className="font-bold">4-24 hours</span>
            </div>
            <div className="flex justify-between">
              <span>Manual Processes</span>
              <span className="font-bold">85%</span>
            </div>
            <div className="flex justify-between">
              <span>Tenant Satisfaction</span>
              <span className="font-bold">67%</span>
            </div>
            <div className="flex justify-between">
              <span>Staff Utilization</span>
              <span className="font-bold">60%</span>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-xl font-semibold mb-4 text-green-600">With Seiketsu AI</h3>
          <div className="space-y-4">
            <div className="flex justify-between">
              <span>Response Time</span>
              <span className="font-bold text-green-600">Instant</span>
            </div>
            <div className="flex justify-between">
              <span>Manual Processes</span>
              <span className="font-bold text-green-600">22%</span>
            </div>
            <div className="flex justify-between">
              <span>Tenant Satisfaction</span>
              <span className="font-bold text-green-600">92%</span>
            </div>
            <div className="flex justify-between">
              <span>Staff Utilization</span>
              <span className="font-bold text-green-600">88%</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Action Panel */}
      <Card className="p-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-center sm:text-left">
            <h3 className="text-xl font-semibold">Optimize Your Property Management</h3>
            <p className="text-muted-foreground">
              Join 200+ property management companies using Seiketsu AI
            </p>
          </div>
          
          <div className="flex gap-3">
            <Button onClick={exportReport} variant="outline">
              Export Analysis
            </Button>
            <Button className="bg-gradient-to-r from-emerald-600 to-green-600 text-white hover:from-emerald-700 hover:to-green-700">
              Schedule Demo
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}