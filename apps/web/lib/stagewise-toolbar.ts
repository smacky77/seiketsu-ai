// @21st-extension/toolbar configuration
import { initToolbar } from '@21st-extension/toolbar';

// Define your toolbar configuration
const stagewiseConfig = {
  plugins: [],
  // You can add more configuration options here as needed
  // Examples:
  // theme: 'dark',
  // position: 'bottom-right',
  // collapsed: true,
};

// Initialize the toolbar when your app starts
export function setupStagewise() {
  // Only initialize once and only in development mode
  if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
    initToolbar(stagewiseConfig);
  }
}