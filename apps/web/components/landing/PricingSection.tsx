'use client'

import { motion } from 'framer-motion'
import { Check, Mic, Users, Building, ArrowRight, Star } from 'lucide-react'

export default function PricingSection() {
  const plans = [
    {
      name: 'Starter',
      price: '$97',
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
      price: '$197',
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
      price: 'Custom',
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

  const faqs = [
    {
      question: 'How quickly can I get started?',
      answer: 'Most agents are up and running within 15 minutes. Our setup wizard guides you through voice training, calendar integration, and basic configuration.'
    },
    {
      question: 'Do I need technical knowledge?',
      answer: 'No technical knowledge required. Our voice agent works out of the box with intelligent defaults, and our support team helps with any customization.'
    },
    {
      question: 'Can I cancel anytime?',
      answer: 'Yes, you can cancel your subscription at any time. There are no long-term contracts or cancellation fees.'
    },
    {
      question: 'How accurate is the voice recognition?',
      answer: 'Our AI achieves 95%+ accuracy in real estate conversations. It continuously learns and improves based on your specific use cases.'
    }
  ]

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
        </motion.div>

        {/* Pricing Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          viewport={{ once: true }}
          className="grid lg:grid-cols-3 gap-8 mb-16"
        >
          {plans.map((plan, index) => {
            const Icon = plan.icon
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
                  <div className="flex items-baseline justify-center gap-1">
                    <span className="text-4xl font-bold">{plan.price}</span>
                    <span className="text-muted-foreground">{plan.period}</span>
                  </div>
                </div>

                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-center gap-3">
                      <Check className="w-5 h-5 text-green-600 shrink-0" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
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
          })}
        </motion.div>

        {/* ROI Calculator */}
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
            <button className="btn btn-primary text-lg group">
              Get Your Custom ROI Report
              <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </motion.div>

        {/* FAQ Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          viewport={{ once: true }}
        >
          <div className="text-center mb-12">
            <h3 className="text-2xl font-bold mb-4">Frequently Asked Questions</h3>
            <p className="text-muted-foreground">
              Everything you need to know about getting started with voice AI
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {faqs.map((faq, index) => (
              <div key={index} className="space-y-3">
                <h4 className="font-semibold">{faq.question}</h4>
                <p className="text-sm text-muted-foreground">{faq.answer}</p>
              </div>
            ))}
          </div>
        </motion.div>

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
            <button className="btn btn-primary text-lg px-8 py-4 group">
              <Mic className="w-5 h-5 mr-2 voice-indicator" />
              Start Free Trial
              <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
            </button>
            <button className="btn btn-secondary text-lg px-8 py-4">
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