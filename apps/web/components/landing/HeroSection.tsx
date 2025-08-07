'use client'

import { useState } from 'react'
import { Mic, Play, ArrowRight, Users, Clock, TrendingUp } from 'lucide-react'
import { motion } from 'framer-motion'

export default function HeroSection() {
  const [isPlaying, setIsPlaying] = useState(false)

  const handleDemoClick = () => {
    setIsPlaying(!isPlaying)
    // Trigger voice demo - placeholder for actual implementation
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

            {/* Main Headline - 5-Second Rule Implementation */}
            <h1 className="text-4xl lg:text-6xl font-bold tracking-tight text-balance mb-6">
              Voice AI That
              <span className="block text-muted-foreground">Qualifies Leads</span>
              <span className="block">While You Sleep</span>
            </h1>

            {/* Value Proposition - Clear Problem/Solution */}
            <p className="text-xl text-muted-foreground text-balance mb-8 max-w-2xl">
              Stop missing opportunities. Our AI voice agent handles lead qualification, 
              property inquiries, and appointment scheduling 24/7 – so you only talk to 
              ready-to-buy prospects.
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

            {/* Primary CTA - Conversion Optimization */}
            <div className="flex flex-col sm:flex-row gap-4">
              <button 
                onClick={handleDemoClick}
                className="btn btn-primary text-lg px-8 py-4 group"
              >
                <Mic className="w-5 h-5 mr-2 voice-indicator" />
                Try Voice Demo
                <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </button>
              
              <a href="/roi-calculator" className="btn btn-secondary text-lg px-8 py-4 bg-gradient-to-r from-green-600/10 to-blue-600/10 border-green-500/20 hover:from-green-600/20 hover:to-blue-600/20">
                <TrendingUp className="w-5 h-5 mr-2" />
                Calculate Your ROI
              </a>
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