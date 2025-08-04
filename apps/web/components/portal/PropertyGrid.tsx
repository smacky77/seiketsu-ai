'use client'

import { useState } from 'react'

// Property grid optimized for client decision-making
interface Property {
  id: string
  address: string
  price: number
  bedrooms: number
  bathrooms: number
  sqft: number
  neighborhood: string
  image: string
  daysOnMarket: number
  saved: boolean
  viewed: boolean
}

const mockProperties: Property[] = [
  {
    id: '1',
    address: '1234 Pine St #304',
    price: 575000,
    bedrooms: 2,
    bathrooms: 2,
    sqft: 1200,
    neighborhood: 'Capitol Hill',
    image: '/api/placeholder/400/250',
    daysOnMarket: 18,
    saved: true,
    viewed: true
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
    daysOnMarket: 13,
    saved: false,
    viewed: false
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
    daysOnMarket: 8,
    saved: true,
    viewed: false
  },
  // Add more mock properties
  {
    id: '4',
    address: '3456 Fremont Ave #101',
    price: 485000,
    bedrooms: 2,
    bathrooms: 1,
    sqft: 950,
    neighborhood: 'Fremont',
    image: '/api/placeholder/400/250',
    daysOnMarket: 25,
    saved: false,
    viewed: false
  }
]

export default function PropertyGrid({ viewMode, sortBy }: { viewMode: 'grid' | 'list', sortBy: string }) {
  const [properties, setProperties] = useState(mockProperties)
  
  const toggleSaved = (id: string) => {
    setProperties(props => 
      props.map(prop => 
        prop.id === id ? { ...prop, saved: !prop.saved } : prop
      )
    )
  }
  
  const markViewed = (id: string) => {
    setProperties(props => 
      props.map(prop => 
        prop.id === id ? { ...prop, viewed: true } : prop
      )
    )
  }
  
  if (viewMode === 'list') {
    return (
      <div className="space-y-4">
        <div className="text-sm text-muted-foreground">
          {properties.length} properties found
        </div>
        
        {properties.map((property) => (
          <div key={property.id} className="bg-card border border-border rounded-lg p-4">
            <div className="flex space-x-4">
              {/* Property image */}
              <div className="w-32 h-24 bg-accent rounded flex-shrink-0 relative">
                {property.saved && (
                  <div className="absolute top-1 right-1 text-red-500">♥️</div>
                )}
                {property.viewed && (
                  <div className="absolute top-1 left-1 text-xs bg-background bg-opacity-90 px-1 rounded">
                    Viewed
                  </div>
                )}
              </div>
              
              {/* Property details */}
              <div className="flex-1">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="font-medium text-foreground">{property.address}</div>
                    <div className="text-sm text-muted-foreground">{property.neighborhood}</div>
                  </div>
                  <div className="text-lg font-bold text-foreground">
                    ${property.price.toLocaleString()}
                  </div>
                </div>
                
                <div className="flex items-center space-x-4 text-sm text-muted-foreground mb-3">
                  <span>🛏️ {property.bedrooms} bed</span>
                  <span>🛁 {property.bathrooms} bath</span>
                  <span>📏 {property.sqft.toLocaleString()} sqft</span>
                  <span>⏱️ {property.daysOnMarket} days</span>
                </div>
                
                <div className="flex space-x-2">
                  <button 
                    onClick={() => markViewed(property.id)}
                    className="btn btn-primary text-sm"
                  >
                    View Details
                  </button>
                  <button className="btn btn-secondary text-sm">
                    Schedule Tour
                  </button>
                  <button 
                    onClick={() => toggleSaved(property.id)}
                    className={`btn text-sm ${
                      property.saved ? 'btn-primary' : 'btn-ghost'
                    }`}
                  >
                    {property.saved ? '♥️ Saved' : '♡ Save'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }
  
  return (
    <div className="space-y-4">
      <div className="text-sm text-muted-foreground">
        {properties.length} properties found
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {properties.map((property) => (
          <div key={property.id} className="bg-card border border-border rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
            {/* Property image */}
            <div className="aspect-video bg-accent relative">
              {property.saved && (
                <button 
                  onClick={() => toggleSaved(property.id)}
                  className="absolute top-2 right-2 text-red-500 text-xl z-10"
                >
                  ♥️
                </button>
              )}
              {property.viewed && (
                <div className="absolute top-2 left-2 bg-background bg-opacity-90 px-2 py-1 rounded text-xs">
                  Viewed
                </div>
              )}
              <div className="absolute bottom-2 right-2 bg-background bg-opacity-90 px-2 py-1 rounded text-xs">
                {property.daysOnMarket} days
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
              <div className="flex items-center justify-between text-sm text-muted-foreground mb-4">
                <span>🛏️ {property.bedrooms}</span>
                <span>🛁 {property.bathrooms}</span>
                <span>📏 {property.sqft.toLocaleString()}</span>
              </div>
              
              {/* Actions */}
              <div className="space-y-2">
                <button 
                  onClick={() => markViewed(property.id)}
                  className="w-full btn btn-primary text-sm"
                >
                  View Details
                </button>
                <div className="flex space-x-2">
                  <button className="flex-1 btn btn-secondary text-sm">
                    Schedule Tour
                  </button>
                  <button 
                    onClick={() => toggleSaved(property.id)}
                    className={`btn text-sm px-3 ${
                      property.saved ? 'btn-primary' : 'btn-ghost'
                    }`}
                  >
                    {property.saved ? '♥️' : '♡'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}