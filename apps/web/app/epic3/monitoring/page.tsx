'use client'

import React from 'react'
import { SystemMonitoringDashboard } from '@/components/epic3/SystemMonitoringDashboard'
import { PerformanceMetrics } from '@/components/epic3/PerformanceMetrics'
import { AlertManagementPanel } from '@/components/epic3/AlertManagementPanel'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Activity, AlertTriangle, BarChart3 } from 'lucide-react'

export default function Epic3MonitoringPage() {
  return (
    <div className="min-h-screen bg-slate-900 p-4">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <Button variant="ghost" asChild className="text-slate-400 hover:text-white mb-4">
              <a href="/epic3">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Epic 3
              </a>
            </Button>
            <h1 className="text-3xl font-bold text-white">
              Epic 3 System Monitoring
            </h1>
            <p className="text-slate-400 mt-2">
              Real-time monitoring and performance analytics for market intelligence and communication systems
            </p>
          </div>
          <div className="flex gap-2">
            <div className="flex items-center gap-2 bg-green-900/20 text-green-400 px-3 py-1 rounded-full">
              <Activity className="w-4 h-4" />
              All Systems Operational
            </div>
          </div>
        </div>

        {/* System Status Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                Market Intelligence
              </CardTitle>
              <BarChart3 className="h-4 w-4 text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">99.8%</div>
              <p className="text-xs text-slate-400">
                Uptime last 24h
              </p>
              <div className="mt-2">
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{width: '99.8%'}}></div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                Communication System
              </CardTitle>
              <Activity className="h-4 w-4 text-green-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">100%</div>
              <p className="text-xs text-slate-400">
                Message delivery rate
              </p>
              <div className="mt-2">
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{width: '100%'}}></div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                Scheduling System
              </CardTitle>
              <AlertTriangle className="h-4 w-4 text-yellow-400" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">97.2%</div>
              <p className="text-xs text-slate-400">
                Booking success rate
              </p>
              <div className="mt-2">
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div className="bg-yellow-600 h-2 rounded-full" style={{width: '97.2%'}}></div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* System Monitoring Dashboard */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">System Performance Monitor</CardTitle>
            <CardDescription className="text-slate-400">
              Real-time system metrics and health indicators
            </CardDescription>
          </CardHeader>
          <CardContent>
            <SystemMonitoringDashboard />
          </CardContent>
        </Card>

        {/* Performance Metrics */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Performance Analytics</CardTitle>
            <CardDescription className="text-slate-400">
              Detailed performance metrics and trends
            </CardDescription>
          </CardHeader>
          <CardContent>
            <PerformanceMetrics />
          </CardContent>
        </Card>

        {/* Alert Management */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Alert Management</CardTitle>
            <CardDescription className="text-slate-400">
              System alerts, notifications, and incident management
            </CardDescription>
          </CardHeader>
          <CardContent>
            <AlertManagementPanel />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}