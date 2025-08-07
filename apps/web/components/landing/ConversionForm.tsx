'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowRight, Check, Mic, Calendar, Star, Users } from 'lucide-react'

export default function ConversionForm() {
  const [formStep, setFormStep] = useState(1)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    role: '',
    leadsPerMonth: '',
    currentChallenges: []
  })

  const handleInputChange = (field: string, value: string | string[]) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleNext = () => {
    if (formStep < 3) {
      setFormStep(formStep + 1)
    }
  }

  const handleSubmit = () => {
    // Handle form submission
    try {
      // Process form data here
      // In production, this would send data to API
      setFormStep(4) // Success step
    } catch (error) {
      // Handle submission error
      setFormStep(3) // Stay on current step
    }
  }

  const challenges = [
    'Missing after-hours leads',
    'Unqualified prospects',
    'Time spent on screening',
    'Inconsistent follow-up',
    'Low conversion rates'
  ]

  const leadVolumes = [
    '1-10 leads/month',
    '11-25 leads/month', 
    '26-50 leads/month',
    '51-100 leads/month',
    '100+ leads/month'
  ]

  const benefits = [
    {
      icon: Mic,
      title: "Voice Demo",
      description: "Experience real AI conversations"
    },
    {
      icon: Calendar,
      title: "Custom Setup",
      description: "Tailored to your business needs"
    },
    {
      icon: Star,
      title: "Expert Support",
      description: "White-glove onboarding included"
    }
  ]

  return (
    <section className="py-20 bg-muted/30">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Left Side - Value Proposition */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl lg:text-4xl font-bold mb-6">
              Start Qualifying Leads
              <span className="block text-muted-foreground">In The Next 15 Minutes</span>
            </h2>
            
            <p className="text-xl text-muted-foreground mb-8">
              Join 500+ real estate professionals who transformed their lead qualification 
              process with voice AI technology.
            </p>

            {/* Benefits */}
            <div className="space-y-6 mb-8">
              {benefits.map((benefit, index) => {
                const Icon = benefit.icon
                return (
                  <div key={index} className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-foreground rounded-lg flex items-center justify-center shrink-0">
                      <Icon className="w-6 h-6 text-background" />
                    </div>
                    <div>
                      <h3 className="font-semibold mb-1">{benefit.title}</h3>
                      <p className="text-sm text-muted-foreground">{benefit.description}</p>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Social Proof */}
            <div className="border border-border rounded-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                <Users className="w-6 h-6" />
                <span className="font-semibold">Join 500+ Active Users</span>
              </div>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold">95%</div>
                  <div className="text-sm text-muted-foreground">Lead Quality</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">3x</div>
                  <div className="text-sm text-muted-foreground">More Qualified</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">24/7</div>
                  <div className="text-sm text-muted-foreground">Availability</div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Right Side - Multi-Step Form */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            viewport={{ once: true }}
            className="card p-8"
          >
            {/* Progress Indicator */}
            <div className="flex items-center justify-between mb-8">
              {[1, 2, 3].map((step) => (
                <div key={step} className="flex items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                    formStep >= step ? 'bg-foreground text-background' : 'bg-muted text-muted-foreground'
                  }`}>
                    {formStep > step ? <Check className="w-4 h-4" /> : step}
                  </div>
                  {step < 3 && (
                    <div className={`w-12 h-0.5 mx-2 ${
                      formStep > step ? 'bg-foreground' : 'bg-muted'
                    }`} />
                  )}
                </div>
              ))}
            </div>

            {/* Form Steps */}
            {formStep === 1 && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-xl font-semibold mb-2">Get Your Free Demo</h3>
                  <p className="text-muted-foreground">Tell us about yourself</p>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Full Name *</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      className="w-full px-4 py-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-foreground"
                      placeholder="Enter your full name"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-2">Email Address *</label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      className="w-full px-4 py-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-foreground"
                      placeholder="your@email.com"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-2">Phone Number *</label>
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      className="w-full px-4 py-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-foreground"
                      placeholder="(555) 123-4567"
                    />
                  </div>
                </div>

                <button
                  onClick={handleNext}
                  disabled={!formData.name || !formData.email || !formData.phone}
                  className="w-full btn btn-primary py-3 text-lg group disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Continue
                  <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            )}

            {formStep === 2 && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-xl font-semibold mb-2">About Your Business</h3>
                  <p className="text-muted-foreground">Help us customize your experience</p>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Company/Brokerage</label>
                    <input
                      type="text"
                      value={formData.company}
                      onChange={(e) => handleInputChange('company', e.target.value)}
                      className="w-full px-4 py-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-foreground"
                      placeholder="Your brokerage name"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-2">Role</label>
                    <select
                      value={formData.role}
                      onChange={(e) => handleInputChange('role', e.target.value)}
                      className="w-full px-4 py-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-foreground"
                    >
                      <option value="">Select your role</option>
                      <option value="agent">Real Estate Agent</option>
                      <option value="broker">Broker</option>
                      <option value="team-leader">Team Leader</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-2">Current Lead Volume</label>
                    <div className="space-y-2">
                      {leadVolumes.map((volume) => (
                        <label key={volume} className="flex items-center gap-3 cursor-pointer">
                          <input
                            type="radio"
                            name="leadVolume"
                            value={volume}
                            onChange={(e) => handleInputChange('leadsPerMonth', e.target.value)}
                            className="w-4 h-4"
                          />
                          <span className="text-sm">{volume}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleNext}
                  className="w-full btn btn-primary py-3 text-lg group"
                >
                  Continue
                  <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            )}

            {formStep === 3 && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-xl font-semibold mb-2">Current Challenges</h3>
                  <p className="text-muted-foreground">What's your biggest pain point? (Select all that apply)</p>
                </div>
                
                <div className="space-y-3">
                  {challenges.map((challenge) => (
                    <label key={challenge} className="flex items-center gap-3 cursor-pointer p-3 border border-border rounded-lg hover:bg-muted/30">
                      <input
                        type="checkbox"
                        value={challenge}
                        onChange={(e) => {
                          const currentChallenges = formData.currentChallenges
                          if (e.target.checked) {
                            handleInputChange('currentChallenges', [...currentChallenges, challenge])
                          } else {
                            handleInputChange('currentChallenges', currentChallenges.filter(c => c !== challenge))
                          }
                        }}
                        className="w-4 h-4"
                      />
                      <span className="text-sm">{challenge}</span>
                    </label>
                  ))}
                </div>

                <button
                  onClick={handleSubmit}
                  className="w-full btn btn-primary py-3 text-lg group"
                >
                  Get My Free Demo
                  <Mic className="w-5 h-5 ml-2 voice-indicator" />
                </button>
                
                <p className="text-xs text-muted-foreground text-center">
                  No credit card required • Setup in 15 minutes • Cancel anytime
                </p>
              </div>
            )}

            {formStep === 4 && (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Check className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-xl font-semibold mb-4">Demo Scheduled!</h3>
                <p className="text-muted-foreground mb-6">
                  We'll send you a demo link and calendar invite within the next 5 minutes.
                </p>
                <div className="bg-muted rounded-lg p-4">
                  <p className="text-sm">
                    <strong>Next Steps:</strong> Check your email for the demo link and prepare 
                    to experience how voice AI can transform your lead qualification process.
                  </p>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </section>
  )
}