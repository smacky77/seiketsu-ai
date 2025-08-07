'use client'

import React from 'react'

interface OrganizationSwitcherProps {
  className?: string
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
