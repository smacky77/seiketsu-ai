'use client'

import { useState } from 'react'

// Property filters based on client decision-making patterns
export default function PropertyFilters() {
  const [filters, setFilters] = useState({
    priceRange: [450000, 600000],
    bedrooms: '2+',
    bathrooms: '2+',
    propertyType: 'condo',
    neighborhoods: ['Capitol Hill', 'Belltown'],
    amenities: ['parking', 'laundry', 'pet-friendly']
  })
  
  const [isExpanded, setIsExpanded] = useState(true)
  
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium text-foreground">Filters</h3>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          {isExpanded ? 'Hide' : 'Show'}
        </button>
      </div>
      
      {isExpanded && (
        <div className="space-y-6">
          {/* Price Range */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Price Range
            </label>
            <div className="space-y-2">
              <div className="flex items-center space-x-2 text-sm">
                <span>$450K</span>
                <div className="flex-1 bg-muted rounded-full h-2 relative">
                  <div className="bg-foreground rounded-full h-2 w-3/4"></div>
                </div>
                <span>$600K</span>
              </div>
              <div className="text-xs text-muted-foreground">
                $450,000 - $600,000
              </div>
            </div>
          </div>
          
          {/* Bedrooms */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Bedrooms
            </label>
            <div className="grid grid-cols-4 gap-2">
              {['1+', '2+', '3+', '4+'].map((option) => (
                <button
                  key={option}
                  className={`p-2 text-sm rounded border transition-colors ${
                    filters.bedrooms === option
                      ? 'border-foreground bg-accent text-accent-foreground'
                      : 'border-border text-muted-foreground hover:border-muted-foreground'
                  }`}
                >
                  {option}
                </button>
              ))}
            </div>
          </div>
          
          {/* Property Type */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Property Type
            </label>
            <div className="space-y-2">
              {['condo', 'townhouse', 'house', 'apartment'].map((type) => (
                <label key={type} className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name="propertyType"
                    value={type}
                    checked={filters.propertyType === type}
                    className="text-foreground"
                  />
                  <span className="text-sm capitalize">{type}</span>
                </label>
              ))}
            </div>
          </div>
          
          {/* Neighborhoods */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Preferred Areas
            </label>
            <div className="space-y-2">
              {['Capitol Hill', 'Belltown', 'South Lake Union', 'Fremont', 'Wallingford'].map((area) => (
                <label key={area} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={filters.neighborhoods.includes(area)}
                    className="text-foreground"
                  />
                  <span className="text-sm">{area}</span>
                </label>
              ))}
            </div>
          </div>
          
          {/* Must-Have Amenities */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Must-Have Features
            </label>
            <div className="space-y-2">
              {[
                { id: 'parking', label: 'Parking' },
                { id: 'laundry', label: 'In-unit laundry' },
                { id: 'pet-friendly', label: 'Pet-friendly' },
                { id: 'gym', label: 'Gym/Fitness' },
                { id: 'balcony', label: 'Balcony/Patio' }
              ].map((amenity) => (
                <label key={amenity.id} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={filters.amenities.includes(amenity.id)}
                    className="text-foreground"
                  />
                  <span className="text-sm">{amenity.label}</span>
                </label>
              ))}
            </div>
          </div>
          
          {/* Actions */}
          <div className="pt-4 border-t border-border space-y-2">
            <button className="w-full btn btn-primary text-sm">
              Apply Filters
            </button>
            <button className="w-full btn btn-ghost text-sm">
              Reset All
            </button>
          </div>
        </div>
      )}
    </div>
  )
}