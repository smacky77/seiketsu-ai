'use client'

import { useState, useCallback, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Epic3Service } from '@/lib/api/services/epic3.service'
import { 
  EmailCampaign,
  SMSCampaign,
  CommunicationWorkflow
} from '@/lib/api/services/epic3.service'

// Email Campaigns Hook
export function useEmailCampaigns() {
  const queryClient = useQueryClient()

  const {
    data: campaigns,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['email-campaigns'],
    queryFn: Epic3Service.communication.getEmailCampaigns,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000 // 10 minutes (formerly gcTime)
  })

  const createCampaignMutation = useMutation({
    mutationFn: Epic3Service.communication.createEmailCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-campaigns'] })
    }
  })

  const updateCampaignMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<EmailCampaign> }) =>
      Epic3Service.communication.updateEmailCampaign(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-campaigns'] })
    }
  })

  const pauseCampaignMutation = useMutation({
    mutationFn: Epic3Service.communication.pauseEmailCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-campaigns'] })
    }
  })

  const resumeCampaignMutation = useMutation({
    mutationFn: Epic3Service.communication.resumeEmailCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['email-campaigns'] })
    }
  })

  const createCampaign = useCallback((campaign: Partial<EmailCampaign>) => {
    return createCampaignMutation.mutateAsync(campaign)
  }, [createCampaignMutation])

  const updateCampaign = useCallback((id: string, updates: Partial<EmailCampaign>) => {
    return updateCampaignMutation.mutateAsync({ id, updates })
  }, [updateCampaignMutation])

  const pauseCampaign = useCallback((id: string) => {
    return pauseCampaignMutation.mutateAsync(id)
  }, [pauseCampaignMutation])

  const resumeCampaign = useCallback((id: string) => {
    return resumeCampaignMutation.mutateAsync(id)
  }, [resumeCampaignMutation])

  // Calculate aggregate metrics
  const getAggregateMetrics = useCallback(() => {
    if (!campaigns) return null

    const totals = campaigns.reduce((acc, campaign) => ({
      sent: acc.sent + campaign.metrics.sent,
      opened: acc.opened + campaign.metrics.opened,
      clicked: acc.clicked + campaign.metrics.clicked,
      bounced: acc.bounced + campaign.metrics.bounced,
      unsubscribed: acc.unsubscribed + campaign.metrics.unsubscribed
    }), { sent: 0, opened: 0, clicked: 0, bounced: 0, unsubscribed: 0 })

    return {
      ...totals,
      openRate: totals.sent > 0 ? (totals.opened / totals.sent) * 100 : 0,
      clickRate: totals.opened > 0 ? (totals.clicked / totals.opened) * 100 : 0,
      unsubscribeRate: totals.sent > 0 ? (totals.unsubscribed / totals.sent) * 100 : 0
    }
  }, [campaigns])

  const getCampaignsByStatus = useCallback((status: string) => {
    return campaigns?.filter(campaign => campaign.status === status) || []
  }, [campaigns])

  return {
    campaigns,
    isLoading,
    error,
    refetch,
    createCampaign,
    updateCampaign,
    pauseCampaign,
    resumeCampaign,
    getAggregateMetrics,
    getCampaignsByStatus,
    isCreating: createCampaignMutation.isPending,
    isUpdating: updateCampaignMutation.isPending,
    isPausing: pauseCampaignMutation.isPending,
    isResuming: resumeCampaignMutation.isPending
  }
}

// SMS Campaigns Hook
export function useSMSCampaigns() {
  const queryClient = useQueryClient()

  const {
    data: campaigns,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['sms-campaigns'],
    queryFn: Epic3Service.communication.getSMSCampaigns,
    staleTime: 2 * 60 * 1000,
    gcTime: 10 * 60 * 1000
  })

  const createCampaignMutation = useMutation({
    mutationFn: Epic3Service.communication.createSMSCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sms-campaigns'] })
    }
  })

  const updateCampaignMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<SMSCampaign> }) =>
      Epic3Service.communication.updateSMSCampaign(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sms-campaigns'] })
    }
  })

  const createCampaign = useCallback((campaign: Partial<SMSCampaign>) => {
    return createCampaignMutation.mutateAsync(campaign)
  }, [createCampaignMutation])

  const updateCampaign = useCallback((id: string, updates: Partial<SMSCampaign>) => {
    return updateCampaignMutation.mutateAsync({ id, updates })
  }, [updateCampaignMutation])

  const getAggregateMetrics = useCallback(() => {
    if (!campaigns) return null

    const totals = campaigns.reduce((acc, campaign) => ({
      sent: acc.sent + campaign.metrics.sent,
      delivered: acc.delivered + campaign.metrics.delivered,
      failed: acc.failed + campaign.metrics.failed,
      replied: acc.replied + campaign.metrics.replied
    }), { sent: 0, delivered: 0, failed: 0, replied: 0 })

    return {
      ...totals,
      deliveryRate: totals.sent > 0 ? (totals.delivered / totals.sent) * 100 : 0,
      responseRate: totals.delivered > 0 ? (totals.replied / totals.delivered) * 100 : 0,
      failureRate: totals.sent > 0 ? (totals.failed / totals.sent) * 100 : 0
    }
  }, [campaigns])

  return {
    campaigns,
    isLoading,
    error,
    refetch,
    createCampaign,
    updateCampaign,
    getAggregateMetrics,
    isCreating: createCampaignMutation.isPending,
    isUpdating: updateCampaignMutation.isPending
  }
}

// Communication Workflows Hook
export function useCommunicationWorkflows() {
  const queryClient = useQueryClient()

  const {
    data: workflows,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['communication-workflows'],
    queryFn: Epic3Service.communication.getWorkflows,
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000
  })

  const createWorkflowMutation = useMutation({
    mutationFn: Epic3Service.communication.createWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication-workflows'] })
    }
  })

  const updateWorkflowMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<CommunicationWorkflow> }) =>
      Epic3Service.communication.updateWorkflow(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['communication-workflows'] })
    }
  })

  const triggerWorkflowMutation = useMutation({
    mutationFn: ({ workflowId, leadId, context }: { 
      workflowId: string; 
      leadId: string; 
      context?: any 
    }) => Epic3Service.communication.triggerWorkflow(workflowId, leadId, context)
  })

  const createWorkflow = useCallback((workflow: Partial<CommunicationWorkflow>) => {
    return createWorkflowMutation.mutateAsync(workflow)
  }, [createWorkflowMutation])

  const updateWorkflow = useCallback((id: string, updates: Partial<CommunicationWorkflow>) => {
    return updateWorkflowMutation.mutateAsync({ id, updates })
  }, [updateWorkflowMutation])

  const triggerWorkflow = useCallback((workflowId: string, leadId: string, context?: any) => {
    return triggerWorkflowMutation.mutateAsync({ workflowId, leadId, context })
  }, [triggerWorkflowMutation])

  const getWorkflowsByTrigger = useCallback((triggerType: string) => {
    return workflows?.filter(workflow => workflow.triggerType === triggerType) || []
  }, [workflows])

  const getActiveWorkflows = useCallback(() => {
    return workflows?.filter(workflow => workflow.active) || []
  }, [workflows])

  const getWorkflowMetrics = useCallback(() => {
    if (!workflows) return null

    const totals = workflows.reduce((acc, workflow) => ({
      triggered: acc.triggered + workflow.metrics.triggered,
      completed: acc.completed + workflow.metrics.completed,
      abandoned: acc.abandoned + workflow.metrics.abandoned
    }), { triggered: 0, completed: 0, abandoned: 0 })

    return {
      ...totals,
      completionRate: totals.triggered > 0 ? (totals.completed / totals.triggered) * 100 : 0,
      abandonmentRate: totals.triggered > 0 ? (totals.abandoned / totals.triggered) * 100 : 0
    }
  }, [workflows])

  return {
    workflows,
    isLoading,
    error,
    refetch,
    createWorkflow,
    updateWorkflow,
    triggerWorkflow,
    getWorkflowsByTrigger,
    getActiveWorkflows,
    getWorkflowMetrics,
    isCreating: createWorkflowMutation.isPending,
    isUpdating: updateWorkflowMutation.isPending,
    isTriggering: triggerWorkflowMutation.isPending
  }
}

// Personalization Hook
export function usePersonalization() {
  const queryClient = useQueryClient()

  const {
    data: rules,
    isLoading: isLoadingRules,
    error: rulesError
  } = useQuery({
    queryKey: ['personalization-rules'],
    queryFn: Epic3Service.communication.getPersonalizationRules,
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000
  })

  const {
    data: optimalTimes,
    isLoading: isLoadingTimes,
    error: timesError
  } = useQuery({
    queryKey: ['optimal-send-times'],
    queryFn: () => Epic3Service.communication.getOptimalSendTimes(),
    staleTime: 60 * 60 * 1000, // 1 hour
    gcTime: 4 * 60 * 60 * 1000 // 4 hours
  })

  const updateRulesMutation = useMutation({
    mutationFn: Epic3Service.communication.updatePersonalizationRules,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['personalization-rules'] })
    }
  })

  const updateRules = useCallback((newRules: any) => {
    return updateRulesMutation.mutateAsync(newRules)
  }, [updateRulesMutation])

  const generatePersonalizedContent = useCallback((template: string, leadData: any) => {
    if (!rules || !Array.isArray(rules)) return template

    let personalizedContent = template

    // Apply personalization rules
    rules.forEach((rule: any) => {
      const placeholder = `{${rule.field}}`
      const value = leadData[rule.field]
      
      if (value && personalizedContent.includes(placeholder)) {
        personalizedContent = personalizedContent.replace(
          new RegExp(placeholder, 'g'), 
          value
        )
      }
    })

    return personalizedContent
  }, [rules])

  const getOptimalSendTime = useCallback((channel: 'email' | 'sms', timezone?: string) => {
    if (!optimalTimes || !Array.isArray(optimalTimes)) return null

    return optimalTimes.find((time: any) => 
      time.channel === channel && 
      (!timezone || time.timezone === timezone)
    )
  }, [optimalTimes])

  return {
    rules,
    optimalTimes,
    isLoadingRules,
    isLoadingTimes,
    rulesError,
    timesError,
    updateRules,
    generatePersonalizedContent,
    getOptimalSendTime,
    isUpdatingRules: updateRulesMutation.isPending
  }
}

// Communication Analytics Hook
export function useCommunicationAnalytics(timeframe: string = '30d') {
  const { campaigns: emailCampaigns, getAggregateMetrics: getEmailMetrics } = useEmailCampaigns()
  const { campaigns: smsCampaigns, getAggregateMetrics: getSMSMetrics } = useSMSCampaigns()
  const { workflows, getWorkflowMetrics } = useCommunicationWorkflows()

  const [analytics, setAnalytics] = useState<any>(null)

  useEffect(() => {
    if (emailCampaigns && smsCampaigns && workflows) {
      const emailMetrics = getEmailMetrics()
      const smsMetrics = getSMSMetrics()
      const workflowMetrics = getWorkflowMetrics()

      setAnalytics({
        email: emailMetrics,
        sms: smsMetrics,
        workflows: workflowMetrics,
        overview: {
          totalMessages: (emailMetrics?.sent || 0) + (smsMetrics?.sent || 0),
          totalEngagements: (emailMetrics?.clicked || 0) + (smsMetrics?.replied || 0),
          totalUnsubscribed: emailMetrics?.unsubscribed || 0,
          engagementRate: calculateOverallEngagementRate(emailMetrics, smsMetrics)
        }
      })
    }
  }, [emailCampaigns, smsCampaigns, workflows, getEmailMetrics, getSMSMetrics, getWorkflowMetrics])

  const calculateOverallEngagementRate = useCallback((emailMetrics: any, smsMetrics: any) => {
    const totalSent = (emailMetrics?.sent || 0) + (smsMetrics?.sent || 0)
    const totalEngagements = (emailMetrics?.clicked || 0) + (smsMetrics?.replied || 0)
    
    return totalSent > 0 ? (totalEngagements / totalSent) * 100 : 0
  }, [])

  const getTopPerformingCampaigns = useCallback((limit: number = 5) => {
    if (!emailCampaigns && !smsCampaigns) return []

    const allCampaigns = [
      ...(emailCampaigns || []).map(c => ({
        ...c,
        type: 'email',
        engagementRate: c.metrics.sent > 0 ? (c.metrics.clicked / c.metrics.sent) * 100 : 0
      })),
      ...(smsCampaigns || []).map(c => ({
        ...c,
        type: 'sms',
        engagementRate: c.metrics.sent > 0 ? (c.metrics.replied / c.metrics.sent) * 100 : 0
      }))
    ]

    return allCampaigns
      .sort((a, b) => b.engagementRate - a.engagementRate)
      .slice(0, limit)
  }, [emailCampaigns, smsCampaigns])

  const getChannelComparison = useCallback(() => {
    const emailMetrics = getEmailMetrics()
    const smsMetrics = getSMSMetrics()

    if (!emailMetrics || !smsMetrics) return null

    return {
      email: {
        sent: emailMetrics.sent,
        engagementRate: emailMetrics.clickRate,
        unsubscribeRate: emailMetrics.unsubscribeRate
      },
      sms: {
        sent: smsMetrics.sent,
        engagementRate: smsMetrics.responseRate,
        deliveryRate: smsMetrics.deliveryRate
      }
    }
  }, [getEmailMetrics, getSMSMetrics])

  return {
    analytics,
    getTopPerformingCampaigns,
    getChannelComparison,
    isLoading: !analytics,
    hasData: !!analytics
  }
}