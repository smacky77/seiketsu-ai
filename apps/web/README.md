# Seiketsu AI - Frontend Application

Voice-first real estate intelligence platform landing page built with Next.js 14, TypeScript, and Tailwind CSS.

## Overview

This is the frontend implementation of the Seiketsu AI landing page, designed following UX research and conversion optimization principles. The application uses a clean, monochromatic design system inspired by Vercel's design philosophy.

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with OKLCH color system
- **Animations**: Framer Motion
- **Icons**: Lucide React

## Design System

### Color Palette (OKLCH Monochromatic)
- `background`: Pure white (oklch(100% 0 0))
- `foreground`: Pure black (oklch(0% 0 0))
- `muted`: Light gray (oklch(96% 0 0))
- `border`: Border gray (oklch(85% 0 0))

### Typography
- **Primary**: Inter (400, 500, 600, 700)
- **Mono**: JetBrains Mono (400, 500, 600)

## Components

### Landing Page Sections
- `HeroSection` - Conversion-optimized hero with voice demo
- `TrustIndicators` - Social proof and testimonials
- `FeatureShowcase` - Problem/solution showcase
- `PricingSection` - Transparent pricing with ROI calculator
- `ConversionForm` - Progressive lead qualification form

### Layout Components
- `Navigation` - Responsive header with voice-themed branding
- `Footer` - Comprehensive footer with links and contact info

## Getting Started

### Installation
```bash
npm install
```

### Development
```bash
npm run dev
```

### Build
```bash
npm run build
```

### Production
```bash
npm run start
```

## UX Implementation

The landing page is built according to UX research findings:

1. **5-Second Rule**: Clear value proposition in hero section
2. **Trust Building**: Security badges, testimonials, and metrics
3. **Conversion Optimization**: Multiple CTAs with risk reversal
4. **Mobile-First**: Responsive design with touch-friendly interactions
5. **Voice-First Messaging**: Voice command indicators throughout

## Performance

- **First Contentful Paint**: < 1.5s target
- **Bundle Size**: Optimized with Next.js automatic code splitting
- **Accessibility**: WCAG 2.1 AA compliant
- **SEO**: Optimized meta tags and structured data

## File Structure

```
apps/web/
├── app/
│   ├── globals.css          # Global styles and design system
│   ├── layout.tsx           # Root layout with SEO
│   └── page.tsx             # Main landing page
├── components/
│   ├── landing/             # Landing page sections
│   └── layout/              # Layout components
└── public/                  # Static assets
```

## Deployment

The application is ready for deployment on Vercel, Netlify, or any platform supporting Next.js applications.

## License

Private - Seiketsu AI Platform