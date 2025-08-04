"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Mic, MicOff, Phone, PhoneCall, Loader2 } from "lucide-react"

export type VoiceStatus = 'idle' | 'listening' | 'processing' | 'speaking' | 'error'

interface VoiceStatusIndicatorProps {
  status: VoiceStatus
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  className?: string
}

const statusConfig = {
  idle: {
    color: 'bg-muted text-muted-foreground',
    icon: MicOff,
    label: 'Idle',
    animation: ''
  },
  listening: {
    color: 'bg-blue-500/20 text-blue-600 dark:text-blue-400',
    icon: Mic,
    label: 'Listening',
    animation: 'animate-pulse'
  },
  processing: {
    color: 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-400',
    icon: Loader2,
    label: 'Processing',
    animation: 'animate-spin'
  },
  speaking: {
    color: 'bg-green-500/20 text-green-600 dark:text-green-400',
    icon: PhoneCall,
    label: 'Speaking',
    animation: 'animate-voice-pulse'
  },
  error: {
    color: 'bg-red-500/20 text-red-600 dark:text-red-400',
    icon: Phone,
    label: 'Error',
    animation: 'animate-bounce-gentle'
  }
}

const sizeConfig = {
  sm: 'w-6 h-6',
  md: 'w-8 h-8',
  lg: 'w-12 h-12'
}

export function VoiceStatusIndicator({ 
  status, 
  size = 'md', 
  showLabel = false,
  className 
}: VoiceStatusIndicatorProps) {
  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <div className={cn("flex items-center space-x-2", className)}>
      <div className={cn(
        "flex items-center justify-center rounded-full transition-all duration-300",
        config.color,
        config.animation,
        sizeConfig[size]
      )}>
        <Icon className={cn(
          size === 'sm' ? 'w-3 h-3' : 
          size === 'md' ? 'w-4 h-4' : 
          'w-6 h-6'
        )} />
      </div>
      {showLabel && (
        <span className={cn(
          "text-sm font-medium",
          size === 'sm' ? 'text-xs' : 'text-sm'
        )}>
          {config.label}
        </span>
      )}
    </div>
  )
}

interface WaveformProps {
  isActive?: boolean
  bars?: number
  className?: string
}

export function Waveform({ isActive = false, bars = 5, className }: WaveformProps) {
  return (
    <div className={cn("flex items-center justify-center space-x-1", className)}>
      {Array.from({ length: bars }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "w-1 bg-current transition-all duration-300",
            isActive ? 'animate-waveform' : 'h-2'
          )}
          style={{
            animationDelay: isActive ? `${i * 100}ms` : '0ms',
            height: isActive ? 'auto' : '8px'
          }}
        />
      ))}
    </div>
  )
}

interface VoiceControlsProps {
  isRecording: boolean
  onToggleRecording: () => void
  onEndCall?: () => void
  disabled?: boolean
  className?: string
}

export function VoiceControls({ 
  isRecording, 
  onToggleRecording, 
  onEndCall,
  disabled = false,
  className 
}: VoiceControlsProps) {
  return (
    <div className={cn("flex items-center space-x-4", className)}>
      <button
        onClick={onToggleRecording}
        disabled={disabled}
        className={cn(
          "flex items-center justify-center w-12 h-12 rounded-full transition-all duration-200",
          "focus:outline-none focus:ring-2 focus:ring-offset-2",
          isRecording 
            ? "bg-red-500 hover:bg-red-600 text-white focus:ring-red-500" 
            : "bg-blue-500 hover:bg-blue-600 text-white focus:ring-blue-500",
          disabled && "opacity-50 cursor-not-allowed"
        )}
      >
        {isRecording ? (
          <div className="w-4 h-4 rounded-sm bg-white" />
        ) : (
          <Mic className="w-5 h-5" />
        )}
      </button>
      
      {onEndCall && (
        <button
          onClick={onEndCall}
          disabled={disabled}
          className={cn(
            "flex items-center justify-center w-10 h-10 rounded-full",
            "bg-gray-500 hover:bg-gray-600 text-white transition-all duration-200",
            "focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500",
            disabled && "opacity-50 cursor-not-allowed"
          )}
        >
          <Phone className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}