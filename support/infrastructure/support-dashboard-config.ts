// Seiketsu AI Support Dashboard Configuration
// Real-time monitoring and management interface for 24/7 support operations

export interface SupportDashboardConfig {
  slaTargets: SLATargets;
  alertRules: AlertRule[];
  escalationPaths: EscalationPath[];
  metrics: MetricConfig[];
  integrations: IntegrationConfig;
  teamStructure: TeamStructure;
}

export interface SLATargets {
  critical: string; // "15m"
  high: string;     // "1h"
  standard: string; // "4h"
  satisfaction: number; // 0.95 = 95%
}

export interface AlertRule {
  id: string;
  name: string;
  condition: string;
  severity: 'P0' | 'P1' | 'P2' | 'P3';
  channels: string[];
  escalationDelay: string;
}

export interface EscalationPath {
  triggerId: string;
  steps: EscalationStep[];
}

export interface EscalationStep {
  level: number;
  role: string;
  delay: string;
  channels: string[];
  autoAssign: boolean;
}

export const supportDashboardConfig: SupportDashboardConfig = {
  slaTargets: {
    critical: '15m',
    high: '1h', 
    standard: '4h',
    satisfaction: 0.95
  },

  alertRules: [
    {
      id: 'sla_breach_critical',
      name: 'Critical SLA Breach',
      condition: 'ticket.priority === "critical" && ticket.responseTime > "15m"',
      severity: 'P0',
      channels: ['slack-emergency', 'sms-manager', 'pagerduty'],
      escalationDelay: '5m'
    },
    {
      id: 'satisfaction_drop',
      name: 'Satisfaction Score Drop',
      condition: 'satisfaction.daily < 0.90',
      severity: 'P2',
      channels: ['slack-management', 'email-team'],
      escalationDelay: '30m'
    },
    {
      id: 'high_volume_spike',
      name: 'High Ticket Volume Spike',
      condition: 'tickets.hourly > (tickets.average * 2)',
      severity: 'P1',
      channels: ['slack-ops', 'sms-leads'],
      escalationDelay: '15m'
    },
    {
      id: 'system_downtime',
      name: 'Support System Downtime',
      condition: 'system.availability < 0.99',
      severity: 'P0',
      channels: ['slack-emergency', 'pagerduty', 'sms-all'],
      escalationDelay: '0m'
    }
  ],

  escalationPaths: [
    {
      triggerId: 'critical_issue',
      steps: [
        {
          level: 1,
          role: 'senior_support_engineer',
          delay: '0m',
          channels: ['slack-direct', 'phone-call'],
          autoAssign: true
        },
        {
          level: 2,
          role: 'support_manager',
          delay: '15m',
          channels: ['slack-escalation', 'phone-call'],
          autoAssign: true
        },
        {
          level: 3,
          role: 'engineering_lead',
          delay: '30m',
          channels: ['slack-engineering', 'phone-call'],
          autoAssign: false
        },
        {
          level: 4,
          role: 'cto',
          delay: '45m',
          channels: ['direct-phone', 'text-message'],
          autoAssign: true
        }
      ]
    },
    {
      triggerId: 'enterprise_client_issue',
      steps: [
        {
          level: 1,
          role: 'customer_success_manager',
          delay: '0m',
          channels: ['dedicated-slack', 'phone-call'],
          autoAssign: true
        },
        {
          level: 2,
          role: 'technical_account_manager',
          delay: '30m',
          channels: ['escalation-slack', 'video-call'],
          autoAssign: true
        }
      ]
    }
  ],

  metrics: [
    {
      id: 'first_response_time',
      name: 'First Response Time',
      type: 'duration',
      target: '15m',
      alertThreshold: '20m',
      displayFormat: 'minutes',
      dashboardPosition: { row: 1, col: 1 }
    },
    {
      id: 'resolution_time',
      name: 'Resolution Time',
      type: 'duration',
      target: '4h',
      alertThreshold: '6h',
      displayFormat: 'hours',
      dashboardPosition: { row: 1, col: 2 }
    },
    {
      id: 'satisfaction_score',
      name: 'Customer Satisfaction',
      type: 'percentage',
      target: 95,
      alertThreshold: 90,
      displayFormat: 'percentage',
      dashboardPosition: { row: 1, col: 3 }
    },
    {
      id: 'ticket_volume',
      name: 'Ticket Volume',
      type: 'count',
      target: null,
      alertThreshold: null,
      displayFormat: 'number',
      dashboardPosition: { row: 2, col: 1 }
    },
    {
      id: 'escalation_rate',
      name: 'Escalation Rate',
      type: 'percentage',
      target: 5,
      alertThreshold: 10,
      displayFormat: 'percentage',
      dashboardPosition: { row: 2, col: 2 }
    },
    {
      id: 'agent_utilization',
      name: 'Agent Utilization',
      type: 'percentage',
      target: 80,
      alertThreshold: 95,
      displayFormat: 'percentage',
      dashboardPosition: { row: 2, col: 3 }
    }
  ],

  integrations: {
    ticketing: {
      platform: 'zendesk',
      apiKey: process.env.ZENDESK_API_KEY || '',
      webhookUrl: '/api/webhooks/zendesk',
      syncInterval: '5m',
      fieldMappings: {
        priority: 'custom_field_priority',
        clientTier: 'custom_field_client_tier',
        productArea: 'custom_field_product_area'
      }
    },
    chat: {
      platform: 'intercom',
      apiKey: process.env.INTERCOM_API_KEY || '',
      webhookUrl: '/api/webhooks/intercom',
      autoRouting: true,
      businessHours: {
        timezone: 'America/New_York',
        hours: '24/7'
      }
    },
    phone: {
      platform: 'twilio_flex',
      accountSid: process.env.TWILIO_ACCOUNT_SID || '',
      authToken: process.env.TWILIO_AUTH_TOKEN || '',
      mainNumber: '+18005SEIKETSU',
      emergencyNumber: '+18005SEIKETSU911',
      recordingEnabled: true
    },
    monitoring: {
      platform: 'datadog',
      apiKey: process.env.DATADOG_API_KEY || '',
      dashboardId: 'support-overview',
      alerting: true,
      customMetrics: [
        'seiketsu.support.response_time',
        'seiketsu.support.satisfaction',
        'seiketsu.support.ticket_volume'
      ]
    },
    crm: {
      platform: 'salesforce',
      instanceUrl: process.env.SALESFORCE_URL || '',
      clientId: process.env.SALESFORCE_CLIENT_ID || '',
      clientSecret: process.env.SALESFORCE_CLIENT_SECRET || '',
      syncTickets: true,
      createTasks: true
    },
    knowledgeBase: {
      platform: 'gitbook',
      apiKey: process.env.GITBOOK_API_KEY || '',
      spaceId: 'seiketsu-support',
      autoSuggest: true,
      searchEnabled: true
    }
  },

  teamStructure: {
    roles: [
      {
        id: 'support_manager',
        name: 'Support Manager',
        level: 5,
        permissions: ['all'],
        coverage: '24/7',
        count: 2,
        skills: ['leadership', 'escalation', 'process'],
        languages: ['en'],
        certifications: ['zendesk_admin', 'itil_foundation']
      },
      {
        id: 'senior_support_engineer',
        name: 'Senior Support Engineer',
        level: 4,
        permissions: ['tickets', 'escalations', 'knowledge_base'],
        coverage: '24/7',
        count: 4,
        skills: ['api_integration', 'troubleshooting', 'voice_tech'],
        languages: ['en'],
        certifications: ['seiketsu_certified', 'aws_basics']
      },
      {
        id: 'support_engineer',
        name: 'Support Engineer', 
        level: 3,
        permissions: ['tickets', 'knowledge_base'],
        coverage: '24/7',
        count: 8,
        skills: ['general_support', 'basic_api', 'real_estate'],
        languages: ['en', 'es'],
        certifications: ['seiketsu_certified']
      },
      {
        id: 'customer_success_manager',
        name: 'Customer Success Manager',
        level: 4,
        permissions: ['accounts', 'escalations', 'billing'],
        coverage: 'business_hours',
        count: 6,
        skills: ['onboarding', 'relationship', 'optimization'],
        languages: ['en'],
        certifications: ['csm_certified', 'seiketsu_expert']
      },
      {
        id: 'technical_account_manager',
        name: 'Technical Account Manager',
        level: 5,
        permissions: ['enterprise_accounts', 'custom_solutions'],
        coverage: 'on_call',
        count: 3,
        skills: ['enterprise_sales', 'technical_consulting', 'project_management'],
        languages: ['en'],
        certifications: ['pmp', 'seiketsu_expert', 'aws_solutions_architect']
      }
    ],
    shifts: [
      {
        name: 'US Morning',
        timezone: 'America/New_York',
        hours: '06:00-14:00',
        coverage: ['support_engineer', 'senior_support_engineer', 'support_manager']
      },
      {
        name: 'US Afternoon',
        timezone: 'America/New_York', 
        hours: '14:00-22:00',
        coverage: ['support_engineer', 'senior_support_engineer', 'customer_success_manager']
      },
      {
        name: 'US Night/APAC',
        timezone: 'America/Los_Angeles',
        hours: '22:00-06:00',
        coverage: ['support_engineer', 'senior_support_engineer']
      }
    ],
    onCallRotation: {
      managers: ['manager_1', 'manager_2'],
      engineers: ['senior_1', 'senior_2', 'senior_3', 'senior_4'],
      rotationWeeks: 1,
      escalationDelay: '15m'
    }
  }
};

export default supportDashboardConfig;

// Types for configuration
interface MetricConfig {
  id: string;
  name: string;
  type: 'duration' | 'percentage' | 'count' | 'currency';
  target: number | string | null;
  alertThreshold: number | string | null;
  displayFormat: string;
  dashboardPosition: { row: number; col: number };
}

interface IntegrationConfig {
  ticketing: TicketingConfig;
  chat: ChatConfig;
  phone: PhoneConfig;
  monitoring: MonitoringConfig;
  crm: CRMConfig;
  knowledgeBase: KnowledgeBaseConfig;
}

interface TicketingConfig {
  platform: string;
  apiKey: string;
  webhookUrl: string;
  syncInterval: string;
  fieldMappings: Record<string, string>;
}

interface ChatConfig {
  platform: string;
  apiKey: string;
  webhookUrl: string;
  autoRouting: boolean;
  businessHours: {
    timezone: string;
    hours: string;
  };
}

interface PhoneConfig {
  platform: string;
  accountSid: string;
  authToken: string;
  mainNumber: string;
  emergencyNumber: string;
  recordingEnabled: boolean;
}

interface MonitoringConfig {
  platform: string;
  apiKey: string;
  dashboardId: string;
  alerting: boolean;
  customMetrics: string[];
}

interface CRMConfig {
  platform: string;
  instanceUrl: string;
  clientId: string;
  clientSecret: string;
  syncTickets: boolean;
  createTasks: boolean;
}

interface KnowledgeBaseConfig {
  platform: string;
  apiKey: string;
  spaceId: string;
  autoSuggest: boolean;
  searchEnabled: boolean;
}

interface TeamStructure {
  roles: Role[];
  shifts: Shift[];
  onCallRotation: OnCallRotation;
}

interface Role {
  id: string;
  name: string;
  level: number;
  permissions: string[];
  coverage: string;
  count: number;
  skills: string[];
  languages: string[];
  certifications: string[];
}

interface Shift {
  name: string;
  timezone: string;
  hours: string;
  coverage: string[];
}

interface OnCallRotation {
  managers: string[];
  engineers: string[];
  rotationWeeks: number;
  escalationDelay: string;
}