'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Check, Mic, Users, Building, ArrowRight, Star, Calculator, TrendingUp, DollarSign } from 'lucide-react'
import { useExperimentVariant, useABTest } from './ABTestProvider'

export default function ABTestPricingSection() {
  const { track } = useABTest()
  const [calculatorInputs, setCalculatorInputs] = useState({
    currentLeads: 50,
    currentConversion: 15,
    averageCommission: 6000
  })
  
  // Get pricing variant for testing
  const pricingVariant = useExperimentVariant('pricing-presentation')
  
  const pricingConfig = pricingVariant?.config || {
    displayType: 'monthly',
    showAnnualDiscount: false,
    priceFirst: true,
    showFeatures: true
  }

  const plans = [
    {
      name: 'Starter',
      monthlyPrice: 97,
      annualPrice: 679, // 30% discount
      period: '/month',
      description: 'Perfect for individual agents',
      icon: Mic,
      popular: false,
      features: [
        '24/7 voice agent',
        'Up to 100 conversations/month',
        'Basic lead qualification',
        'Calendar integration',
        'Email notifications',
        'Mobile app access',
        'Standard support'
      ],
      cta: 'Start Free Trial'
    },
    {
      name: 'Professional',
      monthlyPrice: 197,
      annualPrice: 1379, // 30% discount
      period: '/month',
      description: 'For growing teams and brokers',
      icon: Users,
      popular: true,
      features: [
        'Everything in Starter',
        'Up to 500 conversations/month',
        'Advanced qualification scoring',
        'Custom scripts & responses',
        'Team performance analytics',
        'CRM integrations',
        'Priority support',
        'White-label options'
      ],
      cta: 'Start Free Trial'
    },
    {
      name: 'Enterprise',
      monthlyPrice: 'Custom',
      annualPrice: 'Custom',
      period: '',
      description: 'For large brokerages and agencies',
      icon: Building,
      popular: false,
      features: [
        'Everything in Professional',
        'Unlimited conversations',
        'Multi-tenant management',
        'Custom AI training',
        'Advanced analytics & reporting',
        'API access',
        'Dedicated success manager',
        'Custom integrations',
        'SLA guarantees'
      ],
      cta: 'Contact Sales'
    }
  ]

  const calculateROI = () => {
    const currentQualified = (calculatorInputs.currentLeads * calculatorInputs.currentConversion) / 100
    const withAI = (calculatorInputs.currentLeads * 45) / 100 // 45% conversion with AI
    const additionalDeals = withAI - currentQualified
    const additionalAnnualCommission = additionalDeals * 12 * calculatorInputs.averageCommission
    return Math.round(additionalAnnualCommission)
  }

  const handlePlanClick = (planName: string, action: string) => {
    track('pricing_plan_clicked', {
      plan_name: planName,
      action: action,
      pricing_variant: pricingVariant?.id,
      display_type: pricingConfig.displayType
    })
  }

  const handleCalculatorChange = (field: string, value: number) => {
    setCalculatorInputs(prev => ({ ...prev, [field]: value }))
    track('roi_calculator_input', {
      field: field,
      value: value,
      pricing_variant: pricingVariant?.id
    })
  }

  const renderPricingCard = (plan: any, index: number) => {
    const Icon = plan.icon
    const isAnnual = pricingConfig.displayType === 'annual'
    const displayPrice = isAnnual && typeof plan.annualPrice === 'number' 
      ? Math.round(plan.annualPrice / 12) 
      : plan.monthlyPrice
    const originalPrice = plan.monthlyPrice
    
    return (
      <div
        key={index}
        className={`card p-8 relative ${
          plan.popular ? 'border-foreground border-2' : ''
        }`}
      >
        {plan.popular && (
          <div className="absolute -top-4 left-1/2 -translate-x-1/2">
            <div className="bg-foreground text-background px-4 py-2 rounded-full text-sm font-semibold flex items-center gap-2">
              <Star className="w-4 h-4" />
              Most Popular
            </div>
          </div>
        )}

        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
            <Icon className="w-8 h-8" />
          </div>
          <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
          <p className="text-muted-foreground mb-4">{plan.description}</p>
          
          {/* Dynamic pricing display based on experiment variant */}
          {pricingConfig.priceFirst ? (
            <div>
              <div className="flex items-baseline justify-center gap-1 mb-2">
                <span className="text-4xl font-bold">
                  {typeof displayPrice === 'number' ? `$${displayPrice}` : displayPrice}
                </span>
                <span className="text-muted-foreground">{plan.period}</span>
              </div>
              
              {isAnnual && pricingConfig.showAnnualDiscount && typeof plan.annualPrice === 'number' && (
                <div className="flex items-center justify-center gap-2">
                  <span className="text-sm text-muted-foreground line-through">${originalPrice}/mo</span>
                  <span className="text-sm text-green-600 font-semibold bg-green-100 px-2 py-1 rounded">
                    Save 30%
                  </span>
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Features first variant */}
        {pricingConfig.showFeatures && (
          <ul className="space-y-3 mb-8">
            {plan.features.map((feature: string, featureIndex: number) => (
              <li key={featureIndex} className="flex items-center gap-3">
                <Check className="w-5 h-5 text-green-600 shrink-0" />
                <span className="text-sm">{feature}</span>
              </li>
            ))}
          </ul>
        )}

        {/* Price second variant */}
        {!pricingConfig.priceFirst && (
          <div className="text-center mb-6">
            <div className="flex items-baseline justify-center gap-1">
              <span className="text-3xl font-bold">
                {typeof displayPrice === 'number' ? `$${displayPrice}` : displayPrice}
              </span>
              <span className="text-muted-foreground">{plan.period}</span>
            </div>
          </div>
        )}

        <button
          onClick={() => handlePlanClick(plan.name, plan.cta)}
          className={`w-full py-3 text-lg font-semibold rounded-lg transition-all group ${
            plan.popular
              ? 'bg-foreground text-background hover:bg-muted-foreground'
              : 'border border-border hover:bg-muted'
          }`}
        >
          {plan.cta}
          <ArrowRight className="w-5 h-5 ml-2 inline group-hover:translate-x-1 transition-transform" />
        </button>
      </div>
    )
  }

  const renderROICalculator = () => {
    if (pricingConfig.displayType !== 'calculator') return null

    const projectedROI = calculateROI()
    
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
        viewport={{ once: true }}
        className="card p-8 mb-16"
      >
        <div className="text-center mb-8">
          <Calculator className="w-12 h-12 mx-auto mb-4 text-green-600" />
          <h3 className="text-2xl font-bold mb-4">Interactive ROI Calculator</h3>
          <p className="text-muted-foreground">
            Customize these inputs to see your potential return on investment
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Input Controls */}
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2">Current leads per month</label>
              <input
                type="range"
                min="10"
                max="200"
                value={calculatorInputs.currentLeads}
                onChange={(e) => handleCalculatorChange('currentLeads', parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-muted-foreground mt-1">
                <span>10</span>
                <span className="font-semibold">{calculatorInputs.currentLeads}</span>
                <span>200</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Current conversion rate (%)</label>
              <input
                type="range"
                min="5"
                max="50"
                value={calculatorInputs.currentConversion}
                onChange={(e) => handleCalculatorChange('currentConversion', parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-muted-foreground mt-1">
                <span>5%</span>
                <span className="font-semibold">{calculatorInputs.currentConversion}%</span>
                <span>50%</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Average commission per deal</label>
              <input
                type="range"
                min="2000"
                max="15000"
                step="500"
                value={calculatorInputs.averageCommission}
                onChange={(e) => handleCalculatorChange('averageCommission', parseInt(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-muted-foreground mt-1">
                <span>$2K</span>
                <span className="font-semibold">${calculatorInputs.averageCommission.toLocaleString()}</span>
                <span>$15K</span>
              </div>
            </div>
          </div>

          {/* Results */}
          <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-lg p-6">
            <div className="text-center">
              <TrendingUp className="w-12 h-12 text-green-600 mx-auto mb-4" />
              <div className="text-3xl font-bold text-green-600 mb-2">
                ${projectedROI.toLocaleString()}
              </div>
              <div className="text-sm text-gray-600 mb-6">
                Additional annual commission with Seiketsu AI
              </div>
              
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span>Current qualified leads/month:</span>
                  <span className="font-semibold">
                    {Math.round((calculatorInputs.currentLeads * calculatorInputs.currentConversion) / 100)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>With Seiketsu AI (45% conversion):</span>
                  <span className="font-semibold text-green-600">
                    {Math.round((calculatorInputs.currentLeads * 45) / 100)}
                  </span>
                </div>
                <div className="flex justify-between border-t pt-3">
                  <span>ROI multiple vs Professional plan:</span>
                  <span className="font-semibold text-green-600">
                    {Math.round(projectedROI / (197 * 12))}x
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="text-center mt-8">
          <button 
            onClick={() => handlePlanClick('ROI Calculator', 'Get Custom Report')}
            className="btn btn-primary text-lg px-8 py-4 group"
          >
            <DollarSign className="w-5 h-5 mr-2" />
            Get Your Custom ROI Report
            <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </motion.div>
    )
  }

  return (
    <section id="pricing" className="py-20">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl lg:text-4xl font-bold mb-6">
            Simple, Transparent Pricing
          </h2>
          <p className="text-xl text-muted-foreground text-balance max-w-3xl mx-auto">
            Start qualifying leads in minutes, not months. All plans include 
            14-day free trial with full access to features.
          </p>
          
          {/* Annual/Monthly Toggle for Annual Focus Variant */}
          {pricingConfig.showAnnualDiscount && (
            <div className="flex items-center justify-center gap-4 mt-6">
              <span className={`text-sm ${pricingConfig.displayType === 'monthly' ? 'font-semibold' : 'text-muted-foreground'}`}>
                Monthly
              </span>
              <div className="relative">
                <input type="checkbox" className="sr-only" checked={pricingConfig.displayType === 'annual'} readOnly />
                <div className="w-12 h-6 bg-muted rounded-full border border-border"></div>
                <div className={`absolute top-0.5 left-0.5 w-5 h-5 bg-foreground rounded-full transition-transform ${
                  pricingConfig.displayType === 'annual' ? 'translate-x-6' : ''
                }`}></div>
              </div>
              <span className={`text-sm ${pricingConfig.displayType === 'annual' ? 'font-semibold' : 'text-muted-foreground'}`}>
                Annual
                <span className="ml-1 text-green-600 font-semibold">(Save 30%)</span>
              </span>
            </div>
          )}
        </motion.div>

        {/* Render ROI Calculator if that's the variant */}
        {renderROICalculator()}

        {/* Pricing Cards - Only show if not calculator variant */}
        {pricingConfig.displayType !== 'calculator' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            viewport={{ once: true }}
            className="grid lg:grid-cols-3 gap-8 mb-16"
          >
            {plans.map((plan, index) => renderPricingCard(plan, index))}
          </motion.div>
        )}

        {/* Standard ROI Section for non-calculator variants */}
        {pricingConfig.displayType !== 'calculator' && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            viewport={{ once: true }}
            className="card p-8 mb-16"
          >
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold mb-4">Calculate Your ROI</h3>
              <p className="text-muted-foreground">
                See how much additional commission you could earn with better lead qualification
              </p>
            </div>

            <div className="grid md:grid-cols-4 gap-6 text-center">
              <div>
                <div className="text-3xl font-bold mb-2">50</div>
                <div className="text-sm text-muted-foreground">Current leads/month</div>
              </div>
              <div>
                <div className="text-3xl font-bold mb-2">15%</div>
                <div className="text-sm text-muted-foreground">Current conversion</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600 mb-2">45%</div>
                <div className="text-sm text-muted-foreground">With Seiketsu AI</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600 mb-2">$90K</div>
                <div className="text-sm text-muted-foreground">Additional annual commission</div>
              </div>
            </div>

            <div className="text-center mt-6">
              <button 
                onClick={() => handlePlanClick('Standard ROI', 'Get Custom Report')}
                className="btn btn-primary text-lg group"
              >
                Get Your Custom ROI Report
                <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </motion.div>
        )}

        {/* Final CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          viewport={{ once: true }}
          className="text-center mt-16 py-12 bg-muted/30 rounded-2xl"
        >
          <h3 className="text-2xl font-bold mb-4">
            Ready to Transform Your Lead Qualification?
          </h3>
          <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
            Join hundreds of real estate professionals who have 3x their qualified leads 
            with voice AI technology.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button 
              onClick={() => handlePlanClick('Final CTA', 'Start Free Trial')}
              className="btn btn-primary text-lg px-8 py-4 group"
            >
              <Mic className="w-5 h-5 mr-2 voice-indicator" />
              Start Free Trial
              <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
            </button>
            <button 
              onClick={() => handlePlanClick('Final CTA', 'Schedule Demo')}
              className="btn btn-secondary text-lg px-8 py-4"
            >
              Schedule Demo Call
            </button>
          </div>
          <p className="text-sm text-muted-foreground mt-4">
            No credit card required • 14-day free trial • Cancel anytime
          </p>
        </motion.div>
      </div>
    </section>
  )
}