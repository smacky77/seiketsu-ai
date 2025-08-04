'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Building2, 
  ChevronDown, 
  Check, 
  Plus,
  Settings,
  Users,
  Crown
} from 'lucide-react'

interface Tenant {
  id: string
  name: string
  plan: 'starter' | 'professional' | 'enterprise'
  agentCount: number
  status: 'active' | 'trial' | 'suspended'
}

const mockTenants: Tenant[] = [
  {
    id: '1',
    name: 'Premier Realty Group',
    plan: 'enterprise',
    agentCount: 25,
    status: 'active'
  },
  {
    id: '2',
    name: 'Sunset Properties',
    plan: 'professional',
    agentCount: 8,
    status: 'active'
  },
  {
    id: '3',
    name: 'Metro Home Solutions',
    plan: 'starter',
    agentCount: 3,
    status: 'trial'
  }
]

export function TenantSwitcher() {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedTenant, setSelectedTenant] = useState(mockTenants[0])

  const handleTenantSelect = (tenant: Tenant) => {
    setSelectedTenant(tenant)
    setIsOpen(false)
  }

  const getPlanIcon = (plan: string) => {
    switch (plan) {
      case 'enterprise':
        return <Crown className="w-3 h-3 text-yellow-500" />
      case 'professional':
        return <Settings className="w-3 h-3 text-blue-500" />
      case 'starter':
        return <Users className="w-3 h-3 text-green-500" />
      default:
        return null
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500'
      case 'trial':
        return 'bg-yellow-500'
      case 'suspended':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  return (
    <div className="relative">
      {/* Current Tenant Display */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 bg-muted rounded-lg hover:bg-accent transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-background rounded-lg flex items-center justify-center border border-border">
            <Building2 className="w-5 h-5 text-foreground" />
          </div>
          <div className="text-left">
            <div className="font-medium text-foreground">{selectedTenant.name}</div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {getPlanIcon(selectedTenant.plan)}
              <span className="capitalize">{selectedTenant.plan}</span>
              <span>•</span>
              <span>{selectedTenant.agentCount} agents</span>
              <div className={`w-2 h-2 rounded-full ${getStatusColor(selectedTenant.status)}`} />
            </div>
          </div>
        </div>
        <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Tenant Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full left-0 right-0 mt-2 bg-card border border-border rounded-lg shadow-lg z-50"
          >
            <div className="p-2">
              {/* Tenant List */}
              <div className="space-y-1">
                {mockTenants.map((tenant) => (
                  <button
                    key={tenant.id}
                    onClick={() => handleTenantSelect(tenant)}
                    className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-muted transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-muted rounded-lg flex items-center justify-center">
                        <Building2 className="w-4 h-4 text-muted-foreground" />
                      </div>
                      <div className="text-left">
                        <div className="font-medium text-sm">{tenant.name}</div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          {getPlanIcon(tenant.plan)}
                          <span className="capitalize">{tenant.plan}</span>
                          <span>•</span>
                          <span>{tenant.agentCount} agents</span>
                          <div className={`w-2 h-2 rounded-full ${getStatusColor(tenant.status)}`} />
                        </div>
                      </div>
                    </div>
                    {selectedTenant.id === tenant.id && (
                      <Check className="w-4 h-4 text-green-500" />
                    )}
                  </button>
                ))}
              </div>

              {/* Add New Tenant */}
              <div className="border-t border-border mt-2 pt-2">
                <button className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-muted transition-colors text-muted-foreground">
                  <div className="w-8 h-8 bg-muted rounded-lg flex items-center justify-center border-2 border-dashed border-border">
                    <Plus className="w-4 h-4" />
                  </div>
                  <span className="text-sm font-medium">Add New Agency</span>
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}