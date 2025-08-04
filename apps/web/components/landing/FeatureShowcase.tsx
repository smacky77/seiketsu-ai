'use client'

import { motion } from 'framer-motion'
import { Mic, Brain, Calendar, Users, BarChart3, MessageSquare, Clock, Target, Zap } from 'lucide-react'

export default function FeatureShowcase() {
  const problems = [
    {
      title: "Missing Leads After Hours",
      description: "Prospects call outside business hours and you lose them to competitors",
      impact: "40% of leads lost"
    },
    {
      title: "Unqualified Lead Waste",
      description: "Agents spend hours on prospects who aren't ready to buy or sell",
      impact: "60% time waste"
    },
    {
      title: "Inconsistent Follow-up",
      description: "Manual processes lead to missed opportunities and poor client experience",
      impact: "30% conversion loss"
    }
  ]

  const solutions = [
    {
      icon: Mic,
      title: "24/7 Voice Intelligence",
      description: "Never miss a lead again with AI that answers calls, texts, and web inquiries around the clock",
      benefits: [
        "Instant response to all inquiries",
        "Natural conversation experience", 
        "Multi-channel communication"
      ]
    },
    {
      icon: Brain,
      title: "Smart Lead Qualification",
      description: "AI evaluates prospects using your criteria and scores them for immediate follow-up priority",
      benefits: [
        "Custom qualification criteria",
        "Real-time scoring and routing",
        "Detailed prospect insights"
      ]
    },
    {
      icon: Calendar,
      title: "Intelligent Scheduling",
      description: "Seamlessly book appointments based on agent availability and prospect preferences",
      benefits: [
        "Calendar integration",
        "Automated reminders",
        "Conflict resolution"
      ]
    }
  ]

  const workflow = [
    {
      step: "1",
      title: "Prospect Inquiry",
      description: "Voice, text, or web inquiry received",
      icon: MessageSquare
    },
    {
      step: "2", 
      title: "AI Engagement",
      description: "Natural conversation to understand needs",
      icon: Brain
    },
    {
      step: "3",
      title: "Qualification & Scoring",
      description: "Automated assessment and priority scoring",
      icon: Target
    },
    {
      step: "4",
      title: "Agent Handoff",
      description: "Qualified leads delivered with full context",
      icon: Users
    }
  ]

  return (
    <section className="py-20">
      <div className="max-w-7xl mx-auto px-6">
        {/* Problem Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl lg:text-4xl font-bold mb-6">
            Stop Losing Leads to
            <span className="block text-muted-foreground">Manual Processes</span>
          </h2>
          <p className="text-xl text-muted-foreground text-balance max-w-3xl mx-auto">
            Real estate professionals lose thousands in commission every month due to 
            inefficient lead qualification and after-hours missed opportunities.
          </p>
        </motion.div>

        {/* Problem Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          viewport={{ once: true }}
          className="grid lg:grid-cols-3 gap-8 mb-20"
        >
          {problems.map((problem, index) => (
            <div key={index} className="text-center">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <div className="w-8 h-8 bg-red-500 rounded-full"></div>
              </div>
              <h3 className="font-semibold mb-3">{problem.title}</h3>
              <p className="text-sm text-muted-foreground mb-3">{problem.description}</p>
              <div className="text-sm font-semibold text-red-600">{problem.impact}</div>
            </div>
          ))}
        </motion.div>

        {/* Solution Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl lg:text-4xl font-bold mb-6">
            Voice AI That Works
            <span className="block text-muted-foreground">Like Your Best Agent</span>
          </h2>
          <p className="text-xl text-muted-foreground text-balance max-w-3xl mx-auto">
            Our AI understands real estate conversations, qualifies prospects with precision, 
            and ensures you only spend time on qualified opportunities.
          </p>
        </motion.div>

        {/* Feature Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          viewport={{ once: true }}
          className="grid lg:grid-cols-3 gap-8 mb-20"
        >
          {solutions.map((solution, index) => {
            const Icon = solution.icon
            return (
              <div key={index} className="card p-8">
                <div className="w-12 h-12 bg-foreground rounded-lg flex items-center justify-center mb-6">
                  <Icon className="w-6 h-6 text-background" />
                </div>
                <h3 className="text-xl font-semibold mb-4">{solution.title}</h3>
                <p className="text-muted-foreground mb-6">{solution.description}</p>
                <ul className="space-y-2">
                  {solution.benefits.map((benefit, benefitIndex) => (
                    <li key={benefitIndex} className="flex items-center gap-2 text-sm">
                      <div className="w-1.5 h-1.5 bg-foreground rounded-full"></div>
                      <span>{benefit}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )
          })}
        </motion.div>

        {/* How It Works */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          viewport={{ once: true }}
          className="bg-muted/30 rounded-2xl p-8 lg:p-12"
        >
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">How It Works</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              From first contact to qualified handoff in minutes, not hours.
            </p>
          </div>

          <div className="grid lg:grid-cols-4 gap-8">
            {workflow.map((step, index) => {
              const Icon = step.icon
              return (
                <div key={index} className="text-center relative">
                  {/* Connection Line */}
                  {index < workflow.length - 1 && (
                    <div className="hidden lg:block absolute top-12 left-full w-full h-0.5 bg-border -translate-x-1/2 z-0"></div>
                  )}
                  
                  {/* Step Content */}
                  <div className="relative z-10">
                    <div className="w-24 h-24 bg-foreground rounded-full flex items-center justify-center mx-auto mb-4">
                      <Icon className="w-8 h-8 text-background" />
                    </div>
                    <div className="text-sm font-semibold text-muted-foreground mb-2">
                      Step {step.step}
                    </div>
                    <h3 className="font-semibold mb-2">{step.title}</h3>
                    <p className="text-sm text-muted-foreground">{step.description}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </motion.div>

        {/* ROI Preview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.0 }}
          viewport={{ once: true }}
          className="grid lg:grid-cols-2 gap-12 items-center mt-20"
        >
          <div>
            <h2 className="text-3xl font-bold mb-6">
              Measurable Results From Day One
            </h2>
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <div className="font-semibold">3x More Qualified Leads</div>
                  <div className="text-sm text-muted-foreground">Better qualification means higher conversion rates</div>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Clock className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <div className="font-semibold">80% Time Savings</div>
                  <div className="text-sm text-muted-foreground">Focus on closing deals, not screening calls</div>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Zap className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <div className="font-semibold">24/7 Lead Capture</div>
                  <div className="text-sm text-muted-foreground">Never miss another opportunity</div>
                </div>
              </div>
            </div>
          </div>

          <div className="card p-8">
            <h3 className="text-xl font-semibold mb-6">ROI Calculator</h3>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Current leads/month:</span>
                <span className="font-semibold">50</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Current conversion:</span>
                <span className="font-semibold">15%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">With Seiketsu AI:</span>
                <span className="font-semibold text-green-600">45%</span>
              </div>
              <div className="border-t border-border pt-4">
                <div className="flex justify-between text-lg font-semibold">
                  <span>Additional closings/month:</span>
                  <span className="text-green-600">+15</span>
                </div>
                <div className="text-sm text-muted-foreground mt-1">
                  Based on $6,000 avg commission
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}