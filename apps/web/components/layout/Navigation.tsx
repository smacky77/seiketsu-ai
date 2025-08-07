'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Menu, X, Mic, ArrowRight } from 'lucide-react'

export default function Navigation() {
  const [isOpen, setIsOpen] = useState(false)

  const navigation = [
    { name: 'How It Works', href: '#how-it-works' },
    { name: 'Features', href: '#features' },
    { name: 'ROI Calculator', href: '/roi-calculator', special: true },
    { name: 'Pricing', href: '#pricing' },
    { name: 'Demo', href: '#demo' },
  ]

  return (
    <nav className="sticky top-0 z-50 bg-background/80 backdrop-blur-lg border-b border-border">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-foreground rounded-lg flex items-center justify-center">
              <Mic className="w-5 h-5 text-background" />
            </div>
            <span className="text-xl font-bold">Seiketsu AI</span>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {navigation.map((item) => (
              <a
                key={item.name}
                href={item.href}
                className={`transition-colors ${
                  item.special 
                    ? 'bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent font-semibold hover:from-green-700 hover:to-blue-700'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {item.name}
              </a>
            ))}
          </div>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center gap-4">
            <button className="btn btn-ghost">
              Sign In
            </button>
            <button className="btn btn-primary group">
              <Mic className="w-4 h-4 mr-2 voice-indicator" />
              Start Free Trial
              <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden p-2"
          >
            {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden border-t border-border"
          >
            <div className="py-4 space-y-4">
              {navigation.map((item) => (
                <a
                  key={item.name}
                  href={item.href}
                  className={`block transition-colors ${
                    item.special 
                      ? 'bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent font-semibold'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                  onClick={() => setIsOpen(false)}
                >
                  {item.name}
                </a>
              ))}
              <div className="pt-4 border-t border-border space-y-2">
                <button className="w-full btn btn-ghost">
                  Sign In
                </button>
                <button className="w-full btn btn-primary group">
                  <Mic className="w-4 h-4 mr-2 voice-indicator" />
                  Start Free Trial
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </nav>
  )
}