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
    const response = await apiClient.get<{
      leads: Lead[];
      total: number;
      pagination: {
        page: number;
        limit: number;
        totalPages: number;
      };
    }>(API_CONFIG.ENDPOINTS.LEADS.LIST, params);
    return response.data;
  }

  // Get lead by ID
  async getLead(id: string): Promise<Lead> {
    const response = await apiClient.get<Lead>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      undefined,
      { id }
    );
    return response.data;
  }

  // Create lead
  async createLead(data: Partial<Lead>): Promise<Lead> {
    const response = await apiClient.post<Lead>(API_CONFIG.ENDPOINTS.LEADS.CREATE, data);
    return response.data;
  }

  // Update lead
  async updateLead(id: string, data: Partial<Lead>): Promise<Lead> {
    const response = await apiClient.put<Lead>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      data,
      { id }
    );
    return response.data;
  }

  // Delete lead
  async deleteLead(id: string): Promise<void> {
    await apiClient.delete(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { id }
    );
  }

  // Qualify lead
  async qualifyLead(id: string, data?: {
    overrides?: Record<string, any>;
    includeRecommendations?: boolean;
  }): Promise<LeadQualificationResult> {
    const response = await apiClient.post<LeadQualificationResult>(
      API_CONFIG.ENDPOINTS.LEADS.QUALIFY,
      data,
      { id }
    );
    return response.data;
  }

  // Assign lead to agent
  async assignLead(id: string, agentId: string, notes?: string): Promise<Lead> {
    const response = await apiClient.post<Lead>(
      API_CONFIG.ENDPOINTS.LEADS.ASSIGN,
      { agentId, notes },
      { id }
    );
    return response.data;
  }

  // Add interaction
  async addInteraction(leadId: string, interaction: Partial<Interaction>): Promise<Interaction> {
    const response = await apiClient.post<Interaction>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { ...interaction, action: 'add_interaction' },
      { id: leadId }
    );
    return response.data;
  }

  // Update interaction
  async updateInteraction(
    leadId: string,
    interactionId: string,
    data: Partial<Interaction>
  ): Promise<Interaction> {
    const response = await apiClient.put<Interaction>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { ...data, action: 'update_interaction', interactionId },
      { id: leadId }
    );
    return response.data;
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
    const response = await apiClient.get<{
      interactions: Interaction[];
      total: number;
    }>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { ...params, action: 'interactions' },
      { id: leadId }
    );
    return response.data;
  }

  // Schedule follow-up
  async scheduleFollowUp(leadId: string, data: {
    type: 'call' | 'email' | 'meeting';
    scheduledAt: string;
    notes?: string;
    agentId?: string;
  }): Promise<Interaction> {
    const response = await apiClient.post<Interaction>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { ...data, action: 'schedule_followup' },
      { id: leadId }
    );
    return response.data;
  }

  // Update lead status
  async updateStatus(leadId: string, status: Lead['status'], notes?: string): Promise<Lead> {
    const response = await apiClient.patch<Lead>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { status, notes },
      { id: leadId }
    );
    return response.data;
  }

  // Add tags to lead
  async addTags(leadId: string, tags: string[]): Promise<Lead> {
    const response = await apiClient.patch<Lead>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { action: 'add_tags', tags },
      { id: leadId }
    );
    return response.data;
  }

  // Remove tags from lead
  async removeTags(leadId: string, tags: string[]): Promise<Lead> {
    const response = await apiClient.patch<Lead>(
      API_CONFIG.ENDPOINTS.LEADS.DETAILS,
      { action: 'remove_tags', tags },
      { id: leadId }
    );
    return response.data;
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
    const response = await apiClient.get<{
      leads: Lead[];
      total: number;
    }>(API_CONFIG.ENDPOINTS.LEADS.LIST, {
      search: query,
      ...filters
    });
    return response.data;
  }

  // Get lead analytics
  async getLeadAnalytics(params?: {
    startDate?: string;
    endDate?: string;
    groupBy?: 'day' | 'week' | 'month';
    agentId?: string;
  }): Promise<LeadAnalytics> {
    const response = await apiClient.get<LeadAnalytics>(
      API_CONFIG.ENDPOINTS.LEADS.ANALYTICS,
      params
    );
    return response.data;
  }

  // Get leads requiring follow-up
  async getFollowUpLeads(params?: {
    overdue?: boolean;
    dueToday?: boolean;
    dueThisWeek?: boolean;
    agentId?: string;
  }): Promise<Lead[]> {
    const response = await apiClient.get<Lead[]>(
      API_CONFIG.ENDPOINTS.LEADS.LIST,
      { ...params, followUp: true }
    );
    return response.data;
  }

  // Bulk update leads
  async bulkUpdateLeads(leadIds: string[], updates: {
    status?: Lead['status'];
    assignedTo?: string;
    tags?: string[];
    notes?: string;
  }): Promise<{ updated: number; errors: string[] }> {
    const response = await apiClient.patch<{ updated: number; errors: string[] }>(
      API_CONFIG.ENDPOINTS.LEADS.LIST,
      { leadIds, updates, action: 'bulk_update' }
    );
    return response.data;
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

    const response = await apiClient.post<{
      jobId: string;
      status: string;
    }>(API_CONFIG.ENDPOINTS.LEADS.LIST, formData);
    return response.data;
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
    const response = await apiClient.get<{
      status: 'pending' | 'processing' | 'completed' | 'failed';
      progress: number;
      processed: number;
      total: number;
      errors: string[];
      duplicates: number;
    }>(API_CONFIG.ENDPOINTS.LEADS.LIST, { jobId, action: 'import_status' });
    return response.data;
  }

  // Export leads to CSV
  async exportLeads(params?: {
    status?: string[];
    source?: string[];
    startDate?: string;
    endDate?: string;
    format?: 'csv' | 'xlsx';
  }): Promise<Blob> {
    // For now, return a mock blob until proper export API is implemented
    const csvContent = 'id,firstName,lastName,email,phone,status\n';
    return new Blob([csvContent], { type: 'text/csv' });
  }
}

// Create singleton instance
export const leadsService = new LeadsService();

export default leadsService;