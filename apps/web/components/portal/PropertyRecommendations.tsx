'use client'

import { useState } from 'react'

// Property recommendations based on client decision-making research
interface PropertyRecommendation {
  id: string
  address: string
  price: number
  bedrooms: number
  bathrooms: number
  sqft: number
  neighborhood: string
  image: string
  matchScore: number
  matchReasons: string[]
  listingDate: string
  timeOnMarket: number
}

const mockProperties: PropertyRecommendation[] = [
  {
    id: '1',
    address: '1234 Pine St #304',
    price: 575000,
    bedrooms: 2,
    bathrooms: 2,
    sqft: 1200,
    neighborhood: 'Capitol Hill',
    image: '/api/placeholder/400/250',
    matchScore: 95,
    matchReasons: ['Perfect location match', 'Within budget', 'Has parking', 'Pet-friendly'],
    listingDate: '2024-01-15',
    timeOnMarket: 18
  },
  {
    id: '2',
    address: '5678 Bell St #507',
    price: 625000,
    bedrooms: 3,
    bathrooms: 2,
    sqft: 1400,
    neighborhood: 'Belltown',
    image: '/api/placeholder/400/250',
    matchScore: 88,
    matchReasons: ['Extra bedroom', 'In-unit laundry', 'Modern building'],
    listingDate: '2024-01-20',
    timeOnMarket: 13
  },
  {
    id: '3',
    address: '9012 Westlake Ave #212',
    price: 545000,
    bedrooms: 2,
    bathrooms: 2,
    sqft: 1100,
    neighborhood: 'South Lake Union',
    image: '/api/placeholder/400/250',
    matchScore: 82,
    matchReasons: ['Great value', 'Tech district', 'Easy commute'],
    listingDate: '2024-01-25',
    timeOnMarket: 8
  }
]

export default function PropertyRecommendations({ preferences }: { preferences: any }) {
  const [selectedProperty, setSelectedProperty] = useState<string | null>(null)
  
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-foreground">AI-Curated Recommendations</h2>
          <p className="text-sm text-muted-foreground">
            Properties matched to your preferences with explanation
          </p>
        </div>
        <button className="btn btn-secondary text-sm">
          Refine Search
        </button>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {mockProperties.map((property) => (
          <div
            key={property.id}
            className={`bg-muted rounded-lg overflow-hidden border transition-all duration-200 cursor-pointer ${
              selectedProperty === property.id
                ? 'border-foreground shadow-lg'
                : 'border-border hover:border-muted-foreground'
            }`}
            onClick={() => setSelectedProperty(
              selectedProperty === property.id ? null : property.id
            )}
          >
            {/* Property image placeholder */}
            <div className="aspect-video bg-accent relative">
              <div className="absolute top-2 right-2 bg-green-500 text-white px-2 py-1 rounded text-xs font-medium">
                {property.matchScore}% Match
              </div>
              <div className="absolute bottom-2 left-2 bg-background bg-opacity-90 px-2 py-1 rounded text-xs">
                {property.timeOnMarket} days on market
              </div>
            </div>
            
            <div className="p-4">
              {/* Property details */}
              <div className="mb-3">
                <div className="font-medium text-foreground mb-1">{property.address}</div>
                <div className="text-sm text-muted-foreground">{property.neighborhood}</div>
                <div className="text-lg font-bold text-foreground mt-2">
                  ${property.price.toLocaleString()}
                </div>
              </div>
              
              {/* Property specs */}
              <div className="flex items-center space-x-4 text-sm text-muted-foreground mb-3">
                <span>🛏️ {property.bedrooms} bed</span>
                <span>🛁 {property.bathrooms} bath</span>
                <span>📏 {property.sqft.toLocaleString()} sqft</span>
              </div>
              
              {/* Match reasons - transparency for decision-making */}
              <div className="space-y-1">
                <div className="text-xs font-medium text-foreground">Why this matches:</div>
                {property.matchReasons.slice(0, 3).map((reason, index) => (
                  <div key={index} className="text-xs text-muted-foreground flex items-center space-x-1">
                    <span className="w-1 h-1 bg-green-500 rounded-full"></span>
                    <span>{reason}</span>
                  </div>
                ))}
              </div>
              
              {/* Quick actions */}
              <div className="mt-4 flex space-x-2">
                <button className="btn btn-primary text-xs flex-1">
                  Schedule Viewing
                </button>
                <button className="btn btn-secondary text-xs px-3">
                  ♥️
                </button>
                <button className="btn btn-secondary text-xs px-3">
                  📷
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Load more properties */}
      <div className="mt-6 text-center">
        <button className="btn btn-ghost">
          View All Recommendations (47 total)
        </button>
      </div>
    </div>
  )
}