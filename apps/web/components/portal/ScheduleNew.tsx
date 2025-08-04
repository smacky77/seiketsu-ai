'use client'

// New appointment booking interface
export default function ScheduleNew({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-background bg-opacity-90 flex items-center justify-center z-50">
      <div className="bg-card border border-border rounded-lg p-6 max-w-md w-full mx-4">
        <div className="text-center">
          <div className="text-4xl mb-4">📅</div>
          <h3 className="text-lg font-medium text-foreground mb-2">
            Schedule New Appointment
          </h3>
          <p className="text-muted-foreground mb-6">
            Advanced scheduling interface coming soon
          </p>
          
          <div className="flex space-x-3">
            <button onClick={onClose} className="btn btn-secondary flex-1">
              Close
            </button>
            <button className="btn btn-primary flex-1">
              Coming Soon
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}