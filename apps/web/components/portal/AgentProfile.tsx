'use client'

// Agent profile and information display
export default function AgentProfile() {
  return (
    <div className="space-y-6">
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="text-center py-12">
          <div className="text-4xl mb-4">👤</div>
          <h3 className="text-lg font-medium text-foreground mb-2">
            Agent Profile
          </h3>
          <p className="text-muted-foreground mb-4">
            Detailed agent information and expertise
          </p>
          <button className="btn btn-primary">
            Coming Soon
          </button>
        </div>
      </div>
    </div>
  )
}