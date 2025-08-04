'use client'

// Calendar-based appointment scheduling interface
export default function AppointmentCalendar() {
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="text-center py-12">
        <div className="text-4xl mb-4">📅</div>
        <h3 className="text-lg font-medium text-foreground mb-2">
          Calendar View
        </h3>
        <p className="text-muted-foreground mb-4">
          Interactive calendar for scheduling appointments
        </p>
        <button className="btn btn-primary">
          Coming Soon
        </button>
      </div>
    </div>
  )
}