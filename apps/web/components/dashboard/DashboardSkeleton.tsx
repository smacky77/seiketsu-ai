'use client'

export function DashboardSkeleton() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6 animate-pulse">
      {/* Primary Workspace Skeleton */}
      <div className="lg:col-span-2 space-y-6">
        {/* Voice Agent Workspace Skeleton */}
        <div className="card p-6">
          <div className="h-6 bg-muted rounded w-48 mb-6"></div>
          <div className="bg-muted rounded-lg p-6 mb-6">
            <div className="h-4 bg-background rounded w-32 mb-4"></div>
            <div className="h-20 bg-background rounded mb-4"></div>
            <div className="flex justify-center gap-4">
              <div className="w-12 h-12 bg-background rounded-full"></div>
              <div className="w-16 h-16 bg-background rounded-full"></div>
              <div className="w-12 h-12 bg-background rounded-full"></div>
            </div>
          </div>
          <div className="space-y-4">
            <div className="h-4 bg-muted rounded w-full"></div>
            <div className="h-4 bg-muted rounded w-full"></div>
          </div>
        </div>

        {/* Conversation Manager Skeleton */}
        <div className="card p-6">
          <div className="h-6 bg-muted rounded w-40 mb-6"></div>
          <div className="flex gap-2 mb-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-8 bg-muted rounded-lg w-24"></div>
            ))}
          </div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-4 bg-muted rounded-lg">
                <div className="h-4 bg-background rounded w-32 mb-2"></div>
                <div className="h-3 bg-background rounded w-full mb-2"></div>
                <div className="h-3 bg-background rounded w-48"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      {/* Secondary Panel Skeleton */}
      <div className="space-y-6">
        {/* Lead Qualification Skeleton */}
        <div className="card p-6">
          <div className="h-6 bg-muted rounded w-36 mb-6"></div>
          <div className="space-y-2 mb-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-3 bg-muted rounded-lg">
                <div className="h-4 bg-background rounded w-full"></div>
              </div>
            ))}
          </div>
          <div className="space-y-4">
            <div className="bg-muted rounded-lg p-4">
              <div className="h-4 bg-background rounded w-24 mb-3"></div>
              <div className="h-2 bg-background rounded w-full"></div>
            </div>
            <div className="grid grid-cols-1 gap-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="p-3 bg-muted rounded-lg">
                  <div className="h-3 bg-background rounded w-20 mb-1"></div>
                  <div className="h-4 bg-background rounded w-full"></div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Performance Metrics Skeleton */}
        <div className="card p-6">
          <div className="h-6 bg-muted rounded w-32 mb-6"></div>
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="p-4 bg-muted rounded-lg">
                <div className="h-4 bg-background rounded w-28 mb-2"></div>
                <div className="h-6 bg-background rounded w-16"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}