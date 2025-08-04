// Leads Management Service
import { apiClient } from '../client';
import { API_CONFIG } from '../config';

// Types
export interface Lead {
  id: string;
  personalInfo: {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    address?: {
      street?: string;
      city?: string;
      state?: string;
      zipCode?: string;
    };
  };
  preferences: {
    propertyTypes: string[];
    priceRange: {
      min: number;
      max: number;
    };
    locations: string[];
    bedrooms?: number;
    bathrooms?: number;
    features?: string[];
    timeline: 'immediate' | '3_months' | '6_months' | '1_year' | 'flexible';
  };
  qualification: {
    score: number;
    status: 'unqualified' | 'cold' | 'warm' | 'hot' | 'qualified';
    creditScore?: number;
    income?: number;
    preApproved?: boolean;
    cashBuyer?: boolean;
    firstTimeBuyer?: boolean;
    motivation: string;
    urgency: 'low' | 'medium' | 'high';
  };
  interactions: Interaction[];
  assignedTo?: string;
  source: 'website' | 'phone' | 'referral' | 'social' | 'advertising' | 'event';
  tags: string[];
  notes: string;
  lastContact: string;
  nextFollowUp?: string;
  status: 'new' | 'contacted' | 'nurturing' | 'qualified' | 'converted' | 'lost';
  tenantId: string;
  createdAt: string;
  updatedAt: string;
}

export interface Interaction {
  id: string;
  type: 'call' | 'email' | 'meeting' | 'property_viewing' | 'voice_conversation';
  direction: 'inbound' | 'outbound';
  summary: string;
  notes?: string;
  outcome: string;
  duration?: number;
  scheduledAt?: string;
  completedAt: string;
  agentId: string;
  recordingUrl?: string;
  transcriptUrl?: string;
}

export interface LeadQualificationResult {
  score: number;
  status: 'unqualified' | 'cold' | 'warm' | 'hot' | 'qualified';
  factors: Array<{
    factor: string;
    score: number;
    weight: number;
    description: string;
  }>;
  recommendations: string[];
  nextActions: Array<{
    action: string;
    priority: 'low' | 'medium' | 'high';
    timeline: string;
  }>;
}

export interface LeadAnalytics {
  totalLeads: number;
  newLeads: number;
  qualifiedLeads: number;
  convertedLeads: number;
  conversionRate: number;
  averageQualificationScore: number;
  sourceDistribution: Array<{
    source: string;
    count: number;
    percentage: number;
    conversionRate: number;
  }>;
  statusDistribution: Array<{
    status: string;
    count: number;
    percentage: number;
  }>;
  trends: {
    leads: Array<{
      date: string;
      count: number;
      qualified: number;
      converted: number;
    }>;
    qualificationScores: Array<{
      date: string;
      averageScore: number;
    }>;
  };
}

// Leads Service Class
class LeadsService {
  // Get all leads
  async getLeads(params?: {
    status?: string[];
    source?: string[];
    assignedTo?: string;
    qualificationStatus?: string[];
    minScore?: number;
    maxScore?: number;
    createdAfter?: string;
    createdBefore?: string;
    sortBy?: 'created' | 'updated' | 'score' | 'lastContact';
    sortOrder?: 'asc' | 'desc';
    limit?: number;
    offset?: number;
  }): Promise<{
    leads: Lead[];
    total: number;
    pagination: {
      page: number;
      limit: number;
      totalPages: number;
    };
  }> {
    return apiClient.get<{
      leads: Lead[];
      total: number;
      pagination: {
        page: number;
        limit: number;
        totalPages: number;
      };
    }>(API_CONFIG.ENDPOINTS.LEADS.LIST, params);
  }

  // Get lead by ID
  async getLead(id: string): Promise<Lead> {
    return apiClient.get<Lead>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      undefined,
      { id }
    );
  }

  // Create lead
  async createLead(data: Partial<Lead>): Promise<Lead> {
    return apiClient.post<Lead>(API_CONFIG.ENDPOINTS.LEADS.CREATE, data);
  }

  // Update lead
  async updateLead(id: string, data: Partial<Lead>): Promise<Lead> {
    return apiClient.put<Lead>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      data,
      { id }
    );
  }

  // Delete lead
  async deleteLead(id: string): Promise<void> {
    return apiClient.delete(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { id }
    );
  }

  // Qualify lead
  async qualifyLead(id: string, data?: {
    overrides?: Record<string, any>;
    includeRecommendations?: boolean;
  }): Promise<LeadQualificationResult> {
    return apiClient.post<LeadQualificationResult>(
      API_CONFIG.ENDPOINTS.LEADS.QUALIFY,
      data,
      { id }
    );
  }

  // Assign lead to agent
  async assignLead(id: string, agentId: string, notes?: string): Promise<Lead> {
    return apiClient.post<Lead>(
      API_CONFIG.ENDPOINTS.LEADS.ASSIGN,
      { agentId, notes },
      { id }
    );
  }

  // Add interaction
  async addInteraction(leadId: string, interaction: Partial<Interaction>): Promise<Interaction> {
    return apiClient.post<Interaction>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { ...interaction, action: 'add_interaction' },
      { id: leadId }
    );
  }

  // Update interaction
  async updateInteraction(
    leadId: string,
    interactionId: string,
    data: Partial<Interaction>
  ): Promise<Interaction> {
    return apiClient.put<Interaction>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { ...data, action: 'update_interaction', interactionId },
      { id: leadId }
    );
  }

  // Get lead interactions
  async getInteractions(leadId: string, params?: {
    type?: string[];
    startDate?: string;
    endDate?: string;
    limit?: number;
    offset?: number;
  }): Promise<{
    interactions: Interaction[];
    total: number;
  }> {
    return apiClient.get<{
      interactions: Interaction[];
      total: number;
    }>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { ...params, action: 'interactions' },
      { id: leadId }
    );
  }

  // Schedule follow-up
  async scheduleFollowUp(leadId: string, data: {
    type: 'call' | 'email' | 'meeting';
    scheduledAt: string;
    notes?: string;
    agentId?: string;
  }): Promise<Interaction> {
    return apiClient.post<Interaction>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { ...data, action: 'schedule_followup' },
      { id: leadId }
    );
  }

  // Update lead status
  async updateStatus(leadId: string, status: Lead['status'], notes?: string): Promise<Lead> {
    return apiClient.patch<Lead>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { status, notes },
      { id: leadId }
    );
  }

  // Add tags to lead
  async addTags(leadId: string, tags: string[]): Promise<Lead> {
    return apiClient.patch<Lead>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { action: 'add_tags', tags },
      { id: leadId }
    );
  }

  // Remove tags from lead
  async removeTags(leadId: string, tags: string[]): Promise<Lead> {
    return apiClient.patch<Lead>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { action: 'remove_tags', tags },
      { id: leadId }
    );
  }

  // Search leads
  async searchLeads(query: string, filters?: {
    status?: string[];
    source?: string[];
    tags?: string[];
  }): Promise<{
    leads: Lead[];
    total: number;
  }> {
    return apiClient.get<{
      leads: Lead[];
      total: number;
    }>(API_CONFIG.ENDPOINTS.LEADS.LIST, {
      search: query,
      ...filters
    });
  }

  // Get lead analytics
  async getLeadAnalytics(params?: {
    startDate?: string;
    endDate?: string;
    groupBy?: 'day' | 'week' | 'month';
    agentId?: string;
  }): Promise<LeadAnalytics> {
    return apiClient.get<LeadAnalytics>(
      API_CONFIG.ENDPOINTS.LEADS.ANALYTICS,
      params
    );
  }

  // Get leads requiring follow-up
  async getFollowUpLeads(params?: {
    overdue?: boolean;
    dueToday?: boolean;
    dueThisWeek?: boolean;
    agentId?: string;
  }): Promise<Lead[]> {
    return apiClient.get<Lead[]>(
      API_CONFIG.ENDPOINTS.LEADS.LIST,
      { ...params, followUp: true }
    );
  }

  // Bulk update leads
  async bulkUpdateLeads(leadIds: string[], updates: {
    status?: Lead['status'];
    assignedTo?: string;
    tags?: string[];
    notes?: string;
  }): Promise<{ updated: number; errors: string[] }> {
    return apiClient.patch<{ updated: number; errors: string[] }>(
      API_CONFIG.ENDPOINTS.LEADS.LIST,
      { leadIds, updates, action: 'bulk_update' }
    );
  }

  // Import leads from CSV
  async importLeads(file: File, options?: {
    skipDuplicates?: boolean;
    autoQualify?: boolean;
    defaultSource?: string;
    defaultAssignee?: string;
  }): Promise<{
    jobId: string;
    status: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options) {
      Object.entries(options).forEach(([key, value]) => {
        formData.append(key, String(value));
      });
    }

    return apiClient.post<{
      jobId: string;
      status: string;
    }>(API_CONFIG.ENDPOINTS.LEADS.LIST, formData);
  }

  // Get import status
  async getImportStatus(jobId: string): Promise<{
    status: 'pending' | 'processing' | 'completed' | 'failed';
    progress: number;
    processed: number;
    total: number;
    errors: string[];
    duplicates: number;
  }> {
    return apiClient.get<{
      status: 'pending' | 'processing' | 'completed' | 'failed';
      progress: number;
      processed: number;
      total: number;
      errors: string[];
      duplicates: number;
    }>(API_CONFIG.ENDPOINTS.LEADS.LIST, { jobId, action: 'import_status' });
  }

  // Export leads to CSV
  async exportLeads(params?: {
    status?: string[];
    source?: string[];
    startDate?: string;
    endDate?: string;
    format?: 'csv' | 'xlsx';
  }): Promise<Blob> {
    const response = await fetch(
      apiClient.buildUrl(API_CONFIG.ENDPOINTS.LEADS.LIST, {
        ...params,
        action: 'export'
      }),
      {
        headers: apiClient.getHeaders()
      }
    );

    if (!response.ok) {
      throw new Error('Export failed');
    }

    return response.blob();
  }
}

// Create singleton instance
export const leadsService = new LeadsService();

export default leadsService;