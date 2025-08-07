'use client'

import { useState } from 'react'
import { Mic, Play, ArrowRight, Users, Clock, TrendingUp, Calculator, Rocket } from 'lucide-react'
import { motion } from 'framer-motion'
import { useExperimentVariant, useABTest } from './ABTestProvider'

export default function ABTestHeroSection() {
  const [isPlaying, setIsPlaying] = useState(false)
  const { track } = useABTest()
  
  // Get headline variant for testing
  const headlineVariant = useExperimentVariant('landing-headline-test')
  const ctaVariant = useExperimentVariant('cta-optimization')
  
  // Default to control if no experiment is running
  const headlineConfig = headlineVariant?.config || {
    headline: 'Voice-First Real Estate Intelligence',
    subheadline: 'Transform your real estate business with AI-powered voice agents',
    cta: 'Book Free Demo'
  }
  
  const ctaConfig = ctaVariant?.config || {
    color: '#3b82f6',
    text: 'Book Free Demo',
    position: 'center',
    size: 'large'
  }

  const handleDemoClick = () => {
    setIsPlaying(!isPlaying)
    track('cta_clicked', {
      cta_type: 'hero_demo_button',
      cta_text: ctaConfig.text,
      cta_color: ctaConfig.color,
      experiment_headline: headlineVariant?.id,
      experiment_cta: ctaVariant?.id
    })
  }

  const handleROIClick = () => {
    track('roi_calculator_clicked', {
      source: 'hero_section',
      experiment_headline: headlineVariant?.id
    })
  }

  // Dynamic CTA button styles based on variant
  const ctaButtonStyle = {
    backgroundColor: ctaConfig.color,
    borderColor: ctaConfig.color,
    color: ctaConfig.color === '#f97316' ? 'white' : 'white' // Handle orange text color
  }

  return (
    <section className="relative px-6 py-20 lg:py-32">
      <div className="max-w-7xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="lg:pr-8"
          >
            {/* Trust Indicator Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-muted rounded-full text-sm text-muted-foreground mb-6">
              <Users className="w-4 h-4" />
              <span>Trusted by 500+ real estate professionals</span>
            </div>

            {/* Dynamic Headline Based on Experiment Variant */}
            <h1 className="text-4xl lg:text-6xl font-bold tracking-tight text-balance mb-6">
              {headlineConfig.headline}
            </h1>

            {/* Dynamic Subheadline */}
            <p className="text-xl text-muted-foreground text-balance mb-8 max-w-2xl">
              {headlineConfig.subheadline}
            </p>

            {/* Trust Metrics - Social Proof */}
            <div className="flex items-center gap-8 mb-8">
              <div className="text-center">
                <div className="text-2xl font-bold">95%</div>
                <div className="text-sm text-muted-foreground">Lead Quality</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">3x</div>
                <div className="text-sm text-muted-foreground">More Qualified</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold">24/7</div>
                <div className="text-sm text-muted-foreground">Availability</div>
              </div>
            </div>

            {/* Dynamic Primary CTA Based on Experiment */}
            <div className="flex flex-col sm:flex-row gap-4">
              <button 
                onClick={handleDemoClick}
                className="text-lg px-8 py-4 rounded-lg font-semibold transition-all group hover:opacity-90"
                style={ctaButtonStyle}
              >
                {/* Dynamic icon based on CTA variant */}
                {ctaConfig.text.includes('Demo') && <Mic className="w-5 h-5 mr-2 voice-indicator" />}
                {ctaConfig.text.includes('Started') && <Rocket className="w-5 h-5 mr-2" />}
                {ctaConfig.text.includes('Risk-Free') && <Users className="w-5 h-5 mr-2" />}
                {ctaConfig.text.includes('ROI') && <Calculator className="w-5 h-5 mr-2" />}
                {ctaConfig.text.includes('Join') && <Users className="w-5 h-5 mr-2" />}
                
                {ctaConfig.text}
                <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </button>
              
              <button 
                onClick={handleROIClick}
                className="btn btn-secondary text-lg px-8 py-4 bg-gradient-to-r from-green-600/10 to-blue-600/10 border-green-500/20 hover:from-green-600/20 hover:to-blue-600/20"
              >
                <TrendingUp className="w-5 h-5 mr-2" />
                Calculate Your ROI
              </button>
            </div>

            {/* Risk Reversal */}
            <p className="text-sm text-muted-foreground mt-4">
              No credit card required • 14-day free trial • Setup in minutes
            </p>
          </motion.div>

          {/* Demo Visualization */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="relative"
            onViewportEnter={() => {
              track('hero_demo_viewed', {
                experiment_headline: headlineVariant?.id,
                experiment_cta: ctaVariant?.id
              })
            }}
          >
            <div className="card p-8">
              {/* Voice Interaction Mockup */}
              <div className="space-y-4">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 bg-foreground rounded-full flex items-center justify-center">
                    <Mic className="w-6 h-6 text-background" />
                  </div>
                  <div>
                    <div className="font-semibold">Seiketsu AI Agent</div>
                    <div className="text-sm text-muted-foreground">Active • Qualifying leads</div>
                  </div>
                </div>

                {/* Conversation Preview */}
                <div className="space-y-3">
                  <div className="bg-muted p-3 rounded-lg">
                    <div className="text-sm font-medium mb-1">Prospect</div>
                    <div className="text-sm">"I'm looking for a 3-bedroom house under $500k"</div>
                  </div>
                  
                  <div className="bg-accent p-3 rounded-lg">
                    <div className="text-sm font-medium mb-1">AI Agent</div>
                    <div className="text-sm">"Great! I can help you find that. What area are you focusing on, and when are you looking to move?"</div>
                  </div>
                </div>

                {/* Live Status Indicators */}
                <div className="flex items-center justify-between pt-4 border-t border-border">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-sm">Qualifying lead...</span>
                  </div>
                  <div className="flex items-center gap-1 text-sm text-muted-foreground">
                    <Clock className="w-4 h-4" />
                    <span>2:34</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Floating Stats */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.8 }}
              className="absolute -bottom-4 -right-4 bg-background border border-border rounded-lg p-4 shadow-lg"
            >
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-600" />
                <div>
                  <div className="text-sm font-semibold">Lead Quality Score</div>
                  <div className="text-2xl font-bold text-green-600">92%</div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}