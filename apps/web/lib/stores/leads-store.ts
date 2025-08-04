import { create } from 'zustand'
import type { Lead, LeadStatus, Interaction, Note } from '@/types'

interface LeadsState {
  leads: Lead[]
  selectedLead: Lead | null
  filters: {
    status: LeadStatus[]
    dateRange: {
      start: Date | null
      end: Date | null
    }
    scoreRange: {
      min: number
      max: number
    }
    search: string
  }
  sortBy: 'createdAt' | 'updatedAt' | 'score' | 'lastName'
  sortOrder: 'asc' | 'desc'
  isLoading: boolean
  error: string | null
  pagination: {
    page: number
    limit: number
    total: number
  }
}

interface LeadsActions {
  // Lead management
  setLeads: (leads: Lead[]) => void
  addLead: (lead: Lead) => void
  updateLead: (leadId: string, updates: Partial<Lead>) => void
  removeLead: (leadId: string) => void
  setSelectedLead: (lead: Lead | null) => void
  updateLeadStatus: (leadId: string, status: LeadStatus) => void
  updateLeadScore: (leadId: string, score: number) => void

  // Interactions
  addInteraction: (leadId: string, interaction: Interaction) => void
  updateInteraction: (leadId: string, interactionId: string, updates: Partial<Interaction>) => void
  removeInteraction: (leadId: string, interactionId: string) => void

  // Notes
  addNote: (leadId: string, note: Note) => void
  updateNote: (leadId: string, noteId: string, updates: Partial<Note>) => void
  removeNote: (leadId: string, noteId: string) => void

  // Filtering and sorting
  setFilters: (filters: Partial<LeadsState['filters']>) => void
  clearFilters: () => void
  setSorting: (sortBy: LeadsState['sortBy'], sortOrder: LeadsState['sortOrder']) => void
  
  // Search and pagination
  setSearch: (search: string) => void
  setPagination: (pagination: Partial<LeadsState['pagination']>) => void
  nextPage: () => void
  previousPage: () => void

  // Loading and error states
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void

  // Bulk operations
  bulkUpdateStatus: (leadIds: string[], status: LeadStatus) => void
  bulkDelete: (leadIds: string[]) => void

  // Utilities
  getLeadById: (id: string) => Lead | undefined
  getFilteredLeads: () => Lead[]
  getLeadsByStatus: (status: LeadStatus) => Lead[]
  getRecentLeads: (days?: number) => Lead[]
  getHighScoreLeads: (minScore?: number) => Lead[]
  getLeadStats: () => {
    total: number
    byStatus: Record<LeadStatus, number>
    averageScore: number
    recentCount: number
  }
}

type LeadsStore = LeadsState & LeadsActions

const defaultFilters: LeadsState['filters'] = {
  status: [],
  dateRange: { start: null, end: null },
  scoreRange: { min: 0, max: 100 },
  search: '',
}

export const useLeadsStore = create<LeadsStore>((set, get) => ({
  // Initial state
  leads: [],
  selectedLead: null,
  filters: defaultFilters,
  sortBy: 'createdAt',
  sortOrder: 'desc',
  isLoading: false,
  error: null,
  pagination: {
    page: 1,
    limit: 25,
    total: 0,
  },

  // Lead management
  setLeads: (leads) => {
    set({
      leads,
      pagination: { ...get().pagination, total: leads.length },
    })
  },

  addLead: (lead) => {
    const { leads } = get()
    const newLeads = [lead, ...leads]
    set({
      leads: newLeads,
      pagination: { ...get().pagination, total: newLeads.length },
    })
  },

  updateLead: (leadId, updates) => {
    const { leads, selectedLead } = get()
    const newLeads = leads.map(lead =>
      lead.id === leadId ? { ...lead, ...updates, updatedAt: new Date() } : lead
    )
    set({
      leads: newLeads,
      selectedLead: selectedLead?.id === leadId 
        ? { ...selectedLead, ...updates, updatedAt: new Date() }
        : selectedLead,
    })
  },

  removeLead: (leadId) => {
    const { leads, selectedLead } = get()
    const newLeads = leads.filter(lead => lead.id !== leadId)
    set({
      leads: newLeads,
      selectedLead: selectedLead?.id === leadId ? null : selectedLead,
      pagination: { ...get().pagination, total: newLeads.length },
    })
  },

  setSelectedLead: (lead) => set({ selectedLead: lead }),

  updateLeadStatus: (leadId, status) => {
    get().updateLead(leadId, { status })
  },

  updateLeadScore: (leadId, score) => {
    get().updateLead(leadId, { score })
  },

  // Interactions
  addInteraction: (leadId, interaction) => {
    const { leads } = get()
    const lead = leads.find(l => l.id === leadId)
    if (lead) {
      const updatedInteractions = [interaction, ...lead.interactions]
      get().updateLead(leadId, { interactions: updatedInteractions })
    }
  },

  updateInteraction: (leadId, interactionId, updates) => {
    const { leads } = get()
    const lead = leads.find(l => l.id === leadId)
    if (lead) {
      const updatedInteractions = lead.interactions.map(interaction =>
        interaction.id === interactionId ? { ...interaction, ...updates } : interaction
      )
      get().updateLead(leadId, { interactions: updatedInteractions })
    }
  },

  removeInteraction: (leadId, interactionId) => {
    const { leads } = get()
    const lead = leads.find(l => l.id === leadId)
    if (lead) {
      const updatedInteractions = lead.interactions.filter(
        interaction => interaction.id !== interactionId
      )
      get().updateLead(leadId, { interactions: updatedInteractions })
    }
  },

  // Notes
  addNote: (leadId, note) => {
    const { leads } = get()
    const lead = leads.find(l => l.id === leadId)
    if (lead) {
      const updatedNotes = [note, ...lead.notes]
      get().updateLead(leadId, { notes: updatedNotes })
    }
  },

  updateNote: (leadId, noteId, updates) => {
    const { leads } = get()
    const lead = leads.find(l => l.id === leadId)
    if (lead) {
      const updatedNotes = lead.notes.map(note =>
        note.id === noteId ? { ...note, ...updates, updatedAt: new Date() } : note
      )
      get().updateLead(leadId, { notes: updatedNotes })
    }
  },

  removeNote: (leadId, noteId) => {
    const { leads } = get()
    const lead = leads.find(l => l.id === leadId)
    if (lead) {
      const updatedNotes = lead.notes.filter(note => note.id !== noteId)
      get().updateLead(leadId, { notes: updatedNotes })
    }
  },

  // Filtering and sorting
  setFilters: (newFilters) => {
    const { filters } = get()
    set({
      filters: { ...filters, ...newFilters },
      pagination: { ...get().pagination, page: 1 },
    })
  },

  clearFilters: () => {
    set({
      filters: defaultFilters,
      pagination: { ...get().pagination, page: 1 },
    })
  },

  setSorting: (sortBy, sortOrder) => {
    set({ sortBy, sortOrder })
  },

  // Search and pagination
  setSearch: (search) => {
    get().setFilters({ search })
  },

  setPagination: (pagination) => {
    set({
      pagination: { ...get().pagination, ...pagination },
    })
  },

  nextPage: () => {
    const { pagination } = get()
    if (pagination.page < Math.ceil(pagination.total / pagination.limit)) {
      set({
        pagination: { ...pagination, page: pagination.page + 1 },
      })
    }
  },

  previousPage: () => {
    const { pagination } = get()
    if (pagination.page > 1) {
      set({
        pagination: { ...pagination, page: pagination.page - 1 },
      })
    }
  },

  // Loading and error states
  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error, isLoading: false }),

  // Bulk operations
  bulkUpdateStatus: (leadIds, status) => {
    const { leads } = get()
    const updatedLeads = leads.map(lead =>
      leadIds.includes(lead.id) 
        ? { ...lead, status, updatedAt: new Date() }
        : lead
    )
    set({ leads: updatedLeads })
  },

  bulkDelete: (leadIds) => {
    const { leads, selectedLead } = get()
    const updatedLeads = leads.filter(lead => !leadIds.includes(lead.id))
    set({
      leads: updatedLeads,
      selectedLead: selectedLead && leadIds.includes(selectedLead.id) 
        ? null 
        : selectedLead,
      pagination: { ...get().pagination, total: updatedLeads.length },
    })
  },

  // Utilities
  getLeadById: (id) => {
    const { leads } = get()
    return leads.find(lead => lead.id === id)
  },

  getFilteredLeads: () => {
    const { leads, filters, sortBy, sortOrder } = get()
    
    let filtered = leads.filter(lead => {
      // Status filter
      if (filters.status.length > 0 && !filters.status.includes(lead.status)) {
        return false
      }
      
      // Date range filter
      if (filters.dateRange.start && new Date(lead.createdAt) < filters.dateRange.start) {
        return false
      }
      if (filters.dateRange.end && new Date(lead.createdAt) > filters.dateRange.end) {
        return false
      }
      
      // Score range filter
      if (lead.score < filters.scoreRange.min || lead.score > filters.scoreRange.max) {
        return false
      }
      
      // Search filter
      if (filters.search) {
        const search = filters.search.toLowerCase()
        const fullName = `${lead.contact.firstName} ${lead.contact.lastName}`.toLowerCase()
        const email = lead.contact.email.toLowerCase()
        const phone = lead.contact.phone.toLowerCase()
        
        if (!fullName.includes(search) && !email.includes(search) && !phone.includes(search)) {
          return false
        }
      }
      
      return true
    })
    
    // Sort
    filtered.sort((a, b) => {
      let aVal: any = a[sortBy]
      let bVal: any = b[sortBy]
      
      if (sortBy === 'lastName') {
        aVal = a.contact.lastName
        bVal = b.contact.lastName
      }
      
      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1
      return 0
    })
    
    return filtered
  },

  getLeadsByStatus: (status) => {
    const { leads } = get()
    return leads.filter(lead => lead.status === status)
  },

  getRecentLeads: (days = 7) => {
    const { leads } = get()
    const cutoff = new Date()
    cutoff.setDate(cutoff.getDate() - days)
    return leads.filter(lead => new Date(lead.createdAt) >= cutoff)
  },

  getHighScoreLeads: (minScore = 80) => {
    const { leads } = get()
    return leads.filter(lead => lead.score >= minScore)
  },

  getLeadStats: () => {
    const { leads } = get()
    
    const byStatus: Record<LeadStatus, number> = {
      new: 0,
      qualified: 0,
      contacted: 0,
      scheduled: 0,
      converted: 0,
      lost: 0,
    }
    
    let totalScore = 0
    const recentCutoff = new Date()
    recentCutoff.setDate(recentCutoff.getDate() - 7)
    let recentCount = 0
    
    leads.forEach(lead => {
      byStatus[lead.status]++
      totalScore += lead.score
      if (new Date(lead.createdAt) >= recentCutoff) {
        recentCount++
      }
    })
    
    return {
      total: leads.length,
      byStatus,
      averageScore: leads.length > 0 ? totalScore / leads.length : 0,
      recentCount,
    }
  },
}))