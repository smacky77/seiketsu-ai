'use client'

// Multi-channel communication options
export default function ContactMethods({ compact = false }: { compact?: boolean }) {
  const contactOptions = [
    { icon: '📞', label: 'Call', method: 'phone', available: true },
    { icon: '💬', label: 'Text', method: 'sms', available: true },
    { icon: '✉️', label: 'Email', method: 'email', available: true },
    { icon: '📹', label: 'Video', method: 'video', available: false }
  ]
  
  if (compact) {
    return (
      <div className="flex space-x-2">
        {contactOptions.filter(opt => opt.available).map((option) => (
          <button
            key={option.method}
            className="btn btn-secondary text-sm px-3"
            title={option.label}
          >
            {option.icon}
          </button>
        ))}
      </div>
    )
  }
  
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h3 className="text-lg font-medium text-foreground mb-4">Contact Methods</h3>
      <div className="grid grid-cols-2 gap-3">
        {contactOptions.map((option) => (
          <button
            key={option.method}
            disabled={!option.available}
            className={`p-3 rounded-lg text-left transition-colors ${
              option.available
                ? 'bg-muted hover:bg-accent text-foreground'
                : 'bg-muted opacity-50 cursor-not-allowed text-muted-foreground'
            }`}
          >
            <div className="text-xl mb-1">{option.icon}</div>
            <div className="text-sm font-medium">{option.label}</div>
            {!option.available && (
              <div className="text-xs opacity-75">Coming Soon</div>
            )}
          </button>
        ))}
      </div>
    </div>
  )
}