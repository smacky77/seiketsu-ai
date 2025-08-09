'use client'

import React from 'react'

interface OrganizationSwitcherProps {
  className?: string
}

export function useOrganizationContext() {
  return {
    currentOrg: { id: '1', name: 'Seiketsu AI', slug: 'seiketsu' },
    organization: { id: '1', name: 'Seiketsu AI', slug: 'seiketsu' },
    setCurrentOrg: () => {},
    isAdmin: true
  }
}

export function OrganizationSwitcher({ className }: OrganizationSwitcherProps) {
  return (
    <div className={className}>
      <div className="text-sm font-medium mb-2">Organization</div>
      <div className="p-2 bg-muted rounded-lg">
        <span className="text-sm">Seiketsu AI</span>
      </div>
    </div>
  )
}

export default OrganizationSwitcher
