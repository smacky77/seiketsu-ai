// @21st-extension/toolbar configuration
// import { initToolbar } from '@21st-extension/toolbar'; // Disabled due to missing module

let initToolbar: any;
try {
  // Dynamically import to avoid build-time error if module is missing
  initToolbar = require('@21st-extension/toolbar').initToolbar;
} catch (e) {
  console.warn('Could not load @21st-extension/toolbar:', e);
  initToolbar = () => {};
}

// Enhanced toolbar configuration for BMAD Phase 2
const stagewiseConfig = {
  plugins: [
    'voice-processing',
    'real-estate-data',
    'lead-qualification',
    'market-intelligence'
  ],
  theme: 'dark',
  position: 'bottom-right',
  aiAssistance: true,
  realTimeCollaboration: true,
  // Development workflow enhancements
  features: {
    codeGeneration: true,
    apiTesting: true,
    performanceMonitoring: true,
    errorTracking: true,
    realtimeSync: true
  },
  // Integration settings
  integrations: {
    backend: 'http://localhost:8000',
    websocket: 'ws://localhost:8000/ws',
    elevenlabs: process.env.NEXT_PUBLIC_ELEVENLABS_API_KEY
  }
};

// Initialize the toolbar when your app starts
export function setupStagewise() {
  // Only initialize once and only in development mode
  if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
    initToolbar(stagewiseConfig);
  }
}