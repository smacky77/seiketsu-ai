'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Server, 
  Database, 
  Wifi, 
  HardDrive, 
  Cpu, 
  Activity,
  AlertCircle,
  CheckCircle,
  Clock,
  RefreshCw
} from 'lucide-react'

interface SystemComponent {
  name: string
  status: 'healthy' | 'warning' | 'critical'
  uptime: string
  lastCheck: string
  metrics: {
    cpu?: number
    memory?: number
    disk?: number
    latency?: number
  }
  icon: any
}

const systemComponents: SystemComponent[] = [
  {
    name: 'Voice Processing Server',
    status: 'healthy',
    uptime: '99.97%',
    lastCheck: '30s ago',
    metrics: { cpu: 23, memory: 68, latency: 120 },
    icon: Server
  },
  {
    name: 'Database Cluster',
    status: 'healthy',
    uptime: '99.99%',
    lastCheck: '15s ago',
    metrics: { cpu: 45, memory: 72, disk: 34 },
    icon: Database
  },
  {
    name: 'API Gateway',
    status: 'warning',
    uptime: '98.23%',
    lastCheck: '45s ago',
    metrics: { cpu: 67, memory: 89, latency: 890 },
    icon: Wifi
  },
  {
    name: 'Storage System',
    status: 'healthy',
    uptime: '99.95%',
    lastCheck: '20s ago',
    metrics: { disk: 67, memory: 34 },
    icon: HardDrive
  }
]

const getStatusColor = (status: string) => {
  switch (status) {
    case 'healthy':
      return 'text-green-500'
    case 'warning':
      return 'text-yellow-500'
    case 'critical':
      return 'text-red-500'
    default:
      return 'text-gray-500'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'healthy':
      return <CheckCircle className="w-4 h-4 text-green-500" />
    case 'warning':
      return <AlertCircle className="w-4 h-4 text-yellow-500" />
    case 'critical':
      return <AlertCircle className="w-4 h-4 text-red-500" />
    default:
      return <Clock className="w-4 h-4 text-gray-500" />
  }
}

const getMetricColor = (value: number, threshold: { warning: number; critical: number }) => {
  if (value >= threshold.critical) return 'bg-red-500'
  if (value >= threshold.warning) return 'bg-yellow-500'
  return 'bg-green-500'
}

export function SystemHealthMonitor() {
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const [isRefreshing, setIsRefreshing] = useState(false)

  const handleRefresh = () => {
    setIsRefreshing(true)
    setTimeout(() => {
      setLastUpdated(new Date())
      setIsRefreshing(false)
    }, 1000)
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold">System Health</h2>
          <p className="text-sm text-muted-foreground">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="btn btn-secondary"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* System Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-muted rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-5 h-5 text-green-500" />
            <span className="font-medium">Overall System Status</span>
          </div>
          <div className="text-2xl font-bold text-green-500">Operational</div>
          <div className="text-sm text-muted-foreground">All critical systems running normally</div>
        </div>

        <div className="bg-muted rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="w-5 h-5 text-blue-500" />
            <span className="font-medium">Global Performance</span>
          </div>
          <div className="text-2xl font-bold">98.7%</div>
          <div className="text-sm text-muted-foreground">Average performance score</div>
        </div>
      </div>

      {/* Component Status Grid */}
      <div className="space-y-4">
        {systemComponents.map((component, index) => (
          <motion.div
            key={component.name}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-muted rounded-lg p-4"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-background rounded-lg flex items-center justify-center border border-border">
                  <component.icon className="w-5 h-5 text-muted-foreground" />
                </div>
                <div>
                  <div className="font-medium">{component.name}</div>
                  <div className="text-sm text-muted-foreground">
                    Uptime: {component.uptime} • {component.lastCheck}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {getStatusIcon(component.status)}
                <span className={`text-sm font-medium capitalize ${getStatusColor(component.status)}`}>
                  {component.status}
                </span>
              </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {component.metrics.cpu !== undefined && (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-muted-foreground">CPU</span>
                    <span className="text-xs font-medium">{component.metrics.cpu}%</span>
                  </div>
                  <div className="h-2 bg-background rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${getMetricColor(component.metrics.cpu, { warning: 70, critical: 90 })}`}
                      style={{ width: `${component.metrics.cpu}%` }}
                    />
                  </div>
                </div>
              )}

              {component.metrics.memory !== undefined && (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-muted-foreground">Memory</span>
                    <span className="text-xs font-medium">{component.metrics.memory}%</span>
                  </div>
                  <div className="h-2 bg-background rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${getMetricColor(component.metrics.memory, { warning: 80, critical: 95 })}`}
                      style={{ width: `${component.metrics.memory}%` }}
                    />
                  </div>
                </div>
              )}

              {component.metrics.disk !== undefined && (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-muted-foreground">Disk</span>
                    <span className="text-xs font-medium">{component.metrics.disk}%</span>
                  </div>
                  <div className="h-2 bg-background rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${getMetricColor(component.metrics.disk, { warning: 85, critical: 95 })}`}
                      style={{ width: `${component.metrics.disk}%` }}
                    />
                  </div>
                </div>
              )}

              {component.metrics.latency !== undefined && (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-muted-foreground">Latency</span>
                    <span className="text-xs font-medium">{component.metrics.latency}ms</span>
                  </div>
                  <div className="h-2 bg-background rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${getMetricColor(
                        (component.metrics.latency / 1000) * 100, 
                        { warning: 50, critical: 80 }
                      )}`}
                      style={{ width: `${Math.min((component.metrics.latency / 1000) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}