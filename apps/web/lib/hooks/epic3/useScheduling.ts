'use client'

import { useState, useCallback, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Epic3Service } from '@/lib/api/services/epic3.service'
import { 
  SchedulingAvailability,
  TimeSlot,
  AppointmentBookingRequest,
  AppointmentReminder
} from '@/lib/api/services/epic3.service'

// Agent Availability Hook
export function useAgentAvailability(agentId: string, dateRange?: { start: string; end: string }) {
  const queryClient = useQueryClient()

  const {
    data: availability,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['agent-availability', agentId, dateRange],
    queryFn: () => Epic3Service.scheduling.getAgentAvailability(
      agentId, 
      dateRange?.start || new Date().toISOString().split('T')[0],
      dateRange?.end || new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    ),
    enabled: !!agentId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 15 * 60 * 1000 // 15 minutes
  })

  const updateAvailabilityMutation = useMutation({
    mutationFn: ({ agentId, availability }: { 
      agentId: string; 
      availability: Partial<SchedulingAvailability> 
    }) => Epic3Service.scheduling.updateAgentAvailability(agentId, availability),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-availability'] })
    }
  })

  const updateAvailability = useCallback((updates: Partial<SchedulingAvailability>) => {
    return updateAvailabilityMutation.mutateAsync({ agentId, availability: updates })
  }, [agentId, updateAvailabilityMutation])

  const getAvailableSlots = useCallback((date: string, duration: number = 60) => {
    const dayAvailability = availability?.find(a => a.date === date)
    return dayAvailability?.timeSlots.filter(slot => slot.available) || []
  }, [availability])

  const getBookedSlots = useCallback((date: string) => {
    const dayAvailability = availability?.find(a => a.date === date)
    return dayAvailability?.timeSlots.filter(slot => !slot.available) || []
  }, [availability])

  const getTotalAvailableHours = useCallback((date?: string) => {
    let slotsToCheck = availability || []
    
    if (date) {
      slotsToCheck = availability?.filter(a => a.date === date) || []
    }

    return slotsToCheck.reduce((total, day) => {
      const availableSlots = day.timeSlots.filter(slot => slot.available)
      const hours = availableSlots.reduce((dayTotal, slot) => {
        const start = new Date(`2000-01-01T${slot.startTime}`)
        const end = new Date(`2000-01-01T${slot.endTime}`)
        return dayTotal + (end.getTime() - start.getTime()) / (1000 * 60 * 60)
      }, 0)
      return total + hours
    }, 0)
  }, [availability])

  return {
    availability,
    isLoading,
    error,
    refetch,
    updateAvailability,
    getAvailableSlots,
    getBookedSlots,
    getTotalAvailableHours,
    isUpdating: updateAvailabilityMutation.isPending
  }
}

// Available Time Slots Hook
export function useAvailableTimeSlots(agentId: string, date: string, duration: number = 60) {
  const {
    data: timeSlots,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['available-time-slots', agentId, date, duration],
    queryFn: () => Epic3Service.scheduling.getAvailableTimeSlots(agentId, date, duration),
    enabled: !!(agentId && date),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000 // 10 minutes
  })

  const getSlotsByTimeOfDay = useCallback(() => {
    if (!timeSlots) return { morning: [], afternoon: [], evening: [] }

    return timeSlots.reduce((groups, slot) => {
      const hour = parseInt(slot.startTime.split(':')[0])
      if (hour < 12) {
        groups.morning.push(slot)
      } else if (hour < 17) {
        groups.afternoon.push(slot)
      } else {
        groups.evening.push(slot)
      }
      return groups
    }, { morning: [] as TimeSlot[], afternoon: [] as TimeSlot[], evening: [] as TimeSlot[] })
  }, [timeSlots])

  const getNextAvailableSlot = useCallback(() => {
    return timeSlots?.[0] || null
  }, [timeSlots])

  return {
    timeSlots,
    isLoading,
    error,
    refetch,
    getSlotsByTimeOfDay,
    getNextAvailableSlot,
    hasAvailableSlots: !!(timeSlots && timeSlots.length > 0)
  }
}

// Appointment Management Hook
export function useAppointments(filters?: {
  agentId?: string
  startDate?: string
  endDate?: string
  status?: string
}) {
  const queryClient = useQueryClient()

  const {
    data: appointments,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['appointments', filters],
    queryFn: () => Epic3Service.scheduling.getAppointments(
      filters?.agentId,
      filters?.startDate,
      filters?.endDate
    ),
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000 // 5 minutes
  })

  const bookAppointmentMutation = useMutation({
    mutationFn: Epic3Service.scheduling.bookAppointment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      queryClient.invalidateQueries({ queryKey: ['agent-availability'] })
      queryClient.invalidateQueries({ queryKey: ['available-time-slots'] })
    }
  })

  const updateAppointmentMutation = useMutation({
    mutationFn: ({ appointmentId, updates }: { 
      appointmentId: string; 
      updates: any 
    }) => Epic3Service.scheduling.updateAppointment(appointmentId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
    }
  })

  const cancelAppointmentMutation = useMutation({
    mutationFn: ({ appointmentId, reason }: { 
      appointmentId: string; 
      reason?: string 
    }) => Epic3Service.scheduling.cancelAppointment(appointmentId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      queryClient.invalidateQueries({ queryKey: ['agent-availability'] })
      queryClient.invalidateQueries({ queryKey: ['available-time-slots'] })
    }
  })

  const bookAppointment = useCallback((booking: AppointmentBookingRequest) => {
    return bookAppointmentMutation.mutateAsync(booking)
  }, [bookAppointmentMutation])

  const updateAppointment = useCallback((appointmentId: string, updates: any) => {
    return updateAppointmentMutation.mutateAsync({ appointmentId, updates })
  }, [updateAppointmentMutation])

  const cancelAppointment = useCallback((appointmentId: string, reason?: string) => {
    return cancelAppointmentMutation.mutateAsync({ appointmentId, reason })
  }, [cancelAppointmentMutation])

  const getAppointmentsByStatus = useCallback((status: string) => {
    return appointments && Array.isArray(appointments) 
      ? appointments.filter(appointment => appointment.status === status) 
      : []
  }, [appointments])

  const getUpcomingAppointments = useCallback((limit?: number) => {
    const upcoming = appointments && Array.isArray(appointments)
      ? appointments.filter(appointment => 
          new Date(appointment.scheduledTime) > new Date() &&
          appointment.status !== 'cancelled'
        ).sort((a, b) => 
          new Date(a.scheduledTime).getTime() - new Date(b.scheduledTime).getTime()
        )
      : []

    return limit ? upcoming.slice(0, limit) : upcoming
  }, [appointments])

  const getTodayAppointments = useCallback(() => {
    const today = new Date().toISOString().split('T')[0]
    return appointments && Array.isArray(appointments)
      ? appointments.filter(appointment => 
          appointment.scheduledTime.toISOString().split('T')[0] === today &&
          appointment.status !== 'cancelled'
        )
      : []
  }, [appointments])

  const getAppointmentMetrics = useCallback(() => {
    if (!appointments || !Array.isArray(appointments)) return null

    const total = appointments.length
    const completed = appointments.filter(a => a.status === 'completed').length
    const cancelled = appointments.filter(a => a.status === 'cancelled').length
    const noShow = appointments.filter(a => a.status === 'no_show').length

    return {
      total,
      completed,
      cancelled,
      noShow,
      completionRate: total > 0 ? (completed / total) * 100 : 0,
      cancellationRate: total > 0 ? (cancelled / total) * 100 : 0,
      noShowRate: total > 0 ? (noShow / total) * 100 : 0
    }
  }, [appointments])

  return {
    appointments,
    isLoading,
    error,
    refetch,
    bookAppointment,
    updateAppointment,
    cancelAppointment,
    getAppointmentsByStatus,
    getUpcomingAppointments,
    getTodayAppointments,
    getAppointmentMetrics,
    isBooking: bookAppointmentMutation.isPending,
    isUpdating: updateAppointmentMutation.isPending,
    isCancelling: cancelAppointmentMutation.isPending
  }
}

// Appointment Reminders Hook
export function useAppointmentReminders(appointmentId?: string) {
  const queryClient = useQueryClient()

  const {
    data: reminders,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['appointment-reminders', appointmentId],
    queryFn: () => Epic3Service.scheduling.getReminders(appointmentId),
    staleTime: 2 * 60 * 1000,
    gcTime: 10 * 60 * 1000
  })

  const scheduleReminderMutation = useMutation({
    mutationFn: Epic3Service.scheduling.scheduleReminder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointment-reminders'] })
    }
  })

  const updateReminderSettingsMutation = useMutation({
    mutationFn: Epic3Service.scheduling.updateReminderSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointment-reminders'] })
    }
  })

  const scheduleReminder = useCallback((reminder: Omit<AppointmentReminder, 'status'>) => {
    return scheduleReminderMutation.mutateAsync(reminder)
  }, [scheduleReminderMutation])

  const updateReminderSettings = useCallback((settings: any) => {
    return updateReminderSettingsMutation.mutateAsync(settings)
  }, [updateReminderSettingsMutation])

  const getRemindersByType = useCallback((type: string) => {
    return reminders?.filter(reminder => reminder.reminderType === type) || []
  }, [reminders])

  const getPendingReminders = useCallback(() => {
    return reminders?.filter(reminder => reminder.status === 'scheduled') || []
  }, [reminders])

  const getFailedReminders = useCallback(() => {
    return reminders?.filter(reminder => reminder.status === 'failed') || []
  }, [reminders])

  return {
    reminders,
    isLoading,
    error,
    refetch,
    scheduleReminder,
    updateReminderSettings,
    getRemindersByType,
    getPendingReminders,
    getFailedReminders,
    isScheduling: scheduleReminderMutation.isPending,
    isUpdatingSettings: updateReminderSettingsMutation.isPending
  }
}

// Calendar Integration Hook
export function useCalendarIntegration(agentId?: string) {
  const queryClient = useQueryClient()

  const {
    data: integrations,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['calendar-integrations', agentId],
    queryFn: Epic3Service.scheduling.getCalendarIntegrations,
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000
  })

  const connectCalendarMutation = useMutation({
    mutationFn: ({ provider, credentials }: { 
      provider: string; 
      credentials: any 
    }) => Epic3Service.scheduling.connectCalendar(provider, credentials),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-integrations'] })
    }
  })

  const syncCalendarMutation = useMutation({
    mutationFn: Epic3Service.scheduling.syncCalendar,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-integrations'] })
      queryClient.invalidateQueries({ queryKey: ['agent-availability'] })
    }
  })

  const disconnectCalendarMutation = useMutation({
    mutationFn: Epic3Service.scheduling.disconnectCalendar,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar-integrations'] })
    }
  })

  const connectCalendar = useCallback((provider: string, credentials: any) => {
    return connectCalendarMutation.mutateAsync({ provider, credentials })
  }, [connectCalendarMutation])

  const syncCalendar = useCallback((integrationId: string) => {
    return syncCalendarMutation.mutateAsync(integrationId)
  }, [syncCalendarMutation])

  const disconnectCalendar = useCallback((integrationId: string) => {
    return disconnectCalendarMutation.mutateAsync(integrationId)
  }, [disconnectCalendarMutation])

  const getConnectedProviders = useCallback(() => {
    return integrations && Array.isArray(integrations)
      ? integrations.filter(integration => integration.connected)
      : []
  }, [integrations])

  const getIntegrationByProvider = useCallback((provider: string) => {
    return integrations && Array.isArray(integrations)
      ? integrations.find(integration => integration.provider === provider)
      : undefined
  }, [integrations])

  const getLastSyncTime = useCallback(() => {
    if (!integrations || !Array.isArray(integrations)) return null
    
    const connected = integrations.filter(i => i.connected)
    if (connected.length === 0) return null

    return connected.reduce((latest, integration) => {
      return integration.lastSync > latest ? integration.lastSync : latest
    }, connected[0].lastSync)
  }, [integrations])

  return {
    integrations,
    isLoading,
    error,
    refetch,
    connectCalendar,
    syncCalendar,
    disconnectCalendar,
    getConnectedProviders,
    getIntegrationByProvider,
    getLastSyncTime,
    isConnecting: connectCalendarMutation.isPending,
    isSyncing: syncCalendarMutation.isPending,
    isDisconnecting: disconnectCalendarMutation.isPending
  }
}

// Smart Scheduling Hook
export function useSmartScheduling() {
  const [suggestions, setSuggestions] = useState<any[]>([])
  const [isGenerating, setIsGenerating] = useState(false)

  const generateSuggestionsMutation = useMutation({
    mutationFn: Epic3Service.scheduling.getSmartSuggestions
  })

  const optimizeScheduleMutation = useMutation({
    mutationFn: ({ agentId, date }: { agentId: string; date: string }) =>
      Epic3Service.scheduling.optimizeSchedule(agentId, date)
  })

  const generateSuggestions = useCallback(async (requirements: any) => {
    setIsGenerating(true)
    try {
      const result = await generateSuggestionsMutation.mutateAsync(requirements)
      setSuggestions(Array.isArray(result) ? result : [])
      return result
    } catch (error) {
      console.error('Error generating suggestions:', error)
      throw error
    } finally {
      setIsGenerating(false)
    }
  }, [generateSuggestionsMutation])

  const optimizeSchedule = useCallback((agentId: string, date: string) => {
    return optimizeScheduleMutation.mutateAsync({ agentId, date })
  }, [optimizeScheduleMutation])

  const getBestSuggestion = useCallback(() => {
    if (!suggestions || suggestions.length === 0) return null
    return suggestions.reduce((best, current) => 
      current.confidence > best.confidence ? current : best
    )
  }, [suggestions])

  const getSuggestionsByAgent = useCallback((agentId: string) => {
    return Array.isArray(suggestions)
      ? suggestions.filter(suggestion => suggestion.agentId === agentId)
      : []
  }, [suggestions])

  return {
    suggestions,
    isGenerating,
    generateSuggestions,
    optimizeSchedule,
    getBestSuggestion,
    getSuggestionsByAgent,
    isOptimizing: optimizeScheduleMutation.isPending
  }
}

// Scheduling Analytics Hook
export function useSchedulingAnalytics(timeframe: string = '30d') {
  const { appointments, getAppointmentMetrics } = useAppointments()
  const [analytics, setAnalytics] = useState<any>(null)

  useEffect(() => {
    if (appointments) {
      const metrics = getAppointmentMetrics()
      
      // Calculate additional analytics
      const now = new Date()
      const timeframeStart = new Date()
      
      switch (timeframe) {
        case '7d':
          timeframeStart.setDate(now.getDate() - 7)
          break
        case '30d':
          timeframeStart.setDate(now.getDate() - 30)
          break
        case '90d':
          timeframeStart.setDate(now.getDate() - 90)
          break
        default:
          timeframeStart.setDate(now.getDate() - 30)
      }

      const periodAppointments = Array.isArray(appointments)
        ? appointments.filter(apt => new Date(apt.scheduledTime) >= timeframeStart)
        : []

      const avgBookingLeadTime = periodAppointments.reduce((sum, apt) => {
        const leadTime = new Date(apt.scheduledTime).getTime() - new Date(apt.createdAt).getTime()
        return sum + (leadTime / (1000 * 60 * 60 * 24)) // Convert to days
      }, 0) / (periodAppointments.length || 1)

      const appointmentsByType = periodAppointments.reduce((acc, apt) => {
        acc[apt.appointmentType] = (acc[apt.appointmentType] || 0) + 1
        return acc
      }, {} as Record<string, number>)

      setAnalytics({
        ...metrics,
        periodAppointments: periodAppointments.length,
        avgBookingLeadTime: Math.round(avgBookingLeadTime * 10) / 10,
        appointmentsByType,
        peakBookingTimes: calculatePeakBookingTimes(periodAppointments),
        agentUtilization: calculateAgentUtilization(periodAppointments)
      })
    }
  }, [appointments, timeframe, getAppointmentMetrics])

  const calculatePeakBookingTimes = useCallback((appointments: any[]) => {
    const hourCounts = appointments.reduce((acc, apt) => {
      const hour = new Date(apt.scheduledTime).getHours()
      acc[hour] = (acc[hour] || 0) + 1
      return acc
    }, {} as Record<number, number>)

    return Object.entries(hourCounts)
      .sort(([,a], [,b]) => (b as number) - (a as number))
      .slice(0, 3)
      .map(([hour, count]) => ({ hour: parseInt(hour), count }))
  }, [])

  const calculateAgentUtilization = useCallback((appointments: any[]) => {
    const agentAppointments = appointments.reduce((acc, apt) => {
      acc[apt.agentId] = (acc[apt.agentId] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    return Object.entries(agentAppointments)
      .map(([agentId, count]) => ({ agentId, appointments: count }))
      .sort((a, b) => (b.appointments as number) - (a.appointments as number))
  }, [])

  return {
    analytics,
    isLoading: !analytics && !!appointments,
    hasData: !!analytics
  }
}