import Navigation from '@/components/layout/Navigation'
import Footer from '@/components/layout/Footer'
import HeroSection from '@/components/landing/HeroSection'
import TrustIndicators from '@/components/landing/TrustIndicators'
import FeatureShowcase from '@/components/landing/FeatureShowcase'
import PricingSection from '@/components/landing/PricingSection'
import ConversionForm from '@/components/landing/ConversionForm'

export default function HomePage() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <Navigation />
      
      {/* Hero Section - Conversion Optimization */}
      <HeroSection />
      
      {/* Trust Indicators - Enterprise Prospect Concerns */}
      <TrustIndicators />
      
      {/* Feature Showcase - User Value Priorities */}
      <section id="features">
        <FeatureShowcase />
      </section>
      
      {/* Pricing Section - Transparent Pricing */}
      <PricingSection />
      
      {/* Conversion Form - Lead Qualification UX Flow */}
      <section id="demo">
        <ConversionForm />
      </section>
      
      <Footer />
    </main>
  )
}