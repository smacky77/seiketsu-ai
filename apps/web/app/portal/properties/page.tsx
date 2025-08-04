'use client'

import { useState } from 'react'
import PropertyFilters from '@/components/portal/PropertyFilters'
import PropertyGrid from '@/components/portal/PropertyGrid'
import SavedSearches from '@/components/portal/SavedSearches'

export default function PropertiesPage() {
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [sortBy, setSortBy] = useState('recommended')
  
  return (
    <div className="space-y-6">
      {/* Page header with clear hierarchy */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
        <div>
          <h1 className="text-2xl font-bold text-foreground">My Properties</h1>
          <p className="text-muted-foreground">
            Saved searches, favorites, and personalized recommendations
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <select 
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm"
          >
            <option value="recommended">Recommended</option>
            <option value="price-low">Price: Low to High</option>
            <option value="price-high">Price: High to Low</option>
            <option value="newest">Newest Listed</option>
            <option value="size">Square Footage</option>
          </select>
          
          <div className="flex border border-border rounded-lg overflow-hidden">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 text-sm ${viewMode === 'grid' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            >
              ██
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 text-sm ${viewMode === 'list' ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground'}`}
            >
              ≡
            </button>
          </div>
        </div>
      </div>
      
      {/* Saved searches - quick access to client preferences */}
      <SavedSearches />
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters sidebar */}
        <div className="lg:col-span-1">
          <PropertyFilters />
        </div>
        
        {/* Property results */}
        <div className="lg:col-span-3">
          <PropertyGrid viewMode={viewMode} sortBy={sortBy} />
        </div>
      </div>
    </div>
  )
}