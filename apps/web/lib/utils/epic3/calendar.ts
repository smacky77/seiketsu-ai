// Calendar Integration Utilities

export interface CalendarEvent {
  id: string
  title: string
  start: Date
  end: Date
  description?: string
  location?: string
  attendees?: string[]
  recurring?: boolean
  recurrenceRule?: string
}

export interface CalendarProvider {
  id: string
  name: string
  authUrl: string
  scopes: string[]
  clientId: string
}

export class CalendarManager {
  private static instance: CalendarManager
  private providers: Map<string, CalendarProvider> = new Map()
  private connections: Map<string, any> = new Map()

  private constructor() {
    this.initializeProviders()
  }

  static getInstance(): CalendarManager {
    if (!CalendarManager.instance) {
      CalendarManager.instance = new CalendarManager()
    }
    return CalendarManager.instance
  }

  private initializeProviders() {
    // Google Calendar
    this.providers.set('google', {
      id: 'google',
      name: 'Google Calendar',
      authUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
      scopes: ['https://www.googleapis.com/auth/calendar'],
      clientId: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ''
    })

    // Microsoft Outlook
    this.providers.set('outlook', {
      id: 'outlook',
      name: 'Microsoft Outlook',
      authUrl: 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
      scopes: ['https://graph.microsoft.com/calendars.readwrite'],
      clientId: process.env.NEXT_PUBLIC_OUTLOOK_CLIENT_ID || ''
    })

    // Apple Calendar (CalDAV)
    this.providers.set('apple', {
      id: 'apple',
      name: 'Apple Calendar',
      authUrl: 'caldav://icloud.com',
      scopes: ['calendar.read', 'calendar.write'],
      clientId: ''
    })
  }

  getProvider(providerId: string): CalendarProvider | undefined {
    return this.providers.get(providerId)
  }

  getAllProviders(): CalendarProvider[] {
    return Array.from(this.providers.values())
  }

  async connectProvider(providerId: string, credentials: any): Promise<boolean> {
    try {
      const provider = this.getProvider(providerId)
      if (!provider) {
        throw new Error(`Provider ${providerId} not found`)
      }

      // Store connection details (in real implementation, these would be encrypted)
      this.connections.set(providerId, {
        provider,
        credentials,
        connectedAt: new Date(),
        status: 'connected'
      })

      return true
    } catch (error) {
      console.error(`Failed to connect to ${providerId}:`, error)
      return false
    }
  }

  isConnected(providerId: string): boolean {
    const connection = this.connections.get(providerId)
    return connection && connection.status === 'connected'
  }

  async disconnectProvider(providerId: string): Promise<boolean> {
    try {
      this.connections.delete(providerId)
      return true
    } catch (error) {
      console.error(`Failed to disconnect from ${providerId}:`, error)
      return false
    }
  }

  async syncEvents(providerId: string, startDate: Date, endDate: Date): Promise<CalendarEvent[]> {
    try {
      if (!this.isConnected(providerId)) {
        throw new Error(`Not connected to ${providerId}`)
      }

      // Mock event sync - in real implementation, this would call the actual APIs
      const mockEvents: CalendarEvent[] = [
        {
          id: `${providerId}-1`,
          title: 'Team Meeting',
          start: new Date(startDate.getTime() + 2 * 60 * 60 * 1000), // +2 hours
          end: new Date(startDate.getTime() + 3 * 60 * 60 * 1000), // +3 hours
          description: 'Weekly team sync',
          location: 'Conference Room A'
        },
        {
          id: `${providerId}-2`,
          title: 'Client Call',
          start: new Date(startDate.getTime() + 24 * 60 * 60 * 1000 + 10 * 60 * 60 * 1000), // Next day +10 hours
          end: new Date(startDate.getTime() + 24 * 60 * 60 * 1000 + 11 * 60 * 60 * 1000), // Next day +11 hours
          description: 'Property consultation',
          attendees: ['client@email.com']
        }
      ]

      return mockEvents
    } catch (error) {
      console.error(`Failed to sync events from ${providerId}:`, error)
      return []
    }
  }

  async createEvent(providerId: string, event: Omit<CalendarEvent, 'id'>): Promise<string | null> {
    try {
      if (!this.isConnected(providerId)) {
        throw new Error(`Not connected to ${providerId}`)
      }

      // Mock event creation - return generated ID
      const eventId = `${providerId}-${Date.now()}`
      console.log(`Created event ${eventId} in ${providerId}:`, event)
      
      return eventId
    } catch (error) {
      console.error(`Failed to create event in ${providerId}:`, error)
      return null
    }
  }

  async updateEvent(providerId: string, eventId: string, updates: Partial<CalendarEvent>): Promise<boolean> {
    try {
      if (!this.isConnected(providerId)) {
        throw new Error(`Not connected to ${providerId}`)
      }

      console.log(`Updated event ${eventId} in ${providerId}:`, updates)
      return true
    } catch (error) {
      console.error(`Failed to update event ${eventId} in ${providerId}:`, error)
      return false
    }
  }

  async deleteEvent(providerId: string, eventId: string): Promise<boolean> {
    try {
      if (!this.isConnected(providerId)) {
        throw new Error(`Not connected to ${providerId}`)
      }

      console.log(`Deleted event ${eventId} from ${providerId}`)
      return true
    } catch (error) {
      console.error(`Failed to delete event ${eventId} from ${providerId}:`, error)
      return false
    }
  }

  // Utility methods
  formatEventForCalendar(appointment: any): Omit<CalendarEvent, 'id'> {
    return {
      title: `${appointment.appointmentType.replace('_', ' ')} - ${appointment.clientName}`,
      start: new Date(appointment.scheduledTime),
      end: new Date(appointment.scheduledTime.getTime() + appointment.duration * 60 * 1000),
      description: `Appointment with ${appointment.clientName}\nPhone: ${appointment.clientPhone}\nEmail: ${appointment.clientEmail}${appointment.propertyAddress ? `\nProperty: ${appointment.propertyAddress}` : ''}${appointment.notes ? `\nNotes: ${appointment.notes}` : ''}`,
      location: appointment.propertyAddress || 'Office',
      attendees: [appointment.clientEmail]
    }
  }

  generateICalString(event: CalendarEvent): string {
    const formatDate = (date: Date): string => {
      return date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')
    }

    const lines = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//Seiketsu AI//Epic 3 Scheduling//EN',
      'BEGIN:VEVENT',
      `UID:${event.id}`,
      `DTSTART:${formatDate(event.start)}`,
      `DTEND:${formatDate(event.end)}`,
      `SUMMARY:${event.title}`,
      event.description ? `DESCRIPTION:${event.description.replace(/\n/g, '\\n')}` : '',
      event.location ? `LOCATION:${event.location}` : '',
      'END:VEVENT',
      'END:VCALENDAR'
    ].filter(Boolean)

    return lines.join('\r\n')
  }

  findConflicts(events: CalendarEvent[], newEvent: Omit<CalendarEvent, 'id'>): CalendarEvent[] {
    return events.filter(event => {
      const eventStart = new Date(event.start)
      const eventEnd = new Date(event.end)
      const newStart = new Date(newEvent.start)
      const newEnd = new Date(newEvent.end)

      // Check for overlap
      return (newStart < eventEnd && newEnd > eventStart)
    })
  }

  suggestAlternativeTimes(
    conflicts: CalendarEvent[], 
    preferredTime: Date, 
    duration: number, 
    workingHours: { start: string; end: string }
  ): Date[] {
    const suggestions: Date[] = []
    const [workStart, workEnd] = [
      parseInt(workingHours.start.split(':')[0]),
      parseInt(workingHours.end.split(':')[0])
    ]

    // Try slots before and after the preferred time
    const baseDate = new Date(preferredTime)
    baseDate.setMinutes(0, 0, 0) // Round to nearest hour

    for (let hourOffset = -4; hourOffset <= 4; hourOffset++) {
      if (hourOffset === 0) continue // Skip the original time

      const suggestedTime = new Date(baseDate.getTime() + hourOffset * 60 * 60 * 1000)
      const suggestedHour = suggestedTime.getHours()

      // Check if within working hours
      if (suggestedHour < workStart || suggestedHour > workEnd - 2) continue

      // Check for conflicts
      const hasConflict = conflicts.some(conflict => {
        const conflictStart = new Date(conflict.start)
        const conflictEnd = new Date(conflict.end)
        const suggestedEnd = new Date(suggestedTime.getTime() + duration * 60 * 1000)

        return (suggestedTime < conflictEnd && suggestedEnd > conflictStart)
      })

      if (!hasConflict) {
        suggestions.push(suggestedTime)
      }

      if (suggestions.length >= 3) break
    }

    return suggestions.sort((a, b) => {
      // Sort by proximity to original time
      const aDiff = Math.abs(a.getTime() - preferredTime.getTime())
      const bDiff = Math.abs(b.getTime() - preferredTime.getTime())
      return aDiff - bDiff
    })
  }
}

// Timezone utilities
export class TimezoneManager {
  private static readonly commonTimezones = [
    { id: 'America/New_York', name: 'Eastern Time', offset: -5 },
    { id: 'America/Chicago', name: 'Central Time', offset: -6 },
    { id: 'America/Denver', name: 'Mountain Time', offset: -7 },
    { id: 'America/Los_Angeles', name: 'Pacific Time', offset: -8 },
    { id: 'America/Phoenix', name: 'Arizona Time', offset: -7 },
    { id: 'America/Anchorage', name: 'Alaska Time', offset: -9 },
    { id: 'Pacific/Honolulu', name: 'Hawaii Time', offset: -10 },
    { id: 'UTC', name: 'UTC', offset: 0 }
  ]

  static getCommonTimezones() {
    return this.commonTimezones
  }

  static convertToTimezone(date: Date, timezone: string): Date {
    try {
      return new Date(date.toLocaleString('en-US', { timeZone: timezone }))
    } catch (error) {
      console.error(`Invalid timezone: ${timezone}`, error)
      return date
    }
  }

  static formatForTimezone(date: Date, timezone: string, format: string = 'short'): string {
    try {
      const options: Intl.DateTimeFormatOptions = {
        timeZone: timezone,
        year: 'numeric',
        month: format === 'long' ? 'long' : 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      }

      return date.toLocaleString('en-US', options)
    } catch (error) {
      console.error(`Error formatting date for timezone ${timezone}:`, error)
      return date.toLocaleString()
    }
  }

  static getTimezoneOffset(timezone: string): number {
    try {
      const now = new Date()
      const utc = new Date(now.getTime() + now.getTimezoneOffset() * 60000)
      const target = new Date(utc.toLocaleString('en-US', { timeZone: timezone }))
      return (target.getTime() - utc.getTime()) / (1000 * 60 * 60)
    } catch (error) {
      console.error(`Error getting timezone offset for ${timezone}:`, error)
      return 0
    }
  }

  static detectUserTimezone(): string {
    return Intl.DateTimeFormat().resolvedOptions().timeZone
  }
}

// Working hours and availability utilities
export class ScheduleManager {
  static parseWorkingHours(workingHours: string): { start: number; end: number } {
    const [start, end] = workingHours.split('-').map(time => {
      const [hour, minute] = time.trim().split(':').map(Number)
      return hour + minute / 60
    })
    return { start, end }
  }

  static generateTimeSlots(
    startHour: number,
    endHour: number,
    duration: number = 60,
    buffer: number = 0
  ): string[] {
    const slots: string[] = []
    const totalDuration = duration + buffer

    for (let hour = startHour; hour < endHour; hour += totalDuration / 60) {
      const wholeHour = Math.floor(hour)
      const minutes = Math.round((hour - wholeHour) * 60)
      
      if (wholeHour + totalDuration / 60 <= endHour) {
        slots.push(`${wholeHour.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`)
      }
    }

    return slots
  }

  static isWithinWorkingHours(time: Date, workingHours: { start: string; end: string }): boolean {
    const hour = time.getHours() + time.getMinutes() / 60
    const start = parseFloat(workingHours.start.replace(':', '.'))
    const end = parseFloat(workingHours.end.replace(':', '.'))
    
    return hour >= start && hour <= end
  }

  static calculateTravelTime(from: string, to: string): Promise<number> {
    // Mock implementation - in reality, integrate with Google Maps API
    return new Promise((resolve) => {
      setTimeout(() => {
        const distance = Math.random() * 30 // Random distance up to 30 miles
        const travelTime = Math.max(15, distance * 2) // Minimum 15 minutes
        resolve(Math.round(travelTime))
      }, 100)
    })
  }

  static optimizeAppointmentOrder(appointments: any[]): any[] {
    // Simple optimization by location proximity (mock implementation)
    return appointments.sort((a, b) => {
      // In reality, this would use actual location data and routing
      const aLocation = a.propertyAddress || 'office'
      const bLocation = b.propertyAddress || 'office'
      return aLocation.localeCompare(bLocation)
    })
  }
}

// Recurrence pattern utilities
export class RecurrenceManager {
  static parseRecurrenceRule(rrule: string): any {
    const parts = rrule.split(';')
    const rule: any = {}

    parts.forEach(part => {
      const [key, value] = part.split('=')
      rule[key] = value
    })

    return rule
  }

  static generateRecurrentDates(
    startDate: Date,
    recurrenceRule: string,
    count: number = 10
  ): Date[] {
    const rule = this.parseRecurrenceRule(recurrenceRule)
    const dates: Date[] = []

    if (rule.FREQ === 'DAILY') {
      const interval = parseInt(rule.INTERVAL || '1')
      for (let i = 0; i < count; i++) {
        const date = new Date(startDate)
        date.setDate(startDate.getDate() + i * interval)
        dates.push(date)
      }
    } else if (rule.FREQ === 'WEEKLY') {
      const interval = parseInt(rule.INTERVAL || '1')
      for (let i = 0; i < count; i++) {
        const date = new Date(startDate)
        date.setDate(startDate.getDate() + i * interval * 7)
        dates.push(date)
      }
    } else if (rule.FREQ === 'MONTHLY') {
      const interval = parseInt(rule.INTERVAL || '1')
      for (let i = 0; i < count; i++) {
        const date = new Date(startDate)
        date.setMonth(startDate.getMonth() + i * interval)
        dates.push(date)
      }
    }

    return dates
  }

  static createRecurrenceRule(pattern: {
    frequency: 'DAILY' | 'WEEKLY' | 'MONTHLY' | 'YEARLY'
    interval: number
    count?: number
    until?: Date
    byDay?: string[]
  }): string {
    const parts = [`FREQ=${pattern.frequency}`]

    if (pattern.interval > 1) {
      parts.push(`INTERVAL=${pattern.interval}`)
    }

    if (pattern.count) {
      parts.push(`COUNT=${pattern.count}`)
    }

    if (pattern.until) {
      const until = pattern.until.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')
      parts.push(`UNTIL=${until}`)
    }

    if (pattern.byDay && pattern.byDay.length > 0) {
      parts.push(`BYDAY=${pattern.byDay.join(',')}`)
    }

    return parts.join(';')
  }
}

// Export singleton instance
export const calendarManager = CalendarManager.getInstance()