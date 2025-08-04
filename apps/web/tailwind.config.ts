import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // OKLCH Monochromatic System - Pure blacks, whites, grays
        background: 'oklch(100% 0 0)', // Pure white
        foreground: 'oklch(0% 0 0)', // Pure black
        muted: {
          DEFAULT: 'oklch(96% 0 0)', // Light gray
          foreground: 'oklch(20% 0 0)', // Dark gray
        },
        accent: {
          DEFAULT: 'oklch(90% 0 0)', // Accent gray
          foreground: 'oklch(10% 0 0)', // Dark accent
        },
        border: 'oklch(85% 0 0)', // Border gray
        card: {
          DEFAULT: 'oklch(98% 0 0)', // Card background
          foreground: 'oklch(5% 0 0)', // Card text
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
export default config