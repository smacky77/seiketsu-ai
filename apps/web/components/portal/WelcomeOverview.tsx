'use client'

// Welcome overview based on client trust-building patterns from UX research
interface ClientData {
  name: string
  agent: {
    name: string
    photo: string
    phone: string
    email: string
    responseTime: string
  }
  searchStatus: {
    budget: string
    location: string
    propertyType: string
    timeline: string
    viewedProperties: number
    savedProperties: number
    scheduledViewings: number
  }
}

export default function WelcomeOverview({ client }: { client: ClientData }) {
  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
        {/* Personalized welcome */}
        <div>
          <h1 className="text-2xl font-bold text-foreground mb-2">
            Welcome back, {client.name}
          </h1>
          <p className="text-muted-foreground">
            Your property search is progressing well. Here's your latest update.
          </p>
        </div>
        
        {/* Trust-building agent connection */}
        <div className="bg-muted rounded-lg p-4 min-w-0 lg:min-w-[300px]">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-accent rounded-full flex items-center justify-center">
              👤
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-medium text-foreground">{client.agent.name}</div>
              <div className="text-sm text-muted-foreground">Your dedicated agent</div>
              <div className="text-xs text-muted-foreground">
                Avg. response: {client.agent.responseTime}
              </div>
            </div>
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          </div>
        </div>
      </div>
      
      {/* Search progress indicators - builds confidence */}
      <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center p-4 bg-muted rounded-lg">
          <div className="text-2xl font-bold text-foreground">{client.searchStatus.viewedProperties}</div>
          <div className="text-sm text-muted-foreground">Properties Viewed</div>
        </div>
        <div className="text-center p-4 bg-muted rounded-lg">
          <div className="text-2xl font-bold text-foreground">{client.searchStatus.savedProperties}</div>
          <div className="text-sm text-muted-foreground">Saved Favorites</div>
        </div>
        <div className="text-center p-4 bg-muted rounded-lg">
          <div className="text-2xl font-bold text-foreground">{client.searchStatus.scheduledViewings}</div>
          <div className="text-sm text-muted-foreground">Upcoming Viewings</div>
        </div>
        <div className="text-center p-4 bg-accent rounded-lg">
          <div className="text-sm font-medium text-accent-foreground">Search Timeline</div>
          <div className="text-xs text-accent-foreground opacity-75">{client.searchStatus.timeline}</div>
        </div>
      </div>
      
      {/* Current search criteria - transparency */}
      <div className="mt-6 p-4 bg-muted rounded-lg">
        <h3 className="font-medium text-foreground mb-3">Your Current Search</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Budget: </span>
            <span className="font-medium">{client.searchStatus.budget}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Location: </span>
            <span className="font-medium">{client.searchStatus.location}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Type: </span>
            <span className="font-medium">{client.searchStatus.propertyType}</span>
          </div>
        </div>
      </div>
    </div>
  )
}