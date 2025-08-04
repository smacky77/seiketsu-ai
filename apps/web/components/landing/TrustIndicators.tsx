'use client'

import { motion } from 'framer-motion'
import { Shield, Award, Star, CheckCircle, Users, Clock } from 'lucide-react'

export default function TrustIndicators() {
  const testimonials = [
    {
      quote: "Seiketsu AI increased our qualified leads by 300% in the first month. The voice agent never sleeps and never misses a call.",
      author: "Sarah Chen",
      role: "Broker Owner",
      company: "Pacific Realty Group"
    },
    {
      quote: "Our agents now focus on closing deals instead of qualifying leads. It's like having a team of assistants working 24/7.",
      author: "Michael Rodriguez", 
      role: "Team Leader",
      company: "Metro Home Solutions"
    },
    {
      quote: "The ROI was immediate. We're capturing leads we would have lost and qualifying them before we even know they exist.",
      author: "Jennifer Walsh",
      role: "Real Estate Agent",
      company: "Coldwell Banker"
    }
  ]

  const certifications = [
    {
      icon: Shield,
      title: "SOC 2 Compliant",
      description: "Enterprise-grade security"
    },
    {
      icon: Award,
      title: "Real Estate Tech",
      description: "2024 Innovation Award"
    },
    {
      icon: CheckCircle,
      title: "GDPR Compliant",
      description: "Data privacy certified"
    }
  ]

  const stats = [
    {
      icon: Users,
      number: "500+",
      label: "Active Agents"
    },
    {
      icon: Clock,
      number: "24/7",
      label: "Uptime"
    },
    {
      icon: Star,
      number: "4.9/5",
      label: "Customer Rating"
    }
  ]

  return (
    <section className="py-20 bg-muted/30">
      <div className="max-w-7xl mx-auto px-6">
        {/* Trust Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl font-bold mb-4">
            Trusted by Real Estate Professionals
          </h2>
          <p className="text-xl text-muted-foreground text-balance max-w-3xl mx-auto">
            Join hundreds of agents and brokers who have transformed their lead qualification 
            process with voice AI technology.
          </p>
        </motion.div>

        {/* Key Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          viewport={{ once: true }}
          className="grid grid-cols-3 gap-8 mb-16"
        >
          {stats.map((stat, index) => {
            const Icon = stat.icon
            return (
              <div key={index} className="text-center">
                <div className="flex justify-center mb-4">
                  <Icon className="w-8 h-8 text-foreground" />
                </div>
                <div className="text-3xl font-bold mb-2">{stat.number}</div>
                <div className="text-muted-foreground">{stat.label}</div>
              </div>
            )
          })}
        </motion.div>

        {/* Customer Testimonials */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          viewport={{ once: true }}
          className="grid lg:grid-cols-3 gap-8 mb-16"
        >
          {testimonials.map((testimonial, index) => (
            <div key={index} className="card p-6">
              <div className="flex items-center gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-current text-foreground" />
                ))}
              </div>
              <blockquote className="text-sm mb-4 text-balance">
                "{testimonial.quote}"
              </blockquote>
              <div className="border-t border-border pt-4">
                <div className="font-semibold text-sm">{testimonial.author}</div>
                <div className="text-sm text-muted-foreground">{testimonial.role}</div>
                <div className="text-sm text-muted-foreground">{testimonial.company}</div>
              </div>
            </div>
          ))}
        </motion.div>

        {/* Security & Compliance */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          viewport={{ once: true }}
          className="border-t border-border pt-16"
        >
          <div className="text-center mb-12">
            <h3 className="text-2xl font-bold mb-4">
              Enterprise-Grade Security & Compliance
            </h3>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Your client data and conversations are protected with the highest standards 
              of security and privacy compliance.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {certifications.map((cert, index) => {
              const Icon = cert.icon
              return (
                <div key={index} className="text-center">
                  <div className="flex justify-center mb-4">
                    <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center">
                      <Icon className="w-8 h-8" />
                    </div>
                  </div>
                  <h4 className="font-semibold mb-2">{cert.title}</h4>
                  <p className="text-sm text-muted-foreground">{cert.description}</p>
                </div>
              )
            })}
          </div>
        </motion.div>

        {/* Industry Recognition */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          viewport={{ once: true }}
          className="text-center mt-16"
        >
          <p className="text-sm text-muted-foreground mb-6">
            As featured in:
          </p>
          <div className="flex justify-center items-center gap-12 opacity-60">
            {/* Placeholder for industry publication logos */}
            <div className="text-lg font-semibold">TechCrunch</div>
            <div className="text-lg font-semibold">Real Estate News</div>
            <div className="text-lg font-semibold">PropTech Today</div>
            <div className="text-lg font-semibold">Inman</div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}