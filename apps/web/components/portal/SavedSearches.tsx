'use client'

import { useState } from 'react'

// Saved searches for quick access to client preferences
interface SavedSearch {
  id: string
  name: string
  criteria: {
    priceRange: string
    location: string
    bedrooms: string
    propertyType: string
  }
  resultCount: number
  lastUpdated: string
  newListings: number
}

const mockSavedSearches: SavedSearch[] = [
  {
    id: '1',
    name: 'Capitol Hill Condos',
    criteria: {
      priceRange: '$450K - $600K',
      location: 'Capitol Hill',
      bedrooms: '2+',
      propertyType: 'Condo'
    },
    resultCount: 23,
    lastUpdated: '2 hours ago',
    newListings: 3
  },
  {
    id: '2',
    name: 'Belltown 3BR',
    criteria: {
      priceRange: '$600K - $700K',
      location: 'Belltown',
      bedrooms: '3+',
      propertyType: 'Condo'
    },
    resultCount: 8,
    lastUpdated: '1 day ago',
    newListings: 1
  },
  {
    id: '3',
    name: 'Budget Options',
    criteria: {
      priceRange: '$400K - $500K',
      location: 'All areas',
      bedrooms: '2+',
      propertyType: 'Any'
    },
    resultCount: 47,
    lastUpdated: '3 hours ago',
    newListings: 5
  }
]

export default function SavedSearches() {
  const [searches, setSearches] = useState(mockSavedSearches)
  const [showCreateNew, setShowCreateNew] = useState(false)
  
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-foreground">Saved Searches</h2>
          <p className="text-sm text-muted-foreground">
            Quick access to your property preferences
          </p>
        </div>
        <button 
          onClick={() => setShowCreateNew(true)}
          className="btn btn-secondary text-sm"
        >
          + New Search
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {searches.map((search) => (
          <div key={search.id} className="bg-muted rounded-lg p-4 hover:bg-accent transition-colors cursor-pointer">
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="font-medium text-foreground">{search.name}</div>
                <div className="text-sm text-muted-foreground">
                  {search.resultCount} properties
                </div>
              </div>
              {search.newListings > 0 && (
                <span className="bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                  {search.newListings} new
                </span>
              )}
            </div>
            
            <div className="space-y-1 text-xs text-muted-foreground mb-3">
              <div>{search.criteria.priceRange}</div>
              <div>{search.criteria.location}</div>
              <div>{search.criteria.bedrooms} bedrooms • {search.criteria.propertyType}</div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="text-xs text-muted-foreground">
                Updated {search.lastUpdated}
              </div>
              <div className="flex space-x-1">
                <button className="text-xs text-muted-foreground hover:text-foreground">
                  ✏️
                </button>
                <button className="text-xs text-muted-foreground hover:text-foreground">
                  🔔
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Create new search modal */}
      {showCreateNew && (
        <div className="fixed inset-0 bg-background bg-opacity-90 flex items-center justify-center z-50">
          <div className="bg-card border border-border rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold text-foreground mb-4">Create New Search</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">
                  Search Name
                </label>
                <input 
                  type="text" 
                  placeholder="e.g., Downtown Condos"
                  className="w-full p-2 border border-border rounded bg-background text-foreground"
                />
              </div>
              
              <div className="text-sm text-muted-foreground">
                Search criteria will be based on your current filters.
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button 
                onClick={() => setShowCreateNew(false)}
                className="btn btn-secondary flex-1"
              >
                Cancel
              </button>
              <button 
                onClick={() => setShowCreateNew(false)}
                className="btn btn-primary flex-1"
              >
                Save Search
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}