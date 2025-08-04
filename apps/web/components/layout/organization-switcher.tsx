"use client"

import * as React from "react"
import { Check, ChevronsUpDown, Plus, Building } from "lucide-react"
import { useRouter } from "next/navigation"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useAuthStore } from "@/lib/stores/auth-store"
import type { Organization } from "@/types"

interface OrganizationSwitcherProps {
  organizations?: Organization[]
  className?: string
}

export function OrganizationSwitcher({ 
  organizations = [], 
  className 
}: OrganizationSwitcherProps) {
  const [open, setOpen] = React.useState(false)
  const router = useRouter()
  const { organization: currentOrg, user } = useAuthStore()

  // Mock organizations for demo - replace with actual API call
  const mockOrganizations: Organization[] = React.useMemo(() => [
    {
      id: '1',
      name: 'Acme Real Estate',
      slug: 'acme-real-estate',
      logo: '/avatars/acme.png',
      settings: {
        voiceSettings: {
          defaultVoice: 'alloy',
          voiceSpeed: 1.0,
          language: 'en-US',
          enableTranscription: true,
          enableRecording: true,
          maxCallDuration: 1800
        },
        integrations: [],
        branding: {
          primaryColor: '#3b82f6',
          companyName: 'Acme Real Estate',
          websiteUrl: 'https://acme-real-estate.com'
        },
        security: {
          requireMFA: false,
          sessionTimeout: 3600,
          allowedDomains: [],
          ipWhitelist: []
        }
      },
      subscription: {
        id: 'sub_1',
        plan: 'professional',
        status: 'active',
        currentPeriodStart: new Date(),
        currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
        usage: {
          voiceMinutes: 1500,
          leadsProcessed: 250,
          agents: 3,
          integrations: 2
        }
      },
      createdAt: new Date('2024-01-01'),
      updatedAt: new Date()
    },
    {
      id: '2',
      name: 'Downtown Properties',
      slug: 'downtown-properties',
      logo: '/avatars/downtown.png',
      settings: {
        voiceSettings: {
          defaultVoice: 'echo',
          voiceSpeed: 1.1,
          language: 'en-US',
          enableTranscription: true,
          enableRecording: true,
          maxCallDuration: 1200
        },
        integrations: [],
        branding: {
          primaryColor: '#10b981',
          companyName: 'Downtown Properties',
          websiteUrl: 'https://downtown-properties.com'
        },
        security: {
          requireMFA: true,
          sessionTimeout: 1800,
          allowedDomains: ['downtown-properties.com'],
          ipWhitelist: []
        }
      },
      subscription: {
        id: 'sub_2',
        plan: 'enterprise',
        status: 'active',
        currentPeriodStart: new Date(),
        currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
        usage: {
          voiceMinutes: 5000,
          leadsProcessed: 1200,
          agents: 10,
          integrations: 5
        }
      },
      createdAt: new Date('2024-02-15'),
      updatedAt: new Date()
    }
  ], [])

  const allOrganizations = organizations.length > 0 ? organizations : mockOrganizations
  const selectedOrg = currentOrg || allOrganizations[0]

  const handleOrganizationSelect = (org: Organization) => {
    if (org.id === selectedOrg?.id) {
      setOpen(false)
      return
    }

    // Update the auth store with new organization
    useAuthStore.getState().updateOrganization(org)
    
    // Navigate to the organization-specific dashboard
    router.push(`/org/${org.slug}/dashboard`)
    setOpen(false)
  }

  const handleCreateOrganization = () => {
    router.push('/organizations/new')
    setOpen(false)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          aria-label="Select organization"
          className={cn("w-[200px] justify-between", className)}
        >
          <div className="flex items-center space-x-2 truncate">
            <Avatar className="h-5 w-5">
              <AvatarImage
                src={selectedOrg?.logo}
                alt={selectedOrg?.name}
                className="grayscale"
              />
              <AvatarFallback className="text-xs">
                {selectedOrg?.name?.slice(0, 2).toUpperCase() || 'ORG'}
              </AvatarFallback>
            </Avatar>
            <span className="truncate">{selectedOrg?.name || 'Select organization'}</span>
          </div>
          <ChevronsUpDown className="ml-auto h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[200px] p-0">
        <Command>
          <CommandInput placeholder="Search organizations..." />
          <CommandList>
            <CommandEmpty>No organizations found.</CommandEmpty>
            <CommandGroup heading="Organizations">
              {allOrganizations.map((org) => (
                <CommandItem
                  key={org.id}
                  onSelect={() => handleOrganizationSelect(org)}
                  className="text-sm"
                >
                  <div className="flex items-center space-x-2 flex-1">
                    <Avatar className="h-5 w-5">
                      <AvatarImage src={org.logo} alt={org.name} />
                      <AvatarFallback className="text-xs">
                        {org.name.slice(0, 2).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex flex-col">
                      <span className="truncate">{org.name}</span>
                      <span className="text-xs text-muted-foreground capitalize">
                        {org.subscription.plan}
                      </span>
                    </div>
                  </div>
                  <Check
                    className={cn(
                      "ml-auto h-4 w-4",
                      selectedOrg?.id === org.id ? "opacity-100" : "opacity-0"
                    )}
                  />
                </CommandItem>
              ))}
            </CommandGroup>
            {user?.role === 'admin' && (
              <>
                <CommandSeparator />
                <CommandGroup>
                  <CommandItem onSelect={handleCreateOrganization}>
                    <Plus className="mr-2 h-4 w-4" />
                    Create Organization
                  </CommandItem>
                </CommandGroup>
              </>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}

// Additional components for organization management
export function OrganizationCard({ organization }: { organization: Organization }) {
  const router = useRouter()

  return (
    <div className="card p-6 hover:shadow-md transition-shadow cursor-pointer"
         onClick={() => router.push(`/org/${organization.slug}/dashboard`)}>
      <div className="flex items-start space-x-4">
        <Avatar className="h-12 w-12">
          <AvatarImage src={organization.logo} alt={organization.name} />
          <AvatarFallback>
            <Building className="h-6 w-6" />
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-lg truncate">{organization.name}</h3>
          <p className="text-sm text-muted-foreground capitalize">
            {organization.subscription.plan} Plan
          </p>
          <div className="flex items-center space-x-4 mt-2 text-sm text-muted-foreground">
            <span>{organization.subscription.usage.agents} agents</span>
            <span>{organization.subscription.usage.voiceMinutes} minutes used</span>
            <span className={cn(
              "capitalize px-2 py-1 rounded-full text-xs",
              organization.subscription.status === 'active' 
                ? "bg-green-100 text-green-700" 
                : "bg-red-100 text-red-700"
            )}>
              {organization.subscription.status}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

// Organization context provider for deep multi-tenant support
export function useOrganizationContext() {
  const { organization, user } = useAuthStore()
  
  return {
    organization,
    user,
    isAdmin: user?.role === 'admin',
    canManageOrganization: user?.role === 'admin' || user?.role === 'manager',
    subscriptionPlan: organization?.subscription.plan,
    isSubscriptionActive: organization?.subscription.status === 'active',
    usageStats: organization?.subscription.usage,
  }
}