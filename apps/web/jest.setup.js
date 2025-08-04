import '@testing-library/jest-dom'

// Global test utilities and setup
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
    forward: jest.fn(),
    refresh: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

// Mock Framer Motion
jest.mock('framer-motion', () => ({
  motion: {
    div: 'div',
    span: 'span',
    p: 'p',
    h1: 'h1',
    h2: 'h2',
    h3: 'h3',
    button: 'button',
    form: 'form',
    input: 'input',
    section: 'section',
    article: 'article',
    header: 'header',
    footer: 'footer',
  },
  AnimatePresence: ({ children }) => children,
}))

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  Mic: () => <span data-testid="mic-icon">Mic</span>,
  Phone: () => <span data-testid="phone-icon">Phone</span>,
  MessageSquare: () => <span data-testid="message-icon">Message</span>,
  Calendar: () => <span data-testid="calendar-icon">Calendar</span>,
  Settings: () => <span data-testid="settings-icon">Settings</span>,
  User: () => <span data-testid="user-icon">User</span>,
  Home: () => <span data-testid="home-icon">Home</span>,
  Search: () => <span data-testid="search-icon">Search</span>,
  Filter: () => <span data-testid="filter-icon">Filter</span>,
  Heart: () => <span data-testid="heart-icon">Heart</span>,
  Share: () => <span data-testid="share-icon">Share</span>,
  ChevronDown: () => <span data-testid="chevron-down-icon">ChevronDown</span>,
  ChevronRight: () => <span data-testid="chevron-right-icon">ChevronRight</span>,
  Play: () => <span data-testid="play-icon">Play</span>,
  Pause: () => <span data-testid="pause-icon">Pause</span>,
  Volume2: () => <span data-testid="volume-icon">Volume2</span>,
  Menu: () => <span data-testid="menu-icon">Menu</span>,
  X: () => <span data-testid="x-icon">X</span>,
  Check: () => <span data-testid="check-icon">Check</span>,
  AlertCircle: () => <span data-testid="alert-icon">AlertCircle</span>,
  Info: () => <span data-testid="info-icon">Info</span>,
  Building: () => <span data-testid="building-icon">Building</span>,
  Users: () => <span data-testid="users-icon">Users</span>,
  BarChart: () => <span data-testid="bar-chart-icon">BarChart</span>,
  TrendingUp: () => <span data-testid="trending-up-icon">TrendingUp</span>,
  Shield: () => <span data-testid="shield-icon">Shield</span>,
  Zap: () => <span data-testid="zap-icon">Zap</span>,
  Globe: () => <span data-testid="globe-icon">Globe</span>,
  Lock: () => <span data-testid="lock-icon">Lock</span>,
  Mail: () => <span data-testid="mail-icon">Mail</span>,
  ExternalLink: () => <span data-testid="external-link-icon">ExternalLink</span>,
}))