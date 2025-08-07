'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import RealEstateAgencyROICalculator from './RealEstateAgencyROICalculator'
import PropertyManagementROICalculator from './PropertyManagementROICalculator'
import CommercialRealEstateROICalculator from './CommercialRealEstateROICalculator'

export default function ROICalculatorHub() {
  const [activeTab, setActiveTab] = useState('residential')

  const calculatorTypes = [
    {
      id: 'residential',
      title: 'Real Estate Agency',
      description: 'Residential real estate agencies and brokerages',
      icon: '🏠',
      highlights: ['180% higher conversion', '24/7 lead engagement', '65% productivity boost'],
      component: RealEstateAgencyROICalculator
    },
    {
      id: 'property-management',
      title: 'Property Management',
      description: 'Rental property management companies',
      icon: '🏢',
      highlights: ['78% process automation', '52% cost reduction', '92% tenant satisfaction'],
      component: PropertyManagementROICalculator
    },
    {
      id: 'commercial',
      title: 'Commercial Real Estate',
      description: 'Commercial real estate firms and brokers',
      icon: '🏗️',
      highlights: ['42% faster sales cycles', '230% close rate improvement', '88% client retention'],
      component: CommercialRealEstateROICalculator
    }
  ]

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-6 py-12">
        <h1 className="text-5xl font-bold text-primary">
          Seiketsu AI ROI Calculator Suite
        </h1>
        <p className="text-2xl text-muted-foreground max-w-4xl mx-auto">
          Calculate your exact ROI with our interactive calculators designed for different real estate sectors. 
          See how Seiketsu AI delivers 200-400% ROI within 30 days.
        </p>
        
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mt-12">
          <Card className="p-6 text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">500+</div>
            <div className="text-sm text-muted-foreground">Companies Trust Seiketsu</div>
          </Card>
          <Card className="p-6 text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">320%</div>
            <div className="text-sm text-muted-foreground">Average ROI Achieved</div>
          </Card>
          <Card className="p-6 text-center">
            <div className="text-3xl font-bold text-purple-600 mb-2">30</div>
            <div className="text-sm text-muted-foreground">Days to Full ROI</div>
          </Card>
          <Card className="p-6 text-center">
            <div className="text-3xl font-bold text-orange-600 mb-2">24/7</div>
            <div className="text-sm text-muted-foreground">AI Agent Availability</div>
          </Card>
        </div>
      </div>

      {/* Calculator Selection */}
      <div className="space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-semibold mb-4">Choose Your Industry Calculator</h2>
          <p className="text-lg text-muted-foreground">
            Select the calculator that matches your business model for the most accurate ROI projections
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-1 md:grid-cols-3 h-auto p-2 bg-muted/30">
            {calculatorTypes.map((calc) => (
              <TabsTrigger
                key={calc.id}
                value={calc.id}
                className="flex flex-col items-center space-y-3 p-6 data-[state=active]:bg-background data-[state=active]:shadow-md"
              >
                <div className="text-4xl mb-2">{calc.icon}</div>
                <div className="text-lg font-semibold">{calc.title}</div>
                <div className="text-sm text-muted-foreground text-center">{calc.description}</div>
                <div className="flex flex-wrap gap-2 mt-3">
                  {calc.highlights.map((highlight, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary"
                    >
                      {highlight}
                    </span>
                  ))}
                </div>
              </TabsTrigger>
            ))}
          </TabsList>

          {calculatorTypes.map((calc) => (
            <TabsContent key={calc.id} value={calc.id} className="mt-8">
              <calc.component />
            </TabsContent>
          ))}
        </Tabs>
      </div>

      {/* Value Proposition */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 py-12">
        <Card className="p-8">
          <h3 className="text-2xl font-semibold mb-6">Why Seiketsu AI Delivers Superior ROI</h3>
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-white text-xs">✓</span>
              </div>
              <div>
                <div className="font-medium">Instant Implementation</div>
                <div className="text-sm text-muted-foreground">Deploy in 24 hours, see results in week 1</div>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-white text-xs">✓</span>
              </div>
              <div>
                <div className="font-medium">Human-Like Intelligence</div>
                <div className="text-sm text-muted-foreground">Advanced AI that understands context and nuance</div>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-purple-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-white text-xs">✓</span>
              </div>
              <div>
                <div className="font-medium">Seamless Integration</div>
                <div className="text-sm text-muted-foreground">Works with your existing CRM and tools</div>
              </div>
            </div>
            
            <div className="flex items-start space-x-3">
              <div className="w-6 h-6 bg-orange-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <span className="text-white text-xs">✓</span>
              </div>
              <div>
                <div className="font-medium">Proven Results</div>
                <div className="text-sm text-muted-foreground">500+ successful deployments across all sectors</div>
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-8">
          <h3 className="text-2xl font-semibold mb-6">Implementation Timeline</h3>
          <div className="space-y-6">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
                <span className="font-bold text-blue-600 dark:text-blue-400">1</span>
              </div>
              <div>
                <div className="font-medium">Day 1: Setup & Configuration</div>
                <div className="text-sm text-muted-foreground">AI training on your business processes</div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                <span className="font-bold text-green-600 dark:text-green-400">7</span>
              </div>
              <div>
                <div className="font-medium">Week 1: First Results</div>
                <div className="text-sm text-muted-foreground">Initial ROI becomes visible</div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center">
                <span className="font-bold text-purple-600 dark:text-purple-400">30</span>
              </div>
              <div>
                <div className="font-medium">Month 1: Full ROI Realization</div>
                <div className="text-sm text-muted-foreground">Complete return on investment achieved</div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* CTA Section */}
      <Card className="p-12 text-center bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950">
        <h2 className="text-3xl font-bold mb-4">Ready to Transform Your Business?</h2>
        <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
          Join hundreds of real estate professionals who've already achieved 200-400% ROI with Seiketsu AI
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button size="lg" className="bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:from-blue-700 hover:to-purple-700">
            Start Free 14-Day Trial
          </Button>
          <Button size="lg" variant="outline">
            Schedule Live Demo
          </Button>
        </div>
        
        <div className="mt-8 flex flex-wrap justify-center gap-8 text-sm text-muted-foreground">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>No credit card required</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span>24-hour setup</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
            <span>White-glove onboarding</span>
          </div>
        </div>
      </Card>
    </div>
  )
}